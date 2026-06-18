#!/usr/bin/env python3
"""
B2-style consecutive-prime correction ladder.

The earlier B2 pair prototype reweighted a candidate gap using only the
Hardy-Littlewood pair factor for {0, g}.  That is not really a consecutive
prime-gap model: a gap also asserts that every admissible candidate between
0 and g failed to be prime.

This script implements a first finite consecutive correction.  For a wheel
admissible candidate of rank k and gap g, let H be the earlier wheel
admissible offsets.  The correction factor is a truncated inclusion-exclusion
estimate of

    P(no h in H is prime | p and p + g are prime),

using singular-series ratios for {0, g} union subsets of H.  The truncation
order is controlled by --ie-order.  The --consecutive-alpha parameter shrinks
the correction toward B1, with alpha=0 exactly equal to B1.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import random
from functools import lru_cache
from pathlib import Path

from rpi_b1_u1 import WheelFirstHit, small_primes_upto
from rpi_b2_pair_ladder import B1Baseline, RankModSymbolizer, run_baseline


class B2ConsecutiveBaseline:
    def __init__(
        self,
        wheel_y: int,
        tuple_y: int,
        ie_order: int = 2,
        consecutive_alpha: float = 1.0,
        max_rank: int = 128,
        max_correction_rank: int = 32,
        pair_alpha: float = 0.0,
        min_factor: float = 1e-6,
    ):
        if tuple_y < 2:
            raise ValueError("tuple_y must be >= 2")
        if ie_order < 1:
            raise ValueError("ie_order must be >= 1")
        if consecutive_alpha < 0.0:
            raise ValueError("consecutive_alpha must be >= 0")
        if pair_alpha < 0.0:
            raise ValueError("pair_alpha must be >= 0")
        if max_rank < 8:
            raise ValueError("max_rank must be >= 8")
        if max_correction_rank < 2:
            raise ValueError("max_correction_rank must be >= 2")
        if not 0.0 < min_factor <= 1.0:
            raise ValueError("min_factor must be in (0, 1]")

        self.wheel = WheelFirstHit(wheel_y)
        self.tuple_primes = small_primes_upto(tuple_y)
        self.ie_order = ie_order
        self.consecutive_alpha = consecutive_alpha
        self.pair_alpha = pair_alpha
        self.max_rank = max_rank
        self.max_correction_rank = min(max_correction_rank, max_rank)
        self.min_factor = min_factor
        if pair_alpha == 0.0:
            self.label = (
                f"B2consec({wheel_y},{tuple_y},r={ie_order},"
                f"alpha={consecutive_alpha:g})"
            )
        else:
            self.label = (
                f"B2consec({wheel_y},{tuple_y},r={ie_order},"
                f"pair={pair_alpha:g},excl={consecutive_alpha:g})"
            )
        self.y = wheel_y
        self.tuple_y = tuple_y
        self.W = self.wheel.W
        self.phi = self.wheel.phi

    def admissible_count_leq(self, p: int, gap: int) -> int:
        return self.wheel.admissible_count_leq(p, gap)

    def _offset_for_rank_mod(self, p_mod: int, rank: int) -> int:
        return self.wheel.kth_admissible_offset(p_mod, rank)

    @lru_cache(maxsize=None)
    def _singular_series(self, offsets: tuple[int, ...]) -> float:
        offsets = tuple(sorted(set(offsets)))
        size = len(offsets)
        factor = 1.0
        for q in self.tuple_primes:
            nu = len({h % q for h in offsets})
            local = (1.0 - 1.0 / q) ** (-size) * (1.0 - nu / q)
            if local <= 0.0:
                return 0.0
            factor *= local
        return factor

    @lru_cache(maxsize=None)
    def _ie_coefficients(self, p_mod: int, rank: int) -> tuple[float, ...]:
        if rank <= 1:
            return ()

        gap = self._offset_for_rank_mod(p_mod, rank)
        intermediates = tuple(
            self._offset_for_rank_mod(p_mod, k) for k in range(1, rank)
        )
        base = self._singular_series((0, gap))
        if base <= 0.0:
            return tuple(0.0 for _ in range(min(self.ie_order, len(intermediates))))

        coeffs: list[float] = []
        max_order = min(self.ie_order, len(intermediates))
        for order in range(1, max_order + 1):
            subtotal = 0.0
            for subset in itertools.combinations(intermediates, order):
                offsets = tuple(sorted((0, gap, *subset)))
                subtotal += self._singular_series(offsets) / base
            coeffs.append(subtotal)
        return tuple(coeffs)

    @lru_cache(maxsize=None)
    def _pair_factor_for_rank(self, p_mod: int, rank: int) -> float:
        if self.pair_alpha == 0.0:
            return 1.0
        gap = self._offset_for_rank_mod(p_mod, rank)
        pair = self._singular_series((0, gap))
        return max(self.min_factor, pair**self.pair_alpha)

    def _consecutive_factor(self, p: int, rank: int) -> float:
        if (
            self.consecutive_alpha == 0.0
            or rank <= 1
            or rank > self.max_correction_rank
        ):
            return 1.0

        logp = math.log(p)
        raw = 1.0
        for order, coeff in enumerate(
            self._ie_coefficients(p % self.W, rank), start=1
        ):
            raw += ((-1.0) ** order) * coeff / (logp**order)

        shrunk = 1.0 + self.consecutive_alpha * (raw - 1.0)
        return max(self.min_factor, shrunk)

    def _distribution(
        self, p: int, min_rank: int | None = None
    ) -> tuple[list[float], float, float]:
        theta = self.wheel.theta(p)
        q = 1.0 - theta
        rank_limit = self.max_rank if min_rank is None else max(self.max_rank, min_rank)

        weights = []
        q_power = 1.0
        p_mod = p % self.W
        for rank in range(1, rank_limit + 1):
            factor = self._pair_factor_for_rank(p_mod, rank)
            factor *= self._consecutive_factor(p, rank)
            weights.append(q_power * factor)
            q_power *= q

        # The explicit finite correction is only trusted on the head of the
        # distribution.  Ranks above max_correction_rank and the far tail fall
        # back to B1, which keeps normalization stable and makes alpha=0
        # exactly recover B1.
        tail_weight = q_power / theta
        norm = sum(weights) + tail_weight
        probabilities = [weight / norm for weight in weights]
        return probabilities, tail_weight / norm, norm

    def log2_prob_gap(self, p: int, gap: int) -> float:
        rank = self.wheel.admissible_count_leq(p, gap)
        if rank <= 0:
            return -math.inf
        probabilities, _, _ = self._distribution(p, rank)
        if rank <= len(probabilities):
            return math.log2(max(probabilities[rank - 1], 1e-300))

        theta = self.wheel.theta(p)
        q = 1.0 - theta
        _, _, norm = self._distribution(p, rank)
        return math.log2(max((q ** (rank - 1)) / norm, 1e-300))

    def symbol_mass(self, p: int, symbol: int, symbolizer: RankModSymbolizer) -> float:
        if not isinstance(symbolizer, RankModSymbolizer):
            raise TypeError("B2ConsecutiveBaseline currently supports rank_mod only")

        probabilities, _, norm = self._distribution(p)
        mass = 0.0
        for idx, prob in enumerate(probabilities, start=1):
            if idx % symbolizer.mod == symbol:
                mass += prob

        theta = self.wheel.theta(p)
        q = 1.0 - theta
        first_tail_rank = len(probabilities) + 1
        target = symbolizer.mod if symbol == 0 else symbol
        delta = (target - (first_tail_rank % symbolizer.mod)) % symbolizer.mod
        first = first_tail_rank + delta
        tail_sum = (q ** (first - 1)) / (1.0 - q**symbolizer.mod)
        mass += tail_sum / norm
        return max(mass, 1e-300)

    def sample_gap(self, p: int, rng: random.Random) -> int:
        probabilities, tail_mass, _ = self._distribution(p)
        target = rng.random()
        acc = 0.0
        for rank, prob in enumerate(probabilities, start=1):
            acc += prob
            if target <= acc:
                return self.wheel.kth_admissible_offset(p, rank)

        theta = self.wheel.theta(p)
        q = 1.0 - theta
        remaining = max(0.0, min(1.0, (target - acc) / max(tail_mass, 1e-300)))
        extra = int(math.floor(math.log1p(-remaining) / math.log(q))) + 1
        return self.wheel.kth_admissible_offset(p, len(probabilities) + extra)


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
    parser.add_argument("--consecutive-alpha", type=float, default=1.0)
    parser.add_argument("--pair-alpha", type=float, default=0.0)
    parser.add_argument("--symbol-mod", type=int, default=64)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--max-rank", type=int, default=128)
    parser.add_argument("--max-correction-rank", type=int, default=32)
    parser.add_argument("--nulls", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/results_b2_consecutive_ladder"),
    )
    args = parser.parse_args()

    symbolizer = RankModSymbolizer(args.symbol_mod)
    baselines = [
        B1Baseline(2),
        B1Baseline(args.b1_y),
        B2ConsecutiveBaseline(
            args.b1_y,
            args.tuple_y,
            args.ie_order,
            args.consecutive_alpha,
            args.max_rank,
            args.max_correction_rank,
            args.pair_alpha,
        ),
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
        "ie_order": args.ie_order,
        "consecutive_alpha": args.consecutive_alpha,
        "pair_alpha": args.pair_alpha,
        "symbolizer": "rank_mod",
        "symbol_mod": args.symbol_mod,
        "depth": args.depth,
        "max_rank": args.max_rank,
        "max_correction_rank": args.max_correction_rank,
        "nulls": args.nulls,
        "seed": args.seed,
        "baselines": [
            {"label": b.label, "y": b.y, "W": b.W, "phi_W": b.phi}
            for b in baselines
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "b2_consecutive_ladder.csv", rows)
    (args.out / "b2_consecutive_ladder_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(json.dumps(metadata, indent=2))
    print()
    print("baseline,exp,X,n,R_bits_per_gap,B_bits,null_p95,empirical_p_ge,ctw_weight")
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
