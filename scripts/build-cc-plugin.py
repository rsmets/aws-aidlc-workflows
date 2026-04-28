#!/usr/bin/env python3
"""Generate the Claude Code AIDLC plugin from canonical aidlc-rules/ source files.

This script is the single source of truth for the plugin's structure. It:
  1. Reads aidlc-rules/VERSION for version stamping
  2. Copies rule-detail files into skill references/ directories
  3. Transforms core-workflow.md path-resolution for plugin-native loading
  4. Emits plugin.json, orchestrator agent, slash commands, and SKILL.md files

Usage:
    python scripts/build-cc-plugin.py [--output-dir plugins/claude-code-aidlc]

The output directory is cleaned and recreated on each run to prevent orphans.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to repo root)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = REPO_ROOT / "aidlc-rules"
RULES_ENTRY = RULES_DIR / "aws-aidlc-rules" / "core-workflow.md"
RULE_DETAILS = RULES_DIR / "aws-aidlc-rule-details"
VERSION_FILE = RULES_DIR / "VERSION"

DEFAULT_OUTPUT = REPO_ROOT / "plugins" / "claude-code-aidlc"

# The exact text block in core-workflow.md that gets replaced.
# Matched by its section header — we replace from "## MANDATORY: Rule Details Loading"
# through the blank line after "All subsequent rule detail file references...".
PATH_RESOLUTION_OLD = """\
## MANDATORY: Rule Details Loading
**CRITICAL**: When performing any phase, you MUST read and use relevant content from rule detail files. Check these paths in order and use the first one that exists, regardless of which IDE or setup method was used:
- `.aidlc/aidlc-rules/aws-aidlc-rule-details/` (typical with AI-assisted setup)
- `.aidlc-rule-details/` (typical with Cursor, Cline, Claude Code, GitHub Copilot, OpenAI Codex)
- `.kiro/aws-aidlc-rule-details/` (typical with Kiro IDE and CLI)
- `.amazonq/aws-aidlc-rule-details/` (typical with Amazon Q Developer)

All subsequent rule detail file references (e.g., `common/process-overview.md`, `inception/workspace-detection.md`) are relative to whichever rule details directory was resolved above."""

PATH_RESOLUTION_NEW = """\
## MANDATORY: Rule Details Loading
**CRITICAL**: When performing any phase, you MUST read and use relevant content from rule detail files. Rule details are bundled with this plugin — read them from the plugin's own skill references directories.

The orchestrator agent routes to the correct skill for each phase:
- **Common rules**: Read from the `aidlc-common` skill's `references/` directory
- **Inception phase rules**: Read from the `aidlc-inception` skill's `references/` directory
- **Construction phase rules**: Read from the `aidlc-construction` skill's `references/` directory
- **Operations phase rules**: Read from the `aidlc-operations` skill's `references/` directory
- **Extension rules**: Read from `aidlc-security-baseline` or `aidlc-property-testing` skill `references/` directories

All subsequent rule detail file references (e.g., `common/process-overview.md`, `inception/workspace-detection.md`) are relative paths within the appropriate skill's `references/` directory."""


# ---------------------------------------------------------------------------
# Template: plugin.json
# ---------------------------------------------------------------------------
def plugin_json_content(version: str) -> str:
    return json.dumps(
        {
            "name": "aidlc",
            "version": version,
            "description": "AI-Driven Development Life Cycle — structured adaptive workflow for software development with AI coding agents",
            "repository": "https://github.com/awslabs/aidlc-workflows",
            "license": "Apache-2.0",
        },
        indent=2,
    ) + "\n"


