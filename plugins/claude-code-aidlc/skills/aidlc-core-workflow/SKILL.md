---
name: AIDLC Core Workflow
description: >-
  The master AI-DLC adaptive workflow — load when initializing or resuming an
  AIDLC software development workflow. Defines the three-phase lifecycle
  (Inception, Construction, Operations), stage sequencing, mandatory rules,
  and the adaptive execution model.
version: 0.1.8
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
