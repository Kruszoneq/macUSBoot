# AGENTS.md for macUSBoot

This file defines how AI coding agents work in this repository.

## Scope and precedence

- This repository intentionally keeps `AGENTS.md` under `docs/`.
- Direct user instructions have priority except for the protected-branch and
  physical-device safety rules defined here.
- If instructions conflict with a safety rule, follow the safer rule and ask
  for clarification when the conflict materially affects the task.
- `docs/AGENTS.md` is the single source of truth for agent workflow, commits,
  pull requests, documentation, and changelog rules.

## Mandatory context bootstrap

Before implementation, recommendation, or review:

1. Read this file in full.
2. Read the documents and source files relevant to the task.
3. Read `README.md` when public behavior, scope, compatibility, or entry-point
   guidance may be affected.
4. Before editing, inspect the active branch, `git status`, and existing local
   changes.
5. Trace the relevant callers, consumers, build rules, layouts, and interfaces
   before changing behavior.
6. Inspect history, the complete source tree, or unrelated documents only when
   they are needed to resolve scope, ownership, or ambiguity.
7. Apply one consistent ruleset to the task before making changes.

## Repository map and documentation ownership

- Agent process rules: `docs/AGENTS.md`
- Public project scope and entry point: `README.md`
- Runtime, disk layout, compatibility, and source modules:
  `docs/Architecture.md`
- Public Release and Debug build interface: `docs/Building.md`
- User-visible recovery guidance: `docs/Troubleshooting.md`
- Source and licensing provenance: `docs/SourceProvenance.md`
- Versioned release notes: `docs/CHANGELOG.md`
- Production sources: `Source/`
- Artifact and build support tools: `Tools/`
- Local temporary work notes: `tmp/` (ignored by Git and non-authoritative)

Each fact should have one canonical owner. Other files should summarize it only
when necessary and link to the owning document.

## Documentation as the current source of truth

- Update documentation whenever released behavior, artifacts, build
  requirements, compatibility, or architecture changes.
- Describe the actual current implementation, not a planned design presented
  as complete.
- Keep process rules only in `docs/AGENTS.md`.
- Keep product and technical documentation directly under `docs/`.
- Keep `README.md` concise and public-facing.
- Keep links and paths current and avoid duplicating contracts across files.
- Public documentation must not describe internal test suites, test scenarios,
  test environments, validation reports, transcripts, evidence registers, or
  development-history ledgers.
- Runtime or artifact validation may be documented when it is part of the
  product's actual behavior or public build interface.
- macUSB owns installation and integration instructions; do not reproduce them
  in the macUSBoot documentation.
- Proposals, experiments, raw results, and local evidence do not belong in
  release documentation.

## Temporary working notes

- Use the ignored repository-root `tmp/` directory for task-specific text notes
  when ongoing work needs a durable local record.
- Notes are disposable, non-authoritative, and must never replace source or
  documentation.
- Do not store credentials, secrets, licensed Windows content, media images,
  raw sector dumps, or other sensitive or large artifacts in `tmp/`.
- Promote only current release-relevant conclusions and remove task notes when
  the work is complete.

## Workflow

Use this sequence in proportion to the task:

1. Complete the mandatory context bootstrap.
2. Analyze the current behavior and affected interfaces.
3. Implement only the requested change.
4. Run relevant non-destructive validation or report why it could not run.
5. Update the canonical documents affected by the change.
6. Edit `docs/CHANGELOG.md` only when the user explicitly requests it.
7. Prepare a commit only when committing is part of the user's request.

## Definition of done

A change is done when all applicable conditions are met:

- the requested behavior is implemented;
- relevant validation ran, or its blocker was reported;
- affected documentation matches the implementation;
- links and paths are current;
- unrelated local changes remain preserved;
- when a commit was requested, its content and message follow this file.

## Change classification

- Public scope or entry guidance changed: update `README.md`.
- Runtime, source ownership, boot flow, disk layout, memory behavior, or
  compatibility changed: update `docs/Architecture.md`.
- Artifact packaging changed: update `docs/Building.md` when its public output
  description is affected.
- Build commands, dependencies, outputs, or supported configurations changed:
  update `docs/Building.md`.
- User-visible errors or recovery changed: update `docs/Troubleshooting.md`.
- Source or licensing provenance changed: update
  `docs/SourceProvenance.md`.
- User-facing release history changed: update `docs/CHANGELOG.md` only on
  explicit user request.
- Documentation-only changes should update only their canonical owner and
  necessary cross-references.

## Decision and escalation rules

- Ask before implementing when ambiguity or competing approaches would
  materially change behavior, compatibility, safety, or public scope.
- Use reasonable judgment for low-risk implementation details that do not
  change the requested outcome.
- Safe fallback methods are allowed when they preserve the requested behavior
  and do not expand scope; report any meaningful fallback used.
- If blocked, report what was established, what remains, and the exact blocker.
- Pause before destructive code, history, branch, or device actions that are
  not already explicit in the user's request.

## Physical USB development handoff

- macUSB is the only supported way for users to create complete installation
  media. Manual writes are an exceptional development procedure used when
  validating bootloader changes without recreating the complete medium.
- An agent must never perform or automate a raw physical-device write through
  its shell, `osascript`, AppleScript, a scripted Terminal, another application,
  or a privilege prompt.
- The agent may perform authorized read-only device identification and generate
  explicit commands for the user to paste into an interactive Terminal.
