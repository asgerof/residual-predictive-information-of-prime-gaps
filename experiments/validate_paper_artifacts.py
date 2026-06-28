#!/usr/bin/env python3
"""
Validate pinned paper-scale artifacts used by the final report.

This script is intentionally conservative:
- it reads only artifacts pinned in experiments/final_manifest.json;
- it does not discover experiment folders implicitly;
- it does not rerun long simulations;
- it fails if required files, metadata, checkpoint counts, or headline metrics drift;
- it warns, but does not fail, when optional/pilot artifacts or generated figures are absent.
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
FIGURE_SCRIPT_PATH = ROOT / "rpi_paper_figures.py"
FIGURE_README_PATH = REPO_ROOT / "paper_figures" / "README.md"
FIGURE_OUT_DIR = REPO_ROOT / "paper_figures"

EXPECTED_MAX_EXP = 26
EXPECTED_X = 1 << EXPECTED_MAX_EXP
EXPECTED_NULLS = 200
EXPECTED_SEED = 20260616
EXPECTED_TRAIN_WINDOWS = 3
EXPECTED_MANIFEST_SCHEMA_VERSION = 2
EXPECTED_REQUIRED = {
    "paper_b1_stop_time",
    "paper_ctw_rank64_stop_time",
    "paper_baseline_ladder",
}
EXPECTED_FIGURES = {
    "figure_1_b1_residual_stop_time.svg": [
        "paper_b1_y11_depth4_stop_time_x26_n200",
        "b1_u1_real_vs_null.csv",
    ],
    "figure_2_ctw_positive_control.svg": [
        "paper_ctw_rank64_depth1_stop_time_x26_n200",
        "ctw_symbol_ladder.csv",
    ],
    "figure_3_baseline_ladder_bits.svg": [
        "paper_ladder_b0_b1_y11_x26_n200",
        "baseline_ladder.csv",
    ],
}

WARNINGS: list[str] = []


class ValidationError(Exception):
    """Raised when a reproducibility invariant is violated."""


def warn(message: str) -> None:
    WARNINGS.append(message)


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


def try_read_csv(path: Path) -> list[dict[str, str]] | None:
    try:
        return read_csv(path)
    except Exception as exc:  # warning path only; keep optional artifacts non-fatal
        warn(f"optional/readability issue for {path}: {exc}")
        return None


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
    if not rows:
        raise ValidationError(f"no rows available in {path}")
    return max(rows, key=lambda row: as_float(row, "exp", path))


def rows_where(rows: list[dict[str, str]], key: str, value: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key) == value]


def artifact_path(spec: dict[str, Any]) -> Path:
    return ROOT / spec["path"]


def metadata_path(spec: dict[str, Any]) -> Path | None:
    value = spec.get("metadata_path")
    return ROOT / value if value else None


def artifact_directory(spec: dict[str, Any]) -> str:
    return Path(spec["path"]).parts[0]


def expected_testable_exps(metadata: dict[str, Any]) -> set[int]:
    min_exp = int(metadata["min_exp"])
    max_exp = int(metadata["max_exp"])
    train_windows = int(metadata.get("train_windows", EXPECTED_TRAIN_WINDOWS))
    first_test_exp = min_exp + train_windows
    return set(range(first_test_exp, max_exp + 1))


def expected_testable_exp_count(metadata: dict[str, Any]) -> int:
    return len(expected_testable_exps(metadata))


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

    expected_null_indices = set(range(EXPECTED_NULLS))
    actual_null_indices = set(per_null)
    if actual_null_indices != expected_null_indices:
        missing = sorted(expected_null_indices - actual_null_indices)[:10]
        extra = sorted(actual_null_indices - expected_null_indices)[:10]
        raise ValidationError(
            f"{path} has wrong null_index set; missing sample {missing}, "
            f"extra sample {extra}"
        )

    bad_counts = {
        idx: count for idx, count in per_null.items() if count != expected_rows_per_null
    }
    if bad_counts:
        sample = dict(sorted(bad_counts.items())[:5])
        raise ValidationError(
            f"{path} has wrong rows per null; expected "
            f"{expected_rows_per_null}, sample failures: {sample}"
        )

    expected_exps = expected_testable_exps(metadata)
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


def validate_rows_cover_exps(
    rows: list[dict[str, str]], path: Path, metadata: dict[str, Any], label: str
) -> None:
    actual = {int(as_float(row, "exp", path)) for row in rows}
    expected = expected_testable_exps(metadata)
    if actual != expected:
        raise ValidationError(
            f"{label} exp coverage: expected {sorted(expected)}, got {sorted(actual)}"
        )


def validate_manifest_schema(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assert_equal(
        int(manifest.get("schema_version", -1)),
        EXPECTED_MANIFEST_SCHEMA_VERSION,
        "final_manifest schema_version",
    )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValidationError("final_manifest.json has no artifacts object")

    required_keys = {
        key for key, spec in artifacts.items() if bool(spec.get("required", True))
    }
    assert_equal(required_keys, EXPECTED_REQUIRED, "required paper-scale artifact keys")

    for key, spec in artifacts.items():
        if not isinstance(spec, dict):
            raise ValidationError(f"manifest artifact {key!r} is not an object")
        for field in ("name", "path"):
            if field not in spec:
                raise ValidationError(f"manifest artifact {key!r} is missing {field!r}")
        if "required" in spec and not isinstance(spec["required"], bool):
            raise ValidationError(f"manifest artifact {key!r} has non-boolean required flag")

    return artifacts


def validate_optional_artifacts(artifacts: dict[str, dict[str, Any]]) -> None:
    """Report optional/pilot artifact drift without blocking paper-scale validation."""
    for key, spec in sorted(artifacts.items()):
        if key in EXPECTED_REQUIRED:
            continue

        path = artifact_path(spec)
        if not path.exists():
            warn(f"optional artifact missing: {key} -> {path}")
            continue
        try_read_csv(path)

        meta_path = metadata_path(spec)
        if meta_path is None:
            warn(f"optional artifact has no metadata_path: {key}")
            continue
        if not meta_path.exists():
            warn(f"optional metadata missing: {key} -> {meta_path}")
            continue

        try:
            metadata = read_json(meta_path)
        except Exception as exc:
            warn(f"optional metadata is not readable JSON: {key} -> {exc}")
            continue

        checkpoint_files: list[str] = []
        if metadata.get("checkpoint_file"):
            checkpoint_files.append(metadata["checkpoint_file"])
        checkpoint_files.extend(metadata.get("checkpoint_files", []))
        for checkpoint_file in checkpoint_files:
            checkpoint_path = meta_path.parent / checkpoint_file
            if not checkpoint_path.exists():
                warn(f"optional checkpoint missing: {key} -> {checkpoint_path}")
            else:
                try_read_csv(checkpoint_path)


def validate_manifest_and_artifacts() -> dict[str, Any]:
    manifest = read_json(MANIFEST_PATH)
    artifacts = validate_manifest_schema(manifest)

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
                validate_rows_cover_exps(
                    baseline_rows, artifact_path(spec), metadata, f"{name} {baseline}"
                )
        elif key == "paper_baseline_ladder":
            for baseline in ("B0", "B1(11)"):
                baseline_rows = rows_where(rows, "baseline", baseline)
                assert_equal(
                    len(baseline_rows),
                    expected_count,
                    f"{name} aggregated rows for {baseline}",
                )
                validate_rows_cover_exps(
                    baseline_rows, artifact_path(spec), metadata, f"{name} {baseline}"
                )
        else:
            assert_equal(len(rows), expected_count, f"{name} aggregated row count")
            validate_rows_cover_exps(rows, artifact_path(spec), metadata, name)

    validate_optional_artifacts(artifacts)
    return manifest


def validate_metrics() -> None:
    metrics = read_json(METRICS_PATH)
    assert_equal(bool(metrics.get("ok")), True, "final_metrics ok")
    assert_equal(
        metrics.get("generated_from"),
        "experiments/final_manifest.json",
        "final_metrics generated_from",
    )

    paper_scale = metrics["paper_scale"]
    assert_equal(int(paper_scale["max_exp"]), EXPECTED_MAX_EXP, "paper_scale max_exp")
    assert_equal(int(paper_scale["X"]), EXPECTED_X, "paper_scale X")
    assert_equal(int(paper_scale["nulls"]), EXPECTED_NULLS, "paper_scale nulls")
    assert_equal(int(paper_scale["seed"]), EXPECTED_SEED, "paper_scale seed")

    manifest = read_json(MANIFEST_PATH)
    artifacts = validate_manifest_schema(manifest)
    expected_dirs = sorted(artifact_directory(artifacts[key]) for key in EXPECTED_REQUIRED)
    actual_dirs = sorted(paper_scale.get("artifact_directories", []))
    assert_equal(actual_dirs, expected_dirs, "paper_scale artifact directories")

    conclusion = metrics.get("conclusion", {})
    assert_equal(
        bool(conclusion.get("paper_scale_runs_complete")),
        True,
        "conclusion paper_scale_runs_complete",
    )
    assert_equal(
        bool(conclusion.get("positive_controls_pass")),
        True,
        "conclusion positive_controls_pass",
    )
    assert_equal(
        bool(conclusion.get("residual_beyond_B1_detected")),
        False,
        "conclusion residual_beyond_B1_detected",
    )

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


def validate_figure_contract() -> None:
    """Ensure the paper figure generator is tied to pinned paper-scale inputs."""
    if not FIGURE_SCRIPT_PATH.exists():
        raise ValidationError(f"missing figure generator: {FIGURE_SCRIPT_PATH}")
    figure_script = FIGURE_SCRIPT_PATH.read_text(encoding="utf-8")

    if not FIGURE_README_PATH.exists():
        warn(f"missing paper figure README: {FIGURE_README_PATH}")
        readme = ""
    else:
        readme = FIGURE_README_PATH.read_text(encoding="utf-8")

    for figure_name, required_tokens in EXPECTED_FIGURES.items():
        if figure_name not in figure_script:
            raise ValidationError(f"figure generator does not write {figure_name}")
        if readme and figure_name not in readme:
            warn(f"paper figure README does not mention {figure_name}")
        for token in required_tokens:
            if token not in figure_script:
                raise ValidationError(
                    f"figure generator for {figure_name} is not tied to {token}"
                )

        figure_path = FIGURE_OUT_DIR / figure_name
        if not figure_path.exists():
            warn(
                f"generated figure not committed: {figure_path}; "
                "run python experiments/rpi_paper_figures.py before manuscript assembly"
            )
            continue
        content = figure_path.read_text(encoding="utf-8", errors="replace")
        if "<svg" not in content[:500].lower():
            raise ValidationError(f"generated figure does not look like SVG: {figure_path}")


def main() -> int:
    try:
        validate_manifest_and_artifacts()
        validate_metrics()
        validate_figure_contract()
    except ValidationError as exc:
        print(f"artifact validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "artifact validation passed: required paper-scale CSV, metadata, "
        "checkpoint counts, final metrics, and figure input contracts are consistent"
    )
    if WARNINGS:
        print("artifact validation warnings:", file=sys.stderr)
        for warning in WARNINGS:
            print(f"- {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
