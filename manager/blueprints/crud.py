from dotenv import load_dotenv

from flask import Blueprint, request, render_template, jsonify, url_for, redirect
from flask_cors import CORS
from flask_login import (
    current_user,
    login_required,
)
from werkzeug.exceptions import NotFound, Unauthorized

from manager.models import Registry
from manager.solr import Solr

load_dotenv()

registry = Registry()

crud = Blueprint('manager', __name__)

CORS(crud)

@crud.route("/", methods=["GET"])
def index():
	records = registry.get_all(format='json')
	return render_template('index.html', records=records, user=current_user)

@crud.route("/record/create", methods=["GET"])
@login_required
def create_record():
	if request.method == "GET":
		record = registry.get_blank_record()
		return render_template('crud/edit.html', record=record.to_form(), user=current_user)

@crud.route("/record/<id>", methods=["GET", "POST", "DELETE"])
def handle_record(id):
	record = registry.get(id)
	if not record:
		raise NotFound

	if request.method == "GET":
		format = request.args.get('f', 'html')
		edit = request.args.get('edit') == "true"
		if format == "html":
			if edit:
				return render_template('crud/edit.html', record=record.to_form(), user=current_user)
			else:
				return render_template('crud/view.html', record=record.to_json(), user=current_user)
		elif format == "json":
			return jsonify(record.to_json())
		elif format == "solr":
			return jsonify(record.to_solr())

	if request.method == "POST":
		if current_user.is_authenticated:
			record = registry.load_record_from_form_data(request.form)
			record.save()
			return redirect(url_for('manager.handle_record', id=record.id))
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
			records = [i.to_solr() for i in registry.get_all()]
			s.multi_add(records)
			return redirect('/')
		else:
			record = registry.get(id)
			record.index()
			return redirect(url_for('manager.handle_record', id=record.id))
	elif request.method == "DELETE":
		pass
