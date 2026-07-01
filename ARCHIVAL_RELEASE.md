# Archival Release Guide

This file describes the release and Zenodo archival procedure for this repository. It intentionally avoids hard-coding a same-version Zenodo DOI in the repository files before the final archive is created. Zenodo mints the version-specific DOI after the GitHub release exists, so embedding that DOI back into the same archived snapshot would create an unnecessary DOI-only release loop.

## Release candidate checklist

Before creating an archival release or submission update:

1. Confirm the following GitHub Actions workflows are green on the release commit:
   - `Reproducibility`
   - `Artifact validation`
   - `Manuscript build`
2. Download the `paper-pdf` artifact from the `Manuscript build` workflow and inspect it manually.
3. Confirm that `experiments/final_report.md` and `experiments/final_metrics.json` regenerate without a diff.
4. Confirm the paper-scale artifact directories listed in `experiments/final_manifest.json` are present.
5. Confirm the manuscript claim remains finite-scale and model-class-specific.
6. Confirm that `CITATION.cff`, the README citation guidance, and the manuscript availability statement do not contain a stale version-specific Zenodo DOI.

## Intended final release

Recommended release tag:

```text
v0.1.1
```

Recommended release title:

```text
Residual Predictive Information in Prime Gaps v0.1.1
```

Canonical release-note wording:

```markdown
Final paper-scale release for the residual predictive information of prime gaps study.

This release contains:

- the LaTeX manuscript source (`paper.tex`) and bibliography (`references.bib`);
- generated paper figures in PDF, SVG, and PNG format;
- pinned paper-scale artifacts through `X = 2^26`;
- final machine-readable metrics and compact final report;
- validation, robustness-audit, and figure-generation scripts;
- GitHub Actions workflows for reproducibility, artifact validation, and manuscript PDF build.

Main scoped conclusion:

A prequential residual-coding protocol detects strong missing arithmetic structure under the weak `B0` baseline, but under the tested online residual predictors it finds no robust positive residual predictive information beyond the `B1(11)` wheel-first-hit baseline up to `X = 2^26`.

This is a finite-scale empirical/methodological result. It is not an asymptotic theorem and not a claim that prime gaps contain no residual information.
```

## DOI handling without a loop

For the final release:

1. Create the GitHub release from the final checked commit.
2. Let Zenodo archive that GitHub release and mint the version-specific DOI.
3. Use the DOI shown on the Zenodo record and GitHub release page when citing that archived version.
4. Do not create another release only to embed the newly minted DOI back into the same repository files.

A later repository edit may mention the DOI on `main`, but that is live repository metadata. It is not necessary to create a new archive unless scientific content, manuscript text, figures, code, or pinned artifacts change.

## What cannot be inferred from the release

Preserve the following limitations in any release notes, preprint upload, or submission cover text:

- the main result is finite-scale through `X = 2^26`;
- the negative result is specific to the tested residual predictors;
- `B1(11)` is a wheel-first-hit baseline, not a complete Hardy--Littlewood or global analytic model;
- the implemented `B2` diagnostics are not exhaustive;
- the 200 stop-time null replicates support a controlled finite-scale study, not extreme-tail claims.
