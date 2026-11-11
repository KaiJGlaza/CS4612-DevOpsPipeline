# Requirements checklist

Taken from our project proposal ("Secure DevOps Pipeline"). Check items off as they land on `main` and are verified, and note where the evidence lives.

Status as of Nov 9. Presentation is **Nov 18**, report due **Dec 4**.

Legend: `[x]` done and verified · `[~]` partly done · `[ ]` not started

---

## 1. Sample app and control pipeline

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [~] | Sample application the pipelines build and deploy | Elvin | Notes app built on `elvin-sample-app`: 35 tests, all 6 scans green. Waiting on a teammate's approval to merge |
| [~] | App has real injection surface (SQL + HTML) for seeded defects | Elvin | `/notes/search` (SQLi) and `/search` (XSS). Local CodeQL flags both planted bugs. Done once merged |
| [ ] | **Unsecured pipeline**: test → build → ship, no scans, no approval | Elvin | Not yet in `.github/workflows/` |
| [ ] | Both pipelines run on the same runner image so timings are comparable | Elvin | Secure deploy pinned to `ubuntu-24.04` (PR #8); unsecured pipeline must match |

## 2. Threat model (OWASP Top 10 CI/CD Security Risks)

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [ ] | Threat model written for this pipeline's environment | Kai | Not in the repo yet |
| [ ] | Covers at least: dependency poisoning, secret exposure, unauthorized config changes | Kai | |
| [ ] | Each threat mapped to the control that mitigates it (and the stage it sits at) | Kai | |

## 3. Security controls in the secured pipeline

### 3a. Shift-left placement (cheap checks early, expensive checks later)

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Code scanning at commit / PR | Kofi | `codeql.yml`: push + pull_request |
| [x] | Secret scanning at commit / PR | Kofi | `gitleaks.yml`: push + pull_request, full history (`fetch-depth: 0`) |
| [x] | Dependency scan at build | Phillip | `trivy-scan.yml` → `library-scan` |
| [x] | Container image scan at build | Phillip | `trivy-scan.yml` → `image-scan` |
| [x] | Dockerfile / config scan | Phillip | `trivy-scan.yml` → `dockerfile-scan` |
| [~] | Infrastructure and runtime checks run **before deployment** | Kai | Scans gate the PR merge (required checks), but `secure-deploy.yml` doesn't re-run or `needs:` them. State this as the design or a limitation |

### 3b. Tools

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Gitleaks: secret scanning | Kofi | `gitleaks.yml` |
| [x] | CodeQL: SAST | Kofi | `codeql.yml` (python + actions) |
| [x] | Trivy: SCA + container scanning | Phillip | `trivy-scan.yml` |

### 3c. Failure policy per gate

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [~] | Trivy gates fail on HIGH/CRITICAL | Phillip | `exit-code: "1"`, `severity: HIGH,CRITICAL`. Image scan uses `ignore-unfixed` |
| [~] | Gitleaks gate fails on any detected secret | Kofi | Action default; not written down |
| [~] | CodeQL gate blocks merge on alerts | Kofi | Required check exists; confirm alerts actually fail it (code scanning merge protection / severity threshold) |
| [ ] | **Failure policy written down** for every gate (what fails, what severity, who can override) | Kofi + Phillip | Proposal says "explicitly defined failure policy" |

## 4. Identity, secrets, least privilege

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Deploy secret only available in the protected `production` environment | Kai | `secure-deploy.yml` → `environment: production`, `DEPLOY_TOKEN` |
| [x] | Secret never printed; only a fingerprint | Kai | `sha256sum` step in `secure-deploy.yml` |
| [~] | Least-privilege `permissions:` on every workflow | All | `secure-deploy.yml` uses `permissions: {}` + per-job. `trivy-scan.yml` and `codeql.yml` have no top-level block; `gitleaks.yml` grants `pull-requests: write` workflow-wide |
| [~] | Third-party actions pinned to commit SHAs | All | Pinned in `secure-deploy.yml`/Trivy action. Tags (`@v4`, `@v6`, `@v7`) still used in `codeql.yml`, `gitleaks.yml`, `trivy-scan.yml` checkout |
| [ ] | Secrets in an **external store** (proposal names AWS Secrets Manager) | Kai | Currently GitHub environment secrets. Either implement or list it under limitations |
| [x] | Role separation: author ≠ deploy approver | Kai | `production` env: required reviewers, `prevent_self_review: true`, `can_admins_bypass: false` |

## 5. Policy enforcement (can't be bypassed by a rushed developer)

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Branch protection on `main` (PR required, 1 approval) | Kai | Ruleset `protect-main` active on GitHub; `current_user_can_bypass: never` |
| [x] | Required status checks (all 6 scan jobs) | Kai | Live ruleset; branch must also be up to date with `main` (`strict_required_status_checks_policy: true`) |
| [x] | Deployment needs environment approval | Kai | `production` environment reviewers |
| [x] | Approval can't be reused after new pushes | Kai | Live ruleset: `dismiss_stale_reviews_on_push: true`, `require_last_push_approval: true` |
| [x] | `main` can't be force-pushed or deleted | Kai | Live ruleset: `non_fast_forward` and `deletion` rules |
| [ ] | Repo copy of the ruleset matches the live one | Kai | `.github/rulesets/protect-main.json` is out of date: it shows the stale-review settings as `false` and lacks the force-push, deletion and up-to-date rules. Export the live ruleset over it |

## 6. Evaluation: seeded defects (same commit through both pipelines)

Record for each: unsecured result · secured result · which gate caught it · run links.

| | Test | Owner | Branch | Unsecured | Secured |
|---|---|---|---|---|---|
| [ ] | SQL injection | Elvin | `test-elvin-sqli` (todo). Plant verified with local CodeQL | | |
| [ ] | XSS | Elvin | `test-elvin-xss` (todo). Plant A verified with local CodeQL; needs `@app.route` | | |
| [ ] | Hardcoded API key | Kofi | not found on remote | | |
| [ ] | Hardcoded cryptographic key | Kofi | not found on remote | | |
| [ ] | Key hidden in an old commit | Kofi | not found on remote | | |
| [~] | Outdated / vulnerable library | Phillip | `PhillipEiser-test-1` (PR #4) | | blocked (Trivy) |
| [~] | Container runs as root | Phillip | `PhillipEiser-test-2` (PR #5) | | blocked (Trivy) |
| [~] | Outdated base image | Phillip | `PhillipEiser-test-3` (PR #6) | | blocked (Trivy) |
| [x] | *Real, not planted:* new zlib CVEs in `python:3.13-slim` | Elvin | `elvin-sample-app`, first commit | (would have shipped) | blocked (Trivy `image-scan`); fixed with `apt-get upgrade`. See `docs/04` |

## 7. Evaluation: policy enforcement tests

| | Test | Owner | Branch / how | Result |
|---|---|---|---|---|
| [ ] | Push directly to `main` is rejected | Kai | `git push origin main` | |
| [~] | Merging a PR with a failing / critical scan is blocked | Kai | `test-kai-failing-scan`; also seen on Elvin's PR (blocked by Trivy before the zlib fix) | |
| [ ] | Approving your own deploy is blocked | Kai | settings test, screenshot | |
| [~] | Deploy secret can't be stolen from a pull request | Kai | `test-kai-steal-secret` | |

## 8. Evaluation: performance overhead

| | Metric | Owner | Notes |
|---|---|---|---|
| [ ] | Total pipeline time, unsecured vs secured | Elvin | Same commit, same runner. Several runs, use the median |
| [ ] | Per-stage / per-job time | Elvin | From the Actions run timings (`gh run view --json jobs`) |
| [ ] | Proportion of builds failed by security gates | Elvin | Over all evaluation runs |
| [ ] | Results chart | Elvin | Hand to Phillip for slides |

## 8b. Added scope (future work)

| | Item | Owner | Notes |
|---|---|---|---|
| [ ] | CSRF protection on the app's create/delete forms | Elvin | Decided Nov 8: not in the UI change; build as its own change. Options: hand-rolled token with `secrets` + session (no new deps, but needs a `SECRET_KEY` managed in the deploy) or Flask-WTF (new dependency) |
| [ ] | Security headers (Content-Security-Policy etc.) | Elvin | Decided Nov 8: future work. Note that a CSP blocks the planted XSS from running, so the XSS demo branch would have to remove it |

## 9. Deliverables

| | Deliverable | Owner | Due |
|---|---|---|---|
| [ ] | Working secured pipeline + sample app on `main` | All | Nov 17 |
| [ ] | Working unsecured control pipeline | Elvin | Nov 17 |
| [ ] | Demo: bad commit ships through unsecured, blocked by secured | All | Nov 17 |
| [ ] | Slides | Phillip | Nov 17 |
| [ ] | Report: intro + results (Elvin), background + secret/code scanning (Kofi), library/container scanning + limitations (Phillip), threat model + secure deploy (Kai) | All | Dec 4 |
| [ ] | Limitations section (e.g. no external secret store, scans not re-run at deploy, CodeQL misses XSS in `@app.get` routes and templates, scanner data errors, `apt-get upgrade` reproducibility) | Phillip | Dec 4 |

## Proposal timeline vs. where we are

| Week | Proposal task | Status |
|---|---|---|
| 1 | Define vulnerability requirements, scope, limitations | [~] covered by README "who does what"; limitations not written |
| 2 | Sample app + unsecured pipeline; threat model with control mapping | [~] app built (awaiting merge); unsecured pipeline and threat model outstanding |
| 3 | Secret scanning + static analysis | [x] |
| 4 | Dependency + container scanning; failure policy per gate | [~] scanning done, policy not written |
| 5 | Branch protection, required checks, least-privilege permissions | [~] protection + checks done, permissions uneven |
| 6 | Run evaluation with seeded defects and policy tests | [ ] |
| Final | Limitations, report, demo | [ ] |
