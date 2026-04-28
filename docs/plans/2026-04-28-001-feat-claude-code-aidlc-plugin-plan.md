---
title: "feat: Add Claude Code plugin for AIDLC methodology"
type: feat
status: completed
date: 2026-04-28
origin: docs/brainstorms/2026-04-28-claude-code-aidlc-plugin-requirements.md
---

# feat: Add Claude Code plugin for AIDLC methodology

## Overview

Package the AIDLC methodology as a Claude Code plugin so users can install it with a single command instead of manually copying rule files into their workspace. The plugin provides an orchestrator agent, phase-specific slash commands, and 7 skills that bundle the canonical rule content. A generator script produces plugin files from the source rules, and CI enforces they never drift.

## Problem Frame

The current Claude Code onboarding requires downloading a zip, extracting it, copying `core-workflow.md` as `CLAUDE.md` (overwriting existing project instructions), and copying `aws-aidlc-rule-details/` into the workspace. This is the worst onboarding path of the 8 supported platforms — it overwrites user config, pollutes the project with methodology files, has no update path, and provides no interactive guidance. (see origin: docs/brainstorms/2026-04-28-claude-code-aidlc-plugin-requirements.md)

## Requirements Trace

- R1. Plugin installs via `claude plugin install` from the git repo URL
- R2. Orchestrator agent drives the three-phase workflow, detecting current phase from workspace state
- R3. Slash commands (`/aidlc`, `/aidlc:inception`, `/aidlc:construction`, `/aidlc:operations`) dispatch to the orchestrator
- R4. Seven skills provide methodology content organized by phase and cross-cutting concern
- R5. Rule-details content loads exclusively from `${CLAUDE_PLUGIN_ROOT}/skills/*/references/` — no workspace fallback
- R6. Generator script produces plugin content from canonical `aidlc-rules/` source files
- R7. CI enforces sync via `git diff --exit-code` after regeneration
- R8. Plugin version tracks `aidlc-rules/VERSION`

## Scope Boundaries

- In scope: Plugin structure, agent, commands, skills, generator script, CI sync job, labeler/CODEOWNERS updates
- Not in scope: Changes to canonical rule files, other platform delivery methods, marketplace publishing, MCP servers, hooks
- Deliberate divergence: The `aidlc-core-workflow` skill replaces the path-resolution section (lines 13-20 of `core-workflow.md`) with plugin-native paths. The generator handles this transformation.

## Context & Research

### Relevant Code and Patterns

- `aidlc-rules/aws-aidlc-rules/core-workflow.md` — 540-line entry point with path-resolution at lines 13-20
- `aidlc-rules/aws-aidlc-rule-details/` — 29 rule files organized in `common/`, `inception/`, `construction/`, `extensions/`, `operations/`
- `aidlc-rules/VERSION` — currently `0.1.8`, updated by release workflow
- `.github/workflows/ci.yml` — markdownlint job, SHA-pinned actions, `permissions: {}` default
- `.github/labeler.yml` — auto-label rules for `rules`, `documentation`, `github`
- `.github/CODEOWNERS` — team ownership by directory
- `scripts/aidlc-evaluator/` — Python convention: uv-managed, ruff-linted, but CI uses inline pip installs
- Cross-references between rule files use relative paths like `inception/workspace-detection.md` and `../common/depth-levels.md`

### Key Conventions to Follow

- Action pinning: full SHA + version comment
- Workflow: `permissions: {}` default, per-job explicit permissions, concurrency groups
- File naming: kebab-case for markdown, snake_case for Python
- Commits: conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- Markdown: must pass `npx markdownlint-cli2 "**/*.md"` with the repo's config

## Key Technical Decisions

