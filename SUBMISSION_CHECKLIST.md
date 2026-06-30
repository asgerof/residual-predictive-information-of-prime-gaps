# Submission Readiness Checklist

This checklist turns the repository from a research archive into a preprint/submission package.

## Fresh reproducibility check

Open or update a pull request without `[skip ci]` in the commit message and require the `Reproducibility` workflow to pass before merging.

The workflow should run:

```powershell
python -m unittest discover -s tests -v
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1 -SkipRuns
python experiments\validate_paper_artifacts.py
python experiments\rpi_robustness_audit.py
python experiments\rpi_paper_figures.py
```

A release/publication commit should have a visible green CI result rather than relying only on earlier local or skipped runs.

## Fresh-clone reproducibility guide

Use `REPRODUCING.md` as the reviewer-facing validation guide. It separates:

- quick validation from committed/pinned artifacts;
- manuscript figure regeneration;
- manuscript PDF build;
- long-running simulation reruns and resume protocol.

The default reviewer path should validate the committed paper-scale record. It should not require rerunning the long simulations.

## Manuscript build

Primary manuscript source:

```text
paper.tex
references.bib
```

Suggested local build command if a TeX distribution is installed:

```bash
latexmk -pdf paper.tex
```

Equivalent manual build:

```bash
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

The manuscript expects the generated paper figures to exist in `paper_figures/`:

```text
paper_figures/figure_1_b1_residual_stop_time.pdf
paper_figures/figure_2_ctw_positive_control.pdf
paper_figures/figure_3_baseline_ladder_bits.pdf
```

Regenerate figures from pinned paper-scale artifacts with:

```powershell
python experiments\rpi_paper_figures.py
```

The `Manuscript build` GitHub Actions workflow should also pass before release. It regenerates manuscript figures, builds `paper.pdf`, checks that the PDF exists, and uploads it as a workflow artifact for manual inspection.

Manual PDF inspection should check:

- figure placement and scaling;
- table width and line wrapping;
- citation and bibliography rendering;
- unresolved LaTeX warnings or missing references;
- consistency between the abstract, results table, and `experiments/final_metrics.json`.

## Related-work and positioning pass

Use `paper_related_work_positioning.md` as the reviewer-facing positioning note. Before submission, either integrate its compact insertion into the introduction/discussion or preserve the same distinction in the cover letter:

- the paper is not an absolute randomness test for the primes;
- the paper is not just a correlation, bias, entropy, or compression study;
- the main object is residual online predictive gain after a declared arithmetic baseline and model-complexity penalty;
- the positive `B0` control shows that omitted arithmetic structure can look like residual signal;
- the negative `B1(11)` result is finite-scale and model-class-specific.

## Preprint/release steps

Before an arXiv-style release:

1. Confirm the `Reproducibility` workflow is green on the final PR or release commit.
2. Confirm the `Artifact validation` workflow is green on the final PR or release commit.
3. Confirm the `Manuscript build` workflow is green on the final PR or release commit.
4. Download the `paper-pdf` workflow artifact and inspect figures, references, captions, and table placement.
5. Verify that `experiments/final_report.md` and `experiments/final_metrics.json` have no uncommitted regeneration diff.
6. Create a version tag, for example `v0.1.0`.
7. Archive the release on Zenodo or another DOI provider.
8. Update `CITATION.cff` with the final DOI, release date, and version.
9. In the manuscript, replace the repository-only availability statement with the archived DOI.

See `ARCHIVAL_RELEASE.md` for suggested release notes and DOI metadata steps.

## Reviewer-facing caution points

Preserve these limits in the final manuscript:

- The main result is finite-scale through `X = 2^26`.
- The negative result is specific to the tested residual predictors.
- `B1(11)` is a wheel-first-hit baseline, not a full Hardy--Littlewood or global analytic model.
- The implemented `B2` diagnostics are not exhaustive.
- The 200 stop-time null replicates support a controlled finite-scale study, not extreme-tail claims.
