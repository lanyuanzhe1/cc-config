---
name: cc-sync
description: Use when checking, comparing, pushing, or pulling personal Codex skills, agents, plugins, MCP servers, safe settings, and portable memory across machines.
triggers:
  - /cc-sync
  - cc-sync
  - sync Codex config
  - sync cc config
  - 同步配置
  - 同步Codex配置
---

# cc-sync

Synchronize portable Codex configuration through `~/cc-config`.

## Commands

- `/cc-sync status` — fetch and report local/remote state; no configuration writes
- `/cc-sync diff` — show local ↔ repository differences; no configuration writes
- `/cc-sync push` — copy approved local changes into the repository, commit, and push
- `/cc-sync pull` — fetch repository changes and apply approved changes locally

If the user says only “test” or “check”, run `status`. Never infer `push` or `pull`.

## Current layout

Use lowercase `.codex` in generated paths. On a case-insensitive filesystem, do not treat `.Codex` as a separate root.

| Item | Local source | Repository path | Method |
|---|---|---|---|
| Skills | `~/.agents/skills/`, then `~/.codex/skills/` | `skills/` | merged directories |
| Agents | `~/.codex/agents/` | `agents/` | full file copy |
| Plugins | `[plugins]` in `~/.codex/config.toml` | `config/plugins.json` | table export/merge |
| MCP | `[mcp_servers]` in `~/.codex/config.toml` | `config/mcp-servers.json` | table export/merge with placeholders |
| Settings | safe keys in `~/.codex/config.toml` | `config/settings.json` | whitelist export/merge |
| Memory | exported portable records | `memory/` | export/import, never live DB copy |
| Manifest | generated metadata | `manifests/<hostname>.json` | generated |

### Explicit exclusions

Never synchronize, compare, copy, delete, mention as pending, or add to summaries:

- user-level base instruction files (`AGENTS.md` and `CLAUDE.md`)
- project-level base instruction files (`AGENTS.md` and `CLAUDE.md`)
- `.env`, `auth.json`, tokens, API keys, cookies, credentials
- absolute project trust entries from `[projects]`
- live SQLite databases or their `-wal`/`-shm` files
- plugin caches or bundled/plugin-provided skills under `~/.codex/plugins/cache/`
- runtime state, sessions, logs, attachments, browser profiles, generated media

## Skill merge contract

Build one logical skill set without modifying either local source:

1. Enumerate direct child directories containing `SKILL.md` in `~/.agents/skills/`.
2. Add direct child directories containing `SKILL.md` in `~/.codex/skills/`.
3. If the same name exists in both roots, `~/.agents/skills/<name>` wins. Report the shadowed Codex copy.
4. Ignore `.system`, hidden directories, symlinks escaping the source root, caches, and directories without `SKILL.md`.
5. On push, copy each selected directory to `~/cc-config/skills/<name>/` with `rsync -a --delete`.
6. A repository-only skill is a pull candidate. A local-only skill is a push candidate.
7. Never delete a local skill during pull without separate explicit confirmation.

## Safe config contract

Parse TOML with Python 3.11+ `tomllib`. Do not parse TOML with regex.

Export these top-level settings only when present:

- `model`
- `model_reasoning_effort`
- `personality`
- `notify`
- `wire_api`
- `[desktop]`
- `[features]`
- `[plugins]`
- `[marketplaces]`
- `[mcp_servers]`

Before export, recursively reject any field whose key contains `secret`, `token`, `password`, `api_key`, `apikey`, `credential`, or `cookie`. Do not export `base_url`, `[projects]`, or any value containing the current home directory. Report rejected fields without printing their values.

Store plugins and MCP separately from general settings. Pull merges only the listed keys/tables into the existing `config.toml`; unrelated local fields remain unchanged. Use a TOML-aware writer (`tomlkit` preferred) so comments and unrelated formatting survive. Create a timestamped backup beside `config.toml` immediately before a pull modifies it.

### MCP platform mapping

Use `~/cc-config/config/platform-map.json`, which must be gitignored. Reverse-map machine-specific executable paths to `{{VAR}}` on push and expand them on pull. If a placeholder has no mapping, skip that server and report it; never write an unresolved placeholder into `config.toml`.

