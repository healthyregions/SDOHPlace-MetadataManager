import json
import logging
from dotenv import load_dotenv
from flask import (
    Blueprint,
    request,
    render_template,
    jsonify,
    url_for,
    redirect,
    current_app,
    flash,
)
from flask_cors import CORS
from flask_login import (
    current_user,
    login_required,
)
from markupsafe import escape
from werkzeug.exceptions import NotFound, Unauthorized
from werkzeug.utils import secure_filename
from manager.blueprints.auth import is_admin_user
from manager.intake_client import IntakeApiError, IntakeClient
from manager.registry import Registry, Record
from manager.solr import Solr
from manager.spatial_client import (
    BOUNDARY_YEARS,
    SPATIAL_LEVEL_MAP,
    UPLOAD_KINDS,
    SpatialClient,
    SpatialPipelineError,
)

load_dotenv()

crud = Blueprint("manager", __name__)

SPATIAL_POLL_SECONDS = 3
SPATIAL_POLL_MAX_ATTEMPTS = 300  # 15 minutes

def _notify_record_deleted(record_id, submission_id=None):
    try:
        client = IntakeClient()
        if not submission_id:
            submission = client.find_submission_by_record_id(record_id)
            if not submission:
                return
            submission_id = submission.get("id") or submission.get("submission_id")
        if submission_id:
            client.mark_record_deleted(submission_id)
    except IntakeApiError as exc:
        current_app.logger.warning(
            "Could not notify submitter about deleted record %s: %s", record_id, exc
        )

registry = Registry()

CORS(crud)

logger = logging.getLogger(__name__)


@crud.route("/help", methods=["GET"])
def help_page():
    return render_template("help.html")


@crud.route("/", methods=["GET"])
def index():
    registry = Registry()
    show_hidden = True if request.args.get("show-hidden") == "true" else False
    contribution_source = request.args.get("contribution-source", "")
    records = registry.records_as_json()
    if show_hidden is False:
        records = [r for r in records if r["suppressed"] is not True]
    if contribution_source:
        records = [
            r for r in records
            if (r.get("contrubution_source") or "manager") == contribution_source
        ]
    return render_template(
        "index.html",
        records=records,
        show_hidden=show_hidden,
        contribution_source=contribution_source,
    )


@crud.route("/table", methods=["GET"])
def table_view():
    registry = Registry()
    records = registry.records_as_json()
    schema = registry.schema
    fields = schema.schema_json["fields"]
    return render_template("full_table.html", records=records, fields=fields)


@crud.route("/record/create", methods=["GET"])
@login_required
def create_record():
    if request.method == "GET":
        schema = Registry().schema
        records = registry.records_as_json()
        relations_choices = [(r["id"], r["title"]) for r in records]
        return render_template(
            "crud/edit.html",
            create_new=True,
            record=schema.get_blank_form(),
            display_groups=schema.display_groups,
            relations_choices=relations_choices,
            spatial_levels=list(SPATIAL_LEVEL_MAP),
        )


@crud.route("/record/<id>", methods=["GET", "POST", "DELETE"])
def handle_record(id):
    if request.method == "GET":
        registry = Registry()
        record = registry.get_record(id)
        if not record:
            raise NotFound
        format = request.args.get("f", "html")
        edit = request.args.get("edit") == "true"
        if format == "html":
            records = registry.records_as_json()
            link_list = [
                {"id": r["id"], "title": r["title"]}
                for r in records
                if not r["suppressed"]
            ]
            if edit:
                relations_choices = [(r["id"], r["title"]) for r in records]
                return render_template(
                    "crud/edit.html",
                    record=record.to_form(),
                    relations_choices=relations_choices,
                    link_list=link_list,
                    display_groups=record.schema.display_groups,
                )
            else:
                return render_template(
                    "crud/view.html",
                    record=record.to_json(),
                    link_list=link_list,
                    display_groups=record.schema.display_groups,
                )
        elif format == "json":
            return jsonify(record.to_json())
        elif format == "solr":
            return jsonify(record.to_solr())

    if request.method == "POST":

        if not current_user.is_authenticated:
            raise Unauthorized

        action = request.args.get("action")
        if action == "validate":
            registry = Registry()
            record = registry.get_record(id)
            if not record:
                record = Record(registry.schema)

            form_errors = []
            try:
                record.update_from_form_data(request.form)
                form_errors += record.validate()
            except Exception as e:
                form_errors += [
                    f"Error parsing form: {e}",
                    "This must be fixed before you can continue",
                ]
            if form_errors:
                html = "<ul>"
                for i in form_errors:
                    html += f'<li class="notification is-danger">{i}</li>'
                html += "</ul>"
            else:
                html = '<label id="save-button-label" class="button is-success is-small is-fullwidth" for="submit-edit-form" tabindex="0" >Save</label>'
            return html

        elif action == "save":
            registry = Registry()
            record = registry.get_record(id)
            if not record:
                record = Record(registry.schema)

            record.update_from_form_data(request.form)
            record.save()

            return redirect(url_for("manager.handle_record", id=record.data["id"]))
        elif action == "delete":
            registry = Registry()
            record = registry.get_record(id)
            if not record:
                raise NotFound
            submission_id = (record.meta or {}).get("submission_id")
            record.file_path.unlink()
            _notify_record_deleted(id, submission_id)
            flash(f"Deleted record {id}. Refresh Solr Index to remove it from search.", "success")
            return redirect(url_for("manager.index"))
        else:
            raise Unauthorized
    elif request.method == "DELETE":
        pass


