# Paper Draft Skeleton: Residual Predictive Information in Prime Gaps

This is a paper-facing skeleton built around the completed paper-scale suite.
It is intended as the starting point for a manuscript, not as the final prose.

## Working Title

Residual Predictive Information in Prime Gaps: A Prequential Falsification
Protocol and a Negative Result Beyond Wheel-First-Hit Baselines

## Short Title

Residual Predictive Information in Prime Gaps

## Abstract Draft

We introduce a prequential information-theoretic protocol for testing residual
sequential predictability in consecutive prime gaps after explicit arithmetic
structure has been built into a null model. For dyadic windows \([X,2X)\), the
protocol compares the log-loss of an arithmetic baseline \(B_k\) against a
penalized online residual predictor \(U_k\), reporting the per-gap code gain
\(R_k(X)=(L_{B_k}-L_{U_k})/|G_X|\). The goal is not to measure absolute
compressibility of the primes, but to ask whether previous gap history improves
prediction once local density and finite wheel constraints are already included.

The completed paper-scale suite reaches \(X=2^{26}\) with 200 stop-time
synthetic null replicates/checkpoints. The residual machinery detects strong
missing structure under the weak \(B_0\) baseline: a rank-mod-64 CTW residual
coder obtains \(R=0.2674244536300398\) bits/gap and about \(974{,}961\) bits of
total gain at \(X=2^{26}\). However, the same machinery gives null-level behavior
against the wheel-first-hit baseline \(B_1(11)\), and the main \(B_1(11)\)
bucket-residual test gives \(R=-2.7429243523407067\cdot 10^{-7}\) bits/gap with
\(z=-0.318\) versus stop-time nulls. These results support a finite-scale
negative conclusion: under the tested residual predictors, no positive residual
predictive information is detected beyond \(B_1(11)\) up to \(X=2^{26}\). The
paper is therefore framed as a reproducible protocol and falsification study,
not as an asymptotic proof of absence.

## Core Contribution

The paper should make four claims.

1. **Protocol.** Residual predictive information in prime gaps can be defined as
   a penalized prequential code gain over an explicit arithmetic null hierarchy.
2. **Control.** The residual machinery detects known missing arithmetic
   structure when the baseline is deliberately too weak.
3. **Negative result.** Under the implemented tests, the detected signal
   disappears after the \(B_1(11)\) wheel-first-hit baseline.
4. **Claim discipline.** The result is finite-scale and model-class-specific;
   it does not rule out stronger residual models or canonical higher-order
   arithmetic baselines.

## Claims and Non-Claims

### Safe claims

- The paper-scale suite is complete for the main tests through \(X=2^{26}\)
  with 200 null replicates/checkpoints.
- Positive controls against \(B_0\) pass.
- The main \(B_1(11)\) tests do not detect positive residual predictive
  information at the tested scale.
- The result is consistent with the interpretation that the apparent \(B_0\)
  signal is small-modulus arithmetic structure absorbed by \(B_1(11)\).

### Claims to avoid

- Do not claim that prime gaps contain no residual information.
- Do not claim that the implemented \(B_2\)-style prototypes exhaust all
  tuple-corrected arithmetic baselines.
- Do not claim an asymptotic theorem.
- Do not treat huge \(B_0\) ladder z-scores as headline evidence; use effect
  sizes and empirical null ranks instead.

## Proposed Manuscript Structure

### 1. Introduction

Open by distinguishing absolute compressibility from relative predictive
information. The primes are computable, so ordinary compression is not the
right question. The paper asks whether previous prime gaps help predict the
next gap after explicit arithmetic structure has already been included in the
null model.

Suggested final paragraph:

> We present a prequential falsification protocol for this question and apply
> it to consecutive prime gaps up to \(X=2^{26}\). The protocol is sensitive
> enough to detect missing wheel structure under a weak baseline, but detects no
> positive residual predictive information beyond the wheel-first-hit baseline
> \(B_1(11)\) under the tested residual coders.

### 2. Prequential Residual Information

Define the gap block \(G_X\), prequential log-loss, baseline code length
\(L_{B_k}\), residual code length \(L_{U_k}\), and

\[
R_k(X)=\frac{L_{B_k}(G_X)-L_{U_k}(G_X)}{|G_X|}.
\]

Emphasize that \(U_k\) must be online and penalized. A positive residual signal
must pay for its own model complexity.

### 3. Arithmetic Null Hierarchy

Introduce \(B_0\), \(B_1(y)\), \(B_2(y,r)\), and \(B_3(y,r,z)\).

The implemented headline baseline is \(B_1(11)\), where \(W=2310\) and
\(\phi(W)=480\). This baseline models the next gap as a first hit among
wheel-admissible offsets.

