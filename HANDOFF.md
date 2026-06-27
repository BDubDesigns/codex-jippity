# Jippity — Design Handoff

## What Exists

Shared core via `jippity --mode <region|screen|window|quick>` with four thin wrapper scripts:

| Script | Equivalent core command |
|--------|------------------------|
| `jippity-window` | `jippity --mode window` |
| `jippity-screen` | `jippity --mode screen` |
| `jippity-region` | `jippity --mode region` |
| `jippity-quick` | `jippity --mode quick` |

All four work end-to-end and have been tested on this machine.

Additional commands:
- `jippity-toggle` — switches between one-shot and continue-thread mode
- `jippity-reset` — clears session ID, resets to one-shot mode
- `jippity-setup` — creates directories, prints KDE hotkey binding instructions

### Key design decisions (already made)

- **Shared core refactored.** Phase 2 complete. `jippity --mode <mode>` handles all modes; wrappers are one-liner `exec` calls.
- **Output via `-o` flag.** Codex CLI's `--output-last-message <file>` writes only the clean final response, avoiding the noisy metadata header.
- **Dynamic dialog sizing.** Uses `fold -w 80` to estimate visual wrapped lines; height = (lines × 22px + 100px), clamped 120–800px.
- **Persistent storage.** Screenshots → `~/.local/share/jippity/screenshots/`, responses → `.../responses/`, logs → `.../logs/`. History appended to `history.jsonl` (JSONL format).
- **State file at `~/.config/jippity/state`.** Tracks `SESSION_ID`, `SESSION_MODE` (one-shot/continue), `LAST_MODE`. Sourced by bash on startup.
- **Session resume.** When mode is "continue", uses `codex exec resume <session_id> -i <image> -o <outfile> -- <prompt>`. Session ID extracted from logfile after each run.
- **No streaming.** Uses `codex exec` which blocks for full response. Streaming is possible later.
- **Notification popup.** `kdialog --passivepopup "Jippity response ready" 3` after each completion.
- **Suppressed spectacle noise.** Stderr from `spectacle` redirected to `/dev/null` to hide Tesseract library warnings.

### What was validated

- `spectacle -a`, `-f`, `-r` with `-b -n -o` — screenshot capture from CLI
- `codex exec -i <image> -o <file> -- <prompt>` — one-shot non-interactive with image
- `codex exec resume --last -i <image> -o <file> -- <prompt>` — session continuation
- Session ID extraction: `grep -oP 'session id: \K\S+'` from codex log output
- `kdialog --inputbox`, `--textbox`, `--passivepopup` — all dialog types work
- State file round-trip: toggle writes, source reads, reset clears

### What didn't work

- **Always-on-top for response window.** Tried KWin scripting via qdbus6 (`workspace.windowList()`, `keepAbove` property). Script loaded without errors but had no visible effect on Wayland. Deferred — a future tray app could focus the response window on click instead, which is cleaner UX.

## Directly Next

- **Bind KDE global shortcuts.** Super+S → `jippity --mode region`, Super+W → `jippity --mode screen`, Super+A → `jippity --mode window`, Super+Q → `jippity --mode quick`. Optional Super+R → `jippity-reset`, Super+T → `jippity-toggle`. See `jippity-setup` output.
- **Tray app (Phase 5).** System tray with quick action buttons, session toggle, recent history access. Could be a small Python/Qt or C++/Qt app, or a KDE Plasma applet.

## Longer-Term Vision (Phase 6–7)

| Phase | Feature |
|-------|---------|
| 6 | Voice input (off by default, toggleable) |
| 7 | Rich GUI — Tauri, Qt, or GTK frontend wrapping the proven core |

The guiding principle remains: avoid agent-framework complexity until the basic loop proves it deserves it.

## Repo

https://github.com/BDubDesigns/codex-jippity
