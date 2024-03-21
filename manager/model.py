import os
import csv
import sys
import json
from pathlib import Path
from sqlalchemy import func
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from dotenv import load_dotenv
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely import unary_union

from manager.utils import METADATA_DIR, FIELD_LOOKUP, STATE_FP_LOOKUP, COUNTY_LSAD_LOOKUP, get_clean_field_from_form
from manager.service.solr import Solr

csv.field_size_limit(sys.maxsize)

load_dotenv()

db = SQLAlchemy()

class User(UserMixin):
    def __init__(self, email, password):
        self.id = email
        self.password = password

class Field():

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def validate(self, value):

        errors = []
        if isinstance(value, list):
            values_list = value
            if not self.multiple:
                msg = f"{self.label} -- Multi-value not allowed. Got: {value}"
                print(msg)
                errors.append(msg)
        else:
            values_list = [value]
        for val in values_list:
            if val and (self.controlled and val not in self.controlled_options):
                msg = f"{self.label} -- {val} not in list of acceptable values"
                print(msg)
                errors.append(msg)
        return errors


class RecordSchema():

    lookup: dict = {}

    @property
    def fields(self):
        return list(self.lookup.values())

    def from_schema_files(self, file_list):

        for path in file_list:
            with open(path, 'r') as o:
                schema_json = json.load(o)
                for k, v in schema_json.items():
                    f = Field(**v)
                    self.lookup[k] = f

        for k, v in self.lookup.items():
            v.column_name = k

        return self


class Record():

    schema: RecordSchema = None

    def __init__(self, schema: RecordSchema, **kwargs):

        self.schema = schema
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def validate(self):
        """ validate this record against its schema. """

        errors = []
        for key, field in self.schema.lookup.items():
            value = self.get_value(key)
            errors += field.validate(value)

        return errors

    def get_value(self, field_name):
        try:
            return self.__getattribute__(field_name)
        except AttributeError:
            return None

    def to_json(self):
        return {k: self.get_value(k) for k in self.schema.lookup.keys()}

    def to_form(self):
        """ Prepares the raw backend data to populate an html form. """

        data = {}
        for key, field in self.schema.lookup.items():
            value = self.get_value(key)
            if not value:
                value = ""
            if key == "references" and isinstance(value, dict):
                lines = ""
                for x, y in value.items():
                    lines += f"{x}:: {y}\n"
                value = lines
            if field.multiple and isinstance(value, list):
                if field.widget == "text-area.html":
                    value = "\n".join(value)
                else:
                    value = "|".join(value)
            data[key] = value
        return data

    def to_solr(self):
        """A variation on to_json() that uses the SOLR uris instead, and
        omits empty fields. Plus some other value wrangling."""

        solr_doc = {}
        for key, field in self.schema.lookup.items():
            value = self.get_value(key)
            if value is not None:
                if key == "references":
                    value = json.dumps(value)
                solr_doc[field.uri] = value
        return solr_doc

    def save(self, index=True):

        self.metadata_version = "SDOH PlaceProject"
        self.modified = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        record_file = Path(METADATA_DIR, "staging", self.id+".json")
        with open(record_file, "w") as o:
            json.dump(self.to_json(), o, indent=2)
        
        if index:
            self.index()

    def index(self, solr_instance=None):
        solr_doc = self.to_solr()
        if not solr_instance:
            solr_instance = Solr()
        try:
            solr_instance.add(solr_doc)
            result = {
                "success": True,
                "document": solr_doc
            }
        except Exception as e:
            result = {
                "success": False,
                "error": str(e)
            }
        return result