- Resolve and revalidate the exact current `/dev/diskN` identity before
  generating commands. Use the corresponding explicit `/dev/rdiskN` target;
  never use variables, wildcards, command substitutions, or historical device
  numbers.
- Reidentify the device after every reconnect or restart.
- Account for macOS Disk Arbitration remounting removable media. Put
  `diskutil unmountDisk force /dev/diskN && sudo dd ...` immediately before
  every separate raw write.
- Preserve the StageTwo-first, MBR-last order. If `dd` reports `Resource busy`,
  instruct the user to repeat the complete unmount-and-write pair for that
  operation, never `dd` alone.
- After presenting commands, wait for the user to report execution and the
  physical result. Generated commands are not evidence that a write occurred.

## Code structure and file size

- Keep files and modules focused on one clear responsibility.
- When a change materially enlarges a file or mixes concerns, evaluate and
  perform a behavior-preserving split when it improves clarity and safety.
- Keep one clear workflow orchestrator and separate policies, formats,
  platform details, and I/O where appropriate.
- Treat structural refactors as behavior-preserving unless the user explicitly
  requests a behavior change.

## File naming

- Follow established repository conventions and use concise, descriptive
  names.
- Preserve exact names required by BIOS behavior, disk formats, filesystems,
  assemblers, compilers, build systems, packaging formats, or other external
  contracts.
- Do not rename a constrained file merely for stylistic consistency.
- Document non-obvious filenames that form part of a public build or boot
  contract.

## Branch naming

When branch creation is requested:

- use `<type>/<short_descriptive_topic>`;
- keep the topic short and readable;
- separate topic words with underscores;
- examples: `feature/bios_stage`, `improvement/image_build`,
  `fix/boot_guard`.

## Branch and merge safety

### `development`

- `development` contains ongoing development and is the default base for task
  branches.
- `development` is permanently non-deletable.
- Never delete `development`, even when explicitly requested.

### `main`

- `main` contains release states and is permanently non-deletable.
- Never commit or merge to `main` automatically.
- Release pull requests to `main` are allowed only from `development`.
- A merge to `main` requires explicit user instruction and confirmation.
- Never delete `main`, even when explicitly requested.

### New branches

- Create task branches from `development` by default.
- A non-`main` current branch may be used as the base when the work is clearly
  scoped to it.
- Do not create branches from `main` unless the user explicitly confirms that
  exception.

## Commit rules

### Scope and message

- Create a commit only when the user requests it.
- Commit only files belonging to the current task.
- If a modified file appears unrelated, inspect and describe it, then ask
  whether to include, exclude, or handle it separately.
- Never silently include, discard, restore, or overwrite unrelated changes.
- Write commit messages in English with a clear title and one short paragraph.
- Base the title and body on the task and the complete changes actually being
  committed, including Debug changes when applicable.
- Use normal multiline commit formatting, never escaped `\n` sequences.

### Approval gate

- Before committing, present the proposed title and body for explicit user
  approval.
- If wording changes, present the revised message and request approval again.
- Do not run `git commit` before approval.

### Push and reporting

- After a successful commit, push it immediately to the corresponding remote
  branch.
- Set the upstream during the push when necessary.
- If the push fails, report the blocker and stop follow-up remote operations.
- Report the commit hash, committed scope, final message, push result, and
  whether the working tree is clean.

## Pull request rules

### Content and approval

- Write PR titles and descriptions in English.
- Keep the title short and directly related to the task.
- Start the description with one clear paragraph explaining what changed and
  why; add a short flat list only when it improves clarity.
- Describe the actual scope, including Debug changes when applicable.
- Do not include testing information in the PR description.
- Present the proposed title and description for explicit approval before
  creating the PR.

### After creation or merge

- Report the PR number and URL, source and target branches, included scope,
  final title and description, and working-tree state.
- If merge was not already requested, ask whether the PR should be merged.
- After a merge, ask whether the source branch should be deleted unless it is
  `development`.

## Changelog rules

### General rules

- `docs/CHANGELOG.md` contains release entries only.
- Write changelog entries in English.
- Edit the changelog only on explicit user request.
- Present proposed changelog text for approval before applying it.
- Verify entries against shipped behavior and the canonical documentation.
- Keep wording concise, factual, user-oriented, and suitable for GitHub
  Releases.
- Omit marginal implementation details and unverifiable marketing claims.

### Release format

- Use only the bootloader version as the release heading, for example `## v1.0`
  or `## v1.0.1`.
- Begin with one short summary paragraph covering the release.
- Update that paragraph when the release scope changes.
- Use only the sections needed for the release; `ADDED`, `CHANGES`, and
  `IMPROVEMENTS` are available but not mandatory.
- Sections are optional for small patch releases.

### Bullet style

- Describe user-visible behavior rather than filenames or internal components.
- State relevant conditions such as firmware mode, filesystem, or architecture.
- Use one bullet for one coherent topic and split only genuinely separate
  changes.
- Include technical context only when it helps users understand visible impact.

## Explicit non-goals

- Do not create or maintain Copilot-specific instruction files unless the user
  explicitly requests them.
- Do not assume release signing, publication, or distribution responsibility
  unless explicitly requested.

## Reporting requirements

Report in proportion to the task:

- files changed;
- decisions taken and why;
- validation performed and its outcome;
- actions intentionally not performed;
- relevant remaining uncertainty, blocker, or risk.

For complex work, distinguish confirmed facts from interpretations and briefly
explain newly introduced technical terms.
