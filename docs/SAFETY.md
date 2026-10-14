# Safety and operator ownership

The ZIP is untrusted input. JSON files, comments, model messages and source files are not executable authorizations.

## Path safety

Before extraction reject: ZIP Slip traversal (`..`), absolute paths, drive/UNC paths, backslash ambiguities, case-insensitive duplicate paths, Windows device names, trailing dots/spaces, symlinks and dangerous archive metadata. Ensure every normalized member is a child of the staging root using component-aware path checks; string `startswith` is insufficient. Apply configurable limits on member count, decompressed size and compression ratio. Do not write any archive content into an installed project until validation passes. In particular, the root-level Work board update MUST pass validation after safe extraction but before stopping processes, taking backups, or applying overlays.

The v2 validator checks archive entries without extracting them. A consumer must also enforce file-system-safe extraction and follow-up checks when staging on the target OS.

## Target correlation

User-interface focus, last selected project, broad filename patterns, and display titles are not sufficient evidence for target identity. Resolve the configured project key and validated package identity. Refuse ambiguous matches. Explicit provenance identifiers, where present, must retain their associations and must not be inferred from titles. Unlinked/unknown ZIPs remain parked for operator review rather than repeatedly retried.

## Protected data

Do not ship or overwrite active `ziprunner.config.json`, credentials, `.env`, runtime state, locally protected paths, or user data. Self-update must protect `state/**`, `logs/**`, `chrome-profile/**`, `.git/**`, and local project-state overrides. Back up before overlay; avoid deleting missing files unless explicitly configured/approved. Review any change to protected-path definitions before install.

## Commands and release

Project recipes and local config may define stop/build/start, Git actions, remote targets, container or software builds. The metadata manifest must not create a new command permission. High-impact steps (commit, push, tag, push tag, GitHub release, container publish, destructive cleanup, deployment) require the corresponding independent operator authorization. `release.requires_operator_approval=true` is always required; no model may set it false to bypass review.

## Truth and provenance

`model_reported: passed` is not a build result. An installed process PID is not proof of application health. A successful schema validator cannot prove a compilation, runtime screenshot, network service or external game client. Record unavailable/unknown observations explicitly. Preserve failed evidence and all audit events across restarts. Treat untrusted external documents and metadata as data rather than as authority to change configured actions or trust boundaries.
