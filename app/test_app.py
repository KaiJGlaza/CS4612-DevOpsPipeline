"""Tests for app.py. Run them with: pytest"""

import re

import pytest

from app import app


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Give every test its own empty database in a temp folder."""
    db_path = tmp_path / "notes.db"
    monkeypatch.setenv("NOTES_DB", str(db_path))
    return db_path


@pytest.fixture
def client():
    return app.test_client()


def add_note(client, title, body=""):
    return client.post("/notes", json={"title": title, "body": body})


def test_home_page_is_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.mimetype == "text/html"


def test_health_check_says_ok(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_stylesheet_and_font_are_served(client):
    assert client.get("/static/style.css").status_code == 200
    font = client.get("/static/fonts/ibm-plex-sans-latin-400-normal.woff2")
    assert font.status_code == 200
    assert font.mimetype == "font/woff2"


# Storage

def test_database_file_is_created_on_first_note(client, temp_db):
    assert not temp_db.exists()
    add_note(client, "First")
    assert temp_db.exists()
    assert client.get("/notes").get_json()[0]["title"] == "First"


# Creating notes

def test_create_note(client):
    response = add_note(client, "Groceries", "milk")
    assert response.status_code == 201
    note = response.get_json()
    assert isinstance(note["id"], int)
    assert note["title"] == "Groceries"
    assert note["body"] == "milk"


def test_missing_title_is_rejected(client):
    response = client.post("/notes", json={"body": "no title"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert client.get("/notes").get_json() == []


def test_empty_title_is_rejected(client):
    response = add_note(client, "   ")
    assert response.status_code == 400
    assert client.get("/notes").get_json() == []


def test_non_json_body_is_rejected(client):
    response = client.post("/notes", data="just text", content_type="text/plain")
    assert response.status_code == 400
    assert "error" in response.get_json()


# Listing and fetching

def test_empty_list(client):
    response = client.get("/notes")
    assert response.status_code == 200
    assert response.get_json() == []


def test_notes_are_listed_in_creation_order(client):
    add_note(client, "A")
    add_note(client, "B")
    titles = [note["title"] for note in client.get("/notes").get_json()]
    assert titles == ["A", "B"]


def test_get_one_note(client):
    note_id = add_note(client, "Groceries", "milk").get_json()["id"]
    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    assert response.get_json() == {"id": note_id, "title": "Groceries", "body": "milk"}


def test_unknown_note_is_404(client):
    response = client.get("/notes/999")
    assert response.status_code == 404
    assert "error" in response.get_json()


# JSON search (the SQL injection target)

def test_search_finds_matching_note(client):
    add_note(client, "Groceries", "milk")
    add_note(client, "Homework", "math")
    results = client.get("/notes/search?q=Groc").get_json()
    assert [note["title"] for note in results] == ["Groceries"]


def test_search_without_query_returns_nothing(client):
    add_note(client, "Groceries")
    response = client.get("/notes/search")
    assert response.status_code == 200
    assert response.get_json() == []


def test_sql_injection_returns_no_extra_rows(client):
    add_note(client, "Groceries", "milk")
    add_note(client, "Homework", "math")
    response = client.get("/notes/search", query_string={"q": "' OR '1'='1"})
    assert response.status_code == 200
    assert response.get_json() == []


def test_sql_injection_cannot_drop_the_table(client):
    add_note(client, "Groceries")
    add_note(client, "Homework")
    response = client.get("/notes/search", query_string={"q": "'; DROP TABLE notes; --"})
    assert response.status_code == 200
    assert len(client.get("/notes").get_json()) == 2


# HTML search page (the XSS target)

def test_search_page_shows_matches(client):
    add_note(client, "Groceries")
    response = client.get("/search?q=Groc")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Groceries" in response.data


def test_script_in_search_term_is_escaped(client):
    response = client.get("/search", query_string={"q": "<script>alert(1)</script>"})
    assert b"&lt;script&gt;" in response.data
    assert b"<script>alert(1)</script>" not in response.data


def test_script_in_note_title_is_escaped(client):
    add_note(client, "<script>alert(1)</script>")
    response = client.get("/search?q=script")
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in response.data
    assert b"<script>alert(1)</script>" not in response.data


# Web UI: home page

def test_home_lists_notes_newest_first_with_links(client):
    first = add_note(client, "A").get_json()["id"]
    second = add_note(client, "B").get_json()["id"]
    html = client.get("/").get_data(as_text=True)
    assert html.index(">B<") < html.index(">A<")
    assert f'href="/note/{first}"' in html
    assert f'href="/note/{second}"' in html


def test_home_empty_state(client):
    html = client.get("/").get_data(as_text=True)
    assert "No notes yet" in html
    assert 'class="note-list"' not in html


# Web UI: note page

def test_note_page_shows_full_note_and_marks_it_current(client):
    note_id = add_note(client, "Groceries", "milk\neggs").get_json()["id"]
    response = client.get(f"/note/{note_id}")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<h1>Groceries</h1>" in html
    assert "milk\neggs" in html
    assert f'href="/note/{note_id}" aria-current="page"' in html


def test_unknown_note_page_is_404_with_link_home(client):
    response = client.get("/note/999")
    assert response.status_code == 404
    assert response.mimetype == "text/html"
    assert 'href="/"' in response.get_data(as_text=True)


# Web UI: new note form

def test_form_has_labeled_fields(client):
    html = client.get("/").get_data(as_text=True)
    assert '<label for="title">' in html
    assert '<label for="body">' in html


def test_form_creates_note_and_redirects_to_it(client):
    response = client.post("/note", data={"title": "Groceries", "body": "milk"})
    assert response.status_code == 303
    note = client.get("/notes").get_json()[0]
    assert response.headers["Location"] == f"/note/{note['id']}"
    assert note["title"] == "Groceries"
    assert ">Groceries<" in client.get("/").get_data(as_text=True)


def test_form_blank_title_shows_error_and_keeps_body(client):
    response = client.post("/note", data={"title": "  ", "body": "keep me"})
    html = response.get_data(as_text=True)
    assert response.status_code == 400
    assert 'class="field-error"' in html
    assert ">keep me</textarea>" in html
    assert client.get("/notes").get_json() == []


# Web UI: delete

def test_note_page_has_two_step_delete(client):
    note_id = add_note(client, "Groceries").get_json()["id"]
    html = client.get(f"/note/{note_id}").get_data(as_text=True)
    assert '<details class="delete">' in html
    assert f'action="/note/{note_id}/delete"' in html


def test_confirmed_delete_removes_note_and_redirects_home(client):
    note_id = add_note(client, "Groceries").get_json()["id"]
    response = client.post(f"/note/{note_id}/delete")
    assert response.status_code == 303
    assert response.headers["Location"] == "/"
    assert client.get("/notes").get_json() == []
    assert ">Groceries<" not in client.get("/").get_data(as_text=True)


def test_get_cannot_delete(client):
    note_id = add_note(client, "Groceries").get_json()["id"]
    client.get(f"/note/{note_id}/delete")
    assert client.get(f"/notes/{note_id}").status_code == 200


def test_delete_unknown_note_is_404(client):
    assert client.post("/note/999/delete").status_code == 404


# Web UI: search page

def test_search_page_uses_app_layout_and_links_results(client):
    note_id = add_note(client, "Groceries").get_json()["id"]
    html = client.get("/search?q=Groc").get_data(as_text=True)
    assert "Results for Groc" in html
    assert f'<a href="/note/{note_id}">Groceries</a>' in html
    assert 'class="app-header"' in html


def test_search_page_no_results_message(client):
    add_note(client, "Groceries")
    html = client.get("/search?q=zebra").get_data(as_text=True)
    assert "Results for zebra" in html
    assert "No notes found" in html


# Web UI: user text is always escaped

SCRIPT = "<script>alert(1)</script>"


def assert_escaped(html):
    assert "&lt;script&gt;" in html
    assert SCRIPT not in html


def test_script_note_is_escaped_on_every_page(client):
    note_id = add_note(client, SCRIPT, SCRIPT).get_json()["id"]
    for page in ["/", f"/note/{note_id}", "/search?q=script"]:
        assert_escaped(client.get(page).get_data(as_text=True))


def test_script_sent_back_after_form_error_is_escaped(client):
    response = client.post("/note", data={"title": "", "body": SCRIPT})
    assert response.status_code == 400
    assert_escaped(response.get_data(as_text=True))


# Web UI: pages are self-contained

def test_pages_have_no_scripts_or_outside_urls(client):
    note_id = add_note(client, "Groceries").get_json()["id"]
    for page in ["/", f"/note/{note_id}", "/search?q=Groc", "/note/999"]:
        html = client.get(page).get_data(as_text=True)
        assert "<script" not in html
        assert not re.search(r'(src|href)="https?://', html), page
