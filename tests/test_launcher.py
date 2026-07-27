import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.install = self.base / "install"
        self.install.mkdir()
        for name in ("jippity", "jippity-tools", "jippity_common.py"):
            source = ROOT / name
            target = self.install / name
            shutil.copy2(source, target)
            target.chmod(0o755)
        (self.install / "tools").mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.args_file = self.base / "codex-args"
        self.kdialog_file = self.base / "kdialog-calls"
        self.home = self.base / "home"
        self.env = os.environ.copy()
        self.env.update({
            "PATH": str(self.bin) + os.pathsep + self.env["PATH"],
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_DATA_HOME": str(self.home / ".local" / "share"),
            "CODEX_ARGS_FILE": str(self.args_file),
            "KDIALOG_CALLS_FILE": str(self.kdialog_file),
        })
        self.write_stub("codex", """#!/bin/sh
printf '%s\\n' "$@" > "$CODEX_ARGS_FILE"
output=''
while [ "$#" -gt 0 ]; do
    if [ "$1" = -o ]; then shift; output=$1; fi
    shift
done
[ -z "$output" ] || printf 'stub response\\n' > "$output"
""")
        self.write_stub("kdialog", """#!/bin/sh
printf '%s\\n' "$*" >> "$KDIALOG_CALLS_FILE"
case "$*" in
  *--inputbox*) printf 'test prompt\\n' ;;
  *--yesno*)
    case "$*" in
      *'live web search'*) [ "${STUB_LIVE_SEARCH:-0}" = 1 ] && exit 0 || exit 1 ;;
      *'full system access'*) [ "${STUB_FULL_ACCESS:-0}" = 1 ] && exit 0 || exit 1 ;;
      *) exit 1 ;;
    esac ;;
esac
""")

    def tearDown(self):
        self.temp.cleanup()

    def write_stub(self, name, content):
        path = self.bin / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def run_launcher(self, live=False, full=False, tools=False):
        if tools:
            (self.install / "tools" / "trusted").write_text(
                "# @tool trusted\n# @description test manifest\n", encoding="utf-8"
            )
        env = self.env.copy()
        env.update({"STUB_LIVE_SEARCH": "1" if live else "0", "STUB_FULL_ACCESS": "1" if full else "0"})
        return subprocess.run([str(self.install / "jippity"), "--mode", "quick"],
                              cwd=self.base, env=env, text=True, capture_output=True, check=False)

    def codex_args(self):
        return self.args_file.read_text(encoding="utf-8").splitlines()

    def test_live_search_and_full_access_are_independent(self):
        cases = ((True, False, False, True, False), (False, True, True, False, True),
                 (True, True, True, True, True), (False, False, True, False, False))
        for live, full, tools, expect_search, expect_access in cases:
            with self.subTest(live=live, full=full, tools=tools):
                self.args_file.unlink(missing_ok=True)
                self.kdialog_file.unlink(missing_ok=True)
                result = self.run_launcher(live, full, tools)
                self.assertEqual(result.returncode, 0, result.stderr)
                args = self.codex_args()
                self.assertEqual("--search" in args, expect_search)
                self.assertEqual("danger-full-access" in args, expect_access)

    def test_no_tools_keeps_live_search_available_and_full_access_unavailable(self):
        result = self.run_launcher(live=True, full=True, tools=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--search", self.codex_args())
        self.assertNotIn("danger-full-access", self.codex_args())
        self.assertNotIn("full system access", self.kdialog_file.read_text(encoding="utf-8"))

    def test_state_is_data_not_shell_code(self):
        state = self.home / ".config" / "jippity" / "state"
        state.parent.mkdir(parents=True)
        state.write_text('THREAD_ID="$(touch should-not-exist)"\nVOICE_ENABLED=$(touch also-should-not-exist)\nUNKNOWN_KEY=secret\n', encoding="utf-8")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.base / "should-not-exist").exists())
        self.assertFalse((self.base / "also-should-not-exist").exists())
        saved = state.read_text(encoding="utf-8")
        self.assertIn("VOICE_ENABLED=false", saved)
        self.assertNotIn("UNKNOWN_KEY", saved)


if __name__ == "__main__":
    unittest.main()
