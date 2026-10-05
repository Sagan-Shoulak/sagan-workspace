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

The carried `repository-segmentation/` inventories and old monorepo checker
are historical transfer evidence, not current workspace validation. That
checker fails explicitly in this standalone candidate. Use the focused
commands below and its own CI for current operation; retain the historical
records for audit and recovery context.

## Prerequisites and exact commands

Use Git Bash, Git, and Python 3.11 or newer. From the workspace repository root:

```bash
bash scripts/bootstrap.sh
bash scripts/status.sh
bash scripts/update.sh
bash scripts/build.sh
bash scripts/test.sh
bash scripts/lock.sh
bash scripts/editor-workspace.sh
bash scripts/restore-lock.sh
python -m unittest discover -s tests -p '*_test.py' -v
bash -n scripts/bootstrap.sh scripts/status.sh scripts/update.sh scripts/build.sh scripts/test.sh scripts/lock.sh scripts/editor-workspace.sh scripts/restore-lock.sh scripts/integrated-package-smoke.sh
```

`bootstrap.sh` and `status.sh` accept `--root`, `--manifest`, and `--lock` for
isolated test fixtures. Normal use needs no arguments. A zero status means
every active checkout is clean, has the manifest's exact origin URL, and is at
its locked commit. A missing, dirty, wrong-origin, or wrong-commit checkout
returns nonzero. No command here pushes, tags, changes a remote, or deletes a
checkout.

`update.sh` requires every active checkout to match the lock first. It fetches
only the manifest's `default_branch` from each exact origin with `--no-tags`,
reports the fetched tip, and leaves HEAD and `workspace.lock` unchanged. It
requires network; with several active repositories, fetches are sequential,
not atomic. Inspect any partial success before retrying.

`lock.sh` previews a proposed lock from clean children at their fetched
`origin/dev` tips. It refuses a dirty or wrong-origin child, a tip that is not
descended from the old lock, and a lock with extra release/artifact fields
that this first generator cannot preserve. The preview changes no file.
After running the focused build, tests, and integration checks at every
candidate revision, use `bash scripts/lock.sh --write` to atomically replace
`workspace.lock`; inspect and commit its diff with the test evidence. The
command does not run those checks for you. It only works after you have
deliberately selected each reviewed remote tip in the corresponding clean
child checkout. If a child should remain at its old pin, do not advance the
lock merely because a newer remote tip exists.

`build.sh` requires every active checkout to be clean at the exact lock.
For the primary `sagan` checkout it invokes `mingw32-make` on Windows or
`make` elsewhere for `bin/sagan` and `bin/sagan-lsp`. Use `--make PATH` to
select a known compatible make executable. `test.sh` runs this workspace's
offline unit tests, then builds and executes only the primary's focused
package-catalog and package-resolution test binaries. It does not run the
full compiler suite. Both commands may create ignored build outputs inside
the child. Every future active component must provide its own reviewed
`scripts/workspace-build.sh` and `scripts/workspace-test.sh`; an absent script
is an error, never a silently skipped component. Component-owned scripts
run inside their own checkout after exact-lock verification.

`editor-workspace.sh` requires every active checkout to pass the same exact
origin, clean-tree, and locked-HEAD checks as `status.sh`. It writes ignored
`build/sagan.code-workspace` with the coordinator and active child folders,
using paths relative to that file. Run it after bootstrap, then open the
generated file in VS Code. It is idempotent when the file already matches.
If the existing file differs, inspect your editor customizations first; only
then use `bash scripts/editor-workspace.sh --force` to replace it. A missing
or dirty child fails before changing the generated file. The generator does
not clone, reset, delete, or retarget a child repository.

`restore-lock.sh` accepts the same options. It clones a missing checkout;
otherwise it requires the exact manifest origin and a clean working tree,
fetches a missing locked commit without tags, and detaches HEAD at that
commit. It does not reset or discard tracked/untracked work. Git is instructed
not to overwrite ignored files; a collision fails and leaves HEAD unchanged.
It may change files in a clean child checkout, so inspect status and the lock
before invoking it. It does not change remote settings or push.
When more than one repository is active, restoration is sequential rather
than atomic: if a later checkout fails, earlier clean checkouts may already
be at their pins. Run `bash scripts/status.sh` and inspect the failure before
retrying; do not assume an all-or-nothing rollback.

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
  verification or run `bash scripts/restore-lock.sh` to select the pinned
  commit in a clean child.
