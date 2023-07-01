import os
import glob
import json
import urllib.request
from datetime import datetime

from manager.utils import FIELD_LOOKUP
from manager.model import RecordModel, db

class Ingest:

	def __init__(self):
		pass

	def get(self, request):
		pass

	def set(self, request):
		""" fairly sure this isn't needed at all """
		print(request)
		data = json.loads(request.data)

		uuid = data.get("id", None)
		url = data.get("url", None)

		if not uuid or not url:
			return json.dumps({"error": "UUID or URL is missing!"})

		# Check if uuid at Solr

		try:
			response = urllib.request.urlopen(url)
			md = response.read().decode('utf-8')
		except Exception as e:
			print(e)
			return json.dumps({"error": "URL is invalid!"})

		parsed = self.parse(md)
		if parsed:
			self.save(parsed)
			return json.dumps({"status": "success"})
		return json.dumps({"error": "Failed to parse markdown file"})

	def save(self, parsed):
		pass

	def parse_markdown(self, md_path):
		parsed = {}

		with open(md_path, "r") as o:
			md = o.read()

		sections = md.split("##")[1:]
		for section in sections:
			title, content = section.split("\n", 1)
			title = title.lstrip().rstrip()
			title_key = title.lower().replace(" ", "_")

			content_list = content.split("\n")
			content_cleaned = "|".join([i.rstrip().rstrip("*").lstrip("*") for i in content_list if i])
			if title_key in FIELD_LOOKUP:
				parsed[title_key] = content_cleaned
			else:
				print(f"ERROR matching this section header: {title}")

		return parsed
	
	def process_aardvark_files(self, file_dir, staging_dir):

		for p in glob.glob(os.path.join(file_dir, "*.md")):
			id = os.path.splitext(os.path.basename(p))[0].lower().replace(" ", "-").replace("_", "-")

			if "template" in id or "readme" in id:
				continue
			print(id)
			record_data = self.parse_markdown(p)
			record_data['id'] = id
			stage_path = os.path.join(staging_dir, id + ".json")
			with open(stage_path, "w") as f:
				json.dump(record_data, f, indent=2)

	def load_from_staging(self, staging_dir):

		for json_file in glob.glob(os.path.join(staging_dir, "*.json")):
			with open(json_file, "r") as f:
				record_data = json.load(f)
				id = record_data.pop('id')

			record = RecordModel.query.get(id)
			if not record:
				record = RecordModel()
				record.id = id
				db.session.add(record)

			for k, v in record_data.items():
				if k == "modified":
					v = datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
				if isinstance(v, list):
					v = "|".join(v)
				setattr(record, k, v)

			record.resource_class = "Dataset"
			record.access_rights = "Public"

			db.session.commit()

	def save_to_staging(self):

		for record in RecordModel.query.all():
			record.export_to_staging()

	def update(self, request):
		pass

	def delete(self, request):
		pass
