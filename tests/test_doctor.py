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
        elif name == "python3":
            body += f'exec "{sys.executable}" "$@"\n'
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

    def test_passing_checks_do_not_add_actionable_fixes(self):
        sys.path.insert(0, str(ROOT))
        try:
            spec = importlib.util.spec_from_loader(
                "doctor", SourceFileLoader("doctor", str(DOCTOR))
            )
            doctor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(doctor)
        finally:
            sys.path.pop(0)
        report = {"overall": "PASS", "checks": [
            {"id": "platform.linux", "status": "PASS", "message": "Linux detected", "fix": "ignore me"},
        ]}
        from io import StringIO
        from contextlib import redirect_stdout
        output = StringIO()
        with redirect_stdout(output):
            doctor.print_human(report)
        self.assertNotIn("Actionable fixes:", output.getvalue())
        self.assertNotIn("ignore me", output.getvalue())

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
        self.assertIn("WARN PyQt6 not available; prompts use the KDialog fallback and the history viewer is unavailable", result.stdout)
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
        self.assertIn("codex --version", result.stdout)
        self.assertIn("model/API request", result.stdout)

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
                                        env=self.env, text=True, capture_output=True, check=False).stdout, "")
        install = self.home / "install directory"
        (install / "tools").mkdir(parents=True)
        for name in ("jippity", "jippity-window", "jippity-screen", "jippity-region",
                     "jippity-quick", "jippity-prompt", "jippity-history", "jippity-setup",
                     "jippity-tools", "jippity-common", "jippity-doctor"):
            source = ROOT / ("jippity_common.py" if name == "jippity-common" else name)
            target = install / ("jippity_common.py" if name == "jippity-common" else name)
            shutil.copy2(source, target)
            target.chmod(0o755)
        shutil.copy2(ROOT / "examples/tools/jippity-doctor", install / "tools/jippity-doctor")
        manifest_before = (install / "tools/jippity-doctor").read_bytes()
        listed = subprocess.run([sys.executable, str(install / "jippity-tools"), "--list"],
                                cwd=self.base, env=self.env, text=True, capture_output=True, check=False)
        self.assertEqual(listed.stdout.strip(), "jippity-doctor")
        block = subprocess.run([sys.executable, str(install / "jippity-tools")], cwd=self.base,
                               env=self.env, text=True, capture_output=True, check=False).stdout
        tool_json = subprocess.run([sys.executable, str(install / "jippity-tools"), "--json"],
                                   cwd=self.base, env=self.env, text=True, capture_output=True, check=False).stdout
        instructions = json.loads(tool_json)[0]["instruction"]
        self.assertEqual(len(instructions), 5)
        advertised_command = json.loads(tool_json)[0]["command"]
        self.assertIn("${HOME}", advertised_command)
        self.assertNotIn(str(self.home), block)
        self.assertNotIn(str(self.home), advertised_command)
        self.assertIn("Use the default human-readable report for ordinary troubleshooting.", block)
        self.assertIn("Prefer --json when structured inspection helps.", block)
        self.assertIn("Summarize findings and recommended fixes instead of dumping raw JSON.", block)
        self.assertIn("The doctor diagnoses only and never repairs the system.", block)
        self.assertIn("It requires neither networking nor sandbox bypass.", block)
        invocation = subprocess.run(advertised_command + " --json", shell=True,
                                    cwd=self.base, env=self.env, text=True,
                                    capture_output=True, check=False)
        self.assertEqual(invocation.returncode, 0, invocation.stderr)
        self.assertEqual(json.loads(invocation.stdout)["schema"], "jippity-doctor/v1")
        (install / "tools/broken").write_text("# @description missing tool name\n")
        (install / "tools/external-missing").write_text(
            "# @tool external-missing\n# @command external-missing\n"
            "# @installed-by external\n"
        )
        doctor_result = subprocess.run([sys.executable, str(install / "jippity-doctor"), "--json"],
                                       cwd=self.base, env=self.env, text=True, capture_output=True, check=False)
        self.assertEqual(doctor_result.returncode, 0)
        checks = {item["id"]: item for item in json.loads(doctor_result.stdout)["checks"]}
        self.assertEqual(checks["tool.broken"]["status"], "WARN")
        self.assertEqual(checks["tool.external-missing"]["status"], "WARN")
        self.assertEqual(manifest_before, (install / "tools/jippity-doctor").read_bytes())

    def test_missing_wrapper_is_required_failure(self):
        install = self.base / "install"
        install.mkdir()
        for name in ("jippity", "jippity-window", "jippity-screen", "jippity-region",
                     "jippity-quick", "jippity-prompt", "jippity-history", "jippity-setup",
                     "jippity-tools", "jippity-doctor"):
            target = install / name
            shutil.copy2(ROOT / name, target)
            target.chmod(0o755)
        (install / "jippity-window").chmod(0o644)
        sys.path.insert(0, str(ROOT))
        try:
            spec = importlib.util.spec_from_loader(
                "doctor", SourceFileLoader("doctor", str(DOCTOR))
            )
            doctor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(doctor)
        finally:
            sys.path.pop(0)
        checks = {item["id"]: item for item in doctor.build_report(str(install), self.env)["checks"]}
        self.assertEqual(checks["script.jippity-window"]["status"], "FAIL")

    def test_command_validation_for_absolute_relative_and_bundled_tools(self):
        install = self.base / "install"
        tools = install / "tools"
        tools.mkdir(parents=True)
        bundled = install / "jippity-doctor"
        bundled.write_text("#!/bin/sh\n", encoding="utf-8")
        bundled.chmod(0o755)
        absolute = self.base / "absolute-tool"
        absolute.write_text("#!/bin/sh\n", encoding="utf-8")
        absolute.chmod(0o755)
        (tools / "absolute-missing").write_text("# @tool absolute-missing\n# @command /missing/tool\n# @installed-by external\n")
        missing_home = self.home / "private path" / "missing-tool"
        (tools / "absolute-home-missing").write_text(
            f"# @tool absolute-home-missing\n# @command {missing_home}\n# @installed-by external\n"
        )
        (tools / "absolute-valid").write_text(f"# @tool absolute-valid\n# @command {absolute}\n# @installed-by external\n")
        (tools / "relative-missing").write_text("# @tool relative-missing\n# @command no-such-tool\n# @installed-by external\n")
        (tools / "bundled-valid").write_text("# @tool bundled-valid\n# @command jippity-doctor\n# @installed-by jippity\n")
        sys.path.insert(0, str(ROOT))
        try:
            spec = importlib.util.spec_from_loader(
                "doctor", SourceFileLoader("doctor", str(DOCTOR))
            )
            doctor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(doctor)
        finally:
            sys.path.pop(0)
        checks = {item["id"]: item for item in doctor.build_report(str(install), self.env)["checks"]}
        self.assertEqual(checks["tool.absolute-missing"]["status"], "WARN")
        self.assertEqual(checks["tool.absolute-home-missing"]["status"], "WARN")
        self.assertNotIn(str(self.home), checks["tool.absolute-home-missing"]["message"])
        self.assertIn("~", checks["tool.absolute-home-missing"]["message"])
        self.assertEqual(checks["tool.absolute-valid"]["status"], "PASS")
        self.assertEqual(checks["tool.relative-missing"]["status"], "WARN")
        self.assertEqual(checks["tool.bundled-valid"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
