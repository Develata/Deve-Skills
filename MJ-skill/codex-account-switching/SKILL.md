---
name: codex-account-switching
description: Multi-account Codex MCP isolation on Claude Desktop and Claude CLI. Use when more than one OpenAI account / API key needs to coexist on the same machine, or when a task must explicitly run on one specific account.
---

# Codex Multi-Account MCP Switching

## When to Use

- Two or more Codex accounts (ChatGPT and/or API key) need to coexist on the same machine
- A task must run on one specific account (rate-limit isolation, billing separation, scoped keys)
- You see "wrong account active" symptoms after `codex login`

## When NOT to Use

- Single-account workflows — keep the original `codex` MCP entry as-is
- Temporary one-off account switches — `CODEX_HOME=<path> codex ...` ad-hoc is fine without this skill

## Core Model

One **`CODEX_HOME` per account**. Each home holds its own `auth.json`, `config.toml`, session cache. Each account is exposed via a **dedicated MCP server name** in both Claude Desktop and Claude CLI, so prompts pick the account by name and never collide.

| Account role | `CODEX_HOME` | MCP server name |
|---|---|---|
| Primary | `~/.codex` | `codex-main` |
| Secondary | `~/.codex-b` | `codex-b` |
| Tertiary | `~/.codex-c` | `codex-c` |

Force `cli_auth_credentials_store="file"` on every instance so credentials stay inside the home dir instead of mixing through the system keychain.

## One-Time Setup

### 1. Create the home dir BEFORE first login

```bash
mkdir -p ~/.codex-b
```

> **Verified-mandatory**: `codex login` aborts with `CODEX_HOME points to "<path>", but that path does not exist` if the home dir is missing. Tested 2026-04-10 against `codex-cli 0.118.0`.

### 2. Login (ChatGPT path)

```bash
CODEX_HOME=~/.codex-b codex -c 'cli_auth_credentials_store="file"' login
# completes in browser
```

### 2'. Login (API key path)

```bash
printenv OPENAI_API_KEY_B | CODEX_HOME=~/.codex-b codex -c 'cli_auth_credentials_store="file"' login --with-api-key
```

Never write API keys directly into Claude config files.

### 3. Verify isolation

```bash
CODEX_HOME=~/.codex   codex -c 'cli_auth_credentials_store="file"' login status
CODEX_HOME=~/.codex-b codex -c 'cli_auth_credentials_store="file"' login status
ls -la ~/.codex/auth.json ~/.codex-b/auth.json
```

Expectations:
- Each home reports an independent login state
- Each `auth.json` is a real file (not a symlink to the same target)
- Each home contains its own `config.toml` (or empty if not customized)

### 4. Add MCP servers — Claude CLI

```bash
# Locate the codex binary (adapt if installed differently)
CODEX_BIN="$(which codex)"   # e.g. /opt/homebrew/bin/codex on macOS arm64

# Remove the ambiguous bare entry first to prevent accidental fall-through
claude mcp remove codex -s user

# Add explicit per-account entries
claude mcp add codex-main "$CODEX_BIN" mcp-server -s user -e CODEX_HOME=$HOME/.codex
claude mcp add codex-b    "$CODEX_BIN" mcp-server -s user -e CODEX_HOME=$HOME/.codex-b

# Verify
claude mcp list
claude mcp get codex-main
claude mcp get codex-b
```

All entries should report `✓ Connected`.

### 5. Add MCP servers — Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`. Replace the single `codex` entry with one entry per account:

```json
{
  "mcpServers": {
    "codex-main": {
      "command": "<CODEX_BIN_PATH>",
      "args": ["mcp-server"],
      "env": { "CODEX_HOME": "<HOME_DIR>/.codex" }
    },
    "codex-b": {
      "command": "<CODEX_BIN_PATH>",
      "args": ["mcp-server"],
      "env": { "CODEX_HOME": "<HOME_DIR>/.codex-b" }
    }
  }
}
```

Replace `<CODEX_BIN_PATH>` with the output of `which codex` (e.g., `/opt/homebrew/bin/codex` on macOS arm64) and `<HOME_DIR>` with your home directory (e.g., `/Users/yourname`).

Then **fully restart Claude Desktop** (Quit, not just close window).

> **Assumption-dependent**: Claude Desktop honoring the `env.CODEX_HOME` field is the standard stdio-MCP pattern but cannot be verified without a Desktop restart. After restart, each Codex server should report its own account identity in the first invocation. If a server reports the wrong account, the env injection failed and the entry needs review.

## Per-Task Usage

When dispatching a Codex job, route to a specific MCP server explicitly:

> "Use `codex-b` to investigate the legacy module loader."

