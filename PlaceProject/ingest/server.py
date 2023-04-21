import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from controller.ingest import ingest

load_dotenv()

app = Flask(__name__)
CORS(app)

app.register_blueprint(ingest)

mode = os.getenv("MODE", "prod")

if mode == "prod":
    app.run("0.0.0.0", 80)
else:
    app.run(debug=True, host='127.0.0.1', port=5000)
