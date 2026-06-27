# Jippity — Design Handoff

## What Exists

Shared core via `jippity --mode <region|screen|window|quick>` with four thin wrapper scripts:

| Script | Equivalent |
|--------|------------|
| `jippity-window` | `jippity --mode window` |
| `jippity-screen` | `jippity --mode screen` |
| `jippity-region` | `jippity --mode region` |
| `jippity-quick` | `jippity --mode quick` |

Additional commands:
- `jippity-toggle` — switches between one-shot and continue-thread mode
- `jippity-reset` — clears thread, resets to one-shot mode
- `jippity-setup` — creates directories, prints KDE hotkey binding instructions

### Key design decisions (already built)

- **Shared core refactored.** `jippity --mode <mode>` handles all modes; wrappers are one-liner `exec` calls.
- **Clean output via `-o` flag.** `codex exec --output-last-message <file>` writes only the final response, no metadata header.
- **Dynamic dialog sizing.** `fold -w 80` estimates visual wrapped lines; height = (lines × 22px + 100px), clamped 120–800px.
- **Persistent storage.** Screenshots, responses, logs under `~/.local/share/jippity/`. History appended to `history.jsonl` (JSONL: timestamp, mode, prompt, responseFile, imageFile).
- **State file at `~/.config/jippity/state`.** Tracks `THREAD_ID`, `THREAD_MODE` (one-shot/continue), `LAST_MODE`.
- **Spectacle noise suppressed.** Stderr redirected to `/dev/null` to hide Tesseract library warnings.
- **Notification popup.** `kdialog --passivepopup "Jippity response ready" 3` after each completion.
- **No streaming.** Blocks for full response. Streaming possible later.

### What was validated

- `spectacle -a`, `-f`, `-r` with `-b -n -o` — screenshot capture from CLI
- `codex exec -i <image> -o <file> -- <prompt>` — one-shot non-interactive with image
- `codex exec resume --last -i <image> -o <file> -- <prompt>` — session continuation (alternative approach, not used)
- `kdialog --inputbox`, `--textbox`, `--passivepopup` — all dialog types work
- State file round-trip: toggle writes, source reads, reset clears

### What didn't work

- **Always-on-top for response window.** Tried KWin scripting via qdbus6. Script loaded without errors but had no visible effect on Wayland. Deferred — a future tray app could focus the response window instead.

## Session Resume Design (Phase 3 — planned)

### Rejected approach

Initial implementation used `codex exec resume <session_id>` to continue threads via codex's session store. Problems:
- Session IDs conflicted with OpenCode sessions (same codex data dir)
- `codex exec resume` behavior with specific UUIDs was unreliable
- One-off jippity questions polluted codex's session browser
- Brittle — breaks if codex changes session storage format

### Current plan: local history reconstruction

All `codex exec` calls use `--ephemeral` to avoid polluting codex's session store. Thread continuity is handled locally:

1. **State file** stores a `THREAD_ID` (UUID Jippity generates) and `THREAD_MODE` (one-shot or continue).
2. **History file** (`history.jsonl`) stores every exchange with its `THREAD_ID`, prompt, response, screenshot path, timestamp.
3. On a **continue** run, read all history entries with the same `THREAD_ID`, format them as a plain-text conversation block, and prepend to the new prompt:

```
[Previous conversation]
User: remember the cat hunts at midnight
Jippity: I'll remember that. The cat hunts at midnight.
[New message]
User: what did I send last?
```

4. Send the assembled context + new prompt to `codex exec --ephemeral -o <file>`.
5. Save the new exchange to `history.jsonl` with the same `THREAD_ID`.
6. A **reset** generates a new `THREAD_ID` and switches back to one-shot mode.

Benefits:
- Zero dependency on codex session store. Works even if codex clears sessions.
- No pollution of codex's session browser.
- Full control over context window (can truncate, summarize, or prune old history).
- Resilient to codex updates.
- Same token cost — the model sees the same conversation either way.

## Directly Next

- **Implement local history reconstruction** for session resume (Phase 3).
- **Bind KDE global shortcuts.** Super+S → `jippity --mode region`, etc. See `jippity-setup` output.
- **Tray app (Phase 5).** System tray with quick action buttons, session toggle, recent history access.

## Longer-Term Vision (Phase 6–7)

| Phase | Feature |
|-------|---------|
| 6 | Voice input (off by default, toggleable) |
| 7 | Rich GUI — Tauri, Qt, or GTK frontend wrapping the proven core |

## Repo

https://github.com/BDubDesigns/codex-jippity
