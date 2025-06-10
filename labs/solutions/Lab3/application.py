import os
import requests
from flask import Flask

application = Flask(__name__)
# Ensure the environment variable is set
if "BACKEND_API_URL" not in os.environ:
    raise EnvironmentError("BACKEND_API_URL environment variable is not set")

API_URL = os.environ.get("BACKEND_API_URL")

@application.route("/")
def index():
    try:
        res = requests.post(f"{API_URL}/record", json={"user": "sre-student"})
        return f"Backend Response: {res.text}"
    except Exception as e:
        return f"Error contacting backend: {e}", 500

