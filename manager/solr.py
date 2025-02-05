import os
import pysolr

from flask import current_app

SOLR_HOST = os.getenv("SOLR_HOST", "").rstrip("/")
SOLR_CORE = os.getenv("SOLR_CORE", "").rstrip("/")
SOLR_USERNAME = os.getenv("SOLR_USERNAME", "")
SOLR_PASSWORD = os.getenv("SOLR_PASSWORD", "")
SOLR_URL = f"{SOLR_HOST}/{SOLR_CORE}/"


class Solr:
    def __init__(self, verbose=False):
        self.solr = pysolr.Solr(
            SOLR_URL, always_commit=True, auth=(SOLR_USERNAME, SOLR_PASSWORD)
        )
        self.health_check()
        self.verbose = verbose
        if self.verbose:
            print(f"Solr host: {SOLR_URL}")
        current_app.logger.debug(f"solr client initialized. core: {SOLR_URL}")

    def add(self, doc):
        current_app.logger.debug(f"Solr add document: {doc['id']}")
        return self.solr.add([doc])

    def multi_add(self, arr):
        current_app.logger.debug(f"Solr adding {len(arr)} documents.")
        return self.solr.add(arr)

    def search(self, query, filters=None):
        return self.solr.search(query, **filters)

    def delete(self, identifier):
        return self.solr.delete(id=identifier)

    def multi_delete(self, identifiers):
        return self.solr.delete(id=identifiers)

    def delete_all(self):
        return self.solr.delete(q="*:*")

    def health_check(self):
        try:
            self.solr.ping()
        except Exception as e:
            print(e)
