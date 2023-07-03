import os
import click
from flask.cli import with_appcontext
from dotenv import load_dotenv

load_dotenv()

METADATA_DIR = os.getenv("METADATA_DIR")

from manager.service.ingest import Ingest

@click.command()
@with_appcontext
@click.option('--file_dir')
def migrate_legacy_markdown(file_dir):

	
	staging_dir = os.path.join(METADATA_DIR, 'staging')

	i = Ingest()
	if file_dir is None:
		file_dir = os.path.join(METADATA_DIR, 'legacy', 'Aardvark')
	
	i.process_aardvark_files(file_dir, staging_dir)

@click.command()
@with_appcontext
def load_from_staging():

	i = Ingest()
	i.load_from_staging(os.path.join(METADATA_DIR, 'staging'))

@click.command()
@with_appcontext
def save_to_staging():

	Ingest().save_to_staging()