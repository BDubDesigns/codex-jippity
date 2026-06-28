# Jippity — Agent Guide

## What this is

A Linux desktop assistant that wraps [Codex CLI](https://github.com/openai/codex). Press a hotkey → (optional screenshot) → type prompt → Codex answers. Shell scripts, no build system or language runtime.

## Current state

**Phases 0–4.6 implemented.** Code exists, tested on this machine.

| Script | Purpose |
|--------|---------|
| `jippity` | Shared core: `jippity --mode <region\|screen\|window\|quick>` · `jippity --history` |
| `jippity-window` | Wrapper → `jippity --mode window` |
| `jippity-screen` | Wrapper → `jippity --mode screen` |
| `jippity-region` | Wrapper → `jippity --mode region` |
| `jippity-quick` | Wrapper → `jippity --mode quick` |
| `jippity-prompt` | PyQt6 helper: prompt input + continue-thread checkbox dialog |
| `jippity-history` | PyQt6 helper: browse/search/delete threads, set active thread |
| `jippity-setup` | Create dirs, print KDE hotkey instructions |

## Key design facts

- **Core principle:** thin UX layer over `codex` CLI. Jippity owns hotkeys, screenshots, prompt input, output display. Codex owns model, reasoning, auth.
- **Target platform:** Linux + KDE Plasma + Wayland + CachyOS/Arch + fish shell.
- **External deps:** `codex`, `spectacle`, `kdialog`, `jq`, standard Unix tools, KDE global shortcuts.
- **Config / state:** `~/.config/jippity/state` (THREAD_ID, LAST_MODE, CONTINUE_DEFAULT)
- **History:** `~/.local/share/jippity/` with `screenshots/`, `responses/`, `logs/`, `history.jsonl`

## Key design decisions

- **Shared core** — `jippity --mode <mode>`. Four wrappers are one-liner `exec` calls.
- **Clean output** — `codex exec -o <file>` writes only the last message, no metadata header.
- **`--ephemeral`** — all `codex exec` calls use `--ephemeral` to avoid polluting codex's session store with one-off questions.
- **Local thread resume** — instead of `codex exec resume`, reconstruct conversation history from local `history.jsonl` and prepend to the new prompt. More reliable, no dependency on codex session store, works even if codex clears sessions.
- **Combined prompt dialog** — uses a tiny PyQt6 helper (`jippity-prompt`) if available (input + continue-thread checkbox in one native Qt dialog), falls back to `kdialog --inputbox` + `kdialog --yesno`. No separate toggle/reset flow — checkbox is sticky across runs.
- **History viewer** — `jippity --history` launches a PyQt6 window (`jippity-history`) listing threads (most recent first), full transcript on selection, search across prompts+responses, multi-select delete (also removes screenshot files), and "Set as Active Thread" (writes THREAD_ID + CONTINUE_DEFAULT=true so next prompt auto-continues).
- **JSONL storage** — entries are written via `jq -nc` (compact, one per line). The viewer's parser is tolerant of legacy pretty-printed entries and migrates them to compact form on the first delete.
- **Dynamic dialog sizing** — `fold -w 80` for visual line estimate, `height = lines × 22px + 100px`, clamped 120–800px.
- **Spectacle noise suppressed** — stderr to `/dev/null`.
- **Notification** — `kdialog --passivepopup` after each response.
- **No streaming** — blocks for full response.

## Development roadmap

| Phase | What | Status |
|-------|------|--------|
| 0 | Manual validation: `codex -i`, `spectacle` CLI, `kdialog` | Done |
| 1 | Four standalone scripts | Done |
| 2 | Shared core: `jippity --mode <mode>` | Done |
| 3 | Session resume via local history reconstruction | Done |
| 4 | History storage (prompt, response, screenshot, timestamp) | Done |
| 4.5 | History viewer (`jippity --history`) | Done |
| 4.6 | Active-thread visibility in history viewer | Done |
| 5 | *(folded into Phase 7)* | — |
| 6 | Voice input | Future |
| 7 | Rich GUI + tray (Tauri/Qt/GTK/Electron) | Future |

## Hotkeys (not yet bound)

| Key | Command | Action |
|-----|---------|--------|
| Super+S | `jippity --mode region` | Select region → screenshot → prompt → Codex |
| Super+W | `jippity --mode screen` | Full screen → prompt → Codex |
| Super+A | `jippity --mode window` | Active window → prompt → Codex |
| Super+Q | `jippity --mode quick` | Prompt only → Codex |
| Super+H | `jippity --history` | Browse/search/delete threads, set active |

## Error handling

Show user-readable popups for: missing deps, cancelled capture, empty prompt, Codex non-zero exit, timeout.

## Implementation philosophy

"Start tiny. Prefer boring Linux tools before building custom infrastructure." Avoid agent-framework complexity until the workflow proves it deserves it.
