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
)
from flask_cors import CORS
from flask_login import (
    current_user,
    login_required,
)
from werkzeug.exceptions import NotFound, Unauthorized

from manager.registry import Registry, Record
from manager.solr import Solr

load_dotenv()

crud = Blueprint("manager", __name__)

registry = Registry()

CORS(crud)

logger = logging.getLogger(__name__)


@crud.route("/", methods=["GET"])
def index():
    registry = Registry()
    show_hidden = True if request.args.get("show-hidden") == "true" else False
    records = registry.records_as_json()
    if show_hidden is False:
        records = [r for r in records if r["suppressed"] is not True]
    return render_template("index.html", records=records, show_hidden=show_hidden)


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
        else:
            raise Unauthorized
    elif request.method == "DELETE":
        pass


@crud.route("/solr/<id>", methods=["POST", "DELETE"])
@login_required
def handle_solr(id):
    s = Solr()
    if request.method == "POST":
        # ultimately, reindex-all should be calling a method on Solr()
        # but leaving here for the moment.
        if id == "reindex-all":
            current_app.logger.info("reindexing all records...")
            s.delete_all()
            registry = Registry()
            records = [i.to_solr() for i in registry.records]
            s.multi_add(records)
            return redirect("/")
        else:
            current_app.logger.info(f"indexing {id}")
            registry = Registry()
            record = registry.get_record(id)
            if not record:
                raise NotFound
            result = record.index(solr_instance=s)
            if result["success"]:
                current_app.logger.info(f"record {id} indexed successfully")
                current_app.logger.debug(result["document"])
                return f'<div class="notification is-success">{record.data["title"]} re-indexed successfully</div>'
            else:
                current_app.logger.error(result["error"])
                return f'<div class="notification is-danger">Error while re-indexing record: {result["error"]}</div>'
    elif request.method == "DELETE":
        pass
