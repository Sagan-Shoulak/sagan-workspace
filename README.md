# Sagan workspace

This public repository coordinates ordinary sibling Git checkouts at exact
commits; it does not own their product code. The initial split preserves the
historical `repository-segmentation/` archive for provenance. The other
component repositories are not active yet, and cross-repository independence
has not been certified.

The current lock activates only the transferred primary `sagan` repository.
Other entries in `workspace.toml` are planned names,
not a claim that their GitHub repositories already exist. The source SHA is
an exact lock pin, not an automatically updated branch tip.

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
Build compiles the pinned primary compiler and language server. Test runs the
workspace contracts and the primary package-catalog/resolution tests, not
the full compiler suite. Future active components must provide their own
`scripts/workspace-build.sh` and `scripts/workspace-test.sh` entry points.
Editor-workspace generates ignored `build/sagan.code-workspace` from only
active, clean, exact-lock checkouts. It does not include planned repositories
or overwrite a differing editor file without explicit `--force`.

`scripts/package_index.py` also combines installed package catalogs from
separately checked-out physics and rendering repos. Its locked mode refuses
to run until those repos become active, clean, and pinned; the current
workspace lock intentionally has neither active. A separate explicit
`--component` mode supports local extraction rehearsals without pretending
that the planned GitHub repositories exist. The combined catalog is consumed
through `SAGAN_PACKAGE_INDEX`; see the exact rehearsal command in
[MAINTAINERS.md](MAINTAINERS.md).

Read [MAINTAINERS.md](MAINTAINERS.md) for the exact operating and recovery
workflow, [TECHNOLOGY.md](TECHNOLOGY.md) for the conceptual model, and
[CODEX_START.md](CODEX_START.md) to orient a new chat. The broader sequence
remains in [the fracture roadmap](docs/contributing/repository-fracturing-roadmap.md).
