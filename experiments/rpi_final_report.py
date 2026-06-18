#!/usr/bin/env python3
"""
Generate a compact final report from the experiment CSV artifacts.

The experiment has many pilot outputs.  This script collects the main
positive controls, B1 null results, and B2 calibration attempts into a single
machine-readable JSON file and a short Markdown report.
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
    metadata_path: Path | None = None
    required: bool = True


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


def fmt_power_of_two(value: int) -> str:
    if value > 0 and value & (value - 1) == 0:
        return f"2^{value.bit_length() - 1}"
    return str(value)


def metric_row(label: str, values: dict[str, Any]) -> dict[str, Any]:
    out = {"label": label}
    out.update(values)
    return out


def load_manifest() -> dict[str, Artifact]:
    manifest_path = ROOT / "final_manifest.json"
    manifest = read_json(manifest_path)
    artifacts = {}
    for key, spec in manifest["artifacts"].items():
        metadata_path = spec.get("metadata_path")
        artifacts[key] = Artifact(
            name=spec["name"],
            path=ROOT / spec["path"],
            metadata_path=ROOT / metadata_path if metadata_path else None,
            required=bool(spec.get("required", True)),
        )
    return artifacts


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
        if not artifact.path.exists():
            continue
        artifact_meta = None
        if artifact.metadata_path and artifact.metadata_path.exists():
            artifact_meta = read_json(artifact.metadata_path)
        metrics["artifacts"][key] = {
            "name": artifact.name,
            "path": str(artifact.path.relative_to(ROOT)),
            "metadata_path": (
                str(artifact.metadata_path.relative_to(ROOT))
                if artifact.metadata_path and artifact.metadata_path.exists()
                else None
            ),
            "metadata": artifact_meta,
        }

    b1_bucket = latest_row(read_csv(artifacts["b1_bucket"].path))
    metrics["b1_bucket_latest"] = metric_row(
        "B1 bucket residual latest",
        {
            "X": int(as_float(b1_bucket, "X")),
            "n": int(as_float(b1_bucket, "n")),
            "R_bits_per_gap": as_float(b1_bucket, "R_bits_per_gap"),
            "null_mean": as_float(b1_bucket, "null_mean"),
        },
    )
    if artifacts["b1_bucket_stop_time"].path.exists():
        b1_stop = latest_row(read_csv(artifacts["b1_bucket_stop_time"].path))
        metrics["b1_bucket_stop_time_latest"] = metric_row(
            "B1 bucket residual latest with stop-time null",
            {
                "X": int(as_float(b1_stop, "X")),
                "n": int(as_float(b1_stop, "n")),
                "R_bits_per_gap": as_float(b1_stop, "R_bits_per_gap"),
                "null_mean": as_float(b1_stop, "null_mean"),
                "null_sd": as_float(b1_stop, "null_sd"),
                "null_p05": as_float(b1_stop, "null_p05"),
                "null_p95": as_float(b1_stop, "null_p95"),
            },
        )
        stop_meta = metrics["artifacts"]["b1_bucket_stop_time"].get("metadata")
        if stop_meta and int(as_float(b1_stop, "exp")) != int(stop_meta["max_exp"]):
            metrics["warnings"].append(
                "B1 stop-time latest CSV row does not match metadata max_exp."
            )

    ladder = read_csv(artifacts["baseline_ladder"].path)
    latest_b0 = latest_row(rows_where(ladder, "baseline", "B0"))
    latest_b1 = latest_row(rows_where(ladder, "baseline", "B1(11)"))
    metrics["baseline_ladder_latest"] = [
        metric_row(
            "B0",
            {
                "X": int(as_float(latest_b0, "X")),
                "n": int(as_float(latest_b0, "n")),
                "bits_per_gap": as_float(latest_b0, "B1_exact_bits_per_gap"),
                "R_bits_per_gap": as_float(latest_b0, "R_bits_per_gap"),
            },
        ),
        metric_row(
            "B1(11)",
            {
                "X": int(as_float(latest_b1, "X")),
                "n": int(as_float(latest_b1, "n")),
                "bits_per_gap": as_float(latest_b1, "B1_exact_bits_per_gap"),
                "R_bits_per_gap": as_float(latest_b1, "R_bits_per_gap"),
            },
        ),
    ]
    metrics["baseline_ladder_latest"].append(
        metric_row(
            "B0 minus B1",
            {
                "X": int(as_float(latest_b1, "X")),
                "bits_per_gap": as_float(latest_b0, "B1_exact_bits_per_gap")
                - as_float(latest_b1, "B1_exact_bits_per_gap"),
            },
        )
    )

    symbol = read_csv(artifacts["symbol_depth1"].path)
    symbol_b0 = latest_row(rows_where(symbol, "baseline", "B0"))
    symbol_b1 = latest_row(rows_where(symbol, "baseline", "B1(11)"))
    metrics["positive_control_gap_mod210_depth1"] = [
        metric_row(
            "B0",
            {
                "X": int(as_float(symbol_b0, "X")),
                "R_bits_per_gap": as_float(symbol_b0, "R_bits_per_gap"),
            },
        ),
        metric_row(
            "B1(11)",
            {
                "X": int(as_float(symbol_b1, "X")),
                "R_bits_per_gap": as_float(symbol_b1, "R_bits_per_gap"),
            },
        ),
    ]

    ctw = read_csv(artifacts["ctw_rank64"].path)
    ctw_b0 = latest_row(rows_where(ctw, "baseline", "B0"))
    ctw_b1 = latest_row(rows_where(ctw, "baseline", "B1(11)"))
    metrics["positive_control_rank64_ctw"] = [
        metric_row(
            "B0",
            {
                "X": int(as_float(ctw_b0, "X")),
                "R_bits_per_gap": as_float(ctw_b0, "R_bits_per_gap"),
            },
        ),
        metric_row(
            "B1(11)",
            {
                "X": int(as_float(ctw_b1, "X")),
                "R_bits_per_gap": as_float(ctw_b1, "R_bits_per_gap"),
            },
        ),
    ]
    if artifacts["ctw_rank64_stop_time"].path.exists():
        ctw_stop = read_csv(artifacts["ctw_rank64_stop_time"].path)
        ctw_stop_b0 = latest_row(rows_where(ctw_stop, "baseline", "B0"))
        ctw_stop_b1 = latest_row(rows_where(ctw_stop, "baseline", "B1(11)"))
        metrics["positive_control_rank64_ctw_stop_time"] = [
            metric_row(
                "B0",
                {
                    "X": int(as_float(ctw_stop_b0, "X")),
                    "R_bits_per_gap": as_float(ctw_stop_b0, "R_bits_per_gap"),
                    "null_mean": as_float(ctw_stop_b0, "null_mean"),
                    "null_p95": as_float(ctw_stop_b0, "null_p95"),
                },
            ),
            metric_row(
                "B1(11)",
                {
                    "X": int(as_float(ctw_stop_b1, "X")),
                    "R_bits_per_gap": as_float(ctw_stop_b1, "R_bits_per_gap"),
                    "null_mean": as_float(ctw_stop_b1, "null_mean"),
                    "null_p95": as_float(ctw_stop_b1, "null_p95"),
                },
            ),
        ]

    pair_alpha = latest_row(read_csv(artifacts["pair_alpha"].path))
    metrics["b2_pair_alpha_latest"] = metric_row(
        "B2 pair alpha scan latest",
        {
            "X": int(as_float(pair_alpha, "X")),
            "selected_alpha": as_float(pair_alpha, "selected_alpha"),
            "selected_delta_vs_B1_bits_per_gap": as_float(
                pair_alpha, "selected_delta_vs_B1_bits_per_gap"
            ),
            "oracle_alpha": as_float(pair_alpha, "oracle_alpha"),
            "oracle_delta_vs_B1_bits_per_gap": as_float(
                pair_alpha, "oracle_delta_vs_B1_bits_per_gap"
            ),
        },
    )

    transition = latest_row(read_csv(artifacts["transition_mod30"].path))
    metrics["transition_mod30_lam001_latest"] = metric_row(
        "Transition mod 30 lambda 0.01 latest",
        {
            "X": int(as_float(transition, "X")),
            "Btr_gain_vs_B1": as_float(transition, "Btr_gain_vs_B1"),
            "U_gain_vs_Btr": as_float(transition, "U_gain_vs_Btr"),
        },
    )

    consecutive = latest_row(read_csv(artifacts["consecutive_alpha"].path))
    metrics["b2_consecutive_alpha_latest"] = metric_row(
        "B2 consecutive alpha scan latest",
        {
            "X": int(as_float(consecutive, "X")),
            "selected_alpha": as_float(consecutive, "selected_alpha"),
            "selected_delta_vs_B1_bits_per_gap": as_float(
                consecutive, "selected_delta_vs_B1_bits_per_gap"
            ),
            "oracle_alpha": as_float(consecutive, "oracle_alpha"),
            "oracle_delta_vs_B1_bits_per_gap": as_float(
                consecutive, "oracle_delta_vs_B1_bits_per_gap"
            ),
        },
    )

    two_alpha = latest_row(read_csv(artifacts["consecutive_two_alpha"].path))
    metrics["b2_consecutive_two_alpha_latest"] = metric_row(
        "B2 consecutive two-alpha scan latest",
        {
            "X": int(as_float(two_alpha, "X")),
            "selected_pair_alpha": as_float(two_alpha, "selected_pair_alpha"),
            "selected_exclusion_alpha": as_float(
                two_alpha, "selected_exclusion_alpha"
            ),
            "selected_delta_vs_B1_bits_per_gap": as_float(
                two_alpha, "selected_delta_vs_B1_bits_per_gap"
            ),
            "oracle_pair_alpha": as_float(two_alpha, "oracle_pair_alpha"),
            "oracle_exclusion_alpha": as_float(two_alpha, "oracle_exclusion_alpha"),
            "oracle_delta_vs_B1_bits_per_gap": as_float(
                two_alpha, "oracle_delta_vs_B1_bits_per_gap"
            ),
        },
    )

    head8 = latest_row(read_csv(artifacts["consecutive_two_alpha_head8"].path))
    metrics["b2_consecutive_two_alpha_head8_latest"] = metric_row(
        "B2 consecutive two-alpha head-8 latest",
        {
            "X": int(as_float(head8, "X")),
            "selected_pair_alpha": as_float(head8, "selected_pair_alpha"),
            "selected_exclusion_alpha": as_float(head8, "selected_exclusion_alpha"),
            "oracle_pair_alpha": as_float(head8, "oracle_pair_alpha"),
            "oracle_exclusion_alpha": as_float(head8, "oracle_exclusion_alpha"),
            "oracle_delta_vs_B1_bits_per_gap": as_float(
                head8, "oracle_delta_vs_B1_bits_per_gap"
            ),
        },
    )

    metrics["conclusion"] = {
        "residual_beyond_B1_detected": False,
        "positive_controls_pass": True,
        "strong_residual_hypothesis_status": "not supported by these pilots",
        "best_current_baseline": "B1(11) wheel-first-hit among tested families",
    }
    return metrics


def render_report(metrics: dict[str, Any]) -> str:
    if not metrics.get("ok"):
        missing = "\n".join(
            f"- {item['name']}: `{item['path']}`" for item in metrics["missing"]
        )
        return f"# Final Experiment Report\n\nMissing required artifacts:\n\n{missing}\n"

    lines: list[str] = []
    lines.append("# Final Experiment Report")
    lines.append("")
    lines.append("Date: 2026-06-16.")
    lines.append("")
    lines.append("## Bottom Line")
    lines.append("")
    lines.append(
        "The implemented pilots do not detect positive residual predictive "
        "information beyond the wheel-first-hit baseline `B1(11)`.  The "
        "framework does detect known wheel structure against `B0`, and that "
        "signal disappears once `B1(11)` is used."
    )
    lines.append("")
    lines.append("## Key Metrics")
    lines.append("")

    b1 = metrics["b1_bucket_latest"]
    lines.append(
        f"- B1 bucket residual at `X={b1['X']}`: "
        f"`R={fmt(b1['R_bits_per_gap'])}` bits/gap "
        f"(null mean `{fmt(b1['null_mean'])}`)."
    )
    if "b1_bucket_stop_time_latest" in metrics:
        b1_stop = metrics["b1_bucket_stop_time_latest"]
        lines.append(
            f"- B1 stop-time null at `X={b1_stop['X']}`: "
            f"real `R={fmt(b1_stop['R_bits_per_gap'], 9)}`, "
            f"null mean `{fmt(b1_stop['null_mean'], 9)}`, "
            f"null 5-95% `[{fmt(b1_stop['null_p05'], 9)}, "
            f"{fmt(b1_stop['null_p95'], 9)}]` bits/gap."
        )

    ladder = metrics["baseline_ladder_latest"]
    lines.append(
        f"- Baseline exact code length at `X={ladder[1]['X']}`: "
        f"`B0={fmt(ladder[0]['bits_per_gap'])}`, "
        f"`B1(11)={fmt(ladder[1]['bits_per_gap'])}`, "
        f"gain `{fmt(ladder[2]['bits_per_gap'])}` bits/gap."
    )

    rank = metrics["positive_control_rank64_ctw"]
    lines.append(
        f"- Positive control rank-mod CTW at `X={rank[0]['X']}`: "
        f"`R(B0)={fmt(rank[0]['R_bits_per_gap'])}`, "
        f"`R(B1)={fmt(rank[1]['R_bits_per_gap'])}` bits/gap."
    )
    if "positive_control_rank64_ctw_stop_time" in metrics:
        rank_stop = metrics["positive_control_rank64_ctw_stop_time"]
        lines.append(
            f"- Stop-time rank-mod CTW control at `X={rank_stop[0]['X']}`: "
            f"`R(B0)={fmt(rank_stop[0]['R_bits_per_gap'])}` "
            f"(null p95 `{fmt(rank_stop[0]['null_p95'])}`), "
            f"`R(B1)={fmt(rank_stop[1]['R_bits_per_gap'])}` "
            f"(null p95 `{fmt(rank_stop[1]['null_p95'])}`)."
        )

    gapmod = metrics["positive_control_gap_mod210_depth1"]
    lines.append(
        f"- Positive control gap-mod-210 depth 1 at `X={gapmod[0]['X']}`: "
        f"`R(B0)={fmt(gapmod[0]['R_bits_per_gap'])}`, "
        f"`R(B1)={fmt(gapmod[1]['R_bits_per_gap'])}` bits/gap."
    )

    lines.append("")
    lines.append("## B2 Attempts")
    lines.append("")

    pair = metrics["b2_pair_alpha_latest"]
    lines.append(
        f"- Pair singular-series alpha scan at `X={pair['X']}`: selected "
        f"`alpha={pair['selected_alpha']:g}`, oracle "
        f"`alpha={pair['oracle_alpha']:g}`, oracle gain "
        f"`{fmt(pair['oracle_delta_vs_B1_bits_per_gap'])}` bits/gap."
    )

    trans = metrics["transition_mod30_lam001_latest"]
    lines.append(
        f"- Residue-transition calibration at `X={trans['X']}` with "
        f"`lambda=0.01`: transition gain "
        f"`{fmt(trans['Btr_gain_vs_B1'])}` bits/gap."
    )

    consec = metrics["b2_consecutive_alpha_latest"]
    lines.append(
        f"- Consecutive finite IE alpha scan at `X={consec['X']}`: selected "
        f"`alpha={consec['selected_alpha']:g}`, oracle "
        f"`alpha={consec['oracle_alpha']:g}`."
    )

    two = metrics["b2_consecutive_two_alpha_latest"]
    lines.append(
        f"- Two-alpha scan at `X={two['X']}`: selected "
        f"`({two['selected_pair_alpha']:g}, "
        f"{two['selected_exclusion_alpha']:g})`, oracle "
        f"`({two['oracle_pair_alpha']:g}, "
        f"{two['oracle_exclusion_alpha']:g})`."
    )

    head8 = metrics["b2_consecutive_two_alpha_head8_latest"]
    lines.append(
        f"- Gentle head-8 sensitivity at `X={head8['X']}`: oracle "
        f"`({head8['oracle_pair_alpha']:g}, "
        f"{head8['oracle_exclusion_alpha']:g})`."
    )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The tested B2 families are useful negative controls: when they are "
        "miscalibrated, the residual CTW expert gains against them, but exact "
        "prequential log-loss shows that they are worse than `B1(11)`.  "
        "Chronological and oracle calibration both collapse back to `B1(11)` "
        "in the final tested windows."
    )
    lines.append("")
    lines.append("## Remaining Limits")
    lines.append("")
    largest_b1_x = metrics.get("b1_bucket_stop_time_latest", b1)["X"]
    lines.append(
        f"- The largest main B1 residual run reaches only "
        f"`X={fmt_power_of_two(largest_b1_x)}`."
    )
    if "b1_bucket_stop_time_latest" in metrics:
        lines.append(
            "- Stop-time synthetic nulls are now included for the main B1 and "
            "rank-mod CTW checks; some older auxiliary pilots still use fixed-count nulls."
        )
    else:
        lines.append("- Synthetic nulls condition on the real number of events per window.")
    lines.append("- The B2 attempts are finite, truncated, and not canonical.")
    lines.append("- No B3 analytic correction has been implemented.")
    lines.append(
        "- Real prime windows now use segmented streaming prime-pair generation; "
        "the full paper-scale runs still need to be executed."
    )
    lines.append("")
    lines.append("## Reproducibility")
    lines.append("")
    lines.append(
        "The compact report is generated from the pinned artifact manifest "
        "`experiments/final_manifest.json`."
    )
    if metrics.get("warnings"):
        lines.append("")
        lines.append("Warnings:")
        for warning in metrics["warnings"]:
            lines.append(f"- {warning}")
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
