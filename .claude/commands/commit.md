---
description: Stage all changes, craft a clean commit + PR, and push to GitHub.
argument-hint: [optional: short description to guide the PR title]
---

You are acting as a senior engineer doing a clean, professional commit and PR. Follow every step below exactly.

## Step 1 — Understand the current state

Run these in parallel:
- `git status` — see what is staged/unstaged/untracked
- `git diff HEAD` — see all changes (staged + unstaged) in full
- `git log --oneline -10` — see recent commit history to match style
- `git branch --show-current` — confirm current branch name

## Step 2 — Agent consultation

Before writing anything, briefly consult relevant agents from AGENTS.md:

- **DataEngineer**: Are any of the changed files risky to commit as-is? (formatting, dead code, debug prints)
- **QAGovernance**: Are there missing tests for any new models or changed logic?
- **ProjectManager**: Is this a logical, self-contained unit of work? Should anything be excluded from this commit?

If any agent raises a blocker, fix it before proceeding. Surface the consultation result as a short bullet list.

## Step 3 — Stage files

Stage all changed tracked files. Use specific file paths — do NOT use `git add .` or `git add -A` unless every untracked file should be included (check `git status` first for anything that should be excluded like `.env`, secrets, large binaries, or generated files).

```bash
git add <specific files>
```

Never stage:
- `.env` or any secrets file
- `target/` or `dbt_packages/`
- `.venv/` or `.venv311/`
- Any `*.json` key files

## Step 4 — Write the commit message

Analyze all staged changes and write a commit message following this format:

```
<type>(<scope>): <short imperative summary under 72 chars>

<body: 2-4 bullet points explaining WHAT changed and WHY, not HOW>
-
-

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `ci`, `style`

Scope examples: `bi`, `gold`, `silver`, `bronze`, `ci`, `infra`, `config`

Rules:
- Imperative mood ("add", "fix", "remove" — not "added", "fixed")
- No period at end of subject line
- Body explains motivation, not mechanics
- If $ARGUMENTS was provided, use it to guide the title

## Step 5 — Commit

```bash
git commit -m "$(cat <<'EOF'
<your message here>
EOF
)"
```

## Step 6 — Push branch to origin

```bash
git push -u origin HEAD
```

If the push is rejected (non-fast-forward), diagnose why before doing anything destructive. Do NOT force push unless the user explicitly says to.

## Step 7 — Create the Pull Request

Use `gh pr create` with this structure:

```bash
gh pr create \
  --title "<same as commit subject line>" \
  --base master \
  --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>
- <bullet 3>

## Changes
| File/Area | What changed |
|---|---|
| `path/to/file` | description |

## Test plan
- [ ] dbt build passes (`dbt build --target dev`)
- [ ] No new ERRORs (WARNs on public data are expected)
- [ ] Dashboard loads without errors (if bi/ changed)

## Agent sign-off
- DataEngineer: ✓
- QAGovernance: ✓

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Step 8 — Report back

Print a short summary:
- Branch name
- Commit SHA (first 7 chars)
- PR URL
- Any agent concerns that were noted but not blocking
