---
name: find-skill
description: Search the BuildWithClaude marketplace (github.com/davepoon/buildwithclaude) for Claude Code skills, plugins, commands, hooks, and MCP servers. Use when the user wants to find a skill by keyword, category, or name — e.g. "find me skills for PDF", "search marketplace for Slack automation", "show me all finance plugins". Covers 316+ skills across 117+ plugins.
license: MIT
---

# Find Skill — BuildWithClaude Marketplace Search

Search the BuildWithClaude community marketplace for Claude Code plugins and skills.

## Search Methods

### Method 1: Search marketplace.json (fast, plugin-level)

Fetch the marketplace index and filter by keyword, name, description, or category:

```bash
curl -sL "https://raw.githubusercontent.com/davepoon/buildwithclaude/main/.claude-plugin/marketplace.json" | python -c "
import sys, json
query = '<KEYWORD>'.lower()
data = json.load(sys.stdin)
matches = []
for p in data.get('plugins', []):
    text = json.dumps(p).lower()
    if query in text:
        matches.append(p)
for m in matches:
    print(f\"[{m.get('category', '?').upper()}] {m['name']}\")
    print(f\"  {m['description'][:120]}\")
    print(f\"  Keywords: {', '.join(m.get('keywords', [])[:8])}\")
    print(f\"  Source: {m.get('source', '?')}\")
    print()
print(f'--- {len(matches)} results for \"{query}\" ---')
"
```

Replace `<KEYWORD>` with the search term. Use lowercase. Multi-word queries: join with `.*` (e.g., `slack.*automation`).

### Method 2: Deep search SKILL.md files (slower, individual skills)

Search all 316+ SKILL.md files by name via the GitHub tree API:

```bash
curl -sL "https://api.github.com/repos/davepoon/buildwithclaude/git/trees/main?recursive=1" | python -c "
import sys, json
query = '<KEYWORD>'.lower()
data = json.load(sys.stdin)
matches = [t['path'] for t in data.get('tree', []) if 'SKILL.md' in t['path'] and query in t['path'].lower()]
for m in sorted(matches):
    print(m)
print(f'--- {len(matches)} matching skill files ---')
"
```

### Method 3: Full-text search across SKILL.md frontmatter

To search by skill description (not just filename), fetch the YAML frontmatter from matching files:

```bash
# First get matching file paths from Method 2, then:
curl -sL "https://raw.githubusercontent.com/davepoon/buildwithclaude/main/<path>/SKILL.md" | head -6
```

### Method 4: Category browsing

List all unique categories and their plugins:

```bash
curl -sL "https://raw.githubusercontent.com/davepoon/buildwithclaude/main/.claude-plugin/marketplace.json" | python -c "
import sys, json
from collections import defaultdict
data = json.load(sys.stdin)
cats = defaultdict(list)
for p in data.get('plugins', []):
    cats[p.get('category', 'uncategorized')].append(p['name'])
for cat, plugins in sorted(cats.items()):
    print(f'\n## {cat.upper()} ({len(plugins)} plugins)')
    for name in plugins:
        print(f'  - {name}')
"
```

## Installation

Once you find a skill you want, install it via the Claude Code plugin system:

```bash
claude plugins install <plugin-name>
```

Or manually add the skill to `~/.claude/skills/<skill-name>/SKILL.md`.

## Tips

- Start with **Method 1** for broad plugin searches (fast, covers descriptions and keywords)
- Use **Method 2** to locate specific skill files by name
- Combine methods: find a plugin via Method 1, then explore its skills via Method 2
- The `all-skills` plugin bundles 31 general-purpose skills (pdf, xlsx, docx, pptx, etc.)
- Domain-specific plugins (e.g., `agents-blockchain-web3`, `commands-game-development`) live in topic directories under `plugins/`
