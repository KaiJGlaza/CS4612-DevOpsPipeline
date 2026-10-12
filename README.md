# Secure DevOps Pipeline

CS 4612 group project · Kai, Elvin, Kofi, Phillip

We build two pipelines for the same small app, one unsecured and one with security scans, and compare what each one catches.

## Who does what

| Person | Your files | Job |
|---|---|---|
| Elvin | `app/` · `unsecured-pipeline.yml` · `deploy.yml` | Sample app + unsecured pipeline |
| Kofi | `secret-and-code-scan.yml` | Gitleaks + CodeQL |
| Phillip | `dependency-and-container-scan.yml` | Trivy |
| Kai | `docs/threat-model.md` · `docs/repo-settings.md` | Threat model + GitHub settings |

Look for `TODO` in your file. The `.yml` files are instructions GitHub runs automatically on every pull request. They live in `.github/workflows/` (on a Mac, press Cmd + Shift + . to see hidden folders).

## How to make a change

1. Open your file on GitHub and click the pencil icon.
2. Click **Commit changes** → **Create a new branch** → **Propose changes** → **Create pull request**.
3. Get a teammate to approve it, then click **Merge**.

Never edit `main` directly.

## Dates

Demo ready: **Sun Nov 8** · Report due: **Fri Dec 4**
