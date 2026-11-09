# 1. Sample app

**Owner:** Elvin · **Status:** in progress (the skeleton is on `main`; the notes API is being built on `elvin-notes-api`)

## In one sentence

A small Python web app that both pipelines build and ship. It's the target that the planted bugs go into.

## Where it lives

| File | What it is |
|---|---|
| `app/app.py` | The Flask web app |
| `app/test_app.py` | Automated tests (pytest), run by every pipeline |
| `app/requirements.txt` | Libraries the app uses (`flask`, `pytest`), with exact versions |
| `app/Dockerfile` | Packages the app into a container image |

## How it works

**Today:** two routes. `GET /` returns a hello message, and `GET /health` returns `{"status": "ok"}`.

**Planned (notes API):** a tiny notes service that saves to a SQLite database:

| Route | Does |
|---|---|
| `POST /notes` | Create a note (`title`, `body`) |
| `GET /notes` | List all notes |
| `GET /notes/<id>` | Get one note |
| `GET /notes/search?q=` | Search notes, returns JSON. **This is the SQL injection target** |
| `GET /search?q=` | Search results as an HTML page that echoes your search term. **This is the XSS target** |

On `main` the code is written safely:
- **Parameterized SQL:** the search term is passed to the database as data, never pasted into the SQL text.
- **Auto-escaped HTML:** Flask's templates turn `<script>` into harmless text.

The test branches each change **one line** to remove one of those protections, so the vulnerable diff is easy to show on a slide.

**The container** (`Dockerfile`):
- starts from the small official `python:3.13-slim` image
- installs the pinned libraries
- removes `pip`, because Trivy flagged the outdated libraries bundled inside it
- runs as a normal user (`appuser`), not root

## What it protects against

The app isn't a security control itself. It provides realistic attack surface, so the scanners have something real to catch:
- **SQL injection** (OWASP Top 10 A03: Injection)
- **Cross-site scripting** (also A03)

## How to demo it

```
cd app
pip install -r requirements.txt
python app.py                          # runs on http://localhost:5000
pytest                                 # run the tests
docker build -t cs4612-app . && docker run -p 5000:5000 cs4612-app
```

## Results so far

- The app builds and its tests pass in the secure deploy pipeline (`main`, Nov 6).

## Limitations

- The vulnerable search page is a **reflected** XSS (the search term is echoed straight back). We chose that because CodeQL's default checks follow user input from the request to the page, but not through a database. Stored XSS (malicious text saved in a note, then displayed later) would probably slip past CodeQL. That's worth mentioning as a limitation of static analysis.
- Routes must be written as `@app.route(...)`, not `@app.get(...)`/`@app.post(...)`, or CodeQL can't see XSS in them. See the talking point in [03-secret-and-code-scanning.md](03-secret-and-code-scanning.md).
- The database lives inside the container and is lost when the container restarts. That's fine for a demo.
