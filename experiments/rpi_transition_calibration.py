#!/usr/bin/env python3
"""
Chronological residue-transition calibration.

This is a more realistic B2-style baseline than the raw pair-factor prototype.
It keeps B1's within-symbol first-hit distribution, but replaces B1's symbol
mass by a transition probability learned only from earlier dyadic windows:

    Btr(g | p) = B1(g | p, s) * P_train(s | c)
              = B1(g | p) * P_train(s | c) / B1_s(s | p).

Here c is the current prime residue p mod M and s is the next prime residue
(p + g) mod M.  This targets the known phenomenon that consecutive primes have
biased residue transitions, while keeping the test protocol chronological.

The script also evaluates a residual sparse-CTW expert over the emitted
transition symbols on top of the calibrated baseline.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from rpi_b1_u1 import WheelFirstHit, prime_pairs_upto
from rpi_ctw_symbol_ladder import SparseCTW


@dataclass
class Event:
    p: int
    gap: int
    context: int
    symbol: int
    b1_symbol_mass: float
    b1_log2_gap: float


class NextResidueSymbolizer:
    def __init__(self, mod: int):
        if mod <= 1:
            raise ValueError("mod must be > 1")
        self.mod = mod
        self.units = [r for r in range(mod) if math.gcd(r, mod) == 1]
        self.unit_index = {r: i for i, r in enumerate(self.units)}
        self.name = f"next_unit_residue_mod_{mod}"
        self.alphabet_size = len(self.units)
        self.context_size = len(self.units)
        self._mass_cache: dict[tuple[int, int, int, int], list[float]] = {}

    def context(self, p: int) -> int:
        return self.unit_index[p % self.mod]

    def symbol(self, p: int, gap: int) -> int:
        return self.unit_index[(p + gap) % self.mod]

    def b1_symbol_masses(self, wheel: WheelFirstHit, p: int) -> list[float]:
        theta_key = int(round(wheel.theta(p) * 10**12))
        period = math.lcm(wheel.W, self.mod)
        key = (wheel.W, p % period, self.mod, theta_key)
        cached = self._mass_cache.get(key)
        if cached is not None:
            return cached

        q = 1.0 - wheel.theta(p)
        candidates = [
            gap
            for gap in range(1, period + 1)
            if math.gcd((p + gap) % wheel.W, wheel.W) == 1
        ]
        denom = 1.0 - q ** len(candidates)
        masses = [0.0] * self.alphabet_size
        for idx, gap in enumerate(candidates, start=1):
            masses[self.symbol(p, gap)] += wheel.theta(p) * (q ** (idx - 1)) / denom
        self._mass_cache[key] = masses
        return masses

    def b1_symbol_mass(self, wheel: WheelFirstHit, p: int, symbol: int) -> float:
        return max(self.b1_symbol_masses(wheel, p)[symbol], 1e-300)


class KTTransition:
    def __init__(self, context_size: int, alphabet_size: int, prior: float = 0.5):
        self.context_size = context_size
        self.alphabet_size = alphabet_size
        self.prior = prior
        self.counts: dict[int, dict[int, int]] = defaultdict(dict)
        self.totals: dict[int, int] = defaultdict(int)

    def prob(self, context: int, symbol: int) -> float:
        counts = self.counts[context]
        total = self.totals[context]
        return (counts.get(symbol, 0) + self.prior) / (
            total + self.prior * self.alphabet_size
        )

    def update(self, context: int, symbol: int) -> None:
        counts = self.counts[context]
        counts[symbol] = counts.get(symbol, 0) + 1
        self.totals[context] += 1

    def update_window(self, events: list[Event]) -> None:
        for ev in events:
            self.update(ev.context, ev.symbol)


def build_windows(
    min_exp: int,
    max_exp: int,
    wheel: WheelFirstHit,
    symbolizer: NextResidueSymbolizer,
) -> dict[int, list[Event]]:
    limit = (1 << (max_exp + 1)) + 200_000
    windows: dict[int, list[Event]] = {exp: [] for exp in range(min_exp, max_exp + 1)}
    for p, p_next in prime_pairs_upto(limit):
        if p < (1 << min_exp):
            continue
        if p >= (1 << (max_exp + 1)):
            break
        exp = p.bit_length() - 1
        if not min_exp <= exp <= max_exp:
            continue
        gap = p_next - p
        symbol = symbolizer.symbol(p, gap)
        windows[exp].append(
            Event(
                p=p,
                gap=gap,
                context=symbolizer.context(p),
                symbol=symbol,
                b1_symbol_mass=symbolizer.b1_symbol_mass(wheel, p, symbol),
                b1_log2_gap=wheel.log2_prob_gap(p, gap),
            )
        )
    return windows


def evaluate_window(
    events: list[Event],
    transition: KTTransition,
    residual: SparseCTW,
    update_residual_online: bool,
    transition_lambda: float,
) -> dict[str, float]:
    trans_model = deepcopy(transition)
    logw_base = math.log(0.5)
    logw_ctw = math.log(0.5)

    b1_bits = 0.0
    trans_bits = 0.0
    u_bits = 0.0
    trans_gain = 0.0
    residual_gain = 0.0
    for ev in events:
        pb1 = max(ev.b1_symbol_mass, 1e-300)
        p_emp = trans_model.prob(ev.context, ev.symbol)
        ptr = max((1.0 - transition_lambda) * pb1 + transition_lambda * p_emp, 1e-300)
        delta_tr = math.log2(ptr) - math.log2(pb1)
        trans_gain += delta_tr

        pc = max(residual.prob(ev.symbol), 1e-300)
        m0 = max(logw_base, logw_ctw)
        wb = math.exp(logw_base - m0)
        wc = math.exp(logw_ctw - m0)
        pu = (wb * ptr + wc * pc) / (wb + wc)
        delta_u = math.log2(pu) - math.log2(ptr)
        residual_gain += delta_u

        logw_base += math.log(ptr)
        logw_ctw += math.log(pc)
        z = max(logw_base, logw_ctw)
        logw_base -= z
        logw_ctw -= z

        if update_residual_online:
            residual.update(ev.symbol)

        b_gap_bits = -ev.b1_log2_gap
        b1_bits += b_gap_bits
        trans_bits += b_gap_bits - delta_tr
        u_bits += b_gap_bits - delta_tr - delta_u

    n = len(events)
    ctw_weight = math.exp(logw_ctw) / (math.exp(logw_base) + math.exp(logw_ctw))
    return {
        "n": float(n),
        "B1_bits_per_gap": b1_bits / n,
        "Btr_bits_per_gap": trans_bits / n,
        "U_bits_per_gap": u_bits / n,
        "Btr_gain_vs_B1": trans_gain / n,
        "U_gain_vs_Btr": residual_gain / n,
        "U_gain_vs_B1": (trans_gain + residual_gain) / n,
        "final_ctw_weight": ctw_weight,
    }


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
    parser.add_argument("--max-exp", type=int, default=20)
    parser.add_argument("--train-windows", type=int, default=3)
    parser.add_argument("--y", type=int, default=11)
    parser.add_argument("--mod", type=int, default=30)
    parser.add_argument("--transition-lambda", type=float, default=1.0)
    parser.add_argument("--residual-depth", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("experiments/results_transition_calibration"))
    args = parser.parse_args()

    wheel = WheelFirstHit(args.y)
    symbolizer = NextResidueSymbolizer(args.mod)
    windows = build_windows(args.min_exp, args.max_exp, wheel, symbolizer)
    transition = KTTransition(symbolizer.context_size, symbolizer.alphabet_size)
    residual = SparseCTW(symbolizer.alphabet_size, args.residual_depth)
    rows: list[dict[str, float | str]] = []

    for exp in range(args.min_exp, args.max_exp + 1):
        events = windows[exp]
        if not events:
            continue
        if exp < args.min_exp + args.train_windows:
            transition.update_window(events)
            for ev in events:
                residual.update(ev.symbol)
            continue

        metrics = evaluate_window(
            events,
            transition,
            residual,
            update_residual_online=True,
            transition_lambda=args.transition_lambda,
        )
        rows.append(
            {
                "exp": float(exp),
                "X": float(1 << exp),
                "mod": float(args.mod),
                "symbol": symbolizer.name,
                **metrics,
            }
        )

        transition.update_window(events)

    metadata = {
        "min_exp": args.min_exp,
        "max_exp": args.max_exp,
        "train_windows": args.train_windows,
        "y": args.y,
        "W": wheel.W,
        "phi_W": wheel.phi,
        "mod": args.mod,
        "transition_lambda": args.transition_lambda,
        "symbol": symbolizer.name,
        "residual_depth": args.residual_depth,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "transition_calibration.csv", rows)
    (args.out / "transition_calibration_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(json.dumps(metadata, indent=2))
    print()
    print("exp,X,n,Btr_gain_vs_B1,U_gain_vs_Btr,B1_bits,Btr_bits,U_bits,ctw_weight")
    for row in rows:
        print(
            f"{int(float(row['exp']))},{int(float(row['X']))},{int(float(row['n']))},"
            f"{float(row['Btr_gain_vs_B1']):.6f},"
            f"{float(row['U_gain_vs_Btr']):.6f},"
            f"{float(row['B1_bits_per_gap']):.6f},"
            f"{float(row['Btr_bits_per_gap']):.6f},"
            f"{float(row['U_bits_per_gap']):.6f},"
            f"{float(row['final_ctw_weight']):.3f}"
        )


if __name__ == "__main__":
    main()
