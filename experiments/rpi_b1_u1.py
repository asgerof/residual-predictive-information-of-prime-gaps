#!/usr/bin/env python3
"""
Pilot test for residual predictive information in prime gaps:

    B1(y): wheel-corrected first-hit model
    U1:    Bayesian two-expert mixture:
           (a) B1 bucket probabilities
           (b) KT-smoothed finite-depth Markov predictor on buckets of g/log(p)

The exact-gap probability under U1 is defined as

    U1(g | history, p) =
        U1_bucket(b(g,p) | history, p) * B1(g | p, b(g,p)),

so the per-gap code gain over B1 is

    log2 U1_bucket(b | history, p) - log2 B1_bucket(b | p).

The B1 bucket expert is included in U1, so a positive gain requires the
residual Markov expert to improve prediction enough to overcome the mixture
penalty. This makes the residual model a bucket-level reweighting of B1, not
a hidden replacement for the arithmetic baseline.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import random
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def primes_upto(n: int) -> list[int]:
    if n < 2:
        return []
    sieve = bytearray(b"\x01") * (n + 1)
    sieve[0:2] = b"\x00\x00"
    limit = math.isqrt(n)
    for p in range(2, limit + 1):
        if sieve[p]:
            start = p * p
            sieve[start : n + 1 : p] = b"\x00" * (((n - start) // p) + 1)
    return [i for i, is_prime in enumerate(sieve) if is_prime]


def iter_primes_upto(n: int, segment_size: int = 1 << 20) -> Iterable[int]:
    """Yield primes up to n without materializing the full prime list."""
    if n < 2:
        return
    base = primes_upto(math.isqrt(n))
    for low in range(2, n + 1, segment_size):
        high = min(n, low + segment_size - 1)
        sieve = bytearray(b"\x01") * (high - low + 1)
        for composite in (0, 1):
            if low <= composite <= high:
                sieve[composite - low] = 0
        for p in base:
            start = max(p * p, ((low + p - 1) // p) * p)
            if start > high:
                continue
            sieve[start - low : high - low + 1 : p] = b"\x00" * (
                ((high - start) // p) + 1
            )
        for offset, is_prime in enumerate(sieve):
            if is_prime:
                yield low + offset


def prime_pairs_upto(n: int, segment_size: int = 1 << 20) -> Iterable[tuple[int, int]]:
    prev: int | None = None
    for p in iter_primes_upto(n, segment_size):
        if prev is not None:
            yield prev, p
        prev = p


def small_primes_upto(y: int) -> list[int]:
    return primes_upto(y)


def bucket_edges(width: float, max_value: float) -> list[float]:
    edges = []
    x = 0.0
    while x <= max_value + 1e-12:
        edges.append(round(x, 12))
        x += width
    edges.append(math.inf)
    return edges


def bucket_index(gap: int, p: int, edges: list[float]) -> int:
    value = gap / math.log(p)
    idx = bisect.bisect_right(edges, value) - 1
    return max(0, min(idx, len(edges) - 2))


class WheelFirstHit:
    def __init__(self, y: int):
        self.y = y
        self.small_primes = small_primes_upto(y)
        self.W = 1
        for q in self.small_primes:
            self.W *= q
        self.units = [r for r in range(self.W) if math.gcd(r, self.W) == 1]
        self.phi = len(self.units)
        self._offset_cache: dict[int, list[int]] = {}

    def theta(self, p: int) -> float:
        # Conditional success probability among wheel-admissible positions.
        raw = self.W / (self.phi * math.log(p))
        return min(max(raw, 1e-12), 1.0 - 1e-12)

    def offsets_for_residue(self, p_mod: int) -> list[int]:
        cached = self._offset_cache.get(p_mod)
        if cached is not None:
            return cached
        offsets = []
        for u in self.units:
            d = (u - p_mod) % self.W
            offsets.append(self.W if d == 0 else d)
        offsets.sort()
        self._offset_cache[p_mod] = offsets
        return offsets

    def admissible_count_leq(self, p: int, m: int) -> int:
        if m <= 0:
            return 0
        offsets = self.offsets_for_residue(p % self.W)
        full, rem = divmod(m, self.W)
        return full * self.phi + bisect.bisect_right(offsets, rem)

    def kth_admissible_offset(self, p: int, k: int) -> int:
        if k <= 0:
            raise ValueError("k must be positive")
        offsets = self.offsets_for_residue(p % self.W)
        full, idx = divmod(k - 1, self.phi)
        return full * self.W + offsets[idx]

    def sample_gap(self, p: int, rng: random.Random) -> int:
        theta = self.theta(p)
        q = 1.0 - theta
        # K is the 1-indexed admissible candidate at which the first hit occurs.
        k = int(math.floor(math.log1p(-rng.random()) / math.log(q))) + 1
        return self.kth_admissible_offset(p, k)

    def log2_prob_gap(self, p: int, gap: int) -> float:
        theta = self.theta(p)
        failures = self.admissible_count_leq(p, gap - 1)
        return failures * math.log2(1.0 - theta) + math.log2(theta)

    def bucket_mass(self, p: int, b: int, edges: list[float]) -> float:
        logp = math.log(p)
        lo = edges[b]
        hi = edges[b + 1]
        lower = max(1, math.ceil(lo * logp))
        before = self.admissible_count_leq(p, lower - 1)
        q = 1.0 - self.theta(p)
        if math.isinf(hi):
            return q**before
        upper = math.ceil(hi * logp) - 1
        if upper < lower:
            return 0.0
        through = self.admissible_count_leq(p, upper)
        count = through - before
        if count <= 0:
            return 0.0
        return (q**before) * (1.0 - q**count)


class KTMarkovBuckets:
    def __init__(self, alphabet_size: int, depth: int):
        self.K = alphabet_size
        self.depth = depth
        self.counts: dict[tuple[int, ...], list[int]] = defaultdict(
            lambda: [0] * self.K
        )
        self.history: list[int] = []

    def clone_empty(self) -> "KTMarkovBuckets":
        return KTMarkovBuckets(self.K, self.depth)

    def _contexts(self) -> Iterable[tuple[int, ...]]:
        max_depth = min(self.depth, len(self.history))
        for d in range(max_depth + 1):
            if d == 0:
                yield ()
            else:
                yield tuple(self.history[-d:])

    def prob(self, symbol: int) -> float:
        probs = []
        for ctx in self._contexts():
            counts = self.counts[ctx]
            total = sum(counts)
            probs.append((counts[symbol] + 0.5) / (total + 0.5 * self.K))
        return sum(probs) / len(probs)

    def update(self, symbol: int) -> None:
        for ctx in self._contexts():
            self.counts[ctx][symbol] += 1
        self.history.append(symbol)

    def train(self, symbols: Iterable[int]) -> None:
        for symbol in symbols:
            self.update(symbol)


@dataclass
class Event:
    p: int
    gap: int
    bucket: int
    b1_bucket_mass: float
    b1_log2_gap: float


def build_real_windows(
    min_exp: int,
    max_exp: int,
    wheel: WheelFirstHit,
    edges: list[float],
) -> dict[int, list[Event]]:
    limit = (1 << (max_exp + 1)) + 200_000
    windows: dict[int, list[Event]] = {m: [] for m in range(min_exp, max_exp + 1)}
    for p, p_next in prime_pairs_upto(limit):
        if p < (1 << min_exp):
            continue
        if p >= (1 << (max_exp + 1)):
            break
        m = p.bit_length() - 1
        if m < min_exp or m > max_exp:
            continue
        gap = p_next - p
        b = bucket_index(gap, p, edges)
        mass = max(wheel.bucket_mass(p, b, edges), 1e-300)
        windows[m].append(Event(p, gap, b, mass, wheel.log2_prob_gap(p, gap)))
    return windows


def synthetic_windows_from_lengths(
    real_windows: dict[int, list[Event]],
    wheel: WheelFirstHit,
    edges: list[float],
    rng: random.Random,
) -> dict[int, list[Event]]:
    synthetic: dict[int, list[Event]] = {}
    for m, real_events in real_windows.items():
        if not real_events:
            synthetic[m] = []
            continue
        p = real_events[0].p
        events = []
        for _ in real_events:
            gap = wheel.sample_gap(p, rng)
            b = bucket_index(gap, p, edges)
            mass = max(wheel.bucket_mass(p, b, edges), 1e-300)
            events.append(Event(p, gap, b, mass, wheel.log2_prob_gap(p, gap)))
            p += gap
        synthetic[m] = events
    return synthetic


def synthetic_windows_to_endpoints(
    real_windows: dict[int, list[Event]],
    wheel: WheelFirstHit,
    edges: list[float],
    rng: random.Random,
) -> dict[int, list[Event]]:
    synthetic: dict[int, list[Event]] = {}
    for m, real_events in real_windows.items():
        if not real_events:
            synthetic[m] = []
            continue
        p = real_events[0].p
        stop = 1 << (m + 1)
        events = []
        while p < stop:
            gap = wheel.sample_gap(p, rng)
            b = bucket_index(gap, p, edges)
            mass = max(wheel.bucket_mass(p, b, edges), 1e-300)
            events.append(Event(p, gap, b, mass, wheel.log2_prob_gap(p, gap)))
            p += gap
        synthetic[m] = events
    return synthetic


def synthetic_windows(
    real_windows: dict[int, list[Event]],
    wheel: WheelFirstHit,
    edges: list[float],
    rng: random.Random,
    null_mode: str,
) -> dict[int, list[Event]]:
    if null_mode == "fixed-count":
        return synthetic_windows_from_lengths(real_windows, wheel, edges, rng)
    if null_mode == "stop-time":
        return synthetic_windows_to_endpoints(real_windows, wheel, edges, rng)
    raise ValueError(f"unknown null_mode: {null_mode}")


def evaluate_windows(
    windows: dict[int, list[Event]],
    min_exp: int,
    max_exp: int,
    train_windows: int,
    alphabet_size: int,
    depth: int,
) -> list[dict[str, float]]:
    rows = []
    model = KTMarkovBuckets(alphabet_size, depth)

    def mixture_prob_and_update(
        ev: Event, logw_b1: float, logw_markov: float
    ) -> tuple[float, float, float]:
        pb = max(ev.b1_bucket_mass, 1e-300)
        pm = max(model.prob(ev.bucket), 1e-300)
        m0 = max(logw_b1, logw_markov)
        wb = math.exp(logw_b1 - m0)
        wm = math.exp(logw_markov - m0)
        pu = (wb * pb + wm * pm) / (wb + wm)

        logw_b1 += math.log(pb)
        logw_markov += math.log(pm)
        z = max(logw_b1, logw_markov)
        logw_b1 -= z
        logw_markov -= z
        model.update(ev.bucket)
        return max(pu, 1e-300), logw_b1, logw_markov

    for m in range(min_exp, max_exp + 1):
        events = windows[m]
        if not events:
            continue
        testable = m >= min_exp + train_windows
        gain = 0.0
        b1_bits = 0.0
        u1_bits = 0.0
        bucket_b1_bits = 0.0
        bucket_u1_bits = 0.0
        if testable:
            # The Markov counts are trained on earlier windows. Expert weights
            # are reset for each held-out window, so trying the residual expert
            # costs about one bit per window rather than being killed forever by
            # poor early-window performance.
            logw_b1 = math.log(0.5)
            logw_markov = math.log(0.5)
            for ev in events:
                pb = max(ev.b1_bucket_mass, 1e-300)
                pu, logw_b1, logw_markov = mixture_prob_and_update(
                    ev, logw_b1, logw_markov
                )
                delta = math.log2(pu) - math.log2(pb)
                gain += delta
                b1_gap_bits = -ev.b1_log2_gap
                b1_bits += b1_gap_bits
                u1_bits += b1_gap_bits - delta
                bucket_b1_bits += -math.log2(pb)
                bucket_u1_bits += -math.log2(pu)
            n = len(events)
            rows.append(
                {
                    "exp": m,
                    "X": float(1 << m),
                    "n": float(n),
                    "R_bits_per_gap": gain / n,
                    "B1_exact_bits_per_gap": b1_bits / n,
                    "U1_exact_bits_per_gap": u1_bits / n,
                    "B1_bucket_bits_per_gap": bucket_b1_bits / n,
                    "U1_bucket_bits_per_gap": bucket_u1_bits / n,
                }
            )
        else:
            for ev in events:
                model.update(ev.bucket)
    return rows


def summarize_nulls(
    real_windows: dict[int, list[Event]],
    min_exp: int,
    max_exp: int,
    train_windows: int,
    alphabet_size: int,
    depth: int,
    wheel: WheelFirstHit,
    edges: list[float],
    nulls: int,
    seed: int,
    null_mode: str = "fixed-count",
    checkpoint_path: Path | None = None,
    resume: bool = False,
    checkpoint_every_seconds: float = 120.0,
) -> dict[int, dict[str, float]]:
    by_exp: dict[int, list[float]] = defaultdict(list)
    if checkpoint_path is None:
        rng = random.Random(seed)
        for _ in range(nulls):
            synth = synthetic_windows(real_windows, wheel, edges, rng, null_mode)
            rows = evaluate_windows(
                synth, min_exp, max_exp, train_windows, alphabet_size, depth
            )
            for row in rows:
                by_exp[int(row["exp"])].append(row["R_bits_per_gap"])
        return summarize_null_values(by_exp)

    completed: set[int] = set()
    last_report = time.monotonic()
    if resume:
        completed, loaded = load_null_checkpoint(checkpoint_path)
        by_exp.update(loaded)
    elif checkpoint_path.exists():
        checkpoint_path.unlink()

    for null_index in range(nulls):
        if null_index in completed:
            continue
        rng = random.Random(seed + null_index)
        synth = synthetic_windows(real_windows, wheel, edges, rng, null_mode)
        rows = evaluate_windows(
            synth, min_exp, max_exp, train_windows, alphabet_size, depth
        )
        append_null_checkpoint(checkpoint_path, null_index, rows)
        for row in rows:
            by_exp[int(row["exp"])].append(row["R_bits_per_gap"])
        now = time.monotonic()
        if now - last_report >= checkpoint_every_seconds:
            print(
                f"checkpointed {len(completed | set(range(null_index + 1)))}/{nulls} nulls "
                f"to {checkpoint_path}",
                flush=True,
            )
            last_report = now

    return summarize_null_values(by_exp)


def summarize_null_values(
    by_exp: dict[int, list[float]],
) -> dict[int, dict[str, float]]:
    out = {}
    for m, values in by_exp.items():
        values_sorted = sorted(values)
        out[m] = {
            "null_mean": statistics.fmean(values),
            "null_sd": statistics.pstdev(values) if len(values) > 1 else 0.0,
            "null_p05": values_sorted[max(0, int(0.05 * (len(values) - 1)))],
            "null_p95": values_sorted[min(len(values) - 1, int(0.95 * (len(values) - 1)))],
        }
    return out


def write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-exp", type=int, default=12)
    parser.add_argument("--max-exp", type=int, default=23)
    parser.add_argument("--train-windows", type=int, default=3)
    parser.add_argument("--y", type=int, default=11)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--bucket-width", type=float, default=0.5)
    parser.add_argument("--bucket-max", type=float, default=8.0)
    parser.add_argument("--nulls", type=int, default=50)
    parser.add_argument(
        "--checkpoint-nulls",
        action="store_true",
        help="Write raw null-replicate rows after each completed null.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from an existing null checkpoint in the output directory.",
    )
    parser.add_argument("--checkpoint-every-seconds", type=float, default=120.0)
    parser.add_argument(
        "--null-mode",
        choices=["fixed-count", "stop-time"],
        default="fixed-count",
    )
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--out", type=Path, default=Path("experiments/results"))
    args = parser.parse_args()

    edges = bucket_edges(args.bucket_width, args.bucket_max)
    wheel = WheelFirstHit(args.y)
    real_windows = build_real_windows(args.min_exp, args.max_exp, wheel, edges)
    alphabet_size = len(edges) - 1

    real_rows = evaluate_windows(
        real_windows,
        args.min_exp,
        args.max_exp,
        args.train_windows,
        alphabet_size,
        args.depth,
    )
    null_summary = summarize_nulls(
        real_windows,
        args.min_exp,
        args.max_exp,
        args.train_windows,
        alphabet_size,
        args.depth,
        wheel,
        edges,
        args.nulls,
        args.seed,
        args.null_mode,
        args.out / "b1_u1_null_checkpoint.csv" if args.checkpoint_nulls else None,
        args.resume,
        args.checkpoint_every_seconds,
    )

    rows = []
    for row in real_rows:
        m = int(row["exp"])
        enriched = dict(row)
        enriched.update(null_summary[m])
        sd = enriched["null_sd"]
        enriched["z_vs_null"] = (
            (enriched["R_bits_per_gap"] - enriched["null_mean"]) / sd
            if sd > 0
            else 0.0
        )
        rows.append(enriched)

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "b1_u1_real_vs_null.csv", rows)
    metadata = {
        "min_exp": args.min_exp,
        "max_exp": args.max_exp,
        "train_windows": args.train_windows,
        "y": args.y,
        "W": wheel.W,
        "phi_W": wheel.phi,
        "depth": args.depth,
        "bucket_edges": edges,
        "nulls": args.nulls,
        "null_mode": args.null_mode,
        "checkpoint_nulls": args.checkpoint_nulls,
        "checkpoint_file": (
            "b1_u1_null_checkpoint.csv" if args.checkpoint_nulls else None
        ),
        "seed": args.seed,
    }
    (args.out / "b1_u1_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(json.dumps(metadata, indent=2))
    print()
    print(
        "exp,X,n,R_bits_per_gap,null_mean,null_sd,z_vs_null,"
        "B1_exact_bits_per_gap,U1_exact_bits_per_gap"
    )
    for row in rows:
        print(
            f"{int(row['exp'])},{int(row['X'])},{int(row['n'])},"
            f"{row['R_bits_per_gap']:.6f},{row['null_mean']:.6f},"
            f"{row['null_sd']:.6f},{row['z_vs_null']:.2f},"
            f"{row['B1_exact_bits_per_gap']:.6f},"
            f"{row['U1_exact_bits_per_gap']:.6f}"
        )


if __name__ == "__main__":
    main()
