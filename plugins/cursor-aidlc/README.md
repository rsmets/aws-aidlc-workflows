# AI-DLC Cursor Rules

AI-Driven Development Life Cycle (AI-DLC) packaged as a Cursor rule set.
Provides the same adaptive three-phase workflow (Inception, Construction,
Operations) as the Claude Code plugin, distributed via Cursor's native rule
system.

**Version**: 0.1.8
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

Once installed, the `.cursor/rules/aidlc-orchestrator.mdc` rule is set to
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
