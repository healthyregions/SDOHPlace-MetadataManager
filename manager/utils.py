import os

from dotenv import load_dotenv

load_dotenv()

METADATA_DIR = os.path.join(os.path.dirname(__file__), "metadata")

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

	if field_def.multiple:
		if field_def.widget == "select.html":
			value = form.getlist(field)
		if field_def.widget == 'text-area.html':
			value = form.get(field)
			value = [i.rstrip() for i in value.split("\n")]
			value = [i for i in value if i]
			return value

	if field_def.data_type == "boolean":
		if value == "on":
			return True
		elif value == "off":
			return False

	return value

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

STATE_FP_LOOKUP = {
	'01':'Alabama',
	'02':'Alaska',
	'04':'Arizona',
	'05':'Arkansas',
	'06':'California',
	'08':'Colorado',
	'09':'Connecticut',
	'10':'Delaware',
	'11':'District of Columbia',
	'12':'Florida',
	'13':'Georgia',
	'15':'Hawaii',
	'16':'Idaho',
	'17':'Illinois',
	'18':'Indiana',
	'19':'Iowa',
	'20':'Kansas',
	'21':'Kentucky',
	'22':'Louisiana',
	'23':'Maine',
	'24':'Maryland',
	'25':'Massachusetts',
	'26':'Michigan',
	'27':'Minnesota',
	'28':'Mississippi',
	'29':'Missouri',
	'30':'Montana',
	'31':'Nebraska',
	'32':'Nevada',
	'33':'New Hampshire',
	'34':'New Jersey',
	'35':'New Mexico',
	'36':'New York',
	'37':'North Carolina',
	'38':'North Dakota',
	'39':'Ohio',
	'40':'Oklahoma',
	'41':'Oregon',
	'42':'Pennsylvania',
	'72':'Puerto Rico',
	'44':'Rhode Island',
	'45':'South Carolina',
	'46':'South Dakota',
	'47':'Tennessee',
	'48':'Texas',
	'49':'Utah',
	'50':'Vermont',
	'51':'Virginia',
	'78':'Virgin Islands',
	'53':'Washington',
	'54':'West Virginia',
	'55':'Wisconsin',
	'56':'Wyoming',
}

COUNTY_LSAD_LOOKUP = {
	"00": "",
	"03": "City and Borough",
	"04": "Borough",
	"05": "Census Area",
	"06": "County",
	"12": "Municipality",
	"15": "Parish",
	"25": "city",
}