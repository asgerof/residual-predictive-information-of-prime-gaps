# Paper-Scale Experiment Plan and Status

Date: 2026-06-28.

## Status

The first paper-scale suite has been completed and merged.

Completed artifacts:

- `experiments/paper_b1_y11_depth4_stop_time_x26_n200/`
- `experiments/paper_ctw_rank64_depth1_stop_time_x26_n200/`
- `experiments/paper_ladder_b0_b1_y11_x26_n200/`
- `experiments/paper_logs/`

All main runs use:

- `min_exp = 12`
- `max_exp = 26`
- `train_windows = 3`
- `nulls = 200`
- `seed = 20260616`
- checkpointed/resumable nulls

## Purpose

The paper-scale suite fixes the main empirical question:

> Does an online residual predictor detect positive residual predictive
> information in consecutive prime gaps after the wheel-first-hit baseline
> `B1(11)` has already absorbed known arithmetic structure?

The result of this first suite is negative: no positive residual signal is
detected beyond `B1(11)` through `X = 2^26`, while positive controls against
`B0` pass.

## Completed Main Runs

### B1(11) bucket residual, stop-time null

```powershell
python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 26 --train-windows 3 --nulls 200 --null-mode stop-time --checkpoint-nulls --checkpoint-every-seconds 120 --y 11 --depth 4 --out experiments\paper_b1_y11_depth4_stop_time_x26_n200
```

Resume form:

```powershell
python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 26 --train-windows 3 --nulls 200 --null-mode stop-time --checkpoint-nulls --resume --checkpoint-every-seconds 120 --y 11 --depth 4 --out experiments\paper_b1_y11_depth4_stop_time_x26_n200
```

### rank_mod_64 CTW control, stop-time null

```powershell
python experiments\rpi_ctw_symbol_ladder.py --min-exp 12 --max-exp 26 --train-windows 3 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 200 --null-mode stop-time --checkpoint-nulls --checkpoint-every-seconds 120 --out experiments\paper_ctw_rank64_depth1_stop_time_x26_n200
```

Resume form:

```powershell
python experiments\rpi_ctw_symbol_ladder.py --min-exp 12 --max-exp 26 --train-windows 3 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 200 --null-mode stop-time --checkpoint-nulls --resume --checkpoint-every-seconds 120 --out experiments\paper_ctw_rank64_depth1_stop_time_x26_n200
```

### B0/B1 exact baseline ladder

```powershell
python experiments\rpi_baseline_ladder.py --min-exp 12 --max-exp 26 --train-windows 3 --nulls 200 --checkpoint-nulls --checkpoint-every-seconds 120 --b1-y 11 --depth 4 --out experiments\paper_ladder_b0_b1_y11_x26_n200
```

Resume form:

```powershell
python experiments\rpi_baseline_ladder.py --min-exp 12 --max-exp 26 --train-windows 3 --nulls 200 --checkpoint-nulls --resume --checkpoint-every-seconds 120 --b1-y 11 --depth 4 --out experiments\paper_ladder_b0_b1_y11_x26_n200
```

## Artifact Rules

- Paper-scale outputs live in `experiments/paper_*` directories.
- Long null runs use `--checkpoint-nulls`; each completed null replicate is
  appended to a checkpoint CSV and can be resumed with `--resume`.
- `experiments/final_manifest.json` pins the artifacts used in the compact
  final report.
- Pilot artifacts remain available, but the headline final report should use
  paper-scale artifacts for the main claim.

## Review-Facing Criteria

The paper should not claim positive residual information unless all of these
hold:

- Positive code gain survives `B1(11)` and stop-time nulls.
- The gain appears under at least two independent residual symbolizations.
- The gain is absent or much weaker in synthetic null sequences.
- The gain persists over increasing dyadic windows.
- Tuning is chronological; oracle rows remain diagnostics only.

The first paper-scale suite does not meet these criteria for a positive claim.
The publishable claim is the protocol plus a negative result at the tested
scale.
