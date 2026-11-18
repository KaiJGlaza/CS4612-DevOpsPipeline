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
| `elvin-sample-app` (real, not planted) | New zlib CVEs in the base image | Failed (blocked). See the incident below |

## Talking point: a real incident the pipeline caught (Nov 9, 2026)

**What happened:** Elvin pushed the notes app, and Trivy's `image-scan` failed with **2 HIGH** findings. Neither came from our code. Both were in **`zlib1g`**, the compression library inside the official `python:3.13-slim` base image. The same scan had passed on `main` three days earlier. The vulnerabilities were real, and new.

| CVE | What the bug is | Score | Published |
|---|---|---|---|
| **CVE-2026-85091** | Heap buffer overflow (out-of-bounds write) in zlib's `gz_vacate()`, reachable through the `gzprintf()`/`gzvprintf()` write functions after a write stall | CVSS 3.1 **7.4 HIGH** (VulnCheck); Red Hat 8.1 | Sep 3, 2026 |
| **CVE-2026-76844** | Heap buffer overflow in zlib's `gz_write()`: after a failed `write()`, a stale pointer makes a later write go past a heap allocation | CVSS 3.1 **7.4 HIGH** (VulnCheck); Red Hat 8.6 | Aug 24, 2026 |

**Timeline:**

| Date | Event |
|---|---|
| Aug 24 and Sep 3 | Both CVEs published (CNA: VulnCheck) |
| Sep 17 | Fixed upstream in zlib (commit `df84af25`, issue madler/zlib#1310) |
| **Nov 7** | Debian ships the fix for Debian 13: **DSA-6613-1**, zlib `1:1.3.dfsg+really1.3.1-1+deb13u1` |
| Nov 9 | The official `python:3.13-slim` image **still has the old zlib** (`…-1+b1`). Our pipeline blocks the PR |
| Nov 9 | Fixed with one Dockerfile line: `apt-get upgrade` installs Debian's patch during our build |

**Before and after (local Trivy, same settings as CI: HIGH/CRITICAL, ignore-unfixed):**

| Image | Result |
|---|---|
| `python:3.13-slim` as published | ❌ 7 HIGH: 2 zlib + 5 in libraries bundled with pip |
| Our image before the fix | ❌ 2 HIGH: zlib (the `pip uninstall` step already removes the other 5) |
| Our image with `apt-get upgrade` | ✅ 0 |

**Things worth knowing (and saying honestly):**
- **"Official image" doesn't mean "patched."** Debian had a fix out for two days, but the image everyone pulls hadn't been rebuilt yet. Without the scan, we'd have shipped a known-vulnerable library.
- **The danger in *our* app is probably low.** Both bugs are in zlib's gz\* *file-writing* functions, not in decompressing attacker-supplied data, and our app doesn't compress anything. The scanner judges what's *installed*, not what's *reachable*. That's the right default for a gate, and it's also why scanners produce findings that need human triage.
- **Scanner data has errors.** Trivy titled CVE-2026-76844 *"webpack-dev-middleware: Information Disclosure via Path Traversal"*, a JavaScript package unrelated to zlib. Debian, NVD and Aqua's own AVD page all describe it as the zlib heap overflow. It looks like a data error in Trivy's database (our inference, not confirmed). Trivy also summarizes CVE-2026-85091 as "allows arbitrary code execution", while the CVE record only says heap overflow (Debian's advisory says "potentially" code execution).
- **The affected version range is disputed.** CVE-2026-85091 lists zlib 1.3.1.2–1.3.2, but Debian's 1.3.1-based package is still marked vulnerable, and a third party on the upstream issue argued 1.3.1 lacks `gz_vacate()` entirely. Debian patched it anyway.

**What to say in one line:** *"The secured pipeline caught a real, brand-new vulnerability in an official image we didn't write. The fix took one line, and the unsecured pipeline would have shipped it."*

**Sources:** Debian security tracker (CVE-2026-85091, CVE-2026-76844); DSA-6613-1 (debian-security-announce, Nov 7, 2026); NVD API records; Aqua AVD; VulnCheck advisory; github.com/madler/zlib/issues/1310.

## Limitations

- It only knows about **publicly disclosed** vulnerabilities. A zero-day or a malicious-but-unreported package passes.
- `ignore-unfixed` means a known CRITICAL vulnerability with no fix yet won't block.
- It reports what's **installed**, not what's **reachable**, so some findings (like the zlib ones above) may not be exploitable in our app and need human judgement.
- Its database can be wrong: a mismatched title for CVE-2026-76844, and an overstated "arbitrary code execution" summary (see the incident above).
- `apt-get upgrade` makes builds less reproducible: the same Dockerfile can produce different images on different days.
- `actions/checkout@v4` is referenced by version tag, not locked to a commit.
- The workflow has no `permissions:` block, so it gets the repo's default token permissions.
