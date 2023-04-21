import json
import urllib.request


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
		print(parsed)

	def parse(self, md):
		parsed = {}

		sections = md.split("##")[1:]
		for section in sections:
			title, content = section.split("\n", 1)
			# title = title.strip().lower().replace(" ", "-")
			parsed[title] = content

		return parsed

	def update(self, request):
		pass

	def delete(self, request):
		pass
