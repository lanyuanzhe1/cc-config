---
name: cc-sync
description: |
  Cross-platform Claude Code configuration sync via GitHub. 
  Sync skills, plugins, MCP, settings, agents, CLAUDE.md, and global memory 
  between Mac and Windows. Commands: /cc-sync status, /cc-sync diff, 
  /cc-sync push, /cc-sync pull.
triggers:
  - /cc-sync
  - cc-sync
  - sync claude code config
  - sync cc config
  - 同步配置
  - 同步claude配置
---

# cc-sync: Cross-Platform Claude Code Configuration Sync

Synchronize Claude Code configurations between Mac and Windows via a central GitHub repository (`cc-config`).

## What Gets Synced

| Item | Method | Direction |
|------|--------|-----------|
| Skills (`~/.claude/skills/`) | Full file copy | Bidirectional |
| Plugins (`installed_plugins.json`) | Manifest sync | Bidirectional |
| Settings (`settings.json`) | Field-level (whitelist) | Bidirectional |
| MCP (`.mcp.json`) | Platform-aware with `{{VAR}}` | Bidirectional |
| Agents (`~/.claude/agents/`) | Full file copy | Bidirectional |
| CLAUDE.md | File sync | Bidirectional |
| Global Memory | File sync | Bidirectional |

## Prerequisites

- Git installed and configured
- GitHub account with SSH or HTTPS access
- A GitHub repository named `cc-config` (use Setup to create it)

## Commands

- `/cc-sync status` — Show current sync state (read-only)
- `/cc-sync diff` — Compare local vs repository (read-only)
- `/cc-sync push` — Upload local config to repository
- `/cc-sync pull` — Download repository config to local

---

## Setup (First Time)

If `~/cc-config/.git` does NOT exist, run this setup. Otherwise skip directly to the requested command.

### Step A: Determine username and repo URL

First, determine the GitHub username:
```bash
gh auth status 2>/dev/null && gh api user --jq '.login' 2>/dev/null || git config --global user.name
```

If `gh` is not available, ask the user for their GitHub username.

### Step B: Create the GitHub repository

Check if the repo already exists:
```bash
gh repo view cc-config 2>/dev/null
```

