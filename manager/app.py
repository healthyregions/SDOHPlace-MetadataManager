import os
import json

from dotenv import load_dotenv
from flask import (
    Flask,
    request,
    redirect,
    render_template_string,
    url_for,
)
from flask_cors import CORS
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from manager.routes import crud
from manager.model import User
from manager.commands import (
    add_spatial_coverage,
    index,
    inspect_schema,
)
load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)

# load user list from json file
users = {}
with open(f"{PROJECT_DIR}/users.json", "r") as o:
    # userdata = json.load(o)
    for u in json.load(o):
        users[u['id']] = User(u['id'], u['password'])

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

app.cli.add_command(index)
app.cli.add_command(add_spatial_coverage)
app.cli.add_command(inspect_schema)

app.config['DEBUG'] = True

app.register_blueprint(crud)

@app.get("/login")
def login():
    return """<form method=post>
      Email: <input name="email"><br>
      Password: <input name="password" type=password><br>
      <button>Log In</button>
    </form>"""

@app.post("/login")
def login_view():
    user = users.get(request.form["email"])

    if user is None or user.password != request.form["password"]:
        return redirect(url_for("login"))

    login_user(user)
    return redirect(url_for("manager.index"))

@app.route("/protected")
@login_required
def protected():
    return render_template_string(
        "Logged in as: {{ user.id }}",
        user=current_user
    )

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("manager.index"))
