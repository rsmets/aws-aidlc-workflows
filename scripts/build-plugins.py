#!/usr/bin/env python3
"""Generate AIDLC plugins for supported AI coding agents from the canonical
aidlc-rules/ source files.

This script is the single source of truth for all generated plugin packages.
By default it builds every supported target:
  - Claude Code plugin (plugins/claude-code-aidlc/)
  - Cursor rules bundle  (plugins/cursor-aidlc/)

For each target it:
  1. Reads aidlc-rules/VERSION for version stamping
  2. Copies or adapts rule-detail files into the target-specific layout
  3. Transforms core-workflow.md path-resolution for plugin-native loading
  4. Emits target-specific metadata (plugin.json, .mdc frontmatter, etc.)

Usage:
    python scripts/build-plugins.py               # build all targets
    python scripts/build-plugins.py --target cc   # build only Claude Code
    python scripts/build-plugins.py --target cursor   # build only Cursor

The output directories are cleaned and recreated on each run to prevent orphans.
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

CC_DEFAULT_OUTPUT = REPO_ROOT / "plugins" / "claude-code-aidlc"
CURSOR_DEFAULT_OUTPUT = REPO_ROOT / "plugins" / "cursor-aidlc"

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
# Template: plugin README
# ---------------------------------------------------------------------------
def plugin_readme(version: str) -> str:
    return f"""\
# AI-DLC Claude Code Plugin

AI-Driven Development Life Cycle (AI-DLC) packaged as a Claude Code plugin.
Provides an adaptive three-phase software development workflow (Inception,
Construction, Operations) driven by an orchestrator agent, phase-specific slash
commands, and progressive-disclosure skills.

**Version**: {version}
**Source of truth**: `aidlc-rules/` in this repository
**Generator**: `scripts/build-cc-plugin.py`

> This directory is **generated**. Do not edit files here directly — edit the
> canonical sources in `aidlc-rules/` and run the generator. CI enforces sync.

## What You Get

| Component                    | Purpose                                                      |
| ---------------------------- | ------------------------------------------------------------ |
| `/aidlc`                     | Start or resume an AI-DLC workflow                           |
| `/aidlc:inception`           | Start or resume the Inception phase                          |
| `/aidlc:construction`        | Start or resume the Construction phase                       |
| `/aidlc:operations`          | Start or resume the Operations phase (placeholder)           |
| `aidlc-orchestrator` agent   | Drives the three-phase workflow, detects phase from state    |
| `aidlc-core-workflow` skill  | Master workflow definition                                   |
| `aidlc-inception` skill      | Inception phase rules (workspace detection, requirements, …) |
| `aidlc-construction` skill   | Construction phase rules (design, NFR, code generation, …)   |
| `aidlc-operations` skill     | Operations phase rules (placeholder)                         |
| `aidlc-common` skill         | Cross-cutting rules (terminology, depth, error handling, …)  |
| `aidlc-security-baseline`    | Opt-in security extension                                    |
| `aidlc-property-testing`     | Opt-in property-based testing extension                      |

## Installing

### For Development (Local Path)

Use `--plugin-dir` to load the plugin from a local path for a single session.
This is the fastest way to iterate on plugin changes without publishing.

```bash
# From a clone of this repo, at the repo root:
claude --plugin-dir ./plugins/claude-code-aidlc
```

The flag is repeatable for loading multiple plugins side-by-side:

```bash
claude --plugin-dir ./plugins/claude-code-aidlc --plugin-dir ../other-plugin
```

Inside the session, use `/reload-plugins` to pick up changes without
restarting Claude Code.

### For Persistent Local Install (Development)

Add this repo as a local marketplace, then install the plugin from it:

```bash
# Register the repo as a marketplace (persists across sessions)
claude plugin marketplace add /absolute/path/to/aws-aidlc-workflows

# Install the aidlc plugin
claude plugin install aidlc
```

Scope the install with `--scope user|project|local` if needed (defaults to
`user`).

### For End Users (Git Install)

Once published, users install directly from the repository:

```bash
claude plugin marketplace add https://github.com/awslabs/aidlc-workflows
claude plugin install aidlc
```

## Using the Plugin

After installation, start or resume a workflow:

```text
/aidlc
```

With no argument, the orchestrator detects existing AIDLC state in the
workspace (via `aidlc-docs/aidlc-state.md`) and either resumes or shows the
welcome message. You can also provide an initial request:

```text
/aidlc build a REST API for order management
```

Target a specific phase:

```text
/aidlc:inception
/aidlc:construction
/aidlc:operations
```

## How It Works

