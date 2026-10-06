---
title: Workspace technology overview
status: review-needed
publication_ready: false
verified_in: null
verified_on: null
verified_by: null
---

# Workspace technology overview

The workspace is an integration coordinator, not a package manager or a
replacement for the component repositories. Each child in `checkouts/` is a
normal Git repository. Development, versioning, and release ownership remain
with that child. The workspace records which exact revisions have been tested
together and hosts cross-repository examples and compatibility evidence.

The carried `repository-segmentation/` tree is a provenance record from the
intact monorepo transfer and extraction rehearsals. Its old path manifests
and transfer audit do not describe the live standalone workspace. The active
contracts are the root manifest/lock and the focused workspace commands;
the historical segmentation checker refuses to pass in this repository.

`workspace.toml` maps stable component IDs to owner
URLs, local checkout names, and lifecycle states. Only `active` entries are
bootstrapped. `planned` entries are proposals; `existing-outside-organization`
and `archived` entries are also excluded. `workspace.lock` must contain one
matching URL and full commit SHA for every active entry, and no others.
There is no implicit fallback to `dev` or the latest release.

`scripts/workspace.py` validates that pair before touching a checkout.
Bootstrap clones a missing active repository and detaches at the lock SHA;
status compares its origin, working-tree cleanliness, and HEAD. The strict
origin check prevents a coincidentally matching commit from silently standing
in for a different owner. An existing checkout is treated as user work and is
never auto-reset or auto-deleted. Restore-lock explicitly moves only clean,
correct-origin checkouts to the pin and refuses to overwrite ignored files.
A clone or checkout failure leaves any
partial directory for inspection. The Bash entry points are thin wrappers so
Windows, Linux, and macOS share the same rules.
Update fetches the manifest's normal branch without moving a child HEAD or
rewriting `workspace.lock`. Lock refresh accepts only a clean checkout at
the fetched remote branch tip that descends from the current pin. It previews
by default; an explicit write atomically records the reviewed SHA. A child
must be built and tested at its candidate revision before that write. The
current minimal lock format has no extra release/artifact fields; lock
refresh refuses to discard such fields if they appear later.
Build and test first require all active sources to match the lock. The
coordinator generates the combined package index, builds the pinned compiler
and language server, and passes their paths to the component-owned Bash
hooks. The docs hook also receives the coordinator's Python executable.
Focused test runs workspace contracts, language package-catalog and
package-resolution binaries, and each active component's own test hook; no
unreviewed manifest shell command is run. Component hooks must exist before
activation. This source-level workflow does not imply installed-artifact or
release validation.
The editor generator reads the same validated active set and checks each
checkout before writing a VS Code multi-root file under ignored `build/`.
Its folder paths are relative to the generated file, so the workspace root
and child repositories can be opened together without copying product code.
It refuses to replace a differing file unless the maintainer explicitly
uses `--force`; planned repositories never appear as phantom editor roots.

The dependency direction is outward: the workspace consumes language,
extension, docs, physics, rendering, and game checkouts. Those repositories
must not import source code from this workspace to build their own products.
The workspace also combines the installed package rows from the
physics and rendering component catalogs into one generated index. It
rebases each manifest path under a common root, validates manifest identity,
and rejects duplicate package versions or paths escaping that root. Locked
mode requires clean, exact-revision active checkouts; explicit component mode
is for local extraction rehearsals only. The generated index is not a
workspace lock or a package release.

An offline contract workflow runs on GitHub-hosted Linux, Windows, and macOS.
Each component also has independent focused CI. Installed-artifact and
release validation remain later milestones in
[the roadmap](docs/contributing/repository-fracturing-roadmap.md).

The lock is about source compatibility. Release manifests and Sagan package
locks retain their own meaning; a workspace lock does not declare a public
release, upload an artifact, or override the current release pause. The
operational commands and recovery paths live in [MAINTAINERS.md](MAINTAINERS.md).
