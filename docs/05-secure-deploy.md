# 5. Secure deploy

**Owner:** Kai · **Status:** done (merged in PRs #7 and #8, first successful deploy Nov 6)

## In one sentence

After code reaches `main`, the pipeline builds and tests the container, then **waits for a different teammate to approve** before it can use the deploy secret and publish the image.

## Where it lives

- `.github/workflows/secure-deploy.yml`
- GitHub settings → Environments → `production`
- The image is published to `ghcr.io/kaijglaza/cs4612-devopspipeline`

## How it works

Two jobs, both on `ubuntu-24.04`:

1. **`build`** (no secrets, read-only):
   - Builds the image and runs the tests **inside** it.
   - Saves the image as a file and hands it to the next job.
2. **`deploy`** (runs in the `production` environment):
   - **Pauses until a reviewer approves.**
   - Loads the image.
   - Checks that `DEPLOY_TOKEN` exists and prints only a **fingerprint** (a short hash), never the secret itself.
   - Logs in to GitHub's container registry and pushes the image tagged with the commit and as `latest`.

**Security design choices:**

| Choice | Why |
|---|---|
| `permissions: {}` at the top, then only what each job needs | Least privilege. `build` can only read; only `deploy` can write packages |
| `DEPLOY_TOKEN` is an **environment** secret, not a repo secret | Only jobs running in `production` can see it, and those need approval |
| Environment reviewers with **prevent self-review** on | Separation of duties: whoever pushed can't approve their own deploy |
| Admins **can't bypass** the environment | Not even the repo owner can skip approval |
| Branch policy on the environment | Only allowed branches can deploy |
| `concurrency: production`, no cancel | Deploys never overlap or cut each other off |
| All actions locked to a specific commit (`@3d3c42e…`) | A compromised action tag can't change what runs |
| `persist-credentials: false` on checkout | The git token doesn't linger on disk for later steps |

**Reviewers:** all four team members are listed. Because self-review is blocked, any deploy needs someone other than the person who triggered it.

## What it protects against

- **CICD-SEC-1, Insufficient flow control:** nothing ships without a second person.
- **CICD-SEC-2, Inadequate identity and access management**, and **CICD-SEC-5, Insufficient pipeline-based access controls (PBAC):** each job gets only the permissions and secrets it needs.
- **CICD-SEC-6, Insufficient credential hygiene:** the secret is locked to one environment and never printed.

## How to demo it

1. Merge a harmless change to `main`, and show the run pausing at "Waiting for review."
2. Try to approve it as the person who pushed. GitHub refuses.
3. Have a teammate approve it, and show the image appearing in the repo's Packages.
4. **Steal-the-secret test** (`test-kai-steal-secret`): open a PR whose workflow tries to print `DEPLOY_TOKEN`. Without the environment it gets nothing. With `environment: production`, it's blocked by the branch policy and approval.

## Results so far

- Nov 3: the first deploy failed with "denied" when pushing to ghcr on `ubuntu-latest` (26.04, Docker 29).
- Nov 6: fixed by pinning `ubuntu-24.04` (PR #8), and the deploy succeeded.
- Nov 11: PR #9's deploy (run 43119689259) waited for review, was approved by yemouu (not the person who merged), and pushed tag `32ffe3e`.
- Nov 11: PR #11's deploy (run 43132320536) was started by Kai's merge. Kai got no approve option; yemouu approved it and tag `64e789e` was pushed.
- Nov 11, steal-the-secret test (PR #10): a repo secret leaked; `DEPLOY_TOKEN` stayed empty and the PR was refused the `production` environment. Details in [07-test-branches.md](07-test-branches.md).

## Limitations

- The proposal calls for an **external secret store** (AWS Secrets Manager). We use GitHub's environment secrets instead.
- The deploy doesn't re-run the scans. It relies on the scans that had to pass before the code could merge to `main` (see [06-branch-protection.md](06-branch-protection.md)).
- "Ship" means pushing an image to a registry. Nothing is running it as a live server.
