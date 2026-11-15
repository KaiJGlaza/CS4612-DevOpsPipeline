# 2. Unsecured pipeline (the control)

**Owner:** Elvin · **Status:** built and running on `elvin-unsecured-pipeline` (first successful ship Nov 15), not yet merged

## In one sentence

A deliberately naive pipeline (test, build, ship) with no security checks, so we can show what gets through when security is an afterthought.

## Where it lives

- `.github/workflows/unsecured-deploy.yml`
- The image is published to `ghcr.io/kaijglaza/cs4612-unsecured`, a **separate** package from the secured pipeline's `cs4612-devopspipeline`

## How it works

One job, `ship`, on `ubuntu-24.04`, started by **every push to any branch**:

1. Checks out the code.
2. Builds the image and runs the tests inside it, with **the same two commands as the secured pipeline's `build` job**.
3. Logs in to GitHub's container registry and pushes the image, tagged with the commit (`cb1b777`) and the branch name (`/` becomes `-`).

There's no scan, no pull request, no review and no approval. If the tests pass, it ships.

**Secure vs. unsecured, setting by setting.** Every unsecured choice is the opposite of the secure one, on purpose:

| Setting | Secure deploy | Unsecured deploy |
|---|---|---|
| Token permissions | `permissions: {}`, then the minimum per job | `permissions: write-all` |
| Action references | Locked to a commit (`@3d3c42e…`) | Movable version tags (`@v7`, `@v4`) |
| Checkout credentials | `persist-credentials: false` | Default: the token stays in `.git/config` for later steps |
| Deploy secret | `DEPLOY_TOKEN`, an environment secret, only after approval | `UNSAFE_DEPLOY_TOKEN`, a repo secret in the job's `env`, visible to every step including third-party actions |
| Approval | `production` environment, reviewers, no self-review | None |
| Triggers | Push to `main` (which needs a reviewed PR with green scans) | Push to any branch |
| Jobs | `build` and `deploy` split, image handed over as a file | One job does everything |

**Hard limits on the sloppiness.** It's meant to show a careless team, not an open door:
- **Push is the only trigger.** Nothing runs from pull requests or forks, so only people with push access to the repo can start it with the repo's token and secret.
- **It never prints a secret.**
- `UNSAFE_DEPLOY_TOKEN` holds a dummy value. Never put a real credential in it.
- `main` is still protected by the `protect-main` ruleset, which the write-all token can't bypass.

## Why it's built this way

| Decision | Why |
|---|---|
| Same repo, same commits | Both pipelines see exactly the same code with no copying, and a planted branch "ships" the moment it's pushed |
| Same build and test commands, same runner | Differences in outcome and time come from the security controls, not the build |
| Separate image (`cs4612-unsecured`) | A vulnerable test build can never overwrite the secured image |
| "Realistically sloppy" settings | That's how many real pipelines look; reading the file next to `secure-deploy.yml` shows every missing control |
| One job, not two | An unsecured team has no reason to split privileges. Splitting costs the secured pipeline an artifact upload and download, which counts as security overhead |
| Planted test branches delete their own safety tests | The app's security tests would otherwise fail the build and nothing would ship. Careless code usually comes without a test for its bug, which is the point: tests only catch what someone thought to test, and CodeQL catches the flaw without one |

**Timing rules** (for the comparison in the results):
- Machine time only. Unsecured = this run's duration. Secured = the longest parallel scan + the secure `build` job + the `deploy` job's running time.
- Time spent waiting for a PR review or the `production` approval is reported separately as "human overhead".
- The same commit, several runs, median.

## What it protects against

Nothing, and that's the point. It's the **control group**. It shows these OWASP CI/CD risks happening:
- **CICD-SEC-1, Insufficient flow control:** code reaches "production" with no review or approval.
- **CICD-SEC-3, Dependency chain abuse:** vulnerable libraries and base images ship unchecked, and actions are referenced by tags someone else can move.
- **CICD-SEC-5, Insufficient PBAC**, and **CICD-SEC-6, Insufficient credential hygiene:** every step gets a write-all token and the secret.

## How to demo it

Push one of the test branches and show the unsecured run going green all the way to "Push the image", and the new tag appearing under `cs4612-unsecured`, while the secured checks on the same commit go red.

## Results so far

- Nov 15, first run (run 43730580164, commit `cb1b777`): build, tests and push all succeeded with no PR and no approval. It shipped `cs4612-unsecured:cb1b777` and `:elvin-unsecured-pipeline`. The secured image's tags didn't change.
- Nov 15, failing-test check (run 43731775002, throwaway branch): the run failed at "Run the tests inside the image", login and push were skipped, and no tag was published. The branch was then deleted.
- **CodeQL didn't flag the workflow.** On the same commit, CodeQL's `actions` analysis ran its 17 default rules and found nothing in `unsecured-deploy.yml`, so the required `CodeQL (actions, none)` check passed. The only `actions` alerts are 3 older `missing-workflow-permissions` alerts on `trivy-scan.yml`, which are on `main` too. Why it misses each weakness:
  - `write-all` is an explicit permissions block, so the "missing permissions" rule doesn't fire.
  - Tag-pinned actions and a secret in job-level `env` aren't checked by the default query suite.
- Seeded-defect runs (SQLi, XSS): not run yet.

## Limitations

- **The secured pipeline's scanners don't catch an insecure workflow file.** CodeQL's default rules pass it, so the only thing stopping it reaching `main` is a reviewer reading it.
- The `cs4612-unsecured` package is **public**, because that was the default when the first image was published. Anyone can pull it, including the planted, vulnerable builds. It can be made private in the package settings.
- It runs on **every push by everyone**, which uses extra Actions minutes and publishes an image each time. Old images can be pruned.
- The write-all token and repo secret stay in place while the workflow exists. Plan to disable or remove it after the report (Dec 4).
- "Ship" means pushing an image to a registry. Nothing runs it as a live server.
