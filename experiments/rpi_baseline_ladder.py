#!/usr/bin/env python3
"""
Baseline ladder pilot:

    B0      local density first-hit model on even gaps
    B1(y)   wheel-corrected first-hit model

Both are tested against the same conservative residual U model from
rpi_b1_u1.py: a two-expert bucket mixture of the baseline bucket distribution
and a KT-smoothed finite-depth Markov predictor.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from rpi_b1_u1 import (
    WheelFirstHit,
    bucket_edges,
    build_real_windows,
    evaluate_windows,
    summarize_nulls,
)


def safe_label(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def run_one_baseline(
    label: str,
    y: int,
    min_exp: int,
    max_exp: int,
    train_windows: int,
    depth: int,
    edges: list[float],
    nulls: int,
    seed: int,
    checkpoint_path: Path | None,
    resume: bool,
    checkpoint_every_seconds: float,
) -> tuple[list[dict[str, float | str]], dict[str, object]]:
    wheel = WheelFirstHit(y)
    windows = build_real_windows(min_exp, max_exp, wheel, edges)
    alphabet_size = len(edges) - 1
    real_rows = evaluate_windows(
        windows, min_exp, max_exp, train_windows, alphabet_size, depth
    )
    null_summary = summarize_nulls(
        windows,
        min_exp,
        max_exp,
        train_windows,
        alphabet_size,
        depth,
        wheel,
        edges,
        nulls,
        seed,
        "fixed-count",
        checkpoint_path,
        resume,
        checkpoint_every_seconds,
    )

    rows: list[dict[str, float | str]] = []
    for row in real_rows:
        exp = int(row["exp"])
        enriched: dict[str, float | str] = {
            "baseline": label,
            "y": float(y),
            "W": float(wheel.W),
            "phi_W": float(wheel.phi),
        }
        enriched.update(row)
        enriched.update(null_summary[exp])
        sd = float(enriched["null_sd"])
        enriched["z_vs_null"] = (
            (float(enriched["R_bits_per_gap"]) - float(enriched["null_mean"])) / sd
            if sd > 0
            else 0.0
        )
        rows.append(enriched)

    metadata = {
        "label": label,
        "y": y,
        "W": wheel.W,
        "phi_W": wheel.phi,
    }
    return rows, metadata


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-exp", type=int, default=12)
    parser.add_argument("--max-exp", type=int, default=21)
    parser.add_argument("--train-windows", type=int, default=3)
    parser.add_argument("--b1-y", type=int, default=11)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--bucket-width", type=float, default=0.5)
    parser.add_argument("--bucket-max", type=float, default=8.0)
    parser.add_argument("--nulls", type=int, default=12)
    parser.add_argument(
        "--checkpoint-nulls",
        action="store_true",
        help="Write raw null-replicate rows after each completed null.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing null checkpoint files in the output directory.",
    )
    parser.add_argument("--checkpoint-every-seconds", type=float, default=120.0)
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--out", type=Path, default=Path("experiments/results_ladder"))
    args = parser.parse_args()

    edges = bucket_edges(args.bucket_width, args.bucket_max)
    all_rows: list[dict[str, float | str]] = []
    baselines = [("B0", 2), (f"B1({args.b1_y})", args.b1_y)]
    metadata: dict[str, object] = {
        "min_exp": args.min_exp,
        "max_exp": args.max_exp,
        "train_windows": args.train_windows,
        "depth": args.depth,
        "bucket_edges": edges,
        "nulls": args.nulls,
        "checkpoint_nulls": args.checkpoint_nulls,
        "checkpoint_files": (
            [
                f"baseline_ladder_null_checkpoint_{safe_label(label)}.csv"
                for label, _ in baselines
            ]
            if args.checkpoint_nulls
            else []
        ),
        "seed": args.seed,
        "baselines": [],
    }

    for label, y in baselines:
        rows, baseline_meta = run_one_baseline(
            label,
            y,
            args.min_exp,
            args.max_exp,
            args.train_windows,
            args.depth,
            edges,
            args.nulls,
            args.seed,
            (
                args.out / f"baseline_ladder_null_checkpoint_{safe_label(label)}.csv"
                if args.checkpoint_nulls
                else None
            ),
            args.resume,
            args.checkpoint_every_seconds,
        )
        all_rows.extend(rows)
        metadata["baselines"].append(baseline_meta)  # type: ignore[index]

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "baseline_ladder.csv", all_rows)
    (args.out / "baseline_ladder_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(json.dumps(metadata, indent=2))
    print()
    print("baseline,exp,X,n,R_bits_per_gap,null_mean,z_vs_null,B_bits,U_bits")
    for row in all_rows:
        print(
            f"{row['baseline']},{int(float(row['exp']))},{int(float(row['X']))},"
            f"{int(float(row['n']))},{float(row['R_bits_per_gap']):.6f},"
            f"{float(row['null_mean']):.6f},{float(row['z_vs_null']):.2f},"
            f"{float(row['B1_exact_bits_per_gap']):.6f},"
            f"{float(row['U1_exact_bits_per_gap']):.6f}"
        )


if __name__ == "__main__":
    main()
