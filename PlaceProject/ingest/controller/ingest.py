import json

from flask import Blueprint, request
from flask_cors import CORS

from service.ingest import Ingest

ingest = Blueprint('ingest', __name__)
CORS(ingest)


@ingest.route("/", methods=["GET"])
def index():
	return json.dumps({})


@ingest.route("/place", methods=["GET", "POST", "PATCH", "DELETE"])
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

