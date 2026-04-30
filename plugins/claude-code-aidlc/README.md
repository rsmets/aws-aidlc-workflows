# AI-DLC Claude Code Plugin

AI-Driven Development Life Cycle (AI-DLC) packaged as a Claude Code plugin.
Provides an adaptive three-phase software development workflow (Inception,
Construction, Operations) driven by an orchestrator agent, phase-specific slash
commands, and progressive-disclosure skills.

**Version**: 0.1.8
**Source of truth**: `aidlc-rules/` in this repository
**Generator**: `scripts/build-plugins.py`

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
python scripts/build-plugins.py
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
