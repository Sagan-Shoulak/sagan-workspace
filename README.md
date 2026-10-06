# Sagan workspace

This public repository coordinates ordinary sibling Git checkouts at exact
commits; it does not own their product code. The initial split preserves the
historical `repository-segmentation/` archive for provenance. The primary
language, official docs, physics, rendering, and VS Code extension are active
at reviewed source pins. The game stays separate from the default workspace.

The source SHAs in `workspace.lock` are exact pins, not automatically updated
branch tips. `sagan-workspace` itself and `sagan-space-game` remain planned in
the manifest rather than being recursively bootstrapped.

From Git Bash, with Python 3.11+ and Git installed:

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
```

Bootstrap clones into gitignored `checkouts/` and detaches each active
checkout at its pinned commit. It never deletes an existing checkout or
overwrites a dirty, wrong-origin, or wrong-commit checkout. Status is
read-only and returns nonzero until all active checkouts match the lock.
Restore-lock fetches and detaches a clean, correctly owned checkout at the
pin; it refuses dirty work and ignored-file collisions.
Update fetches the current `dev` tip without moving any checkout or lock.
Lock previews clean, fast-forward `origin/dev` tips and changes the lock only
with `bash scripts/lock.sh --write` after focused compatibility checks.
Build compiles the pinned primary compiler and language server, creates the
combined physics/rendering package index, and calls each active component's
own `scripts/workspace-build.sh`. Test runs the workspace contracts, focused
primary package tests, and each component's `scripts/workspace-test.sh`, not
the full compiler suite. The coordinator supplies exact compiler, index, and
Python paths to those hooks.
Editor-workspace generates ignored `build/sagan.code-workspace` from only
active, clean, exact-lock checkouts. It does not include planned repositories
or overwrite a differing editor file without explicit `--force`.

`scripts/package_index.py` also combines installed package catalogs from
separately checked-out physics and rendering repos. Its locked mode requires
both to be active, clean, and pinned. A separate explicit `--component` mode
supports isolated extraction rehearsals. The combined catalog is consumed
through `SAGAN_PACKAGE_INDEX`; see the exact rehearsal command in
[MAINTAINERS.md](MAINTAINERS.md).

Read [MAINTAINERS.md](MAINTAINERS.md) for the exact operating and recovery
workflow, [TECHNOLOGY.md](TECHNOLOGY.md) for the conceptual model, and
`CODEX_START.md` once if it still exists, then `AGENTS.md` for lasting chat
guidance. The broader sequence
remains in [the fracture roadmap](docs/contributing/repository-fracturing-roadmap.md).
