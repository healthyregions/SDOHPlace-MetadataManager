from dotenv import load_dotenv

from flask import Blueprint, request, render_template, jsonify, url_for, redirect, flash
from flask_cors import CORS
from flask_login import (
    current_user,
    login_required,
)
from werkzeug.exceptions import NotFound, Unauthorized

from manager.models import db, Record, Schema
from manager.solr import Solr

load_dotenv()

crud = Blueprint('manager', __name__)

CORS(crud)

@crud.route("/", methods=["GET"])
def index():
	records = [r.to_json() for r in Record.query.all()]
	records = sorted(records, key=lambda d: d['title'])
	return render_template('index.html', records=records)

@crud.route("/table", methods=["GET"])
def table_view():
	records = [r.to_json() for r in Record.query.all()]
	records = sorted(records, key=lambda d: d['title'])
	return render_template('full_table.html', records=records)

@crud.route("/record/create", methods=["GET"])
@login_required
def create_record():
	if request.method == "GET":
		schema = Schema.query.get(1)
		records = [r.to_json() for r in Record.query.all()]
		relations_choices = [(r['id'], r['title']) for r in records]
		return render_template('crud/edit.html',
						 record=schema.get_blank_form(),
						 field_groups=schema.grouped_fields,
						 relations_choices=relations_choices,
						 )

@crud.route("/record/validate", methods=["POST"])
@login_required
def validate_record():
	if request.method == "POST":
		schema = Schema.query.get(1)
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
		r = Record.query.filter_by(data_file=id+".json")
		if r:
			record = r[0]
		else:
			return NotFound
		format = request.args.get('f', 'html')
		edit = request.args.get('edit') == "true"
		if format == "html":
			if edit:
				records = [r.to_json() for r in Record.query.all()]
				relations_choices = [(r['id'], r['title']) for r in records]
				return render_template('crud/edit.html', record=record.to_form(), field_groups=record.schema.grouped_fields, relations_choices=relations_choices)
			else:
				return render_template('crud/view.html', record=record.to_json(), field_groups=record.schema.grouped_fields)
		elif format == "json":
			return jsonify(record.to_json())
		elif format == "solr":
			return jsonify(record.to_solr())

	if request.method == "POST":
		if current_user.is_authenticated:
			record = Record.query.filter_by(data_file=id+".json").first()
			if record:
				record.save_from_form_data(request.form)
				record.last_modified_by = current_user.name
				db.session.commit()
			else:
				record = Record()
				record.schema_id = 1
				record.save_from_form_data(request.form)
				db.session.add(record)
				db.session.commit()
			record.load_data()
			return redirect(url_for('manager.handle_record', id=record.data['id']))
		else:
			return Unauthorized
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
			s.delete_all()
			records = [i.to_solr() for i in Record.query.all()]
			s.multi_add(records)
			return redirect('/')
		else:
			try:
				record = Record.query.filter_by(data_file=id+".json")[0]
				record.index()
				return f'<div class="notification is-success">{record.data["title"]} re-indexed successfully</div>'
			except Exception as e:
				return f'<div class="notification is-success">Error while re-indexing record: {e}</div>'
	elif request.method == "DELETE":
		pass
