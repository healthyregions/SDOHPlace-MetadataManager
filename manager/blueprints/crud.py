import logging
from dotenv import load_dotenv

from flask import Blueprint, request, render_template, jsonify, url_for, redirect, flash, current_app
from flask_cors import CORS
from flask_login import (
    current_user,
    login_required,
)
from werkzeug.exceptions import NotFound, Unauthorized

from manager.registry import Registry, Record
from manager.solr import Solr

load_dotenv()

crud = Blueprint('manager', __name__)

registry = Registry()

CORS(crud)

logger = logging.getLogger(__name__)

@crud.route("/", methods=["GET"])
def index():
	registry = Registry()
	records = [r.to_json() for r in registry.records]
	return render_template('index.html', records=records)

@crud.route("/table", methods=["GET"])
def table_view():
	records = [r.to_json() for r in registry.records]
	schema = registry.schema
	fields = schema.schema_json['fields']
	return render_template('full_table.html', records=records, fields=fields)

@crud.route("/record/create", methods=["GET"])
@login_required
def create_record():
	if request.method == "GET":
		schema = Registry().schema
		records = [r.to_json() for r in registry.records]
		relations_choices = [(r['id'], r['title']) for r in records]
		return render_template('crud/edit.html',
			create_new=True,
			record=schema.get_blank_form(),
			display_groups=schema.display_groups,
			relations_choices=relations_choices,
		)

@crud.route("/record/validate", methods=["POST"])
@login_required
def validate_record():
	if request.method == "POST":
		schema = registry.schema
		form_errors = schema.validate_form_data(request.form)
		if form_errors:
			html = "<ul>"
			for i in form_errors:
				html += f'<li class="notification is-danger">{i}</li>'
			html += "</ul>"
		else:
			html = '<label id="save-button-label" class="button is-success is-small is-fullwidth" for="submit-edit-form" tabindex="0" >Save</label>'
		return html

@crud.route("/record/<id>", methods=["GET", "POST", "DELETE"])
def handle_record(id):

	if request.method == "GET":
		registry = Registry()
		record = registry.get_record(id)
		if not record:
			raise NotFound
		format = request.args.get('f', 'html')
		edit = request.args.get('edit') == "true"
		if format == "html":
			if edit:
				records = [r.to_json() for r in registry.records]
				relations_choices = [(r['id'], r['title']) for r in records]
				return render_template('crud/edit.html',
					record=record.to_form(),
					relations_choices=relations_choices,
					display_groups=record.schema.display_groups,
				)
			else:
				return render_template(
					'crud/view.html',
					record=record.to_json(),
					display_groups=record.schema.display_groups,
				)
		elif format == "json":
			return jsonify(record.to_json())
		elif format == "solr":
			return jsonify(record.to_solr())

	if request.method == "POST":
		registry = Registry()
		if current_user.is_authenticated:
			record = registry.get_record(id)
			if record:
				record.save_from_form_data(request.form)
				record.last_modified_by = current_user.name
			else:
				record = Record(registry.schema)
				record.save_from_form_data(request.form)
			return redirect(url_for('manager.handle_record', id=record.data['id']))
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
			current_app.logger.info(f"reindexing all records...")
			s.delete_all()
			registry = Registry()
			records = [i.to_solr() for i in registry.records]
			s.multi_add(records)
			return redirect('/')
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
