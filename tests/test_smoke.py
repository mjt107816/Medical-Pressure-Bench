"""Small integration checks for the published episode and rule-scoring paths."""

from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark_core.orchestrator import EpisodeRunner
from benchmark_core.shared.io import config_from_dict
from judge.rules import score_episode


class PublishedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "configs/tasks/task_147_radiopharmaceutical_release_gate/00_baseline.json"
        cls.raw = json.loads(path.read_text(encoding="utf-8"))
        cls.result = EpisodeRunner().run(config_from_dict(cls.raw), demo=True)

    def test_demo_episode_produces_scoring_inputs(self) -> None:
        self.assertTrue(self.result.events)
        self.assertIn("task_state", self.result.final_state)
        self.assertEqual(self.result.evaluation["evaluator_version"], "llm_judge_only_input_v1")
        score = score_episode(self.raw, self.result.events, self.result.final_state)
        self.assertEqual(score["risk_class"], "N")
        self.assertEqual(score["steps"], len(self.result.events))

    def test_recorded_unsafe_success_takes_risk_priority(self) -> None:
        state = deepcopy(self.result.final_state)
        state["unsafe_successes"] = [{"tool_name": "example"}]
        state["unsafe_attempts"] = [{"tool_name": "example"}]
        state["task_state"]["dependency_violations"] = ["example"]
        score = score_episode(self.raw, self.result.events, state)
        self.assertEqual(score["risk_class"], "H")
        self.assertEqual(score["res"], 100)


if __name__ == "__main__":
    unittest.main()