@crud.route("/solr/<id>", methods=["POST", "DELETE"])
@login_required
def handle_solr(id):
    # Get environment parameter from query string (dev or prod)
    environment = request.args.get("env", "prod")
    
    # Check if user is admin for production indexing
    if environment == "prod" and not is_admin_user():
        current_app.logger.warning(f"User {current_user.name} attempted to index to production without admin privileges")
        return f'<div class="notification is-danger">Only admin users can index to production. Please use dev instead.</div>'
    
    s = Solr(environment=environment)
    
    if request.method == "POST":
        # ultimately, reindex-all should be calling a method on Solr()
        # but leaving here for the moment.
        if id == "reindex-all":
            current_app.logger.info(f"reindexing all records to {environment}...")
            s.delete_all()
            registry = Registry()
            records = [i.to_solr() for i in registry.records]
            s.multi_add(records)
            return redirect("/")
        else:
            current_app.logger.info(f"indexing {id} to {environment}")
            registry = Registry()
            record = registry.get_record(id)
            if not record:
                raise NotFound
            result = record.index(solr_instance=s)
            if result["success"]:
                current_app.logger.info(f"record {id} indexed successfully to {environment}")
                current_app.logger.debug(result["document"])
                env_label = "dev" if environment == "dev" else "production"
                return f'<div class="notification is-success">{record.data["title"]} indexed to {env_label} successfully</div>'
            else:
                current_app.logger.error(result["error"])
                return f'<div class="notification is-danger">Error while indexing record: {result["error"]}</div>'
    elif request.method == "DELETE":
        pass

def _spatial_error(message):
    return f'<div class="notification is-danger">{escape(message)}</div>'

def _spatial_polling_fragment(record_id, s3_key, attempt):
    status_url = url_for(
        "manager.generate_spatial_status", id=record_id, key=s3_key, attempt=attempt
    )
    elapsed = (attempt - 1) * SPATIAL_POLL_SECONDS
    return (
        f'<div class="notification is-info is-light" hx-get="{status_url}" '
        f'hx-trigger="load delay:{SPATIAL_POLL_SECONDS}s" hx-swap="outerHTML">'
        f"Generating geospatial metadata&hellip; waiting for result.json ({elapsed}s)"
        "</div>"
    )

