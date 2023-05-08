import json
import urllib.request

from manager.utils import FIELD_LOOKUP

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

	def update(self, request):
		pass

	def delete(self, request):
		pass