- **Generator is stdlib-only Python**: Avoids adding a Dependabot entry or CI dependency install. The script only needs `pathlib`, `os`, `json`, and string manipulation — no third-party libraries required.
- **Path-resolution transformation**: The generator replaces lines 13-20 of `core-workflow.md` (the 4-path workspace resolution) with a single directive pointing to `${CLAUDE_PLUGIN_ROOT}/skills/<phase>/references/`. All other relative path references (`common/process-overview.md`, `inception/workspace-detection.md`, etc.) are preserved as-is, because the `references/` directories maintain the same internal structure.
- **SKILL.md = handwritten index + generated references/**: Each skill's `SKILL.md` is a handwritten template (with frontmatter and trigger description) stored as a Jinja-like template in the generator. The `references/` subdirectory contains byte-identical copies of the canonical rule files. This keeps skill descriptions human-crafted for trigger quality while automating the content sync.
- **Orchestrator loads skills by reading SKILL.md**: The agent's system prompt instructs it to use the `Skill` tool or `Read` tool to load the appropriate phase skill, which in turn reads its `references/` files on demand — implementing the progressive-disclosure pattern.
- **Plugin install path**: `claude plugin install --from plugins/claude-code-aidlc` from a clone, or directly from the GitHub repo URL pointing to the `plugins/claude-code-aidlc` subdirectory.

## Open Questions

### Resolved During Planning

- **How does the orchestrator detect current phase?** By checking workspace for `aidlc-docs/aidlc-state.md` (primary signal — contains current phase/stage), falling back to directory existence (`aidlc-docs/inception/`, `aidlc-docs/construction/`). This matches the existing `session-continuity.md` resume protocol.
- **Which sections of core-workflow.md need path rewriting?** Only lines 13-20 (the "MANDATORY: Rule Details Loading" path-resolution block). The "Common Rules" section below it (lines 22-27) uses relative paths that resolve correctly against the preserved directory structure.
- **Should the generator emit SKILL.md programmatically or use templates?** Templates — each SKILL.md has a handwritten frontmatter block (name, description, version) and a brief index section, followed by instructions to read from `references/`. Templates live inside the generator script as string constants.

### Deferred to Implementation

- Exact wording of SKILL.md `description` fields — these control CC auto-activation and need testing with the actual plugin runtime
- Whether `${CLAUDE_PLUGIN_ROOT}` resolves correctly inside skill markdown content read by the agent (vs. only in hooks/commands) — verify during implementation; if not, use relative paths from the skill's own directory

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```text
Generator data flow:

  aidlc-rules/
  ├── VERSION ─────────────────────────────────────► plugin.json (version field)
  ├── aws-aidlc-rules/
  │   └── core-workflow.md ──[transform L13-20]──► skills/aidlc-core-workflow/references/core-workflow.md
  └── aws-aidlc-rule-details/
      ├── common/*.md ────────[copy]──────────────► skills/aidlc-common/references/common/*.md
      ├── inception/*.md ─────[copy]──────────────► skills/aidlc-inception/references/inception/*.md
      ├── construction/*.md ──[copy]──────────────► skills/aidlc-construction/references/construction/*.md
      ├── operations/*.md ────[copy]──────────────► skills/aidlc-operations/references/operations/*.md
      └── extensions/
          ├── security/**  ───[copy]──────────────► skills/aidlc-security-baseline/references/extensions/security/**
          └── testing/**  ────[copy]──────────────► skills/aidlc-property-testing/references/extensions/testing/**

  Generator also writes (from templates embedded in script):
  ├── .claude-plugin/plugin.json
  ├── agents/aidlc-orchestrator.md
  ├── commands/aidlc.md, aidlc-inception.md, aidlc-construction.md, aidlc-operations.md
  └── skills/*/SKILL.md  (7 skills, each with frontmatter + index)