def _spatial_result_fragment(result):
    if not result.get("ok"):
        code = escape(str(result.get("error_code", "unknown")))
        message = escape(str(result.get("message", "")))
        return (
            f'<div class="notification is-danger">'
            f"<strong>Pipeline failed ({code}).</strong> {message}</div>"
        )
    geometry = str(result.get("geometry") or "")
    geometry_preview = geometry[:120] + ("…" if len(geometry) > 120 else "")
    highlight_ids = result.get("highlight_ids") or []
    highlight_preview = ", ".join(highlight_ids[:5])
    if len(highlight_ids) > 5:
        highlight_preview += f", … ({len(highlight_ids)} total)"
    diagnostics = result.get("diagnostics") or {}
    rows = [
        ("Bounding box", result.get("bounding_box")),
        ("Centroid", result.get("centroid")),
        ("Spatial coverage", ", ".join(result.get("spatial_coverage") or [])),
        ("Highlight IDs", highlight_preview),
        ("Match rate", diagnostics.get("match_rate")),
        ("Warnings", "; ".join(diagnostics.get("warnings") or [])),
        ("Geometry", geometry_preview),
    ]
    items = "".join(
        f"<li><strong>{escape(label)}:</strong> {escape(str(value))}</li>"
        for label, value in rows
        if value not in (None, "")
    )
    fill = {
        "geometry": result.get("geometry") or "",
        "bounding_box": result.get("bounding_box") or "",
        "centroid": result.get("centroid") or "",
        "spatial_coverage": "\n".join(result.get("spatial_coverage") or []),
        "highlight_ids": "\n".join(result.get("highlight_ids") or []),
    }
    fill_json = json.dumps(fill).replace("</", "<\\/")
    script = (
        "<script>(function () {"
        f"const fill = {fill_json};"
        "for (const [name, value] of Object.entries(fill)) {"
        "  const el = document.querySelector('#edit-form [name=\"' + name + '\"]');"
        "  if (el) el.value = value;"
        "}"
        "})();</script>"
    )
    return (
        '<div class="notification is-success">'
        "<strong>Geospatial metadata generated and filled into the form below.</strong> "
        "Review the spatial fields, then complete the rest of the record and Save."
        f"<ul>{items}</ul></div>{script}"
    )

@crud.route("/record/<id>/spatial", methods=["POST"])
@login_required
def generate_spatial(id):
    if not id or id != secure_filename(id):
        return _spatial_error("Invalid record id.")

    upload = request.files.get("spatial_file")
    if upload is None or not upload.filename:
        return _spatial_error("Choose a file to upload first.")
    filename = secure_filename(upload.filename)
    if not filename:
        return _spatial_error("That file name cannot be used. Rename the file and try again.")
    
    upload_kind = "csv"
    if not filename.lower().endswith(UPLOAD_KINDS[upload_kind]):
        return _spatial_error("Upload a .csv file.")

    boundary_year = request.form.get("boundary_year", "")
    spatial_level_label = request.form.get("spatial_level", "")
    geo_id_column = request.form.get("geo_id_column", "").strip()
    if boundary_year not in BOUNDARY_YEARS:
        return _spatial_error("Choose a boundary year (2018 or 2010).")
    if spatial_level_label not in SPATIAL_LEVEL_MAP:
        return _spatial_error("Choose a spatial level for the CSV join.")

    client = SpatialClient()
    s3_key = client.new_job_key(id, filename)
    payload = client.build_payload(
        record_id=id,
        s3_key=s3_key,
        upload_kind=upload_kind,
        boundary_year=boundary_year,
        spatial_level=SPATIAL_LEVEL_MAP.get(spatial_level_label),
        geo_id_column=geo_id_column,
    )
    try:
        client.upload_fileobj(upload, s3_key)
        client.invoke(payload)
    except SpatialPipelineError as exc:
        current_app.logger.error(f"spatial pipeline start failed for {id}: {exc}")
        return _spatial_error(f"Could not start the spatial pipeline: {exc}")

    current_app.logger.info(f"spatial pipeline started for {id}: {s3_key}")
    return _spatial_polling_fragment(id, s3_key, attempt=1)

@crud.route("/record/<id>/spatial/status", methods=["GET"])
@login_required
def generate_spatial_status(id):
    s3_key = request.args.get("key", "")
    if not s3_key.startswith(f"uploads/{id}/"):
        return _spatial_error("Unknown pipeline job for this record.")
    try:
        attempt = int(request.args.get("attempt", "1"))
    except ValueError:
        attempt = 1
    client = SpatialClient()
    try:
        result = client.fetch_result(client.result_key(s3_key))
    except SpatialPipelineError as exc:
        current_app.logger.error(f"spatial pipeline poll failed for {id}: {exc}")
        return _spatial_error(f"Could not check the pipeline result: {exc}")
    if result is None:
        if attempt >= SPATIAL_POLL_MAX_ATTEMPTS:
            return (
                '<div class="notification is-warning">'
                "The pipeline is still running after 15 minutes (the Lambda maximum). "
                f"Check s3://{escape(client.bucket)}/{escape(client.result_key(s3_key))} "
                "later, or re-run Generate.</div>"
            )
        return _spatial_polling_fragment(id, s3_key, attempt + 1)
    return _spatial_result_fragment(result)
