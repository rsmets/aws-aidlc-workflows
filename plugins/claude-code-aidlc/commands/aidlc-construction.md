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