If the above fails (repo doesn't exist), create it:
```bash
gh repo create cc-config --public --description "Claude Code cross-platform config sync"
```

If `gh` is not available, instruct the user to create it manually at `https://github.com/new` with name `cc-config`.

### Step C: Clone locally

```bash
git clone git@github.com:<username>/cc-config.git ~/cc-config 2>/dev/null || \
git clone https://github.com/<username>/cc-config.git ~/cc-config
```

### Step D: Initialize repository structure

```bash
mkdir -p ~/cc-config/settings
mkdir -p ~/cc-config/mcp
mkdir -p ~/cc-config/skills
mkdir -p ~/cc-config/plugins
mkdir -p ~/cc-config/agents
mkdir -p ~/cc-config/global-memory
mkdir -p ~/cc-config/manifests
```

### Step E: Create platform-map.json (gitignored, per-machine)

Read the local `~/.claude/.mcp.json` to discover any platform-specific paths. Ask the user to provide path mappings for common variables:

Create `~/cc-config/mcp/platform-map.json`:
```json
{
  "mac": {},
  "win": {}
}
```

Populate the current platform's section with path mappings. Common variables: `{{PYTHON}}`, `{{NODE}}`. Ask the user for the correct paths on this machine.

### Step F: Create .gitignore

Write `~/cc-config/.gitignore`:
```
mcp/platform-map.json
```

### Step G: First commit and push

```bash
cd ~/cc-config
git add -A
git commit -m "chore: initialize cc-config repository structure"
git push -u origin main
```

Setup complete. Now proceed to the requested command.

---

## /cc-sync status

Show current sync state without modifying anything.

### Algorithm

**1. Verify repo and fetch remote:**
```bash
cd ~/cc-config && git fetch origin 2>/dev/null
```
If `~/cc-config/.git` doesn't exist, instruct user to run setup first.

**2. Determine hostname and platform:**
- macOS: run `hostname` or `scutil --get ComputerName`
- Windows: run `echo %COMPUTERNAME%`
- Platform: check `uname -s` — "Darwin" = mac, "MINGW*" or "MSYS*" = win

**3. Read last sync manifest:**
Check if `~/cc-config/manifests/<hostname>.json` exists. If yes, read it to get `last_sync` and `last_commit`. If no, this machine has never synced.

**4. Detect local changes (compare ~/.claude/ vs ~/cc-config/):**

For each sync item:

- **Skills:** `diff -rq ~/.claude/skills/ ~/cc-config/skills/ 2>/dev/null` — count added, modified, deleted directories
- **Plugins:** Compare `~/.claude/plugins/installed_plugins.json` with `~/cc-config/plugins/installed_plugins.json` using `diff`
- **Settings:** Read `~/.claude/settings.json`, extract whitelist fields (model, theme, effortLevel, includeCoAuthoredBy, enableAllProjectMcpServers, permissions, hooks, enabledPlugins, enabledMcpjsonServers). Compare to `~/cc-config/settings/settings.sync.json` field by field.
- **MCP:** Read `~/.claude/.mcp.json`. For each server, reverse-map known paths to `{{VAR}}` using local `platform-map.json`. Compare to `~/cc-config/mcp/mcp.sync.json`.
- **Agents:** `diff -rq ~/.claude/agents/ ~/cc-config/agents/ 2>/dev/null`
- **CLAUDE.md:** `diff ~/.claude/CLAUDE.md ~/cc-config/CLAUDE.md 2>/dev/null`
- **Global Memory:** List `.md` files under `~/.claude/projects/*/memory/`, compare names and content with `~/cc-config/global-memory/`

**5. Check remote changes:**
```bash
cd ~/cc-config
REMOTE_AHEAD=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
LOCAL_AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")
```

**6. Report:**

```
📊 cc-sync Status — <hostname> (<platform>)

Last sync: <timestamp or "Never">
Last commit: <short SHA or "N/A">

Local changes (not yet pushed):
  Skills:     <n> added, <n> modified, <n> deleted (or "up to date")
  Plugins:    <changed or "up to date">
  Settings:   <n> fields changed (or "up to date")
  MCP:        <changed or "up to date">
  Agents:     <n> added, <n> modified (or "up to date")
  CLAUDE.md:  <changed or "up to date">
  Memory:     <n> added, <n> modified (or "up to date")

Remote changes: <n> commits ahead
Local unpushed: <n> commits

Status: <"Up to date" | "Ready to push" | "Ready to pull" | "Diverged — push/pull needed" | "Never synced — run push or pull">
```

### Edge Cases

- **No manifest:** Report "Never synced"
- **File missing locally:** Report as "not found"
- **File missing in repo:** Report as "not tracked"
- **Empty repo (first push by anyone):** Report "No commits yet — push first"

---

## /cc-sync diff

Read-only comparison between local configuration and repository. Shows exactly what would change on push or pull, without making any modifications.

### Algorithm

**1. Ensure repo is current:**
```bash
cd ~/cc-config && git fetch origin && git merge --ff-only origin/main 2>/dev/null || true
```

**2. Compare each sync item:**

#### Skills

```bash
# New locally (would be added on push)
comm -23 <(ls ~/.claude/skills/ 2>/dev/null | sort) <(ls ~/cc-config/skills/ 2>/dev/null | sort)

# Only in repo (would be added on pull)
comm -13 <(ls ~/.claude/skills/ 2>/dev/null | sort) <(ls ~/cc-config/skills/ 2>/dev/null | sort)

# In both — check for differences
for dir in $(comm -12 <(ls ~/.claude/skills/ 2>/dev/null | sort) <(ls ~/cc-config/skills/ 2>/dev/null | sort)); do
  if ! diff -rq ~/.claude/skills/"$dir" ~/cc-config/skills/"$dir" > /dev/null 2>&1; then
    echo "MODIFIED: $dir"
  fi
done
```

#### Plugins

Read both `~/.claude/plugins/installed_plugins.json` and `~/cc-config/plugins/installed_plugins.json`. Parse the JSON, iterate over plugin names. For each:
- In local but not repo → `+ added`
- In repo but not local → `- removed`
- In both with different version → `~ version: X → Y`

#### Settings

Read `~/.claude/settings.json`. Extract the whitelist fields: `model`, `theme`, `effortLevel`, `includeCoAuthoredBy`, `enableAllProjectMcpServers`, `permissions`, `hooks`, `enabledPlugins`, `enabledMcpjsonServers`.

Compare each extracted field against the corresponding value in `~/cc-config/settings/settings.sync.json`. Report differences line by line.

If `settings.sync.json` doesn't exist in repo, report all local whitelist fields as `+ new`.

#### MCP

1. Read `~/.claude/.mcp.json`
2. Read `~/cc-config/mcp/mcp.sync.json`
3. Read `~/cc-config/mcp/platform-map.json` for reverse-mapping
4. For each server in local `.mcp.json`, reverse-map command paths using platform-map: if the command path matches a known mapped path, replace with `{{VAR}}`
5. Compare server-by-server against repo

#### Agents

Same pattern as Skills: `comm` for added/removed, `diff -rq` for modified.

#### CLAUDE.md

```bash
diff ~/.claude/CLAUDE.md ~/cc-config/CLAUDE.md 2>/dev/null
```

#### Global Memory

Compare `.md` files in `~/.claude/projects/*/memory/` with `~/cc-config/global-memory/`. Files with same name but different content = modified. New files = added. Files in repo not in any local memory dir = removed.

**3. Display diff report:**

Use the following format:
```
📋 Diff Report: local ↔ cc-config

Skills:
  + write-a-skill/              (new locally — would push)
  ~ diagnose/                   (modified — SKILL.md differs)
  (2 items changed)

Plugins:
  + superpowers@claude-plugins-official 6.0.3
  (1 item changed)

Settings:
  ~ effortLevel: "high" → "xhigh"
  ~ model: "sonnet" → "opus"
  (2 fields changed)

MCP:
  + mcp-vision                  (new locally — would push)
  (1 item changed)

Agents:
  (no changes)

CLAUDE.md:
  ~ modified (15 lines changed)

Memory:
  + user-preferences.md         (new locally)
  (1 item changed)

═══════════════════════════════════
Summary: 7 items scanned, 5 with changes
  4 local-only changes (push needed)
  0 remote-only changes
  1 both-sides change (needs merge)
```

**Display rules:**
- `+` prefix for additions
- `-` prefix for deletions
- `~` prefix for modifications
- Items with no changes: print `(no changes)` on a single line
- For large text diffs (>20 lines), show first 10 changed lines followed by `... (N more lines)`

---

## /cc-sync push

Upload local configuration to the GitHub repository.

### Phase 1: Pre-flight Summary

Run the diff algorithm (from `/cc-sync diff`) internally. Present a summary using `AskUserQuestion`:

```
🔄 Preparing to push from <hostname>:
  Skills:    1 added, 1 modified
  Plugins:   up to date
  Settings:  2 fields changed
  MCP:       1 server added
  Agents:    up to date
  CLAUDE.md: modified
  Memory:    1 added

Proceed with push?
```

Options: `["Yes, push now", "No, cancel", "Show full diff first"]`

If "Show full diff first", display the full diff, then re-ask. If "No", abort. If "Yes", continue.

### Phase 2: Pull Remote Changes

```bash
cd ~/cc-config
git fetch origin
REMOTE_AHEAD=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
```

If `REMOTE_AHEAD` > 0:
```bash
git pull --rebase origin main
```

If rebase succeeds with no conflicts → continue to Phase 3.

If rebase fails with conflicts → **Enter Conflict Resolution Mode** (see below). After resolving all conflicts and completing the rebase, continue to Phase 3.

If this is the first push (repo has no commits / empty main branch), skip pull entirely.

### Phase 3: Copy Local Files to Repo

For each sync item with detected changes:

**Skills:**
```bash
# Copy new/modified skills
for dir in <changed_skill_dirs>; do
  rsync -a --delete ~/.claude/skills/"$dir"/ ~/cc-config/skills/"$dir"/
done
# Remove deleted skills
for dir in <deleted_skill_dirs>; do
  rm -rf ~/cc-config/skills/"$dir"
done
```

**Plugins:**
```bash
cp ~/.claude/plugins/installed_plugins.json ~/cc-config/plugins/installed_plugins.json
```

**Settings (whitelist extraction):**

Read `~/.claude/settings.json`. Extract only these fields: `model`, `theme`, `effortLevel`, `includeCoAuthoredBy`, `enableAllProjectMcpServers`, `permissions`, `hooks`, `enabledPlugins`, `enabledMcpjsonServers`. Write to `~/cc-config/settings/settings.sync.json`.

Use Python for the extraction (available on both platforms):
```bash
python3 -c "
import json, os
home = os.path.expanduser('~')
with open(os.path.join(home, '.claude', 'settings.json')) as f:
    local = json.load(f)
whitelist = ['model','theme','effortLevel','includeCoAuthoredBy','enableAllProjectMcpServers','permissions','hooks','enabledPlugins','enabledMcpjsonServers']
sync = {k: v for k, v in local.items() if k in whitelist}
with open(os.path.join(home, 'cc-config', 'settings', 'settings.sync.json'), 'w') as f:
    json.dump(sync, f, indent=2)
print(f'Synced {len(sync)} fields to settings.sync.json')
"
```

On Windows, use the same Python script (paths auto-resolve via `os.path.expanduser`).

**MCP (with reverse mapping):**

Read `~/.claude/.mcp.json`. Read `~/cc-config/mcp/platform-map.json` for the current platform.

For each MCP server in local config:
1. Check if its `command` matches any value in the platform-map → if yes, replace with `{{VAR}}`
2. Preserve `args`, `env` as-is
3. Add/update `platforms` array: if current platform not in list, add it

Write the result to `~/cc-config/mcp/mcp.sync.json`.

If `platform-map.json` has no entries yet, ask user: "I see MCP server '<name>' uses command '<path>'. Should I add this as a platform variable?" If yes, guide them to add it to `platform-map.json`.

**Agents:**
```bash
rsync -a --delete ~/.claude/agents/ ~/cc-config/agents/ 2>/dev/null || true
```

**CLAUDE.md:**
```bash
cp ~/.claude/CLAUDE.md ~/cc-config/CLAUDE.md 2>/dev/null || echo "No user-level CLAUDE.md found at ~/.claude/CLAUDE.md"
```
Note: `~/.claude/CLAUDE.md` is a user-level file. If it doesn't exist, skip (don't error).

