import json
import os
from pathlib import Path
from urllib.parse import quote, urlencode
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from manager.blueprints.auth import is_admin_user
from manager.intake_client import IntakeApiError, IntakeClient
from manager.models import SubmissionReviewLog, db
from manager.registry import Record, Registry
from manager.utils import METADATA_DIR, generate_id

submissions = Blueprint("submissions", __name__, url_prefix="/submissions")

def _normalize_items(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ["items", "results", "submissions", "data"]:
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []

def _extract_payload(submission):
    if not isinstance(submission, dict):
        return {}
    for key in ["payload_json", "payload", "record", "data"]:
        value = submission.get(key)
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
    return {}

def _is_admin_user():
    return is_admin_user()

def _require_admin_redirect():
    if not _is_admin_user():
        flash("Admin access required", "danger")
        return redirect(url_for("manager.index"))
    return None

def _record_from_payload(payload, schema=None):
    schema = schema or Registry().schema
    record = Record(schema)
    data = {}
    for field in schema.lookup.values():
        if field.id in payload:
            data[field.id] = payload.get(field.id)
        else:
            data[field.id] = field.get_default()
    metadata_field = schema.lookup.get("metadata_version")
    if (
        not data.get("metadata_version")
        or (
            metadata_field
            and metadata_field.controlled
            and data.get("metadata_version") not in metadata_field.controlled_options
        )
    ):
        data["metadata_version"] = "SDOH PlaceProject"
    record.data = data
    return record

def _record_id_from_submission(submission, payload):
    return submission.get("record_id") or payload.get("id") or generate_id()

def _record_form_context(payload):
    registry = Registry()
    record = _record_from_payload(payload, registry.schema)
    records = registry.records_as_json()
    relations_choices = [(r["id"], r["title"]) for r in records]
    return {
        "record": record.to_form(),
        "display_groups": record.schema.display_groups,
        "relations_choices": relations_choices,
    }

def _record_from_form(form_data):
    registry = Registry()
    record = Record(registry.schema)
    record.update_from_form_data(form_data)
    return record

def _submitter_email(submission):
    if not isinstance(submission, dict):
        return ""
    return submission.get("submitter_email") or submission.get("email") or ""

def _submitter_name(submission):
    if not isinstance(submission, dict):
        return ""
    return submission.get("submitter_name") or submission.get("name") or ""

def _submitter_username(submission):
    if not isinstance(submission, dict):
        return ""
    return submission.get("submitter_username") or ""

def _submitter_id(submission):
    if not isinstance(submission, dict):
        return ""
    return submission.get("submitter_id") or submission.get("sub") or ""

def _submission_id(submission):
    return submission.get("id") or submission.get("submission_id")

def _all_submission_items(client):
    return _normalize_items(client.list_submissions())

def _contributors_from_submissions(items, record_ids=None):
    record_ids = record_ids or set()
    contributors = {}
    for item in items:
        if item.get("status") == "deleted":
            continue
        email = _submitter_email(item)
        name = _submitter_name(item)
        key = email or name or "Unknown"
        contributor = contributors.setdefault(
            key,
            {
                "key": key,
                "email": email,
                "name": name,
                "username": _submitter_username(item),
                "user_id": _submitter_id(item),
                "submission_count": 0,
                "statuses": set(),
                "latest_update": "",
                "submissions": [],
            },
        )
        contributor["submission_count"] += 1
        if item.get("status"):
            contributor["statuses"].add(item.get("status"))
        updated_at = item.get("updated_at") or item.get("submitted_at") or ""
        if updated_at > contributor["latest_update"]:
            contributor["latest_update"] = updated_at
        if not contributor["email"] and email:
            contributor["email"] = email
        if not contributor["name"] and name:
            contributor["name"] = name
        if not contributor["username"] and _submitter_username(item):
            contributor["username"] = _submitter_username(item)
        if not contributor["user_id"] and _submitter_id(item):
            contributor["user_id"] = _submitter_id(item)
        payload = _extract_payload(item)
        contributor["submissions"].append(
            {
                "id": _submission_id(item),
                "title": _payload_title(payload, _submission_id(item)),
                "status": item.get("status") or "",
                "updated_at": updated_at,
                "record_id": item.get("record_id") or payload.get("id") or "",
                "has_record": (item.get("record_id") or payload.get("id") or "") in record_ids,
            }
        )
    for contributor in contributors.values():
        contributor["statuses"] = ", ".join(sorted(contributor["statuses"]))
        contributor["submissions"] = sorted(
            contributor["submissions"],
            key=lambda item: item["updated_at"],
            reverse=True,
        )
    return sorted(contributors.values(), key=lambda item: item["key"].lower())

def _payload_title(payload, fallback):
    title = payload.get("title") if isinstance(payload, dict) else ""
    if isinstance(title, list):
        title = title[0] if title else ""
    return title or fallback

def _frontend_submission_url(submission_id):
    base_url = os.getenv("DISCOVERY_APP_URL", "").rstrip("/")
    if not base_url or not submission_id:
        return ""
    return f"{base_url}/contribute/submissions/?id={quote(str(submission_id), safe='')}"

def _render_email_template(template_name, **context):
    text = render_template(f"email/{template_name}.txt", **context).strip()
    lines = text.splitlines()
    if lines and lines[0].startswith("Subject:"):
        subject = lines[0].replace("Subject:", "", 1).strip()
        body = "\n".join(lines[1:]).lstrip()
        return subject, body
    return "", text

def _gmail_compose_url(email, subject, body):
    return (
        "https://mail.google.com/mail/?"
        + urlencode(
            {
                "view": "cm",
                "fs": "1",
                "to": email,
                "su": subject,
                "body": body,
            }
        )
    )

def _email_template_name(status):
    if status == "needs_changes":
        return "submission_needs_changes"
    if status == "rejected":
        return "submission_rejected"
    if status == "approved":
        return "submission_approved"
    return ""

def _email_submitter_links(submission, payload, notes):
    email = _submitter_email(submission)
    if not email:
        return {}
    submission_id = submission.get("id") or submission.get("submission_id")
    template_name = _email_template_name(submission.get("status"))
    if not template_name:
        return {}
    title = _payload_title(
        payload,
        str(submission_id or "submission"),
    )
    subject, body = _render_email_template(
        template_name,
        title=title,
        notes=notes,
        submission_url=_frontend_submission_url(submission_id),
        contact_email=os.getenv("CONTACT_EMAIL", ""),
    )
    return {
        "gmail": _gmail_compose_url(email, subject, body),
    }

def _render_submission_detail(
    submission,
    submission_id,
    payload,
    error=None,
    validation_errors=None,
    notes=None,
):
    submission_text = json.dumps(submission, indent=2) if submission else "{}"
    if notes is not None:
        review_notes = notes
    elif submission:
        review_notes = submission.get("review_notes", "")
    else:
        review_notes = ""
    email_submitter_links = {}
    if submission:
        email_submitter_links = _email_submitter_links(submission, payload, review_notes)
    return render_template(
        "submissions/detail.html",
        submission=submission,
        submission_id=submission_id,
        submission_text=submission_text,
        error=error,
        validation_errors=validation_errors or [],
        review_notes=review_notes,
        email_submitter_links=email_submitter_links,
        **_record_form_context(payload),
    )

def _save_review_log(submission_id, action, reviewer, record_id=None, notes=None, payload_json=None):
    entry = SubmissionReviewLog(
        submission_id=str(submission_id),
        action=action,
        reviewer=reviewer,
        record_id=record_id,
        notes=notes,
        payload_json=payload_json,
    )
    db.session.add(entry)
    db.session.commit()

@submissions.route("/", methods=["GET"])
@login_required
def list_submissions():
    redirect_response = _require_admin_redirect()
    if redirect_response:
        return redirect_response
    status = request.args.get("status", "submitted")
    client = IntakeClient()
    items = []
    error = None
    try:
        response = client.list_submissions(status=status)
        items = _normalize_items(response)
    except IntakeApiError as exc:
        error = str(exc)
    return render_template("submissions/list.html", submissions=items, status=status, error=error)

@submissions.route("/contributors", methods=["GET"])
@login_required
def list_contributors():
    redirect_response = _require_admin_redirect()
    if redirect_response:
        return redirect_response
    client = IntakeClient()
    error = None
    contributors = []
    try:
        record_ids = {record["id"] for record in Registry().records_as_json()}
        contributors = _contributors_from_submissions(_all_submission_items(client), record_ids)
    except IntakeApiError as exc:
        error = str(exc)
    return render_template(
        "submissions/contributors.html",
        contributors=contributors,
        error=error,
    )


@submissions.route("/contributors/update", methods=["POST"])
@login_required
def update_contributor():
    redirect_response = _require_admin_redirect()
    if redirect_response:
        return redirect_response
    original_email = request.form.get("original_email", "").strip()
    original_name = request.form.get("original_name", "").strip()
    submitter_email = request.form.get("submitter_email", "").strip()
    submitter_name = request.form.get("submitter_name", "").strip()
    client = IntakeClient()
    updated = 0
    try:
        for item in _all_submission_items(client):
            item_email = _submitter_email(item)
            item_name = _submitter_name(item)
            if original_email and item_email != original_email:
                continue
            if not original_email and item_name != original_name:
                continue
            client.update_submission(
                _submission_id(item),
                submitter_email=submitter_email,
                submitter_name=submitter_name,
            )
            updated += 1
    except IntakeApiError as exc:
        flash(f"Intake API error: {exc}", "danger")
        return redirect(url_for("submissions.list_contributors"))
    flash(f"Updated {updated} submission{'s' if updated != 1 else ''}", "success")
    return redirect(url_for("submissions.list_contributors"))

@submissions.route("/approved/add-records", methods=["POST"])
@login_required
def add_approved_records():
    redirect_response = _require_admin_redirect()
    if redirect_response:
        return redirect_response
    client = IntakeClient()
    reviewer = current_user.email if current_user.email else current_user.name
    created = 0
    skipped = 0
    failed = []
    try:
        response = client.list_submissions(status="approved")
        items = _normalize_items(response)
        for submission in items:
            submission_id = submission.get("id") or submission.get("submission_id")
            payload = _extract_payload(submission)
            record = _record_from_payload(payload)
            record_id = _record_id_from_submission(submission, payload)
            record.data["id"] = record_id
            record.file_path = Path(METADATA_DIR, "records", f"{record_id}.json")
            if record.file_path.exists():
                skipped += 1
                continue
            validation_errors = record.validate()
            if validation_errors:
                failed.append(f"{submission_id}: {'; '.join(validation_errors)}")
                continue
            event = {
                "action": "add_approved_submission_record",
                "submission_id": str(submission_id),
                "reviewer": reviewer,
            }
            record.save(history=True, history_event=event)
            client.decide_submission(
                submission_id=submission_id,
                decision="approve",
                record_id=record_id,
                reviewed_by=reviewer,
                reviewed_payload=record.to_json(),
            )
            _save_review_log(
                submission_id=submission_id,
                action="add_record",
                reviewer=reviewer,
                record_id=record_id,
                payload_json=json.dumps(record.to_json()),
            )
            created += 1
    except IntakeApiError as exc:
        flash(f"Intake API error: {exc}", "danger")
        return redirect(url_for("submissions.list_submissions", status="approved"))
    if created:
        flash(f"Added {created} approved record{'s' if created != 1 else ''}", "success")
    if skipped:
        flash(f"Skipped {skipped} approved record{'s' if skipped != 1 else ''} that already exist", "warning")
    for error in failed:
        flash(error, "danger")
    if not created and not skipped and not failed:
        flash("No approved submissions found", "warning")
    return redirect(url_for("submissions.list_submissions", status="approved"))

@submissions.route("/<submission_id>/delete", methods=["POST"])
@login_required
def delete_submission(submission_id):
    redirect_response = _require_admin_redirect()
    if redirect_response:
        return redirect_response
    client = IntakeClient()
    status = request.form.get("status") or request.args.get("status") or "submitted"
    reviewer = current_user.email if current_user.email else current_user.name
    try:
        result = client.delete_submission(submission_id)
        _save_review_log(
            submission_id=submission_id,
            action="delete_submission",
            reviewer=reviewer,
        )
        if result.get("soft_deleted"):
            flash(f"Submission {submission_id} moved to deleted status", "success")
        else:
            flash(f"Submission {submission_id} deleted", "success")
    except IntakeApiError as exc:
        flash(f"Intake API error: {exc}", "danger")

    return redirect(url_for("submissions.list_submissions", status=status))

@submissions.route("/<submission_id>", methods=["GET"])
@login_required
def view_submission(submission_id):
    redirect_response = _require_admin_redirect()
    if redirect_response:
        return redirect_response
    client = IntakeClient()
    error = None
    validation_errors = []
    submission = {}
    payload = {}
    try:
        submission = client.get_submission(submission_id)
        payload = _extract_payload(submission)
    except IntakeApiError as exc:
        error = str(exc)
    return _render_submission_detail(
        submission=submission,
        submission_id=submission_id,
        payload=payload,
        error=error,
        validation_errors=validation_errors,
    )


@submissions.route("/<submission_id>/action", methods=["POST"])
@login_required
def submission_action(submission_id):
    redirect_response = _require_admin_redirect()
    if redirect_response:
        return redirect_response
    action = request.form.get("action", "save")
    notes = request.form.get("notes", "").strip()
    try:
        record = _record_from_form(request.form)
        payload = record.to_json()
    except Exception as exc:
        flash(f"Error parsing submission form: {exc}", "danger")
        return redirect(url_for("submissions.view_submission", submission_id=submission_id))
    client = IntakeClient()
    reviewer = current_user.email if current_user.email else current_user.name
    try:
        client.update_submission(submission_id, payload_json=payload)
        if action == "save":
            _save_review_log(
                submission_id=submission_id,
                action="save_admin_edits",
                reviewer=reviewer,
                notes=notes,
                payload_json=json.dumps(payload),
            )
            flash("Submission edits saved", "success")
            return redirect(url_for("submissions.view_submission", submission_id=submission_id))

        if action == "approve":
            record_id = record.data.get("id") or generate_id()
            record.data["id"] = record_id
            validation_errors = record.validate()
            if validation_errors:
                for err in validation_errors:
                    flash(err, "danger")
                return _render_submission_detail(
                    submission={"id": submission_id, "status": "submitted"},
                    submission_id=submission_id,
                    payload=record.to_json(),
                    validation_errors=validation_errors,
                    notes=notes,
                )
            client.decide_submission(
                submission_id=submission_id,
                decision="approve",
                notes=notes,
                record_id=record_id,
                reviewed_by=reviewer,
                reviewed_payload=record.to_json(),
            )
            _save_review_log(
                submission_id=submission_id,
                action="approve",
                reviewer=reviewer,
                record_id=record_id,
                notes=notes,
                payload_json=json.dumps(record.to_json()),
            )
            flash("Submission approved. Add it from the Approved tab when ready.", "success")
            return redirect(url_for("submissions.list_submissions", status="approved"))

        if action in ["needs_changes", "reject"]:
            decided_submission = client.decide_submission(
                submission_id=submission_id,
                decision=action,
                notes=notes,
                reviewed_by=reviewer,
                reviewed_payload=payload,
            )
            _save_review_log(
                submission_id=submission_id,
                action=action,
                reviewer=reviewer,
                notes=notes,
                payload_json=json.dumps(payload),
            )
            if action == "needs_changes":
                flash(
                    "Submission marked as needs_changes. Use Email Submitter to send the admin notes.",
                    "success",
                )
                return redirect(url_for("submissions.view_submission", submission_id=submission_id))
            email_links = _email_submitter_links(
                decided_submission,
                payload,
                notes,
            )
            if email_links.get("gmail"):
                return redirect(email_links["gmail"])
            flash(f"Submission marked as {action}", "success")
            return redirect(url_for("submissions.list_submissions"))
        flash("Unknown action", "danger")
        return redirect(url_for("submissions.view_submission", submission_id=submission_id))

    except IntakeApiError as exc:
        flash(f"Intake API error: {exc}", "danger")
        return redirect(url_for("submissions.view_submission", submission_id=submission_id))