# ---------------------------------------------------------------------------
# Template: orchestrator agent
# ---------------------------------------------------------------------------
ORCHESTRATOR_AGENT = """\
---
description: >-
  AI-DLC orchestrator — drives the three-phase adaptive software development
  workflow (Inception, Construction, Operations). Use when starting a new
  development task with AIDLC, resuming an in-progress AIDLC workflow, or
  when the user asks to plan, design, build, or implement software using the
  AI-Driven Development Life Cycle methodology.
---

# AIDLC Orchestrator Agent

You are the AI-DLC (AI-Driven Development Life Cycle) orchestrator. Your job is
to guide the user through a structured, adaptive software development workflow
organized into three phases: **Inception**, **Construction**, and **Operations**.

## Phase Detection and Session Resumption

Before starting any workflow, check the workspace for existing AIDLC state:

1. **Check for `aidlc-docs/aidlc-state.md`** — if it exists, read it to
   determine the current phase, stage, and last completed step. Present the
   session continuity prompt from the `aidlc-common` skill's
   `references/common/session-continuity.md`.

2. **Check for `aidlc-docs/` subdirectories** — if `aidlc-state.md` is missing
   but `aidlc-docs/inception/` or `aidlc-docs/construction/` exist, infer the
   phase from directory presence.

3. **No existing state** — this is a new workflow. Proceed with initialization.

## New Workflow Initialization

When starting a new AIDLC workflow:

1. **Load the core workflow** — Read the `aidlc-core-workflow` skill to
   understand the full adaptive workflow structure and mandatory rules.

2. **Load common rules** — Read these files from the `aidlc-common` skill's
   `references/` directory:
   - `common/process-overview.md` — workflow overview
   - `common/session-continuity.md` — session resumption guidance
   - `common/content-validation.md` — content validation requirements
   - `common/question-format-guide.md` — question formatting rules

3. **Display the welcome message** — Read `common/welcome-message.md` from the
   `aidlc-common` skill's `references/` directory and display it to the user.
   This should only be done ONCE at the start of a new workflow.

4. **Scan extensions** — Read the opt-in files from the extension skills:
   - `aidlc-security-baseline` skill for security extension opt-in
   - `aidlc-property-testing` skill for property-based testing opt-in

   Load ONLY the opt-in prompts at this stage. Full extension rules are loaded
   on-demand when the user opts in during Requirements Analysis.

5. **Begin Inception Phase** — Start with Workspace Detection as defined in the
   core workflow.

## Phase Routing

When executing a specific phase, load the corresponding skill and read its
rule-detail files from `references/`:

- **Inception Phase**: Load the `aidlc-inception` skill. Read rule files from
  its `references/inception/` directory as needed (e.g.,
  `references/inception/workspace-detection.md`,
  `references/inception/requirements-analysis.md`).

- **Construction Phase**: Load the `aidlc-construction` skill. Read rule files
  from its `references/construction/` directory as needed (e.g.,
  `references/construction/functional-design.md`,
  `references/construction/code-generation.md`).

- **Operations Phase**: Load the `aidlc-operations` skill. Read rule files from
  its `references/operations/` directory as needed.

## Extension Handling

During Requirements Analysis, present the opt-in prompts from extension skills.
When the user opts in:

- **Security Baseline**: Read the full rules from the `aidlc-security-baseline`
  skill's `references/extensions/security/baseline/security-baseline.md`.

- **Property-Based Testing**: Read the full rules from the
  `aidlc-property-testing` skill's
  `references/extensions/testing/property-based/property-based-testing.md`.

Track extension enablement in `aidlc-docs/aidlc-state.md` under
`## Extension Configuration`.

## Cross-Cutting Rules

Throughout the workflow, reference common rules from the `aidlc-common` skill:

- `references/common/terminology.md` — for consistent terminology
- `references/common/depth-levels.md` — for adaptive detail levels
- `references/common/error-handling.md` — for error recovery procedures
- `references/common/overconfidence-prevention.md` — for confidence calibration
- `references/common/ascii-diagram-standards.md` — for diagram formatting
- `references/common/workflow-changes.md` — for workflow modification handling

## Phase Boundaries

At each phase boundary:

1. Present the completion message as defined in the phase's rule files
2. Wait for explicit user approval before proceeding
3. Log the transition in `aidlc-docs/audit.md`
4. Update `aidlc-docs/aidlc-state.md` with the new phase/stage

## Key Principles

- **Follow the core workflow exactly** — the adaptive workflow rules in
  `core-workflow.md` define which stages execute and when
- **Progressive loading** — only read rule-detail files when the stage requires
  them, not all at once
- **User control** — always wait for explicit approval at stage boundaries
- **Audit trail** — log every user input and AI response in `audit.md`
"""


