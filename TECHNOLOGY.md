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

The dependency direction is outward: the workspace consumes language,
extension, docs, physics, rendering, and game checkouts. Those repositories
must not import source code from this workspace to build their own products.
The current candidate has only exact checkout bootstrap/status; package-index
generation, editor workspace generation, lock refresh, build, focused tests,
and full integration tests remain later milestones in
[the roadmap](docs/contributing/repository-fracturing-roadmap.md).

The lock is about source compatibility. Release manifests and Sagan package
locks retain their own meaning; a workspace lock does not declare a public
release, upload an artifact, or override the current release pause. The
operational commands and recovery paths live in [MAINTAINERS.md](MAINTAINERS.md).
