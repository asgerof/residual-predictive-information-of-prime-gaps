#!/usr/bin/env python3
"""
Audit paper-scale robustness from committed artifacts.

This is a second layer after validate_paper_artifacts.py. The validator checks
that the pinned files are complete and internally consistent. This audit checks
that the paper's qualitative conclusion is not an endpoint-only accident:

- the B1(11) bucket residual stays inside the 5-95% stop-time null band across
  every tested dyadic exponent;
- the rank_mod_64 CTW positive control separates strongly from the B0 null at
  every tested exponent;
- the same CTW residual does not separate from the B1(11) null;
- the exact baseline ladder keeps B1(11) below B0 at every tested exponent.

The script reads only artifacts pinned in experiments/final_manifest.json and
performs no long simulation or implicit artifact discovery.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "final_manifest.json"

MAX_ABS_Z_FOR_B1_BUCKET = 1.0
CTW_POSITIVE_CONTROL_MAX_P = 0.01
CTW_B1_NULL_MIN_P = 0.05
CTW_B1_NULL_MAX_P = 0.95


class RobustnessError(Exception):
    """Raised when a paper-scale robustness invariant is violated."""


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RobustnessError(f"missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RobustnessError(f"missing CSV file: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RobustnessError(f"empty CSV file: {path}")
    return rows


def as_float(row: dict[str, str], key: str, path: Path) -> float:
    if key not in row:
        raise RobustnessError(f"{path} is missing required column {key!r}")
    return float(row[key])


def exp_of(row: dict[str, str], path: Path) -> int:
    return int(as_float(row, "exp", path))


def sorted_by_exp(rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: exp_of(row, path))


def rows_where(rows: list[dict[str, str]], key: str, value: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key) == value]


def artifact_path(manifest: dict[str, Any], key: str) -> Path:
    artifacts = manifest.get("artifacts", {})
    if key not in artifacts:
        raise RobustnessError(f"final_manifest.json is missing artifact key {key!r}")
    return ROOT / artifacts[key]["path"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RobustnessError(message)


def require_inside_null_band(rows: list[dict[str, str]], path: Path, label: str) -> None:
    outside: list[tuple[int, float, float, float]] = []
    for row in sorted_by_exp(rows, path):
        value = as_float(row, "R_bits_per_gap", path)
        low = as_float(row, "null_p05", path)
        high = as_float(row, "null_p95", path)
        if not low <= value <= high:
            outside.append((exp_of(row, path), value, low, high))

    if outside:
        sample = outside[:5]
        raise RobustnessError(
            f"{label} leaves the 5-95% null band; sample failures: {sample}"
        )


def validate_b1_bucket(path: Path) -> str:
    rows = sorted_by_exp(read_csv(path), path)
    require_inside_null_band(rows, path, "B1(11) bucket residual")

    z_values = [abs(as_float(row, "z_vs_null", path)) for row in rows]
    max_abs_z = max(z_values)
    require(
        max_abs_z <= MAX_ABS_Z_FOR_B1_BUCKET,
        f"B1(11) bucket residual max |z| is {max_abs_z}, "
        f"above {MAX_ABS_Z_FOR_B1_BUCKET}",
    )

    return (
        f"B1(11) bucket residual: {len(rows)} exponents stay inside the "
        f"5-95% stop-time null band; max |z| = {max_abs_z:.3f}"
    )


def validate_ctw_control(path: Path) -> str:
    rows = read_csv(path)
    b0_rows = sorted_by_exp(rows_where(rows, "baseline", "B0"), path)
    b1_rows = sorted_by_exp(rows_where(rows, "baseline", "B1(11)"), path)

    require(b0_rows, f"{path} has no B0 rows")
    require(b1_rows, f"{path} has no B1(11) rows")
    require(
        [exp_of(row, path) for row in b0_rows] == [exp_of(row, path) for row in b1_rows],
        "CTW B0 and B1(11) rows cover different exponents",
    )

    weak_control_failures: list[tuple[int, float, float, float]] = []
    for row in b0_rows:
        exp = exp_of(row, path)
        value = as_float(row, "R_bits_per_gap", path)
        high = as_float(row, "null_p95", path)
        empirical_p_ge = as_float(row, "empirical_p_ge", path)
        total_gain = as_float(row, "total_gain_bits", path)
        if not (value > high and empirical_p_ge <= CTW_POSITIVE_CONTROL_MAX_P and total_gain > 0.0):
            weak_control_failures.append((exp, value, high, empirical_p_ge))

    if weak_control_failures:
        raise RobustnessError(
            "CTW positive control does not separate from B0 at every exponent; "
            f"sample failures: {weak_control_failures[:5]}"
        )

    require_inside_null_band(b1_rows, path, "rank_mod_64 CTW under B1(11)")

    b1_p_failures: list[tuple[int, float]] = []
    for row in b1_rows:
        empirical_p_ge = as_float(row, "empirical_p_ge", path)
        if not CTW_B1_NULL_MIN_P <= empirical_p_ge <= CTW_B1_NULL_MAX_P:
            b1_p_failures.append((exp_of(row, path), empirical_p_ge))

    if b1_p_failures:
        raise RobustnessError(
            "CTW B1(11) null p-values are not central across exponents; "
            f"sample failures: {b1_p_failures[:5]}"
        )

    min_b0_gain = min(as_float(row, "total_gain_bits", path) for row in b0_rows)
    return (
        f"rank_mod_64 CTW: B0 positive control separates at all {len(b0_rows)} "
        f"exponents with min gain {min_b0_gain:.3f} bits; B1(11) rows stay "
        "inside the 5-95% null band with central empirical p-values"
    )


def validate_baseline_ladder(path: Path) -> str:
    rows = read_csv(path)
    b0_by_exp = {exp_of(row, path): row for row in rows_where(rows, "baseline", "B0")}
    b1_by_exp = {exp_of(row, path): row for row in rows_where(rows, "baseline", "B1(11)")}

    require(b0_by_exp, f"{path} has no B0 rows")
    require(b1_by_exp, f"{path} has no B1(11) rows")
    require(
        set(b0_by_exp) == set(b1_by_exp),
        "baseline ladder B0 and B1(11) rows cover different exponents",
    )

    improvements: list[float] = []
    failures: list[tuple[int, float, float]] = []
    for exp in sorted(b0_by_exp):
        b0_bits = as_float(b0_by_exp[exp], "B1_exact_bits_per_gap", path)
        b1_bits = as_float(b1_by_exp[exp], "B1_exact_bits_per_gap", path)
        improvement = b0_bits - b1_bits
        improvements.append(improvement)
        if improvement <= 0.0:
            failures.append((exp, b0_bits, b1_bits))

    if failures:
        raise RobustnessError(
            "B1(11) does not improve on B0 at every ladder exponent; "
            f"sample failures: {failures[:5]}"
        )

    return (
        f"baseline ladder: B1(11) improves on B0 at all {len(improvements)} "
        f"exponents; improvement range = [{min(improvements):.3f}, "
        f"{max(improvements):.3f}] bits/gap"
    )


def main() -> int:
    try:
        manifest = read_json(MANIFEST_PATH)
        summaries = [
            validate_b1_bucket(artifact_path(manifest, "paper_b1_stop_time")),
            validate_ctw_control(artifact_path(manifest, "paper_ctw_rank64_stop_time")),
            validate_baseline_ladder(artifact_path(manifest, "paper_baseline_ladder")),
        ]
    except RobustnessError as exc:
        print(f"robustness audit failed: {exc}", file=sys.stderr)
        return 1

    print("paper-scale robustness audit passed")
    for summary in summaries:
        print(f"- {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
