#!/usr/bin/env python3
"""
Estimate paper-suite runtimes before launching long experiments.

The estimates are intentionally conservative planning numbers, not benchmark
claims.  They scale from measured probes on the current machine and from the
expected number of prime gaps in dyadic windows.
"""

from __future__ import annotations

import argparse
import json
import math


MEASURED_GAPS = {
    15: 3030,
    16: 5709,
    17: 10749,
    18: 20390,
    19: 38635,
    20: 73586,
    21: 140336,
    22: 268216,
}

CALIBRATIONS = {
    "b1_stop_time": {
        "seconds": 159.55,
        "max_exp": 22,
        "nulls": 12,
        "description": "B1(11) bucket residual, stop-time nulls",
    },
    "ctw_rank64_stop_time": {
        "seconds": 58.08,
        "max_exp": 20,
        "nulls": 12,
        "description": "rank-mod-64 CTW ladder, stop-time nulls",
    },
}


def estimated_gaps_by_exp(max_exp: int) -> dict[int, int]:
    anchor_exp = max(MEASURED_GAPS)
    anchor_scale = MEASURED_GAPS[anchor_exp] / (
        (2**anchor_exp) / math.log(2**anchor_exp)
    )
    out = {}
    for exp in range(15, max_exp + 1):
        if exp in MEASURED_GAPS:
            out[exp] = MEASURED_GAPS[exp]
        else:
            out[exp] = int(anchor_scale * (2**exp) / math.log(2**exp))
    return out


def calibrated_total_gaps(max_exp: int) -> int:
    counts = estimated_gaps_by_exp(max_exp)
    return sum(counts.values())


def estimate_seconds(kind: str, max_exp: int, nulls: int) -> float:
    cal = CALIBRATIONS[kind]
    cal_total = calibrated_total_gaps(cal["max_exp"])
    target_total = calibrated_total_gaps(max_exp)
    return cal["seconds"] * target_total * (nulls + 1) / (
        cal_total * (cal["nulls"] + 1)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-exp", type=int, required=True)
    parser.add_argument("--nulls", type=int, required=True)
    parser.add_argument(
        "--kind",
        choices=sorted(CALIBRATIONS),
        default="b1_stop_time",
    )
    args = parser.parse_args()

    seconds = estimate_seconds(args.kind, args.max_exp, args.nulls)
    print(
        json.dumps(
            {
                "kind": args.kind,
                "description": CALIBRATIONS[args.kind]["description"],
                "max_exp": args.max_exp,
                "nulls": args.nulls,
                "estimated_seconds": seconds,
                "estimated_minutes": seconds / 60.0,
                "estimated_hours": seconds / 3600.0,
                "estimated_latest_window_gaps": estimated_gaps_by_exp(args.max_exp)[
                    args.max_exp
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