Never just say "use codex" once the migration is complete. The ambiguity is what the multi-account isolation exists to eliminate.

## Helper Scripts

The skill is the **source of truth** for these helpers. The user installs them once into a `PATH` directory (commonly `~/.local/bin/` or `~/bin/`), then re-runs the install whenever the skill is updated. This avoids drift between docs and shell while keeping helpers usable as real executables.

### Install (one-time)

```bash
# Pick whichever PATH directory you already use:
echo "$PATH" | tr ':' '\n' | grep -E "$HOME/bin|$HOME/.local/bin"

# Common targets:
#   ~/.local/bin   (already in PATH on most modern setups)
#   ~/bin          (older convention; may need to be added to PATH)
```

Then create the three helper files below in your chosen directory, e.g.:

```bash
INSTALL_DIR="$HOME/.local/bin"   # or "$HOME/bin"
mkdir -p "$INSTALL_DIR"
# (paste each script body to its own file under $INSTALL_DIR)
chmod +x "$INSTALL_DIR/codex-account-login" \
         "$INSTALL_DIR/codex-account-status" \
         "$INSTALL_DIR/codex-account-relogin"
which codex-account-login codex-account-status codex-account-relogin
```

After every edit to the skill that touches the helper sections, repeat the install to refresh the on-disk copies.

### `~/bin/codex-account-login`

```bash
#!/usr/bin/env bash
# Usage: codex-account-login <name>     e.g. codex-account-login b
# Logs into a per-account CODEX_HOME using file-based credential storage.
set -euo pipefail
name="${1:-}"
if [[ -z "$name" ]]; then
  echo "usage: codex-account-login <name>" >&2; exit 2
fi
if [[ "$name" == "main" ]]; then
  home="$HOME/.codex"
else
  home="$HOME/.codex-$name"
fi
mkdir -p "$home"
echo "==> CODEX_HOME=$home"
CODEX_HOME="$home" codex -c 'cli_auth_credentials_store="file"' login
echo "==> Verifying..."
CODEX_HOME="$home" codex -c 'cli_auth_credentials_store="file"' login status
ls -la "$home/auth.json" 2>/dev/null || echo "WARNING: $home/auth.json missing"
```

### `~/bin/codex-account-status`

```bash
#!/usr/bin/env bash
# Usage: codex-account-status
# Reports login state for every ~/.codex* home dir.
set -uo pipefail
shopt -s nullglob
for h in "$HOME/.codex" "$HOME"/.codex-*; do
  [[ -d "$h" ]] || continue
  printf '%-30s ' "$h"
  CODEX_HOME="$h" codex -c 'cli_auth_credentials_store="file"' login status 2>&1 || echo "(error)"
done
```

### `~/bin/codex-account-relogin`

```bash
#!/usr/bin/env bash
# Usage: codex-account-relogin <name>
# Logs out then logs into a single account home without touching others.
set -euo pipefail
name="${1:-}"
if [[ -z "$name" ]]; then
  echo "usage: codex-account-relogin <name>" >&2; exit 2
fi
if [[ "$name" == "main" ]]; then
  home="$HOME/.codex"
else
  home="$HOME/.codex-$name"
fi
mkdir -p "$home"
CODEX_HOME="$home" codex -c 'cli_auth_credentials_store="file"' logout || true
CODEX_HOME="$home" codex -c 'cli_auth_credentials_store="file"' login
CODEX_HOME="$home" codex -c 'cli_auth_credentials_store="file"' login status
```

### Integrity check after install

```bash
ls -la ~/bin/codex-account-login ~/bin/codex-account-status ~/bin/codex-account-relogin
file ~/bin/codex-account-* | grep -i 'shell script'
codex-account-status
```

## Verification Discipline (per dual-agent-original-request-review)

This skill follows the verification discipline defined in the dual-agent-original-request-review skill. Specifically:

- **Verified facts** (tested 2026-04-10 against `codex-cli 0.118.0` on macOS arm64):
  - `cli_auth_credentials_store="file"` is accepted as a valid `-c` config override
  - `CODEX_HOME=<path>` env var isolates login state across home dirs
  - `CODEX_HOME` path must exist before `codex login` runs (otherwise hard error)
  - `claude mcp add -s user` supports per-server `-e KEY=VALUE` env injection
  - `claude mcp list` and `claude mcp get <name>` report MCP server connection state
  - Codex binary at `/opt/homebrew/bin/codex` is the cask install symlink target

