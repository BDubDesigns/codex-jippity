# Jippity / Codex-Jippity Specification

## Working Name

**Jippity**

Optional nickname / command prefix:

**CJ** — short for **Codex-Jippity**

## Project Summary

Jippity is a lightweight Linux desktop assistant layer over the Codex CLI.

It lets the user press global hotkeys to ask quick questions, optionally attach screenshots of the current screen, active window, or a selected region, then sends the prompt and image to Codex. The response is displayed in a simple desktop-friendly output window.

The first version is intentionally small: one-shot questions only, no tray app, no custom database, no full agent framework, and no background daemon unless required by the desktop environment. Later versions can add resumable Codex sessions, history, tray controls, voice input, model/provider switching, and safety checks.

The goal is not to replace ChatGPT, Zed, OpenClaw, or Hermes. The goal is to create a fast, native-feeling Linux “ask about what I’m doing right now” utility.

---

## Problem

On Linux, there is no official native ChatGPT desktop app. Browser PWAs work, but they do not feel deeply integrated with the desktop.

The user wants a fast way to:

* ask a quick question without opening a browser,
* capture part of the screen and ask about it,
* capture the whole screen and ask about it,
* capture the active app/window and ask about it,
* optionally continue a previous Codex session,
* use whatever model/provider Codex CLI is configured to use.

Codex CLI already supports text prompts, image inputs, flags, provider/model switching, and session resume via `--resume <session_id>`. Jippity should use Codex as the engine instead of trying to become a full LLM platform itself.

---

## Core Principle

Jippity should be a thin Linux-native UX layer over Codex CLI.

It should not duplicate Codex features unless there is a clear UX reason.

Codex owns:

* model/provider behavior,
* reasoning/chat execution,
* session continuation,
* image understanding,
* authentication/provider config.

Jippity owns:

* hotkeys,
* screenshot capture,
* prompt input,
* command construction,
* output display,
* lightweight local preferences,
* optional history metadata.

---

## Target Platform

Initial target:

* Linux
* KDE Plasma
* Wayland
* CachyOS / Arch-like environment
* fish shell compatibility for setup scripts

The first implementation may be KDE-specific if that keeps the MVP simple.

Future support may include:

* GNOME
* wlroots compositors
* X11
* non-KDE screenshot tools

---

## Assumed External Dependencies

Initial MVP may depend on:

* `codex`
* `spectacle`
* `kdialog`
* standard Unix shell tools
* KDE global shortcuts configured manually by the user

Potential later dependencies:

* `sqlite`
* `jq`
* `wl-clipboard`
* `grim`
* `slurp`
* `tesseract` or OCR tooling if needed
* local voice-to-text tooling
* a tray framework such as Qt, Tauri, Electron, or a small Python/GTK/Qt app

---

## MVP Scope

The MVP is a set of small executable scripts that can be bound to KDE global shortcuts.

### MVP Commands

Jippity should provide four commands:

1. `jippity-region`
2. `jippity-screen`
3. `jippity-window`
4. `jippity-quick`

### MVP Hotkey Mapping

Recommended default hotkeys:

| Hotkey      | Command          | Behavior                                               |
| ----------- | ---------------- | ------------------------------------------------------ |
| `Super + S` | `jippity-region` | Select a screen region, then ask Codex about it        |
| `Super + W` | `jippity-screen` | Capture the whole screen, then ask Codex about it      |
| `Super + A` | `jippity-window` | Capture the active window/app, then ask Codex about it |
| `Super + Q` | `jippity-quick`  | Ask a text-only question                               |

The user may choose different hotkeys if these conflict with existing KDE shortcuts.

---

## MVP User Flow

### Region Screenshot Flow

1. User presses `Super + S`.
2. Jippity launches the KDE screenshot region selector.
3. User draws a region.
4. Screenshot is saved to a temporary Jippity path.
5. Jippity opens a small prompt input window.
6. User types a question.
7. Jippity runs Codex with the screenshot and prompt.
8. Jippity captures Codex output.
9. Jippity displays the output in a readable desktop window.
10. Temporary files may be retained in a simple history folder or deleted depending on MVP choice.

Example conceptual command:

`codex -i /path/to/image.png "What am I looking at?"`

### Full Screen Flow

