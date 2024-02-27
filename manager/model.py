import os
import csv
import sys
import json
from pathlib import Path
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely import unary_union

from manager.utils import METADATA_DIR, FIELD_LOOKUP, STATE_FP_LOOKUP, COUNTY_LSAD_LOOKUP

csv.field_size_limit(sys.maxsize)

load_dotenv()

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

    def export_to_staging(self):

        path = os.path.join(METADATA_DIR, 'staging', self.id + ".json")
        with open(path, "w") as f:
            json.dump(self.to_json(), f, indent=2)
