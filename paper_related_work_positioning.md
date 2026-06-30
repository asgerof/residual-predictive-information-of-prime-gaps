# Related-Work and Positioning Note

This note records the intended reviewer-facing positioning of the paper. It can be used as a source for further edits to the introduction, discussion, or cover letter.

## Core distinction

The paper is not primarily another search for correlations, biases, or distributional anomalies in prime gaps. It asks a narrower predictive question:

> After a declared arithmetic baseline has already been supplied, does previous prime-gap history improve online prediction of the next gap enough to pay for a penalized residual predictor?

That distinction is the main novelty. The protocol treats apparent predictability as meaningful only relative to an explicit baseline, an online information discipline, and the residual model's own complexity cost.

## Relationship to probabilistic prime models

Classical and modern probabilistic models of the primes, including Cramer-type models, random-sieve models, Hardy--Littlewood tuple heuristics, and large-gap models, provide the arithmetic null background. This paper does not try to replace those models. It uses them as motivation for a hierarchy of declared baselines:

- `B0`: local-density/parity-level baseline;
- `B1(11)`: finite small-prime wheel-first-hit baseline through modulus `2*3*5*7*11`;
- possible future `B2`: canonical tuple-corrected baselines;
- possible future `B3`: predetermined global analytic corrections.

The paper's negative result is explicitly beyond the implemented `B1(11)` baseline and the tested residual predictors. It does not claim to rule out all higher-order arithmetic effects.

## Related-work boundary

The paper should not be presented as competing with the full number-theoretic literature on prime-gap heuristics, k-tuples, large gaps, or random-sieve models. Its role is narrower: it turns a chosen arithmetic null model into an online coding benchmark and asks whether a declared residual learner improves prediction after that benchmark has already been paid.

This boundary is useful for reviewers. A number theorist may reasonably object that `B1(11)` is not a complete arithmetic model; the correct response is to accept that objection and point out that the claim is deliberately conditional on the declared baseline hierarchy. A statistics or information-theory reviewer may ask what is new relative to compression or entropy tests; the response is that the statistic is prequential, baseline-relative, and constrained by arithmetic admissibility.

## Relationship to biases in consecutive primes

Work on biases in consecutive primes shows that consecutive-prime structure can deviate from naive independence or simple local-density expectations. That literature motivates the need for stronger arithmetic baselines before interpreting a residual signal. In the present repo, the strong positive control against `B0` is consistent with this warning: if the baseline is too weak, a residual learner can detect omitted arithmetic structure. The central result is that this apparent residual signal disappears when the `B1(11)` wheel-first-hit baseline is used.

## Relationship to entropy, compression, and correlation studies

Prior entropy or correlation studies can ask whether prime-derived sequences exhibit statistical structure. This paper instead uses prequential code length: the predictor must assign probability before the next gap is revealed, and any residual learner must pay its own complexity cost. The target is therefore not absolute randomness or compressibility of the primes. The target is residual online predictive gain after declared arithmetic information has been supplied.

## Relationship to universal coding and MDL

The residual statistic is an operational code-length comparison. Positive residual predictive information means that an online residual model shortens the prequential code relative to the declared arithmetic baseline. Null-level or negative results mean that the residual model did not improve prediction enough to overcome its own penalty. This connects the paper to prequential analysis, universal coding, and MDL-style model comparison, but with arithmetic admissibility constraints specific to prime gaps.

## Suggested introduction insertion

A compact insertion for the introduction could be:

```latex
The present question differs from existing studies of prime-gap correlations, consecutive-prime biases, entropy-like statistics, or compression of prime-derived sequences. Those studies ask whether prime-derived data display structure relative to a chosen statistical summary or heuristic model. Here the target is operational and relative: before each gap is revealed, a declared arithmetic baseline has already assigned a probability distribution, and a residual learner receives credit only if previous gap history shortens the prequential code after that baseline and after its own complexity penalty. Thus the experiment is not an absolute randomness test for the primes. It is a test of residual online predictive gain after specified arithmetic information has been made explicit.
```

A stronger reviewer-facing insertion, suitable for the discussion or cover letter, is:

```latex
This paper is not intended to replace the Hardy--Littlewood, random-sieve, large-gap, or consecutive-prime-bias literatures. Those literatures motivate the need for explicit arithmetic baselines. The contribution here is conditional and operational: given a declared baseline and an admissible online residual learner, measure whether previous gap history yields additional prequential code gain. On that narrower question, the tested residual signals separate strongly from the weak local-density baseline but not from the wheel-first-hit baseline \(B_1(11)\).
```

Another compact insertion for the discussion could be:

```latex
The positive-control result under \(B_0\) is also a caution about interpreting empirical structure in prime gaps. A flexible residual predictor can detect structure when the baseline omits small-prime congruence information. The relevant question is therefore not whether a pattern can be found, but whether it survives a declared arithmetic null model. In the present suite the tested signal does not survive \(B_1(11)\), which is why the conclusion is framed as a finite-scale falsification of this residual signal rather than as evidence for absence of all residual structure.
```

## Claim boundary to preserve

The strongest safe claim is:

> A prequential residual-coding protocol detects strong missing arithmetic structure under weak baselines, but under the tested online residual predictors it finds no robust positive residual predictive information beyond the `B1(11)` wheel-first-hit baseline up to `X = 2^26`.

Do not strengthen this into any of the following:

- prime gaps contain no residual information;
- the result proves an asymptotic theorem;
- `B1(11)` is a complete arithmetic model;
- the implemented `B2` diagnostics exhaust tuple-corrected baselines;
- 200 null replicates support extreme-tail claims.
