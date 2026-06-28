#!/usr/bin/env python3
"""
Validate pinned paper-scale artifacts used by the final report.

This script is intentionally conservative:
- it reads only artifacts pinned in experiments/final_manifest.json;
- it does not discover experiment folders implicitly;
- it does not rerun long simulations;
- it fails if required files, metadata, checkpoint counts, or headline metrics drift.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
MANIFEST_PATH = ROOT / "final_manifest.json"
METRICS_PATH = ROOT / "final_metrics.json"

EXPECTED_MAX_EXP = 26
EXPECTED_X = 1 << EXPECTED_MAX_EXP
EXPECTED_NULLS = 200
EXPECTED_SEED = 20260616
EXPECTED_TRAIN_WINDOWS = 3
EXPECTED_REQUIRED = {
    "paper_b1_stop_time",
    "paper_ctw_rank64_stop_time",
    "paper_baseline_ladder",
}


class ValidationError(Exception):
    """Raised when a reproducibility invariant is violated."""


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ValidationError(f"missing CSV file: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValidationError(f"empty CSV file: {path}")
    return rows


def as_float(row: dict[str, str], key: str, path: Path) -> float:
    if key not in row:
        raise ValidationError(f"{path} is missing required column {key!r}")
    return float(row[key])


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValidationError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15):
        raise ValidationError(f"{label}: expected {expected!r}, got {actual!r}")


def latest_row(rows: list[dict[str, str]], path: Path) -> dict[str, str]:
    return max(rows, key=lambda row: as_float(row, "exp", path))


def rows_where(rows: list[dict[str, str]], key: str, value: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key) == value]


def artifact_path(spec: dict[str, Any]) -> Path:
    return ROOT / spec["path"]


def metadata_path(spec: dict[str, Any]) -> Path | None:
    value = spec.get("metadata_path")
    return ROOT / value if value else None


def expected_testable_exp_count(metadata: dict[str, Any]) -> int:
    min_exp = int(metadata["min_exp"])
    max_exp = int(metadata["max_exp"])
    train_windows = int(metadata.get("train_windows", EXPECTED_TRAIN_WINDOWS))
    first_test_exp = min_exp + train_windows
    return max_exp - first_test_exp + 1


def validate_metadata(name: str, metadata: dict[str, Any]) -> None:
    assert_equal(int(metadata["max_exp"]), EXPECTED_MAX_EXP, f"{name} metadata max_exp")
    assert_equal(
        int(metadata.get("train_windows", EXPECTED_TRAIN_WINDOWS)),
        EXPECTED_TRAIN_WINDOWS,
        f"{name} metadata train_windows",
    )
    assert_equal(
        int(metadata.get("nulls", EXPECTED_NULLS)),
        EXPECTED_NULLS,
        f"{name} metadata nulls",
    )
    assert_equal(
        int(metadata.get("seed", EXPECTED_SEED)),
        EXPECTED_SEED,
        f"{name} metadata seed",
    )


def validate_checkpoint(path: Path, metadata: dict[str, Any]) -> None:
    rows = read_csv(path)
    expected_rows_per_null = expected_testable_exp_count(metadata)

    per_null: Counter[int] = Counter()
    exps_by_null: dict[int, set[int]] = defaultdict(set)
    for row in rows:
        if "null_index" not in row:
            raise ValidationError(f"{path} is missing required column 'null_index'")
        null_index = int(row["null_index"])
        exp = int(float(row["exp"]))
        per_null[null_index] += 1
        exps_by_null[null_index].add(exp)

    assert_equal(len(per_null), EXPECTED_NULLS, f"{path} unique null_index count")

    bad_counts = {
        idx: count for idx, count in per_null.items() if count != expected_rows_per_null
    }
    if bad_counts:
        sample = dict(sorted(bad_counts.items())[:5])
        raise ValidationError(
            f"{path} has wrong rows per null; expected "
            f"{expected_rows_per_null}, sample failures: {sample}"
        )

    expected_exps = set(
        range(
            int(metadata["min_exp"])
            + int(metadata.get("train_windows", EXPECTED_TRAIN_WINDOWS)),
            int(metadata["max_exp"]) + 1,
        )
    )
    bad_exps = {
        idx: sorted(exps)
        for idx, exps in exps_by_null.items()
        if exps != expected_exps
    }
    if bad_exps:
        sample = dict(sorted(bad_exps.items())[:3])
        raise ValidationError(
            f"{path} has wrong exp coverage; expected {sorted(expected_exps)}, "
            f"sample failures: {sample}"
        )


def validate_artifact_csv(name: str, path: Path) -> list[dict[str, str]]:
    rows = read_csv(path)
    max_exp = int(as_float(latest_row(rows, path), "exp", path))
    assert_equal(max_exp, EXPECTED_MAX_EXP, f"{name} latest exp")

    latest = latest_row(rows, path)
    if "X" in latest:
        assert_equal(int(as_float(latest, "X", path)), EXPECTED_X, f"{name} latest X")
    return rows


def validate_manifest_and_artifacts() -> dict[str, Any]:
    manifest = read_json(MANIFEST_PATH)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValidationError("final_manifest.json has no artifacts object")

    required_keys = {
        key for key, spec in artifacts.items() if bool(spec.get("required", True))
    }
    assert_equal(required_keys, EXPECTED_REQUIRED, "required paper-scale artifact keys")

    for key in sorted(EXPECTED_REQUIRED):
        spec = artifacts[key]
        name = spec["name"]
        rows = validate_artifact_csv(name, artifact_path(spec))

        meta_path = metadata_path(spec)
        if meta_path is None:
            raise ValidationError(f"{name} has no metadata_path in manifest")
        metadata = read_json(meta_path)
        validate_metadata(name, metadata)

        checkpoint_files: list[str] = []
        if metadata.get("checkpoint_file"):
            checkpoint_files.append(metadata["checkpoint_file"])
        checkpoint_files.extend(metadata.get("checkpoint_files", []))

        if not checkpoint_files:
            raise ValidationError(f"{name} has no checkpoint file recorded in metadata")

        for checkpoint_file in checkpoint_files:
            validate_checkpoint(meta_path.parent / checkpoint_file, metadata)

        # Sanity-check that aggregated CSV covers all testable exponents.
        expected_count = expected_testable_exp_count(metadata)
        if key == "paper_ctw_rank64_stop_time":
            for baseline in ("B0", "B1(11)"):
                baseline_rows = rows_where(rows, "baseline", baseline)
                assert_equal(
                    len(baseline_rows),
                    expected_count,
                    f"{name} aggregated rows for {baseline}",
                )
        elif key == "paper_baseline_ladder":
            for baseline in ("B0", "B1(11)"):
                baseline_rows = rows_where(rows, "baseline", baseline)
                assert_equal(
                    len(baseline_rows),
                    expected_count,
                    f"{name} aggregated rows for {baseline}",
                )
        else:
            assert_equal(len(rows), expected_count, f"{name} aggregated row count")

    return manifest


def validate_metrics() -> None:
    metrics = read_json(METRICS_PATH)
    assert_equal(bool(metrics.get("ok")), True, "final_metrics ok")

    paper_scale = metrics["paper_scale"]
    assert_equal(int(paper_scale["max_exp"]), EXPECTED_MAX_EXP, "paper_scale max_exp")
    assert_equal(int(paper_scale["X"]), EXPECTED_X, "paper_scale X")
    assert_equal(int(paper_scale["nulls"]), EXPECTED_NULLS, "paper_scale nulls")
    assert_equal(int(paper_scale["seed"]), EXPECTED_SEED, "paper_scale seed")

    b1_path = ROOT / "paper_b1_y11_depth4_stop_time_x26_n200" / "b1_u1_real_vs_null.csv"
    b1_latest = latest_row(read_csv(b1_path), b1_path)
    b1_metrics = metrics["paper_b1_stop_time_latest"]
    assert_equal(int(as_float(b1_latest, "n", b1_path)), int(b1_metrics["n"]), "B1 latest n")
    assert_close(as_float(b1_latest, "R_bits_per_gap", b1_path), float(b1_metrics["R_bits_per_gap"]), "B1 latest R")
    assert_close(as_float(b1_latest, "null_mean", b1_path), float(b1_metrics["null_mean"]), "B1 latest null_mean")
    assert_close(as_float(b1_latest, "z_vs_null", b1_path), float(b1_metrics["z_vs_null"]), "B1 latest z")

    ctw_path = ROOT / "paper_ctw_rank64_depth1_stop_time_x26_n200" / "ctw_symbol_ladder.csv"
    ctw_rows = read_csv(ctw_path)
    ctw_metrics = {entry["label"]: entry for entry in metrics["paper_ctw_rank64_stop_time_latest"]}
    for baseline in ("B0", "B1(11)"):
        row = latest_row(rows_where(ctw_rows, "baseline", baseline), ctw_path)
        entry = ctw_metrics[baseline]
        assert_close(as_float(row, "R_bits_per_gap", ctw_path), float(entry["R_bits_per_gap"]), f"CTW {baseline} latest R")
        assert_close(as_float(row, "total_gain_bits", ctw_path), float(entry["total_gain_bits"]), f"CTW {baseline} latest total_gain_bits")
        assert_close(as_float(row, "empirical_p_ge", ctw_path), float(entry["empirical_p_ge"]), f"CTW {baseline} latest empirical_p_ge")

    ladder_path = ROOT / "paper_ladder_b0_b1_y11_x26_n200" / "baseline_ladder.csv"
    ladder_rows = read_csv(ladder_path)
    ladder_metrics = {
        entry["label"]: entry for entry in metrics["paper_baseline_ladder_latest"]
    }
    for baseline in ("B0", "B1(11)"):
        row = latest_row(rows_where(ladder_rows, "baseline", baseline), ladder_path)
        entry = ladder_metrics[baseline]
        assert_close(as_float(row, "B1_exact_bits_per_gap", ladder_path), float(entry["baseline_exact_bits_per_gap"]), f"ladder {baseline} exact bits/gap")
        assert_close(as_float(row, "U1_exact_bits_per_gap", ladder_path), float(entry["residual_exact_bits_per_gap"]), f"ladder {baseline} residual bits/gap")

    b0 = float(ladder_metrics["B0"]["baseline_exact_bits_per_gap"])
    b1 = float(ladder_metrics["B1(11)"]["baseline_exact_bits_per_gap"])
    improvement = float(ladder_metrics["B0 minus B1(11)"]["baseline_exact_bits_per_gap"])
    assert_close(b0 - b1, improvement, "B0 minus B1(11) improvement")


def main() -> int:
    try:
        validate_manifest_and_artifacts()
        validate_metrics()
    except ValidationError as exc:
        print(f"artifact validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "artifact validation passed: required paper-scale CSV, metadata, "
        "checkpoint counts, and final metrics are consistent"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
