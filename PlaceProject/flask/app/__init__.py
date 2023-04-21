from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from app.controller.ingest import ingest

load_dotenv()

app = Flask(__name__)
CORS(app)

app.register_blueprint(ingest)