- `update` failed after an earlier child fetched: the earlier child remains
  at its locked HEAD. Run `bash scripts/status.sh`, inspect the failed
  remote/network, and retry after resolution; do not infer an atomic fetch.
- `lock` refused a candidate: inspect origin, status, fetched `origin/dev`,
  and ancestry against the old pin. Do not force-push or rewrite the lock to
  hide a divergent candidate. Preserve a copy of any reviewed prior lock
  before a deliberate version migration.
- `build` or `test` failed: inspect the failing child, toolchain, and ignored
  output. Keep its lock pin unchanged and rerun only the affected focused
  checks after repair; do not delete the child or run the full suite merely
  to conceal a local prerequisite problem.
- `clone` or `checkout` failed: inspect the reported partial directory and
  network/credentials. Do not overwrite it automatically. If it contains
  useful state, back it up before a manual recovery.

The current local-only primary backup cannot survive loss of this computer
and cannot recreate GitHub settings, secrets, issues, or PR history. The
workspace lock is not a backup. Follow the primary repository's transfer and
backup runbook before any further remote migration. Generated checkouts can be
recreated from the remotes if those remotes and commit objects remain available,
but their unpushed user work cannot be recreated by this script.

## Combined package catalog and local integration rehearsal

When physics and rendering become active, reviewed entries in both the
manifest and lock, use this from the workspace root:

```bash
bash scripts/status.sh
python scripts/package_index.py --from-lock
export SAGAN_PACKAGE_INDEX="$(pwd)/.sagan-package-index.tsv"
```

Today, `--from-lock` deliberately fails because neither split package repo
is active. Do not activate an uncreated remote to make it pass. For the
extracted **local candidates only**, put their checkout directories under
one common parent and provide that parent explicitly. For example, when
the candidate directories are siblings of this workspace candidate under
the Sagan monorepo's ignored `build/`:

```bash
candidate_root="$(cd .. && pwd)"
physics_dir="$candidate_root/segmentation-physics-functional-20261005"
render_dir="$candidate_root/segmentation-render-functional-20261005"
game_dir="$candidate_root/segmentation-game-functional-20261005"
python scripts/package_index.py --root "$candidate_root" \
  --output segmentation-package-index.tsv \
  --component sagan-physics="${physics_dir##*/}" \
  --component sagan-render="${render_dir##*/}"
bash scripts/integrated-package-smoke.sh \
  "$candidate_root/segmentation-package-index.tsv" \
  /c/Users/joeps/coding/sagan/bin/sagan.exe \
  "$physics_dir" "$render_dir" "$game_dir"
```

The generator refuses a differing existing output unless `--force` is
specified, checks package manifest names/versions and path containment,
and rejects duplicate package identities. The smoke script runs the game,
three headless physics checks, and on Windows only, two auto-closing native
render checks against that one catalog. It creates normal ignored test
outputs inside the candidate checkouts; inspect those paths before any
cleanup. This is a local compatibility rehearsal, not independent CI or
permission to publish split repositories.

Focused verification for a catalog change is:

```bash
python -m unittest discover -s tests -p '*_test.py' -v
bash -n scripts/bootstrap.sh scripts/status.sh scripts/update.sh scripts/build.sh scripts/test.sh scripts/lock.sh scripts/editor-workspace.sh scripts/restore-lock.sh scripts/integrated-package-smoke.sh
```

The eventual maintainer guide must add clean-machine drills,
platform-specific compiler prerequisites, cross-repo rollback, and CI secrets
without their values. Those capabilities are not implemented in this candidate.
The draft `.github/workflows/workspace-checks.yml` runs the offline contract
tests on Linux, Windows, and macOS without fetching planned split remotes;
it remains locally reviewed only, not a successful hosted CI run.
