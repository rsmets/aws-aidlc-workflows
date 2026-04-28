---
name: AIDLC Security Baseline Extension
description: >-
  Optional security extension for AIDLC — enforces security baseline rules as
  blocking constraints. Load when the user opts in to security enforcement
  during AIDLC Requirements Analysis.
version: 0.1.8
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
> X) Other (please describe after \[Answer\]: tag below)

## Usage

- Present the opt-in prompt during Requirements Analysis
- If the user opts **in**, read the full rules from
  `references/extensions/security/baseline/security-baseline.md`
- If the user opts **out**, do not load the full rules file
- Track the enablement decision in `aidlc-docs/aidlc-state.md` under
  `## Extension Configuration`
- When enabled, extension rules are **hard constraints** — non-compliance is a
  blocking finding
