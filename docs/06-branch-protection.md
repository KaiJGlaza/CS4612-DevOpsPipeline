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
| Who can bypass | **Nobody** per the repo copy (`bypass_actors: []`). The live API hides this list from non-admins but reports `current_user_can_bypass: never` |
| Pull request required | Yes, with **1 approval** |
| Old approvals dismissed on new pushes | Yes (`dismiss_stale_reviews_on_push`) |
| Last push must be approved by someone else | Yes (`require_last_push_approval`) |
| Required checks (all must pass) | `library-scan`, `dockerfile-scan`, `image-scan`, `Gitleaks`, `CodeQL (python, none)`, `CodeQL (actions, none)` |
| Branch must be up to date with `main` | Yes (`strict_required_status_checks_policy`) |
| Force-push to `main` | Blocked (`non_fast_forward`) |
| Delete `main` | Blocked (`deletion`) |

These are the **live** settings, read from GitHub's API on Nov 9. The copy in `.github/rulesets/protect-main.json` is older and less strict, so treat the live ruleset as the source of truth.

The result is that the only way onto `main` is a PR with green scans and a teammate's approval. Because the secure deploy runs on every push to `main`, nothing reaches the deploy step without passing every scan first.

## What it protects against

- **CICD-SEC-1, Insufficient flow control:** no direct pushes, and no merging with failing scans.
- **Unauthorized config changes:** workflow files are protected by the same rules, so nobody can quietly delete a scan from `main`.

## How to demo it

1. `git push origin main` from a laptop is rejected.
2. Open the PR for `test-kai-failing-scan`: Trivy is red, and the **Merge** button is blocked.
3. Open a clean PR with no approval: Merge is blocked until a teammate approves.

## Results so far

- The rule is live on GitHub and enforced (`current_user_can_bypass: never` for team members).
- Elvin's notes-app PR was blocked by a failing Trivy `image-scan` until the zlib fix landed. That's a real-world example of "can't merge with a failing scan".
- Nov 11: a direct push to `main` was rejected (`GH013`, "Changes must be made through a pull request").
- Phillip's PR #4 has failing required Trivy checks and can't be merged. See [07-test-branches.md](07-test-branches.md).
- Nov 11: the repo copy `protect-main.json` was replaced with the live ruleset from GitHub's API, so the two now match.

## Limitations

- Only 1 approval is required.
