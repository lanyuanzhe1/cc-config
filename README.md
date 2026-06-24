# cc-config

Claude Code cross-platform configuration sync.

This repository stores shared Claude Code configurations between Mac and Windows machines.

## Structure

```
cc-config/
├── settings/          # Whitelisted settings fields
├── mcp/               # MCP server definitions (platform-aware)
├── skills/            # User skill directories
├── plugins/           # Plugin manifest
├── agents/            # Custom agent definitions
├── CLAUDE.md          # User-level CLAUDE.md (cross-platform)
├── global-memory/     # Global memory files
└── manifests/         # Per-machine sync state
```

## Usage

Managed by the `cc-sync` Claude Code skill. Use `/cc-sync status|diff|push|pull` to interact.