# ---------------------------------------------------------------------------
# Template: slash commands
# ---------------------------------------------------------------------------
COMMAND_AIDLC = """\
---
name: aidlc
description: Start or resume an AI-DLC adaptive software development workflow
---

Start or resume the AI-DLC (AI-Driven Development Life Cycle) workflow.

If the user provided a description of their task, pass it to the AIDLC
orchestrator agent as the initial request. If no description was provided,
the orchestrator will detect the workspace state and either resume an
existing workflow or start a new one with a welcome message.

The orchestrator handles all phase detection, skill loading, and workflow
progression automatically.
"""

COMMAND_INCEPTION = """\
---
name: aidlc-inception
description: Start or resume the AIDLC Inception phase (planning and architecture)
---

Start or resume the **Inception Phase** of the AI-DLC workflow.

Direct the AIDLC orchestrator agent to focus on the Inception phase, which
covers:
- Workspace Detection
- Reverse Engineering (brownfield only)
- Requirements Analysis
- User Stories (conditional)
- Workflow Planning
- Application Design (conditional)
- Units Generation (conditional)

If an existing AIDLC workflow is in progress, resume from the current
Inception stage. If no workflow exists, initialize one and begin Inception.
"""

COMMAND_CONSTRUCTION = """\
---
name: aidlc-construction
description: Start or resume the AIDLC Construction phase (design, implementation, and test)
---

Start or resume the **Construction Phase** of the AI-DLC workflow.

Direct the AIDLC orchestrator agent to focus on the Construction phase, which
covers the per-unit loop:
- Functional Design (conditional, per-unit)
- NFR Requirements (conditional, per-unit)
- NFR Design (conditional, per-unit)
- Infrastructure Design (conditional, per-unit)
- Code Generation (always, per-unit)
- Build and Test (always, after all units)

If an existing AIDLC workflow is in progress, resume from the current
Construction stage. If Inception has not been completed, warn the user.
"""

COMMAND_OPERATIONS = """\
---
name: aidlc-operations
description: Start or resume the AIDLC Operations phase (deployment and monitoring)
---

Start or resume the **Operations Phase** of the AI-DLC workflow.

Direct the AIDLC orchestrator agent to focus on the Operations phase.

Note: The Operations phase is currently a placeholder for future expansion.
It will eventually include deployment planning, monitoring setup, incident
response, and maintenance workflows.
"""


# ---------------------------------------------------------------------------
# Template: SKILL.md files
# ---------------------------------------------------------------------------
def skill_core_workflow(version: str) -> str:
    return f"""\
---
name: AIDLC Core Workflow
description: >-
  The master AI-DLC adaptive workflow — load when initializing or resuming an
  AIDLC software development workflow. Defines the three-phase lifecycle
  (Inception, Construction, Operations), stage sequencing, mandatory rules,
  and the adaptive execution model.
version: {version}
---

# AIDLC Core Workflow

This skill contains the master workflow definition for AI-DLC (AI-Driven
Development Life Cycle). It defines:

- The three-phase lifecycle and stage sequencing
- Mandatory rules (rule-details loading, extensions, content validation, etc.)
- Adaptive execution model (which stages run and when)
- Directory structure for generated artifacts
- Audit trail and progress tracking requirements

## Usage

Read the full workflow from `references/core-workflow.md`. This is the
authoritative definition of the AIDLC process and should be loaded at the
start of any new or resumed workflow.

Rule-detail files referenced by the workflow are available in the phase-specific
skills (`aidlc-inception`, `aidlc-construction`, `aidlc-operations`) and the
cross-cutting `aidlc-common` skill.
"""


