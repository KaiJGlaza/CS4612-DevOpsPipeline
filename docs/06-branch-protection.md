# 6. Branch protection (rules on `main`)

**Owner:** Kai · **Status:** done (ruleset `protect-main` active since Nov 3)

## In one sentence

GitHub refuses any change to `main` unless it comes through a pull request that a teammate approved and that passed all six security scans.

## Where it lives

- `.github/rulesets/protect-main.json`, a copy kept in the repo for reference.
- The live rule: GitHub → Settings → Rules → Rulesets → `protect-main`. The JSON file **doesn't apply itself**; the live rule is what's enforced.

## How it works

| Rule | Setting |
|---|---|
| Applies to | The default branch (`main`) |
| Enforcement | Active |
| Who can bypass | **Nobody** (`bypass_actors: []`) |
| Pull request required | Yes, with **1 approval** |
| Required checks (all must pass) | `library-scan`, `dockerfile-scan`, `image-scan`, `Gitleaks`, `CodeQL (python, none)`, `CodeQL (actions, none)` |

The result is that the only way onto `main` is a PR with green scans and a teammate's approval. Because the secure deploy runs on every push to `main`, nothing reaches the deploy step without passing every scan first.

## What it protects against

- **CICD-SEC-1, Insufficient flow control:** no direct pushes, and no merging with failing scans.
- **Unauthorized config changes:** workflow files are protected by the same rules, so nobody can quietly delete a scan from `main`.

## How to demo it

1. `git push origin main` from a laptop is rejected.
2. Open the PR for `test-kai-failing-scan`: Trivy is red, and the **Merge** button is blocked.
3. Open a clean PR with no approval: Merge is blocked until a teammate approves.

## Results so far

- The rule is live on GitHub and enforced.
- The failing-scan and direct-push tests haven't been recorded yet (no PR opened for `test-kai-failing-scan`).

## Limitations

- `dismiss_stale_reviews_on_push: false` and `require_last_push_approval: false`: someone can get approval, then push more commits to the PR, and the old approval still counts. The scans re-run, but the human review doesn't.
- `strict_required_status_checks_policy: false`: a PR doesn't have to be up to date with `main` before merging.
- Only 1 approval is required.
