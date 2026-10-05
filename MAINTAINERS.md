---
title: Maintaining the Sagan workspace
status: review-needed
publication_ready: false
verified_in: null
verified_on: null
verified_by: null
---

# Maintaining the Sagan workspace

This is a local split candidate. Before publication, validate it from a clean
filtered checkout, specialize the remaining integration commands, and verify
organization governance and CI. The current lock contains only the primary
`sagan` source pin. No split-repository URL should be activated until that
repository exists, is backed up, and passes its extraction gate.

## Prerequisites and exact commands

Use Git Bash, Git, and Python 3.11 or newer. From the workspace repository root:

```bash
bash scripts/bootstrap.sh
bash scripts/status.sh
python -m unittest discover -s tests -p workspace_test.py -v
bash -n scripts/bootstrap.sh scripts/status.sh
```

`bootstrap.sh` and `status.sh` accept `--root`, `--manifest`, and `--lock` for
isolated test fixtures. Normal use needs no arguments. A zero status means
every active checkout is clean, has the manifest's exact origin URL, and is at
its locked commit. A missing, dirty, wrong-origin, or wrong-commit checkout
returns nonzero. No command here pushes, tags, changes a remote, or deletes a
checkout.

The root manifest is `workspace.toml`; the tested
source lock is `workspace.lock`; child repositories live under gitignored
`checkouts/`. Change `state` to `active` only alongside an exact, reviewed
lock entry. The checker rejects a missing or extra active lock entry. Record
why a lock SHA changed and which focused compatibility checks established it.
Do not hand-edit the checked-out child to make status green.

## Change and test workflow

Inspect `git status --short --branch`, `git rev-parse HEAD`, and staged paths
before changing anything. Start each authorized request from current `dev` on
a fresh `codex/<request>` branch. Preserve unrelated work. Implement only the
requested scope, run the relevant tests, refine until they pass, commit only
intended paths, merge into `dev`, and rerun those relevant tests on integrated
`dev`. For a bootstrap/lock change, the focused commands above and a clean
checkout bootstrap rehearsal are relevant. For future demo or cross-repo
changes, add the exact affected build/test commands here. Do not run unrelated
executable documentation examples for a structural-only documentation edit;
run affected examples when their content or supporting behavior changes.

Reserve the complete suite for a reviewed `dev`-to-`main` promotion or release.
The project-wide release and `main` promotion hold remains in force until the
owner explicitly reopens it and decides publication/signing policy. A passing
suite is not authorization to publish.

## Failure and recovery

- `missing`: `bash scripts/bootstrap.sh` may clone it. Confirm URL and SHA
  before doing so; the command requires network for public remotes.
- `dirty`: inspect the child with `git -C checkouts/<name> status --short`.
  Commit, stash, or otherwise preserve your work in that child by deliberate
  choice. Bootstrap never discards it.
- `origin URL differs`: inspect `git -C checkouts/<name> remote -v` and the
  manifest. Correct the intended owner deliberately; do not auto-retarget.
- `HEAD differs`: inspect `git -C checkouts/<name> log -1 --oneline` and the
  lock. Preserve any work; choose whether to update the lock after integration
  verification or explicitly checkout the pinned commit in that child.
- `clone` or `checkout` failed: inspect the reported partial directory and
  network/credentials. Do not overwrite it automatically. If it contains
  useful state, back it up before a manual recovery.

The current local-only primary backup cannot survive loss of this computer
and cannot recreate GitHub settings, secrets, issues, or PR history. The
workspace lock is not a backup. Follow the primary repository's transfer and
backup runbook before any further remote migration. Generated checkouts can be
recreated from the remotes if those remotes and commit objects remain available,
but their unpushed user work cannot be recreated by this script.

The eventual maintainer guide must add exact package-index/editor generation,
workspace build/test/update/lock/restore syntax, clean-machine drills,
platform-specific compiler prerequisites, cross-repo rollback, and CI secrets
without their values. Those capabilities are not implemented in this candidate.
