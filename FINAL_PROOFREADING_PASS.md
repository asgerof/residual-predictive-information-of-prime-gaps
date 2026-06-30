# Final Proofreading Pass

Date: 2026-06-30

## Verdict

The repository is ready for the final proofreading/polish stage. The remaining work is not about changing the scientific claim or adding new experiments. It is about making the manuscript easier for a skeptical reader to parse and harder to misread.

The paper should remain framed as:

> A reproducible prequential residual-coding protocol and finite-scale negative result: the tested residual predictors find no robust positive residual predictive information beyond the `B1(11)` wheel-first-hit baseline through `X = 2^26`, while the same machinery detects omitted arithmetic structure under the weaker `B0` baseline.

It should not be framed as:

- a proof that prime gaps contain no residual information;
- an asymptotic theorem;
- a claim that `B1(11)` is a complete arithmetic model;
- a claim that the implemented `B2` diagnostics exhaust tuple-corrected baselines;
- an extreme-tail statistical claim based on 200 null replicates.

## Related-work / positioning pass

The manuscript already cites the right core categories: Cramer-type models, large-gap probabilistic models, consecutive-prime biases, prequential analysis, universal coding, CTW, and MDL-style model comparison.

The main related-work improvement is to make the novelty explicit earlier in the introduction. Suggested insertion after the current paragraph that begins “This paper asks a relative and predictive question”:

```latex
The question also differs from existing studies of prime-gap correlations, consecutive-prime biases, entropy-like statistics, or compression of prime-derived sequences \citep{lemkeoliver2016,kumar2003}. Those studies ask whether prime-derived data display structure relative to a chosen statistical summary or heuristic model. Here the target is operational and relative: before each gap is revealed, a declared arithmetic baseline has already assigned a probability distribution, and a residual learner receives credit only if previous gap history shortens the prequential code after that baseline and after its own complexity penalty. Thus the experiment is not an absolute randomness test for the primes. It is a test of residual online predictive gain after specified arithmetic information has been made explicit.
```

This closes the most likely reviewer objection: “Is this just another correlation/entropy/compression paper about prime gaps?” The answer becomes clearly no.

## Claim-discipline pass

The claim discipline is strong and should be preserved. The manuscript already says the result is finite-scale, model-class-specific, not an asymptotic theorem, not a claim that prime gaps contain no residual information, and not an exhaustive test of higher-order arithmetic baselines.

Recommended small wording improvement for the conclusion:

```latex
The safest conclusion is finite-scale and model-class-specific: under the tested online residual predictors and through $X=2^{26}$, no positive residual predictive information is detected beyond the $B_1(11)$ wheel-first-hit baseline.

This does not prove that prime gaps contain no residual information. It shows that a controlled residual-coding protocol can separate weak-baseline artifacts from robust residual signals, and that the tested positive signal disappears once small-prime wheel structure is included.
```

This is already very close to the current conclusion and should remain the manuscript’s final posture.

## Figure/table readability pass

The figures are now publication-facing and the manuscript-build workflow passed. The remaining readability risk is the headline results table: the current table includes very long floating-point values in a three-column layout. This is precise, but it may be visually cramped in the PDF and less readable than necessary.

Recommended edit:

1. Round displayed manuscript values to 4 significant figures.
2. Preserve exact values in `experiments/final_metrics.json`.
3. State in the table caption that exact values are machine-readable in the repository.
4. Use fixed-width paragraph columns instead of `lll`.

Suggested table replacement:

```latex
\begin{table}[ht]
\centering
\small
\begin{tabular}{p{0.36\linewidth}p{0.30\linewidth}p{0.24\linewidth}}
\toprule
Quantity at $X=2^{26}$ & Value & Interpretation \\
\midrule
Main $B_1(11)$ bucket residual & $-2.7429\cdot10^{-7}$ bits/gap & Null-level \\
Main $B_1(11)$ null 5--95\% interval & $[-2.7445,-2.7406]\cdot10^{-7}$ & Real value inside band \\
Rank-mod-64 CTW under $B_0$ & $0.2674$ bits/gap & Strong positive control \\
Rank-mod-64 CTW under $B_1(11)$ & $-2.7429\cdot10^{-7}$ bits/gap & Null-level \\
Exact $B_0$ code length & $4.5634$ bits/gap & Weak baseline \\
Exact $B_1(11)$ code length & $3.1704$ bits/gap & Wheel baseline \\
$B_0-B_1(11)$ improvement & $1.3930$ bits/gap & Wheel structure absorbed \\
\bottomrule
\end{tabular}
\caption{Headline paper-scale metrics at $X=2^{26}$. Values are rounded for readability; exact values are stored in \texttt{experiments/final\_metrics.json}.}
\label{tab:headline-results}
\end{table}
```

Suggested supporting sentence in `Experiments and Reproducibility`:

```latex
Exact machine-readable values are preserved in \texttt{experiments/final\_metrics.json}; the manuscript rounds some displayed values for readability.
```

## Reviewer-objection pass

Recommended paragraph for the discussion, after the paragraph explaining the positive control:

```latex
Several reviewer objections are therefore addressed by design rather than by rhetoric. If the concern is that the residual models are too weak to find any signal, the $B_0$ positive control shows that they can find omitted arithmetic structure. If the concern is that the negative result is merely an endpoint accident, the cross-exponent audit checks the same qualitative pattern across dyadic windows. If the concern is that $B_1(11)$ is not a complete model of prime gaps, that concern is accepted: the claim is deliberately only beyond this declared wheel-first-hit baseline and the tested residual predictors, not beyond all arithmetic null models.
```

This paragraph should make the manuscript more defensible without expanding the claim.

## Final proofreading outcome

The manuscript is ready for release after one of the following:

1. Apply the three suggested manuscript edits above directly to `paper.tex`, rerun `Manuscript build`, and inspect the uploaded `paper.pdf`; or
2. Leave `paper.tex` unchanged and use this file as the documented final proofreading pass, because the current manuscript already preserves the essential claim discipline.

Preferred path: apply the edits directly to `paper.tex` before release. They improve reviewer readability without changing the result.

## Final release posture

After this pass, the only remaining non-manuscript step is external archival release:

- create/tag release `v0.1.0`;
- archive on Zenodo or another DOI provider;
- update `CITATION.cff` with the DOI;
- update the manuscript availability statement with the DOI.
