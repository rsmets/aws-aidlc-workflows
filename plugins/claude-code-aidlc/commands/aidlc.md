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
