# Secure DevOps Pipeline

CS 4612 group project · Kai, Elvin, Kofi, Phillip

We build two pipelines for the same small app, one unsecured and one with security scans, and compare what each one catches.

## Who does what

| Person | Job |
|---|---|
| Elvin | Sample app (`app/`) + unsecured pipeline |
| Kofi | Secret scanning (Gitleaks) + code scanning (CodeQL) |
| Phillip | Library and container scanning (Trivy) |
| Kai | Threat model + GitHub settings |

Pipeline files must go in a `.github/workflows/` folder. GitHub only runs them from there.

## How to make a change

1. Open the file on GitHub and click the pencil icon.
2. Click **Commit changes** → **Create a new branch** → **Propose changes** → **Create pull request**.
3. Get a teammate to approve it, then click **Merge**.

Never edit `main` directly.

## Dates

Demo ready: **Sun Nov 8** · Report due: **Fri Dec 4**