1. User presses `Super + W`.
2. Jippity captures the entire screen automatically.
3. Jippity asks for a prompt.
4. Jippity sends screenshot and prompt to Codex.
5. Jippity displays the response.

### Active Window Flow

1. User presses `Super + A`.
2. Jippity captures the active window.
3. Jippity asks for a prompt.
4. Jippity sends screenshot and prompt to Codex.
5. Jippity displays the response.

### Quick Question Flow

1. User presses `Super + Q`.
2. Jippity opens a prompt input window.
3. User types a question.
4. Jippity sends the text prompt to Codex with no image.
5. Jippity displays the response.

---

## MVP Non-Goals

The MVP should not include:

* tray app,
* custom chat UI,
* voice input,
* SQLite database,
* session picker,
* model picker,
* settings screen,
* automatic shell command execution,
* file system access beyond screenshots and local config,
* autonomous agent behavior,
* background monitoring,
* OpenClaw/Hermes-style task execution.

The MVP proves the desktop loop:

Hotkey → optional screenshot → prompt → Codex → readable answer.

---

## Session Resume Design

Codex supports session resume using:

`codex --resume <session_id>`

Jippity should eventually support both one-shot mode and continue-thread mode.

### Version 1 Behavior

MVP behavior:

* Always one-shot.
* No resume.
* No session storage required.

### Version 2 Behavior

Add a simple preference:

* Continue previous thread: on/off.

Possible UX:

* Prompt input window includes a checkbox:

  * `Continue previous Codex session`
* Default is unchecked.
* If checked, Jippity uses the stored active session ID.
* Once the user checks it, Jippity remembers that preference.
* User can uncheck it to return to one-shot mode.

### Reset Behavior

Recommended command:

* `jippity-reset`

Recommended hotkey:

* `Super + R`

Behavior:

* Clears active session ID.
* Sets continue-thread preference to false.
* Next question starts fresh.

### Session Storage

Store simple session state in a config file, for example:

`~/.config/jippity/state.json`

Possible contents:

* active session ID
* continue-thread default
* last used capture mode
* last used model/provider if Jippity ever manages that
* timestamp of last session

Jippity should not attempt to fully own Codex’s session history unless needed.

---

## Later Tray App

A later version may include a system tray app.

### Tray App Responsibilities

The tray app may provide:

* quick buttons:

  * Region capture
  * Full screen capture
  * Active window capture
  * Quick question
* current session indicator
* continue-thread toggle
* reset session button
* recent questions/history
* settings
* model/provider shortcuts if Codex supports easy switching
* voice input toggle
* open logs folder
* quit

### Tray App Non-Responsibilities

The tray app should not become a full IDE, browser, or autonomous agent framework.

It should remain a lightweight desktop launcher and session controller for Codex.

---

## Output Display

### MVP Output

Use a simple desktop text window.

Possible tools:

* `kdialog --textbox`
* temporary text file opened in default text viewer
* terminal window with held output
* basic custom GUI later

Recommended MVP:

* write Codex output to a temporary `.txt` or `.md` file,
* open it in `kdialog --textbox`.

### Later Output

Later versions may provide a richer result window with:

* markdown rendering,
* copy button,
* save button,
* continue button,
* open screenshot button,
* command warning banner,
* session metadata.

---

## History

### MVP History

History is optional for MVP.

If retained, save basic artifacts under:

`~/.local/share/jippity/`

Possible structure:

* `screenshots/`
* `responses/`
* `logs/`

### Later History

Later versions may store:

* timestamp,
* prompt,
* response,
* image path,
* capture mode,
* Codex session ID,
* provider/model if discoverable,
* latency,
* exit status,
* error output.

A future SQLite database may be useful, but it is unnecessary for the MVP.

---

## Safety Design

Jippity should not automatically run shell commands returned by Codex.

Later versions may include command safety warnings.

If Codex output contains dangerous-looking shell patterns, Jippity may display a warning banner.

Examples of risky patterns:

* `rm -rf`
* `sudo rm`
* `mkfs`
* `dd if=`
* writing directly to block devices
* recursive permission changes like `chmod -R 777 /`
* commands targeting `/`, `/home`, or mounted drives
* package removal commands affecting large system areas

This should be advisory, not censorship. The purpose is to prevent accidental copy/paste disasters.

