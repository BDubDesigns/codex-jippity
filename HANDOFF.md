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
- `jippity-setup` — creates directories, prints KDE hotkey binding instructions
- `jippity-prompt` — PyQt6 helper for the prompt dialog (input + continue-thread checkbox)
- `jippity-history` — PyQt6 helper for the history viewer (`jippity --history`)

Toolbar removed:
- `jippity-toggle` / `jippity-reset` — deleted. The continue-thread checkbox replaced toggle; reset is no longer a separate script.

### Key design decisions (already built)

- **Shared core refactored.** `jippity --mode <mode>` handles all modes; wrappers are one-liner `exec` calls.
- **Clean output via `-o` flag.** `codex exec -o <file>` writes only the final response, no metadata header.
- **Dynamic dialog sizing.** `fold -w 80` estimates visual wrapped lines; height = (lines × 22px + 100px), clamped 120–800px.
- **Persistent storage.** Screenshots, responses, logs under `~/.local/share/jippity/`. History appended to `history.jsonl` (JSONL: timestamp, mode, prompt, responseFile, imageFile).
- **State file at `~/.config/jippity/state`.** Tracks `THREAD_ID`, `LAST_MODE`, `CONTINUE_DEFAULT` (sticky checkbox state). No persistent mode toggle — continue decision is made per-query via checkbox.
- **Spectacle noise suppressed.** Stderr redirected to `/dev/null` to hide Tesseract library warnings.
- **Notification popup.** `kdialog --passivepopup "Jippity response ready" 3` after each completion.
- **No streaming.** Blocks for full response. Streaming possible later.

### What was validated

- `spectacle -a`, `-f`, `-r` with `-b -n -o` — screenshot capture from CLI
- `codex exec -i <image> -o <file> -- <prompt>` — one-shot non-interactive with image
- `codex exec resume --last -i <image> -o <file> -- <prompt>` — session continuation (alternative approach, not used)
- `kdialog --inputbox`, `--textbox`, `--passivepopup` — all dialog types work
- `jippity-prompt` (PyQt6 helper) — combined input + continue-thread checkbox in one native Qt dialog
- `jippity-history` (PyQt6 helper) — thread list with full transcript, search, multi-select delete (also removes screenshots), and "Set as Active Thread" (writes THREAD_ID + CONTINUE_DEFAULT=true)
- Thread reconstruction from `history.jsonl` — match entries by THREAD_ID, format as conversation block, prepend to prompt

### What didn't work

- **Always-on-top for response window.** Tried KWin scripting via qdbus6. Script loaded without errors but had no visible effect on Wayland. Deferred — a future tray app could focus the response window instead.

## Session Resume Design (Phase 3 — planned)

### Rejected approach

Initial implementation used `codex exec resume <session_id>` to continue threads via codex's session store. Problems:
- Session IDs conflicted with OpenCode sessions (same codex data dir)
- `codex exec resume` behavior with specific UUIDs was unreliable
- One-off jippity questions polluted codex's session browser
- Brittle — breaks if codex changes session storage format

### Current approach: local history reconstruction (implemented)

All `codex exec` calls use `--ephemeral`. Thread continuity is handled locally:

1. **State file** stores `THREAD_ID` (UUID Jippity generates), `LAST_MODE`, `CONTINUE_DEFAULT` (sticky checkbox state).
2. **History file** (`history.jsonl`) stores every exchange with its `THREAD_ID`, prompt, response, screenshot path, timestamp.
3. Continue decision is made **per-query** via:
   - `jippity-prompt` PyQt6 helper (preferred — single dialog with prompt + checkbox, checkbox state is sticky)
   - `kdialog --yesno` fallback (and `kdialog --inputbox` for prompt)
4. If continued: read all history entries with the same `THREAD_ID`, format as conversation block, prepend to the new prompt.
5. Send assembled context to `codex exec --ephemeral -o <file>`.
6. Save the new exchange to `history.jsonl`.
7. Unchecking the checkbox starts a fresh thread with a new `THREAD_ID`.

Benefits:
- Zero dependency on codex session store. Works even if codex clears sessions.
- No pollution of codex's session browser.
- Full control over context window.
- Resilient to codex updates.
- No persistent mode toggle — less confusing UX.

## Directly Next

- **Bind KDE global shortcuts.** Super+S → `jippity --mode region`, etc. See `jippity-setup` output. Super+H → `jippity --history`.
- **Tray app (Phase 5).** System tray with quick action buttons, recent history access.

## Longer-Term Vision (Phase 6–7)

| Phase | Feature |
|-------|---------|
| 6 | Voice input (off by default, toggleable) |
| 7 | Rich GUI — Tauri, Qt, or GTK frontend wrapping the proven core |

## Repo

https://github.com/BDubDesigns/codex-jippity
