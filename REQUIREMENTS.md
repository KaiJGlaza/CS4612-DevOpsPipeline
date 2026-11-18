# Requirements checklist

Taken from our project proposal ("Secure DevOps Pipeline"). Check items off as they land on `main` and are verified, and note where the evidence lives.

Status as of Nov 18. Presentation is **Nov 18**, report due **Dec 4**.

Legend: `[x]` done and verified · `[~]` partly done · `[ ]` not started

---

## 1. Sample app and control pipeline

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Sample application the pipelines build and deploy | Elvin | Notes app (35 tests, all 6 scans green), merged in PR #9, Nov 11 |
| [x] | App has real injection surface (SQL + HTML) for seeded defects | Elvin | `/notes/search` (SQLi) and `/search` (XSS), merged in PR #9, Nov 11. Local CodeQL flags both planted bugs |
| [x] | **Unsecured pipeline**: test → build → ship, no scans, no approval | Elvin | `unsecured-deploy.yml`. First ship Nov 15 (run 43730580164); a failing test stops the ship (run 43731775002). See `docs/02` |
| [x] | Both pipelines run on the same runner image so timings are comparable | Elvin | Both on `ubuntu-24.04` with the same build and test commands |

## 2. Threat model (OWASP Top 10 CI/CD Security Risks)

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Threat model written for this pipeline's environment | Kai | `docs/08-threat-model.md` (STRIDE + risk rating, 11 threats) |
| [x] | Covers at least: dependency poisoning, secret exposure, unauthorized config changes | Kai | T11 (dependency poisoning), T5 (secret exposure), T1 (direct changes to `main`, including workflow files) |
| [x] | Each threat mapped to the control that mitigates it (and the stage it sits at) | Kai | Stage and Mitigation columns in `docs/08-threat-model.md` |

## 3. Security controls in the secured pipeline

### 3a. Shift-left placement (cheap checks early, expensive checks later)

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Code scanning at commit / PR | Kofi | `codeql.yml`: push + pull_request |
| [x] | Secret scanning at commit / PR | Kofi | `gitleaks.yml`: push + pull_request, full history (`fetch-depth: 0`) |
| [x] | Dependency scan at build | Phillip | `trivy-scan.yml` → `library-scan` |
| [x] | Container image scan at build | Phillip | `trivy-scan.yml` → `image-scan` |
| [x] | Dockerfile / config scan | Phillip | `trivy-scan.yml` → `dockerfile-scan` |
| [x] | Infrastructure and runtime checks run **before deployment** | Kai | Scans gate the PR merge (required checks, branch up to date), so nothing reaches the deploy without passing them. `secure-deploy.yml` doesn't re-run them; listed as a residual risk in `docs/08-threat-model.md` |

### 3b. Tools

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Gitleaks: secret scanning | Kofi | `gitleaks.yml` |
| [x] | CodeQL: SAST | Kofi | `codeql.yml` (python + actions) |
| [x] | Trivy: SCA + container scanning | Phillip | `trivy-scan.yml` |

### 3c. Failure policy per gate

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Trivy gates fail on HIGH/CRITICAL | Phillip | `exit-code: "1"`, `severity: HIGH,CRITICAL`. Image scan uses `ignore-unfixed`. Verified Nov 18 on PRs #4, #5, #6 (section 6) |
| [x] | Gitleaks gate fails on any detected secret | Kofi | Action default. Verified Nov 17 on PRs #16, #17, #18 (section 6) |
| [ ] | CodeQL gate blocks merge on alerts | Kofi + Kai | **Checked Nov 18: it doesn't.** On PRs #14 (SQLi) and #15 (XSS) the `CodeQL` alerts check failed, but the ruleset only requires the analysis jobs `CodeQL (python, none)` / `CodeQL (actions, none)`, which passed. Fix: add `CodeQL` as a required check or turn on code scanning merge protection in the ruleset (Kai, admin). Otherwise, list as a limitation |
| [ ] | **Failure policy written down** for every gate (what fails, what severity, who can override) | Kofi + Phillip | Proposal says "explicitly defined failure policy" |

