from __future__ import annotations

import math
import random
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "experiments"))

from rpi_b1_u1 import WheelFirstHit, bucket_edges  # noqa: E402


class WheelFirstHitSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wheel = WheelFirstHit(11)

    def test_b1_11_metadata(self) -> None:
        self.assertEqual(self.wheel.W, 2310)
        self.assertEqual(self.wheel.phi, 480)
        self.assertEqual(self.wheel.small_primes, [2, 3, 5, 7, 11])

    def test_offsets_for_residue_match_declared_wheel_support(self) -> None:
        for p in (13, 17, 101, 1_000_003):
            offsets = self.wheel.offsets_for_residue(p % self.wheel.W)
            offset_set = set(offsets)

            self.assertEqual(len(offsets), self.wheel.phi)
            self.assertEqual(len(offset_set), self.wheel.phi)
            self.assertEqual(offsets, sorted(offsets))
            self.assertTrue(all(1 <= m <= self.wheel.W for m in offsets))

            for m in range(1, self.wheel.W + 1):
                expected_admissible = math.gcd(p + m, self.wheel.W) == 1
                self.assertEqual(
                    m in offset_set,
                    expected_admissible,
                    f"p={p}, offset={m}, W={self.wheel.W}",
                )

    def test_kth_admissible_offset_is_ordered_and_counted_correctly(self) -> None:
        for p in (13, 17, 101, 1_000_003):
            previous = 0
            for k in range(1, 2 * self.wheel.phi + 25):
                offset = self.wheel.kth_admissible_offset(p, k)
                self.assertGreater(offset, previous)
                self.assertEqual(math.gcd(p + offset, self.wheel.W), 1)
                self.assertEqual(self.wheel.admissible_count_leq(p, offset), k)
                self.assertEqual(self.wheel.admissible_count_leq(p, offset - 1), k - 1)
                previous = offset

    def test_first_hit_probabilities_normalize_with_geometric_tail(self) -> None:
        p = 1_000_003
        theta = self.wheel.theta(p)
        q = 1.0 - theta
        terms = 600

        finite_mass = 0.0
        for k in range(1, terms + 1):
            offset = self.wheel.kth_admissible_offset(p, k)
            finite_mass += 2.0 ** self.wheel.log2_prob_gap(p, offset)

        self.assertAlmostEqual(finite_mass + q**terms, 1.0, places=12)

    def test_bucket_masses_partition_unity(self) -> None:
        edges = bucket_edges(width=0.5, max_value=8.0)
        for p in (13, 101, 1_000_003):
            total = sum(
                self.wheel.bucket_mass(p, b, edges)
                for b in range(len(edges) - 1)
            )
            self.assertAlmostEqual(total, 1.0, places=12)

    def test_sampled_gaps_are_wheel_admissible(self) -> None:
        rng = random.Random(20260616)
        for p in (13, 17, 101, 1_000_003):
            for _ in range(200):
                gap = self.wheel.sample_gap(p, rng)
                self.assertGreater(gap, 0)
                self.assertEqual(math.gcd(p + gap, self.wheel.W), 1)


if __name__ == "__main__":
    unittest.main()
