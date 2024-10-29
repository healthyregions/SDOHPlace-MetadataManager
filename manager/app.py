import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager, current_user

from manager.blueprints.crud import crud
from manager.blueprints.auth import auth
from manager.models import db, User
from manager.commands import (
    index,
    inspect_schema,
    load_schema,
    save_records,
    reset_records,
    reset_user_password,
    bulk_update,
    set_all_ids,
    create_user,
)
load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

GBL_HOST = os.getenv("GBL_HOST").rstrip("/")

DISCOVERY_APP_URL = os.getenv("DISCOVERY_APP_URL")

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
app.cli.add_command(inspect_schema)
app.cli.add_command(load_schema)
app.cli.add_command(save_records)
app.cli.add_command(reset_records)
app.cli.add_command(create_user)
app.cli.add_command(reset_user_password)
app.cli.add_command(bulk_update)
app.cli.add_command(set_all_ids)

app.config['DEBUG'] = True

app.register_blueprint(auth)
app.register_blueprint(crud)

@app.context_processor
def get_context():
	return dict(
		gbl_host=GBL_HOST,
        discovery_app_url=DISCOVERY_APP_URL,
		solr={"host":SOLR_HOST,"core":SOLR_CORE},
        user=current_user,
	)