def skill_inception(version: str) -> str:
    return f"""\
---
name: AIDLC Inception Phase
description: >-
  Inception phase rules for AIDLC — planning, requirements, and architecture.
  Load when executing workspace detection, reverse engineering, requirements
  analysis, user stories, workflow planning, application design, or units
  generation stages.
version: {version}
---

# AIDLC Inception Phase

This skill contains the detailed rule files for the AIDLC Inception phase.
The Inception phase determines **WHAT** to build and **WHY**.

## Stages

| Stage                  | Condition              | Rule File                                         |
| ---------------------- | ---------------------- | ------------------------------------------------- |
| Workspace Detection    | ALWAYS                 | `references/inception/workspace-detection.md`     |
| Reverse Engineering    | Brownfield only        | `references/inception/reverse-engineering.md`      |
| Requirements Analysis  | ALWAYS (adaptive)      | `references/inception/requirements-analysis.md`    |
| User Stories           | CONDITIONAL            | `references/inception/user-stories.md`             |
| Workflow Planning      | ALWAYS                 | `references/inception/workflow-planning.md`        |
| Application Design     | CONDITIONAL            | `references/inception/application-design.md`       |
| Units Generation       | CONDITIONAL            | `references/inception/units-generation.md`         |

## Usage

Read the rule file for the current stage from `references/inception/`. Each
file contains the detailed steps, artifacts, and completion criteria for that
stage. Load only the file needed for the current stage — do not load all files
at once.
"""


def skill_construction(version: str) -> str:
    return f"""\
---
name: AIDLC Construction Phase
description: >-
  Construction phase rules for AIDLC — detailed design, implementation, and
  testing. Load when executing functional design, NFR requirements, NFR design,
  infrastructure design, code generation, or build and test stages.
version: {version}
---

# AIDLC Construction Phase

This skill contains the detailed rule files for the AIDLC Construction phase.
The Construction phase determines **HOW** to build it.

## Stages

| Stage                  | Condition              | Rule File                                           |
| ---------------------- | ---------------------- | --------------------------------------------------- |
| Functional Design      | CONDITIONAL (per-unit) | `references/construction/functional-design.md`      |
| NFR Requirements       | CONDITIONAL (per-unit) | `references/construction/nfr-requirements.md`       |
| NFR Design             | CONDITIONAL (per-unit) | `references/construction/nfr-design.md`             |
| Infrastructure Design  | CONDITIONAL (per-unit) | `references/construction/infrastructure-design.md`  |
| Code Generation        | ALWAYS (per-unit)      | `references/construction/code-generation.md`        |
| Build and Test         | ALWAYS                 | `references/construction/build-and-test.md`         |

## Usage

Read the rule file for the current stage from `references/construction/`. Each
unit of work goes through the applicable stages in sequence before moving to the
next unit. Load only the file needed for the current stage.
"""


def skill_operations(version: str) -> str:
    return f"""\
---
name: AIDLC Operations Phase
description: >-
  Operations phase rules for AIDLC — deployment, monitoring, and maintenance.
  Load when executing operations-related stages. Currently a placeholder for
  future expansion.
version: {version}
---

# AIDLC Operations Phase

This skill contains the rule files for the AIDLC Operations phase.

The Operations phase is currently a **placeholder** for future expansion and
will eventually include:

- Deployment planning and execution
- Monitoring and observability setup
- Incident response procedures
- Maintenance and support workflows
- Production readiness checklists

## Usage

Read `references/operations/operations.md` for the current operations
stage definition.
"""


def skill_common(version: str) -> str:
    return f"""\
---
name: AIDLC Common Rules
description: >-
  Cross-cutting AIDLC rules — terminology, depth levels, question formatting,
  error handling, content validation, session continuity, welcome message, and
  other shared guidance. Loaded as supporting context by other AIDLC skills.
version: {version}
---

# AIDLC Common Rules

This skill contains cross-cutting rules that apply across all AIDLC phases.
These files are referenced throughout the workflow and should be loaded when
the corresponding guidance is needed.

## Reference Files

| File                                              | Purpose                          |
| ------------------------------------------------- | -------------------------------- |
| `references/common/process-overview.md`           | Workflow overview and diagram    |
| `references/common/session-continuity.md`         | Session resumption protocol      |
| `references/common/content-validation.md`         | Content validation requirements  |
| `references/common/question-format-guide.md`      | Question formatting rules        |
| `references/common/welcome-message.md`            | User-facing welcome message      |
| `references/common/terminology.md`                | Glossary and naming conventions  |
| `references/common/depth-levels.md`               | Adaptive detail level guidance   |
| `references/common/error-handling.md`             | Error recovery procedures        |
| `references/common/overconfidence-prevention.md`  | Confidence calibration rules     |
| `references/common/ascii-diagram-standards.md`    | ASCII diagram formatting         |
| `references/common/workflow-changes.md`           | Workflow modification handling   |

## Usage

Read individual files from `references/common/` as needed. The core workflow
specifies which common files to load at workflow start and which to reference
during specific stages.
"""


