import json
import logging
from json import JSONDecodeError
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from manager.utils import (
    METADATA_DIR,
    get_clean_field_from_form,
    load_json,
    get_wkt_from_geojson,
    generate_id,
)
from manager.solr import Solr

load_dotenv()


class Schema:
    def __init__(self, file_path: Path):
        self.schema_json = load_json(file_path)

    @property
    def lookup(self):
        lookup_dict = {}
        for f in self.schema_json["fields"]:
            field = Field(**f)
            lookup_dict[f["id"]] = field
        return lookup_dict

    @property
    def fields(self):
        return list(self.lookup.values())

    @property
    def display_groups(self):
        gl = []
        for f in self.schema_json["display_groups"]:
            f["fields"] = [
                i for i in self.schema_json["fields"] if i["display_group"] == f["name"]
            ]
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
            if k == "id":
                form[k] = generate_id()
            else:
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

    def validate_record(self, record):

        errors = []
        extra = set(record.data.keys()) - set(self.lookup.keys())
        if extra:
            errors.append(f"{len(extra)} extra fields: ", extra)

        for id, field in self.lookup.items():
            result = field.validate(record.data[id])
            if result['is_valid']:
                errors.append(result['message'])

        return errors

    def make_record_from_form_data(self, form_data):

        data = {
            "metadata_version": self.schema_json["name"]
        }
        for field in self.lookup.values():
            clean_value = field.get_value_from_form(form_data)
            data[field] = clean_value

        return data


class Registry:
    def __init__(self):
        self.schema: Schema = Schema(Path(METADATA_DIR, "schemas", "sdohplace.json"))
        self.records: list[Record] = []
        self.load_all_records()
        self.record_lookup = {i.data["id"]: i for i in self.records}

    def load_all_records(self):
        files = Path(METADATA_DIR, "records").glob("*.json")
        for f in files:
            record = Record(self.schema).load_from_file(f)
            self.records.append(record)
        self.records.sort(
            key=lambda d: d.data["title"] if d.data["title"] else d.data["id"]
        )

    def get_record(self, id):
        files = Path(METADATA_DIR, "records").glob("*.json")
        record = None
        for f in files:
            loaded = Record(self.schema).load_from_file(f)
            if loaded.data["id"] == id:
                record = loaded
                break
        return record

    def records_as_json(self):
        return [r.to_json() for r in self.records]


