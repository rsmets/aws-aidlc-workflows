---
name: AIDLC Inception Phase
description: >-
  Inception phase rules for AIDLC — planning, requirements, and architecture.
  Load when executing workspace detection, reverse engineering, requirements
  analysis, user stories, workflow planning, application design, or units
  generation stages.
version: 0.1.8
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
