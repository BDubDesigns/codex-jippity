# Jippity

A lightweight Linux desktop assistant that wraps the [Codex CLI](https://github.com/openai/codex). Press a hotkey → (optional screenshot) → type prompt → Codex answers. Pure shell + Python, no build system, no daemon.

## What it does

Press a hotkey, optionally attach a screenshot of your screen/active window/selected region, type a prompt, and Codex answers in a popup window. Threads persist locally — continue a previous conversation, browse past threads, set an old thread as active, search and delete. Optional hold-to-talk voice input via Whisper.

## Status

Phases 0–4.6 + voice input (Phase 6) implemented and tested on CachyOS / KDE Plasma / Wayland. Rich GUI + tray (Phase 7) is the only remaining planned work.

| Area | Status |
|------|--------|
| Hotkey → screenshot → prompt → Codex | Done |
| Session resume via local history reconstruction | Done |
| History storage (prompts, responses, screenshots, timestamps) | Done |
| History viewer (browse, search, delete, set active) | Done |
| Active-thread visibility in history viewer | Done |
| Voice input (hold-to-talk via whisper.cpp) | Done |
| Rich GUI + tray | Planned (Phase 7) |

## Install

### Required (already in your KDE Plasma install)

- `codex` (from OpenAI or your package manager)
- `spectacle`, `kdialog`, `jq`, `parecord`
- Standard Unix tools
- Python 3 with PyQt6 (`python-pyqt6` — shipped with KDE Plasma)

### Optional: voice input

```bash
paru -S whisper.cpp whisper.cpp-model-small.en
```

Then enable voice:

```bash
./jippity --voice
```

## Setup

```bash
./jippity-setup
```

Creates config/state directories and prints KDE global-shortcut binding instructions.

## Hotkeys

| Key | Command | Action |
|-----|---------|--------|
| Super+S | `jippity --mode region` | Select region → screenshot → prompt → Codex |
| Super+W | `jippity --mode screen` | Full screen → prompt → Codex |
| Super+A | `jippity --mode window` | Active window → prompt → Codex |
| Super+Q | `jippity --mode quick` | Prompt only → Codex |
| Super+H | `jippity --history` | Browse/search/delete threads, set active |
| Super+V | `jippity --voice` | Toggle voice input on/off |

Bind them in KDE System Settings → Shortcuts → Custom Shortcuts (point each at the full path of the `jippity` script).

## Continue-thread flow

- When a thread exists, the prompt dialog shows a "Continue previous thread" checkbox.
- Default: unchecked (one-off question). Sticky: your last checkbox choice is remembered for next time.
- Check it to send prior conversation context with your new prompt.
- Uncheck it to start a fresh thread.

## History viewer (Super+H)

- Lists threads (most recent first) with exchange count and timestamp.
- Active thread is marked with `▸` prefix, bold, and a status bar at top.
- Click a thread to read the full transcript.
- Search across prompts and responses.
- Multi-select threads (Ctrl-click) and Delete to remove them and their screenshots.
- "Set as Active Thread" makes the chosen thread active and pre-checks the continue checkbox for the next prompt.

## Voice input (hold-to-talk)

When `VOICE_ENABLED=true` in `~/.config/jippity/state` and `whisper-cli` + a model file are installed, `jippity-prompt` adds a "Hold to Talk" button and listens for Alt-hold. Both call the same record/transcribe pair:

1. `parecord` writes 16 kHz mono WAV to a temp file
2. On release, `whisper-cli -nt --no-timestamps -l en` transcribes the recording
3. Result is inserted at the cursor with a trailing space — no auto-submit, you can edit before pressing Enter

Off by default. `jippity --voice` toggles it on or off and persists the choice in `~/.config/jippity/state`.

## Scripts

| Script | Purpose |
|--------|---------|
| `jippity` | Shared core: `jippity --mode <region\|screen\|window\|quick>` · `jippity --history` · `jippity --voice` |
| `jippity-window` | Wrapper → `jippity --mode window` |
| `jippity-screen` | Wrapper → `jippity --mode screen` |
| `jippity-region` | Wrapper → `jippity --mode region` |
| `jippity-quick` | Wrapper → `jippity --mode quick` |
| `jippity-prompt` | PyQt6 helper: prompt input + continue-thread checkbox + (optional) hold-to-talk voice |
| `jippity-history` | PyQt6 helper: browse/search/delete threads, set active thread |
| `jippity-setup` | Create dirs, print KDE hotkey instructions |

## How it works

- Jippity owns hotkeys, screenshots, prompt input, output display, history storage, and voice capture.
- Codex owns the model, reasoning, and auth.
- All `codex exec` calls use `--ephemeral` to avoid polluting codex's session store.
- Thread continuity is handled locally: Jippity reconstructs prior conversation from `history.jsonl` and prepends it to the new prompt. No dependency on codex's session store — works even if codex clears sessions.
- History is stored as JSONL under `~/.local/share/jippity/` (`screenshots/`, `responses/`, `logs/`, `history.jsonl`).
- State lives at `~/.config/jippity/state` (`THREAD_ID`, `LAST_MODE`, `CONTINUE_DEFAULT`, `VOICE_ENABLED`).

## Implementation philosophy

Start tiny. Prefer boring Linux tools before building custom infrastructure. Avoid agent-framework complexity until the workflow proves it deserves it.

## License

MIT — see `LICENSE` if present.

## Repo

https://github.com/BDubDesigns/codex-jippity