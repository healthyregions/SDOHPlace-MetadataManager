import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager, current_user

from manager.blueprints.crud import crud
from manager.blueprints.auth import auth
from manager.models import db, User
from manager.commands import (
    add_spatial_coverage,
    index,
    inspect_schema,
    load_schema,
    load_records,
)
load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

GBL_HOST = os.getenv("GBL_HOST").rstrip("/")

SOLR_HOST = os.getenv('SOLR_HOST', '').rstrip('/')
SOLR_CORE = os.getenv('SOLR_CORE', '').rstrip('/')

SOLR_URL = f"{SOLR_HOST}/{SOLR_CORE}/"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{PROJECT_DIR}/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
 
with app.app_context():
    db.create_all()

app.secret_key = os.getenv("SECRET_KEY")
CORS(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.cli.add_command(index)
app.cli.add_command(add_spatial_coverage)
app.cli.add_command(inspect_schema)
app.cli.add_command(load_schema)
app.cli.add_command(load_records)

app.config['DEBUG'] = True

app.register_blueprint(auth)
app.register_blueprint(crud)

@app.context_processor
def get_context():
	return dict(
		gbl_host=GBL_HOST,
		solr={"host":SOLR_HOST,"core":SOLR_CORE},
        user=current_user,
	)
