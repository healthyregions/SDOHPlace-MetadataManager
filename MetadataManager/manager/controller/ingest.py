import os
import glob
import json
import click
from dotenv import load_dotenv

from flask import Blueprint, request
from flask_cors import CORS

from manager.schema import Record, db
from manager.service.ingest import Ingest

ingest = Blueprint('ingest', __name__)
CORS(ingest)

load_dotenv()

# experimenting with the addition of CLI commands here
@ingest.cli.command('markdown')
@click.option('--file_dir')
def ingest_markdown_files(file_dir):

	from manager.app import PROJECT_DIR

	i = Ingest()
	if file_dir is None:
		file_dir = os.path.join(PROJECT_DIR, 'metadata', 'Aardvark')
	
	for p in glob.glob(os.path.join(file_dir, "*.md")):
		id = os.path.splitext(os.path.basename(p))[0].lower().replace(" ", "-").replace("_", "-")

		if "template" in id:
			continue
		print(id)
		record_data = i.parse(p)

		record = Record.query.get(id)
		if not record:
			record = Record()
			record.id = id
			db.session.add(record)
		print(record)
		for k, v in record_data.items():
			setattr(record, k, v)
		if not record.title:
			record.title = "NEEDS A TITLE"
		record.resource_class = "Dataset"
		record.access_rights = "Public"
		record.metadata_version = "Aardvark"
		print(json.dumps(record_data, indent=1))
		db.session.commit()

		result = record.index()
		print(json.dumps(result, indent=1))

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

