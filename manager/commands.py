import os
import click
from flask.cli import with_appcontext

from .model import RecordModel
from .service.solr import Solr

from manager.service.ingest import Ingest
from manager.utils import METADATA_DIR

@click.command()
@with_appcontext
@click.option('--file_dir')
def migrate_legacy_markdown(file_dir):
	"""Parse and load the legacy metadata markdown files from 2022-23."""

	staging_dir = os.path.join(METADATA_DIR, 'staging')

	i = Ingest()
	if file_dir is None:
		file_dir = os.path.join(METADATA_DIR, 'legacy', 'Aardvark')
	
	i.process_aardvark_files(file_dir, staging_dir)

@click.command()
@with_appcontext
@click.option('--clean-db', is_flag=True, default=False)
@click.option('--clean-index', is_flag=True, default=False)
def load_from_staging(clean_db, clean_index):
	"""Reset all database content from the local JSON files."""
	i = Ingest()
	i.load_from_staging(os.path.join(METADATA_DIR, 'staging'), clean_db=clean_db, clean_index=clean_index)

@click.command()
@with_appcontext
@click.option('--all', is_flag=True, default=False)
@click.option('--clean', is_flag=True, default=False)
def index(all, clean):
	"""Reset all database content from the local JSON files."""

	s = Solr()
	if clean:
		s.delete_all()
	records = RecordModel.query.all()
	for r in records:
		result = r.index(solr_instance=s)
		if not result['success']:
			print(result)
			exit()

@click.command()
@with_appcontext
def save_to_staging():

	Ingest().save_to_staging()

@click.command()
@with_appcontext
@click.option('--record_id')
def add_spatial_coverage(record_id):

	if record_id is None:
		records = RecordModel.query.order_by('title').all()
	else:
		records = [RecordModel.query.order_by('title').get(record_id)]

	sr_values = {}

	for r in records:
		resolutions = r.spatial_resolution
		if resolutions is None:
			continue
		for sr in resolutions.split("|"):
			pass
			# if not sr in sr_values:
			# 	val = get_spatial_coverage_values(sr)
			# 	sr_values[sr] = val

@click.command()
@with_appcontext
def inspect_schema():

	from .model import Registry

	registry = Registry()
	registry.get_all()