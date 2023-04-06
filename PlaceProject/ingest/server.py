from flask import Flask
from flask_cors import CORS
from controller.ingest import ingest

app = Flask(__name__)
CORS(app)

app.register_blueprint(ingest)

app.run("0.0.0.0", 80)