Possible later modes:

| Mode            | Purpose                                |
| --------------- | -------------------------------------- |
| Ask             | normal question                        |
| Explain Screen  | explain screenshot                     |
| Explain Command | explain what a command does            |
| Verify Command  | check command safety before running    |
| Linux Tutor     | beginner-friendly explanation          |
| Debug Error     | analyze error messages from screenshot |

---

## Privacy and Trust

Jippity should be transparent.

It should make it obvious:

* what screenshot was captured,
* what prompt was sent,
* whether a session was resumed,
* where files are stored,
* what command was run,
* whether history is retained.

Jippity should avoid hidden telemetry.

If telemetry is ever added, it must be opt-in only.

---

## Configuration

Initial config path:

`~/.config/jippity/config.json`

Possible future config fields:

* default continue-thread behavior
* preferred Codex command path
* default output viewer
* screenshot save directory
* whether to retain screenshots
* whether to retain responses
* prompt window type
* output window type
* preferred hotkey hints
* voice input enabled
* safety warnings enabled

---

## Error Handling

Jippity should handle common errors clearly:

* Codex command not found.
* Spectacle command not found.
* kdialog command not found.
* Screenshot capture cancelled.
* Screenshot file was not created.
* Empty prompt submitted.
* Codex exited with non-zero status.
* Codex timed out.
* No active session ID when continue-thread is enabled.
* Resume session failed.

Errors should be shown in a user-readable popup, not silently fail.

---

## Development Roadmap

### Phase 0: Manual Command Validation

Before building Jippity, manually verify:

* Codex can accept image input with `-i`.
* Codex can answer a text prompt from command line.
* Codex can resume a session using `--resume <session_id>`.
* Spectacle can save region screenshots from CLI.
* Spectacle can save full-screen screenshots from CLI.
* Spectacle can save active-window screenshots from CLI.
* kdialog can collect input.
* kdialog can display output text.

### Phase 1: One-Shot Script MVP

Build four executable scripts:

* `jippity-region`
* `jippity-screen`
* `jippity-window`
* `jippity-quick`

Each script should:

1. create needed directories,
2. capture image if needed,
3. prompt for user input,
4. run Codex,
5. capture stdout/stderr,
6. display response or error.

Bind scripts manually to KDE shortcuts.

### Phase 2: Shared Core Script

Refactor duplicate logic into a shared helper.

Possible command:

`jippity --mode region`
`jippity --mode screen`
`jippity --mode window`
`jippity --mode quick`

The hotkey scripts become thin wrappers.

### Phase 3: Session Resume

Add:

* state file,
* active session ID,
* continue-thread toggle,
* reset command,
* optional prompt checkbox.

Use Codex `--resume <session_id>` when continue-thread is enabled.

### Phase 4: History

Add simple history storage.

Save:

* prompt,
* response,
* screenshot path,
* timestamp,
* mode,
* session ID if any.

Do not add a full UI yet unless necessary.

### Phase 5: Tray App

Add a small tray app with:

* quick actions,
* continue-thread toggle,
* reset session,
* recent history,
* settings.

### Phase 6: Voice Input

Add optional voice-to-text before prompt submission.

Voice input should be off by default or clearly toggleable.

### Phase 7: Rich GUI

Only after the CLI/script workflow proves useful, consider a richer app using:

* Tauri,
* Qt,
* GTK,
* Electron,
* or another lightweight GUI toolkit.

The GUI should wrap the proven core command behavior rather than replacing it prematurely.

---

## Implementation Philosophy

Start tiny.

The first useful version should be small enough to understand in one sitting.

Prefer boring Linux tools before building custom infrastructure.

Avoid agent-framework complexity until the workflow has proven it deserves that complexity.

The magic is not in having a huge app. The magic is in making this loop instant:

I see something → press hotkey → ask Jippity → get answer.

---

## Success Criteria for MVP

The MVP is successful if:

* the user can press a hotkey,
* capture a region/fullscreen/window or ask a text-only question,
* type a prompt,
* receive a Codex response,
* and repeat the process reliably.

The MVP does not need to be beautiful.

It needs to feel useful enough that the user naturally reaches for it while using Linux.

---

## Possible Tagline

**Jippity: a Linux-native peek-and-ask assistant powered by Codex.**
