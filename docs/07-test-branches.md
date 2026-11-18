# 7. Test branches and results

**Owner:** everyone (each person seeds 3 tests) · **Status:** seeded defects and policy tests done; timings to do

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
| SQL injection | Elvin | `test-elvin-sqli`, PR #14 | Search builds SQL with an f-string | CodeQL | shipped, [44186982702](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44186982702) | **detected, not blocked**: the `CodeQL` alerts check failed, but it isn't a required check; the required CodeQL jobs passed |
| XSS | Elvin | `test-elvin-xss`, PR #15 | Search page returns unescaped HTML | CodeQL | shipped, [44187039592](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44187039592) | **detected, not blocked**: same as SQL injection |
| Fake API key | Kofi | `test-kofi-api-key`, PR #16 | Hardcoded API key in code | Gitleaks | shipped, [44190093019](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190093019) | **blocked**, Gitleaks failed, [44190153024](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190153024) |
| Fake encryption key | Kofi | `test-kofi-crypto-key`, PR #17 | Hardcoded crypto key | Gitleaks | shipped, [44190092685](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190092685) | **blocked**, Gitleaks failed, [44190156884](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190156884). Trivy `library-scan` and `image-scan` also flagged the private key, [44190156891](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190156891) |
| Key in an old commit | Kofi | `test-kofi-old-commit`, PR #18 | Key added, then deleted | Gitleaks (full history) | shipped, [44190093136](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190093136) | **blocked**, Gitleaks failed, [44190163031](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44190163031) |
| Outdated library | Phillip | `PhillipEiser-test-1`, PR #4 | `urllib3==1.26.4` | Trivy `library-scan` | shipped, [44320989146](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44320989146) | **blocked**, Trivy `library-scan` and `image-scan` failed, [44321004069](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44321004069) |
| App runs as root | Phillip | `PhillipEiser-test-2`, PR #5 | Non-root user removed from Dockerfile | Trivy `dockerfile-scan` | shipped, [44320992064](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44320992064) | **blocked**, Trivy `dockerfile-scan` failed, [44321002945](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44321002945) |
| Outdated base image | Phillip | `PhillipEiser-test-3`, PR #6 | `python:3.11.0-slim` | Trivy `image-scan` | shipped, [44321708503](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44321708503) | **blocked**, Trivy `image-scan` failed, [44321721999](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44321721999) |

**Summary:** all 8 shipped through the unsecured pipeline. The secured pipeline blocked 6 and detected the other 2 (SQLi, XSS) without blocking them, because the CodeQL alerts check isn't required by the ruleset.

**Notes on Phillip's branches (Nov 18):** they were created before the unsecured pipeline existed, so `main` was merged into them to run it. On test 3, the `apt-get upgrade` line from `main` fails on `python:3.11.0-slim` (apt exit code 100) and stopped the unsecured build, so it was removed on that branch only. The first merge run for test 3 ([44320999144](https://github.com/KaiJGlaza/CS4612-DevOpsPipeline/actions/runs/44320999144)) is that failed build and doesn't count as a result.

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
