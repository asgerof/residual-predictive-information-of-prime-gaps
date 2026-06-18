# Residual Predictive Information of Prime Gaps

This repository contains a research-note formulation and pilot experiments
for measuring residual predictive information in consecutive prime gaps.

The central statistic is the prequential per-gap code gain

\[
R_k(X)=\frac{L_{B_k}(G_X)-L_{U_k}(G_X)}{|G_X|},
\]

where \(B_k\) is an explicit arithmetic baseline and \(U_k\) is a penalized
online residual predictor.  The question is whether previous gap history
improves prediction after known arithmetic structure has already been built
into the null model.

## Current Empirical Status

The completed pilots do not detect positive residual predictive information
beyond the wheel-first-hit baseline \(B_1(11)\).

Positive controls pass: residual coders find large gains against \(B_0\), and
those gains disappear against \(B_1(11)\).  Tested \(B_2\)-style refinements
including pair singular-series reweighting, residue-transition calibration,
finite consecutive-prime inclusion-exclusion, and two-parameter
endpoint/exclusion shrinkage do not improve exact prequential log-loss over
\(B_1(11)\) at the tested scales.

The main \(B_1\) residual and rank-mod CTW checks now include stop-time
synthetic nulls, so these controls no longer depend only on conditioning on
the real number of gaps in each held-out window.

The compact final report is:

- `experiments/final_report.md`
- `experiments/final_metrics.json`
- `experiments/final_manifest.json`

## Reproduce

Compile all scripts and regenerate the final report from existing artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1 -SkipRuns
```

Rerun the final suite and regenerate the report:

```powershell
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1
```

The full rerun can take several minutes because the two-parameter \(B_2\)
scans are deliberately chronological and recompute finite corrections.

## Main Files

- `paper_grade_theory.md`: research-note formulation.
- `paper_run_plan.md`: next paper-scale experiment plan and runtime estimates.
- `experiments/results_summary.md`: detailed experiment log and interpretation.
- `experiments/rpi_final_report.py`: final report generator.
- `experiments/rpi_runtime_estimate.py`: estimate long-run wall time before
  launching paper-scale experiments.
- `experiments/run_final_suite.ps1`: reproducibility driver.
- `experiments/results_b1_y11_depth4_stop_time`: main B1 stop-time null run.
- `experiments/results_ctw_rank64_depth1_stop_time`: rank-mod CTW stop-time
  null run.

## Limitations

- The largest main residual run reaches \(X=2^{22}\); the slower \(B_2\)
  scans reach \(X=2^{18}\).
- The next paper-scale runs are expected to exceed 20 minutes on the current
  machine and should be scheduled as resumable long batch jobs using
  `--checkpoint-nulls --resume`.
- The implemented \(B_2\) families are finite prototypes, not canonical
  arithmetic null models.
- No \(B_3\)-style global analytic correction is implemented.
- Real prime-window construction now uses a segmented streaming prime-pair
  generator, but the paper-scale runs have not yet been executed.
