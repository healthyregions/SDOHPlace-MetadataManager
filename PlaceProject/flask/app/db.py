import json
from flask_sqlalchemy import SQLAlchemy

from app.utils import FIELD_LOOKUP

db = SQLAlchemy()

class Record(db.Model):
    __tablename__ = 'records'

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
    georeferenced = db.Column(db.Boolean)
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
    suppressed = db.Column(db.Boolean)

    def to_json(self):
        for i in self.__table__.columns:
            print(FIELD_LOOKUP[i]['uri'])
        return {}