## Portable memory

Current Codex memory may live in `~/.codex/memories_1.sqlite`. Never copy that database.

- If an official memory export/import interface is callable, use it.
- Otherwise export only user-approved, non-secret text records to `~/cc-config/memory/*.json` with stable IDs and timestamps.
- If no safe export interface or understood schema is available, report memory as `unsupported`; do not guess the SQLite schema or mutate it.

## Repository setup

If `~/cc-config/.git` is absent, stop and offer setup. Setup creates:

```text
~/cc-config/
  skills/
  agents/
  config/
    settings.json
    plugins.json
    mcp-servers.json
    platform-map.json   # gitignored
  memory/
  manifests/
```

Ensure `.gitignore` includes:

```gitignore
.DS_Store
**/.DS_Store
config/platform-map.json
```

Do not migrate or remove legacy repository files during `status` or `diff`. Report them as legacy. Migration is a separate confirmed write.

## `/cc-sync status`

1. Verify the repository and run `git fetch origin`.
2. Determine hostname and platform (`darwin` or `win32`).
3. Read `manifests/<hostname>.json`, if valid.
4. Apply the skill merge contract and compare selected skills with `skills/`.
5. Parse `~/.codex/config.toml`, export the safe in-memory views, and compare them with `config/*.json`.
6. Compare agents and supported portable memory.
7. Report repository worktree changes and commit divergence:
   - `git rev-list --count HEAD..origin/main`
   - `git rev-list --count origin/main..HEAD`

Report `Up to date`, `Ready to push`, `Ready to pull`, `Diverged`, or `Never synced`. A dirty `~/cc-config` worktree must be called out separately.

## `/cc-sync diff`

Run the same read-only normalization as `status`, then show:

- `+` local-only (would push)
- `-` repository-only (would pull)
- `~` different on both sides

For skills, report names and changed relative paths, not full contents. For config, show field names and redacted structural changes; never print secret-looking values. Mark legacy repository files separately. Do not merge, pull, copy, or format files.

## `/cc-sync push`

1. Run the complete diff and present a category summary.
2. Ask for confirmation: `Push now`, `Cancel`, or `Show full diff`.
3. Fetch and rebase onto `origin/main`. Resolve conflicts per file/field with the user; never choose silently.
4. Apply only confirmed categories:
   - skills via the skill merge contract
   - agents via `rsync -a --delete`
   - config via safe normalized JSON exports
   - memory only through the portable memory contract
5. Never include explicit exclusions, even if legacy copies exist in the repository.
6. Remove `.DS_Store` only inside `~/cc-config` when confirmed as repository cleanup; add ignore rules.
7. Commit with category counts and push.
8. Write and push the manifest only after the content push succeeds.

If nothing changed, report it and do not create a commit.

## `/cc-sync pull`

1. Fetch and fast-forward `~/cc-config`.
2. Run the complete diff and present the incoming category summary.
3. Ask for confirmation: `Pull now`, `Cancel`, or `Show full diff`.
4. Detect conflicts since the manifest commit. Auto-merge only disjoint JSON fields; ask for overlapping fields or files.
5. Apply confirmed categories:
   - skills to `~/.agents/skills/` by default
   - agents to `~/.codex/agents/`
   - config through a TOML-aware field merge after creating a timestamped backup
   - memory only through a supported import interface
6. Repository deletions never delete local skills or agents without separate confirmation.
7. Validate TOML and JSON, then update and push the manifest.

After plugin changes, tell the user a Codex restart may be required. Do not assume copying plugin configuration installs unavailable plugins.

## Manifest

```json
{
  "hostname": "machine-name",
  "platform": "darwin",
  "last_sync": "ISO-8601 timestamp",
  "last_commit": "full commit SHA",
  "sync_direction": "push"
}
```

## Failure handling

- Network/auth failure: stop before local configuration writes.
- Invalid TOML/JSON: identify the file and parse error; skip that category.
- Missing platform mapping: skip only affected MCP servers.
- Rebase conflict: resolve interactively or `git rebase --abort`.
- Partial pull: restore the timestamped config backup and report copied file paths.
- Dirty sync repository: do not overwrite unknown user changes; identify them and ask how to proceed.