def skill_security_baseline(version: str) -> str:
    return f"""\
---
name: AIDLC Security Baseline Extension
description: >-
  Optional security extension for AIDLC — enforces security baseline rules as
  blocking constraints. Load when the user opts in to security enforcement
  during AIDLC Requirements Analysis.
version: {version}
---

# AIDLC Security Baseline Extension

This is an **opt-in** extension that enforces security baseline rules as
blocking constraints throughout the AIDLC workflow.

## Opt-In Prompt

The following question is presented during Requirements Analysis:

> **Question: Security Extensions**
>
> Should security extension rules be enforced for this project?
>
> A) Yes — enforce all SECURITY rules as blocking constraints
> (recommended for production-grade applications)
>
> B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and
> experimental projects)
>
> X) Other (please describe after \\[Answer\\]: tag below)

## Usage

- Present the opt-in prompt during Requirements Analysis
- If the user opts **in**, read the full rules from
  `references/extensions/security/baseline/security-baseline.md`
- If the user opts **out**, do not load the full rules file
- Track the enablement decision in `aidlc-docs/aidlc-state.md` under
  `## Extension Configuration`
- When enabled, extension rules are **hard constraints** — non-compliance is a
  blocking finding
"""


def skill_property_testing(version: str) -> str:
    return f"""\
---
name: AIDLC Property-Based Testing Extension
description: >-
  Optional property-based testing extension for AIDLC — enforces PBT rules for
  pure functions, serialization, and stateful components. Load when the user
  opts in to property-based testing during AIDLC Requirements Analysis.
version: {version}
---

# AIDLC Property-Based Testing Extension

This is an **opt-in** extension that enforces property-based testing rules
throughout the AIDLC workflow.

## Opt-In Prompt

The following question is presented during Requirements Analysis:

> **Question: Property-Based Testing Extension**
>
> Should property-based testing (PBT) rules be enforced for this project?
>
> A) Yes — enforce all PBT rules as blocking constraints (recommended for
> projects with business logic, data transformations, serialization, or
> stateful components)
>
> B) Partial — enforce PBT rules only for pure functions and serialization
> round-trips (suitable for projects with limited algorithmic complexity)
>
> C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only
> projects, or thin integration layers with no significant business logic)
>
> X) Other (please describe after \\[Answer\\]: tag below)

## Usage

- Present the opt-in prompt during Requirements Analysis
- If the user opts **in** (A or B), read the full rules from
  `references/extensions/testing/property-based/property-based-testing.md`
- If the user opts **out** (C), do not load the full rules file
- Track the enablement decision and level in `aidlc-docs/aidlc-state.md` under
  `## Extension Configuration`
- When enabled, extension rules are **hard constraints** — non-compliance is a
  blocking finding
"""


# ---------------------------------------------------------------------------
# Mapping: which source directories go into which skill's references/
# ---------------------------------------------------------------------------
SKILL_COPY_MAP = {
    "aidlc-common": ["common"],
    "aidlc-inception": ["inception"],
    "aidlc-construction": ["construction"],
    "aidlc-operations": ["operations"],
    "aidlc-security-baseline": ["extensions/security"],
    "aidlc-property-testing": ["extensions/testing"],
}