```

```text
Plugin directory structure (generated output):

  plugins/claude-code-aidlc/
  ├── .claude-plugin/
  │   └── plugin.json                        # name: "aidlc", version from VERSION
  ├── agents/
  │   └── aidlc-orchestrator.md              # orchestrator agent definition
  ├── commands/
  │   ├── aidlc.md                           # /aidlc — main entry point
  │   ├── aidlc-inception.md                 # /aidlc:inception
  │   ├── aidlc-construction.md              # /aidlc:construction
  │   └── aidlc-operations.md                # /aidlc:operations
  └── skills/
      ├── aidlc-core-workflow/
      │   ├── SKILL.md                       # trigger: AIDLC workflow start
      │   └── references/
      │       └── core-workflow.md           # transformed copy
      ├── aidlc-inception/
      │   ├── SKILL.md                       # trigger: inception phase work
      │   └── references/
      │       └── inception/*.md             # copies of all inception rules
      ├── aidlc-construction/
      │   ├── SKILL.md
      │   └── references/
      │       └── construction/*.md
      ├── aidlc-operations/
      │   ├── SKILL.md
      │   └── references/
      │       └── operations/*.md
      ├── aidlc-common/
      │   ├── SKILL.md                       # trigger: AIDLC common rules
      │   └── references/
      │       └── common/*.md
      ├── aidlc-security-baseline/
      │   ├── SKILL.md                       # trigger: security extension opt-in
      │   └── references/
      │       └── extensions/security/**
      └── aidlc-property-testing/
          ├── SKILL.md                       # trigger: property testing opt-in
          └── references/
              └── extensions/testing/**
```

## Implementation Units

- [x] **Unit 1: Generator script**

**Goal:** Create the Python script that produces the entire plugin directory from canonical sources.

**Requirements:** R5, R6, R8

**Dependencies:** None — this is the foundational unit everything else depends on

**Files:**
- Create: `scripts/build-cc-plugin.py`

**Approach:**
- Single-file, stdlib-only Python script (no external dependencies)
- Accept optional `--output-dir` argument defaulting to `plugins/claude-code-aidlc`
- Read `aidlc-rules/VERSION` for version stamping
- Define SKILL.md templates, agent template, command templates, and plugin.json template as string constants inside the script
- Copy rule files preserving directory structure into `references/` subdirectories
- Transform `core-workflow.md` by replacing the path-resolution block (lines 13-20: the 4-path workspace check) with a single directive pointing to `${CLAUDE_PLUGIN_ROOT}/skills/*/references/`
- Clean and recreate the output directory on each run (ensures deleted source files don't leave orphans)
- Exit 0 on success, non-zero with message on failure

**Patterns to follow:**
- Python file naming: `build-cc-plugin.py` (kebab-case script, consistent with repo conventions)
- Existing evaluator scripts use `argparse` and `pathlib`

**Test scenarios:**
- Run script → output directory matches expected structure (all 7 skills, 4 commands, 1 agent, plugin.json)
- `core-workflow.md` in output has transformed path-resolution section, rest unchanged
- All `references/` files are byte-identical to their source (except core-workflow.md transformation)
- `plugin.json` version matches `aidlc-rules/VERSION` content
- Running script twice produces identical output (idempotent)
- Script fails gracefully if `aidlc-rules/` doesn't exist

**Verification:**
- Run script, then `diff -r` between source rule files and generated references (excluding the core-workflow transformation)
- `plugin.json` contains correct version string
- No files outside the expected structure in the output directory

---

- [x] **Unit 2: Plugin manifest and orchestrator agent**

**Goal:** Write the templates for `plugin.json` and the orchestrator agent that the generator will emit.

**Requirements:** R1, R2

**Dependencies:** Unit 1 (templates live inside the generator script)

**Files:**
- Modify: `scripts/build-cc-plugin.py` (add/refine templates)
- Verify output: `plugins/claude-code-aidlc/.claude-plugin/plugin.json`
- Verify output: `plugins/claude-code-aidlc/agents/aidlc-orchestrator.md`

**Approach:**
- `plugin.json`: minimal manifest with `name: "aidlc"`, `version` from VERSION, `description`, `repository` pointing to the GitHub repo, `license: "Apache-2.0"`
- Orchestrator agent frontmatter: `description` field triggers on AIDLC workflow requests ("software development workflow", "AIDLC", "inception phase", "construction phase", etc.)
- Agent system prompt instructs it to: (1) check for `aidlc-docs/aidlc-state.md` to detect resume state, (2) if new workflow, load the `aidlc-core-workflow` skill and display welcome message, (3) load the phase-appropriate skill based on current state, (4) load `aidlc-common` skill for cross-cutting rules, (5) at phase boundaries prompt user to proceed, (6) handle extensions opt-in during Requirements Analysis by loading the extension skills when user opts in
- Agent should reference skills by reading their SKILL.md content and then reading references/ files on demand

**Patterns to follow:**
- Plugin structure from `plugin-dev:plugin-structure` skill documentation
- Session continuity protocol from `aidlc-rules/aws-aidlc-rule-details/common/session-continuity.md`

**Test scenarios:**
- `plugin.json` is valid JSON with required `name` field
- Agent description triggers on phrases like "start AIDLC workflow", "inception phase", "build a new feature using AIDLC"
- Agent system prompt correctly references skill paths using `${CLAUDE_PLUGIN_ROOT}`

**Verification:**
- Generated `plugin.json` passes JSON parsing
- Agent markdown has valid YAML frontmatter with `description` field
- Agent instructions reference all 7 skills and describe the phase-detection logic

---

- [x] **Unit 3: Slash commands**

**Goal:** Write the templates for the 4 slash commands that the generator will emit.

**Requirements:** R3

**Dependencies:** Unit 2 (commands dispatch to the orchestrator agent)

**Files:**
- Modify: `scripts/build-cc-plugin.py` (add command templates)
- Verify output: `plugins/claude-code-aidlc/commands/aidlc.md`
- Verify output: `plugins/claude-code-aidlc/commands/aidlc-inception.md`
- Verify output: `plugins/claude-code-aidlc/commands/aidlc-construction.md`
- Verify output: `plugins/claude-code-aidlc/commands/aidlc-operations.md`

**Approach:**
- `/aidlc` (main entry): accepts a free-text description of the work, dispatches to the orchestrator agent with no phase hint — orchestrator auto-detects from workspace state
- `/aidlc:inception`: dispatches to orchestrator with `phase: inception` hint — starts or resumes inception
- `/aidlc:construction`: dispatches to orchestrator with `phase: construction` hint
- `/aidlc:operations`: dispatches to orchestrator with `phase: operations` hint
- Each command is a thin markdown file with YAML frontmatter (`name`, `description`) and body that instructs the agent what to do
- Commands should pass through any user-provided arguments (e.g., `/aidlc build a REST API` passes "build a REST API" to the orchestrator)

**Patterns to follow:**
- Command file format from `plugin-dev:command-development` skill documentation
- Naming: `aidlc.md`, `aidlc-inception.md` (kebab-case)

**Test scenarios:**
- Each command file has valid YAML frontmatter with `name` and `description`
- `/aidlc` with no args triggers welcome message flow
- `/aidlc build a REST API` passes the description to the orchestrator
- `/aidlc:inception` starts inception phase specifically

**Verification:**
- All 4 command files generated with correct frontmatter
- Command names match expected `/aidlc`, `/aidlc:inception`, `/aidlc:construction`, `/aidlc:operations`

---

- [x] **Unit 4: Skill templates (7 skills)**

**Goal:** Write the SKILL.md templates for all 7 skills and verify the generator copies references correctly.

**Requirements:** R4, R5

**Dependencies:** Unit 1 (templates embedded in generator, references copied by generator)

**Files:**
- Modify: `scripts/build-cc-plugin.py` (add/refine 7 SKILL.md templates)
- Verify output: `plugins/claude-code-aidlc/skills/aidlc-core-workflow/SKILL.md`
- Verify output: `plugins/claude-code-aidlc/skills/aidlc-inception/SKILL.md`
- Verify output: `plugins/claude-code-aidlc/skills/aidlc-construction/SKILL.md`
- Verify output: `plugins/claude-code-aidlc/skills/aidlc-operations/SKILL.md`
- Verify output: `plugins/claude-code-aidlc/skills/aidlc-common/SKILL.md`
- Verify output: `plugins/claude-code-aidlc/skills/aidlc-security-baseline/SKILL.md`
- Verify output: `plugins/claude-code-aidlc/skills/aidlc-property-testing/SKILL.md`

**Approach:**
- Each SKILL.md has three parts: (1) YAML frontmatter with `name`, `description`, `version`, (2) a brief overview of what the skill covers, (3) instructions to read specific files from `references/` on demand
- Skill descriptions must be specific enough to trigger correctly:
  - `aidlc-core-workflow`: triggers on AIDLC workflow initialization, starting a new development workflow
  - `aidlc-inception`: triggers on planning, requirements gathering, user stories, workspace detection, application design
  - `aidlc-construction`: triggers on functional design, NFR, infrastructure design, code generation, build and test
  - `aidlc-operations`: triggers on deployment, monitoring, operations planning
  - `aidlc-common`: triggers on AIDLC terminology, depth levels, question formatting, error handling, content validation — loaded as supporting context by other skills, not typically invoked directly
  - `aidlc-security-baseline`: triggers on security extension opt-in during AIDLC workflow
  - `aidlc-property-testing`: triggers on property-based testing extension opt-in during AIDLC workflow
- Extension skills include the opt-in prompt from the `.opt-in.md` file in their SKILL.md body, and instruct the agent to read the full rules file from `references/` only when the user opts in
- Skills reference files using relative paths from their own directory (e.g., `references/inception/workspace-detection.md`)

**Patterns to follow:**
- SKILL.md format from `plugin-dev:skill-development` documentation
- Progressive disclosure pattern: SKILL.md is lightweight, references loaded on demand

**Test scenarios:**
- All 7 SKILL.md files have valid YAML frontmatter
- Each skill's `references/` directory contains the expected files
- `aidlc-core-workflow/references/core-workflow.md` has the transformed path-resolution section
- Extension skills include the opt-in prompt text
- Common skill lists all 11 common rule files

**Verification:**
- Run generator → all 7 skill directories exist with SKILL.md + references/
- File count in each references/ directory matches source directory
- No orphaned files in references/ that don't exist in source

---

- [x] **Unit 5: Generate initial plugin output and validate**

**Goal:** Run the generator to produce the committed plugin directory and validate the output.

**Requirements:** R6, R8

**Dependencies:** Units 1-4

**Files:**
- Create (generated): entire `plugins/claude-code-aidlc/` directory tree

**Approach:**
- Run `python scripts/build-cc-plugin.py` from repo root
- Validate the generated output: correct structure, file counts, version stamping, content integrity
- Ensure all generated markdown passes `npx markdownlint-cli2`
- Commit the generated output — this becomes the baseline that CI checks against

**Test scenarios:**
- Generated directory structure matches the high-level technical design exactly
- `plugin.json` version is `0.1.8` (current VERSION)
- `core-workflow.md` transformation is correct (path-resolution block replaced, rest unchanged)
- All other reference files are byte-identical to source
- Running generator twice produces identical output
- `npx markdownlint-cli2 "plugins/**/*.md"` passes

**Verification:**
- `diff -r` between source rules and generated references (with expected exceptions)
- markdownlint passes on all generated files
- `python scripts/build-cc-plugin.py && git diff --exit-code plugins/` succeeds (no drift)

---

- [x] **Unit 6: CI sync enforcement**

**Goal:** Add a CI job that runs the generator and fails if committed plugin files don't match.

**Requirements:** R7

**Dependencies:** Unit 5

**Files:**
- Modify: `.github/workflows/ci.yml`

**Approach:**
- Add a new job `plugin-sync` alongside the existing `markdownlint` job
- Job: checkout, setup Python 3.x, run `python scripts/build-cc-plugin.py`, then `git diff --exit-code plugins/`
- Follow existing CI conventions: SHA-pinned actions, `permissions: { contents: read }`, concurrency group
- No Python dependencies to install (stdlib-only script)
- Job should have a descriptive name like "Plugin Sync Check"

**Patterns to follow:**
- Existing `markdownlint` job in `ci.yml` for structure
- SHA-pinned `actions/checkout` and `actions/setup-python` with version comments

**Test scenarios:**
- PR that changes a rule file without regenerating the plugin fails CI
- PR that changes a rule file AND regenerates the plugin passes CI
- PR that only touches non-rule files skips or passes the check quickly

**Verification:**
- CI workflow is valid YAML
- The `plugin-sync` job runs the generator and checks for drift
- Existing `markdownlint` job is unchanged

---

- [x] **Unit 7: Repository metadata updates**

**Goal:** Update labeler, CODEOWNERS, markdownlint config, and documentation for the new plugin directory.

**Requirements:** Supports all requirements (infrastructure)

**Dependencies:** Unit 5 (plugin directory must exist)

**Files:**
- Modify: `.github/labeler.yml`
- Modify: `.github/CODEOWNERS`
- Modify: `AGENTS.md`
- Modify: `README.md` (Claude Code section)
- Modify: `CONTRIBUTING.md`

**Approach:**
- `labeler.yml`: add a `plugin` label for `plugins/**` changes
- `CODEOWNERS`: add `plugins/` owned by `@awslabs/aidlc-admins @awslabs/aidlc-maintainers`
- `AGENTS.md`: add `plugins/claude-code-aidlc/` to repo structure section, note that content is generated by `scripts/build-cc-plugin.py`
- `README.md` Claude Code section: add a "Plugin Install (Recommended)" option above the current manual copy instructions, with the install command
- `CONTRIBUTING.md`: add a note that plugin content is generated — contributors should edit `aidlc-rules/` and run the generator, not edit `plugins/` directly

**Patterns to follow:**
- Existing labeler.yml format
- Existing CODEOWNERS alignment conventions
- README platform-specific setup section format

**Test scenarios:**
- Changes to `plugins/` get the `plugin` label in PRs
- CODEOWNERS covers the `plugins/` directory
- AGENTS.md accurately reflects the new directory

**Verification:**
- labeler.yml is valid YAML with correct glob pattern
- CODEOWNERS has aligned columns
- README install command is correct
- CONTRIBUTING.md mentions the generator script

## System-Wide Impact

- **Interaction graph:** The plugin introduces no runtime hooks, MCP servers, or event handlers. The orchestrator agent is invoked only via explicit slash commands or CC's agent auto-selection. No interaction with existing CLAUDE.md-based setups.
- **Error propagation:** If a user has both the plugin installed AND a manual CLAUDE.md setup, both will load. The plugin's R5 decision (plugin-only loading) means the orchestrator ignores workspace rule-details, but the CLAUDE.md content will still be in context. Users should remove their manual setup when switching to the plugin — document this in README.
- **CI impact:** New `plugin-sync` job adds ~15 seconds to CI (Python setup + script run + git diff). No impact on existing jobs.
- **Release process:** The generator reads `aidlc-rules/VERSION` which is updated by the release workflow. The committed plugin output will be updated in the same release PR, so the plugin version stays in lock-step. No changes to `release.yml`, `release-pr.yml`, or `tag-on-merge.yml` needed — the release PR already touches `aidlc-rules/VERSION`, which triggers the CI sync check, which forces regeneration.
- **markdownlint:** Generated plugin markdown must pass the repo's linting config. The generator must ensure emitted markdown is compliant (fenced code language specified, no bare URLs, etc.).

## Risks & Dependencies

- **`${CLAUDE_PLUGIN_ROOT}` in skill content:** We assume this variable resolves when the agent reads skill markdown and uses it in Read tool paths. If CC only expands it in hook commands and not in agent-read content, we'll need to use relative paths from the skill directory instead. Mitigation: verify during Unit 4 implementation; the fallback is straightforward.
- **Plugin install from subdirectory:** We assume `claude plugin install` can target a subdirectory of a git repo. If not, the plugin directory may need to be installable from the repo root. Mitigation: test during Unit 5; worst case, add a top-level pointer.
- **markdownlint on generated content:** The generator produces SKILL.md files with YAML frontmatter. If the repo's markdownlint config doesn't handle frontmatter well, we may need an ignore entry. Mitigation: run linter in Unit 5 validation.

## Documentation / Operational Notes

- README Claude Code section should present plugin install as the recommended path, with manual setup as a fallback
- CONTRIBUTING.md should warn that `plugins/claude-code-aidlc/` is generated — PRs editing it directly will fail CI
- No monitoring or operational concerns — this is a static content plugin with no runtime services

## Sources & References

- **Origin document:** [docs/brainstorms/2026-04-28-claude-code-aidlc-plugin-requirements.md](../brainstorms/2026-04-28-claude-code-aidlc-plugin-requirements.md)
- Related code: `aidlc-rules/aws-aidlc-rules/core-workflow.md` (lines 13-20 for path-resolution transform)
- Related code: `aidlc-rules/aws-aidlc-rule-details/common/session-continuity.md` (resume protocol for orchestrator)
- Related code: `.github/workflows/ci.yml` (add sync job)
- Plugin structure reference: `plugin-dev:plugin-structure` skill documentation