class Registry():

    def __init__(self):

        schema = RecordSchema().from_schema_files([
            os.path.join(METADATA_DIR, 'aardvark_schema.json'),
            os.path.join(METADATA_DIR, 'sdohplace_schema.json'),
        ])
        self.schema = schema

    def get_grouped_schema_fields(self):
        grouped_lookup = {
            "Identifiers": [],
            "Descriptive": [],
            "SDOH Place Project": [],
            "Credits": [],
            "Categories": [],
            "Temporal": [],
            "Spatial": [],
            "Relations": [],
            "Rights": [],
            "Object": [],
            "Links": [],
            "Admin": [],
        }
        for k, v in self.schema.lookup.items():
            grouped_lookup[v.display_group].append(v.__dict__)
        return grouped_lookup

    def load_record_from_file(self, file_path):

        with open(file_path, "r") as o:
            record_json = json.load(o)
            record = Record(self.schema, **record_json)
            errors = record.validate()
            if errors:
                print(errors)
            return record

    def load_record_from_form_data(self, form_data):

        cleaned_data = {}
        for field, field_def in self.schema.lookup.items():
            clean_value = get_clean_field_from_form(form_data, field, field_def)
            cleaned_data[field] = clean_value
        record = Record(self.schema, **cleaned_data)

        return record

    def get(self, record_id, format: str = None):

        record_file = Path(METADATA_DIR, "staging", record_id+".json")
        if not record_file.is_file():
            return None

        record = self.load_record_from_file(record_file)
        print(record)

        if format == "json":
            return record.to_json()
        elif format == "solr":
            return record.to_solr()
        elif format == "form-data":
            return record.to_form()
        else:
            return record

    def get_all(self, format: str = None, sort_by: str = "title"):

        files = Path(METADATA_DIR, "staging").glob("*.json")
        ids = [i.stem for i in files]
        records = [self.get(i, format=format) for i in ids]
        records.sort(key=lambda x: x[sort_by])
        return records
    
    def get_blank_record(self):

        blank = {}
        for k, v in self.schema.lookup.items():
            if v.multiple:
                val = []
            elif k == "references":
                val = {}
            else:
                val = None
            blank[k] = val
        record = Record(self.schema, **blank)

        return record


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
    data_usage_notes = db.Column(db.String)

    def to_json(self, enhance_geom=True):
        """ Full serialization of the record, splits multiple value fields
        to lists and converts the references JSON string to dict.

        enhance_geom=True will add extra geometry info to the relevant fields."""

        result = {}
        for i in self.__table__.columns:
            value = getattr(self, i.name)
            if i.name == "modified" and value is not None:
                value = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            elif FIELD_LOOKUP[i.name]['multiple'] and value is not None and not isinstance(value, int):
                value = value.split("|")
            result[i.name] = value

        if enhance_geom:
            sres = result.get('spatial_resolution')
            if sres:

                if "County" in sres:
                    df = gpd.read_file("https://github.com/GeoDaCenter/opioid-policy-scan/raw/main/data_final/geometryFiles/county/counties2018.shp")
                    print(df)
                    
                    def make_name(row):
                        if row[0] is None:
                            return ""
                        else:
                            return f'{row[0]}{" " + COUNTY_LSAD_LOOKUP[row[1]] if COUNTY_LSAD_LOOKUP[row[1]] else ""}, {STATE_FP_LOOKUP[row[2]]}'

                    df['cty_name'] = df[["NAME", "LSAD", "STATEFP"]].apply(lambda row: make_name(row), axis=1)
                    result['spatial_coverage'] = list(df['cty_name'])


                    def groupby_multipoly(df, by, aggfunc="first"):
                        data = df.drop(labels=df.geometry.name, axis=1)
                        aggregated_data = data.groupby(by=by).agg(aggfunc)

                        # Process spatial component
                        def merge_geometries(block):
                            return MultiPolygon(block.values)

                        g = df.groupby(by=by, group_keys=False)[df.geometry.name].agg(
                            merge_geometries
                        )

                        # Aggregate
                        aggregated_geometry = gpd.GeoDataFrame(g, geometry=df.geometry.name, crs=df.crs)
                        # Recombine
                        aggregated = aggregated_geometry.join(aggregated_data)
                        return aggregated

                    # grouped = groupby_multipoly(df, by='a')
                    def convert_polygons(geom):

                        if geom.geometryType() == "Polygon":
                            return MultiPolygon([geom])
                        else:
                            return geom
                        # return MultiPolygon(block.values)
                    
                    # g = df[df.geometry.name].agg(
                    #         merge_geometries
                    #     )
                    # df["multipolygon"] = df[df.geometry.name].apply(lambda g: convert_polygons(g))
                    # print(list(df[df.geometry.name]))
                    single_geom = unary_union(df[df.geometry.name])

                    result['geometry'] = single_geom.wkt

        return result
    
    def to_form(self):
        """ Prepares the raw backend data to populate an html form. """

        data = {}
        for k, v in self.to_json().items():
            value = "" if v is None else v
            if k == "references" and isinstance(value, dict):
                lines = ""
                for x, y in value.items():
                    lines += f"{x}:: {y}\n"
                value = lines
            if FIELD_LOOKUP[k]['multiple'] and isinstance(value, list):
                if FIELD_LOOKUP[k].get('widget') == "text-area.html":
                    value = "\n".join(value)
                else:
                    value = "|".join(value)
            data[k] = value
        return data

    def to_solr(self, enhance_geom=False):
        """A variation on to_json() that uses the SOLR uris instead, and
        omits empty fields. Plus some other value wrangling."""

        # use self.to_json() to parse all values, and then insert them into
        # a dictionary with the proper URIs as keys. The references field
        # must still be handled specially.
        json_doc = self.to_json(enhance_geom=enhance_geom)
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

    def index(self, solr_instance=None):
        solr_doc = self.to_solr()
        if not solr_instance:
            solr_instance = Solr()
        try:
            solr_instance.add(solr_doc)
            result = {
                "success": True,
                "document": solr_doc
            }
        except Exception as e:
            result = {
                "success": False,
                "error": str(e)
            }
        return result

    def export_to_staging(self):

        path = os.path.join(METADATA_DIR, 'staging', self.id + ".json")
        with open(path, "w") as f:
            json.dump(self.to_json(), f, indent=2)
