---
name: AIDLC Construction Phase
description: >-
  Construction phase rules for AIDLC — detailed design, implementation, and
  testing. Load when executing functional design, NFR requirements, NFR design,
  infrastructure design, code generation, or build and test stages.
version: 0.1.8
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
