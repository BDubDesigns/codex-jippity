# Jippity — Agent Guide

## What this is

A Linux desktop assistant that wraps [Codex CLI](https://github.com/openai/codex). Press a hotkey → (optional screenshot) → type prompt → Codex answers. Shell scripts, no build system or language runtime.

## Current state

**Phases 0–4.6 + voice input (Phase 6) + tools implemented.** Code exists, tested on this machine.

| Script | Purpose |
|--------|---------|
| `jippity` | Shared core: `jippity --mode <region\|screen\|window\|quick>` · `jippity --history` · `jippity --voice` |
| `jippity-window` | Wrapper → `jippity --mode window` |
| `jippity-screen` | Wrapper → `jippity --mode screen` |
| `jippity-region` | Wrapper → `jippity --mode region` |
| `jippity-quick` | Wrapper → `jippity --mode quick` |
| `jippity-prompt` | PyQt6 helper: prompt input + continue-thread checkbox dialog + (optional) hold-to-talk voice |
| `jippity-history` | PyQt6 helper: browse/search/delete threads, set active thread |
| `jippity-setup` | Create dirs, print KDE hotkey instructions |
| `jippity-tools` | Scan `tools/` dir, emit tools index block for codex context or JSON for viewers |

## Key design facts

- **Core principle:** thin UX layer over `codex` CLI. Jippity owns hotkeys, screenshots, prompt input, output display. Codex owns model, reasoning, auth.
- **Target platform:** Linux + KDE Plasma + Wayland + CachyOS/Arch + fish shell.
- **External deps:** `codex`, `spectacle`, `kdialog`, `jq`, standard Unix tools, KDE global shortcuts.
- **Config / state:** `~/.config/jippity/state` (THREAD_ID, LAST_MODE, CONTINUE_DEFAULT, VOICE_ENABLED)
- **History:** `~/.local/share/jippity/` with `screenshots/`, `responses/`, `logs/`, `history.jsonl`

## Key design decisions

- **Shared core** — `jippity --mode <mode>`. Four wrappers are one-liner `exec` calls.
- **Clean output** — `codex exec -o <file>` writes only the last message, no metadata header.
- **`--ephemeral`** — all `codex exec` calls use `--ephemeral` to avoid polluting codex's session store with one-off questions.
- **Local thread resume** — instead of `codex exec resume`, reconstruct conversation history from local `history.jsonl` and prepend to the new prompt. More reliable, no dependency on codex session store, works even if codex clears sessions.
- **Combined prompt dialog** — uses a tiny PyQt6 helper (`jippity-prompt`) if available (input + continue-thread checkbox in one native Qt dialog), falls back to `kdialog --inputbox` + `kdialog --yesno`. No separate toggle/reset flow — checkbox is sticky across runs.
- **Voice input (hold-to-talk)** — when `VOICE_ENABLED=true` in state file and `whisper-cli` + a model file are installed, `jippity-prompt` adds a "Hold to Talk" button and listens for Alt-hold. Both call the same `start_recording()` / `stop_and_transcribe()` pair: `parecord` writes 16kHz mono WAV, then `whisper-cli -nt` transcribes and inserts at the cursor (no auto-submit — user can edit first). Off by default, zero-cost fallback if deps are missing.
- **History viewer** — `jippity --history` launches a PyQt6 window (`jippity-history`) listing threads (most recent first), full transcript on selection, search across prompts+responses, multi-select delete (also removes screenshot files), and "Set as Active Thread" (writes THREAD_ID + CONTINUE_DEFAULT=true so next prompt auto-continues).
- **JSONL storage** — entries are written via `jq -nc` (compact, one per line). The viewer's parser is tolerant of legacy pretty-printed entries and migrates them to compact form on the first delete.
- **Dynamic dialog sizing** — `fold -w 80` for visual line estimate, `height = lines × 22px + 100px`, clamped 120–800px.
- **Spectacle noise suppressed** — stderr to `/dev/null`.
- **Notification** — `kdialog --passivepopup` after each response.
- **Tools** — a `tools/` subdirectory in the repo holds tool manifests (small files with `# @tool` front-matter). `jippity-tools` scans this dir and prepends an `[Available jippity tools]` index block to the context sent to codex. Codex can then invoke the tools via its shell. The history viewer's "Tools…" button shows the same index. External tools already in `$PATH` (like `codex-reset`) are documented via stub manifests; bundled tools are real executable scripts placed in `tools/`.

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
| 6 | Voice input | Done |
| 7 | Rich GUI + tray (Tauri/Qt/GTK/Electron) | Future |

## Tools

A `tools/` subdirectory in the repo holds tool manifests — small files with `# @tool` front-matter describing a tool codex can invoke.

| Tool | Status |
|------|--------|
| `codex-reset` | Stub manifest (external — already in `$PATH` on this machine) |

Tool file format:

```
# @tool <name>
# @description <one-line>
# @usage <usage line>            (repeatable)
# @example <example command>     (optional, repeatable)
# @installed-by <external|jippity> [<notes>]
```

`jippity-tools` scans `tools/`, parses the front-matter, and emits either:
- A plain-text `[Available jippity tools]` index block (default) — prepended to codex context
- `--json` — structured JSON list (for the history viewer's "Tools…" button)
- `--list` — one tool name per line

## Hotkeys (not yet bound)

| Key | Command | Action |
|-----|---------|--------|
| Super+S | `jippity --mode region` | Select region → screenshot → prompt → Codex |
| Super+W | `jippity --mode screen` | Full screen → prompt → Codex |
| Super+A | `jippity --mode window` | Active window → prompt → Codex |
| Super+Q | `jippity --mode quick` | Prompt only → Codex |
| Super+H | `jippity --history` | Browse/search/delete threads, set active |
| Super+V | `jippity --voice` | Toggle voice input on/off |

## Error handling

Show user-readable popups for: missing deps, cancelled capture, empty prompt, Codex non-zero exit, timeout.

## Implementation philosophy

"Start tiny. Prefer boring Linux tools before building custom infrastructure." Avoid agent-framework complexity until the workflow proves it deserves it.
