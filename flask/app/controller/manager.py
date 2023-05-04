from flask import Blueprint, request, render_template, jsonify, url_for, redirect
from flask_cors import CORS

from app.schema import Record, db
from app.utils import GROUPED_FIELD_LOOKUP, clean_form_data

manager = Blueprint('manager', __name__)
CORS(manager)

@manager.route("/", methods=["GET"])
def index():
	records = Record.query.all()
	return render_template('index.html', records=records)

@manager.route("/record/<id>", methods=["GET", "POST", "PATCH", "DELETE"])
def detail(id):
	if request.method == "GET":
		record = Record.query.get_or_404(id)
		return render_template('record.html', record=record.to_json(), field_groups=GROUPED_FIELD_LOOKUP)
	
@manager.route("/record/create", methods=["GET", "POST", "PATCH", "DELETE"])
def create():
	if request.method == "GET":
		return render_template('edit.html', record=None, field_groups=GROUPED_FIELD_LOOKUP)
	
	elif request.method == "POST":
		print(request.form)
		print(dir(request.form))
		cleaned_data = clean_form_data(request.form)
		record = Record()
		for k, v in cleaned_data.items():
			setattr(record, k, v)
		db.session.add(record)
		db.session.commit()
		return redirect(url_for('manager.detail', id=record.id))

@manager.route("/record/<id>/edit", methods=["GET", "POST", "PATCH", "DELETE"])
def edit(id):
	if request.method == "GET":
		record = Record.query.get_or_404(id)
		return render_template('edit.html', record=record.to_form(), field_groups=GROUPED_FIELD_LOOKUP)

	elif request.method == "POST":
		cleaned_data = clean_form_data(request.form)
		record = Record.query.get_or_404(request.form['id'])
		for k, v in cleaned_data.items():
			setattr(record, k, v)

		db.session.commit()
		return redirect(url_for('manager.detail', id=record.id))

@manager.route("/record/<id>/json", methods=["GET"])
def as_json(id):
	record = Record.query.get_or_404(id)
	return jsonify(record.to_json())

@manager.route("/record/<id>/solr", methods=["GET"])
def as_solr(id):
	record = Record.query.get_or_404(id)
	return jsonify(record.to_solr())
