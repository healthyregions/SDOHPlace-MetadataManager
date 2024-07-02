import os
import click
from flask.cli import with_appcontext

from .solr import Solr

from .models import db, Schema, Record
from .utils import METADATA_DIR


@click.command()
@with_appcontext
@click.option('--all', is_flag=True, default=False)
@click.option('--clean', is_flag=True, default=False)
def index(all, clean):
	"""Reindex all Solr records from database content."""

	s = Solr()
	if clean:
		s.delete_all()
	for r in Record.query.all():
		result = r.index(solr_instance=s)
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

	s = Schema.query.get(1)
	for k, v in s.grouped_fields.items():
		print(f"\n## {k}")
		for f in v:
			print(f"- {f['label']}")


@click.command()
@with_appcontext
@click.option('-s', '--source')
@click.option('-n', '--name')
def load_schema(source, name):

	file_name = os.path.basename(source)
	new_schema = Schema(
		data_file=file_name,
		slug=os.path.splitext(file_name)[0],
		name=name,
	)

	db.session.add(new_schema)
	db.session.commit()

@click.command()
@with_appcontext
def reset_records():
	""" Removes all DB Record objects and recreates them from files on disk."""

	confirm = input("delete all database records? This cannot be undone. Y/n ")
	if confirm.lower().startswith("n"):
		exit()

	for record in Record.query.all():
		db.session.delete(record)
	db.session.commit()
	for file_name in os.listdir(os.path.join(METADATA_DIR, 'records')):
		new_record = Record(
			data_file=file_name,
			schema_id=1,
			last_modified_by="Admin",
		)

		db.session.add(new_record)
		db.session.commit()
