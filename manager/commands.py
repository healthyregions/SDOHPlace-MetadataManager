import json
import random
import string
from pathlib import Path

import click
from flask.cli import with_appcontext
from flask.cli import AppGroup

from werkzeug.security import generate_password_hash

from .solr import Solr
from .registry import Registry
from .models import db, User
from .utils import METADATA_DIR, batch_list

from .coverage.coverage import check_coverage

registry = Registry()

user_grp = AppGroup("user", help="A set of commands for managing users.")


@user_grp.command()
@with_appcontext
@click.argument("name")
@click.argument("email")
@click.argument("password")
def create(name: str, email: str, password: str):
    """Create a user"""

    hashed = generate_password_hash(password, method="pbkdf2:sha256")

    new_user = User(name=name, email=email, password=hashed)
    db.session.add(new_user)
    db.session.commit()

    print(email, hashed)


@user_grp.command()
@with_appcontext
@click.argument("email")
def reset_password(email):
    """Resets a user's password to a random 6 character string"""

    user = User.query.filter_by(email=email).first()

    raw = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    user.password = generate_password_hash(raw, method="pbkdf2:sha256")
    db.session.commit()

    print(raw)


@user_grp.command()
@with_appcontext
@click.argument("email")
@click.argument("password")
def change_password(email, password):
    """Changes a users password"""

    user = User.query.filter_by(email=email).first()

    user.password = generate_password_hash(password, method="pbkdf2:sha256")
    db.session.commit()


registry_grp = AppGroup(
    "registry",
    help="A set of commands for managing and indexing (to Solr) records in the registry.",
)


@registry_grp.command()
@with_appcontext
@click.option("--id")
def save_records(id):
    """Loads all records and performs save() on each one."""
    registry = Registry()

    if id:
        record = registry.get_record(id)
        if not record:
            print(f"record '{id}' not found. invalid id.")
            exit()
        records = [record]
    else:
        records = registry.records

    for r in records:
        print(f"saving: [{r.data['id']}] {r.data['title']}")
        r.save()

@registry_grp.command()
@with_appcontext
@click.option("--id")
@click.option("--verbose", is_flag=True, default=False)
def validate_records(id, verbose):
    """Loads all records and performs validate() on each one."""
    registry = Registry()

    if id:
        record = registry.get_record(id)
        if not record:
            print(f"record '{id}' not found. invalid id.")
            exit()
        records = [record]
    else:
        records = registry.records

    for r in records:
        print(f"validate: [{r.data['id']}] {r.data['title']}")
        errors = r.validate()
        if errors:
            print(f"{len(errors)} errors")
        if verbose:
            print(errors)

@registry_grp.command()
@with_appcontext
@click.option("--id")
@click.option("--clean", is_flag=True, default=False)
@click.option("--verbose", is_flag=True, default=False)
@click.option("--env", type=click.Choice(['stage', 'prod'], case_sensitive=False), default='prod', help="Target environment: stage or prod")
def index(id, clean, verbose, env):
    """Reindex all Solr records from database content."""

    s = Solr(environment=env, verbose=verbose)
    print(f"Indexing to {env} environment (core: {s.core})")
    
    if clean:
        del_result = s.delete_all()
        print(del_result)

    if id:
        record = registry.get_record(id)
        result = record.index(solr_instance=s)
    else:
        records = [r.to_solr() for r in registry.records]
        for batch in batch_list(records, 50):
            result = {
                "success": True,
                "document": f"{len(batch)} records",
            }
            try:
                s.multi_add(batch)
            except Exception as e:
                result["success"] = False
                result["error"] = e
    if not result["success"]:
        print(result)


@registry_grp.command()
@with_appcontext
@click.option(
    "-f", "--field", help="name of field to update, as it is stored in the JSON data"
)
# @click.option('--overwrite', is_flag=True, default=False, help="overwrite existing values in this field")
@click.option("--dry-run", is_flag=True, default=False, help="do not change any data")
@click.option("--old-value", help="the new value to save to the records")
@click.option("--new-value", help="only update fields that match this old value")
def bulk_update(
    field: str,
    # overwrite: bool=False,
    dry_run: bool = False,
    old_value: str = None,
    new_value: str = None,
):
    """Bulk update a field across all records. Optionally only update records with
    a specific existing value. When specifying values:

    "True" | "False"  will be cast as boolean values
    "None" will be cast as None (null)
    """

    print(f"update this field: {field}")
    record_files = Path(METADATA_DIR, "records").glob("*.json")
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


@registry_grp.command()
@with_appcontext
def inspect_schema():
    """Print a representation of the schema."""
    s = Registry().schema
    for dg in s.display_groups:
        print(f"\n## {dg['name']}")
        for f in dg["fields"]:
            print(f"- {f['label']}")


coverage_grp = AppGroup(
    "coverage",
    help="A set of commands for checking coverage of various study datasets.",
)


@coverage_grp.command()
@with_appcontext
@click.argument("input_file")
@click.argument("geography",
    type=click.Choice([
        "state",
        "county",
        "tract",
        "blockgroup",
        "zcta",
    ], case_sensitive=False),
)
@click.option("-i", "--id_field",
    help="name of field in input file that has FIPS, GEOID, or HEROPID in it",
)
@click.option("--apply_to",
    help="name of field in input file that has FIPS, GEOID, or HEROPID in it",
)
def generate_highlight_ids(input_file, geography, id_field, apply_to):

    highlight_ids = check_coverage(input_file, geography, id_field)

    if apply_to:
        from .registry import Registry
        record = Registry().get_record(apply_to)
        if not record:
            print(f"no record exists matching this id: {apply_to}")
            exit()
        record.data["highlight_ids"] = highlight_ids
        record.save()