1. The orchestrator agent detects current phase from workspace state
2. It loads the appropriate phase skill (`aidlc-inception`,
   `aidlc-construction`, or `aidlc-operations`) on demand
3. Each skill's `references/` directory contains the rule-detail files —
   loaded lazily as the workflow progresses
4. The `aidlc-common` skill provides cross-cutting rules (terminology,
   question formatting, error handling) referenced throughout
5. Extension skills (`aidlc-security-baseline`, `aidlc-property-testing`) are
   loaded only when the user opts in during Requirements Analysis

All rule content is bundled with the plugin — no workspace file copies
required.

## Contributing

Do not edit files in this directory directly. Edit the canonical source in
`aidlc-rules/` at the repository root, then regenerate:

```bash
python scripts/build-cc-plugin.py
```

CI (`plugin-sync` job) runs the generator on every PR and fails if the
committed output drifts from the source.

## Structure

```text
plugins/claude-code-aidlc/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (name, version, metadata)
├── agents/
│   └── aidlc-orchestrator.md    # Orchestrator agent definition
├── commands/
│   ├── aidlc.md                 # /aidlc entry command
│   ├── aidlc-inception.md       # /aidlc:inception
│   ├── aidlc-construction.md    # /aidlc:construction
│   └── aidlc-operations.md      # /aidlc:operations
└── skills/
    ├── aidlc-core-workflow/
    ├── aidlc-inception/
    ├── aidlc-construction/
    ├── aidlc-operations/
    ├── aidlc-common/
    ├── aidlc-security-baseline/
    └── aidlc-property-testing/
```

Each skill contains a `SKILL.md` and a `references/` subdirectory with the
bundled rule-detail files.

## License

Apache-2.0 — see [LICENSE](../../LICENSE).
"""


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


def write_plugin_markdownlint_config(output_dir: Path) -> None:
    """Copy aidlc-rules/ markdownlint overrides into the plugin directory and
    layer on plugin-specific settings so generated markdown passes lint."""
    lint_config_src = RULES_DIR / ".markdownlint-cli2.yaml"
    if not lint_config_src.exists():
        return
    config_text = lint_config_src.read_text()
    plugin_additions = (
        "\n"
        "  # --- Plugin-specific overrides ---\n"
        "  MD041: false  # first-line-heading — plugin files use YAML frontmatter\n"
    )
    config_text = config_text.rstrip() + "\n" + plugin_additions
    (output_dir / ".markdownlint-cli2.yaml").write_text(config_text)


def clean_output(output_dir: Path) -> None:
    """Clean and recreate the output directory so deleted source files don't leave orphans."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)


def read_version() -> str:
    """Read version string from aidlc-rules/VERSION."""
    if not RULES_DIR.exists():
        print(f"ERROR: {RULES_DIR} not found. Run from the repository root.", file=sys.stderr)
        sys.exit(1)
    return VERSION_FILE.read_text().strip()


def build_cc_plugin(output_dir: Path) -> None:
    """Generate the Claude Code plugin directory."""
    version = read_version()
    clean_output(output_dir)

    # -- plugin.json --
    manifest_dir = output_dir / ".claude-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(plugin_json_content(version))

    # -- README.md (plugin directory) --
    (output_dir / "README.md").write_text(plugin_readme(version))

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

    write_plugin_markdownlint_config(output_dir)

    print(f"Claude Code plugin generated at {output_dir} (version {version})")


# ---------------------------------------------------------------------------
# Cursor plugin generation
# ---------------------------------------------------------------------------
# Cursor .mdc path-resolution transform: the plugin ships as a .cursor/rules/
# bundle, so rule-details live alongside the core workflow rather than in
# separate skill directories. References resolve inside the imported rule tree.
CURSOR_PATH_RESOLUTION_NEW = """\
## MANDATORY: Rule Details Loading
**CRITICAL**: When performing any phase, you MUST read and use relevant content from rule detail files. Rule details are bundled with this Cursor rule set — read them from the sibling rule files in this directory tree.

Rule-detail files are organized in sibling directories:
- `common/*.mdc` — cross-cutting rules
- `inception/*.mdc` — Inception phase rules
- `construction/*.mdc` — Construction phase rules
- `operations/*.mdc` — Operations phase rules
- `extensions/security/baseline/*.mdc` — security extension
- `extensions/testing/property-based/*.mdc` — property-based testing extension

All subsequent rule detail file references (e.g., `common/process-overview.md`, `inception/workspace-detection.md`) refer to `.mdc` files with the same relative path in this rule tree (e.g., `common/process-overview.mdc`, `inception/workspace-detection.mdc`)."""