class Record:
    def __init__(self, schema: Schema):
        self.file_path = None
        self.schema = schema
        self.data = {}

    def load_from_file(self, file_path):
        self.file_path = file_path
        self.data = load_json(file_path)
        return self

    def save_data(self, index=False):
        self.data["metadata_version"] = "SDOH PlaceProject"
        self.data["modified"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        ## Feb 5th 2025, we may need to show some child records afterall, removing this hard coding
        # if self.data['is_version_of']:
        #     self.data['suppressed'] = True
        # else:
        #     self.data['suppressed'] = False

        if self.data["index_year"]:
            self.data["index_year"] = [int(i) for i in self.data["index_year"]]

        if not self.file_path:
            self.file_path = Path(METADATA_DIR, "records", self.data["id"] + ".json")

        if self.data["references"]:
            cleaned_references = {}
            download_refs = []
            for (
                k,
                v,
            ) in self.data["references"].items():
                if k.startswith('download/'):
                    label = k.rstrip().lstrip()[9:]
                    url = v.rstrip().lstrip()
                    download_refs.append({'label': label, 'url': url})
                else:
                    cleaned_references[k.rstrip().lstrip()] = v.rstrip().lstrip()

            if len(download_refs) > 0:
                cleaned_references['http://schema.org/downloadUrl'] = download_refs
            self.data["references"] = cleaned_references

        coverages = (
            [i.lower() for i in self.data["spatial_coverage"]]
            if self.data["spatial_coverage"]
            else []
        )
        wkt = None
        if "united states" in coverages:
            wkt = get_wkt_from_geojson("full-us-simplified.geojson")
        elif "contiguous us" in coverages:
            wkt = get_wkt_from_geojson("contiguous-us-simplified.geojson")
        elif "alaska" in coverages:
            wkt = get_wkt_from_geojson("alaska-simplified.geojson")
        elif "hawaii" in coverages:
            wkt = get_wkt_from_geojson("hawaii-simplified.geojson")

        if wkt and (not self.data["geometry"] or self.data["geometry"] == "None"):
            self.data["geometry"] = wkt

        with open(self.file_path, "w") as o:
            json.dump(self.to_json(), o, indent=2)

        if index:
            self.index()

    def get_value(self, field_name):
        return self.data[field_name]

    def validateOLD(self):
        """validate this record against its schema."""
        errors = []
        for key, field in self.schema.lookup.items():
            value = self.data.get(key)
            print(key, field, value)
            errors += field.validate(value)
        return errors

    def validate(self):
        return self.schema.validate_record(self)

    def from_form_data(self, form_data):
        pass

    def to_json(self):
        obligations = ["required", "suggested"]
        rs_fields = [i for i in self.schema.fields if i.obligation in obligations]
        required_filled = len([i for i in rs_fields if self.data.get(i.id)])
        filled_pct = int(round((required_filled / len(rs_fields)) * 100, 2))
        if filled_pct >= 90:
            css_color = "success"
        elif filled_pct >= 75:
            css_color = "warning"
        else:
            css_color = "danger"

        meta = self.data.get(
            "_meta",
            {
                "to_fill": "",
                "filled": "",
                "filled_pct": "",
                "progress_class": "",
            },
        )
        meta["to_fill"] = len(rs_fields)
        meta["filled"] = required_filled
        meta["filled_pct"] = filled_pct
        meta["progress_class"] = css_color

        self.data["_meta"] = meta

        return self.data


    def to_form(self):
        """Prepares the raw backend data to populate an html form."""
        form_data = {}
        for key, field in self.schema.lookup.items():
            value = self.data.get(key)
            if not value:
                value = ""
            if key == "references" and isinstance(value, dict):
                lines = ""
                for x, y in value.items():
                    logging.warning(f'item - {x}:: {y}')
                    if x == 'http://schema.org/downloadUrl':
                        try:
                            if isinstance(y, list):
                                # downloadUrl is a list of objects defining label + url
                                # break it up into multiple lines of download/<label>:: <url>
                                for u in y:
                                    lines += f"download/{u['label']}:: {u['url']}\n"
                        except JSONDecodeError as ex:
                            # downloadUrl is a single string
                            lines += f"{x}:: {y}\n"
                    else:
                        lines += f"{x}:: {y}\n"
                value = lines
            if field.multiple and isinstance(value, list):
                if field.widget == "text-area.html":
                    value = "\n".join(value)
                else:
                    value = "|".join([str(i) for i in value])
            form_data[key] = value
        return form_data

    def to_solr(self):
        """A variation on to_json() that uses the SOLR uris instead, and
        omits empty fields. Plus some other value wrangling."""
        solr_doc = {}
        for key, field in self.schema.lookup.items():
            value = self.data.get(key)
            if value is not None and str(value).lower() != "none":
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
            result = {"success": True, "document": solr_doc}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        return result

    def save_from_form_data(self, form_data):
        cleaned_data = {}
        for field, field_def in self.schema.lookup.items():
            clean_value = get_clean_field_from_form(form_data, field, field_def)
            cleaned_data[field] = clean_value
        cleaned_data["metadata_version"] = "SDOH PlaceProject"
        cleaned_data["modified"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        self.data.update(cleaned_data)
        self.save_data()


class Field:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def get_value_from_form(self, form):
        """This function has bespoke logic for handling specific fields."""

        value = form.get(self.id)
        if value == "":
            value = None

        if self.widget == "checkboxes.html":
            value = [
                k.split("--")[1]
                for k, v in form.items()
                if k.split("--")[0] == self.id and v == "on"
            ]
            value = [i.lstrip().rstrip() for i in value]

        if self.id == "references":
            value_dict = {}
            items = [i.rstrip() for i in value.split("\n")]
            items = [i for i in items if i]
            for i in items:
                if "::" in i:
                    kvs = i.split("::")
                    value_dict[kvs[0]] = kvs[1].lstrip().rstrip()
            return value_dict

        if self.multiple:
            if (
                self.widget == "select.html"
                or self.widget == "select-record.html"
            ):
                value = form.getlist(self.id)
            if self.widget == "text-simple.html":
                value = [i.lstrip().rstrip() for i in form.get(self.id).split("|") if i]
            if self.widget == "text-area.html":
                value = form.get(self.id)
                value = [i.rstrip() for i in value.split("\n")]
                value = [i for i in value if i]

        if self.data_type == "boolean":
            if value == "on":
                value = True
            elif value == "off" or not value:
                value = False

        return value

    def validate(self, value):

        errors = []

        if self.label == "Modified":
            return errors

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
