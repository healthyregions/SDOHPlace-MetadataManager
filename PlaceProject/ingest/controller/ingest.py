import json

from flask import Blueprint
from flask_cors import CORS

ingest = Blueprint('ingest', __name__)
CORS(ingest)

@ingest.route("/", methods=["GET"])
def index():
	return json.dumps({})
