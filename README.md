# Residual Predictive Information of Prime Gaps

This repository contains a paper-facing formulation and reproducible experiments for measuring residual predictive information in consecutive prime gaps.

Archived releases are available through Zenodo via the GitHub release archive. For exact reproducibility, cite the version-specific DOI shown on Zenodo for the GitHub release used.

The central statistic is the prequential per-gap code gain

\[
R_k(X)=\frac{L_{B_k}(G_X)-L_{U_k}(G_X)}{|G_X|},
\]

where \(B_k\) is an explicit arithmetic baseline and \(U_k\) is a penalized online residual predictor. The question is whether previous gap history improves prediction after known arithmetic structure has already been built into the null model.

## Current Empirical Status

The paper-scale suite is complete for the main tests through `X = 2^26` with `200` null replicates/checkpoints:

- `B1(11)` bucket residual with stop-time synthetic nulls.
- `rank_mod_64` CTW residual control with stop-time synthetic nulls.
- B0/B1 exact baseline ladder over the same dyadic range.

Bottom line: the experiments do **not** detect positive residual predictive information beyond the wheel-first-hit baseline `B1(11)` at the tested scale.

The controls behave as desired. Residual coders find large apparent signal against the weak `B0` baseline, but that signal disappears once the arithmetic wheel-first-hit baseline `B1(11)` is used. This supports the interpretation that the detected structure is arithmetic baseline structure, not robust residual sequential information.

## Paper Framing

The repo is organized for a paper with a negative/methodological claim:

> A prequential residual-coding protocol detects strong missing arithmetic structure under weak baselines, but under the tested online residual predictors it finds no robust residual predictive information beyond the wheel-first-hit baseline `B1(11)` up to `X = 2^26`.

The paper should be framed as a reproducible protocol and finite-scale falsification study, not as a proof that residual predictive information is absent.

## Paper-facing files

- `paper.tex`: submission-oriented LaTeX manuscript source.
- `references.bib`: BibTeX bibliography for `paper.tex`.
- `SUBMISSION_CHECKLIST.md`: release, CI, manuscript-build, and archival checklist.
- `REPRODUCING.md`: fresh-clone validation guide separating quick artifact validation from long simulation reruns.
- `ARCHIVAL_RELEASE.md`: version-tag, GitHub release, DOI archival, and citation metadata maintenance guide.
- `paper_related_work_positioning.md`: reviewer-facing related-work and claim-positioning note for the introduction, discussion, or cover letter.
- `paper_manuscript_v1.md`: first full manuscript draft and canonical Markdown starting point.
- `paper_grade_theory.md`: theory note updated for the completed paper-scale result.
- `paper_tables.md`: paper-ready result tables.
- `paper_formal_core.md`: reviewer-facing formal definitions, claim-discipline table, `B1(11)` normalization/support checklist, and `B1(11)` threshold defense to integrate into the manuscript.
- `experiments/rpi_paper_figures.py`: reproducible figure generator.
- `paper_figures/README.md`: figure-generation instructions.
- `paper_figures/*.pdf`: primary paper/manuscript vector figures.
- `paper_figures/*.svg`: repository/web vector figures.
- `paper_figures/*.png`: high-resolution preview/fallback figures.
- `experiments/rpi_robustness_audit.py`: endpoint and cross-exponent robustness audit over the pinned paper-scale artifacts.

## Citation and Publication Metadata

The repository includes publication/reuse metadata:

- `LICENSE`: MIT license for reuse of the repository contents.
- `CITATION.cff`: citation metadata crediting Asger Othmar Frøhlich and the intended release version.
- `ARCHIVAL_RELEASE.md`: release-note and archival procedure for DOI-linked versions.

Use the version-specific DOI shown on Zenodo when citing an archived GitHub release. The repository files intentionally avoid embedding a newly minted same-version DOI, which prevents a DOI-only self-reference loop.

## Paper-Scale Headline Results

At `X = 2^26`:

