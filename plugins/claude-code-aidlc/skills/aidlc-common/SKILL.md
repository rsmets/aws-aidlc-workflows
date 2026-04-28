---
name: AIDLC Common Rules
description: >-
  Cross-cutting AIDLC rules — terminology, depth levels, question formatting,
  error handling, content validation, session continuity, welcome message, and
  other shared guidance. Loaded as supporting context by other AIDLC skills.
version: 0.1.8
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
