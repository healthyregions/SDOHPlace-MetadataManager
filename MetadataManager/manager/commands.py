import os
import click
from flask.cli import with_appcontext

from manager.service.ingest import Ingest

@click.command()
@with_appcontext
@click.option('--file_dir')
def migrate_legacy_markdown(file_dir):

	from manager.app import PROJECT_DIR
	staging_dir = os.path.join(PROJECT_DIR, 'metadata', 'staging')

	i = Ingest()
	if file_dir is None:
		file_dir = os.path.join(PROJECT_DIR, 'metadata', 'legacy', 'Aardvark')
	
	i.process_aardvark_files(file_dir, staging_dir)

@click.command()
@with_appcontext
def load_from_staging():

	from manager.app import PROJECT_DIR

	i = Ingest()
	i.load_from_staging(os.path.join(PROJECT_DIR, 'metadata', 'staging'))

@click.command()
@with_appcontext
def save_to_staging():

	Ingest().save_to_staging()