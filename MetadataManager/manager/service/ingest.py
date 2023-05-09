import os
import glob
import json
import urllib.request

from manager.utils import FIELD_LOOKUP
from manager.model import RecordModel, db

class Ingest:

	def __init__(self):
		pass

	def get(self, request):
		pass

	def set(self, request):
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

	def parse(self, md_path):
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
	
	def process_aardvark_files(self, file_dir):

		for p in glob.glob(os.path.join(file_dir, "*.md")):
			id = os.path.splitext(os.path.basename(p))[0].lower().replace(" ", "-").replace("_", "-")

			if "template" in id or "readme" in id:
				continue
			print(id)
			record_data = self.parse(p)

			record = RecordModel.query.get(id)
			if not record:
				record = RecordModel()
				record.id = id
				db.session.add(record)
			print(record)
			for k, v in record_data.items():
				setattr(record, k, v)

			record.resource_class = "Dataset"
			record.access_rights = "Public"
			# print(json.dumps(record_data, indent=1))
			db.session.commit()

			result = record.index()
			# print(json.dumps(result, indent=1))

	def update(self, request):
		pass

	def delete(self, request):
		pass
