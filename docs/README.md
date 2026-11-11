# Project documentation

A plain-language summary of each part of the Secure DevOps Pipeline project: what it is, how it works, what it protects against, and how to demo it. Use these pages to build the slides and the final report.

**Rule:** when a change lands on `main`, update the matching page here in the same PR.

## The big picture

We run the same small app through two pipelines and plant bad code to compare them.

```
                         ┌──────────── every push and pull request ─────────────┐
                         │                                                      │
 Unsecured pipeline:   test ──► build ──► ship                (ships anything)  │
                                                                                │
 Secured pipeline:     SCAN ──► merge to main ──► build + test ──► APPROVE ──► ship
                        │            │                              │
                        │            │                              └─ a different teammate must approve
                        │            └─ needs a PR, 1 approval and all 6 scans passing
                        └─ Gitleaks (secrets) · CodeQL (code) · Trivy (libraries, Dockerfile, image)
```

## Sections

| # | Section | Owner | Status | Page |
|---|---|---|---|---|
| 1 | Sample app | Elvin | in progress | [01-sample-app.md](01-sample-app.md) |
| 2 | Unsecured pipeline (the control) | Elvin | not started | [02-unsecured-pipeline.md](02-unsecured-pipeline.md) |
| 3 | Secret and code scanning (Gitleaks, CodeQL) | Kofi | done | [03-secret-and-code-scanning.md](03-secret-and-code-scanning.md) |
| 4 | Library and container scanning (Trivy) | Phillip | done | [04-library-and-container-scanning.md](04-library-and-container-scanning.md) |
| 5 | Secure deploy (approval + locked secret) | Kai | done | [05-secure-deploy.md](05-secure-deploy.md) |
| 6 | Branch protection (rules on `main`) | Kai | done | [06-branch-protection.md](06-branch-protection.md) |
| 7 | Test branches and results | everyone | in progress | [07-test-branches.md](07-test-branches.md) |

What's still owed against the proposal is tracked in [`../REQUIREMENTS.md`](../REQUIREMENTS.md).

## Page template

Every section page uses the same headings, so they map directly onto slides:

1. **In one sentence**
2. **Where it lives**: files and settings
3. **How it works**
4. **What it protects against**: the threat, tied to the OWASP Top 10 CI/CD Security Risks where it fits
5. **How to demo it**
6. **Results so far**
7. **Limitations**