- Main `B1(11)` bucket residual:
  - `R = -2.7429243523407067e-07` bits/gap.
  - Null mean `-2.7425414055848714e-07`.
  - Null 5-95% interval `[-2.7445474076652e-07, -2.7406420776259464e-07]`.
- `rank_mod_64` CTW control:
  - Against `B0`: `R = 0.2674244536300398` bits/gap, total gain `974961.0972749958` bits.
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

For the reviewer-facing fresh-clone path, start with:

```text
REPRODUCING.md
```

Install the Python dependency used for figure generation:

```powershell
python -m pip install -r requirements.txt
```

Compile all scripts, regenerate the final report from existing pinned artifacts, and validate required artifact, metadata, checkpoint, headline-metric, and cross-exponent robustness consistency:

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

This writes PDF, SVG, and PNG copies of each figure. Use the PDF files for the paper/manuscript, SVG files for repository/web viewing, and PNG files for preview or fallback rendering.

Build the submission manuscript if a TeX distribution is installed:

```bash
latexmk -pdf paper.tex
```

The `Manuscript build` GitHub Actions workflow also regenerates figures, builds `paper.pdf`, checks that the PDF exists, and uploads it as a workflow artifact for manual inspection.

The full final-suite script still reruns the smaller pilot/control suite before regenerating the report when `-SkipRuns` is omitted. The paper-scale artifacts above were generated as long, checkpointed batch runs. See `paper_run_plan.md` for the exact paper-scale commands and resume protocol.

## Reproducibility Guardrails

- `experiments/final_manifest.json` pins the artifacts used by the final report.
- `experiments/validate_paper_artifacts.py` checks that required paper-scale artifacts exist, reach `X = 2^26`, have 200 null checkpoints, cover the expected dyadic exponents, and agree with `experiments/final_metrics.json`.
- `experiments/rpi_robustness_audit.py` checks that the negative result is not an endpoint-only accident: B1 residuals stay inside stop-time null bands across exponents, the B0 positive control separates, and the B1 ladder remains better than B0 across the tested range.
- `.github/workflows/reproducibility.yml` runs compilation, report regeneration, artifact validation, robustness auditing, figure generation, and figure-output existence checks in CI.
- `.github/workflows/manuscript-build.yml` regenerates manuscript figures, builds `paper.pdf`, verifies that the PDF exists, and uploads the PDF as a workflow artifact.

## Main Files

- `paper.tex`: submission-oriented LaTeX manuscript source.
- `references.bib`: BibTeX bibliography for `paper.tex`.
- `SUBMISSION_CHECKLIST.md`: release, CI, manuscript-build, and archival checklist.
- `REPRODUCING.md`: fresh-clone validation and reviewer reproducibility guide.
- `ARCHIVAL_RELEASE.md`: release tag, DOI archival, and citation metadata guide.
- `paper_related_work_positioning.md`: related-work/claim-positioning note.
- `paper_manuscript_v1.md`: first full manuscript draft and canonical Markdown starting point.
- `paper_grade_theory.md`: paper-facing formulation.
- `paper_tables.md`: paper-ready tables.
- `paper_formal_core.md`: formal definitions, `B1(11)` threshold defense, and reviewer-facing claim discipline for manuscript integration.
- `paper_run_plan.md`: completed paper-scale run plan and artifact protocol.
- `paper_figures/`: figure output directory and instructions; generate PDF, SVG, and PNG figures from pinned artifacts using `experiments/rpi_paper_figures.py`.
- `experiments/final_report.md`: compact current results.
- `experiments/final_metrics.json`: machine-readable current metrics.
- `experiments/final_manifest.json`: pinned artifact manifest.
- `experiments/validate_paper_artifacts.py`: reproducibility validator for pinned paper artifacts and metrics.
- `experiments/rpi_robustness_audit.py`: cross-exponent qualitative robustness audit for the paper-scale conclusion.
- `experiments/results_summary.md`: older detailed experiment log and pilot interpretation.
- `experiments/rpi_final_report.py`: final report generator.
- `experiments/rpi_paper_figures.py`: paper figure generator.
