import os
import pysolr

from flask import current_app

SOLR_HOST = os.getenv("SOLR_HOST", "").rstrip("/")
SOLR_CORE = os.getenv("SOLR_CORE", "").rstrip("/")  # Legacy support
SOLR_CORE_STAGE = os.getenv("SOLR_CORE_STAGE", "blacklight-core-stage").rstrip("/")
SOLR_CORE_PROD = os.getenv("SOLR_CORE_PROD", "blacklight-core-prod").rstrip("/")
SOLR_USERNAME = os.getenv("SOLR_USERNAME", "")
SOLR_PASSWORD = os.getenv("SOLR_PASSWORD", "")

# Legacy URL for backward compatibility
SOLR_URL = f"{SOLR_HOST}/{SOLR_CORE}/" if SOLR_CORE else f"{SOLR_HOST}/{SOLR_CORE_PROD}/"


class Solr:
    def __init__(self, environment="prod", verbose=False):
        """
        Initialize Solr client.
        
        Args:
            environment: Either 'stage' or 'prod' to determine which core to use
            verbose: Enable verbose logging
        """
        self.environment = environment
        
        # Determine which core to use based on environment
        if environment == "stage":
            core = SOLR_CORE_STAGE
        elif environment == "prod":
            core = SOLR_CORE_PROD
        else:
            # Fallback to legacy SOLR_CORE or prod
            core = SOLR_CORE if SOLR_CORE else SOLR_CORE_PROD
        
        self.core = core
        self.solr_url = f"{SOLR_HOST}/{core}/"
        
        self.solr = pysolr.Solr(
            self.solr_url, always_commit=True, auth=(SOLR_USERNAME, SOLR_PASSWORD)
        )
        self.health_check()
        self.verbose = verbose
        if self.verbose:
            print(f"Solr host: {self.solr_url}")
        current_app.logger.debug(f"solr client initialized. core: {self.solr_url} (environment: {environment})")

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