## 4. Identity, secrets, least privilege

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Deploy secret only available in the protected `production` environment | Kai | `secure-deploy.yml` → `environment: production`, `DEPLOY_TOKEN` |
| [x] | Secret never printed; only a fingerprint | Kai | `sha256sum` step in `secure-deploy.yml` |
| [~] | Least-privilege `permissions:` on every workflow | All | `secure-deploy.yml` uses `permissions: {}` + per-job. `trivy-scan.yml` is `contents: read` (PR #19). `codeql.yml` sets permissions per job (`security-events: write`, `packages: read`), which is enough. Left: `gitleaks.yml` grants `pull-requests: write` workflow-wide (the action uses it to comment on PRs) |
| [~] | Third-party actions pinned to commit SHAs | All | Pinned in `secure-deploy.yml`/Trivy action. Tags (`@v4`, `@v6`, `@v7`) still used in `codeql.yml`, `gitleaks.yml`, `trivy-scan.yml` checkout |
| [ ] | Secrets in an **external store** (proposal names AWS Secrets Manager) | Kai | Not implemented: GitHub environment secrets are used instead. Listed as a limitation in `docs/05-secure-deploy.md` and `docs/08-threat-model.md` |
| [x] | Role separation: author ≠ deploy approver | Kai | `production` env: required reviewers, `prevent_self_review: true`, `can_admins_bypass: false` |

## 5. Policy enforcement (can't be bypassed by a rushed developer)

| | Requirement | Owner | Evidence / notes |
|---|---|---|---|
| [x] | Branch protection on `main` (PR required, 1 approval) | Kai | Ruleset `protect-main` active on GitHub; `current_user_can_bypass: never` |
| [x] | Required status checks (all 6 scan jobs) | Kai | Live ruleset; branch must also be up to date with `main` (`strict_required_status_checks_policy: true`) |
| [x] | Deployment needs environment approval | Kai | `production` environment reviewers |
| [x] | Approval can't be reused after new pushes | Kai | Live ruleset: `dismiss_stale_reviews_on_push: true`, `require_last_push_approval: true` |
| [x] | `main` can't be force-pushed or deleted | Kai | Live ruleset: `non_fast_forward` and `deletion` rules |
| [x] | Repo copy of the ruleset matches the live one | Kai | `.github/rulesets/protect-main.json` replaced with the live ruleset from GitHub's API on Nov 11 |

## 6. Evaluation: seeded defects (same commit through both pipelines)

Record for each: unsecured result · secured result · which gate caught it · run links.

Nov 18: `main` merged into Phillip's 3 branches so the unsecured pipeline (added Nov 15) runs on them. On test 3, `apt-get upgrade` from `main` fails on `python:3.11.0-slim`, so that line was removed on the branch only.

| | Test | Owner | Branch | Unsecured | Secured |
|---|---|---|---|---|---|
| [~] | SQL injection | Elvin | `test-elvin-sqli`, PR #14 | shipped ([44186982702](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44186982702)) | **detected, not blocked**: `CodeQL` alerts check failed, required CodeQL jobs passed (see 3c) |
| [~] | XSS | Elvin | `test-elvin-xss`, PR #15 | shipped ([44187039592](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44187039592)) | **detected, not blocked**: same as SQLi |
| [x] | Hardcoded API key | Kofi | `test-kofi-api-key`, PR #16 | shipped ([44190093019](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190093019)) | blocked: Gitleaks ([44190153024](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190153024)) |
| [x] | Hardcoded cryptographic key | Kofi | `test-kofi-crypto-key`, PR #17 | shipped ([44190092685](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190092685)) | blocked: Gitleaks ([44190156884](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190156884)), and Trivy `library-scan` + `image-scan` also flagged the private key ([44190156891](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190156891)) |
| [x] | Key hidden in an old commit | Kofi | `test-kofi-old-commit`, PR #18 | shipped ([44190093136](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190093136)) | blocked: Gitleaks, full history ([44190163031](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190163031)) |
| [x] | Outdated / vulnerable library | Phillip | `PhillipEiser-test-1`, PR #4 | shipped ([44320989146](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44320989146)) | blocked: Trivy `library-scan` + `image-scan` ([44321004069](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44321004069)) |
| [x] | Container runs as root | Phillip | `PhillipEiser-test-2`, PR #5 | shipped ([44320992064](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44320992064)) | blocked: Trivy `dockerfile-scan` ([44321002945](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44321002945)) |
| [x] | Outdated base image | Phillip | `PhillipEiser-test-3`, PR #6 | shipped ([44321708503](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44321708503)) | blocked: Trivy `image-scan` ([44321721999](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44321721999)) |
| [x] | *Real, not planted:* new zlib CVEs in `python:3.13-slim` | Elvin | `elvin-sample-app`, first commit | (would have shipped) | blocked (Trivy `image-scan`); fixed with `apt-get upgrade`. See `docs/04` |

## 7. Evaluation: policy enforcement tests

| | Test | Owner | Branch / how | Result |
|---|---|---|---|---|
| [x] | Push directly to `main` is rejected | Kai | `git push origin HEAD:main` | Rejected Nov 11 (`GH013`) |
| [x] | Merging a PR with a failing / critical scan is blocked | Kai | Phillip's PR #4; also seen on Elvin's PR (blocked by Trivy before the zlib fix) | Required Trivy checks failing, merge blocked |
| [x] | Approving your own deploy is blocked | Kai | Merge PR #11, try to approve its deploy | Refused Nov 11 (run 43132320536, `current_user_can_approve: false`); yemouu approved. See `docs/07` |
| [x] | Deploy secret can't be stolen from a pull request | Kai | `test-kai-steal-secret`, PR #10 | Repo secret leaked, `DEPLOY_TOKEN` empty, `production` refused the PR. See `docs/07` |

## 8. Evaluation: performance overhead

| | Metric | Owner | Notes |
|---|---|---|---|
| [x] | Total pipeline time, unsecured vs secured | Elvin | Medians: unsecured 32 s; secured 102.5 s machine time (52 s scans + 27.5 s build + 23 s deploy), **+70.5 s, 3.2×**, plus human approval time. See `docs/07` |
| [x] | Per-stage / per-job time | Elvin | Per-job table in `docs/07`. CodeQL (python) is the slowest job (median 49.5 s) |
| [x] | Proportion of builds failed by security gates | Elvin | 6 of 8 seeded-defect commits (75%) failed a required check; 8 of 8 flagged by some check |
| [ ] | Results chart | Elvin | Hand to Phillip for slides |

## 8b. Added scope (future work)

| | Item | Owner | Notes |
|---|---|---|---|
| [ ] | CSRF protection on the app's create/delete forms | Elvin | Decided Nov 8: not in the UI change; build as its own change. Options: hand-rolled token with `secrets` + session (no new deps, but needs a `SECRET_KEY` managed in the deploy) or Flask-WTF (new dependency) |
| [ ] | Security headers (Content-Security-Policy etc.) | Elvin | Decided Nov 8: future work. Note that a CSP blocks the planted XSS from running, so the XSS demo branch would have to remove it |

## 9. Deliverables

| | Deliverable | Owner | Due |
|---|---|---|---|
| [x] | Working secured pipeline + sample app on `main` | All | Nov 18 |
| [x] | Working unsecured control pipeline | Elvin | Nov 18 |
| [ ] | Demo: bad commit ships through unsecured, blocked by secured | All | Nov 18 |
| [ ] | Slides | Phillip | Nov 18 |
| [ ] | Report: intro + results (Elvin), background + secret/code scanning (Kofi), library/container scanning + limitations (Phillip), threat model + secure deploy (Kai) | All | Dec 4 |
| [ ] | Limitations section (e.g. CodeQL alerts not merge-blocking, no external secret store, scans not re-run at deploy, CodeQL misses XSS in `@app.get` routes and templates, scanner data errors, `apt-get upgrade` reproducibility) | Phillip | Dec 4 |

## Proposal timeline vs. where we are

| Week | Proposal task | Status |
|---|---|---|
| 1 | Define vulnerability requirements, scope, limitations | [~] covered by README "who does what"; limitations not written |
| 2 | Sample app + unsecured pipeline; threat model with control mapping | [x] app merged (PR #9); threat model done (`docs/08`, PR #11); unsecured pipeline built (`docs/02`) |
| 3 | Secret scanning + static analysis | [x] |
| 4 | Dependency + container scanning; failure policy per gate | [~] scanning done, policy not written |
| 5 | Branch protection, required checks, least-privilege permissions | [~] protection + checks done, permissions uneven |
| 6 | Run evaluation with seeded defects and policy tests | [~] policy tests done (section 7); all 8 seeded defects run (section 6): 6 blocked, 2 detected but not blocked. Timings done (section 8) |
| Final | Limitations, report, demo | [ ] |
