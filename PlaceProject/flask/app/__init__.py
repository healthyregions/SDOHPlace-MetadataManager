import os
from flask import Flask
from flask_cors import CORS
from app.controller.ingest import ingest
from app.controller.manager import manager

from app.schema import db

app = Flask(__name__)
CORS(app)

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = f'sqlite:///{project_dir}/dev.db'

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
app.register_blueprint(manager)
