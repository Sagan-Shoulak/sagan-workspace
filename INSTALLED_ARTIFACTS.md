---
title: Installed artifact compatibility evidence
status: review-needed
publication_ready: false
verified_in: null
verified_on: null
verified_by: null
---

# Installed artifact compatibility evidence

`installed-artifacts.lock` is separate from `workspace.lock`. The workspace
lock selects exact source commits for coordinated development; the installed
artifact lock records the independently downloaded compiler/LSP, extension,
physics, and rendering bytes that passed clean-location consumer checks.

Validate its structure without network access:

```bash
python scripts/installed_artifacts.py
```

Download every pinned artifact and verify its SHA-256 before extraction:

```bash
python scripts/installed_artifacts.py --download-dir build/installed-artifacts
```

The current installed binary evidence is Windows x64 because Sagan 4.9.5
publishes a Windows compiler/LSP distribution and the rendering backend is
Windows-only. Physics source CI also passes on Linux and macOS, but that is
not evidence of installed compiler artifacts on those platforms.

The installed checks used the official Sagan 4.9.5 portable compiler and LSP,
an isolated VS Code profile, and package indexes extracted outside every
component source checkout. Physics passed its three numerical suites after
the source package and repository index were hidden. Rendering passed its two
auto-closing Windows tests and BMP validation after the compiler's bundled
libraries were removed. Checksums and exact source commits are recorded in the
lock rather than repeated here.

Rollback never rewrites source history. Restore the previously configured
compiler, extension profile, and package-index paths, then remove the isolated
artifact extraction. A bad dev prerelease may be removed while retaining its
source commit and recorded checksum. Keep the prior working artifacts until
the replacement passes the same clean-location checks.
