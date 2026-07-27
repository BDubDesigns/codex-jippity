# Jippity

Jippity is a lightweight KDE Plasma and Wayland hotkey frontend for the [Codex CLI](https://github.com/openai/codex). Capture a region, window, or screen; ask a question; and receive the answer in a popup without interrupting your desktop workflow. It supports region, window, full-screen, and text-only prompts, plus local conversation threads with searchable history and the option to continue a previous thread. Optional Whisper transcription runs locally.

It is implemented with shell and Python/PyQt6, with no daemon and no build system.

> **Current platform scope:** Jippity is Linux-only, designed for KDE Plasma on Wayland, and tested on CachyOS/Arch Linux. It has not yet been broadly tested or supported across other distributions or desktop environments.

<!-- Add a real screen recording or GIF here when one is available. -->

## Why I built this

I wanted to ask Codex about something visible on my desktop without opening a terminal, manually creating or locating a screenshot, attaching it separately, and breaking my current workflow. Jippity keeps that flow to a hotkey, a capture when needed, and a question.

## Install and setup

Clone the repository, enter it, and run setup:

```bash
git clone https://github.com/BDubDesigns/codex-jippity.git
cd codex-jippity
./jippity-setup
```

The setup script creates Jippity's local directories and prints KDE global-shortcut binding instructions. Install any missing dependencies first, then bind the commands in KDE System Settings to the full path of the `jippity` script.

### Required

- Codex CLI (`codex`)
- Spectacle (`spectacle`)
- KDialog (`kdialog`)
- `jq`
- Python 3
- Standard Unix commands used by the scripts, including `bash`, `cat`, `date`, `fold`, `grep`, `mkdir`, `mktemp`, `rm`, and `tr`

Some dependencies may already be installed depending on your distribution. KDE Plasma installations do not necessarily include every dependency above.

### Recommended

- PyQt6, for the combined native prompt dialog and history viewer. Without it, Jippity falls back to a two-step KDialog prompt flow.

### Optional voice input

- `parecord`, or the applicable PipeWire/PulseAudio compatibility package
- whisper.cpp
- A compatible Whisper model

For CachyOS/Arch Linux, for example:

```bash
paru -S whisper.cpp whisper.cpp-model-small.en
```

Then enable voice input:

```bash
./jippity --voice
```

Voice input is off by default. When enabled and the dependencies are available, hold Alt or the on-screen button while the prompt is open, then release to transcribe locally into the prompt.

## Hotkeys

| Key | Command | Action |
|-----|---------|--------|
| Super+S | `jippity --mode region` | Select region, then ask Codex |
| Super+W | `jippity --mode screen` | Capture full screen, then ask Codex |
| Super+A | `jippity --mode window` | Capture active window, then ask Codex |
| Super+Q | `jippity --mode quick` | Text-only prompt |
| Super+H | `jippity --history` | Browse, search, delete, or continue threads |
| Super+V | `jippity --voice` | Toggle optional voice input |

Bind them in KDE System Settings > Shortcuts > Custom Shortcuts.

## What it does

- Captures a selected region, active window, or full screen, or accepts a text-only prompt.
- Shows the Codex answer in a popup and stores local transcripts.
- Lets you continue a previous thread, browse history, search prompts and responses, delete threads, and set an active thread.
- Uses local history reconstruction for thread continuity rather than Codex session storage.
- Uses `codex exec --ephemeral` for each request.

## Status and roadmap

Core screenshot and text prompt flows work, as do local thread continuation and searchable history. Voice input is implemented. A richer GUI and tray are future work, not a requirement for using the current application. [Jippity Doctor is tracked separately in Issue #8](https://github.com/BDubDesigns/codex-jippity/issues/8).

## Custom tools

Custom tools are an advanced feature. Active manifests live in `tools/`. A manifest teaches Codex about a command; it does not install or implement that command. External commands must already be installed and available in `$PATH`. Bundled tools would include both a real executable command and an associated manifest.

Review a command before teaching Codex to invoke it. Adding active tools may expose the per-prompt **Run Codex without sandboxing** option; treat tools that require unsandboxed execution cautiously.

Documentation-only manifest format:

```text
# @tool example-command
# @description Brief description of what the command does
# @usage example-command [options]
# @example example-command --help
# @installed-by external (must be installed separately and available in $PATH)
```

Jippity Doctor will provide a bundled diagnostic command and an optional example manifest in [Issue #8](https://github.com/BDubDesigns/codex-jippity/issues/8).

## Privacy and security

- History, screenshots, responses, and logs are stored locally under `~/.local/share/jippity/`.
- Configuration and state are stored under `~/.config/jippity/`.
- Prompts and attached screenshots are passed through the Codex CLI and are subject to your Codex/OpenAI configuration and policies.
- Whisper transcription runs locally when whisper.cpp is used.
- The unsandboxed execution option grants Codex-invoked commands broad access as your current user, including local files and the network. It should normally remain disabled.
- Avoid capturing or submitting sensitive information you do not intend to send through Codex.
- Saved local history may itself contain sensitive prompts, answers, or screenshots.

## Scripts

| Script | Purpose |
|--------|---------|
| `jippity` | Shared core: `jippity --mode <region\|screen\|window\|quick>`, `--history`, `--voice` |
| `jippity-window` | Wrapper for window capture |
| `jippity-screen` | Wrapper for screen capture |
| `jippity-region` | Wrapper for region capture |
| `jippity-quick` | Wrapper for text-only prompts |
| `jippity-prompt` | PyQt6 prompt helper, with optional voice input |
| `jippity-history` | PyQt6 history viewer |
| `jippity-setup` | Creates directories and prints shortcut instructions |
| `jippity-tools` | Reads active tool manifests from `tools/` |

## License

[MIT License](LICENSE)
