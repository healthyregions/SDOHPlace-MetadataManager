import click
from flask.cli import with_appcontext

from .solr import Solr

from .models import Registry

registry = Registry()


@click.command()
@with_appcontext
@click.option('--all', is_flag=True, default=False)
@click.option('--clean', is_flag=True, default=False)
def index(all, clean):
	"""Reset all database content from the local JSON files."""

	s = Solr()
	if clean:
		s.delete_all()
	records = registry.get_all()
	for r in records:
		result = r.index(solr_instance=s)
		if not result['success']:
			print(result)
			exit()


@click.command()
@with_appcontext
@click.option('--record_id')
def add_spatial_coverage(record_id):

	if record_id is None:
		records = registry.get_all()
	else:
		records = [registry.get(record_id)]

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

	registry.get_all()