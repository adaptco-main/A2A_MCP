from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from codex_qernel import CodexQernel, QernelConfig
from codex_qernel.capsules import CapsuleManifest, discover_capsule_manifests


class CodexQernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        base = Path(self.tempdir.name)
        self.capsules_dir = base / "capsules"
        self.events_log = base / "events.ndjson"
        self.capsules_dir.mkdir(parents=True, exist_ok=True)
        valid_manifest = {
            "id": "capsule.test.v1",
            "version": "1.0.0",
            "name": "Test Capsule",
            "description": "Used by tests",
        }
        invalid_manifest = {
            "id": "capsule.invalid",
            "name": "Broken Capsule",
        }
        (self.capsules_dir / "valid.json").write_text(json.dumps(valid_manifest), encoding="utf-8")
        (self.capsules_dir / "invalid.json").write_text(json.dumps(invalid_manifest), encoding="utf-8")
        self.config = QernelConfig(
            os_name="TestOS",
            qernel_version="9.9.9",
            capsules_dir=self.capsules_dir,
            events_log=self.events_log,
            auto_refresh=True,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_discover_capsule_manifests_filters_invalid_files(self) -> None:
        manifests = discover_capsule_manifests(self.capsules_dir)
        self.assertEqual(len(manifests), 1)
        manifest = manifests[0]
        self.assertIsInstance(manifest, CapsuleManifest)
        self.assertEqual(manifest.capsule_id, "capsule.test.v1")
        self.assertEqual(manifest.name, "Test Capsule")

    def test_qernel_refresh_and_events(self) -> None:
        qernel = CodexQernel(self.config)
        health = qernel.health_status()
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["os"], "TestOS")
        self.assertEqual(health["capsules_loaded"], 1)

        capsules = qernel.list_capsules()
        self.assertEqual(len(capsules), 1)
        self.assertEqual(capsules[0]["id"], "capsule.test.v1")

        manifest = qernel.get_capsule("capsule.test.v1")
        self.assertEqual(manifest["name"], "Test Capsule")
        self.assertIsNone(qernel.get_capsule("missing"))

        qernel.refresh()
        events = qernel.read_events(limit=5)
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[-1].event, "codex.qernel.refreshed")
        self.assertEqual(events[-1].payload["capsule_count"], 1)

        extra_event = qernel.record_event("codex.test.event", {"key": "value"})
        self.assertEqual(extra_event.payload["key"], "value")
        all_events = qernel.read_events(limit=10)
        self.assertEqual(all_events[-1].event, "codex.test.event")


class ConfigFromEnvTests(unittest.TestCase):
    def test_environment_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            os.environ["AXQXOS_NAME"] = "EnvOS"
            os.environ["CODEX_QERNEL_VERSION"] = "2.3.4"
            os.environ["CODEX_CAPSULE_DIR"] = "relative_capsules"
            os.environ["CODEX_EVENTS_LOG"] = "logs/events.ndjson"
            os.environ["CODEX_AUTO_REFRESH"] = "false"
            config = QernelConfig.from_env(base_dir=base)
            self.assertEqual(config.os_name, "EnvOS")
            self.assertEqual(config.qernel_version, "2.3.4")
            self.assertEqual(config.capsules_dir, base / "relative_capsules")
            self.assertEqual(config.events_log, base / "logs/events.ndjson")
            self.assertFalse(config.auto_refresh)
        for var in [
            "AXQXOS_NAME",
            "CODEX_QERNEL_VERSION",
            "CODEX_CAPSULE_DIR",
            "CODEX_EVENTS_LOG",
            "CODEX_AUTO_REFRESH",
        ]:
            os.environ.pop(var, None)


if __name__ == "__main__":
    unittest.main()
