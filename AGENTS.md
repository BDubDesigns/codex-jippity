# Jippity — Agent Guide

## What this is

A Linux desktop assistant that wraps [Codex CLI](https://github.com/openai/codex). Press a hotkey → (optional screenshot) → type prompt → Codex answers. MVP is shell scripts, no build system or language runtime yet.

## Current state

**Pre-implementation.** Only source file is `spec.md` — the design document. No code, no build tooling, no CI, no tests. Git repo is empty (zero commits). Implementation has not started.

## Key design facts

- **Core principle:** thin UX layer over `codex` CLI. Jippity owns hotkeys, screenshots, prompt input, output display. Codex owns model, reasoning, sessions, auth.
- **MVP:** four standalone scripts — `jippity-region`, `jippity-screen`, `jippity-window`, `jippity-quick`.
- **Phase 2:** refactor into `jippity --mode <region|screen|window|quick>`.
- **Target platform:** Linux + KDE Plasma + Wayland + CachyOS/Arch + fish shell.
- **External deps (MVP):** `codex`, `spectacle`, `kdialog`, standard Unix tools, KDE global shortcuts.
- **Config:** `~/.config/jippity/config.json`
- **State (phase 3+):** `~/.config/jippity/state.json`
- **History (phase 4+):** `~/.local/share/jippity/`

## Development roadmap

| Phase | What |
|-------|------|
| 0 | Manual validation: `codex -i`, `spectacle` CLI, `kdialog` input/output |
| 1 | Four standalone scripts (one-shot, no shared core) |
| 2 | Shared core: `jippity --mode <mode>` |
| 3 | Session resume via `codex --resume <session_id>`, state file, continue-thread toggle |
| 4 | History storage (prompt, response, screenshot path, timestamp) |
| 5 | Tray app |
| 6 | Voice input |
| 7 | Rich GUI (Tauri/Qt/GTK/Electron) |

## MVP hotkeys

| Key | Command | Action |
|-----|---------|--------|
| Super+S | `jippity-region` | Select region → screenshot → prompt → Codex |
| Super+W | `jippity-screen` | Full screen → prompt → Codex |
| Super+A | `jippity-window` | Active window → prompt → Codex |
| Super+Q | `jippity-quick` | Prompt only → Codex |

## MVP output display

Write Codex output to temp file, open with `kdialog --textbox`.

## Error handling

Show user-readable popups (not silent failures) for: missing deps (`codex`, `spectacle`, `kdialog`), cancelled capture, empty prompt, Codex non-zero exit, timeout, missing session ID.

## Implementation philosophy

"Start tiny. Prefer boring Linux tools before building custom infrastructure." Avoid agent-framework complexity until the workflow proves it deserves it.
