"""Sample web app for our Secure DevOps Pipeline project.

TODO (Elvin): grow this into a small app the security tests can target,
for example a notes API that saves to a database.
"""

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(message="Hello from the CS4612 DevOps Pipeline project")


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