# ---------------------------------------------------------------------------
# Generator logic
# ---------------------------------------------------------------------------
def transform_core_workflow(source_text: str) -> str:
    """Replace the workspace path-resolution block with plugin-native loading."""
    if PATH_RESOLUTION_OLD not in source_text:
        print(
            "ERROR: Could not find the path-resolution block in core-workflow.md.\n"
            "The canonical file may have changed — update PATH_RESOLUTION_OLD in "
            "this script.",
            file=sys.stderr,
        )
        sys.exit(1)
    return source_text.replace(PATH_RESOLUTION_OLD, PATH_RESOLUTION_NEW, 1)


def copy_references(skill_name: str, src_subdirs: list[str], output_dir: Path) -> None:
    """Copy rule-detail files into a skill's references/ directory."""
    refs_dir = output_dir / "skills" / skill_name / "references"
    for subdir in src_subdirs:
        src = RULE_DETAILS / subdir
        if not src.exists():
            print(f"WARNING: Source directory {src} does not exist, skipping", file=sys.stderr)
            continue
        dst = refs_dir / subdir
        shutil.copytree(src, dst, dirs_exist_ok=True)


def build_plugin(output_dir: Path) -> None:
    """Generate the complete plugin directory."""
    # Validate source exists
    if not RULES_DIR.exists():
        print(f"ERROR: {RULES_DIR} not found. Run from the repository root.", file=sys.stderr)
        sys.exit(1)

    # Read version
    version = VERSION_FILE.read_text().strip()

    # Clean and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # -- plugin.json --
    manifest_dir = output_dir / ".claude-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(plugin_json_content(version))

    # -- orchestrator agent --
    agents_dir = output_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "aidlc-orchestrator.md").write_text(ORCHESTRATOR_AGENT)

    # -- slash commands --
    commands_dir = output_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "aidlc.md").write_text(COMMAND_AIDLC)
    (commands_dir / "aidlc-inception.md").write_text(COMMAND_INCEPTION)
    (commands_dir / "aidlc-construction.md").write_text(COMMAND_CONSTRUCTION)
    (commands_dir / "aidlc-operations.md").write_text(COMMAND_OPERATIONS)

    # -- skills: SKILL.md files --
    skill_templates = {
        "aidlc-core-workflow": skill_core_workflow(version),
        "aidlc-inception": skill_inception(version),
        "aidlc-construction": skill_construction(version),
        "aidlc-operations": skill_operations(version),
        "aidlc-common": skill_common(version),
        "aidlc-security-baseline": skill_security_baseline(version),
        "aidlc-property-testing": skill_property_testing(version),
    }
    for skill_name, content in skill_templates.items():
        skill_dir = output_dir / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(content)

    # -- skills: copy references --
    for skill_name, src_subdirs in SKILL_COPY_MAP.items():
        copy_references(skill_name, src_subdirs, output_dir)

    # -- core-workflow: transform and copy --
    core_src = RULES_ENTRY.read_text()
    core_transformed = transform_core_workflow(core_src)
    core_dest = output_dir / "skills" / "aidlc-core-workflow" / "references"
    core_dest.mkdir(parents=True, exist_ok=True)
    (core_dest / "core-workflow.md").write_text(core_transformed)

    # -- markdownlint config: merge aidlc-rules/ overrides with plugin-specific needs --
    lint_config_src = RULES_DIR / ".markdownlint-cli2.yaml"
    if lint_config_src.exists():
        # Copy the aidlc-rules config (disables rules the source files violate),
        # then layer on plugin-specific settings
        config_text = lint_config_src.read_text()
        # Add frontmatter support so YAML frontmatter in SKILL.md / commands
        # is not treated as content, and enable front_matter_title to suppress
        # MD041 for files with frontmatter.
        plugin_additions = (
            "\n"
            "  # --- Plugin-specific overrides ---\n"
            "  MD041: false  # first-line-heading — plugin files use YAML frontmatter\n"
        )
        # Insert before the last line if possible, or just append
        config_text = config_text.rstrip() + "\n" + plugin_additions
        (output_dir / ".markdownlint-cli2.yaml").write_text(config_text)

    print(f"Plugin generated at {output_dir} (version {version})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the Claude Code AIDLC plugin from canonical rules"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()
    build_plugin(args.output_dir)


if __name__ == "__main__":
    main()