def cursor_orchestrator_rule_content() -> str:
    """The master orchestrator rule — alwaysApply so Cursor loads it on every
    interaction and can route to the phase rules via @references."""
    return """\
---
description: "AI-DLC (AI-Driven Development Life Cycle) adaptive software development workflow orchestrator. Governs the three-phase lifecycle (Inception, Construction, Operations) and routes to phase-specific rules."
alwaysApply: true
---

# AI-DLC Orchestrator (Cursor Rule)

This rule activates the AI-DLC (AI-Driven Development Life Cycle) adaptive
workflow. When the user asks to plan, design, build, or implement software,
follow the three-phase lifecycle defined in the core workflow.

## Workflow Entry Points

1. **New workflow** — no `aidlc-docs/` in the workspace: display the welcome
   message from `common/welcome-message.mdc` and begin the Inception phase.
2. **Resume workflow** — `aidlc-docs/aidlc-state.md` exists: follow the session
   continuity protocol in `common/session-continuity.mdc`.

## Core Workflow

The authoritative workflow definition is in `core-workflow.mdc` (sibling rule
in this directory). Load it to understand stage sequencing, mandatory rules,
and the adaptive execution model.

## Phase Rule Files

Load the rule for the current stage on demand (do not load all at once):

- **Inception phase** — rules in `inception/` (workspace-detection.mdc,
  reverse-engineering.mdc, requirements-analysis.mdc, user-stories.mdc,
  workflow-planning.mdc, application-design.mdc, units-generation.mdc)
- **Construction phase** — rules in `construction/` (functional-design.mdc,
  nfr-requirements.mdc, nfr-design.mdc, infrastructure-design.mdc,
  code-generation.mdc, build-and-test.mdc)
- **Operations phase** — rules in `operations/` (operations.mdc — placeholder)

## Cross-Cutting Rules

Reference as needed during any phase:

- `common/terminology.mdc` — glossary
- `common/depth-levels.mdc` — adaptive detail guidance
- `common/question-format-guide.mdc` — question formatting
- `common/content-validation.mdc` — content validation
- `common/error-handling.mdc` — error recovery
- `common/overconfidence-prevention.mdc` — confidence calibration
- `common/ascii-diagram-standards.mdc` — diagram formatting
- `common/workflow-changes.mdc` — workflow modification handling
- `common/process-overview.mdc` — high-level workflow diagram

## Extensions (Opt-In)

During Requirements Analysis, present the opt-in prompts from:

- `extensions/security/baseline/security-baseline.opt-in.mdc`
- `extensions/testing/property-based/property-based-testing.opt-in.mdc`

Load the full extension rules only when the user opts in:

- `extensions/security/baseline/security-baseline.mdc`
- `extensions/testing/property-based/property-based-testing.mdc`

## Key Principles

- **Follow the core workflow exactly** — see `core-workflow.mdc`
- **Progressive loading** — load only the rule for the current stage
- **User control** — wait for explicit approval at stage boundaries
- **Audit trail** — log user inputs and AI responses in `aidlc-docs/audit.md`
"""


