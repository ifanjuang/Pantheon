"""Regression tests for mandatory Governance Doctor fail-closed behavior."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pantheon_mcp import doctor


class TestDoctorFailClosed(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = doctor.find_repo_root()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _copy_register_schemas(self) -> None:
        target = self.tmp / "schemas"
        target.mkdir(parents=True, exist_ok=True)
        for name in doctor.REGISTER_KEY_TO_SCHEMA.values():
            shutil.copy2(self.repo / "schemas" / name, target / name)

    def test_real_repository_reports_structured_green_result(self) -> None:
        report = doctor.run_all(self.repo)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["checks"]["mandatory"], 5)
        mandatory = [item for item in report["checks"] if item["mandatory"]]
        self.assertTrue(mandatory)
        self.assertTrue(all(item["status"] == "pass" for item in mandatory))
        for item in report["checks"]:
            self.assertIn(item["status"], doctor.CHECK_STATUSES)
            self.assertEqual(
                set(item["counts"]),
                {"expected", "evaluated", "passed", "failed", "not_run"},
            )

    def test_ai_logs_are_not_part_of_mandatory_file_health(self) -> None:
        self.assertNotIn("ai_logs/README.md", doctor.MANDATORY_FILES)
        for relative in doctor.MANDATORY_FILES:
            source = self.repo / relative
            target = self.tmp / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        self.assertFalse((self.tmp / "ai_logs").exists())
        result = doctor.check_mandatory_files(self.tmp)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["missing"], [])

    def test_missing_required_instance_directory_is_not_run(self) -> None:
        result = doctor.check_vertical_slice(self.tmp)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "not_run")
        self.assertGreater(result["counts"]["not_run"], 0)

    def test_empty_required_register_corpus_is_not_run(self) -> None:
        (self.tmp / "docs" / "examples" / "cascade_register").mkdir(parents=True)
        result = doctor.check_register_instances(self.tmp)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "not_run")

    def test_missing_required_schemas_is_not_run(self) -> None:
        instances = self.tmp / "docs" / "examples" / "cascade_register"
        instances.mkdir(parents=True)
        (instances / "candidate.yaml").write_text("candidate_id: P-1\n", encoding="utf-8")
        result = doctor.check_register_instances(self.tmp)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "not_run")
        self.assertEqual(len(result["missing_schemas"]), len(doctor.REGISTER_KEY_TO_SCHEMA))

    def test_invalid_schema_is_fail_not_skip(self) -> None:
        self._copy_register_schemas()
        instances = self.tmp / "docs" / "examples" / "cascade_register"
        instances.mkdir(parents=True)
        (instances / "candidate.yaml").write_text("candidate_id: P-1\n", encoding="utf-8")
        (self.tmp / "schemas" / "register_candidate.schema.yaml").write_text("[", encoding="utf-8")
        result = doctor.check_register_instances(self.tmp)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["violations"])

    def test_malformed_instance_yaml_is_fail_not_skip(self) -> None:
        self._copy_register_schemas()
        instances = self.tmp / "docs" / "examples" / "cascade_register"
        instances.mkdir(parents=True)
        (instances / "broken.yaml").write_text("candidate_id: [", encoding="utf-8")
        result = doctor.check_register_instances(self.tmp)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("YAML parse failed" in item["message"] for item in result["violations"]))

    def test_missing_validator_is_blocking_capability_gap(self) -> None:
        with mock.patch.object(doctor, "yaml", None):
            result = doctor.check_register_instances(self.repo)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "capability_gap")
        self.assertTrue(result["mandatory"])

    def test_mandatory_not_run_blocks_but_informational_not_run_does_not(self) -> None:
        passed = doctor._result("pass", "pass", message="ran", expected=1, evaluated=1, passed=1)
        mandatory_not_run = doctor._result(
            "missing", "not_run", message="did not run", expected=1, not_run=1
        )
        informational_not_run = doctor._result(
            "worklist",
            "not_run",
            mandatory=False,
            message="optional corpus absent",
            expected=1,
            not_run=1,
        )
        with (
            mock.patch.object(doctor, "check_mandatory_files", return_value=passed),
            mock.patch.object(doctor, "check_runtime_phrases", return_value=mandatory_not_run),
            mock.patch.object(doctor, "check_retired_vocabulary", return_value=informational_not_run),
            mock.patch.object(doctor, "check_cascade_rule", return_value=passed),
            mock.patch.object(doctor, "check_register_instances", return_value=passed),
            mock.patch.object(doctor, "check_vertical_slice", return_value=passed),
        ):
            blocked = doctor.run_all(self.tmp)
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["summary"]["checks"]["not_run"], 2)

        with (
            mock.patch.object(doctor, "check_mandatory_files", return_value=passed),
            mock.patch.object(doctor, "check_runtime_phrases", return_value=passed),
            mock.patch.object(doctor, "check_retired_vocabulary", return_value=informational_not_run),
            mock.patch.object(doctor, "check_cascade_rule", return_value=passed),
            mock.patch.object(doctor, "check_register_instances", return_value=passed),
            mock.patch.object(doctor, "check_vertical_slice", return_value=passed),
        ):
            healthy = doctor.run_all(self.tmp)
        self.assertTrue(healthy["ok"])
        self.assertEqual(healthy["summary"]["checks"]["not_run"], 1)


if __name__ == "__main__":
    unittest.main()
