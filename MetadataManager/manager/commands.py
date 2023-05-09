import os
import click
from flask.cli import with_appcontext

from manager.service.ingest import Ingest

@click.command()
@with_appcontext
@click.option('--file_dir')
def ingest_aardvark(file_dir):

	from manager.app import PROJECT_DIR

	i = Ingest()
	if file_dir is None:
		file_dir = os.path.join(PROJECT_DIR, 'metadata', 'Aardvark')
	
	i.process_aardvark_files(file_dir)