# Short descriptions for Agent-Requested rules (Cursor uses these to decide
# when to auto-attach the rule based on the user's request).
CURSOR_RULE_DESCRIPTIONS = {
    # common/
    "common/process-overview.md": "AI-DLC workflow overview with three-phase lifecycle diagram",
    "common/session-continuity.md": "AI-DLC session resumption protocol for returning users",
    "common/content-validation.md": "AI-DLC content validation rules for generated files",
    "common/question-format-guide.md": "AI-DLC question formatting rules with multiple-choice structure",
    "common/welcome-message.md": "AI-DLC user-facing welcome message shown at workflow start",
    "common/terminology.md": "AI-DLC terminology glossary — phase vs stage definitions",
    "common/depth-levels.md": "AI-DLC adaptive depth guidance for artifact detail levels",
    "common/error-handling.md": "AI-DLC error handling and recovery procedures",
    "common/overconfidence-prevention.md": "AI-DLC confidence calibration rules",
    "common/ascii-diagram-standards.md": "AI-DLC ASCII diagram formatting standards",
    "common/workflow-changes.md": "AI-DLC workflow modification handling protocol",
    # inception/
    "inception/workspace-detection.md": "AI-DLC workspace detection stage — greenfield vs brownfield, resume vs new",
    "inception/reverse-engineering.md": "AI-DLC reverse engineering stage for brownfield projects",
    "inception/requirements-analysis.md": "AI-DLC requirements analysis stage with adaptive depth",
    "inception/user-stories.md": "AI-DLC user stories and personas generation stage",
    "inception/workflow-planning.md": "AI-DLC workflow planning stage — phase selection and sequencing",
    "inception/application-design.md": "AI-DLC application design stage — component and service identification",
    "inception/units-generation.md": "AI-DLC units generation stage — decomposition into units of work",
    # construction/
    "construction/functional-design.md": "AI-DLC functional design stage per unit",
    "construction/nfr-requirements.md": "AI-DLC NFR requirements stage per unit — tech stack selection",
    "construction/nfr-design.md": "AI-DLC NFR design stage per unit — non-functional patterns",
    "construction/infrastructure-design.md": "AI-DLC infrastructure design stage per unit",
    "construction/code-generation.md": "AI-DLC code generation stage per unit with planning and execution",
    "construction/build-and-test.md": "AI-DLC build and test stage after all units complete",
    # operations/
    "operations/operations.md": "AI-DLC operations phase — placeholder for deployment and monitoring",
    # extensions/
    "extensions/security/baseline/security-baseline.md": "AI-DLC security baseline extension — blocking security constraints",
    "extensions/security/baseline/security-baseline.opt-in.md": "AI-DLC security extension opt-in prompt",
    "extensions/testing/property-based/property-based-testing.md": "AI-DLC property-based testing extension rules",
    "extensions/testing/property-based/property-based-testing.opt-in.md": "AI-DLC property-based testing opt-in prompt",
}


def convert_to_mdc(source_path: Path, rel_path: str) -> str:
    """Wrap a source rule file in Cursor `.mdc` frontmatter.

    Agent Requested rules (description set, globs empty, alwaysApply false) —
    Cursor's AI decides when to load them based on the description.
    """
    body = source_path.read_text()
    description = CURSOR_RULE_DESCRIPTIONS.get(
        rel_path, f"AI-DLC rule: {rel_path}"
    )
    # Escape double quotes in description for YAML safety
    description = description.replace('"', '\\"')
    frontmatter = (
        "---\n"
        f'description: "{description}"\n'
        "alwaysApply: false\n"
        "---\n\n"
    )
    return frontmatter + body


def cursor_plugin_readme(version: str) -> str:
    return f"""\
# AI-DLC Cursor Rules

AI-Driven Development Life Cycle (AI-DLC) packaged as a Cursor rule set.
Provides the same adaptive three-phase workflow (Inception, Construction,
Operations) as the Claude Code plugin, distributed via Cursor's native rule
system.

**Version**: {version}
**Source of truth**: `aidlc-rules/` in this repository
**Generator**: `scripts/build-plugins.py`

> This directory is **generated**. Do not edit files here directly — edit the
> canonical sources in `aidlc-rules/` and run the generator. CI enforces sync.

## Installing

### Option 1: Copy Rules into Your Project (Recommended)

Copy the generated `.mdc` files directly into your project's `.cursor/rules/`
directory:

```bash
# From a clone of this repo, at the repo root:
mkdir -p /path/to/your/project/.cursor/rules
cp -R plugins/cursor-aidlc/rules/* /path/to/your/project/.cursor/rules/
```

Open the project in Cursor — it picks up the `.mdc` rules automatically.
The `aidlc-orchestrator.mdc` rule is set to `alwaysApply: true`, so it
loads on every interaction.

### Option 2: Remote Rules via GitHub

Cursor can import `.mdc` files from a GitHub repository:

1. Open **Cursor Settings → Rules, Commands**
2. Under **Project Rules**, click **+ Add Rule → Remote Rule (GitHub)**
3. Paste: `https://github.com/awslabs/aidlc-workflows`

Cursor scans the whole repo for `.mdc` files and preserves their relative
paths. Because this is a monorepo (not a Cursor-only repo), the imported
rules will be deeply nested under
`.cursor/rules/imported/aidlc-workflows/plugins/cursor-aidlc/rules/…`.
This works but is less clean than Option 1.

## Using the Rules

Once installed, the `aidlc/aidlc-orchestrator.mdc` rule is set to
`alwaysApply: true`, so Cursor loads it on every interaction. To start a
workflow, just describe the work:

> "Help me build a REST API for order management using AI-DLC"

The orchestrator rule routes to the appropriate phase rules on demand via
Cursor's Agent Requested mechanism. Each phase rule has a description that
tells Cursor when to auto-attach it.

## How It Works

Cursor has three rule types, inferred from frontmatter:

| Type | Frontmatter | Usage in this bundle |
|------|-------------|----------------------|
| Always | `alwaysApply: true` | Only the orchestrator rule |
| Agent Requested | `description` set | All phase and common rules |
| Manual | All fields empty | Not used |

This keeps Cursor's context window efficient — only the orchestrator is
always loaded, and phase-specific rules are pulled in only when relevant.

## Structure

```text
plugins/cursor-aidlc/
└── rules/
    ├── aidlc-orchestrator.mdc    # alwaysApply: true
    ├── core-workflow.mdc          # Adapted master workflow
    ├── common/                    # Cross-cutting rules
    ├── inception/                 # Inception phase rules
    ├── construction/              # Construction phase rules
    ├── operations/                # Operations phase rules
    └── extensions/                # Opt-in extensions
        ├── security/baseline/
        └── testing/property-based/
```

## Contributing

Do not edit files in this directory directly. Edit the canonical source in
`aidlc-rules/` at the repository root, then regenerate:

```bash
python scripts/build-plugins.py
```

CI (`plugin-sync` job) runs the generator on every PR and fails if the
committed output drifts from the source.

## License

Apache-2.0 — see [LICENSE](../../LICENSE).
"""


