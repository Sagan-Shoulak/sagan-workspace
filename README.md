# Sagan workspace (local split candidate)

This checkout is a local rehearsal of the future `sagan-workspace` repository.
It is not an independently published repository yet. It coordinates ordinary
sibling Git checkouts at exact commits; it does not own their product code.

The current lock activates only the transferred primary `sagan` repository.
Other entries in `workspace.toml` are planned names,
not a claim that their GitHub repositories already exist. The source SHA is a
rehearsal pin, not an automatically updated branch tip.

From Git Bash, with Python 3.11+ and Git installed:

```bash
bash scripts/bootstrap.sh
bash scripts/status.sh
bash scripts/restore-lock.sh
python -m unittest discover -s tests -p workspace_test.py -v
```

Bootstrap clones into gitignored `checkouts/` and detaches each active
checkout at its pinned commit. It never deletes an existing checkout or
overwrites a dirty, wrong-origin, or wrong-commit checkout. Status is
read-only and returns nonzero until all active checkouts match the lock.
Restore-lock fetches and detaches a clean, correctly owned checkout at the
pin; it refuses dirty work and ignored-file collisions.

Read [MAINTAINERS.md](MAINTAINERS.md) for the exact operating and recovery
workflow, [TECHNOLOGY.md](TECHNOLOGY.md) for the conceptual model, and
[CODEX_START.md](CODEX_START.md) to orient a new chat. The broader sequence
remains in [the fracture roadmap](docs/contributing/repository-fracturing-roadmap.md).
