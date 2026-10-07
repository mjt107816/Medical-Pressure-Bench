"""Regression checks for the files exported in public result archives."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from package_results import public_json
from benchmark_core.runtime.api_config import APISettings


class AnonymizationTests(unittest.TestCase):
    def test_new_run_metadata_omits_connection_details(self) -> None:
        settings = APISettings(
            provider="openai", model="example-model",
            api_base="private-connection-value", api_endpoint="/private-path", api_key="secret",
        )
        public = settings.public_dict()
        self.assertEqual(public["model"], "example-model")
        self.assertFalse({"api_base", "api_endpoint", "api_key"} & public.keys())

    def test_live_run_requires_explicit_connection(self) -> None:
        issues = APISettings(model="example-model", api_key="secret").validate()
        self.assertTrue(any("api_base" in issue for issue in issues))
        self.assertTrue(any("api_endpoint" in issue for issue in issues))

    def test_connection_metadata_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "api_config.public.json"
            path.write_text(json.dumps({
                "provider": "openai", "model": "example-model",
                "api_base": "private-connection-value",
                "api_endpoint": "/chat/completions", "api_key": "example-secret",
            }))
            exported = json.loads(public_json(path))
        self.assertEqual(exported, {"provider": "openai", "model": "example-model"})

    def test_local_path_is_removed_but_simulated_path_remains(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.json"
            path.write_text(json.dumps({
                "error": "trace at /" + "home/researcher/private/log.txt",
                "simulated_file": "/workspace/case/chart.json",
            }))
            exported = json.loads(public_json(path))
        self.assertNotIn("/home/", exported["error"])
        self.assertEqual(exported["simulated_file"], "/workspace/case/chart.json")

    def test_embedded_address_is_removed_from_log(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.json"
            path.write_text(json.dumps({
                "message": "request to " + "https:" + "//private.example.invalid/path",
                "ip": "192.0.2.10",
            }))
            exported = json.loads(public_json(path))
        self.assertEqual(exported["message"], "request to <REDACTED_URL>")
        self.assertEqual(exported["ip"], "<REDACTED_IP>")


if __name__ == "__main__":
    unittest.main()
