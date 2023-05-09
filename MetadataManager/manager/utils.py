import os
import json

project_dir = os.path.dirname(os.path.abspath(__file__))

def generate_field_lookup():
	""" Aggregates the field definition JSON from one or more JSON files,
	returns single dictionary."""
	lookup = dict()
	with open(os.path.join(project_dir, 'metadata', 'Aardvark', '_fields.json'), 'r') as o:
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

def clean_form_data(form):

	out_data = {}
	# interrogate the form by looking for all specific values in it
	for field, field_def in FIELD_LOOKUP.items():
		if field_def['multiple']:
			value = "|".join(form.getlist(field))
		else:
			value = form.get(field)
		if value == "" or value == []:
			value = None

		if field == "references" and value:
			value = json.loads(value.replace("'",'"'))

		if field_def['data_type'] == "boolean":
			if value == "on":
				value = True
			elif value == "off":
				value = False

		out_data[field] = value
	
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
