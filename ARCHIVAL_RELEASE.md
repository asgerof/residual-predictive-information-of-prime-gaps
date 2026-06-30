# Archival Release Guide

This repository now has an archival release for version `0.1.0`.

Current release metadata:

```text
Version: v0.1.0
DOI: 10.5281/zenodo.21073161
Release date: 2026-06-30
Author: Asger Othmar Frøhlich
```

The live citation metadata is stored in `CITATION.cff`, and the manuscript Code and Data Availability section points to the archived DOI. This file is kept as a maintenance guide for future release candidates, follow-up DOI-linked metadata updates, and submission checks.

## Release candidate checklist

Before creating any future archival release or submission update:

1. Confirm the following GitHub Actions workflows are green on the release commit:
   - `Reproducibility`
   - `Artifact validation`
   - `Manuscript build`
2. Download the `paper-pdf` artifact from the `Manuscript build` workflow and inspect it manually.
3. Confirm that `experiments/final_report.md` and `experiments/final_metrics.json` regenerate without a diff.
4. Confirm the paper-scale artifact directories listed in `experiments/final_manifest.json` are present.
5. Confirm the manuscript claim remains finite-scale and model-class-specific.
6. Confirm that `CITATION.cff`, the README citation/DOI line, and the manuscript availability statement agree on the DOI, version, and release date.

## Current version tag

The repository metadata currently targets version `0.1.0`.

Current release tag:

```text
v0.1.0
```

Current release title:

```text
Residual Predictive Information in Prime Gaps v0.1.0
```

Canonical release-note wording:

```markdown
Initial paper-scale release for the residual predictive information of prime gaps study.

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

## DOI maintenance

For a future release, create the GitHub release first and archive it with Zenodo or another DOI provider. Once the DOI exists:

1. Update `CITATION.cff`, for example:

   ```yaml
   doi: "10.xxxx/zenodo.xxxxxxx"
   ```

2. Update the version and release date if needed:

   ```yaml
   version: "0.1.1"
   date-released: "YYYY-MM-DD"
   ```

3. Update the README DOI/citation line.
4. Update the manuscript Code and Data Availability section if the archived DOI changes.
5. Commit those changes and, if needed, create a follow-up tag for the DOI-linked metadata update.

## What cannot be inferred from the release

Preserve the following limitations in any release notes, preprint upload, or submission cover text:

- the main result is finite-scale through `X = 2^26`;
- the negative result is specific to the tested residual predictors;
- `B1(11)` is a wheel-first-hit baseline, not a complete Hardy--Littlewood or global analytic model;
- the implemented `B2` diagnostics are not exhaustive;
- the 200 stop-time null replicates support a controlled finite-scale study, not extreme-tail claims.
