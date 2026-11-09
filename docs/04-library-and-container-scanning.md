# 4. Library and container scanning (Trivy)

**Owner:** Phillip · **Status:** done (merged in PR #1)

## In one sentence

Trivy checks the libraries the app uses, the Dockerfile's settings and the finished container image for known vulnerabilities, and fails the build on anything HIGH or CRITICAL.

## Where it lives

`.github/workflows/trivy-scan.yml`, which has three jobs:

| Job (check name) | Scans | Catches |
|---|---|---|
| `library-scan` | `app/requirements.txt` (`scan-type: fs`) | Libraries with known CVEs |
| `dockerfile-scan` | `app/Dockerfile` (`scan-type: config`) | Bad settings, such as running as root |
| `image-scan` | The built image (`scan-type: image`) | Vulnerable OS packages and libraries inside the container |

## How it works

- Runs on every push and pull request.
- Trivy compares versions against public vulnerability databases.
- **Failure policy:** `exit-code: "1"` with `severity: HIGH,CRITICAL`. Any HIGH or CRITICAL finding fails the job. LOW and MEDIUM findings are reported but don't block.
- The image scan uses `ignore-unfixed: true`, so it only blocks on vulnerabilities that have a fix available.
- The Trivy action is locked to a specific commit (`@ed142fd…`) instead of a version tag.

**Why at build time:** a container image only exists once the app has been built, so dependency and container checks run at the build stage.

## What it protects against

- **CICD-SEC-3, Dependency chain abuse:** outdated or vulnerable libraries.
- **Vulnerable base images:** old OS packages in `python:x.y`.
- **CICD-SEC-7, Insecure system configuration:** containers running as root.

## How to demo it

Open any of PRs #4–#6 (Phillip's test branches) and show the red Trivy check plus its findings list. Compare it with `main`, where all three jobs are green.

## Results so far

| Test branch | Change | Trivy result |
|---|---|---|
| `PhillipEiser-test-1` (PR #4) | Adds `urllib3==1.26.4` (known CVEs) | Failed (blocked) |
| `PhillipEiser-test-2` (PR #5) | Removes the non-root user, so the app runs as root | Failed (blocked) |
| `PhillipEiser-test-3` (PR #6) | Base image `python:3.11.0-slim` (old) | Failed (blocked) |
| `test-kai-failing-scan` | Old `flask==2.2.0` | Failed (blocked) |

## Limitations

- It only knows about **publicly disclosed** vulnerabilities. A zero-day or a malicious-but-unreported package passes.
- `ignore-unfixed` means a known CRITICAL vulnerability with no fix yet won't block.
- `actions/checkout@v4` is referenced by version tag, not locked to a commit.
- The workflow has no `permissions:` block, so it gets the repo's default token permissions.
