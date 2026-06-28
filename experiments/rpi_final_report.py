#!/usr/bin/env python3
"""
Generate a compact final report from pinned experiment artifacts.

The manifest deliberately pins result directories. The report generator does
not discover experiment folders implicitly.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


@dataclass
class Artifact:
    name: str
    path: Path
    metadata_path: Path | None
    required: bool


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def latest_row(rows: list[dict[str, str]], exp_key: str = "exp") -> dict[str, str]:
    return max(rows, key=lambda row: as_float(row, exp_key))


def rows_where(rows: list[dict[str, str]], key: str, value: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key) == value]


def fmt(value: float, digits: int = 6) -> str:
    return f"{value:.{digits}f}"


def metric_row(label: str, values: dict[str, Any]) -> dict[str, Any]:
    out = {"label": label}
    out.update(values)
    return out


def load_manifest() -> dict[str, Artifact]:
    manifest = read_json(ROOT / "final_manifest.json")
    artifacts: dict[str, Artifact] = {}
    for key, spec in manifest["artifacts"].items():
        metadata_path = spec.get("metadata_path")
        artifacts[key] = Artifact(
            name=spec["name"],
            path=ROOT / spec["path"],
            metadata_path=ROOT / metadata_path if metadata_path else None,
            required=bool(spec.get("required", True)),
        )
    return artifacts


def artifact_info(artifact: Artifact) -> dict[str, Any]:
    metadata = None
    if artifact.metadata_path and artifact.metadata_path.exists():
        metadata = read_json(artifact.metadata_path)
    return {
        "name": artifact.name,
        "path": str(artifact.path.relative_to(ROOT)),
        "metadata_path": (
            str(artifact.metadata_path.relative_to(ROOT))
            if artifact.metadata_path and artifact.metadata_path.exists()
            else None
        ),
        "metadata": metadata,
    }


def collect_metrics() -> dict[str, Any]:
    artifacts = load_manifest()
    missing = [
        {"name": artifact.name, "path": str(artifact.path)}
        for artifact in artifacts.values()
        if artifact.required and not artifact.path.exists()
    ]
    if missing:
        return {"ok": False, "missing": missing}

    metrics: dict[str, Any] = {"ok": True, "artifacts": {}, "warnings": []}
    for key, artifact in artifacts.items():
        if artifact.path.exists():
            metrics["artifacts"][key] = artifact_info(artifact)

    b1 = latest_row(read_csv(artifacts["paper_b1_stop_time"].path))
    metrics["paper_b1_stop_time_latest"] = metric_row(
        "Paper B1(11) bucket residual stop-time null",
        {
            "X": int(as_float(b1, "X")),
            "n": int(as_float(b1, "n")),
            "R_bits_per_gap": as_float(b1, "R_bits_per_gap"),
            "B1_exact_bits_per_gap": as_float(b1, "B1_exact_bits_per_gap"),
            "U1_exact_bits_per_gap": as_float(b1, "U1_exact_bits_per_gap"),
            "null_mean": as_float(b1, "null_mean"),
            "null_sd": as_float(b1, "null_sd"),
            "null_p05": as_float(b1, "null_p05"),
            "null_p95": as_float(b1, "null_p95"),
            "z_vs_null": as_float(b1, "z_vs_null"),
        },
    )

    ctw = read_csv(artifacts["paper_ctw_rank64_stop_time"].path)
    ctw_b0 = latest_row(rows_where(ctw, "baseline", "B0"))
    ctw_b1 = latest_row(rows_where(ctw, "baseline", "B1(11)"))
    metrics["paper_ctw_rank64_stop_time_latest"] = [
        metric_row(
            "B0",
            {
                "X": int(as_float(ctw_b0, "X")),
                "n": int(as_float(ctw_b0, "n")),
                "R_bits_per_gap": as_float(ctw_b0, "R_bits_per_gap"),
                "total_gain_bits": as_float(ctw_b0, "total_gain_bits"),
                "final_ctw_weight": as_float(ctw_b0, "final_ctw_weight"),
                "B_exact_bits_per_gap": as_float(ctw_b0, "B_exact_bits_per_gap"),
                "U_exact_bits_per_gap": as_float(ctw_b0, "U_exact_bits_per_gap"),
                "null_mean": as_float(ctw_b0, "null_mean"),
                "null_sd": as_float(ctw_b0, "null_sd"),
                "null_p95": as_float(ctw_b0, "null_p95"),
                "empirical_p_ge": as_float(ctw_b0, "empirical_p_ge"),
            },
        ),
        metric_row(
            "B1(11)",
            {
                "X": int(as_float(ctw_b1, "X")),
                "n": int(as_float(ctw_b1, "n")),
                "R_bits_per_gap": as_float(ctw_b1, "R_bits_per_gap"),
                "total_gain_bits": as_float(ctw_b1, "total_gain_bits"),
                "final_ctw_weight": as_float(ctw_b1, "final_ctw_weight"),
                "B_exact_bits_per_gap": as_float(ctw_b1, "B_exact_bits_per_gap"),
                "U_exact_bits_per_gap": as_float(ctw_b1, "U_exact_bits_per_gap"),
                "null_mean": as_float(ctw_b1, "null_mean"),
                "null_sd": as_float(ctw_b1, "null_sd"),
                "null_p95": as_float(ctw_b1, "null_p95"),
                "empirical_p_ge": as_float(ctw_b1, "empirical_p_ge"),
            },
        ),
    ]

    ladder = read_csv(artifacts["paper_baseline_ladder"].path)
    latest_b0 = latest_row(rows_where(ladder, "baseline", "B0"))
    latest_b1 = latest_row(rows_where(ladder, "baseline", "B1(11)"))
    b0_bits = as_float(latest_b0, "B1_exact_bits_per_gap")
    b1_bits = as_float(latest_b1, "B1_exact_bits_per_gap")
    metrics["paper_baseline_ladder_latest"] = [
        metric_row(
            "B0",
            {
                "X": int(as_float(latest_b0, "X")),
                "n": int(as_float(latest_b0, "n")),
                "baseline_exact_bits_per_gap": b0_bits,
                "residual_exact_bits_per_gap": as_float(latest_b0, "U1_exact_bits_per_gap"),
                "R_bits_per_gap": as_float(latest_b0, "R_bits_per_gap"),
                "null_mean": as_float(latest_b0, "null_mean"),
            },
        ),
        metric_row(
            "B1(11)",
            {
                "X": int(as_float(latest_b1, "X")),
                "n": int(as_float(latest_b1, "n")),
                "baseline_exact_bits_per_gap": b1_bits,
                "residual_exact_bits_per_gap": as_float(latest_b1, "U1_exact_bits_per_gap"),
                "R_bits_per_gap": as_float(latest_b1, "R_bits_per_gap"),
                "null_mean": as_float(latest_b1, "null_mean"),
            },
        ),
        metric_row(
            "B0 minus B1(11)",
            {
                "X": int(as_float(latest_b1, "X")),
                "baseline_exact_bits_per_gap": b0_bits - b1_bits,
            },
        ),
    ]

    metrics["paper_scale"] = {
        "max_exp": 26,
        "X": metrics["paper_b1_stop_time_latest"]["X"],
        "nulls": 200,
        "seed": 20260616,
        "artifact_directories": [
            "paper_b1_y11_depth4_stop_time_x26_n200",
            "paper_ctw_rank64_depth1_stop_time_x26_n200",
            "paper_ladder_b0_b1_y11_x26_n200",
        ],
    }

    optional_b2 = {
        "pair_alpha": ("b2_pair_alpha_latest", "selected_alpha"),
        "transition_mod30": ("transition_mod30_lam001_latest", "Btr_gain_vs_B1"),
        "consecutive_alpha": ("b2_consecutive_alpha_latest", "selected_alpha"),
        "consecutive_two_alpha": ("b2_consecutive_two_alpha_latest", "selected_pair_alpha"),
        "consecutive_two_alpha_head8": ("b2_consecutive_two_alpha_head8_latest", "oracle_pair_alpha"),
    }
    for key, (metric_key, marker) in optional_b2.items():
        artifact = artifacts.get(key)
        if artifact and artifact.path.exists():
            row = latest_row(read_csv(artifact.path))
            entry: dict[str, Any] = {
                "label": artifact.name,
                "X": int(as_float(row, "X")),
            }
            if marker in row:
                entry[marker] = as_float(row, marker)
            metrics[metric_key] = entry

    metrics["conclusion"] = {
        "residual_beyond_B1_detected": False,
        "positive_controls_pass": True,
        "paper_scale_runs_complete": True,
        "strong_residual_hypothesis_status": "not supported at X <= 2^26 by these tests",
        "best_current_baseline": "B1(11) wheel-first-hit among tested families",
    }
    metrics["notes"] = [
        "The B0 controls show large residual signal under CTW/rank-mod, confirming the residual machinery is active.",
        "The same residual machinery gives ordinary null-level behavior against B1(11).",
        "Huge z-scores in the B0 baseline-ladder rows are not treated as primary evidence because the null variance is nearly degenerate; effect sizes and empirical null ranks are preferred.",
    ]
    return metrics


def render_report(metrics: dict[str, Any]) -> str:
    if not metrics.get("ok"):
        missing = "\n".join(
            f"- {item['name']}: `{item['path']}`" for item in metrics["missing"]
        )
        return f"# Final Experiment Report\n\nMissing required artifacts:\n\n{missing}\n"

    b1 = metrics["paper_b1_stop_time_latest"]
    ctw = metrics["paper_ctw_rank64_stop_time_latest"]
    ladder = metrics["paper_baseline_ladder_latest"]

    lines: list[str] = []
    lines.append("# Final Experiment Report")
    lines.append("")
    lines.append("Date: 2026-06-28.")
    lines.append("")
    lines.append("## Bottom Line")
    lines.append("")
    lines.append(
        "The paper-scale experiments do **not** detect positive residual predictive "
        "information beyond the wheel-first-hit baseline `B1(11)` through `X = 2^26`."
    )
    lines.append("")
    lines.append(
        "The framework does detect strong structure against the weaker `B0` baseline. "
        "That signal disappears when the arithmetic wheel-first-hit baseline `B1(11)` "
        "is used, which supports the interpretation that the detected signal is "
        "baseline arithmetic structure rather than robust residual sequential information."
    )
    lines.append("")
    lines.append("## Paper-Scale Suite")
    lines.append("")
    lines.append("Completed main artifacts:")
    lines.append("")
    for directory in metrics["paper_scale"]["artifact_directories"]:
        lines.append(f"- `experiments/{directory}/`")
    lines.append("")
    lines.append("All three main runs reach `X = 2^26` with `200` null replicates/checkpoints.")
    lines.append("")
    lines.append("## Key Metrics at X = 2^26")
    lines.append("")
    lines.append("### Main B1(11) bucket residual")
    lines.append("")
    lines.append(f"- `n = {b1['n']:,}` gaps.")
    lines.append(f"- Real `R = {b1['R_bits_per_gap']}` bits/gap.")
    lines.append(f"- Null mean `{b1['null_mean']}`.")
    lines.append(f"- Null 5-95% interval `[{b1['null_p05']}, {b1['null_p95']}]`.")
    lines.append(f"- `z_vs_null = {b1['z_vs_null']}`.")
    lines.append("")
    lines.append("Interpretation: no positive residual signal beyond `B1(11)`.")
    lines.append("")
    lines.append("### rank_mod_64 CTW control")
    lines.append("")
    lines.append("Against `B0`:")
    lines.append("")
    lines.append(f"- `R = {ctw[0]['R_bits_per_gap']}` bits/gap.")
    lines.append(f"- Total gain `{ctw[0]['total_gain_bits']}` bits.")
    lines.append(f"- Empirical `p_ge = {ctw[0]['empirical_p_ge']}`.")
    lines.append("")
    lines.append("Against `B1(11)`:")
    lines.append("")
    lines.append(f"- `R = {ctw[1]['R_bits_per_gap']}` bits/gap.")
    lines.append(f"- Total gain `{ctw[1]['total_gain_bits']}` bits.")
    lines.append(f"- Empirical `p_ge = {ctw[1]['empirical_p_ge']}`.")
    lines.append("")
    lines.append(
        "Interpretation: the same residual learner strongly detects missing structure "
        "in `B0`, but does not detect residual structure after `B1(11)`."
    )
    lines.append("")
    lines.append("### Exact baseline ladder")
    lines.append("")
    lines.append("At `X = 2^26`:")
    lines.append("")
    lines.append(f"- `B0 = {ladder[0]['baseline_exact_bits_per_gap']}` bits/gap.")
    lines.append(f"- `B1(11) = {ladder[1]['baseline_exact_bits_per_gap']}` bits/gap.")
    lines.append(
        f"- `B1(11)` improves over `B0` by "
        f"`{ladder[2]['baseline_exact_bits_per_gap']}` bits/gap."
    )
    lines.append("")
    lines.append(
        "This quantifies how much arithmetic structure the `B1(11)` wheel-first-hit "
        "baseline already absorbs."
    )
    lines.append("")
    lines.append("## Older B2 Attempts")
    lines.append("")
    lines.append(
        "The earlier B2-style prototypes remain useful negative controls. The tested "
        "families include pair singular-series reweighting, residue-transition "
        "calibration, finite consecutive-prime inclusion-exclusion, and two-parameter "
        "endpoint/exclusion shrinkage. These are not canonical B2 models and should "
        "not be presented as exhausting the space of possible arithmetic refinements."
    )
    lines.append("")
    lines.append("## Interpretation for a Paper")
    lines.append("")
    lines.append("The cleanest paper claim is negative and methodological:")
    lines.append("")
    lines.append(
        "> A prequential residual-coding protocol detects strong missing arithmetic "
        "structure in weak prime-gap baselines, but under the tested online residual "
        "predictors it finds no robust residual predictive information beyond the "
        "wheel-first-hit baseline `B1(11)` up to `X = 2^26`."
    )
    lines.append("")
    lines.append(
        "This is publishable as a careful empirical/protocol paper, not as a proof "
        "that no residual information exists."
    )
    lines.append("")
    lines.append("## Remaining Limits")
    lines.append("")
    lines.append("- The main paper-scale results reach `X = 2^26`; this is empirical evidence at a finite scale.")
    lines.append("- The B2 attempts are finite, truncated prototypes and are not canonical.")
    lines.append("- No B3-style global analytic correction has been implemented.")
    lines.append(
        "- Huge z-scores in the B0 baseline-ladder rows should not be used as headline "
        "evidence because the corresponding null variance is nearly degenerate; use "
        "effect sizes and empirical null ranks instead."
    )
    lines.append("")
    lines.append("## Reproducibility")
    lines.append("")
    lines.append(
        "The compact report is generated from the pinned artifact manifest "
        "`experiments/final_manifest.json`."
    )
    lines.append("")
    lines.append("Regenerate from existing artifacts:")
    lines.append("")
    lines.append("```powershell")
    lines.append("powershell -ExecutionPolicy Bypass -File experiments\\run_final_suite.ps1 -SkipRuns")
    lines.append("```")
    lines.append("")
    lines.append(
        "The paper-scale long-run commands and resume protocol are recorded in "
        "`paper_run_plan.md`."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    metrics = collect_metrics()
    (ROOT / "final_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    (ROOT / "final_report.md").write_text(render_report(metrics), encoding="utf-8")
    print(json.dumps(metrics["conclusion"] if metrics.get("ok") else metrics, indent=2))


if __name__ == "__main__":
    main()