def build_cursor_plugin(output_dir: Path) -> None:
    """Generate the Cursor rules plugin directory.

    Output layout:
        plugins/cursor-aidlc/
        ├── README.md
        ├── .markdownlint-cli2.yaml
        └── rules/
            ├── aidlc-orchestrator.mdc   (alwaysApply: true)
            ├── core-workflow.mdc         (transformed core)
            ├── common/*.mdc
            ├── inception/*.mdc
            ├── construction/*.mdc
            ├── operations/*.mdc
            └── extensions/
                ├── security/baseline/*.mdc
                └── testing/property-based/*.mdc
    """
    version = read_version()
    clean_output(output_dir)

    # README
    (output_dir / "README.md").write_text(cursor_plugin_readme(version))

    # Rule tree root — flat under rules/ so manual copy is straightforward
    rules_root = output_dir / "rules"
    rules_root.mkdir(parents=True)

    # -- Orchestrator rule (alwaysApply) --
    (rules_root / "aidlc-orchestrator.mdc").write_text(
        cursor_orchestrator_rule_content()
    )

    # -- core-workflow.mdc (transformed for Cursor) --
    core_src = RULES_ENTRY.read_text()
    # Apply the Cursor-specific path-resolution transform
    if PATH_RESOLUTION_OLD not in core_src:
        print(
            "ERROR: Could not find the path-resolution block in core-workflow.md.",
            file=sys.stderr,
        )
        sys.exit(1)
    core_transformed_body = core_src.replace(
        PATH_RESOLUTION_OLD, CURSOR_PATH_RESOLUTION_NEW, 1
    )
    core_description = (
        "AI-DLC core workflow — three-phase adaptive software development "
        "lifecycle (Inception, Construction, Operations)"
    )
    core_frontmatter = (
        "---\n"
        f'description: "{core_description}"\n'
        "alwaysApply: false\n"
        "---\n\n"
    )
    (rules_root / "core-workflow.mdc").write_text(
        core_frontmatter + core_transformed_body
    )

    # -- All rule-detail files converted to .mdc --
    for source_md in sorted(RULE_DETAILS.rglob("*.md")):
        rel = source_md.relative_to(RULE_DETAILS)
        rel_str = str(rel)
        mdc_path = rules_root / rel.with_suffix(".mdc")
        mdc_path.parent.mkdir(parents=True, exist_ok=True)
        mdc_path.write_text(convert_to_mdc(source_md, rel_str))

    write_plugin_markdownlint_config(output_dir)

    print(f"Cursor plugin generated at {output_dir} (version {version})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate AIDLC plugins for supported AI coding agents"
    )
    parser.add_argument(
        "--target",
        choices=["all", "cc", "cursor"],
        default="all",
        help="Which plugin(s) to build (default: all)",
    )
    parser.add_argument(
        "--cc-output-dir",
        type=Path,
        default=CC_DEFAULT_OUTPUT,
        help=f"Claude Code plugin output directory "
        f"(default: {CC_DEFAULT_OUTPUT.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--cursor-output-dir",
        type=Path,
        default=CURSOR_DEFAULT_OUTPUT,
        help=f"Cursor plugin output directory "
        f"(default: {CURSOR_DEFAULT_OUTPUT.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()

    if args.target in ("all", "cc"):
        build_cc_plugin(args.cc_output_dir)
    if args.target in ("all", "cursor"):
        build_cursor_plugin(args.cursor_output_dir)


if __name__ == "__main__":
    main()
