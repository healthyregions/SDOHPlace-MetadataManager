import os
import pysolr

SOLR_HOST = os.getenv('SOLR_HOST', '').rstrip('/')
SOLR_CORE = os.getenv('SOLR_CORE', '').rstrip('/')

SOLR_URL = f"{SOLR_HOST}/{SOLR_CORE}/"

class Solr:

	def __init__(self):
		self.solr = pysolr.Solr(
			SOLR_URL,
			always_commit=True
		)
		self.health_check()

	def add(self, doc):
		self.solr.add([doc])

	def multi_add(self, arr):
		self.solr.add(arr)

	def search(self, query, filters=None):
		return self.solr.search(query, **filters)

	def delete(self, identifier):
		return self.solr.delete(id=identifier)

	def multi_delete(self, identifiers):
		return self.solr.delete(id=identifiers)
	
	def delete_all(self):
		return self.solr.delete(q='*:*')

	def health_check(self):
		try:
			self.solr.ping()
		except Exception as e:
			print(e)