import os
import json
import random
import string
from pathlib import Path

import click
from flask.cli import with_appcontext
from flask.cli import AppGroup

from werkzeug.security import generate_password_hash, check_password_hash

from .solr import Solr
from .registry import Registry
from .models import db, User
from .utils import METADATA_DIR, generate_id

registry = Registry()


@click.command()
@with_appcontext
@click.option('-f', '--field', help="name of field to update, as it is stored in the JSON data")
#@click.option('--overwrite', is_flag=True, default=False, help="overwrite existing values in this field")
@click.option('--dry-run', is_flag=True, default=False, help="do not change any data")
@click.option('--old-value', help="the new value to save to the records")
@click.option('--new-value', help="only update fields that match this old value")
def bulk_update(
		field: str,
		#overwrite: bool=False,
		dry_run: bool=False,
		old_value: str=None,
		new_value: str=None,
	):
	"""Bulk update a field across all records. Optionally only update records with
	a specific existing value. When specifying values:

	"True" | "False"  will be cast as boolean values
	"None" will be cast as None (null)
	"""

	print(f"update this field: {field}")
	record_files = Path(METADATA_DIR, 'records').glob("*.json")
	updated_ct = 0
	to_update = []
	for f in record_files:
		print(f)
		with open(f, "r") as o:
			try:
				data = json.load(o)
			except json.decoder.JSONDecodeError:
				print("error reading that file, skipping")
				continue
		val = data.get(field, "<NOT PRESENT>")

		if val == "<NOT PRESENT>":
			to_update.append(f)
		else:
			if old_value and str(val) != old_value:
				continue
			to_update.append(f)
	print(f"{len(to_update)} records to update")
	if dry_run or not new_value:
		print("exit dry run, no records updated")
		return
	if new_value in ("None", "True", "False"):
		new_value = eval(new_value)
	for f in to_update:
		with open(f, "r") as o:
			data = json.load(o)
		data[field] = new_value
		with open(f, "w") as o:
			json.dump(data, o, indent=2)
	print("done")

@click.command()
@with_appcontext
@click.option('--id')
@click.option('--clean', is_flag=True, default=False)
@click.option('--verbose', is_flag=True, default=False)
def index(id, clean, verbose):
	"""Reindex all Solr records from database content."""

	s = Solr(verbose=verbose)
	if clean:
		del_result = s.delete_all()
		print(del_result)

	if id:
		record = registry.get_record(id)
		result = record.index(solr_instance=s)
	else:
		records = [r.to_solr() for r in registry.records]
		result = {
			"success": True,
			"document": f"{len(records)} records",
		}
		try:
			s.multi_add(records)
		except Exception as e:
			result['success'] = False
			result['error'] = e
	if not result['success']:
		print(result)


# @click.command()
# @with_appcontext
# @click.option('--record_id')
# def add_spatial_coverage(record_id):

# 	if record_id is None:
# 		records = registry.get_all()
# 	else:
# 		records = [registry.get(record_id)]

# 	sr_values = {}

# 	for r in records:
# 		resolutions = r.spatial_resolution
# 		if resolutions is None:
# 			continue
# 		for sr in resolutions.split("|"):
# 			pass
			# if not sr in sr_values:
			# 	val = get_spatial_coverage_values(sr)
			# 	sr_values[sr] = val


@click.command()
@with_appcontext
def inspect_schema():
	s = Registry().schema
	for dg in s.display_groups:
		print(f"\n## {dg['name']}")
		for f in dg['fields']:
			print(f"- {f['label']}")


@click.command()
@with_appcontext
def set_all_ids():

	print("WARNING: this command is in development and will change files. Aborting for now...")
	# exit()

	relation_fields = [
		"relation",
		"member_of",
		"is_part_of",
		"source",
		"is_version_of",
		"replaces",
		"is_replaced_by",
	]

	id_lookup = {}
	for r in registry.records:
		id = r.data["id"]
		id_lookup[id] = generate_id()

	for r in registry.records:
		r.data["id"] = id_lookup[r.data["id"]]
		for f in relation_fields:
			if isinstance(r.data[f], list):
				r.data[f] = [id_lookup[i] for i in r.data[f]]
		r.save_data()

	print(id_lookup)


# @click.command()
# @with_appcontext
# @click.option('-s', '--source')
# @click.option('-n', '--name')
# def load_schema(source, name):

# 	file_name = os.path.basename(source)
# 	new_schema = Schema(
# 		data_file=file_name,
# 		slug=os.path.splitext(file_name)[0],
# 		name=name,
# 	)

# 	db.session.add(new_schema)
# 	db.session.commit()

# @click.command()
# @with_appcontext
# def reset_records():
# 	""" Removes all DB Record objects and recreates them from files on disk."""

# 	confirm = input("delete all database records? This cannot be undone. Y/n ")
# 	if confirm.lower().startswith("n"):
# 		exit()

# 	for record in Record.query.all():
# 		db.session.delete(record)
# 	db.session.commit()
# 	for file_name in os.listdir(os.path.join(METADATA_DIR, 'records')):
# 		new_record = Record(
# 			data_file=file_name,
# 			schema_id=1,
# 			last_modified_by="Admin",
# 		)

# 		db.session.add(new_record)
# 		db.session.commit()

# @click.command()
# @with_appcontext
# def save_records():
# 	""" For all records load data and re-saves it, does not alter any SQLite rows. Helpful during development. """

# 	for record in Record.query.all():
# 		record.load_data()
# 		record.save_data()

@click.command()
@with_appcontext
@click.argument('email')
def reset_user_password(email):
	""" Set a user's password manually """

	user = User.query.filter_by(email=email).first()

	raw = ''.join(random.choices(string.ascii_uppercase +
							string.digits, k=6))

	user.password = generate_password_hash(raw, method='pbkdf2:sha256')
	db.session.commit()

	print(raw)

@click.command()
@with_appcontext
@click.argument('name')
@click.argument('email')
@click.argument('password')
def create_user(name: str, email: str, password: str):
	""" Create a user """

	hashed = generate_password_hash(password, method='pbkdf2:sha256')

	new_user = User(
		name=name,
		email=email,
		password=hashed
	)
	db.session.add(new_user)
	db.session.commit()

	print(email, hashed)


registry_grp = AppGroup('registry')

@registry_grp.command()
@with_appcontext
def resave_records():

	registry = Registry()
	for i in registry.records:
		i.save_data()
