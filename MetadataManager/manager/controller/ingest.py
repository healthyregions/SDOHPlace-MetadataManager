import click

from flask import Blueprint, request
from flask_cors import CORS

from manager.service.ingest import Ingest

ingest = Blueprint('ingest', __name__)
CORS(ingest)

# experimenting with the addition of CLI commands here
@ingest.cli.command('markdown')
@click.argument('file_dir')
def ingest_markdown_files(file_dir):
	print(file_dir)

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

