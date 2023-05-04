import os
from dotenv import load_dotenv

from manager.app import app

load_dotenv()

mode = os.getenv("MODE", "prod")

if mode == "prod":
    app.run("0.0.0.0", 80)
else:
    app.run(debug=True, host='127.0.0.1', port=5000)
