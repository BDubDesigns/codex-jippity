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
- `jippity-prompt` (PyQt6 helper) — combined input + continue-thread checkbox in one native Qt dialog. Optional hold-to-talk: `parecord` (PipeWire) writes 16kHz mono WAV, `whisper-cli` transcribes on release and inserts at cursor. Off by default; falls back silently if `VOICE_ENABLED=false` or whisper missing.
- `jippity-history` (PyQt6 helper) — thread list with full transcript, search, multi-select delete (also removes screenshots), and "Set as Active Thread" (writes THREAD_ID + CONTINUE_DEFAULT=true). Tolerates legacy pretty-printed JSONL; migrates to compact JSONL on first delete.
- Thread reconstruction from `history.jsonl` — match entries by THREAD_ID, format as conversation block, prepend to prompt

### What didn't work

- **Always-on-top for response window.** Tried KWin scripting via qdbus6. Script loaded without errors but had no visible effect on Wayland. Deferred — a future tray app (Phase 7) could focus the response window instead.
- **yad as the prompt-dialog tool.** yad's `webkit2gtk-4.1` dep is 133 MiB and the CachyOS v3 mirrors were 404-ing on multiple transitive deps. Replaced with PyQt6 (already installed via KDE Plasma) — zero new deps and a native Qt look.
- **System tray as a standalone Phase 5.** Hotkeys already cover every invocation; the tray would only add at-a-glance status and response-flash. Not worth a dedicated phase. Folded into Phase 7 (rich GUI) where it belongs alongside the larger frontend.

## Session Resume Design (Phase 3 — done)

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

## Voice Input (Phase 6 — done)

Hold-to-talk transcription wired into `jippity-prompt`. No new Python deps; uses `parecord` (PipeWire, already installed) for capture and `whisper-cli` (whisper.cpp, AUR) for transcription.

1. **State file** gains `VOICE_ENABLED` (default false). Persisted across runs in `~/.config/jippity/state`.
2. **`jippity-prompt`** reads voice_enabled (6th CLI arg). When true and `whisper-cli` + model are found, adds a "Hold to Talk" button and installs an app-wide event filter for Alt-hold.
3. Both the on-screen button (`pressed`/`released`) and Alt (`keyPress`/`keyRelease`, non-autorepeat) call the same `start_recording()` / `stop_and_transcribe()` pair.
4. `start_recording()` spawns `parecord --rate=16000 --format=s16ne --channels=1 --file-format=wav <tmp>` so whisper.cpp gets a 16 kHz mono WAV directly. Button turns red and shows "● Recording…" while held.
5. `stop_and_transcribe()` terminates parecord, runs `whisper-cli -m <model> -f <wav> -nt --no-timestamps -l en`, parses stdout, and calls `QLineEdit.insert(transcript + " ")` at the cursor. No auto-submit — user can edit first.
6. Zero-cost fallback: if `VOICE_ENABLED=false` or whisper missing, the dialog is the plain two-row text+checkbox and no audio stack is touched.

**Model lookup** checks `~/.local/share/jippity/models/ggml-small.en.bin` first, then standard whisper.cpp install paths. Default recommendation is `small.en` (~244 MiB, English-only).

**Install:**
```
paru -S whisper.cpp whisper.cpp-model-small.en
```
Then edit `~/.config/jippity/state` and set `VOICE_ENABLED=true`.

If whisper.cpp latency becomes annoying (model load per utterance, ~1–2 s), swap backend to `python-faster-whisper` (AUR) which keeps the model loaded in-process. The `jippity-prompt` voice block is isolated enough to swap the transcribe function without touching callers.

## Directly Next

- **Bind KDE global shortcuts.** Super+S → `jippity --mode region`, etc. See `jippity-setup` output. Super+H → `jippity --history`.
- **No standalone tray phase.** Tray app folded into Phase 7 (rich GUI).

## Longer-Term Vision (Phase 7)

| Phase | Feature |
|-------|---------|
| 7 | Rich GUI with system tray — Tauri, Qt, or GTK frontend wrapping the proven core. Tray adds at-a-glance status (active thread, last mode, response arrival) without changing invocation: hotkeys remain primary. |

## Repo

https://github.com/BDubDesigns/codex-jippity
