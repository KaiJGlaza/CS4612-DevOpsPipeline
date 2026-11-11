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
| Merge with a failing scan | Kai | `test-kai-failing-scan` (`flask==2.2.0`) | Merge button blocked | Trivy failed on push. PR not opened yet |
| Approve your own deploy | Kai | Trigger a deploy and try to self-approve | GitHub refuses (`prevent_self_review`) | |
| Steal the deploy secret from a PR | Kai | `test-kai-steal-secret` | Repo secret readable, env secret not | Pushed. PR not opened, so it hasn't run |
| Push directly to `main` | Kai | `git push origin main` | Rejected by ruleset | |

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
