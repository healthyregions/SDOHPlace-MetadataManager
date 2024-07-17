import os
import csv
import sys
import json
from datetime import datetime
from flask_login import UserMixin
from dotenv import load_dotenv

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column

from manager.utils import METADATA_DIR, get_clean_field_from_form
from manager.solr import Solr

csv.field_size_limit(sys.maxsize)

load_dotenv()

db = SQLAlchemy()

class User(UserMixin, db.Model):

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str]

class Schema(db.Model):

    id: Mapped[int] = mapped_column(primary_key=True)
    data_file: Mapped[str] = mapped_column(unique=True)
    slug: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]

    @property
    def file_path(self):
        return os.path.join(METADATA_DIR, 'schemas', self.data_file)
    
    @property
    def schema_json(self):
        schema_json = {}
        with open(self.file_path, 'r') as o:
            schema_json = json.load(o)
        return schema_json

    @property
    def lookup(self):

        lookup_dict = {}
        for f in self.schema_json['fields']:
            field = Field(**f)
            lookup_dict[f['id']] = field
        return lookup_dict
    
    @property
    def fields(self):
        return list(self.lookup.values())
    
    @property
    def display_groups(self):
        gl = []
        for f in self.schema_json['display_groups']:
            f['fields'] = [i for i in self.schema_json['fields'] if i['display_group'] == f['name']]
            gl.append(f)

        return gl
    
    def get_blank_record(self):

        blank = {}
        for k, v in self.lookup.items():
            if v.multiple:
                val = []
            elif k == "references":
                val = {}
            else:
                val = None
            blank[k] = val
        return blank
    
    def get_blank_form(self):

        form = self.get_blank_record()
        for k in form.keys():
            form[k] = ""
        return form
    
    def validate_form_data(self, form_data):

        cleaned_data = {}
        for field, field_def in self.lookup.items():
            clean_value = get_clean_field_from_form(form_data, field, field_def)
            cleaned_data[field] = clean_value
        errors = []

        for key, field in self.lookup.items():
            value = cleaned_data.get(key)
            errors += field.validate(value)

        return errors


class Record(db.Model):

    id: Mapped[int] = mapped_column(primary_key=True)
    data_file: Mapped[str] = mapped_column(unique=True)
    schema_id: Mapped[int] = mapped_column(db.ForeignKey('schema.id'))
    last_modified_by: Mapped[str] = mapped_column(nullable=True)

    data = None

    def load_data(self):

        print("loading data")
        if self.data is None and self.file_path:
            print("loading file")
            with open(self.file_path, "r") as o:
                self.data = json.load(o)

    def save_data(self, index=False):
        self.data['metadata_version'] = "SDOH PlaceProject"
        self.data['modified'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(self.file_path, "w") as o:
            json.dump(self.to_json(), o, indent=2)
        
        if index:
            self.index()

    @property
    def schema(self):
        return Schema.query.get(self.schema_id)
    
    @property
    def file_path(self):
        path = None
        if self.data_file:
            path = os.path.join(METADATA_DIR, 'records', self.data_file)
        return path

    def get_value(self, field_name):
        return self.data[field_name]

    def validate(self):
        """ validate this record against its schema. """
        self.load_data()
        errors = []
        for key, field in self.schema.lookup.items():
            value = self.data.get(key)
            errors += field.validate(value)
        return errors
    
    def to_json(self):
        self.load_data()
        data = self.data

        obligations = ['required', 'suggested']
        rs_fields = [i for i in self.schema.fields if i.obligation in obligations]
        required_filled = len([i for i in rs_fields if data[i.id]])
        filled_pct = int(round((required_filled / len(rs_fields)) * 100, 2))
        if filled_pct >= 90:
            css_color = "success"
        elif filled_pct >= 75:
            css_color = "warning"
        else:
            css_color = "danger"

        data['meta'] = {
            'last_modified_by': self.last_modified_by,
            'filled': required_filled,
            'to_fill': len(rs_fields),
            'filled_pct': filled_pct,
            'progress_class': css_color,
        }

        return self.data

    def to_form(self):
        """ Prepares the raw backend data to populate an html form. """
        self.load_data()
        form_data = {}
        for key, field in self.schema.lookup.items():
            value = self.data.get(key)
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
            form_data[key] = value
        return form_data
    
    def to_solr(self):
        """A variation on to_json() that uses the SOLR uris instead, and
        omits empty fields. Plus some other value wrangling."""
        self.load_data()
        solr_doc = {}
        for key, field in self.schema.lookup.items():
            value = self.data.get(key)
            if value is not None:
                if key == "references":
                    value = json.dumps(value)
                solr_doc[field.uri] = value
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
    
    def save_from_form_data(self, form_data):
        cleaned_data = {}
        for field, field_def in self.schema.lookup.items():
            clean_value = get_clean_field_from_form(form_data, field, field_def)
            cleaned_data[field] = clean_value
        cleaned_data['metadata_version'] = "SDOH PlaceProject"
        cleaned_data['modified'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        if self.data_file:
            outpath = os.path.join(METADATA_DIR, 'records', self.data_file)
        else:
            self.data_file = cleaned_data['id'] + ".json"
            outpath = os.path.join(METADATA_DIR, 'records', self.data_file)
        with open(outpath, "w") as o:
            json.dump(cleaned_data, o, indent=2)


class Field():

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def validate(self, value):

        if self.label == "Modified":
            return []

        errors = []
        if isinstance(value, list):
            if self.obligation == "required" and not len(value) > 0:
                msg = f"{self.label} -- missing required value"
                errors.append(msg)
            values_list = value
            if not self.multiple:
                msg = f"{self.label} -- Multi-value not allowed. Got: {value}"
                errors.append(msg)
        else:
            values_list = [value]
        for val in values_list:
            if self.obligation == "required" and not val:
                msg = f"{self.label} -- missing required value"
                errors.append(msg)
            if val and (self.controlled and val not in self.controlled_options):
                msg = f"{self.label} -- {val} not in list of acceptable values"
                errors.append(msg)
        return errors


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