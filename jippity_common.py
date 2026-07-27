"""Small shared, dependency-free helpers used by Jippity scripts."""
import os


MODEL_PATHS = (
    "/usr/share/whisper.cpp-model-small.en/ggml-small.en.bin",
    "/usr/share/whisper.cpp/models/ggml-small.en.bin",
    "/usr/share/whisper.cpp/ggml-small.en.bin",
    "/usr/lib/whisper.cpp/models/ggml-small.en.bin",
    os.path.expanduser("~/.local/share/whisper.cpp/ggml-small.en.bin"),
    os.path.expanduser("~/.local/share/jippity/models/ggml-small.en.bin"),
)
WHISPER_BINARIES = ("whisper-cli", "whisper")


def find_model(paths=MODEL_PATHS):
    """Return the first compatible Whisper model using Jippity's precedence."""
    for path in paths:
        if os.path.isfile(path):
            return path
    return None


def parse_manifest(path):
    """Parse comment front matter, preserving manifests from before @command."""
    tool = {"name": "", "description": "", "usage": [], "example": [],
            "installed_by": "", "command": ""}
    fields = {"tool": "name", "description": "description",
              "installed-by": "installed_by", "command": "command"}
    with open(path, "r", encoding="utf-8") as source:
        for line in source:
            stripped = line.strip()
            if not stripped.startswith("#"):
                break
            body = stripped.lstrip("# ").rstrip()
            if not body.startswith("@") or " " not in body:
                continue
            key, value = body[1:].split(" ", 1)
            value = value.strip()
            if key in ("usage", "example"):
                tool[key].append(value)
            elif key in fields:
                tool[fields[key]] = value
    return tool if tool["name"] else None
