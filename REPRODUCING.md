# Reproducing the Paper-Scale Results

This document describes the intended fresh-clone validation path for the paper-scale result.

The repository is organized around a committed, pinned artifact record rather than requiring every reviewer to rerun the long simulations. The main paper-scale simulations are checkpointed and resumable, but the default validation path checks the committed artifacts, metrics, report, robustness conclusions, and figure-generation contract.

## Fresh-clone validation

From a fresh clone of the repository:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python experiments/validate_paper_artifacts.py
python experiments/rpi_robustness_audit.py
python experiments/rpi_paper_figures.py
```

On Windows, the bundled final-suite driver also regenerates the compact report from the pinned artifacts and checks for metric/report drift:

```powershell
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1 -SkipRuns
```

The `-SkipRuns` mode is the expected reviewer/default mode. It does not rerun the long null simulations. It validates the committed paper-scale record.

## What is pinned

The paper-scale artifacts used for the headline result are pinned in:

```text
experiments/final_manifest.json
```

The required paper-scale artifact directories are:

```text
experiments/paper_b1_y11_depth4_stop_time_x26_n200/
experiments/paper_ctw_rank64_depth1_stop_time_x26_n200/
experiments/paper_ladder_b0_b1_y11_x26_n200/
```

The headline machine-readable metrics are in:

```text
experiments/final_metrics.json
```

The human-readable compact report is:

```text
experiments/final_report.md
```

## Expected headline conclusion

A successful validation should preserve the following qualitative conclusion:

- the paper-scale suite reaches `X = 2^26`;
- the main B1(11) bucket-residual result is null-level against stop-time synthetic nulls;
- the rank-mod-64 CTW residual model strongly separates from the weak `B0` baseline;
- the same residual machinery is null-level under `B1(11)`;
- the final conclusion remains `residual_beyond_B1_detected: false` in `experiments/final_metrics.json`.

The result is therefore a finite-scale, model-class-specific negative result beyond the declared `B1(11)` wheel-first-hit baseline. It is not an asymptotic theorem and not a claim that prime gaps contain no residual information.

## Manuscript build

The manuscript source is:

```text
paper.tex
references.bib
```

Local build command, if a TeX distribution is installed:

```bash
latexmk -pdf paper.tex
```

The GitHub Actions workflow `.github/workflows/manuscript-build.yml` regenerates manuscript figures, builds `paper.pdf`, verifies that the PDF exists, and uploads it as a workflow artifact.

Before release, inspect the generated PDF manually for:

- figure placement and scaling;
- table width and line wrapping;
- citation and bibliography rendering;
- unresolved LaTeX warnings or missing references;
- consistency between the abstract, results table, and `experiments/final_metrics.json`.

## Long-run reproduction

The exact paper-scale commands and resume protocol are recorded in:

```text
paper_run_plan.md
```

Those commands are intentionally not part of the default CI path because they are long-running simulation jobs. They remain the record for independent reruns or extensions of the paper-scale suite.

## CI expectations

A release candidate should have green runs for:

- `Reproducibility`;
- `Artifact validation`;
- `Manuscript build`.

The manuscript-build workflow verifies PDF construction, while the reproducibility workflow verifies the empirical artifact/report path.
