import importlib.util
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "jippity-doctor"
REQUIRED = ("codex", "spectacle", "kdialog", "jq", "python3", "bash", "cat",
             "date", "dirname", "fold", "grep", "mkdir", "mktemp", "pwd", "rm", "tr", "wc")


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.home = self.base / "private-home"
        self.config = self.home / ".config"
        self.data = self.home / ".local" / "share"
        (self.config / "jippity").mkdir(parents=True)
        (self.data / "jippity").mkdir(parents=True)
        self.env = os.environ.copy()
        self.env.update({"PATH": str(self.bin), "HOME": str(self.home),
                         "XDG_CONFIG_HOME": str(self.config),
                         "XDG_DATA_HOME": str(self.data),
                         "XDG_CURRENT_DESKTOP": "KDE", "XDG_SESSION_TYPE": "wayland"})
        for name in REQUIRED:
            self.stub(name)

    def tearDown(self):
        self.temp.cleanup()

    def stub(self, name):
        body = "#!/bin/sh\n"
        if name == "codex":
            body += "[ \"$1\" = --version ] && printf 'codex test-version\\n'\n"
        path = self.bin / name
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def run_doctor(self, *args):
        return subprocess.run([sys.executable, str(DOCTOR), *args], env=self.env,
                              cwd=self.base, text=True, capture_output=True, check=False)

    def test_healthy_required_dependencies_exit_zero_and_json_is_stable(self):
        result = self.run_doctor("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema"], "jippity-doctor/v1")
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["overall"], "PASS")
        self.assertIn("dependency.codex", {item["id"] for item in report["checks"]})
        self.assertNotIn("\x1b", result.stdout)

    def test_missing_required_dependency_fails(self):
        (self.bin / "jq").unlink()
        result = self.run_doctor()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL jq is missing", result.stdout)

    def test_human_report_has_groups_and_actionable_fixes(self):
        result = self.run_doctor()
        self.assertEqual(result.returncode, 0)
        self.assertIn("Platform:", result.stdout)
        self.assertIn("Required dependencies:", result.stdout)
        self.assertIn("Optional voice support:", result.stdout)
        self.assertIn("Actionable fixes:", result.stdout)

    def test_failing_json_is_valid_json(self):
        (self.bin / "jq").unlink()
        result = self.run_doctor("--json")
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        checks = {item["id"]: item for item in report["checks"]}
        self.assertEqual(checks["dependency.jq"]["status"], "FAIL")

    def test_optional_and_recommended_warnings_do_not_fail(self):
        result = self.run_doctor()
        self.assertEqual(result.returncode, 0)
        self.assertIn("WARN PyQt6 not available", result.stdout)
        self.assertIn("WARN parecord not found", result.stdout)

    def test_usage_error(self):
        result = self.run_doctor("--bad")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)

    def test_help_describes_read_only_exit_behavior(self):
        result = self.run_doctor("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Exit codes: 0", result.stdout)
        self.assertIn("read-only", result.stdout)

    def test_non_linux_platform_is_a_required_failure(self):
        sys.path.insert(0, str(ROOT))
        try:
            spec = importlib.util.spec_from_loader(
                "doctor", SourceFileLoader("doctor", str(DOCTOR))
            )
            doctor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(doctor)
        finally:
            sys.path.pop(0)
        report = doctor.build_report(str(ROOT), self.env, platform_name="darwin")
        checks = {item["id"]: item for item in report["checks"]}
        self.assertEqual(checks["platform.linux"]["status"], "FAIL")
        self.assertEqual(report["overall"], "FAIL")

    def test_model_lookup_precedence_matches_shared_source(self):
        spec = importlib.util.spec_from_file_location("common", ROOT / "jippity_common.py")
        common = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(common)
        first, second = self.base / "first.bin", self.base / "second.bin"
        first.write_text("a")
        second.write_text("b")
        self.assertEqual(common.find_model((str(first), str(second))), str(first))

    def test_state_and_history_are_not_mutated_and_paths_are_sanitized(self):
        state = self.config / "jippity" / "state"
        history = self.data / "jippity" / "history.jsonl"
        state.write_text('VOICE_ENABLED=$(touch should-not-exist)\nTOKEN=do-not-print\n')
        history.write_text('{"prompt":"private prompt"}\n')
        before = (state.read_bytes(), history.read_bytes())
        result = self.run_doctor("--json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(before, (state.read_bytes(), history.read_bytes()))
        self.assertNotIn(str(self.home), result.stdout)
        self.assertNotIn("do-not-print", result.stdout)
        self.assertNotIn("private prompt", result.stdout)
        self.assertFalse((self.base / "should-not-exist").exists())
        checks = {item["id"]: item for item in json.loads(result.stdout)["checks"]}
        self.assertEqual(checks["state.validity"]["status"], "WARN")

    def test_examples_are_inactive_and_activated_command_works_outside_repo(self):
        self.assertEqual(subprocess.run([sys.executable, str(ROOT / "jippity-tools"), "--list"],
                                        text=True, capture_output=True, check=False).stdout, "")
        install = self.base / "install"
        (install / "tools").mkdir(parents=True)
        for name in ("jippity", "jippity-prompt", "jippity-history", "jippity-tools",
                     "jippity-common", "jippity-doctor"):
            source = ROOT / ("jippity_common.py" if name == "jippity-common" else name)
            target = install / ("jippity_common.py" if name == "jippity-common" else name)
            shutil.copy2(source, target)
            target.chmod(0o755)
        shutil.copy2(ROOT / "examples/tools/jippity-doctor", install / "tools/jippity-doctor")
        manifest_before = (install / "tools/jippity-doctor").read_bytes()
        listed = subprocess.run([sys.executable, str(install / "jippity-tools"), "--list"],
                                cwd=self.base, text=True, capture_output=True, check=False)
        self.assertEqual(listed.stdout.strip(), "jippity-doctor")
        block = subprocess.run([sys.executable, str(install / "jippity-tools")], cwd=self.base,
                               text=True, capture_output=True, check=False).stdout
        self.assertIn(str(install / "jippity-doctor"), block)
        (install / "tools/broken").write_text("# @description missing tool name\n")
        (install / "tools/external-missing").write_text(
            "# @tool external-missing\n# @command external-missing\n"
            "# @installed-by external\n"
        )
        invocation = subprocess.run([sys.executable, str(install / "jippity-doctor"), "--json"],
                                    cwd=self.base, env=self.env, text=True, capture_output=True, check=False)
        self.assertEqual(invocation.returncode, 0)
        checks = {item["id"]: item for item in json.loads(invocation.stdout)["checks"]}
        self.assertEqual(checks["tool.broken"]["status"], "WARN")
        self.assertEqual(checks["tool.external-missing"]["status"], "WARN")
        self.assertEqual(manifest_before, (install / "tools/jippity-doctor").read_bytes())


if __name__ == "__main__":
    unittest.main()
