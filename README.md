# Residual Predictive Information of Prime Gaps

This repository contains a research-note formulation and reproducible
experiments for measuring residual predictive information in consecutive prime
gaps.

The central statistic is the prequential per-gap code gain

\[
R_k(X)=\frac{L_{B_k}(G_X)-L_{U_k}(G_X)}{|G_X|},
\]

where \(B_k\) is an explicit arithmetic baseline and \(U_k\) is a penalized
online residual predictor. The question is whether previous gap history
improves prediction after known arithmetic structure has already been built into
the null model.

## Current Empirical Status

The paper-scale suite is now complete for the main tests through
`X = 2^26` with `200` null replicates/checkpoints:

- `B1(11)` bucket residual with stop-time synthetic nulls.
- `rank_mod_64` CTW residual control with stop-time synthetic nulls.
- B0/B1 exact baseline ladder over the same dyadic range.

Bottom line: the experiments do **not** detect positive residual predictive
information beyond the wheel-first-hit baseline `B1(11)` at the tested scale.

The controls behave as desired. Residual coders find large apparent signal
against the weak `B0` baseline, but that signal disappears once the arithmetic
wheel-first-hit baseline `B1(11)` is used. This supports the interpretation
that the detected structure is arithmetic baseline structure, not robust
residual sequential information.

## Paper-Scale Headline Results

At `X = 2^26`:

- Main `B1(11)` bucket residual:
  - `R = -2.7429243523407067e-07` bits/gap.
  - Null mean `-2.7425414055848714e-07`.
  - Null 5-95% interval `[-2.7445474076652e-07, -2.7406420776259464e-07]`.
- `rank_mod_64` CTW control:
  - Against `B0`: `R = 0.2674244536300398` bits/gap, total gain
    `974961.0972749958` bits.
  - Against `B1(11)`: `R = -2.742924352340597e-07` bits/gap.
- Exact baseline ladder:
  - `B0 = 4.563439906212204` bits/gap.
  - `B1(11) = 3.1704284777012335` bits/gap.
  - Improvement of `B1(11)` over `B0`: `1.3930114285109703` bits/gap.

The compact final report is:

- `experiments/final_report.md`
- `experiments/final_metrics.json`
- `experiments/final_manifest.json`

## Paper-Scale Artifacts

- `experiments/paper_b1_y11_depth4_stop_time_x26_n200/`
- `experiments/paper_ctw_rank64_depth1_stop_time_x26_n200/`
- `experiments/paper_ladder_b0_b1_y11_x26_n200/`
- `experiments/paper_logs/`

## Reproduce

Compile all scripts and regenerate the final report from existing artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1 -SkipRuns
```

The full final-suite script still reruns the smaller pilot/control suite before
regenerating the report. The paper-scale artifacts above were generated as
long, checkpointed batch runs. See `paper_run_plan.md` for the exact
paper-scale commands and resume protocol.

## Main Files

- `paper_grade_theory.md`: research-note formulation.
- `paper_run_plan.md`: completed paper-scale run plan and artifact protocol.
- `experiments/final_report.md`: compact current results.
- `experiments/final_metrics.json`: machine-readable current metrics.
- `experiments/final_manifest.json`: pinned artifact manifest.
- `experiments/results_summary.md`: older detailed experiment log and pilot
  interpretation.
- `experiments/rpi_final_report.py`: final report generator.
- `experiments/rpi_runtime_estimate.py`: estimate long-run wall time before
  launching paper-scale experiments.
- `experiments/run_final_suite.ps1`: reproducibility driver for compilation,
  pilot reruns, and report generation.

## Limitations

- The main paper-scale results reach `X = 2^26`; they are empirical evidence at
  this range, not an asymptotic theorem.
- The implemented `B2` families are finite prototypes, not canonical arithmetic
  null models.
- No `B3`-style global analytic correction is implemented.
- Some older auxiliary pilots use fixed-count nulls. The main paper-scale B1
  and CTW checks use stop-time nulls.
