# Paper-Scale Experiment Plan

Date: 2026-06-16.

## Purpose

The existing artifacts are pilot-scale.  The next run should not reduce
quality to fit an interactive time budget.  It should instead lock a
paper-scale suite and run it as a long batch job.

## Current Machine

- CPU: Intel Core i7-7700HQ, 4 cores / 8 logical processors.
- RAM: about 16 GB.
- Free C: drive space during planning: about 25 GB.

Timing probes on the existing scripts:

- `B1(11)` stop-time null to `X=2^22`, 12 nulls: about 160 seconds.
- rank-mod CTW stop-time control to `X=2^20`, 12 nulls: about 58 seconds.

## Minimum Paper-Scale Suite

Use the same predeclared protocol for all main results:

1. `B1(11)` bucket residual with stop-time nulls.
2. rank-mod-64 CTW positive/negative control with stop-time nulls.
3. B0/B1 exact baseline ladder on the same maximum dyadic range.
4. Keep the existing B2 scans as prototype negative controls unless a new
   canonical B2 model is introduced.

Recommended first paper-scale target:

```powershell
python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 26 --train-windows 3 --nulls 200 --null-mode stop-time --checkpoint-nulls --checkpoint-every-seconds 120 --y 11 --depth 4 --out experiments\paper_b1_y11_depth4_stop_time_x26_n200

python experiments\rpi_ctw_symbol_ladder.py --min-exp 12 --max-exp 26 --train-windows 3 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 200 --null-mode stop-time --checkpoint-nulls --checkpoint-every-seconds 120 --out experiments\paper_ctw_rank64_depth1_stop_time_x26_n200

python experiments\rpi_baseline_ladder.py --min-exp 12 --max-exp 26 --train-windows 3 --nulls 200 --checkpoint-nulls --checkpoint-every-seconds 120 --b1-y 11 --depth 4 --out experiments\paper_ladder_b0_b1_y11_x26_n200
```

Resume after an interruption by rerunning the same command with `--resume`:

```powershell
python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 26 --train-windows 3 --nulls 200 --null-mode stop-time --checkpoint-nulls --resume --checkpoint-every-seconds 120 --y 11 --depth 4 --out experiments\paper_b1_y11_depth4_stop_time_x26_n200

python experiments\rpi_ctw_symbol_ladder.py --min-exp 12 --max-exp 26 --train-windows 3 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 200 --null-mode stop-time --checkpoint-nulls --resume --checkpoint-every-seconds 120 --out experiments\paper_ctw_rank64_depth1_stop_time_x26_n200

python experiments\rpi_baseline_ladder.py --min-exp 12 --max-exp 26 --train-windows 3 --nulls 200 --checkpoint-nulls --resume --checkpoint-every-seconds 120 --b1-y 11 --depth 4 --out experiments\paper_ladder_b0_b1_y11_x26_n200
```

Estimated wall time on the current machine:

- `B1(11)` stop-time, `X=2^26`, 200 nulls: about 9.3 hours.
- rank-mod CTW stop-time, `X=2^26`, 200 nulls: about 12.4 hours.
- Full main suite above: roughly one day, allowing overhead and thermal
  throttling.

Do not run this interactively under a 20 minute budget.

## Artifact Rules

- Write paper-scale outputs to new `experiments/paper_*` directories.
- For long null runs, use `--checkpoint-nulls`; each completed null replicate
  is appended to a checkpoint CSV and can be resumed with `--resume`.
- After a run completes, update `experiments/final_manifest.json` deliberately.
- Do not let `rpi_final_report.py` discover result directories implicitly.
- Keep pilot artifacts available, but do not mix them with paper-scale
  artifacts in the same final report.

## Review-Facing Criteria

The paper should not claim positive residual information unless all of these
hold:

- Positive code gain survives `B1(11)` and stop-time nulls.
- The gain appears under at least two independent residual symbolizations.
- The gain is absent or much weaker in synthetic null sequences.
- The gain persists over increasing dyadic windows.
- Tuning is chronological; oracle rows remain diagnostics only.

If the paper-scale suite remains negative, the publishable claim is the
protocol plus a negative result at the tested scale.
