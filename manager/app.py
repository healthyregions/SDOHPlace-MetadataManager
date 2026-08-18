import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager, current_user

from manager.blueprints.crud import crud
from manager.blueprints.auth import auth, is_admin_user, is_keycloak_configured
from manager.blueprints.submissions import submissions
from manager.models import db, User
from manager.commands import (
    user_grp,
    registry_grp,
    coverage_grp,
)

load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

DISCOVERY_APP_URL = os.getenv("DISCOVERY_APP_URL")
MANAGER_PUBLIC_URL = os.getenv("MANAGER_PUBLIC_URL")
INTAKE_API_BASE_URL = os.getenv("INTAKE_API_BASE_URL")

SOLR_HOST = os.getenv("SOLR_HOST", "").rstrip("/")
SOLR_CORE = os.getenv("SOLR_CORE", "").rstrip("/")  # Legacy support
SOLR_CORE_DEV = os.getenv("SOLR_CORE_DEV", "blacklight-core-dev").rstrip("/")
SOLR_CORE_PROD = os.getenv("SOLR_CORE_PROD", "blacklight-core-prod").rstrip("/")
MODE = os.getenv("MODE", "prod").lower()

# Legacy URL for backward compatibility
SOLR_URL = f"{SOLR_HOST}/{SOLR_CORE}/" if SOLR_CORE else f"{SOLR_HOST}/{SOLR_CORE_PROD}/"

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{PROJECT_DIR}/data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

app.secret_key = os.getenv("SECRET_KEY")
CORS(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.cli.add_command(user_grp)
app.cli.add_command(registry_grp)
app.cli.add_command(coverage_grp)

app.config["DEBUG"] = True

app.register_blueprint(auth)
app.register_blueprint(crud)
app.register_blueprint(submissions)


@app.context_processor
def get_context():
    if SOLR_CORE:
        active_core = SOLR_CORE
    elif MODE == "dev":
        active_core = SOLR_CORE_DEV
    else:
        active_core = SOLR_CORE_PROD
    solr_active_env = "dev" if active_core == SOLR_CORE_DEV else "prod"
    return dict(
        discovery_app_url=DISCOVERY_APP_URL,
        manager_public_url=MANAGER_PUBLIC_URL,
        is_admin_user=is_admin_user,
        keycloak_configured=is_keycloak_configured(),
        intake={
            "base_url": INTAKE_API_BASE_URL,
        },
        solr={
            "host": SOLR_HOST,
            "core": SOLR_CORE,  # Legacy
            "core_dev": SOLR_CORE_DEV,
            "core_prod": SOLR_CORE_PROD,
            "active_core": active_core,
            "active_env": solr_active_env,
        },
        user=current_user,
    )
