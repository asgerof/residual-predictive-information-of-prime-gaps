#!/usr/bin/env python3
"""
Next-phase residual symbol ladder.

This script keeps the baseline-centered residual coding rule from the earlier
pilots,

    U(g | history, p) = U_s(s(g,p) | history, p) * B(g | p, s(g,p)),

but replaces the residual expert with a sparse context-tree mixture.  The goal
is to give the residual model a stronger sequential learner while keeping the
baseline's exact within-symbol gap distribution.

Supported symbols:

    gap_mod_M       s = g mod M
    rank_mod_M      s = admissible first-hit rank of g modulo M

The rank symbol is useful because, under the wheel-first-hit baseline, the
admissible hit rank is geometric and has a simple baseline distribution.  It
is less tied to a particular residue modulus than g mod M.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from rpi_b1_u1 import WheelFirstHit, prime_pairs_upto
from rpi_symbol_ladder import GapModSymbolizer


class SparseCTW:
    def __init__(self, alphabet_size: int, depth: int, mix_weight: float = 0.5):
        if alphabet_size <= 1:
            raise ValueError("alphabet_size must be > 1")
        if depth < 0:
            raise ValueError("depth must be >= 0")
        if not 0.0 < mix_weight < 1.0:
            raise ValueError("mix_weight must be in (0, 1)")
        self.K = alphabet_size
        self.depth = depth
        self.mix_weight = mix_weight
        self.counts: dict[tuple[int, ...], dict[int, int]] = defaultdict(dict)
        self.totals: dict[tuple[int, ...], int] = defaultdict(int)
        self.history: list[int] = []

    def _kt_prob(self, context: tuple[int, ...], symbol: int) -> float:
        counts = self.counts[context]
        total = self.totals[context]
        return (counts.get(symbol, 0) + 0.5) / (total + 0.5 * self.K)

    def _prob_at(self, context: tuple[int, ...], symbol: int) -> float:
        kt = self._kt_prob(context, symbol)
        if not context:
            return kt
        parent = self._prob_at(context[1:], symbol)
        return self.mix_weight * kt + (1.0 - self.mix_weight) * parent

    def prob(self, symbol: int) -> float:
        d = min(self.depth, len(self.history))
        context = () if d == 0 else tuple(self.history[-d:])
        return self._prob_at(context, symbol)

    def update(self, symbol: int) -> None:
        dmax = min(self.depth, len(self.history))
        for d in range(dmax + 1):
            context = () if d == 0 else tuple(self.history[-d:])
            counts = self.counts[context]
            counts[symbol] = counts.get(symbol, 0) + 1
            self.totals[context] += 1
        self.history.append(symbol)


class Symbolizer(Protocol):
    name: str
    alphabet_size: int

    def symbol(self, wheel: WheelFirstHit, gap: int, p: int) -> int:
        ...

    def baseline_mass(self, wheel: WheelFirstHit, p: int, symbol: int) -> float:
        ...


class GapModAdapter:
    def __init__(self, mod: int):
        self.inner = GapModSymbolizer(mod)
        self.name = f"gap_mod_{mod}"
        self.alphabet_size = mod

    def symbol(self, wheel: WheelFirstHit, gap: int, p: int) -> int:
        return self.inner.symbol(gap, p)

    def baseline_mass(self, wheel: WheelFirstHit, p: int, symbol: int) -> float:
        return self.inner.baseline_mass(wheel, p, symbol)


class RankModSymbolizer:
    def __init__(self, mod: int):
        if mod <= 1:
            raise ValueError("mod must be > 1")
        self.mod = mod
        self.name = f"rank_mod_{mod}"
        self.alphabet_size = mod

    def symbol(self, wheel: WheelFirstHit, gap: int, p: int) -> int:
        rank = wheel.admissible_count_leq(p, gap)
        return rank % self.mod

    def baseline_mass(self, wheel: WheelFirstHit, p: int, symbol: int) -> float:
        theta = wheel.theta(p)
        q = 1.0 - theta
        first_rank = self.mod if symbol == 0 else symbol
        mass = theta * (q ** (first_rank - 1)) / (1.0 - q**self.mod)
        return max(mass, 1e-300)


@dataclass
class SymbolEvent:
    p: int
    gap: int
    symbol: int
    baseline_symbol_mass: float
    baseline_log2_gap: float


def build_real_windows(
    min_exp: int,
    max_exp: int,
    wheel: WheelFirstHit,
    symbolizer: Symbolizer,
) -> dict[int, list[SymbolEvent]]:
    limit = (1 << (max_exp + 1)) + 200_000
    windows: dict[int, list[SymbolEvent]] = {m: [] for m in range(min_exp, max_exp + 1)}
    for p, p_next in prime_pairs_upto(limit):
        if p < (1 << min_exp):
            continue
        if p >= (1 << (max_exp + 1)):
            break
        exp = p.bit_length() - 1
        if exp < min_exp or exp > max_exp:
            continue
        gap = p_next - p
        s = symbolizer.symbol(wheel, gap, p)
        windows[exp].append(
            SymbolEvent(
                p=p,
                gap=gap,
                symbol=s,
                baseline_symbol_mass=symbolizer.baseline_mass(wheel, p, s),
                baseline_log2_gap=wheel.log2_prob_gap(p, gap),
            )
        )
    return windows


def synthetic_windows(
    real_windows: dict[int, list[SymbolEvent]],
    wheel: WheelFirstHit,
    symbolizer: Symbolizer,
    rng: random.Random,
    null_mode: str = "fixed-count",
) -> dict[int, list[SymbolEvent]]:
    out: dict[int, list[SymbolEvent]] = {}
    for exp, real_events in real_windows.items():
        if not real_events:
            out[exp] = []
            continue
        p = real_events[0].p
        stop = 1 << (exp + 1)
        remaining = len(real_events)
        events = []
        while True:
            if null_mode == "fixed-count":
                if remaining <= 0:
                    break
                remaining -= 1
            elif null_mode == "stop-time":
                if p >= stop:
                    break
            else:
                raise ValueError(f"unknown null_mode: {null_mode}")
            gap = wheel.sample_gap(p, rng)
            s = symbolizer.symbol(wheel, gap, p)
            events.append(
                SymbolEvent(
                    p=p,
                    gap=gap,
                    symbol=s,
                    baseline_symbol_mass=symbolizer.baseline_mass(wheel, p, s),
                    baseline_log2_gap=wheel.log2_prob_gap(p, gap),
                )
            )
            p += gap
        out[exp] = events
    return out


def evaluate_windows(
    windows: dict[int, list[SymbolEvent]],
    min_exp: int,
    max_exp: int,
    train_windows: int,
    alphabet_size: int,
    depth: int,
    ctw_mix_weight: float,
) -> list[dict[str, float]]:
    model = SparseCTW(alphabet_size, depth, ctw_mix_weight)
    rows = []

    def mix_prob_and_update(
        ev: SymbolEvent, logw_base: float, logw_ctw: float
    ) -> tuple[float, float, float]:
        pb = max(ev.baseline_symbol_mass, 1e-300)
        pc = max(model.prob(ev.symbol), 1e-300)
        m0 = max(logw_base, logw_ctw)
        wb = math.exp(logw_base - m0)
        wc = math.exp(logw_ctw - m0)
        pu = (wb * pb + wc * pc) / (wb + wc)

        logw_base += math.log(pb)
        logw_ctw += math.log(pc)
        z = max(logw_base, logw_ctw)
        logw_base -= z
        logw_ctw -= z
        model.update(ev.symbol)
        return max(pu, 1e-300), logw_base, logw_ctw

    for exp in range(min_exp, max_exp + 1):
        events = windows[exp]
        if not events:
            continue
        if exp < min_exp + train_windows:
            for ev in events:
                model.update(ev.symbol)
            continue

        logw_base = math.log(0.5)
        logw_ctw = math.log(0.5)
        gain = 0.0
        base_bits = 0.0
        u_bits = 0.0
        base_symbol_bits = 0.0
        u_symbol_bits = 0.0
        for ev in events:
            pb = max(ev.baseline_symbol_mass, 1e-300)
            pu, logw_base, logw_ctw = mix_prob_and_update(ev, logw_base, logw_ctw)
            delta = math.log2(pu) - math.log2(pb)
            gain += delta
            b_gap_bits = -ev.baseline_log2_gap
            base_bits += b_gap_bits
            u_bits += b_gap_bits - delta
            base_symbol_bits += -math.log2(pb)
            u_symbol_bits += -math.log2(pu)

        n = len(events)
        ctw_weight = math.exp(logw_ctw) / (math.exp(logw_base) + math.exp(logw_ctw))
        rows.append(
            {
                "exp": float(exp),
                "X": float(1 << exp),
                "n": float(n),
                "R_bits_per_gap": gain / n,
                "total_gain_bits": gain,
                "final_ctw_weight": ctw_weight,
                "B_exact_bits_per_gap": base_bits / n,
                "U_exact_bits_per_gap": u_bits / n,
                "B_symbol_bits_per_gap": base_symbol_bits / n,
                "U_symbol_bits_per_gap": u_symbol_bits / n,
            }
        )
    return rows


def summarize_nulls(
    real_windows: dict[int, list[SymbolEvent]],
    min_exp: int,
    max_exp: int,
    train_windows: int,
    alphabet_size: int,
    depth: int,
    ctw_mix_weight: float,
    wheel: WheelFirstHit,
    symbolizer: Symbolizer,
    nulls: int,
    seed: int,
    null_mode: str = "fixed-count",
) -> dict[int, dict[str, float]]:
    by_exp: dict[int, list[float]] = defaultdict(list)
    rng = random.Random(seed)
    for _ in range(nulls):
        synth = synthetic_windows(real_windows, wheel, symbolizer, rng, null_mode)
        rows = evaluate_windows(
            synth,
            min_exp,
            max_exp,
            train_windows,
            alphabet_size,
            depth,
            ctw_mix_weight,
        )
        for row in rows:
            by_exp[int(row["exp"])].append(row["R_bits_per_gap"])

    out = {}
    for exp, values in by_exp.items():
        values = sorted(values)
        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)
        out[exp] = {
            "null_mean": mean,
            "null_sd": math.sqrt(var),
            "null_min": values[0],
            "null_p05": values[max(0, int(0.05 * (len(values) - 1)))],
            "null_p50": values[len(values) // 2],
            "null_p95": values[min(len(values) - 1, int(0.95 * (len(values) - 1)))],
            "null_max": values[-1],
        }
    return out


def empirical_p_ge(real_value: float, null_summary_values: list[float]) -> float:
    ge = sum(1 for value in null_summary_values if value >= real_value)
    return (ge + 1.0) / (len(null_summary_values) + 1.0)


def safe_label(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def load_null_checkpoint(path: Path) -> tuple[set[int], dict[int, list[float]]]:
    completed: set[int] = set()
    by_exp: dict[int, list[float]] = defaultdict(list)
    if not path.exists():
        return completed, by_exp
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            null_index = int(row["null_index"])
            exp = int(float(row["exp"]))
            completed.add(null_index)
            by_exp[exp].append(float(row["R_bits_per_gap"]))
    return completed, by_exp


def append_null_checkpoint(path: Path, null_index: int, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["null_index", "exp", "X", "n", "R_bits_per_gap"],
        )
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "null_index": null_index,
                    "exp": row["exp"],
                    "X": row["X"],
                    "n": row["n"],
                    "R_bits_per_gap": row["R_bits_per_gap"],
                }
            )


def run_baseline(
    label: str,
    y: int,
    symbolizer: Symbolizer,
    args: argparse.Namespace,
) -> tuple[list[dict[str, float | str]], dict[str, object]]:
    wheel = WheelFirstHit(y)
    windows = build_real_windows(args.min_exp, args.max_exp, wheel, symbolizer)
    real_rows = evaluate_windows(
        windows,
        args.min_exp,
        args.max_exp,
        args.train_windows,
        symbolizer.alphabet_size,
        args.depth,
        args.ctw_mix_weight,
    )

    null_values_by_exp: dict[int, list[float]] = defaultdict(list)
    checkpoint_path = None
    completed: set[int] = set()
    if args.checkpoint_nulls:
        checkpoint_path = (
            args.out
            / f"ctw_symbol_ladder_null_checkpoint_{safe_label(label)}.csv"
        )
        if args.resume:
            completed, loaded = load_null_checkpoint(checkpoint_path)
            null_values_by_exp.update(loaded)
        elif checkpoint_path.exists():
            checkpoint_path.unlink()

    last_report = time.monotonic()
    if checkpoint_path is None:
        rng = random.Random(args.seed)
        null_indices = range(args.nulls)
    else:
        null_indices = [i for i in range(args.nulls) if i not in completed]

    for null_index in null_indices:
        rng = (
            random.Random(args.seed + null_index)
            if checkpoint_path is not None
            else rng
        )
        synth = synthetic_windows(windows, wheel, symbolizer, rng, args.null_mode)
        null_rows = evaluate_windows(
            synth,
            args.min_exp,
            args.max_exp,
            args.train_windows,
            symbolizer.alphabet_size,
            args.depth,
            args.ctw_mix_weight,
        )
        if checkpoint_path is not None:
            append_null_checkpoint(checkpoint_path, null_index, null_rows)
        for row in null_rows:
            null_values_by_exp[int(row["exp"])].append(row["R_bits_per_gap"])
        now = time.monotonic()
        if checkpoint_path is not None and now - last_report >= args.checkpoint_every_seconds:
            done = len(completed) + sum(1 for i in range(null_index + 1) if i not in completed)
            print(
                f"{label}: checkpointed {done}/{args.nulls} nulls to {checkpoint_path}",
                flush=True,
            )
            last_report = now

    rows: list[dict[str, float | str]] = []
    for row in real_rows:
        exp = int(row["exp"])
        values = sorted(null_values_by_exp[exp])
        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)
        enriched: dict[str, float | str] = {
            "baseline": label,
            "y": float(y),
            "W": float(wheel.W),
            "phi_W": float(wheel.phi),
            "symbol": symbolizer.name,
            "alphabet_size": float(symbolizer.alphabet_size),
        }
        enriched.update(row)
        enriched.update(
            {
                "null_mean": mean,
                "null_sd": math.sqrt(var),
                "null_min": values[0],
                "null_p05": values[max(0, int(0.05 * (len(values) - 1)))],
                "null_p50": values[len(values) // 2],
                "null_p95": values[min(len(values) - 1, int(0.95 * (len(values) - 1)))],
                "null_max": values[-1],
                "empirical_p_ge": empirical_p_ge(float(row["R_bits_per_gap"]), values),
            }
        )
        rows.append(enriched)

    meta = {"label": label, "y": y, "W": wheel.W, "phi_W": wheel.phi}
    return rows, meta


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_symbolizer(name: str, mod: int) -> Symbolizer:
    if name == "gap_mod":
        return GapModAdapter(mod)
    if name == "rank_mod":
        return RankModSymbolizer(mod)
    raise ValueError(f"unknown symbolizer: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-exp", type=int, default=12)
    parser.add_argument("--max-exp", type=int, default=20)
    parser.add_argument("--train-windows", type=int, default=3)
    parser.add_argument("--b1-y", type=int, default=11)
    parser.add_argument("--symbolizer", choices=["gap_mod", "rank_mod"], default="rank_mod")
    parser.add_argument("--symbol-mod", type=int, default=64)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--ctw-mix-weight", type=float, default=0.5)
    parser.add_argument("--nulls", type=int, default=16)
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
    parser.add_argument(
        "--null-mode",
        choices=["fixed-count", "stop-time"],
        default="fixed-count",
    )
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/results_ctw_symbol_ladder"),
    )
    args = parser.parse_args()

    symbolizer = parse_symbolizer(args.symbolizer, args.symbol_mod)
    baselines = [("B0", 2), (f"B1({args.b1_y})", args.b1_y)]
    all_rows: list[dict[str, float | str]] = []
    metadata: dict[str, object] = {
        "min_exp": args.min_exp,
        "max_exp": args.max_exp,
        "train_windows": args.train_windows,
        "symbolizer": args.symbolizer,
        "symbol_mod": args.symbol_mod,
        "depth": args.depth,
        "ctw_mix_weight": args.ctw_mix_weight,
        "nulls": args.nulls,
        "null_mode": args.null_mode,
        "checkpoint_nulls": args.checkpoint_nulls,
        "checkpoint_files": (
            [f"ctw_symbol_ladder_null_checkpoint_{safe_label(label)}.csv" for label, _ in baselines]
            if args.checkpoint_nulls
            else []
        ),
        "seed": args.seed,
        "baselines": [],
    }

    for label, y in baselines:
        rows, meta = run_baseline(label, y, symbolizer, args)
        all_rows.extend(rows)
        metadata["baselines"].append(meta)  # type: ignore[index]

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "ctw_symbol_ladder.csv", all_rows)
    (args.out / "ctw_symbol_ladder_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(json.dumps(metadata, indent=2))
    print()
    print("baseline,exp,X,n,R_bits_per_gap,null_p95,empirical_p_ge,final_ctw_weight")
    for row in all_rows:
        print(
            f"{row['baseline']},{int(float(row['exp']))},{int(float(row['X']))},"
            f"{int(float(row['n']))},{float(row['R_bits_per_gap']):.6f},"
            f"{float(row['null_p95']):.6f},{float(row['empirical_p_ge']):.3f},"
            f"{float(row['final_ctw_weight']):.3f}"
        )


if __name__ == "__main__":
    main()