B2 wording should be conservative:

> We implemented several finite \(B_2\)-style diagnostics, but do not treat
> them as a canonical tuple-corrected null hierarchy. They are reported only as
> auxiliary checks.

### 4. Synthetic Nulls and Falsification Criteria

Explain stop-time synthetic nulls and why nulls must be generated under the
same baseline and evaluated with the same residual machinery.

List the criteria for a positive claim:

- positive code gain beyond \(B_1(11)\);
- survival under stop-time nulls;
- agreement across at least two independent residual symbolizations;
- absence of the same effect under synthetic nulls;
- persistence over increasing dyadic windows;
- chronological tuning only.

Then state that the completed suite does not meet the positive-claim criteria.

### 5. Experiments

Use the paper-scale artifact table in `paper_tables.md`.

Main experimental blocks:

1. \(B_1(11)\) bucket residual, depth 4, stop-time nulls.
2. rank-mod-64 CTW residual control, depth 1, stop-time nulls.
3. exact B0/B1 baseline ladder.

### 6. Results

The result section should be organized around the falsification logic.

#### 6.1 Main \(B_1(11)\) residual test

At \(X=2^{26}\):

- \(n = 3{,}645{,}744\) gaps.
- \(R=-2.7429243523407067\cdot 10^{-7}\) bits/gap.
- null mean \(=-2.7425414055848714\cdot 10^{-7}\).
- null 5--95% interval
  \([-2.7445474076652\cdot 10^{-7}, -2.7406420776259464\cdot 10^{-7}]\).
- \(z=-0.31818465586295164\).

Conclusion: no positive residual signal beyond \(B_1(11)\).

#### 6.2 Positive control against \(B_0\)

The rank-mod-64 CTW residual model obtains:

- \(R=0.2674244536300398\) bits/gap against \(B_0\);
- total gain \(=974{,}961.0972749958\) bits;
- empirical \(p_{\geq}=0.004975124378109453\).

Conclusion: the residual machinery is active and can find missing structure.

#### 6.3 The same control against \(B_1(11)\)

The same CTW setup gives:

- \(R=-2.742924352340597\cdot 10^{-7}\) bits/gap;
- total gain approximately \(-1\) bit;
- empirical \(p_{\geq}=0.6119402985074627\).

Conclusion: the positive-control signal disappears after wheel-first-hit
structure is included.

#### 6.4 Exact baseline ladder

At \(X=2^{26}\):

- \(B_0=4.563439906212204\) bits/gap.
- \(B_1(11)=3.1704284777012335\) bits/gap.
- Improvement \(=1.3930114285109703\) bits/gap.

Conclusion: \(B_1(11)\) absorbs a large amount of arithmetic structure relative
to \(B_0\), explaining why residual models should not be credited for
rediscovering it.

### 7. Discussion

The main discussion should be about methodological hygiene:

- weak baselines create apparent residual structure;
- positive controls are necessary but not sufficient;
- the proper null must encode known arithmetic constraints;
- negative results are informative when the protocol was capable of detecting
  missing structure under weaker baselines.

### 8. Limitations

Use precise limitations:

- finite scale: \(X\leq 2^{26}\);
- residual model classes are finite;
- \(B_2\)-style tests are prototypes, not canonical;
- no \(B_3\)-style global analytic correction;
- no proof of asymptotic vanishing;
- only a limited set of symbolizations and depths tested.

### 9. Conclusion

Suggested conclusion paragraph:

> The experiments give a clean finite-scale negative result. A residual learner
> detects strong missing structure under a weak baseline, but the signal
> disappears under the \(B_1(11)\) wheel-first-hit baseline. Thus, under the
> tested prequential residual coders and through \(X=2^{26}\), we find no robust
> residual predictive information beyond finite wheel arithmetic. The protocol
> remains useful precisely because it can turn apparent patterns into falsified
> positive claims.

## Figures and Tables

Use:

- `paper_tables.md` for paper-ready summary tables.
- `experiments/rpi_paper_figures.py` to regenerate figure SVGs.
- `paper_figures/` for generated SVG output.

Recommended final figures:

1. \(B_1(11)\) bucket residual vs stop-time null band.
2. CTW residual control against \(B_0\) and \(B_1(11)\).
3. Exact baseline log-loss ladder \(B_0\) vs \(B_1(11)\).

## Reviewer-Risk Checklist

Before submission, verify:

- The paper never treats \(B_2\) prototypes as exhaustive.
- Every positive-control statement is paired with the stronger-baseline null
  result.
- The abstract says finite-scale negative result, not proof.
- All headline numbers are generated from `experiments/final_manifest.json`.
- Figures are regenerated from committed CSV artifacts.
- The open PR #1 is either closed or explicitly ignored before public release.
