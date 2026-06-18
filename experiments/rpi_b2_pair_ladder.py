#!/usr/bin/env python3
"""
First B2-style ladder: pair/singular-series reweighting.

This is a deliberately small step beyond B1.  The baseline is still a
wheel-first-hit model, but each candidate gap m is reweighted by a truncated
Hardy-Littlewood pair factor for the tuple {0, m}:

    weight(m) = product_{q <= tuple_y}
        (1 - 1/q)^(-2) * (1 - nu_q({0,m})/q),

where nu_q is 1 if q divides m and 2 otherwise.  The resulting distribution is
renormalized over the periodic wheel-admissible candidate stream.

This is not a full consecutive-prime tuple baseline.  It only asks whether
the next layer of known pair arithmetic changes the residual tests that have
so far been explained by B1.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from rpi_b1_u1 import WheelFirstHit, prime_pairs_upto, small_primes_upto
from rpi_ctw_symbol_ladder import SparseCTW


class GapBaseline(Protocol):
    label: str
    y: int
    W: int
    phi: int

    def sample_gap(self, p: int, rng: random.Random) -> int:
        ...

    def log2_prob_gap(self, p: int, gap: int) -> float:
        ...

    def symbol_mass(self, p: int, symbol: int, symbolizer: "Symbolizer") -> float:
        ...


class Symbolizer(Protocol):
    name: str
    alphabet_size: int

    def symbol(self, baseline: GapBaseline, gap: int, p: int) -> int:
        ...


class GapModSymbolizer:
    def __init__(self, mod: int):
        if mod <= 1:
            raise ValueError("mod must be > 1")
        self.mod = mod
        self.name = f"gap_mod_{mod}"
        self.alphabet_size = mod

    def symbol(self, baseline: GapBaseline, gap: int, p: int) -> int:
        return gap % self.mod


class RankModSymbolizer:
    def __init__(self, mod: int):
        if mod <= 1:
            raise ValueError("mod must be > 1")
        self.mod = mod
        self.name = f"rank_mod_{mod}"
        self.alphabet_size = mod

    def symbol(self, baseline: GapBaseline, gap: int, p: int) -> int:
        if hasattr(baseline, "admissible_count_leq"):
            rank = baseline.admissible_count_leq(p, gap)  # type: ignore[attr-defined]
        else:
            rank = baseline.wheel.admissible_count_leq(p, gap)  # type: ignore[attr-defined]
        return rank % self.mod


class B1Baseline:
    def __init__(self, y: int):
        self.wheel = WheelFirstHit(y)
        self.label = f"B1({y})" if y > 2 else "B0"
        self.y = y
        self.W = self.wheel.W
        self.phi = self.wheel.phi
        self._symbol_cache: dict[tuple[int, str, int], list[float]] = {}

    def admissible_count_leq(self, p: int, gap: int) -> int:
        return self.wheel.admissible_count_leq(p, gap)

    def sample_gap(self, p: int, rng: random.Random) -> int:
        return self.wheel.sample_gap(p, rng)

    def log2_prob_gap(self, p: int, gap: int) -> float:
        return self.wheel.log2_prob_gap(p, gap)

    def symbol_mass(self, p: int, symbol: int, symbolizer: Symbolizer) -> float:
        if isinstance(symbolizer, RankModSymbolizer):
            theta = self.wheel.theta(p)
            q = 1.0 - theta
            first_rank = symbolizer.mod if symbol == 0 else symbol
            mass = theta * (q ** (first_rank - 1)) / (1.0 - q**symbolizer.mod)
            return max(mass, 1e-300)

        theta_key = int(round(self.wheel.theta(p) * 10**12))
        period = math.lcm(self.W, symbolizer.alphabet_size)
        key = (p % period, symbolizer.name, symbolizer.alphabet_size, theta_key)
        cached = self._symbol_cache.get(key)
        if cached is None:
            cached = [0.0] * symbolizer.alphabet_size
            theta = self.wheel.theta(p)
            q = 1.0 - theta
            offsets = [
                m
                for m in range(1, period + 1)
                if math.gcd((p + m) % self.W, self.W) == 1
            ]
            denom = 1.0 - q ** len(offsets)
            for idx, gap in enumerate(offsets, start=1):
                s = symbolizer.symbol(self, gap, p)
                cached[s] += theta * (q ** (idx - 1)) / denom
            self._symbol_cache[key] = cached
        return max(cached[symbol], 1e-300)


class B2PairBaseline:
    def __init__(self, wheel_y: int, tuple_y: int, pair_alpha: float = 1.0):
        if tuple_y < 2:
            raise ValueError("tuple_y must be >= 2")
        if pair_alpha < 0.0:
            raise ValueError("pair_alpha must be >= 0")
        self.wheel = WheelFirstHit(wheel_y)
        self.tuple_primes = small_primes_upto(tuple_y)
        self.pair_alpha = pair_alpha
        self.tuple_modulus = 1
        for q in self.tuple_primes:
            self.tuple_modulus *= q
        self.label = f"B2pair({wheel_y},{tuple_y},alpha={pair_alpha:g})"
        self.y = wheel_y
        self.tuple_y = tuple_y
        self.W = self.wheel.W
        self.phi = self.wheel.phi
        self.period = math.lcm(self.W, self.tuple_modulus)
        self._period_cache: dict[int, tuple[list[int], list[float]]] = {}
        self._norm_cache: dict[tuple[int, int], float] = {}
        self._symbol_cache: dict[tuple[object, ...], list[float]] = {}

    def admissible_count_leq(self, p: int, gap: int) -> int:
        return self.wheel.admissible_count_leq(p, gap)

    def _pair_factor(self, gap: int) -> float:
        if self.pair_alpha == 0.0:
            return 1.0
        factor = 1.0
        for q in self.tuple_primes:
            if gap % q == 0:
                local = (1.0 - 1.0 / q) ** -1
            else:
                local = (1.0 - 1.0 / q) ** -2 * (1.0 - 2.0 / q)
            if local <= 0.0:
                return 0.0
            factor *= local
        return factor**self.pair_alpha

    def _period_data(self, p: int) -> tuple[list[int], list[float]]:
        key = p % self.period
        cached = self._period_cache.get(key)
        if cached is not None:
            return cached
        gaps = [
            m
            for m in range(1, self.period + 1)
            if math.gcd((p + m) % self.W, self.W) == 1
        ]
        factors = [self._pair_factor(m) for m in gaps]
        cached = (gaps, factors)
        self._period_cache[key] = cached
        return cached

    def _period_norm(self, p: int) -> float:
        theta_key = int(round(self.wheel.theta(p) * 10**12))
        key = (p % self.period, theta_key)
        cached = self._norm_cache.get(key)
        if cached is not None:
            return cached
        _, factors = self._period_data(p)
        q = 1.0 - self.wheel.theta(p)
        norm = sum((q**idx) * factor for idx, factor in enumerate(factors))
        self._norm_cache[key] = norm
        return norm

    def _period_symbol_masses(self, p: int, symbolizer: Symbolizer) -> list[float]:
        if isinstance(symbolizer, RankModSymbolizer):
            gaps, factors = self._period_data(p)
            c = len(gaps)
            q = 1.0 - self.wheel.theta(p)
            superperiod = math.lcm(c, symbolizer.mod)
            key = (
                p % self.period,
                symbolizer.name,
                symbolizer.alphabet_size,
                int(round(q * 10**12)),
                superperiod,
            )
            cached = self._symbol_cache.get(key)
            if cached is not None:
                return cached
            norm = sum((q**idx) * factors[idx % c] for idx in range(superperiod))
            masses = [0.0] * symbolizer.alphabet_size
            for idx in range(superperiod):
                symbol = (idx + 1) % symbolizer.mod
                masses[symbol] += (q**idx) * factors[idx % c] / norm
            self._symbol_cache[key] = masses
            return masses

        theta_key = int(round(self.wheel.theta(p) * 10**12))
        key = (p % self.period, symbolizer.name, symbolizer.alphabet_size, theta_key)
        cached = self._symbol_cache.get(key)
        if cached is not None:
            return cached
        gaps, factors = self._period_data(p)
        q = 1.0 - self.wheel.theta(p)
        norm = self._period_norm(p)
        masses = [0.0] * symbolizer.alphabet_size
        for idx, (gap, factor) in enumerate(zip(gaps, factors)):
            s = symbolizer.symbol(self, gap, p)
            masses[s] += (q**idx) * factor / norm
        self._symbol_cache[key] = masses
        return masses

    def symbol_mass(self, p: int, symbol: int, symbolizer: Symbolizer) -> float:
        return max(self._period_symbol_masses(p, symbolizer)[symbol], 1e-300)

    def log2_prob_gap(self, p: int, gap: int) -> float:
        rank = self.wheel.admissible_count_leq(p, gap)
        if rank <= 0:
            return -math.inf
        gaps, factors = self._period_data(p)
        c = len(gaps)
        idx = (rank - 1) % c
        cycles = (rank - 1) // c
        q = 1.0 - self.wheel.theta(p)
        norm = self._period_norm(p)
        cycle_log = cycles * c * math.log2(q)
        period_stop = 1.0 - q**c
        return cycle_log + math.log2(period_stop * (q**idx) * factors[idx] / norm)

    def sample_gap(self, p: int, rng: random.Random) -> int:
        gaps, factors = self._period_data(p)
        c = len(gaps)
        q = 1.0 - self.wheel.theta(p)
        period_decay = q**c

        cycle = int(math.floor(math.log1p(-rng.random()) / math.log(period_decay)))
        norm = self._period_norm(p)
        target = rng.random()
        acc = 0.0
        idx = 0
        for idx, factor in enumerate(factors):
            acc += (q**idx) * factor / norm
            if acc >= target:
                break
        rank = cycle * c + idx + 1
        return self.wheel.kth_admissible_offset(p, rank)


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
    baseline: GapBaseline,
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
        s = symbolizer.symbol(baseline, gap, p)
        windows[exp].append(
            SymbolEvent(
                p=p,
                gap=gap,
                symbol=s,
                baseline_symbol_mass=baseline.symbol_mass(p, s, symbolizer),
                baseline_log2_gap=baseline.log2_prob_gap(p, gap),
            )
        )
    return windows


def synthetic_windows(
    real_windows: dict[int, list[SymbolEvent]],
    baseline: GapBaseline,
    symbolizer: Symbolizer,
    rng: random.Random,
) -> dict[int, list[SymbolEvent]]:
    out: dict[int, list[SymbolEvent]] = {}
    for exp, real_events in real_windows.items():
        if not real_events:
            out[exp] = []
            continue
        p = real_events[0].p
        events = []
        for _ in real_events:
            gap = baseline.sample_gap(p, rng)
            s = symbolizer.symbol(baseline, gap, p)
            events.append(
                SymbolEvent(
                    p=p,
                    gap=gap,
                    symbol=s,
                    baseline_symbol_mass=baseline.symbol_mass(p, s, symbolizer),
                    baseline_log2_gap=baseline.log2_prob_gap(p, gap),
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
) -> list[dict[str, float]]:
    model = SparseCTW(alphabet_size, depth)
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
        for ev in events:
            pb = max(ev.baseline_symbol_mass, 1e-300)
            pu, logw_base, logw_ctw = mix_prob_and_update(ev, logw_base, logw_ctw)
            delta = math.log2(pu) - math.log2(pb)
            gain += delta
            b_gap_bits = -ev.baseline_log2_gap
            base_bits += b_gap_bits
            u_bits += b_gap_bits - delta

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
            }
        )
    return rows


def run_baseline(
    baseline: GapBaseline,
    symbolizer: Symbolizer,
    args: argparse.Namespace,
) -> list[dict[str, float | str]]:
    windows = build_real_windows(args.min_exp, args.max_exp, baseline, symbolizer)
    real_rows = evaluate_windows(
        windows,
        args.min_exp,
        args.max_exp,
        args.train_windows,
        symbolizer.alphabet_size,
        args.depth,
    )

    null_values_by_exp: dict[int, list[float]] = defaultdict(list)
    rng = random.Random(args.seed)
    for _ in range(args.nulls):
        synth = synthetic_windows(windows, baseline, symbolizer, rng)
        for row in evaluate_windows(
            synth,
            args.min_exp,
            args.max_exp,
            args.train_windows,
            symbolizer.alphabet_size,
            args.depth,
        ):
            null_values_by_exp[int(row["exp"])].append(row["R_bits_per_gap"])

    rows: list[dict[str, float | str]] = []
    for row in real_rows:
        exp = int(row["exp"])
        values = sorted(null_values_by_exp[exp])
        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)
        ge = sum(1 for value in values if value >= row["R_bits_per_gap"])
        enriched: dict[str, float | str] = {
            "baseline": baseline.label,
            "y": float(baseline.y),
            "W": float(baseline.W),
            "phi_W": float(baseline.phi),
            "symbol": symbolizer.name,
            "alphabet_size": float(symbolizer.alphabet_size),
        }
        enriched.update(row)
        enriched.update(
            {
                "null_mean": mean,
                "null_sd": math.sqrt(var),
                "null_p05": values[max(0, int(0.05 * (len(values) - 1)))],
                "null_p50": values[len(values) // 2],
                "null_p95": values[min(len(values) - 1, int(0.95 * (len(values) - 1)))],
                "empirical_p_ge": (ge + 1.0) / (len(values) + 1.0),
            }
        )
        rows.append(enriched)
    return rows


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
        return GapModSymbolizer(mod)
    if name == "rank_mod":
        return RankModSymbolizer(mod)
    raise ValueError(f"unknown symbolizer: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-exp", type=int, default=12)
    parser.add_argument("--max-exp", type=int, default=20)
    parser.add_argument("--train-windows", type=int, default=3)
    parser.add_argument("--b1-y", type=int, default=11)
    parser.add_argument("--tuple-y", type=int, default=13)
    parser.add_argument("--pair-alpha", type=float, default=1.0)
    parser.add_argument("--symbolizer", choices=["gap_mod", "rank_mod"], default="rank_mod")
    parser.add_argument("--symbol-mod", type=int, default=64)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--nulls", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--out", type=Path, default=Path("experiments/results_b2_pair_ladder"))
    args = parser.parse_args()

    symbolizer = parse_symbolizer(args.symbolizer, args.symbol_mod)
    baselines: list[GapBaseline] = [
        B1Baseline(2),
        B1Baseline(args.b1_y),
        B2PairBaseline(args.b1_y, args.tuple_y, args.pair_alpha),
    ]
    rows: list[dict[str, float | str]] = []
    for baseline in baselines:
        rows.extend(run_baseline(baseline, symbolizer, args))

    metadata = {
        "min_exp": args.min_exp,
        "max_exp": args.max_exp,
        "train_windows": args.train_windows,
        "b1_y": args.b1_y,
        "tuple_y": args.tuple_y,
        "pair_alpha": args.pair_alpha,
        "symbolizer": args.symbolizer,
        "symbol_mod": args.symbol_mod,
        "depth": args.depth,
        "nulls": args.nulls,
        "seed": args.seed,
        "baselines": [
            {"label": b.label, "y": b.y, "W": b.W, "phi_W": b.phi}
            for b in baselines
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "b2_pair_ladder.csv", rows)
    (args.out / "b2_pair_ladder_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(json.dumps(metadata, indent=2))
    print()
    print("baseline,exp,X,n,R_bits_per_gap,B_bits,null_p95,empirical_p_ge,final_ctw_weight")
    for row in rows:
        print(
            f"{row['baseline']},{int(float(row['exp']))},{int(float(row['X']))},"
            f"{int(float(row['n']))},{float(row['R_bits_per_gap']):.6f},"
            f"{float(row['B_exact_bits_per_gap']):.6f},"
            f"{float(row['null_p95']):.6f},{float(row['empirical_p_ge']):.3f},"
            f"{float(row['final_ctw_weight']):.3f}"
        )


if __name__ == "__main__":
    main()
