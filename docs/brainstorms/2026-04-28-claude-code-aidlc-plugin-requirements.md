---
date: 2026-04-28
topic: claude-code-aidlc-plugin
---

# Claude Code AIDLC Plugin

## Problem Frame

The current Claude Code setup for AIDLC requires users to download a zip, extract it, copy `core-workflow.md` as `CLAUDE.md` (overwriting any existing project instructions), and copy `aws-aidlc-rule-details/` into the workspace. This is the most error-prone onboarding path of all 8 supported platforms: it overwrites user config, pollutes the workspace with methodology files, has no update path, and provides no interactive workflow guidance.

A Claude Code plugin eliminates all of these issues with a single `claude plugin install` command, versioned updates, and a purpose-built orchestrator agent that drives the three-phase workflow natively.

## Requirements

- R1. Plugin installs via `claude plugin install` from the git repo URL — no zip download, no manual file copying
- R2. An orchestrator agent (`aidlc`) drives the full three-phase workflow (Inception, Construction, Operations), detecting current phase from workspace state and loading the appropriate phase skill
- R3. Slash commands (`/aidlc`, `/aidlc:inception`, `/aidlc:construction`, `/aidlc:operations`) dispatch to the orchestrator with optional phase hints
- R4. Seven skills provide the methodology content, organized by phase and cross-cutting concern:
  - `aidlc-core-workflow` — the master workflow (adapted from core-workflow.md with plugin-native path resolution)
  - `aidlc-inception` — all inception phase rule-details bundled as references/
  - `aidlc-construction` — all construction phase rule-details bundled as references/
  - `aidlc-operations` — operations phase rule-details bundled as references/
  - `aidlc-common` — cross-cutting rules (terminology, depth-levels, question-format, error-handling, content-validation, etc.)
  - `aidlc-security-baseline` — opt-in security extension
  - `aidlc-property-testing` — opt-in property-based testing extension
- R5. Rule-details content in skills comes exclusively from `${CLAUDE_PLUGIN_ROOT}/skills/*/references/` — no workspace path resolution, no fallback to `.aidlc-rule-details/` or other workspace directories
- R6. A generator script (`scripts/build-cc-plugin.py`) produces plugin skill content from the canonical `aidlc-rules/` source files — rules are single source of truth
- R7. CI enforces sync: the `ci.yml` workflow runs the generator and fails via `git diff --exit-code` if committed plugin files don't match regenerated output
- R8. Plugin version tracks `aidlc-rules/VERSION`

## Success Criteria

- A user can install the plugin and run `/aidlc` on a project with zero prior AIDLC setup — the welcome message appears and the workflow begins
- Rule content in the plugin is byte-identical to the canonical source (after frontmatter/path transformations) — CI proves this on every PR
- Existing non-plugin AIDLC setups (CLAUDE.md-based) are unaffected — the plugin is additive, not a replacement of other delivery methods

## Scope Boundaries

- **In scope**: Plugin structure, orchestrator agent, slash commands, skills, generator script, CI sync job
- **Not in scope**: Changes to the canonical rule files themselves, other platform delivery methods, plugin marketplace publishing, MCP servers, hooks
- **Not in scope**: Modifying the AIDLC methodology — the plugin is a packaging/delivery mechanism only
- **Deliberate divergence**: The `aidlc-core-workflow` skill replaces the path-resolution section of `core-workflow.md` with plugin-native paths (`${CLAUDE_PLUGIN_ROOT}/skills/*/references/`). The generator script handles this transformation.

## Key Decisions

- **Plugin name**: `aidlc` — commands namespace as `/aidlc:*`
- **Location**: Same repo under `plugins/claude-code-aidlc/` — CI enforces lock-step with rules
- **Distribution**: `claude plugin install` from git URL only (no marketplace for now)
- **Rule loading**: Plugin-only — agent reads bundled references exclusively, no workspace fallback
- **Extensions**: Two separate opt-in skills (security-baseline, property-based-testing), following the rules' own opt-in pattern
- **Generator approach**: Committed output + CI drift check (option 1a from discussion) — plugin is browsable in repo, reviewable in PRs

## Dependencies / Assumptions

- Claude Code plugin system supports `${CLAUDE_PLUGIN_ROOT}` for portable path references in skill content
- Python 3.x available in CI for the generator script
- The canonical rule file structure (`aidlc-rules/aws-aidlc-rules/` and `aidlc-rules/aws-aidlc-rule-details/`) is stable per CONTRIBUTING.md contract

## Outstanding Questions

### Deferred to Planning

- [Affects R2][Technical] How should the orchestrator agent detect current phase — by checking for `aidlc-docs/inception/`, `aidlc-docs/construction/`, and `aidlc-state.md`? The existing `session-continuity.md` has a resume protocol that should inform this.
- [Affects R6][Technical] Exact transformation rules for the generator: which sections of core-workflow.md need path rewriting, and should the generator emit SKILL.md index content programmatically or use handwritten index templates?
- [Affects R4][Needs research] Optimal SKILL.md description text for each skill — these control when CC auto-activates skills, so wording matters for trigger quality.

## Next Steps

→ `/ce:plan` for structured implementation planning
