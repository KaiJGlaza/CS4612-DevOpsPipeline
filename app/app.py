"""Sample web app for our Secure DevOps Pipeline project.

A small notes app that saves to a SQLite database: a web UI for people and
a JSON API. The search routes are the targets for the planted SQL injection
and XSS test branches, so on main they are written the safe way.
"""

import mimetypes
import os
import sqlite3

from flask import Flask, g, jsonify, redirect, render_template, request, url_for

# Slim Python images don't know .woff2, so fonts would be sent as a generic download
mimetypes.add_type("font/woff2", ".woff2")

app = Flask(__name__)


def get_db():
    """Open the database once per request. NOTES_DB sets where the file lives."""
    if "db" not in g:
        g.db = sqlite3.connect(os.environ.get("NOTES_DB", "notes.db"))
        g.db.row_factory = sqlite3.Row
        g.db.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL)"
        )
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def search_notes(q):
    """Notes whose title or body contains q. The ? placeholders keep q as data, never SQL."""
    if not q:
        return []
    pattern = f"%{q}%"
    rows = get_db().execute(
        "SELECT id, title, body FROM notes WHERE title LIKE ? OR body LIKE ? ORDER BY id",
        (pattern, pattern),
    )
    return [dict(row) for row in rows]


def add_note(title, body):
    db = get_db()
    cursor = db.execute("INSERT INTO notes (title, body) VALUES (?, ?)", (title, body))
    db.commit()
    return cursor.lastrowid


def render_page(template, status=200, **context):
    """Render a UI page. Every page shows the notes list, newest first."""
    rows = get_db().execute("SELECT id, title, body FROM notes ORDER BY id DESC")
    context.setdefault("q", "")
    context.setdefault("current_id", None)
    return render_template(template, notes=[dict(row) for row in rows], **context), status


# Routes use @app.route, not the @app.get/@app.post shorthand. CodeQL only
# recognizes @app.route handlers as web responses, so the shorthand hides XSS.

# Web UI

@app.route("/")
def home():
    return render_page("home.html", form={}, error=None)


@app.route("/note", methods=["POST"])
def create_note_form():
    title = request.form.get("title", "")
    body = request.form.get("body", "")
    if not title.strip():
        return render_page("home.html", 400, form=request.form, error="Give your note a title.")
    note_id = add_note(title, body)
    return redirect(url_for("view_note", note_id=note_id), code=303)


@app.route("/note/<int:note_id>")
def view_note(note_id):
    row = get_db().execute(
        "SELECT id, title, body FROM notes WHERE id = ?", (note_id,)
    ).fetchone()
    if row is None:
        return render_page("not_found.html", 404)
    return render_page("note.html", note=dict(row), current_id=note_id)


@app.route("/note/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):
    db = get_db()
    cursor = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    if cursor.rowcount == 0:
        return render_page("not_found.html", 404)
    return redirect(url_for("home"), code=303)


@app.route("/search")
def search_page():
    # render_template escapes q and the titles, so <script> shows up as text
    q = request.args.get("q", "")
    return render_page("search.html", q=q, results=search_notes(q))


# JSON API

@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="send a JSON object"), 400
    title = data.get("title")
    body = data.get("body", "")
    if not isinstance(title, str) or not title.strip():
        return jsonify(error="title is required"), 400
    if not isinstance(body, str):
        return jsonify(error="body must be text"), 400

    return jsonify(id=add_note(title, body), title=title, body=body), 201


@app.route("/notes")
def list_notes():
    rows = get_db().execute("SELECT id, title, body FROM notes ORDER BY id")
    return jsonify([dict(row) for row in rows])


@app.route("/notes/<int:note_id>")
def get_note(note_id):
    row = get_db().execute(
        "SELECT id, title, body FROM notes WHERE id = ?", (note_id,)
    ).fetchone()
    if row is None:
        return jsonify(error="note not found"), 404
    return jsonify(dict(row))


@app.route("/notes/search")
def search_json():
    return jsonify(search_notes(request.args.get("q", "")))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