**Global Memory:**
```bash
# Collect all memory .md files from all projects
rm -f ~/cc-config/global-memory/*.md
find ~/.claude/projects -path "*/memory/*.md" -exec cp {} ~/cc-config/global-memory/ \; 2>/dev/null || true

# Rebuild MEMORY.md index if memory files exist
if ls ~/cc-config/global-memory/*.md 2>/dev/null | grep -v MEMORY.md > /dev/null; then
  echo "# Global Memory Index" > ~/cc-config/global-memory/MEMORY.md
  echo "" >> ~/cc-config/global-memory/MEMORY.md
  for f in ~/cc-config/global-memory/*.md; do
    basename=$(basename "$f")
    if [ "$basename" != "MEMORY.md" ]; then
      echo "- [$basename]($basename)" >> ~/cc-config/global-memory/MEMORY.md
    fi
  done
fi
```

### Phase 4: Commit and Push

Build a descriptive commit message:
```
cc-sync: push from <hostname> (<platform>)

- skills: <n> added, <n> modified, <n> deleted
- plugins: <summary>
- settings: <changed fields, comma-separated>
- mcp: <summary>
- agents: <summary>
- claude.md: <changed or "no changes">
- memory: <n> added, <n> modified
```

Then:
```bash
cd ~/cc-config
git add -A
git commit -m "<commit message>"
git push origin main
```

