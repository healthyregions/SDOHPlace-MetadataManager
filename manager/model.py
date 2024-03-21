import os
import csv
import sys
import json
from pathlib import Path
from datetime import datetime
from flask_login import UserMixin
from dotenv import load_dotenv

from manager.utils import METADATA_DIR, get_clean_field_from_form
from manager.solr import Solr

csv.field_size_limit(sys.maxsize)

load_dotenv()

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
        record_file = Path(METADATA_DIR, "records", self.id+".json")
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
            os.path.join(METADATA_DIR, 'schemas', 'aardvark_schema.json'),
            os.path.join(METADATA_DIR, 'schemas', 'sdohplace_schema.json'),
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

        record_file = Path(METADATA_DIR, "records", record_id+".json")
        if not record_file.is_file():
            return None

        record = self.load_record_from_file(record_file)

        if format == "json":
            return record.to_json()
        elif format == "solr":
            return record.to_solr()
        elif format == "form-data":
            return record.to_form()
        else:
            return record

    def get_all(self, format: str = None, sort_by: str = "title"):

        files = Path(METADATA_DIR, "records").glob("*.json")
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

"""
retain geom snippet

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

"""