# Secure DevOps Pipeline

CS 4612 group project · Kai, Elvin, Kofi, Phillip

We build two pipelines for the same small app and compare them:

    Unsecured:  test → build → ship                               (ships anything)
    Secured:    test → SCAN → build → TEAMMATE APPROVES → ship    (bad code gets stopped)

Then we plant bad code on purpose and show that the unsecured pipeline ships it and the secured one blocks it.

## Who does what

Everyone builds one piece, runs 3 tests, writes their own report section, and has one team job.

| Person | Builds | Tests | Writes | Team job |
|---|---|---|---|---|
| Elvin | Sample app (`app/`) + unsecured pipeline | SQL injection · XSS · time both pipelines | Intro + results | Results chart |
| Kofi | Secret scan (Gitleaks) + code scan (CodeQL) | Fake API key · fake encryption key · key hidden in an old commit | Background + secret/code scanning | Assemble the report |
| Phillip | Library + container scan (Trivy) | Outdated library · outdated base image · app running as root | Library/container scanning + limitations | Assemble the slides |
| Kai | Secure deploy (teammate approval, locked deploy secrets) + GitHub rules | Merge with a failing scan · approve your own deploy · steal the deploy secret from a pull request | Threat model + secure deploy | Professor contact + weekly check-ins |

Pipeline files must go in a `.github/workflows/` folder. GitHub only runs them from there.

## How to make a change

1. Open the file on GitHub and click the pencil icon.
2. Click **Commit changes** → **Create a new branch** → **Propose changes** → **Create pull request**.
3. Get a teammate to approve it, then click **Merge**.

Never edit `main` directly.

## Deadlines

| By | Done |
|---|---|
| Sun Oct 25 | Everyone's build piece works |
| Sun Nov 1 | All bad code planted on test branches |
| Sun Nov 8 | All tests run and recorded, slides done, demo ready |
| Fri Dec 4 | Report submitted |
