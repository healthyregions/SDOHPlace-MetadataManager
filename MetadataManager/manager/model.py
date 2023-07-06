import os
import json
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

from manager.utils import FIELD_LOOKUP

load_dotenv()
METADATA_DIR = os.getenv('METADATA_DIR')

db = SQLAlchemy()

class RecordModel(db.Model):
    __tablename__ = 'records'

    # Aardvark fields
    id = db.Column(db.String, nullable=False, primary_key=True)
    title = db.Column(db.String, nullable=False)
    alternative_title = db.Column(db.String)
    description = db.Column(db.String)
    language = db.Column(db.String)
    display_note = db.Column(db.String)
    creator = db.Column(db.String)
    publisher = db.Column(db.String)
    provider = db.Column(db.String)
    resource_class = db.Column(db.String, nullable=False)
    resource_type = db.Column(db.String)
    subject = db.Column(db.String)
    theme = db.Column(db.String)
    keyword = db.Column(db.String)
    temporal_coverage = db.Column(db.String)
    date_issued = db.Column(db.String)
    index_year = db.Column(db.Integer)
    date_range = db.Column(db.String)
    spatial_coverage = db.Column(db.String)
    geometry = db.Column(db.String)
    bounding_box = db.Column(db.String)
    centroid = db.Column(db.String)
    georeferenced = db.Column(db.Boolean, nullable=True)
    relation = db.Column(db.String)
    member_of = db.Column(db.String)
    is_part_of = db.Column(db.String)
    source = db.Column(db.String)
    is_version_of = db.Column(db.String)
    replaces = db.Column(db.String)
    is_replaced_by = db.Column(db.String)
    rights = db.Column(db.String)
    rights_holder = db.Column(db.String)
    license = db.Column(db.String)
    access_rights = db.Column(db.String, nullable=False)
    format = db.Column(db.String)
    file_size = db.Column(db.String)
    references = db.Column(db.JSON)
    wxs_indentifier = db.Column(db.String)
    identifier = db.Column(db.String)
    modified = db.Column(db.DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    metadata_version = db.Column(db.String, nullable=False)
    suppressed = db.Column(db.Boolean, nullable=True)

    spatial_resolution = db.Column(db.String)
    spatial_resolution_note = db.Column(db.String)
    methods_variables = db.Column(db.String)
    data_variables = db.Column(db.String)

    def to_json(self):
        """ Full serialization of the record, splits multiple value fields
        to lists and converts the references JSON string to dict."""

        result = {}
        for i in self.__table__.columns:
            value = getattr(self, i.name)
            if i.name == "references" and value is not None:
                pass
            elif i.name == "modified" and value is not None:
                value = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            elif FIELD_LOOKUP[i.name]['multiple'] and value is not None and not isinstance(value, int):
                value = value.split("|")
            result[i.name] = value
        return result
    
    def to_form(self):
        """ Prepares the raw backend data to populate an html form. """

        data = {}
        for k, v in self.to_json().items():
            value = "" if v is None else v
            if FIELD_LOOKUP[k]['multiple'] and isinstance(value, list):
                value = "|".join(value)
            data[k] = value
        return data

    def to_solr(self):
        """A variation on to_json() that uses the SOLR uris instead, and
        omits empty fields. Plus some other value wrangling."""

        # use self.to_json() to parse all values, and then insert them into
        # a dictionary with the proper URIs as keys. The references field
        # must still be handled specially.
        json_doc = self.to_json()
        solr_doc = {}
        for i in self.__table__.columns:
            value = getattr(self, i.name)
            if value is not None:
                if i.name == "references":
                    value = json.dumps(json_doc[i.name])
                else:
                    value = json_doc[i.name]
                uri = FIELD_LOOKUP[i.name]['uri']
                solr_doc[uri] = value
        return solr_doc

    def export_to_staging(self):

        path = os.path.join(METADATA_DIR, 'staging', self.id + ".json")
        with open(path, "w") as f:
            json.dump(self.to_json(), f, indent=2)
