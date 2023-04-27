import os
import json

project_dir = os.path.dirname(os.path.abspath(__file__))

def generate_field_lookup():

    lookup = dict()
    with open(os.path.join(project_dir, 'aardvark_fields.json'), 'r') as o:
        lookup.update(json.load(o))

    return lookup

FIELD_LOOKUP = generate_field_lookup()
