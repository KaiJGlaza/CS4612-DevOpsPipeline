# 8. Threat model: CI/CD pipeline

**Owner:** Kai · **Status:** done (tests recorded Nov 11)

Ratings are judgement calls, not measurements. The "Verified by" column gives the real test result, or "Not tested".

Method: the lecture's four steps (Threat Modeling Analysis slides). 1) Decompose the system. 2) Map threats with STRIDE. 3) Rate risk with the RDP model: Risk = Probability × Damage Potential, banded High / Medium / Low. 4) Plan mitigations.

## 1. Decomposition

**Assets**
- A1 `main` branch: what ships.
- A2 Deploy secret (`DEPLOY_TOKEN`): stands in for a real cloud/server credential.
- A3 Shipped container image (GHCR): what users run.
- A4 Pipeline definitions (`.github/workflows/`): code that runs with the repo's permissions.

**Actors**: team members (write access), repo owner (admin), outside contributor (fork PR), compromised third-party action or package.

**Entry points**: pull request from a branch, pull request from a fork, direct push to `main`, merging a PR, approving a deployment, third-party actions used by workflows, Python packages and the base image pulled during the build.

**Data flow and trust boundaries**

```
 developer ──push──▶ feature branch ──PR──▶ [scans: Trivy / Gitleaks / CodeQL]
                                               │ all green + 1 teammate review
 ═══════ TB1: branch ruleset ══════════════════▼═══════════════
                                             main
                                               │ push event
                                         build + test image
 ═══════ TB2: production environment ═══════════▼═══════════════
                     teammate approval (not the merger) + main-only
                                               │ DEPLOY_TOKEN released here only
                                          push image to GHCR
```
TB1: untrusted code becomes trusted code. TB2: trusted code gets credentials and reaches users.

## 2-4. Threats, risk, mitigations

Stage: **PR** = before merge (TB1), **Deploy** = after merge (TB2), **All** = every workflow.

| # | STRIDE | Threat | P | D | Risk | Stage | Mitigation (implemented) | Verified by |
|---|---|---|---|---|---|---|---|---|
| T1 | Tampering | Push code or workflow changes straight to `main`, skipping scans and review | H | H | **High** | PR | Ruleset: PR required, no direct push, no force push, no deletion, no bypass (owner included) | Direct push rejected, Nov 11: `GH013`, "Changes must be made through a pull request" |
| T2 | Tampering | Merge a PR whose security scan failed | H | H | **High** | PR | Six required status checks (Trivy x3, Gitleaks, CodeQL x2); branch must be up to date with `main` | PR #4 (Phillip): required Trivy `image-scan` and `library-scan` failing, merge blocked |
| T3 | Spoofing | Write-access user posts a fake "success" status named like a scan via the API | M | H | **High** | PR | Required checks pinned to the GitHub Actions app (`integration_id` 15368), so outside statuses don't count | Not tested |
| T4 | Elevation of privilege | One person writes, merges and deploys their own code | M | H | **High** | PR + Deploy | 1 approval required, approval of the most recent push, stale approvals dismissed, environment reviewer with *prevent self-review*, admin bypass off | Deploys 42311435141, 43119689259 and 43132320536 were approved by someone other than the person who triggered them. Run 43132320536: Kai, a listed reviewer, got no approve option on a deploy Kai triggered (`current_user_can_approve: false`). See [07-test-branches.md](07-test-branches.md) |
| T5 | Information disclosure | PR adds a workflow that prints the deploy secret | H | H | **High** | Deploy | Secret stored as an environment secret, not a repo secret; environment accepts only `main`; fork PRs get no secrets; base64 trick defeats masking, so masking is not relied on | Test 3 (PR #10, run 43122287179): a repo secret leaked in base64, `DEPLOY_TOKEN` was empty, and the job asking for `production` was refused |
| T6 | Information disclosure / EoP | Compromised third-party action steals the secret or token (tj-actions, March 2025) | L | H | **Medium** | Deploy | Deploy job actions pinned to full commit SHAs; secret only in the one step that needs it; checkout with `persist-credentials: false` | Not tested |
| T7 | Elevation of privilege | Workflow token used to push code, approve PRs or publish packages | M | M | **Medium** | All | `permissions: {}` at the top, per-job least privilege (`packages: write` only in deploy); repo default token read-only; Actions can't approve PRs | Not tested |
| T8 | Tampering | Image built after approval differs from the one tested | L | M | **Low** | Deploy | Image built and tested once, passed to the deploy job as an artifact; same bytes ship | Not tested |
| T9 | Repudiation | Nobody can tell who shipped what | L | M | **Low** | Deploy | GitHub keeps PR reviews, deployment approvals (who and when) and the image tag = commit SHA | Run 43119689259: triggered by KaiJGlaza, approved by yemouu, image tag `32ffe3e` |
| T10 | Denial of service | Two deploys race and leave production half-updated | L | L | **Low** | Deploy | `concurrency: production`, in-progress deploys never cancelled | Not tested |
| T11 | Tampering | Vulnerable or malicious dependency or base image pulled in through `requirements.txt` or `FROM` (dependency poisoning) | M | H | **High** | PR | Trivy `library-scan` and `image-scan` are required checks and fail on HIGH/CRITICAL | PR #4 (`urllib3==1.26.4`) and PR #6 (`python:3.11.0-slim`): Trivy failed. Also caught real zlib CVEs in `python:3.13-slim` on Elvin's sample-app branch (Nov 9) |

## Residual risks (for "Limitations")
- The deploy workflow trusts that what's on `main` passed scans on the PR; it doesn't re-run them. Safe only while the ruleset has no bypass and requires up-to-date branches.
- The repo owner can still turn the rules off in Settings. Rules stop mistakes and teammates, not a malicious admin. A real org would use org-level rulesets and audit logs.
- `pull_request_target` workflows run with base-branch secrets and would pass the `main`-only rule; none exist in this repo, and adding one requires a reviewed PR.
- Actions in the scan workflows still use movable version tags (`actions/checkout@v4` in Trivy, `@v6` in Gitleaks, `@v7` in CodeQL). Only the deploy workflow pins every action to a commit SHA.
- Secrets live in GitHub environment secrets. The proposal named an external store (AWS Secrets Manager).
- "Ship" means pushing the image to GitHub's container registry (ghcr.io). Nothing runs it as a live site. `DEPLOY_TOKEN` is a random test value that stands in for a real server credential. A real one would let whoever holds it put any image live, which is why T5 is rated High.