If push fails (non-fast-forward), this is unexpected after rebase. Report the error and suggest:
```bash
cd ~/cc-config && git pull --rebase origin main && git push origin main
```

### Phase 5: Update Manifest

Get the new commit SHA:
```bash
cd ~/cc-config && git rev-parse HEAD
```

Create/update `~/cc-config/manifests/<hostname>.json`:
```json
{
  "hostname": "<hostname>",
  "platform": "<darwin|win32>",
  "last_sync": "<ISO 8601 timestamp>",
  "last_commit": "<full SHA>",
  "sync_direction": "push"
}
```

Commit and push the manifest:
```bash
cd ~/cc-config
git add manifests/<hostname>.json
git commit -m "cc-sync: update manifest for <hostname> (push)"
git push origin main
```

Report success:
```
✅ Push complete! <hostname> → cc-config
   Commit: <short SHA>
   Synced: <summary of what was pushed>
```

---

### Conflict Resolution Mode (Push)

Triggered when `git pull --rebase` fails with merge conflicts during Phase 2.

**Step 1: Identify conflicted files:**
```bash
cd ~/cc-config
git diff --name-only --diff-filter=U
```

**Step 2: For each conflicted file, extract both versions:**

- Local version (this machine's push): `git show :2:<file>`
- Remote version (other machine's push): `git show :3:<file>`

**Step 3: Analyze and present each conflict to the user:**

Use `AskUserQuestion` for each conflict. Present:

- The file path
- What changed on this machine (local)
- What changed on the remote
- Whether changes overlap or are in different sections

Options:
- `[Keep Mine]` — discard remote changes for this file
- `[Keep Remote]` — discard local changes for this file
- `[Keep Both (auto-merge)]` — for text files where changes don't overlap, merge both
- `[Show Full Diff]` — show the complete diff before deciding

For JSON files (settings, plugins): present field-by-field. Different fields changed → auto-merge. Same field changed → ask user which value to keep.

For text files (CLAUDE.md, memory, skill files): if changes are in non-overlapping sections (different line ranges), offer "Keep Both". If overlapping, user must choose Mine or Remote.

**Step 4: Apply resolution:**

- Keep Mine: `git checkout --ours <file> && git add <file>`
- Keep Remote: `git checkout --theirs <file> && git add <file>`
- Keep Both: Manually edit the file to include both changes, then `git add <file>`

**Step 5: Continue rebase:**
```bash
git rebase --continue
```
If more conflicts surface, repeat from Step 1.

If rebase becomes too complex, abort and suggest manual resolution:
```bash
git rebase --abort
```
Report: "Rebase aborted. The repository is back to its previous state. Consider pushing/pulling individual items manually."

---

### Edge Cases (Push)

- **First push (empty repo, no commits):** Skip Phase 2 (pull). In Phase 4, use `git push -u origin main`.
- **No changes detected:** Report "Already up to date — nothing to push" and exit.
- **settings.json missing:** Warn "No settings.json found at ~/.claude/settings.json", skip settings sync, continue with other items.
- **skills directory empty:** Skip skills sync (nothing to push).
- **CLAUDE.md not found:** Skip CLAUDE.md sync, note in commit message.

---

## /cc-sync pull

Download configuration from GitHub repository and apply to local `~/.claude/`.

### Phase 1: Fetch Latest

```bash
cd ~/cc-config
git fetch origin
git pull origin main
```

If pull fails (network, auth), report error and abort.

### Phase 2: Diff and Confirm

Run the diff algorithm (from `/cc-sync diff`) to compare repo vs local. Present summary using `AskUserQuestion`:

```
⬇️  Preparing to pull to <hostname>:
  Skills:    2 new, 1 modified, 0 deleted
  Plugins:   3 plugins updated
  Settings:  2 fields will change
  MCP:       1 server config updated
  Agents:    no changes
  CLAUDE.md: modified (12 lines)
  Memory:    1 new memory file

Proceed with pull?
```

Options: `["Yes, pull now", "No, cancel", "Show full diff first"]`

### Phase 3: Conflict Detection

Before applying changes, check if local files have been modified since last sync. Read the manifest for `last_commit`. If local files differ from what was recorded at that commit AND repo also has changes to the same item → potential conflict.

For each sync item:

- **Skills:** If a skill directory was modified locally AND repo has a different version → ask user. Otherwise, just overwrite with repo version.
- **Settings:** Field-level. Different fields changed → auto-merge. Same field changed both sides → ask user.
- **MCP:** Server-level comparison. Same server changed both sides → ask user.
- **CLAUDE.md:** Line-level. Non-overlapping line ranges → auto-merge. Overlapping → ask user.
- **Memory:** Same file changed both sides → ask user.

For each detected conflict, present with same options as push conflict resolution:
`[Keep Local] [Use Incoming] [Auto-merge] [Show Diff]`

### Phase 4: Apply Changes

After user confirms and all conflicts are resolved:

**Skills:**
For new/modified skills in repo:
```bash
rsync -a ~/cc-config/skills/<name>/ ~/.claude/skills/<name>/
```
For skills in repo but not local → this is new, just copy.
For skills deleted in repo (exist locally but not in repo) → **warn, do NOT auto-delete.** Ask user: "Skill '<name>' was removed from the repository. Delete it locally?" Only delete if user confirms.

**Plugins:**
```bash
cp ~/cc-config/plugins/installed_plugins.json ~/.claude/plugins/installed_plugins.json
```
After copying, remind user:
```
⚠️  Plugin manifest updated. To install newly added plugins:
   Run: claude plugins install
```

**Settings (field-level merge):**

Read local `~/.claude/settings.json`. Read repo `~/cc-config/settings/settings.sync.json`. For each field in the whitelist (`model`, `theme`, `effortLevel`, `includeCoAuthoredBy`, `enableAllProjectMcpServers`, `permissions`, `hooks`, `enabledPlugins`, `enabledMcpjsonServers`): overwrite local value with repo value. All other local fields remain untouched.

```bash
python3 -c "
import json, os
home = os.path.expanduser('~')
with open(os.path.join(home, '.claude', 'settings.json')) as f:
    local = json.load(f)
with open(os.path.join(home, 'cc-config', 'settings', 'settings.sync.json')) as f:
    sync = json.load(f)
whitelist = ['model','theme','effortLevel','includeCoAuthoredBy','enableAllProjectMcpServers','permissions','hooks','enabledPlugins','enabledMcpjsonServers']
for k in whitelist:
    if k in sync:
        local[k] = sync[k]
with open(os.path.join(home, '.claude', 'settings.json'), 'w') as f:
    json.dump(local, f, indent=2)
print('Settings merged successfully')
"
```

**MCP (with platform expansion):**

1. Read `~/cc-config/mcp/mcp.sync.json`
2. Read `~/cc-config/mcp/platform-map.json` for current platform
3. Determine current platform: `uname -s` → "Darwin" = `mac`, "MINGW*"/"MSYS*" = `win`
4. For each MCP server in sync file:
   - Check `platforms` array: if current platform is NOT in it, skip this server
   - For each `{{VAR}}` in the server's `command` or `args`, look up in `platform-map.json`[platform]
   - If a `{{VAR}}` has no mapping, warn user: "MCP server '<name>' needs variable '<VAR>' but it's not in your platform-map.json. Add it and re-run pull."
   - Build the `.mcp.json` entry with expanded values
5. Write to `~/.claude/.mcp.json`

If `platform-map.json` is missing entirely, create a minimal one and ask user to fill in paths.

**Agents:**
```bash
rsync -a ~/cc-config/agents/ ~/.claude/agents/ 2>/dev/null || true
```

**CLAUDE.md:**
```bash
cp ~/cc-config/CLAUDE.md ~/.claude/CLAUDE.md 2>/dev/null
```

**Global Memory:**

Copy memory files to the current project's memory directory. Determine the current project path from the conversation context (the working directory of this session).

```bash
# Determine project path from context (working directory)
PROJECT_DIR="<current working directory>"
# For Claude Code, the memory lives at:
MEMORY_DIR="$HOME/.claude/projects/$PROJECT_DIR/memory"
mkdir -p "$MEMORY_DIR"
cp ~/cc-config/global-memory/*.md "$MEMORY_DIR/"
```

If the current project path can't be determined, copy to all project memory directories (or ask user which project to apply to).

### Phase 5: Update Manifest

Update `~/cc-config/manifests/<hostname>.json`:
```json
{
  "hostname": "<hostname>",
  "platform": "<darwin|win32>",
  "last_sync": "<current ISO 8601 timestamp>",
  "last_commit": "<current HEAD SHA from cc-config>",
  "sync_direction": "pull"
}
```

Commit and push the manifest update:
```bash
cd ~/cc-config
git add manifests/<hostname>.json
git commit -m "cc-sync: update manifest for <hostname> (pull)"
git push origin main
```

Report success:
```
✅ Pull complete! cc-config → <hostname>
   Synced: <summary of what was pulled>
```

### Edge Cases (Pull)

- **Skill exists locally but not in repo:** This is a local-only skill. Warn: "Skill '<name>' exists locally but not in the repository. It will NOT be deleted. Push it first if you want to share it." Do NOT auto-delete.
- **Agent exists locally but not in repo:** Same pattern as skills — warn, don't delete.
- **MCP server has no platform mapping:** Skip that server, warn with specific variable name.
- **platform-map.json doesn't exist:** Create a minimal template, warn user to fill it in.
- **settings.json doesn't exist locally:** Create it from `settings.sync.json` (only whitelisted fields).
- **CLAUDE.md doesn't exist locally:** Just copy from repo, no conflict possible.

---

## Reference

### File Paths

| Config | macOS | Windows |
|--------|-------|---------|
| Claude Code root | `~/.claude/` | `%USERPROFILE%\\.claude\\` |
| Settings | `~/.claude/settings.json` | `%USERPROFILE%\\.claude\\settings.json` |
| Skills | `~/.claude/skills/` | `%USERPROFILE%\\.claude\\skills\\` |
| Plugins manifest | `~/.claude/plugins/installed_plugins.json` | `%USERPROFILE%\\.claude\\plugins\\installed_plugins.json` |
| MCP config | `~/.claude/.mcp.json` | `%USERPROFILE%\\.claude\\.mcp.json` |
| Agents | `~/.claude/agents/` | `%USERPROFILE%\\.claude\\agents\\` |
| User CLAUDE.md | `~/.claude/CLAUDE.md` | `%USERPROFILE%\\.claude\\CLAUDE.md` |
| CC Sync repo | `~/cc-config/` | `%USERPROFILE%\\cc-config\\` |

### Settings Whitelist

These fields from `settings.json` are synced (extracted on push, merged on pull):

- `model`
- `theme`
- `effortLevel`
- `includeCoAuthoredBy`
- `enableAllProjectMcpServers`
- `permissions`
- `hooks`
- `enabledPlugins`
- `enabledMcpjsonServers`

**Excluded from sync** (never copied to repo):
- `env` — contains secrets (API keys, tokens) and platform-specific PATH
- Any field value containing absolute user home paths (e.g., `/Users/...` or `C:\\Users\\...`)

### MCP Platform Variables

In `mcp/mcp.sync.json`, use `{{VAR}}` placeholders for platform-specific paths.

**Example `mcp/mcp.sync.json`:**
```json
{
  "playwright": {
    "command": "npx",
    "args": ["@playwright/mcp@latest", "--browser", "firefox"],
    "platforms": ["mac", "win"]
  },
  "mcp-vision": {
    "command": "{{PYTHON}}",
    "args": ["-m", "mcp_ocr.server"],
    "platforms": ["mac", "win"],
    "env": {
      "MCP_OCR_PROVIDER": "siliconflow",
      "SILICONFLOW_MODEL": "deepseek-ai/DeepSeek-OCR"
    }
  }
}
```

**Example `mcp/platform-map.json` (macOS):**
```json
{
  "mac": {
    "{{PYTHON}}": "/opt/homebrew/bin/python3",
    "{{NODE}}": "/opt/homebrew/bin/node"
  },
  "win": {}
}
```

**Example `mcp/platform-map.json` (Windows):**
```json
{
  "mac": {},
  "win": {
    "{{PYTHON}}": "C:\\Users\\<username>\\miniconda\\python.exe",
    "{{NODE}}": "C:\\Program Files\\nodejs\\node.exe"
  }
}
```

This file is **gitignored** — each machine maintains its own copy.

### Manifest Format

`~/cc-config/manifests/<hostname>.json`:
```json
{
  "hostname": "my-macbook",
  "platform": "darwin",
  "last_sync": "2026-06-24T15:30:00+08:00",
  "last_commit": "abc1234def567890...",
  "sync_direction": "push"
}
```

Platform values: `"darwin"` for macOS, `"win32"` for Windows.

### Error Recovery

| Problem | Recovery |
|---------|----------|
| Repo not cloned (`~/cc-config/.git` missing) | Run Setup section first |
| Manifest file corrupted | Delete manifest file, re-sync (treated as first sync) |
| Partial sync (crash mid-operation) | Git state tracks what was committed. Run `status` to check, then retry |
| Merge/rebase too complex | Abort with `git rebase --abort`, suggest syncing items individually |
| Network unavailable | Report clearly, suggest retry when connected |
| Corrupt JSON file | Report parse error with file path, skip that item, continue with others |
| Permission denied (file write) | Report which file failed, suggest checking file permissions |
