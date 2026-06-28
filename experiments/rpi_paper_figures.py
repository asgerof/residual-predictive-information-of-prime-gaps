#!/usr/bin/env python3
"""
Generate paper-facing figures from the pinned paper-scale artifacts.

Run from the repository root:

    python experiments/rpi_paper_figures.py

Outputs are written to paper_figures/ in three formats per figure:

- PDF: primary paper/manuscript vector format.
- SVG: repository/web vector format.
- PNG: preview/fallback format.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
OUT = ROOT / "paper_figures"
FIGURE_FORMATS = ("pdf", "svg", "png")
PNG_DPI = 150

# Keep concrete output names in the script so the artifact validator can verify
# that the expected paper figure targets are generated.
EXPECTED_OUTPUTS = (
    "figure_1_b1_residual_stop_time.pdf",
    "figure_1_b1_residual_stop_time.svg",
    "figure_1_b1_residual_stop_time.png",
    "figure_2_ctw_positive_control.pdf",
    "figure_2_ctw_positive_control.svg",
    "figure_2_ctw_positive_control.png",
    "figure_3_baseline_ladder_bits.pdf",
    "figure_3_baseline_ladder_bits.svg",
    "figure_3_baseline_ladder_bits.png",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def save_figure(fig: plt.Figure, stem: str) -> None:
    for fmt in FIGURE_FORMATS:
        kwargs = {"dpi": PNG_DPI} if fmt == "png" else {}
        fig.savefig(OUT / f"{stem}.{fmt}", **kwargs)


def save_b1_residual() -> None:
    rows = read_csv(
        EXPERIMENTS
        / "paper_b1_y11_depth4_stop_time_x26_n200"
        / "b1_u1_real_vs_null.csv"
    )

    xs = [int(f(row, "exp")) for row in rows]
    real = [f(row, "R_bits_per_gap") for row in rows]
    null_mean = [f(row, "null_mean") for row in rows]
    null_p05 = [f(row, "null_p05") for row in rows]
    null_p95 = [f(row, "null_p95") for row in rows]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(xs, real, marker="o", label="real R")
    ax.plot(xs, null_mean, linestyle="--", label="null mean")
    ax.fill_between(xs, null_p05, null_p95, alpha=0.2, label="null 5-95%")
    ax.axhline(0, linewidth=0.8)
    ax.set_title("B1(11) residual code gain vs stop-time nulls")
    ax.set_xlabel("dyadic exponent")
    ax.set_ylabel("R bits/gap")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, "figure_1_b1_residual_stop_time")
    plt.close(fig)


def save_ctw_control() -> None:
    rows = read_csv(
        EXPERIMENTS
        / "paper_ctw_rank64_depth1_stop_time_x26_n200"
        / "ctw_symbol_ladder.csv"
    )
    b0 = [row for row in rows if row["baseline"] == "B0"]
    b1 = [row for row in rows if row["baseline"] == "B1(11)"]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(
        [int(f(row, "exp")) for row in b0],
        [f(row, "R_bits_per_gap") for row in b0],
        marker="o",
        label="CTW vs B0",
    )
    ax.plot(
        [int(f(row, "exp")) for row in b1],
        [f(row, "R_bits_per_gap") for row in b1],
        marker="o",
        label="CTW vs B1(11)",
    )
    ax.axhline(0, linewidth=0.8)
    ax.set_title("CTW positive control disappears under B1(11)")
    ax.set_xlabel("dyadic exponent")
    ax.set_ylabel("R bits/gap")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, "figure_2_ctw_positive_control")
    plt.close(fig)


def save_baseline_ladder() -> None:
    rows = read_csv(
        EXPERIMENTS
        / "paper_ladder_b0_b1_y11_x26_n200"
        / "baseline_ladder.csv"
    )
    b0 = [row for row in rows if row["baseline"] == "B0"]
    b1 = [row for row in rows if row["baseline"] == "B1(11)"]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(
        [int(f(row, "exp")) for row in b0],
        [f(row, "B1_exact_bits_per_gap") for row in b0],
        marker="o",
        label="B0 exact bits/gap",
    )
    ax.plot(
        [int(f(row, "exp")) for row in b1],
        [f(row, "B1_exact_bits_per_gap") for row in b1],
        marker="o",
        label="B1(11) exact bits/gap",
    )
    ax.set_title("Exact baseline code lengths")
    ax.set_xlabel("dyadic exponent")
    ax.set_ylabel("bits/gap")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, "figure_3_baseline_ladder_bits")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    save_b1_residual()
    save_ctw_control()
    save_baseline_ladder()


if __name__ == "__main__":
    main()