- **Assumption-dependent**:
  - `cli_auth_credentials_store="file"` runtime semantics — verified the flag is accepted, but did NOT verify it actually bypasses the system keychain on a fresh login (the test machine already had `~/.codex/auth.json`). Verify on first new-account login by checking `<CODEX_HOME>/auth.json` was created and the OS did not prompt for keychain access.
  - Claude Desktop honoring `env.CODEX_HOME` — standard stdio-MCP pattern; verify after Desktop restart.

- **Failure mode**: if any of the above breaks, fall back to a single-account `codex` entry and document the failure in this skill's notes section.

## Failure Modes and Recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| `CODEX_HOME points to ... but that path does not exist` | Forgot `mkdir -p` | `mkdir -p $CODEX_HOME` and retry |
| Wrong account replies via MCP | env injection failed in Claude config | `claude mcp get codex-<name>` should show `CODEX_HOME` env; if missing, re-add with `-e CODEX_HOME=...` |
| Stale Desktop after JSON edit | Desktop process not fully restarted | Quit Desktop entirely (`Cmd+Q`), wait, relaunch |
| OS keychain prompts during login | `cli_auth_credentials_store="file"` flag was not applied | Confirm the `-c` flag is on the command (helper scripts always include it) |
| Two homes share the same credentials | One home is a symlink instead of a real dir | `ls -la ~/.codex* /` and replace symlinks with real dirs |
| `claude mcp list` still shows bare `codex` after migration | Entry was project-scoped, not user-scoped | `claude mcp remove codex -s project` or `-s local` |

## Account Removal

To remove a secondary account cleanly:

```bash
# 1. Remove the MCP entry
claude mcp remove codex-b -s user

# 2. (Optional) Delete the home directory
rm -rf ~/.codex-b

# 3. If using Claude Desktop, remove the entry from claude_desktop_config.json and restart
```

Do not remove the primary account (`codex-main`) unless you are migrating back to single-account mode. In that case, re-add a bare `codex` MCP entry pointing to `~/.codex`.

## Codex CLI Upgrade Notes

When upgrading Codex CLI (e.g., `brew upgrade codex`):
- **Account data survives**: `auth.json` and `config.toml` live in `CODEX_HOME` dirs, not the binary install path.
- **Binary path may change**: after upgrade, verify `which codex` still matches the path in your MCP server configs. If it changed, update the MCP entries.
- **Auth format changes**: rare but possible. If a login starts failing after upgrade, run `codex-account-relogin <name>` to refresh credentials.
- **Test after upgrade**: `codex-account-status` should report all accounts as logged in.
- **Server-side default model drift can force a CLI upgrade**: ChatGPT accounts may silently switch default to a newer model (e.g., `gpt-5.5`) that requires CLI ≥ 0.122. Symptom: codex-main returns `model 'gpt-5.5' requires a newer version of Codex`. Account tier (Pro/Team/etc.) is irrelevant — the blocker is CLI version, not subscription.
- **MCP server pins the old binary across `brew upgrade`**: Claude Code spawns codex MCP servers at startup and keeps the subprocess alive. `brew upgrade --cask codex` updates `which codex` immediately, but the running MCP still uses the old path. **Claude Code full restart required** before the new binary takes effect; `/mcp` reconnect alone is insufficient. Verify with `mcp__codex-main__codex` returning a normal response instead of the version error.
- **ChatGPT-account model overrides are constrained**: on a ChatGPT-authenticated MCP, passing `model: "gpt-5.2-codex"` returns `not supported when using Codex with a ChatGPT account`. Do not fall back to codex-specialized model IDs. The only fallbacks are (a) upgrade CLI, (b) switch to an API-key MCP (e.g., `codex-b`) that accepts the full model whitelist.

## Anti-Patterns

- Keeping a bare `codex` MCP alongside `codex-main` "as backup" — accidental use defeats the isolation
- Storing API keys directly in `claude_desktop_config.json` — use `codex login --with-api-key` from a shell with the env var set
- Relying on system keychain when `cli_auth_credentials_store="file"` is set — if you see the OS asking for keychain access, the file-store flag was not applied to that invocation
- Sharing one helper for "all accounts" without naming them — accidental fall-through to `~/.codex` is the most common bug
- Claiming an account is configured before verifying `<CODEX_HOME>/auth.json` exists post-login
- Editing the helper scripts in `~/bin/` directly without updating this skill — drift makes the skill misleading; always edit the skill first, then reinstall

## Skill Location Note

This skill exists in two locations:
- **Project-scoped**: `.claude/skills/codex-account-switching/SKILL.md` (committed with the project)
- **Public backup**: `Develata/Deve-Skills` repo under `MJ-skill/codex-account-switching/`

To use it globally across all projects, copy to `~/.claude/skills/codex-account-switching/` (peer to the `superpowers/` framework). Keep the project-level copy as the primary editing target; sync to other locations after changes.
