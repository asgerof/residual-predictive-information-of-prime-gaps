# Final Experiment Report

Date: 2026-06-28.

## Bottom Line

The paper-scale experiments do **not** detect positive residual predictive
information beyond the wheel-first-hit baseline `B1(11)` through `X = 2^26`.

The framework does detect strong structure against the weaker `B0` baseline.
That signal disappears when the arithmetic wheel-first-hit baseline `B1(11)` is
used, which supports the interpretation that the detected signal is baseline
arithmetic structure rather than robust residual sequential information.

## Paper-Scale Suite

Completed main artifacts:

- `experiments/paper_b1_y11_depth4_stop_time_x26_n200/`
- `experiments/paper_ctw_rank64_depth1_stop_time_x26_n200/`
- `experiments/paper_ladder_b0_b1_y11_x26_n200/`

All three main runs reach `X = 2^26` with `200` null replicates/checkpoints.

## Key Metrics at X = 2^26

### Main B1(11) bucket residual

- `n = 3,645,744` gaps.
- Real `R = -2.7429243523407067e-07` bits/gap.
- Null mean `-2.7425414055848714e-07`.
- Null 5-95% interval
  `[-2.7445474076652e-07, -2.7406420776259464e-07]`.
- `z_vs_null = -0.31818465586295164`.

Interpretation: no positive residual signal beyond `B1(11)`.

### rank_mod_64 CTW control

Against `B0`:

- `R = 0.2674244536300398` bits/gap.
- Total gain `974961.0972749958` bits.
- Empirical `p_ge = 0.004975124378109453`.

Against `B1(11)`:

- `R = -2.742924352340597e-07` bits/gap.
- Total gain approximately `-1` bit.
- Empirical `p_ge = 0.6119402985074627`.

Interpretation: the same residual learner strongly detects missing structure in
`B0`, but does not detect residual structure after `B1(11)`.

### Exact baseline ladder

At `X = 2^26`:

- `B0 = 4.563439906212204` bits/gap.
- `B1(11) = 3.1704284777012335` bits/gap.
- `B1(11)` improves over `B0` by `1.3930114285109703` bits/gap.

This quantifies how much arithmetic structure the `B1(11)` wheel-first-hit
baseline already absorbs.

## Older B2 Attempts

The earlier B2-style prototypes remain useful negative controls. The tested
families include pair singular-series reweighting, residue-transition
calibration, finite consecutive-prime inclusion-exclusion, and two-parameter
endpoint/exclusion shrinkage. In the older final report generation these
chronological/oracle calibrations collapsed back to `B1(11)` or worsened exact
prequential log-loss.

These are not canonical B2 models and should not be presented as exhausting the
space of possible arithmetic refinements.

## Interpretation for a Paper

The cleanest paper claim is negative and methodological:

> A prequential residual-coding protocol detects strong missing arithmetic
> structure in weak prime-gap baselines, but under the tested online residual
> predictors it finds no robust residual predictive information beyond the
> wheel-first-hit baseline `B1(11)` up to `X = 2^26`.

This is publishable as a careful empirical/protocol paper, not as a proof that
no residual information exists.

## Remaining Limits

- The main paper-scale results reach `X = 2^26`; this is empirical evidence at
  a finite scale.
- The B2 attempts are finite, truncated prototypes and are not canonical.
- No B3-style global analytic correction has been implemented.
- Huge z-scores in the B0 baseline-ladder rows should not be used as headline
  evidence because the corresponding null variance is nearly degenerate; use
  effect sizes and empirical null ranks instead.

## Reproducibility

The compact report is generated from the pinned artifact manifest
`experiments/final_manifest.json`.

Regenerate from existing artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1 -SkipRuns
```

The paper-scale long-run commands and resume protocol are recorded in
`paper_run_plan.md`.
