from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
sys.path.insert(0, str(EXPERIMENTS_DIR))

import rpi_final_report  # noqa: E402


class FinalMetricsRecomputeTests(unittest.TestCase):
    def test_collected_metrics_match_committed_json(self) -> None:
        actual = rpi_final_report.collect_metrics()
        expected = json.loads((EXPERIMENTS_DIR / "final_metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)

    def test_committed_report_matches_recomputed_metrics(self) -> None:
        metrics = rpi_final_report.collect_metrics()
        self.assertTrue(
            rpi_final_report.report_matches_metrics(
                EXPERIMENTS_DIR / "final_report.md",
                metrics,
            )
        )

    def test_recomputed_metrics_preserve_paper_conclusion(self) -> None:
        metrics = rpi_final_report.collect_metrics()
        conclusion = metrics["conclusion"]
        self.assertTrue(conclusion["paper_scale_runs_complete"])
        self.assertTrue(conclusion["positive_controls_pass"])
        self.assertFalse(conclusion["residual_beyond_B1_detected"])


if __name__ == "__main__":
    unittest.main()
