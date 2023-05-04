import os
import json

project_dir = os.path.dirname(os.path.abspath(__file__))

def generate_field_lookup():
	""" Aggregates the field definition JSON from one or more JSON files,
	returns single dictionary."""
	lookup = dict()
	with open(os.path.join(project_dir, 'metadata', 'Aardvark', 'aardvark_fields.json'), 'r') as o:
		lookup.update(json.load(o))

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
	v['column_name'] = k
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

		if field_def['data_type'] == "boolean":
			if value == "on":
				value = True
			elif value == "off":
				value = False
		print(field, value)
		out_data[field] = value
	
	return out_data