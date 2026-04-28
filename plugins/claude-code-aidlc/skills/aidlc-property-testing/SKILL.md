---
name: AIDLC Property-Based Testing Extension
description: >-
  Optional property-based testing extension for AIDLC — enforces PBT rules for
  pure functions, serialization, and stateful components. Load when the user
  opts in to property-based testing during AIDLC Requirements Analysis.
version: 0.1.8
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
> X) Other (please describe after \[Answer\]: tag below)

## Usage

- Present the opt-in prompt during Requirements Analysis
- If the user opts **in** (A or B), read the full rules from
  `references/extensions/testing/property-based/property-based-testing.md`
- If the user opts **out** (C), do not load the full rules file
- Track the enablement decision and level in `aidlc-docs/aidlc-state.md` under
  `## Extension Configuration`
- When enabled, extension rules are **hard constraints** — non-compliance is a
  blocking finding
