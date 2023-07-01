import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from manager.routes import crud, ingest
from manager.model import db
from manager.commands import (
    migrate_legacy_markdown,
    load_from_staging,
    save_to_staging,
)
load_dotenv()

app = Flask(__name__)
CORS(app)

app.cli.add_command(migrate_legacy_markdown)
app.cli.add_command(load_from_staging)
app.cli.add_command(save_to_staging)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

database_file = f'sqlite:///{PROJECT_DIR}/dev.db'

# this tutorial has a more robust config class pattern
# https://towardsdatascience.com/building-a-crud-app-with-flask-and-sqlalchemy-1d082741bc2b

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = database_file

db.init_app(app)

if not os.path.exists(database_file):
    with app.app_context():
        db.create_all()

app.register_blueprint(ingest)
app.register_blueprint(crud)
