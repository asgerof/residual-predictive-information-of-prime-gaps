#!/usr/bin/env python3
"""
Residual symbol ladder:

This script tests whether a residual online model can learn richer symbols
than coarse buckets of g/log(p). The first target is gap residues modulo M.

For a baseline B and symbol s(g,p), the exact residual probability is

    U(g | history, p) = U_s(s(g,p) | history, p) * B(g | p, s(g,p)).

Hence the code gain over B is

    log2 U_s(s | history, p) - log2 B_s(s | p).

The tested U_s is a two-expert mixture:

    1. the baseline symbol distribution B_s(. | p);
    2. a KT-smoothed Markov model on previous observed symbols.

This lets the residual expert exploit sequential or distributional deviations
in the chosen symbolization while preserving the baseline's within-symbol
gap distribution.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from rpi_b1_u1 import WheelFirstHit, KTMarkovBuckets, prime_pairs_upto


@dataclass
class SymbolEvent:
    p: int
    gap: int
    symbol: int
    baseline_symbol_mass: float
    baseline_log2_gap: float


class GapModSymbolizer:
    def __init__(self, mod: int):
        if mod <= 1:
            raise ValueError("mod must be > 1")
        self.mod = mod
        self.alphabet_size = mod
        self._candidate_cache: dict[tuple[int, int, int], list[int]] = {}

    def symbol(self, gap: int, p: int) -> int:
        return gap % self.mod

    def _period_candidates(self, wheel: WheelFirstHit, p: int) -> tuple[int, list[int]]:
        L = math.lcm(wheel.W, self.mod)
        key = (wheel.W, self.mod, p % wheel.W)
        cached = self._candidate_cache.get(key)
        if cached is not None:
            return L, cached
        candidates = [
            m for m in range(1, L + 1) if math.gcd((p + m) % wheel.W, wheel.W) == 1
        ]
        self._candidate_cache[key] = candidates
        return L, candidates

    def baseline_mass(self, wheel: WheelFirstHit, p: int, symbol: int) -> float:
        _, candidates = self._period_candidates(wheel, p)
        theta = wheel.theta(p)
        q = 1.0 - theta
        c = len(candidates)
        denom = 1.0 - q**c
        mass = 0.0
        for idx, gap in enumerate(candidates, start=1):
            if gap % self.mod == symbol:
                mass += theta * (q ** (idx - 1)) / denom
        return max(mass, 1e-300)


def build_real_symbol_windows(
    min_exp: int,
    max_exp: int,
    wheel: WheelFirstHit,
    symbolizer: GapModSymbolizer,
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
        s = symbolizer.symbol(gap, p)
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


def synthetic_symbol_windows(
    real_windows: dict[int, list[SymbolEvent]],
    wheel: WheelFirstHit,
    symbolizer: GapModSymbolizer,
    rng: random.Random,
    null_mode: str = "fixed-count",
) -> dict[int, list[SymbolEvent]]:
    synthetic: dict[int, list[SymbolEvent]] = {}
    for exp, real_events in real_windows.items():
        if not real_events:
            synthetic[exp] = []
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
            s = symbolizer.symbol(gap, p)
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
        synthetic[exp] = events
    return synthetic


def evaluate_symbol_windows(
    windows: dict[int, list[SymbolEvent]],
    min_exp: int,
    max_exp: int,
    train_windows: int,
    alphabet_size: int,
    depth: int,
) -> list[dict[str, float]]:
    model = KTMarkovBuckets(alphabet_size, depth)
    rows = []

    def mix_prob_and_update(
        ev: SymbolEvent, logw_base: float, logw_markov: float
    ) -> tuple[float, float, float]:
        pb = max(ev.baseline_symbol_mass, 1e-300)
        pm = max(model.prob(ev.symbol), 1e-300)
        m0 = max(logw_base, logw_markov)
        wb = math.exp(logw_base - m0)
        wm = math.exp(logw_markov - m0)
        pu = (wb * pb + wm * pm) / (wb + wm)

        logw_base += math.log(pb)
        logw_markov += math.log(pm)
        z = max(logw_base, logw_markov)
        logw_base -= z
        logw_markov -= z
        model.update(ev.symbol)
        return max(pu, 1e-300), logw_base, logw_markov

    for exp in range(min_exp, max_exp + 1):
        events = windows[exp]
        if not events:
            continue
        if exp < min_exp + train_windows:
            for ev in events:
                model.update(ev.symbol)
            continue

        logw_base = math.log(0.5)
        logw_markov = math.log(0.5)
        gain = 0.0
        base_bits = 0.0
        u_bits = 0.0
        base_symbol_bits = 0.0
        u_symbol_bits = 0.0
        for ev in events:
            pb = max(ev.baseline_symbol_mass, 1e-300)
            pu, logw_base, logw_markov = mix_prob_and_update(
                ev, logw_base, logw_markov
            )
            delta = math.log2(pu) - math.log2(pb)
            gain += delta
            b_gap_bits = -ev.baseline_log2_gap
            base_bits += b_gap_bits
            u_bits += b_gap_bits - delta
            base_symbol_bits += -math.log2(pb)
            u_symbol_bits += -math.log2(pu)

        n = len(events)
        rows.append(
            {
                "exp": float(exp),
                "X": float(1 << exp),
                "n": float(n),
                "R_bits_per_gap": gain / n,
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
    wheel: WheelFirstHit,
    symbolizer: GapModSymbolizer,
    nulls: int,
    seed: int,
    null_mode: str = "fixed-count",
) -> dict[int, dict[str, float]]:
    by_exp: dict[int, list[float]] = defaultdict(list)
    rng = random.Random(seed)
    for _ in range(nulls):
        synth = synthetic_symbol_windows(real_windows, wheel, symbolizer, rng, null_mode)
        rows = evaluate_symbol_windows(
            synth, min_exp, max_exp, train_windows, alphabet_size, depth
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
            "null_p05": values[max(0, int(0.05 * (len(values) - 1)))],
            "null_p95": values[min(len(values) - 1, int(0.95 * (len(values) - 1)))],
        }
    return out


def run_baseline(
    label: str,
    y: int,
    symbolizer: GapModSymbolizer,
    args: argparse.Namespace,
) -> tuple[list[dict[str, float | str]], dict[str, object]]:
    wheel = WheelFirstHit(y)
    windows = build_real_symbol_windows(args.min_exp, args.max_exp, wheel, symbolizer)
    real_rows = evaluate_symbol_windows(
        windows,
        args.min_exp,
        args.max_exp,
        args.train_windows,
        symbolizer.alphabet_size,
        args.depth,
    )
    null_summary = summarize_nulls(
        windows,
        args.min_exp,
        args.max_exp,
        args.train_windows,
        symbolizer.alphabet_size,
        args.depth,
        wheel,
        symbolizer,
        args.nulls,
        args.seed,
        args.null_mode,
    )

    rows: list[dict[str, float | str]] = []
    for row in real_rows:
        exp = int(row["exp"])
        enriched: dict[str, float | str] = {
            "baseline": label,
            "y": float(y),
            "W": float(wheel.W),
            "phi_W": float(wheel.phi),
            "symbol": f"gap_mod_{symbolizer.mod}",
            "alphabet_size": float(symbolizer.alphabet_size),
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

    return rows, {"label": label, "y": y, "W": wheel.W, "phi_W": wheel.phi}


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
    parser.add_argument("--b1-y", type=int, default=11)
    parser.add_argument("--symbol-mod", type=int, default=210)
    parser.add_argument("--depth", type=int, default=0)
    parser.add_argument("--nulls", type=int, default=12)
    parser.add_argument(
        "--null-mode",
        choices=["fixed-count", "stop-time"],
        default="fixed-count",
    )
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--out", type=Path, default=Path("experiments/results_symbol_ladder"))
    args = parser.parse_args()

    symbolizer = GapModSymbolizer(args.symbol_mod)
    baselines = [("B0", 2), (f"B1({args.b1_y})", args.b1_y)]
    all_rows: list[dict[str, float | str]] = []
    metadata: dict[str, object] = {
        "min_exp": args.min_exp,
        "max_exp": args.max_exp,
        "train_windows": args.train_windows,
        "symbol_mod": args.symbol_mod,
        "depth": args.depth,
        "nulls": args.nulls,
        "null_mode": args.null_mode,
        "seed": args.seed,
        "baselines": [],
    }

    for label, y in baselines:
        rows, meta = run_baseline(label, y, symbolizer, args)
        all_rows.extend(rows)
        metadata["baselines"].append(meta)  # type: ignore[index]

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "symbol_ladder.csv", all_rows)
    (args.out / "symbol_ladder_metadata.json").write_text(
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
            f"{float(row['B_exact_bits_per_gap']):.6f},"
            f"{float(row['U_exact_bits_per_gap']):.6f}"
        )


if __name__ == "__main__":
    main()
