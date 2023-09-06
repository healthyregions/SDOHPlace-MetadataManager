import os
import json

from dotenv import load_dotenv

load_dotenv()

METADATA_DIR = os.getenv('METADATA_DIR')

def generate_field_lookup():
	""" Aggregates the field definition JSON from one or more JSON files,
	returns single dictionary."""
	lookup = dict()
	schema_files = [
		os.path.join(METADATA_DIR, 'aardvark_schema.json'),
		os.path.join(METADATA_DIR, 'sdohplace_schema.json'),
	]
	for path in schema_files:
		with open(path, 'r') as o:
			lookup.update(json.load(o))

	for k, v in lookup.items():
		v['column_name'] = k
	return lookup

FIELD_LOOKUP = generate_field_lookup()

# this allows us to set the order of the display groups
# (we want the Identifiers group at the top)
GROUPED_FIELD_LOOKUP = {
	"Identifiers": [],
	"Descriptive": [],
	"Credits": [],
	"Extra": [],
	"Categories": [],
	"Temporal": [],
	"Spatial": [],
	"Relations": [],
	"Rights": [],
	"Object": [],
	"Links": [],
	"Admin": [],
}
for k, v in FIELD_LOOKUP.items():
	GROUPED_FIELD_LOOKUP[v['display_group']].append(v)

def get_clean_field_from_form(form, field, field_def):
	""" This function has bespoke logic for handling specific fields. """

	value = form.get(field)
	if value == "":
		return None

	if field == "references":
		value_dict = {}
		items = [i.rstrip() for i in value.split("\n")]
		items = [i for i in items if i]
		for i in items:
			if "::" in i:
				kvs = i.split("::")
				value_dict[kvs[0]] = kvs[1].lstrip().rstrip()
		return value_dict

	if field_def['multiple']:
		if field_def.get('widget') == 'text-area.html':
			value = form.get(field)
			print(value)
			value = [i.rstrip() for i in value.split("\n")]
			value = [i for i in value if i]
			value = "|".join([i for i in value if i])
			return value
		else:
			return "|".join(form.getlist(field))

	if field_def['data_type'] == "boolean":
		if value == "on":
			return True
		elif value == "off":
			return False

	return value
	# raise Exception(f"unhandled field: {field}")

def clean_form_data(form):

	out_data = {}
	# interrogate the form by looking for all specific values in it
	for field, field_def in FIELD_LOOKUP.items():
		clean_value = get_clean_field_from_form(form, field, field_def)
		out_data[field] = clean_value
	
	return out_data

STATE_POSTAL = {
	'alabama': 'al',
	'alaska': 'ak',
	'arizona': 'az',
	'arkansas': 'ar',
	'california': 'ca',
	'colorado': 'co',
	'connecticut': 'cn',
	'delaware': 'de',
	'district of columbia': 'dc',
	'florida': 'fl',
	'georgia': 'ga',
	'hawaii': 'hi',
	'idaho': 'id',
	'illinois': 'il',
	'indiana': 'in',
	'iowa': 'ia',
	'kansas': 'ka',
	'kentucky': 'ky',
	'louisiana': 'la',
	'maine': 'me',
	'maryland': 'md',
	'massachusetts': 'ma',
	'michigan': 'mi',
	'minnesota': 'mn',
	'mississippi': 'ms',
	'missouri': 'mo',
	'montana': 'mt',
	'nebraska': 'ne',
	'nevada': 'nv',
	'new hampshire': 'nh',
	'new jersey': 'nj',
	'new mexico': 'nm',
	'new york': 'ny',
	'north carolina': 'nc',
	'north dakota': 'nd',
	'ohio': 'oh',
	'oklahoma': 'ok',
	'oregon': 'or',
	'pennsylvania': 'pa',
	'rhode island': 'ri',
	'south carolina': 'sc',
	'south dakota': 'sd',
	'tennessee': 'tn',
	'texas': 'tx',
	'utah': 'ut',
	'vermont': 'vt',
	'virginia': 'va',
	'washington': 'wa',
	'west virginia': 'wv',
	'wisconsin': 'wi',
	'wyoming': 'wy',
}
STATE_LOOKUP = { v.upper(): k for k, v in STATE_POSTAL.items() }
