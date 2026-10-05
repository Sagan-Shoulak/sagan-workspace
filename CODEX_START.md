# Starting a new Sagan workspace chat

Read `AGENTS.md`, `TECHNOLOGY.md`, `MAINTAINERS.md`, `README.md`,
`workspace.toml`, `workspace.lock`, the fracture
roadmap, and the versioned ecosystem and chat maps. Start read-only: inspect
branch, HEAD, status, staged paths, concurrent work, and the exact checked-out
dependencies. Summarize what belongs to this workspace and what belongs to
each component repository. Ask before broadening scope or changing remote
state. This is a public split repository; do not mistake its planned
component entries for published or active dependencies.

Prefer teaching me what to code through small steps, examples, pseudocode,
review, and verification. Do not implement unless explicitly requested.
Rendering, physics, and game code likewise require an explicit request.
Never assume the language is secure.

For authorized changes, create a `codex/<request>` branch from current `dev`.
Test the affected work and refine until it passes. Stage only intended paths,
merge into `dev`, and rerun relevant tests against concurrent integration.
Reserve the full suite for `dev`-to-`main` promotion or release. The release and
`main` promotion hold remains in effect until the owner explicitly lifts it.
Documentation edits must set the affected page to `review-needed`,
`publication_ready: false`, and clear verification metadata. Do not run
unrelated documentation examples for a structural-only edit.

Use the versioned chat map to identify the owning specialized chat. For work
outside this repository, recommend that chat and provide a self-contained
ready-to-paste prompt with goal, evidence, constraints, dependency versions,
and verification. Do not assume another chat has this history. Use Bash, never
PowerShell. Preserve unrelated work; do not push, publish, release, deploy,
transfer, or change remote settings without current authorization.
