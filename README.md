# Residual Predictive Information of Prime Gaps

This repository contains a paper-facing formulation and reproducible experiments
for measuring residual predictive information in consecutive prime gaps.

The central statistic is the prequential per-gap code gain

\[
R_k(X)=\frac{L_{B_k}(G_X)-L_{U_k}(G_X)}{|G_X|},
\]

where \(B_k\) is an explicit arithmetic baseline and \(U_k\) is a penalized
online residual predictor. The question is whether previous gap history
improves prediction after known arithmetic structure has already been built into
the null model.

## Current Empirical Status

The paper-scale suite is complete for the main tests through `X = 2^26` with
`200` null replicates/checkpoints:

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

## Paper Framing

The repo is now organized for a paper with a negative/methodological claim:

> A prequential residual-coding protocol detects strong missing arithmetic
> structure under weak baselines, but under the tested online residual
> predictors it finds no robust residual predictive information beyond the
> wheel-first-hit baseline `B1(11)` up to `X = 2^26`.

The paper should be framed as a reproducible protocol and finite-scale
falsification study, not as a proof that residual predictive information is
absent.

Paper-facing files:

- `paper.tex`: submission-oriented LaTeX manuscript source.
- `references.bib`: BibTeX bibliography for `paper.tex`.
- `SUBMISSION_CHECKLIST.md`: release, CI, manuscript-build, and archival checklist.
- `paper_manuscript_v1.md`: first full manuscript draft and canonical Markdown
  starting point.
- `paper_grade_theory.md`: theory note updated for the completed paper-scale
  result.
- `paper_tables.md`: paper-ready result tables.
- `paper_formal_core.md`: reviewer-facing formal definitions, claim-discipline
  table, `B1(11)` normalization/support checklist, and `B1(11)` threshold
  defense to integrate into the manuscript.
- `experiments/rpi_paper_figures.py`: reproducible figure generator.
- `paper_figures/README.md`: figure-generation instructions.
- `paper_figures/*.pdf`: primary paper/manuscript vector figures.
- `paper_figures/*.svg`: repository/web vector figures.
- `paper_figures/*.png`: high-resolution preview/fallback figures.
- `experiments/rpi_robustness_audit.py`: endpoint and cross-exponent robustness
  audit over the pinned paper-scale artifacts.

## Publication Readiness Metadata

The repository now includes publication/reuse metadata:

- `LICENSE`: MIT license for reuse of the repository contents.
- `CITATION.cff`: citation metadata crediting Asger Othmar Frøhlich and pointing
  to the repository.

Before public release or archiving, update `CITATION.cff` with any final DOI,
version tag, publication date, or paper identifier.

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

## Reproduce and Validate

Install the Python dependency used for figure generation:

```powershell
python -m pip install -r requirements.txt
```

Compile all scripts, regenerate the final report from existing pinned artifacts,
and validate required artifact, metadata, checkpoint, headline-metric, and
cross-exponent robustness consistency:

```powershell
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1 -SkipRuns
```

Run the artifact validator directly:

```powershell
python experiments\validate_paper_artifacts.py
```

Run the paper-scale robustness audit directly:

```powershell
python experiments\rpi_robustness_audit.py
```

Generate paper figures from the committed paper-scale artifacts:

```powershell
python experiments\rpi_paper_figures.py
```

This writes PDF, SVG, and PNG copies of each figure. Use the PDF files for the
paper/manuscript, SVG files for repository/web viewing, and PNG files for
preview or fallback rendering.

Build the submission manuscript if a TeX distribution is installed:

```bash
latexmk -pdf paper.tex
```

The full final-suite script still reruns the smaller pilot/control suite before
regenerating the report when `-SkipRuns` is omitted. The paper-scale artifacts
above were generated as long, checkpointed batch runs. See `paper_run_plan.md`
for the exact paper-scale commands and resume protocol.

## Reproducibility Guardrails

- `experiments/final_manifest.json` pins the artifacts used by the final report.
- `experiments/validate_paper_artifacts.py` checks that required paper-scale
  artifacts exist, reach `X = 2^26`, have 200 null checkpoints, cover the
  expected dyadic exponents, and agree with `experiments/final_metrics.json`.
- `experiments/rpi_robustness_audit.py` checks that the negative result is not
  an endpoint-only accident: B1 residuals stay inside stop-time null bands
  across exponents, the B0 positive control separates, and the B1 ladder remains
  better than B0 across the tested range.
- `.github/workflows/reproducibility.yml` runs compilation, report regeneration,
  artifact validation, robustness auditing, figure generation, and figure-output
  existence checks in CI.

## Main Files

- `paper.tex`: submission-oriented LaTeX manuscript source.
- `references.bib`: BibTeX bibliography for `paper.tex`.
- `SUBMISSION_CHECKLIST.md`: release, CI, manuscript-build, and archival checklist.
- `paper_manuscript_v1.md`: first full manuscript draft and canonical Markdown
  starting point.
- `paper_grade_theory.md`: paper-facing formulation.
- `paper_tables.md`: paper-ready tables.
- `paper_formal_core.md`: formal definitions, `B1(11)` threshold defense, and
  reviewer-facing claim discipline for manuscript integration.
- `paper_run_plan.md`: completed paper-scale run plan and artifact protocol.
- `paper_figures/`: figure output directory and instructions; generate PDF, SVG,
  and PNG figures from pinned artifacts using `experiments/rpi_paper_figures.py`.
- `experiments/final_report.md`: compact current results.
- `experiments/final_metrics.json`: machine-readable current metrics.
- `experiments/final_manifest.json`: pinned artifact manifest.
- `experiments/validate_paper_artifacts.py`: reproducibility validator for
  pinned paper artifacts and metrics.
- `experiments/rpi_robustness_audit.py`: cross-exponent qualitative robustness
  audit for the paper-scale conclusion.
- `experiments/results_summary.md`: older detailed experiment log and pilot
  interpretation.
- `experiments/rpi_final_report.py`: final report generator.
- `experiments/rpi_paper_figures.py`: paper figure generator.
- `experiments/rpi_runtime_estimate.py`: estimate long-run wall time before
  launching paper-scale experiments.
- `experiments/run_final_suite.ps1`: reproducibility driver for compilation,
  optional pilot reruns, report generation, artifact validation, and robustness
  auditing.

## Limitations

- The main paper-scale results reach `X = 2^26`; they are empirical evidence at
  this range, not an asymptotic theorem.
- The implemented `B2` families are finite prototypes, not canonical arithmetic
  null models and not an exhaustion of possible tuple-corrected baselines.
- No `B3`-style global analytic correction is implemented.
- Some older auxiliary pilots use fixed-count nulls. The main paper-scale B1
  and CTW checks use stop-time nulls.
