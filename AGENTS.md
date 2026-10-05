# Workspace agent rules

Read `CODEX_START.md` once if present, then `TECHNOLOGY.md` and
`MAINTAINERS.md` before making a change. The first chat removes the tracked
bootstrap prompt through a PR; do not recreate it. These guides and the
versioned ecosystem/chat maps remain durable. Treat `workspace.toml` and `workspace.lock` as
paired contracts. Do not activate planned remotes or overwrite child work.

Use Bash commands in instructions to the owner; never give PowerShell.
Preserve unrelated files and concurrent changes. Follow the branch, focused
test, `dev` integration, full-suite-on-`main`, documentation review reset, and
release-hold rules in `MAINTAINERS.md`. The user prefers to be taught what to
write; implement only on explicit request.

Use issues for substantive work, linked PRs into `dev`, and the organization
Project for cross-repo milestones when accessible. Record focused tests,
exact pins, and integration impact; track blocked Project access in the issue.

Route by owner: `sagan` language/toolchain, `sagan-vscode` editor,
`sagan-physics` numeric physics, `sagan-render` rendering,
`sagan-workspace` exact-lock integration, `sagan-docs` official site, and
`sagan-space-game` application/design. Handoffs to another chat must include
goal, evidence, constraints, pins, and verification.
