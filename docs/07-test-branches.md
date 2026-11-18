# 7. Test branches and results

**Owner:** everyone (each person seeds 3 tests) · **Status:** in progress

## In one sentence

Each test branch plants one deliberate flaw, and the same commit goes through both pipelines to show the unsecured one ships it and the secured one blocks it.

## How to record a result

For each test, fill in the table below with:
- what the **unsecured** pipeline did
- what the **secured** pipeline did, and **which check** caught it
- links to the GitHub Actions runs

Test branches are **never merged**. PRs stay open with "Do Not Merge" in the title.

## Seeded defects (detection effectiveness)

| Test | Owner | Branch / PR | The flaw | Expected catch | Unsecured | Secured |
|---|---|---|---|---|---|---|
| SQL injection | Elvin | `test-elvin-sqli` (todo) | Search builds SQL with an f-string | CodeQL | | |
| XSS | Elvin | `test-elvin-xss` (todo) | Search page returns unescaped HTML | CodeQL | | |
| Fake API key | Kofi | (todo) | Hardcoded API key in code | Gitleaks | | |
| Fake encryption key | Kofi | (todo) | Hardcoded crypto key | Gitleaks | | |
| Key in an old commit | Kofi | (todo) | Key added, then deleted | Gitleaks (full history) | | |
| Outdated library | Phillip | `PhillipEiser-test-1`, PR #4 | `urllib3==1.26.4` | Trivy `library-scan` | | **blocked**, Trivy failed |
| App runs as root | Phillip | `PhillipEiser-test-2`, PR #5 | Non-root user removed from Dockerfile | Trivy `dockerfile-scan` | | **blocked**, Trivy failed |
| Outdated base image | Phillip | `PhillipEiser-test-3`, PR #6 | `python:3.11.0-slim` | Trivy `image-scan` | | **blocked**, Trivy failed |

## Policy enforcement

| Test | Owner | Branch / how | Expected | Result |
|---|---|---|---|---|
| Merge with a failing scan | Kai | Phillip's PR #4 (`urllib3==1.26.4`). Kai's `test-kai-failing-scan` repeated it, so it wasn't opened | Merge button blocked | Required Trivy `image-scan` and `library-scan` failing; merge blocked. The PR also lacks an approval and is out of date, so those rules block it too |
| Approve your own deploy | Kai | Kai merged PR #11, then tried to approve the deploy it started | GitHub refuses (`prevent_self_review`) | Refused, Nov 11 (run 43132320536): the pending-deployment dialog gave Kai no approve option and listed only the other reviewers ("aepresso, yemouu, or 1 other"). The API returned `current_user_can_approve: false` although Kai is one of the 4 `production` reviewers. yemouu approved and tag `64e789e` was pushed. The Nov 3 run (41735134908) showed the same dialog |
| Steal the deploy secret from a PR | Kai | `test-kai-steal-secret`, PR #10, run 43122287179 | Repo secret readable, env secret not | Repo secret `UNSAFE_DEPLOY_TOKEN` leaked (length 64; the base64 in the log decoded to the stored value). `DEPLOY_TOKEN` empty (length 0). The job using `production` was refused: "Branch refs/pull/10/merge is not allowed to deploy to production". PR closed and the leaked secret deleted |
| Push directly to `main` | Kai | `git push origin HEAD:main` | Rejected by ruleset | Rejected, Nov 11: `GH013`, "Changes must be made through a pull request" and "6 of 6 required status checks are expected" |

## Performance overhead

Run the same commit through both pipelines several times on `ubuntu-24.04`, and use the median.

| Metric | Unsecured | Secured | Overhead |
|---|---|---|---|
| Total pipeline time | | | |
| Time per stage / job | | | |
| % of evaluation runs failed by a security gate | n/a | | |

Pull timings with:
```
gh run view <run-id> --json jobs --jq '.jobs[] | {name, startedAt, completedAt}'
```
