import os
import json
from dotenv import load_dotenv

from flask import Blueprint, request, render_template, jsonify, url_for, redirect
from flask_cors import CORS
from flask_login import (
    current_user,
    login_required,
)

from manager.model import RecordModel, db
from manager.utils import GROUPED_FIELD_LOOKUP, clean_form_data
from manager.service.ingest import Ingest
from manager.service.solr import Solr
from manager.service.record import Record

load_dotenv()

GBL_HOST = os.getenv("GBL_HOST").rstrip("/")

crud = Blueprint('manager', __name__)
ingest = Blueprint('ingest', __name__)

CORS(ingest)
CORS(crud)

@ingest.context_processor
@crud.context_processor
def get_context():
	return dict(
		gbl_host=GBL_HOST,
		field_groups=GROUPED_FIELD_LOOKUP,
	)

@ingest.route("/ingest", methods=["GET", "POST", "PATCH", "DELETE"])
def place():
	ingest = Ingest()
	if request.method == "GET":
		return ingest.get(request)
	elif request.method == "POST":
		return ingest.set(request)
	elif request.method == "PATCH":
		return ingest.update(request)
	elif request.method == "DELETE":
		return  ingest.delete(request)

@crud.route("/", methods=["GET"])
def index():
	print("user?")
	print(current_user.is_authenticated)
	records = RecordModel.query.order_by('title').all()
	return render_template('index.html', records=records, user=current_user)

@crud.route("/record/create", methods=["GET"])
@login_required
def create_record():
	if request.method == "GET":
		return Record().get(edit=True)

@crud.route("/record/<id>", methods=["GET", "POST", "DELETE"])
def handle_record(id):
	r = Record()
	if request.method == "GET":
		f = request.args.get('f', 'html')
		e = request.args.get('edit') == "true"
		return r.get(id, f, edit=e)
	if current_user.is_authenticated:
		if request.method == "POST":
			return r.post(request.form)
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
			records = [i.to_solr() for i in RecordModel.query.order_by('title').all()]
			s.multi_add(records)
			return redirect('/')
		else:
			r = RecordModel.query.get(id)
			r.index()
			return Record().get(id, 'html')
	elif request.method == "DELETE":
		pass
