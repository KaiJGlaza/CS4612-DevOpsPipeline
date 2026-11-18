# 3. Secret and code scanning (Gitleaks + CodeQL)

**Owner:** Kofi · **Status:** done (merged in PR #2)

## In one sentence

On every push and pull request, Gitleaks looks for passwords and keys committed by mistake, and CodeQL reads the code looking for security bugs such as injection.

## Where it lives

| File | Tool | Check name (used by branch protection) |
|---|---|---|
| `.github/workflows/gitleaks.yml` | Gitleaks: secret scanning | `Gitleaks` |
| `.github/workflows/codeql.yml` | CodeQL: static analysis (SAST) | `CodeQL (python, none)`, `CodeQL (actions, none)` |

## How it works

**Gitleaks**
- Downloads the **entire git history** (`fetch-depth: 0`), not just the latest commit. A key that was committed and then "deleted" in a later commit is still in the history, and Gitleaks finds it there.
- Matches commits against hundreds of patterns for API keys, private keys, tokens and similar.
- If it finds anything, the check fails.

**CodeQL**
- Scans two languages:
  - **python:** the app code, for injection, XSS, unsafe Flask settings and similar.
  - **actions:** the workflow files themselves, for unsafe pipeline patterns such as untrusted input used in scripts or overly broad permissions.
- Uses `build-mode: none`, since Python doesn't need compiling.
- Traces where user input flows. If something from a request reaches a SQL query or an HTML response without being made safe, it raises an alert.
- Results appear under the repo's **Security → Code scanning** tab.

**Why at commit time:** these checks are fast and cheap, so they run first. That's the "shift left" idea in the proposal: catch problems at the earliest stage where they're detectable.

## What it protects against

- **CICD-SEC-6, Insufficient credential hygiene:** secrets committed to the repo.
- **Injection and XSS in app code** (OWASP Top 10 A03).
- **CICD-SEC-4, Poisoned pipeline execution:** CodeQL's `actions` scan flags risky workflow code.

## How to demo it

- **Secret:** push a branch containing a fake API key, and show Gitleaks failing and naming the file and line.
- **Old-commit secret:** add a key, then delete it in a second commit, and show Gitleaks still catching it.
- **Code:** push `test-elvin-sqli` and show CodeQL's SQL injection alert, which points at the vulnerable line.

## Results so far

- Passes on every clean branch (no false positives so far).
- No secret test branches have been run yet (fake API key, fake encryption key, key in an old commit).

## Talking point: CodeQL's blind spot depends on how routes are written

**The finding:** the same XSS bug was **missed or caught depending only on how the route was declared.** We tested it locally on Nov 8 with the CodeQL CLI (2.27.4, `codeql/python-queries` 1.9.0, the same `python-code-scanning` suite GitHub runs).

| How the bug was planted in `/search` | `@app.get("/search")` | `@app.route("/search")` |
|---|---|---|
| Return an f-string HTML page containing the search term | **missed** | caught: Reflected XSS |
| Render the styled page, then insert the raw search term | **missed** | caught: Reflected XSS |
| Wrap the term in `Markup()` and pass it to the template | missed | missed |
| `{{ q\|safe }}` in the HTML template | *not run.* Expected to be missed, since CodeQL doesn't analyze `.html` templates | *not run* |
| Build the template text from the search term | caught: Server-side template injection | *not run.* Not expected to depend on route style |
| Build the SQL query with an f-string | caught: SQL injection | *not run.* Not expected to depend on route style |

**Why:** CodeQL only treats a function's return value as "a web page sent to the browser" when it recognizes the function as a route. It recognizes Flask's `@app.route(...)`, but not the newer shorthand `@app.get(...)` / `@app.post(...)`. With the shorthand, user input still reaches the page, but CodeQL doesn't see the page as a dangerous destination, so it stays silent. It also never reads Jinja `.html` templates.

**What we did:** all routes in `app/app.py` use `@app.route(...)`, with a comment explaining why.

**What to say:**
- A security scanner passing doesn't prove the code is safe. A harmless style choice (`@app.get` vs `@app.route`) made the same vulnerability invisible.
- The **secured pipeline is only as good as the tool's model of your framework.** That's why the proposal layers controls: scanning, plus human review on every PR, plus escaping by default in the code.
- **We only found this because we tested the scanner** before trusting it. Without that, our XSS demo would have shipped through the secured pipeline too.

## Limitations

- **CodeQL's Flask model has blind spots:** routes written with `@app.get`/`@app.post`, `Markup()`, and anything inside templates (see the talking point above).
- Gitleaks only catches secrets that **look like** secrets. A password such as `hunter2` in a variable won't match any pattern.
- CodeQL doesn't follow data **through the database** (stored XSS), and it can report false positives.
- Some actions are referenced by version tag (`@v4`, `@v6`, `@v7`) instead of being locked to a specific commit. A compromised tag could change what runs, which is itself CICD-SEC-3.
- `gitleaks.yml` grants `pull-requests: write` to the whole workflow, and `codeql.yml` sets no top-level `permissions`. Both could be tightened for least privilege.
