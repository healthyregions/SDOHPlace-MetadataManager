import json
from flask_sqlalchemy import SQLAlchemy

from manager.utils import FIELD_LOOKUP

db = SQLAlchemy()

class Record(db.Model):
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
    references = db.Column(db.String)
    wxs_indentifier = db.Column(db.String)
    identifier = db.Column(db.String)
    modified = db.Column(db.String, nullable=False)
    metadata_version = db.Column(db.String, nullable=False)
    suppressed = db.Column(db.Boolean, nullable=True)

    def to_json(self):
        """ Full serialization of the record, splits multiple value fields
        to lists and converts the references JSON string to dict."""

        result = {}
        for i in self.__table__.columns:
            value = getattr(self, i.name)
            if i == "references" and value is not None:
                value = json.loads(value)
            if FIELD_LOOKUP[i.name]['multiple'] and value is not None:
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

        solr_doc = {}
        for i in self.__table__.columns:
            value = getattr(self, i.name)
            if value is not None:
                if FIELD_LOOKUP[i.name]['multiple']:
                    value = value.split("|")

                uri = FIELD_LOOKUP[i.name]['uri']
                solr_doc[uri] = value
        return solr_doc