# 2. Unsecured pipeline (the control)

**Owner:** Elvin · **Status:** not started

## In one sentence

A deliberately naive pipeline (test, build, ship) with no security checks, so we can show what gets through when security is an afterthought.

## Where it lives

`.github/workflows/unsecured-deploy.yml` (planned)

## How it works

Planned design, to be updated once it's built:
1. Runs on every push (including test branches).
2. Builds the container image and runs the tests inside it, **the same steps as the secured pipeline's build job**.
3. "Ships" the image, with no scan, no pull request requirement and no approval.
4. Runs on the **same machine type as the secured pipeline (`ubuntu-24.04`)**, so the timing comparison is fair.

It doesn't push to the real registry, so it can't overwrite the secured pipeline's image. It tags the image as `unsecured-*` or just records that the "ship" step ran.

## What it protects against

Nothing, and that's the point. It's the **control group**. It shows these OWASP CI/CD risks happening:
- **CICD-SEC-1, Insufficient flow control:** code reaches "production" with no review or approval.
- **CICD-SEC-3, Dependency chain abuse:** vulnerable libraries and base images ship unchecked.

## How to demo it

Push one of the test branches and show the unsecured run going green, all the way to "ship," while the secured checks on the same commit go red.

## Results so far

Not run yet.

## Limitations

To be filled in once it's built.
