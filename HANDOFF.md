# Jippity — Design Handoff

## What Exists

Four standalone shell scripts implementing the Phase 1 MVP:

| Script | What it does |
|--------|-------------|
| `jippity-window` | Captures active window → prompts → sends to Codex → displays answer |
| `jippity-screen` | Captures full screen → same pipeline |
| `jippity-region` | Opens region selector → same pipeline |
| `jippity-quick` | Text prompt only, no screenshot |

All four work end-to-end and have been tested on this machine.

### Key design decisions (already made)

- **Scripts are standalone.** No shared core yet. Each script is a self-contained bash file. Phase 2 will refactor into `jippity --mode <mode>`.
- **Output via `-o` flag.** Codex CLI's `--output-last-message <file>` writes only the clean final response, dodging the noisy metadata header that normally wraps the conversation.
- **Dynamic dialog sizing.** The kdialog textbox height is calculated from the response line count (22px per line, clamped 200–800px). No fixed window size.
- **Temp-only storage.** Responses and screenshots live in `/tmp/jippity/` and are wiped on reboot. Persistent history is deferred to Phase 4.
- **No streaming.** MVP uses `codex exec` which blocks until the full response is ready. Streaming is possible later but wasn't needed yet.

### What was validated

- `spectacle -a -b -n -o` — active window capture from CLI
- `spectacle -f`, `-r` — full screen and region capture
- `codex exec -i <image> -o <file> -- <prompt>` — non-interactive with image
- `kdialog --inputbox` and `kdialog --textbox` — both work in this KDE/Wayland environment

### What didn't work

- **Always-on-top for response window.** Tried KWin scripting via qdbus6 (`workspace.windowList()`, `keepAbove` property). Script loaded without errors but had no visible effect on Wayland. Deferred — a future tray app could focus the response window on click instead, which is cleaner UX.

## Directly Next (Phase 2)

- **Refactor into shared core.** Merge the four scripts into `jippity --mode <region|screen|window|quick>`. The four files become thin wrappers that call the core. This eliminates duplication of the temp dir creation, prompt loop, and output display logic.
- **Bind to KDE global shortcuts.** Configure Super+S → `jippity-region`, Super+W → `jippity-screen`, Super+A → `jippity-window`, Super+Q → `jippity-quick` in KDE System Settings > Shortcuts > Custom Shortcuts.
- **Optional: quiet the Tesseract warnings.** Spectacle logs "unable to load Tesseract" on every run — non-fatal but noisy. Can suppress with stderr redirection if desired.

## Short-Term (Phase 3–4)

| Phase | Feature |
|-------|---------|
| 3 | Session resume via `codex --resume <session_id>`, state file at `~/.config/jippity/state.json`, continue-thread toggle in the prompt dialog |
| 4 | Persistent history at `~/.local/share/jippity/` (screenshots, responses, prompts, timestamps, session IDs) |

## Longer-Term Vision (Phase 5–7)

| Phase | Feature |
|-------|---------|
| 5 | System tray app — quick action buttons, session toggle, recent history access |
| 6 | Voice input (off by default, toggleable) |
| 7 | Rich GUI — Tauri, Qt, or GTK frontend wrapping the proven core |

The guiding principle remains: avoid agent-framework complexity until the basic loop proves it deserves it.

## Repo

https://github.com/BDubDesigns/codex-jippity
