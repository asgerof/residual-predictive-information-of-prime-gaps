# Reproducibility Guide

This guide describes the short verification path for the committed paper-scale
artifacts and the long-run path for regenerating them.

## Short path: verify the committed paper-scale artifacts

The paper-scale calculations are already committed as pinned artifacts under
`experiments/paper_*`. The short path does not rerun the long simulations.

```powershell
python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1 -SkipRuns
```

This performs three checks:

1. compiles the experiment/report/figure/validation scripts;
2. regenerates `experiments/final_report.md` and `experiments/final_metrics.json`
   from `experiments/final_manifest.json`;
3. validates that the required paper-scale artifacts, metadata, checkpoint
   counts, dyadic exponent coverage, and headline metrics are internally
   consistent.

The validator can also be run directly:

```powershell
python experiments\validate_paper_artifacts.py
```

A successful run prints:

```text
artifact validation passed: required paper-scale CSV, metadata, checkpoint counts, and final metrics are consistent
```

## Figure regeneration

```powershell
python experiments\rpi_paper_figures.py
```

This writes:

- `paper_figures/figure_1_b1_residual_stop_time.svg`
- `paper_figures/figure_2_ctw_positive_control.svg`
- `paper_figures/figure_3_baseline_ladder_bits.svg`

## Long path: regenerate the paper-scale experiments

The long paper-scale commands and resume forms are recorded in
`paper_run_plan.md`. They are intentionally not run by CI and are not run by the
short verification path because they are checkpointed batch jobs.

Use `--resume` with the documented output directories to continue interrupted
runs. The final report should only use artifacts pinned in
`experiments/final_manifest.json`.

## CI checks

`.github/workflows/reproducibility.yml` runs on branch pushes and pull requests
targeting `main`. It checks that:

- Python dependencies install cleanly;
- experiment, report, figure, and validation scripts compile;
- the final report regenerates from pinned artifacts;
- paper artifacts validate successfully;
- paper figures can be generated;
- regenerated final report files match the committed files.
