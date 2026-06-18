#!/usr/bin/env python3
"""
Chronological alpha calibration for the B2 consecutive-prime baseline.

The consecutive correction in rpi_b2_consecutive_ladder.py estimates the
finite no-intermediate-prime effect with truncated inclusion-exclusion.  This
script scans a shrinkage parameter:

    alpha=0  -> exactly B1
    alpha=1  -> full finite consecutive correction

For each held-out dyadic window, alpha is selected using only earlier windows.
The per-window oracle alpha is also reported as a diagnostic, but is not an
admissible predictor.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

from rpi_b1_u1 import prime_pairs_upto
from rpi_b2_pair_ladder import B1Baseline
from rpi_b2_consecutive_ladder import B2ConsecutiveBaseline


@dataclass
class GapEvent:
    p: int
    gap: int


def parse_alpha_grid(text: str) -> list[float]:
    values = sorted({float(part.strip()) for part in text.split(",") if part.strip()})
    if not values:
        raise ValueError("alpha grid must contain at least one value")
    if values[0] < 0.0:
        raise ValueError("alpha values must be >= 0")
    return values


def build_gap_windows(min_exp: int, max_exp: int) -> dict[int, list[GapEvent]]:
    limit = (1 << (max_exp + 1)) + 200_000
    windows: dict[int, list[GapEvent]] = {m: [] for m in range(min_exp, max_exp + 1)}
    for p, p_next in prime_pairs_upto(limit):
        if p < (1 << min_exp):
            continue
        if p >= (1 << (max_exp + 1)):
            break
        exp = p.bit_length() - 1
        if min_exp <= exp <= max_exp:
            windows[exp].append(GapEvent(p=p, gap=p_next - p))
    return windows


def bits_for_window(
    events: list[GapEvent], baseline: B1Baseline | B2ConsecutiveBaseline
) -> float:
    return sum(-baseline.log2_prob_gap(ev.p, ev.gap) for ev in events)


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-exp", type=int, default=12)
    parser.add_argument("--max-exp", type=int, default=18)
    parser.add_argument("--train-windows", type=int, default=3)
    parser.add_argument("--b1-y", type=int, default=11)
    parser.add_argument("--tuple-y", type=int, default=11)
    parser.add_argument("--ie-order", type=int, default=2)
    parser.add_argument("--max-rank", type=int, default=64)
    parser.add_argument("--max-correction-rank", type=int, default=20)
    parser.add_argument(
        "--alpha-grid",
        default="0,0.03125,0.0625,0.125,0.25,0.5,0.75,1",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/results_b2_consecutive_alpha_scan"),
    )
    args = parser.parse_args()

    alphas = parse_alpha_grid(args.alpha_grid)
    windows = build_gap_windows(args.min_exp, args.max_exp)
    b1 = B1Baseline(args.b1_y)
    baselines = {
        alpha: B2ConsecutiveBaseline(
            args.b1_y,
            args.tuple_y,
            args.ie_order,
            alpha,
            args.max_rank,
            args.max_correction_rank,
        )
        for alpha in alphas
    }

    bits_by_alpha: dict[float, dict[int, float]] = {}
    for alpha, baseline in baselines.items():
        bits_by_alpha[alpha] = {
            exp: bits_for_window(events, baseline)
            for exp, events in windows.items()
            if events
        }
    b1_bits = {
        exp: bits_for_window(events, b1)
        for exp, events in windows.items()
        if events
    }

    grid_rows: list[dict[str, float | str]] = []
    selected_rows: list[dict[str, float | str]] = []
    for exp in range(args.min_exp, args.max_exp + 1):
        events = windows[exp]
        if not events:
            continue
        n = len(events)
        for alpha in alphas:
            bits = bits_by_alpha[alpha][exp]
            grid_rows.append(
                {
                    "exp": float(exp),
                    "X": float(1 << exp),
                    "n": float(n),
                    "alpha": float(alpha),
                    "bits_per_gap": bits / n,
                    "delta_vs_B1_bits_per_gap": (b1_bits[exp] - bits) / n,
                }
            )

        if exp < args.min_exp + args.train_windows:
            continue

        train_exps = list(range(exp - args.train_windows, exp))
        train_scores = {
            alpha: sum(bits_by_alpha[alpha][m] for m in train_exps)
            for alpha in alphas
        }
        selected_alpha = min(alphas, key=lambda alpha: (train_scores[alpha], alpha))
        oracle_alpha = min(alphas, key=lambda alpha: (bits_by_alpha[alpha][exp], alpha))
        selected_bits = bits_by_alpha[selected_alpha][exp]
        oracle_bits = bits_by_alpha[oracle_alpha][exp]
        selected_rows.append(
            {
                "exp": float(exp),
                "X": float(1 << exp),
                "n": float(n),
                "selected_alpha": float(selected_alpha),
                "selected_bits_per_gap": selected_bits / n,
                "selected_delta_vs_B1_bits_per_gap": (b1_bits[exp] - selected_bits) / n,
                "oracle_alpha": float(oracle_alpha),
                "oracle_bits_per_gap": oracle_bits / n,
                "oracle_delta_vs_B1_bits_per_gap": (b1_bits[exp] - oracle_bits) / n,
                "B1_bits_per_gap": b1_bits[exp] / n,
            }
        )

    metadata = {
        "min_exp": args.min_exp,
        "max_exp": args.max_exp,
        "train_windows": args.train_windows,
        "b1_y": args.b1_y,
        "tuple_y": args.tuple_y,
        "ie_order": args.ie_order,
        "max_rank": args.max_rank,
        "max_correction_rank": args.max_correction_rank,
        "alpha_grid": alphas,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "b2_consecutive_alpha_grid.csv", grid_rows)
    write_csv(args.out / "b2_consecutive_alpha_selected.csv", selected_rows)
    (args.out / "b2_consecutive_alpha_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(json.dumps(metadata, indent=2))
    print()
    print("exp,X,n,selected_alpha,selected_delta_vs_B1,oracle_alpha,oracle_delta_vs_B1")
    for row in selected_rows:
        print(
            f"{int(float(row['exp']))},{int(float(row['X']))},{int(float(row['n']))},"
            f"{float(row['selected_alpha']):g},"
            f"{float(row['selected_delta_vs_B1_bits_per_gap']):.6f},"
            f"{float(row['oracle_alpha']):g},"
            f"{float(row['oracle_delta_vs_B1_bits_per_gap']):.6f}"
        )


if __name__ == "__main__":
    main()
