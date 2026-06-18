# B1(y) vs U1 Pilot Results

Date: 2026-06-16.

## Question

Test whether a residual online sequence model \(U_1\) obtains positive
per-gap code gain over a concrete wheel-corrected first-hit model \(B_1(y)\):

\[
R_1(X)=\frac{L_{B_1}(G_X)-L_{U_1}(G_X)}{|G_X|}.
\]

## Implementation

Script: `experiments/rpi_b1_u1.py`.

Baseline:

- \(B_1(y)\) is a wheel-first-hit model.
- \(W_y=\prod_{q\leq y}q\).
- Offsets \(m\) are admissible only if \(\gcd(p+m,W_y)=1\).
- The first-hit hazard among wheel-admissible offsets is
  \[
  \theta(p)=\frac{W_y}{\varphi(W_y)\log p},
  \]
  clipped away from 0 and 1.

Residual model:

- Gaps are bucketed by \(g/\log p\).
- The Markov residual expert is a KT-smoothed finite-depth Markov model on
  bucket symbols.
- \(U_1\) is a two-expert Bayesian mixture of:
  1. the \(B_1\) bucket distribution;
  2. the trained Markov bucket predictor.
- Within each bucket, \(U_1\) uses the conditional \(B_1\) gap distribution.

Thus \(U_1\) can only gain by predicting bucket-level residual structure; it
does not replace \(B_1\) with a hidden gap generator.

Training/testing:

- Training uses only earlier dyadic windows.
- Expert weights are reset at each held-out test window, so trying the
  residual expert costs about one bit per window.
- Synthetic nulls are generated from the same \(B_1(y)\) model.

## Main Pilot

Command:

```powershell
python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 21 --train-windows 3 --nulls 12 --y 11 --depth 4 --out experiments\results_b1_y11_depth4_pilot
```

Parameters:

- \(y=11\), so \(W=2310\), \(\varphi(W)=480\).
- Bucket width: 0.5 for \(g/\log p\), up to 8, with an overflow bucket.
- Markov depth: 4.

Results:

| \(X\) | gaps | \(R_1(X)\) bits/gap | null mean |
|---:|---:|---:|---:|
| 32768 | 3030 | -0.000330033 | -0.000330033 |
| 65536 | 5709 | -0.000175162 | -0.000175162 |
| 131072 | 10749 | -0.000093032 | -0.000093032 |
| 262144 | 20390 | -0.000049044 | -0.000049044 |
| 524288 | 38635 | -0.000025883 | -0.000025883 |
| 1048576 | 73586 | -0.000013590 | -0.000013590 |
| 2097152 | 140336 | -0.000007126 | -0.000007126 |

The value is essentially \(-1/|G_X|\), i.e. the one-bit cost of including the
residual expert in the test-window mixture. No positive residual predictive
information is detected in this pilot.

## Sensitivity Checks

Two additional runs gave the same qualitative result:

```powershell
python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 20 --train-windows 3 --nulls 8 --y 7 --depth 2 --out experiments\results_b1_y7_depth2_pilot
python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 20 --train-windows 3 --nulls 8 --y 11 --depth 6 --out experiments\results_b1_y11_depth6_pilot
```

In both cases \(R_1(X)\) again matched the one-bit-per-window mixture penalty
and did not exceed the synthetic null behavior.

## Baseline Ladder: \(B_0\) vs \(B_1\)

Follow-up script:

`experiments/rpi_baseline_ladder.py`.

Command:

```powershell
python experiments\rpi_baseline_ladder.py --min-exp 12 --max-exp 21 --train-windows 3 --nulls 12 --b1-y 11 --depth 4 --out experiments\results_ladder_b0_b1_y11
```

This compares:

- \(B_0\): implemented as `y=2`, i.e. a local density first-hit model on even
  gaps only;
- \(B_1(11)\): wheel-first-hit with \(W=2310\).

The residual result is again essentially zero for both baselines:

| Baseline | \(X=2^{21}\) gaps | \(R(X)\) bits/gap |
|---|---:|---:|
| \(B_0\) | 140336 | -0.000007126 |
| \(B_1(11)\) | 140336 | -0.000007126 |

However, the exact baseline code lengths are very different:

| \(X\) | \(B_0\) bits/gap | \(B_1(11)\) bits/gap | \(B_0-B_1\) |
|---:|---:|---:|---:|
| 32768 | 3.734550 | 2.226882 | 1.507668 |
| 65536 | 3.830373 | 2.340799 | 1.489574 |
| 131072 | 3.924835 | 2.451311 | 1.473524 |
| 262144 | 4.008503 | 2.548242 | 1.460261 |
| 524288 | 4.092900 | 2.645104 | 1.447796 |
| 1048576 | 4.169057 | 2.731674 | 1.437383 |
| 2097152 | 4.242864 | 2.814953 | 1.427911 |

Interpretation: wheel structure is strongly visible as an arithmetic baseline
improvement, but the current residual model does not rediscover it from
bucketed gap history. This is a limitation of the present \(U\), not evidence
that \(B_0\) is adequate.

The next useful model improvement is therefore not larger \(X\), but a
stronger residual predictor that can use richer sequential symbols, for
example exact small gap residues or a context-tree over wheel-phase changes,
while keeping the information restrictions explicit.

## Rich Symbol Test: Gap Residues Modulo 210

Follow-up script:

`experiments/rpi_symbol_ladder.py`.

Command:

```powershell
python experiments\rpi_symbol_ladder.py --min-exp 12 --max-exp 20 --train-windows 3 --nulls 12 --symbol-mod 210 --depth 0 --b1-y 11 --out experiments\results_symbol_mod210_depth0
```

This changes the residual symbol from coarse \(g/\log p\) buckets to
\[
g \bmod 210.
\]

The residual expert is still conservative: a two-expert mixture of the
baseline symbol distribution and a KT-smoothed online predictor. With
`depth=0`, the residual model is essentially learning the online marginal
distribution of gap residues modulo 210 from previous observations.

Results:

| \(X\) | gaps | \(R_0(X)\) vs \(B_0\) | \(R_1(X)\) vs \(B_1(11)\) |
|---:|---:|---:|---:|
| 32768 | 3030 | 0.048034 | -0.000330 |
| 65536 | 5709 | 0.055518 | -0.000175 |
| 131072 | 10749 | 0.068287 | -0.000093 |
| 262144 | 20390 | 0.072535 | -0.000049 |
| 524288 | 38635 | 0.076678 | -0.000026 |
| 1048576 | 73586 | 0.075740 | -0.000014 |

Interpretation:

- Against \(B_0\), the residual predictor finds a real positive code gain.
- Against \(B_1(11)\), the gain disappears and only the one-bit mixture
  penalty remains.
- This is exactly the desired diagnostic behavior: the test can detect
  arithmetic residue structure when the baseline lacks it, and the effect
  vanishes when the wheel baseline is given that structure explicitly.

This is not evidence for deep residual sequential information. It is evidence
that the experimental framework is now sensitive enough to detect known
arithmetic structure and to watch it disappear under the correct null model.

## Sequential Residue Tests: Depth 1 and Depth 2

The next runs used the same symbol \(g\bmod 210\), but allowed the residual
expert to condition on previous symbols.

Depth 1 command:

```powershell
python experiments\rpi_symbol_ladder.py --min-exp 12 --max-exp 20 --train-windows 3 --nulls 8 --symbol-mod 210 --depth 1 --b1-y 11 --out experiments\results_symbol_mod210_depth1
```

Depth 1 results:

| \(X\) | gaps | \(R_0(X)\) vs \(B_0\) | \(R_1(X)\) vs \(B_1(11)\) |
|---:|---:|---:|---:|
| 32768 | 3030 | 0.058755 | -0.000330 |
| 65536 | 5709 | 0.129785 | -0.000175 |
| 131072 | 10749 | 0.188604 | -0.000093 |
| 262144 | 20390 | 0.216428 | -0.000049 |
| 524288 | 38635 | 0.236881 | -0.000026 |
| 1048576 | 73586 | 0.249686 | -0.000014 |

Depth 2 command:

```powershell
python experiments\rpi_symbol_ladder.py --min-exp 12 --max-exp 19 --train-windows 3 --nulls 6 --symbol-mod 210 --depth 2 --b1-y 11 --out experiments\results_symbol_mod210_depth2
```

Depth 2 results:

| \(X\) | gaps | \(R_0(X)\) vs \(B_0\) | \(R_1(X)\) vs \(B_1(11)\) |
|---:|---:|---:|---:|
| 32768 | 3030 | -0.000330 | -0.000330 |
| 65536 | 5709 | -0.000175 | -0.000175 |
| 131072 | 10749 | 0.066216 | -0.000093 |
| 262144 | 20390 | 0.146065 | -0.000049 |
| 524288 | 38635 | 0.211328 | -0.000026 |

Interpretation:

- Depth 1 greatly strengthens the apparent residual signal against \(B_0\),
  reaching about \(0.25\) bits/gap by \(X=2^{20}\).
- Depth 2 is initially data-hungry, but eventually finds the same kind of
  signal against \(B_0\).
- In both cases, \(B_1(11)\) removes the signal completely.

The large `z_vs_null` values in these runs are not meaningful as calibrated
Gaussian z-scores; the null variance is numerically near zero because the
mixture usually falls back to the baseline expert. The relevant statistic is
the direct code gain and its disappearance under \(B_1\).

## Next-Phase CTW Symbol Tests

Follow-up script:

`experiments/rpi_ctw_symbol_ladder.py`.

This keeps the same baseline-centered coding rule,

\[
U(g\mid H,p)=U_s(s(g,p)\mid H,p)\,B(g\mid p,s(g,p)),
\]

but replaces the residual expert with a sparse context-tree mixture. It also
adds a second symbol family:

\[
s = K(g,p) \bmod M,
\]

where \(K(g,p)\) is the admissible first-hit rank of the observed gap under
the relevant wheel baseline. Under \(B_1(y)\), this rank is geometrically
distributed, so the baseline symbol mass is available in closed form.

Rank-mod pilot command:

```powershell
python experiments\rpi_ctw_symbol_ladder.py --min-exp 12 --max-exp 20 --train-windows 3 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 12 --out experiments\results_ctw_rank64_depth1
```

Results:

| \(X\) | gaps | \(R_0(X)\) vs \(B_0\) | \(R_1(X)\) vs \(B_1(11)\) |
|---:|---:|---:|---:|
| 32768 | 3030 | 0.211081 | -0.000330 |
| 65536 | 5709 | 0.229779 | -0.000175 |
| 131072 | 10749 | 0.255507 | -0.000093 |
| 262144 | 20390 | 0.259341 | -0.000049 |
| 524288 | 38635 | 0.264643 | -0.000026 |
| 1048576 | 73586 | 0.267172 | -0.000014 |

Interpretation:

- The rank-mod symbolization finds a large residual signal against \(B_0\),
  rising to about \(0.27\) bits/gap at \(X=2^{20}\).
- The same signal disappears completely against \(B_1(11)\), leaving only the
  one-bit mixture cost per test window.
- This is an independent positive-control result: the framework is not only
  detecting \(g\bmod 210\), but also wheel-induced structure expressed through
  admissible hit ranks.
- CTW depth 3 was too sparse for \(g\bmod 210\) at these sample sizes and
  failed the positive control. Depth 1 is the useful setting for now.

## First B2 Pair-Correction Prototype

Follow-up script:

`experiments/rpi_b2_pair_ladder.py`.

This implements a first \(B_2\)-style baseline:

\[
B_{2,\mathrm{pair}}(g\mid p)
\propto
B_1(g\mid p)\,\mathfrak S_{\leq y}(\{0,g\}),
\]

where the singular-series factor is truncated to primes \(q\leq y\), and the
distribution is renormalized over the periodic stream of wheel-admissible
first-hit candidates.

Pilot command:

```powershell
python experiments\rpi_b2_pair_ladder.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 6 --out experiments\results_b2_pair_rank64_y11_depth1
```

Results:

| Baseline | \(X=2^{18}\) gaps | baseline bits/gap | \(R(X)\) bits/gap |
|---|---:|---:|---:|
| \(B_0\) | 20390 | 4.008503 | 0.259341 |
| \(B_1(11)\) | 20390 | 2.548242 | -0.000049 |
| \(B_{2,\mathrm{pair}}(11,11)\) | 20390 | 2.622846 | 0.058373 |

Interpretation:

- \(B_1(11)\) remains the best baseline of these three in exact code length.
- The pair-corrected prototype is worse than \(B_1(11)\) by about \(0.075\)
  bits/gap at \(X=2^{18}\).
- The positive residual against \(B_{2,\mathrm{pair}}\) should therefore not
  be read as deep residual information. It is more likely detecting
  miscalibration introduced by the naive pair reweighting.
- This is still useful: the experiment now has a concrete falsification
  mechanism for proposed stronger baselines. A \(B_2\) candidate must improve
  or at least preserve exact prequential code length before residual gains
  against it are mathematically interesting.

## Calibrated B2 Pair Alpha Scan

Follow-up script:

`experiments/rpi_b2_pair_alpha_scan.py`.

The pair correction was generalized to

\[
B_{2,\alpha}(g\mid p)
\propto
B_1(g\mid p)\,\mathfrak S_{\leq y}(\{0,g\})^\alpha,
\]

where \(\alpha=0\) is exactly \(B_1\), and \(\alpha=1\) is the full naive pair
correction.

Calibration command:

```powershell
python experiments\rpi_b2_pair_alpha_scan.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --alpha-grid 0,0.03125,0.0625,0.125,0.25,0.5,0.75,1 --out experiments\results_b2_pair_alpha_scan_y11
```

Selected-alpha results:

| \(X\) | gaps | selected \(\alpha\) | selected gain vs \(B_1\) | oracle \(\alpha\) |
|---:|---:|---:|---:|---:|
| 32768 | 3030 | 0.125 | -0.001608 | 0 |
| 65536 | 5709 | 0 | 0.000000 | 0 |
| 131072 | 10749 | 0 | 0.000000 | 0 |
| 262144 | 20390 | 0 | 0.000000 | 0 |

Interpretation:

- Chronological calibration quickly selects \(\alpha=0\), i.e. no pair
  correction.
- Even the inadmissible per-window oracle selects \(\alpha=0\) on all held-out
  windows in this scan.
- A short residual check with `--pair-alpha 0` confirms that
  \(B_{2,\alpha=0}\) is numerically identical to \(B_1(11)\), including the
  disappearance of the rank-mod residual signal.
- Conclusion: this truncated pair-factor family does not produce a stronger
  baseline at these scales. The next \(B_2\) attempt should model
  consecutive-prime constraints or learned residue-transition calibration,
  not just multiply first-hit probabilities by a raw pair singular series.

## Residue-Transition Calibration Attempt

Follow-up script:

`experiments/rpi_transition_calibration.py`.

This implements a chronological transition baseline for consecutive-prime
residues. For a modulus \(M\), let

\[
c=p_n\bmod M,\qquad s=p_{n+1}\bmod M.
\]

The calibrated baseline keeps \(B_1\)'s within-symbol first-hit distribution,
but replaces the \(B_1\) symbol mass by a transition estimate trained only on
earlier dyadic windows:

\[
B_{\mathrm{tr}}(g\mid p)
=
B_1(g\mid p)\,
\frac{
P_{\mathrm{train}}(s\mid c)
}{
B_{1,s}(s\mid p)
}.
\]

To avoid over-trusting a coarse empirical transition table, the implemented
test uses shrinkage

\[
P_\lambda(s\mid c,p)
=
(1-\lambda)B_{1,s}(s\mid p)
+\lambda P_{\mathrm{train}}(s\mid c),
\]

so \(\lambda=0\) is exactly \(B_1\).

Representative commands:

```powershell
python experiments\rpi_transition_calibration.py --min-exp 12 --max-exp 18 --train-windows 3 --y 11 --mod 30 --transition-lambda 0.01 --residual-depth 1 --out experiments\results_transition_mod30_lam001
python experiments\rpi_transition_calibration.py --min-exp 12 --max-exp 17 --train-windows 3 --y 11 --mod 210 --transition-lambda 0.01 --residual-depth 1 --out experiments\results_transition_mod210_lam001
```

Selected results:

| Modulus | \(\lambda\) | largest \(X\) | transition gain vs \(B_1\) | residual gain vs transition |
|---:|---:|---:|---:|---:|
| 30 | 0 | \(2^{18}\) | 0.000000 | -0.000049 |
| 30 | 0.01 | \(2^{18}\) | -0.000468 | -0.000049 |
| 30 | 0.05 | \(2^{18}\) | -0.005165 | -0.000049 |
| 30 | 0.10 | \(2^{18}\) | -0.014192 | -0.000049 |
| 210 | 0 | \(2^{17}\) | 0.000000 | -0.000093 |
| 210 | 0.01 | \(2^{17}\) | -0.002162 | -0.000093 |

Interpretation:

- The coarse empirical residue-transition calibration does not improve
  \(B_1(11)\); every positive shrinkage weight tested made exact code length
  worse.
- The residual CTW expert is also rejected on top of these transition
  baselines, leaving the one-bit mixture cost.
- This suggests \(B_1\)'s full wheel phase already captures the finite
  transition information available to this simple calibration, and that
  collapsing to \(p\bmod 30\) or \(p\bmod 210\) loses useful information.
- The next plausible \(B_2\) must be more local and consecutive-specific:
  for example a calibrated no-intermediate-prime model over short admissible
  candidate patterns, rather than a coarse residue-transition table.

## Consecutive-Prime \(B_2\) Prototype

Follow-up scripts:

- `experiments/rpi_b2_consecutive_ladder.py`
- `experiments/rpi_b2_consecutive_alpha_scan.py`

This implements the next \(B_2\)-style attempt suggested by the transition
calibration result.  Instead of reweighting only by the endpoint pair
\(\{0,g\}\), the new baseline tries to model the fact that a consecutive
prime gap also asserts that no wheel-admissible intermediate candidate became
prime.

For a wheel-admissible candidate of rank \(k\), let \(H\) be the earlier
wheel-admissible offsets before the candidate gap \(g\).  The correction is a
truncated inclusion-exclusion estimate of

\[
P(\text{no }h\in H\text{ is prime}\mid p\text{ and }p+g\text{ are prime}),
\]

using truncated singular-series ratios for
\(\{0,g\}\cup S\), \(S\subseteq H\).  The implemented correction is finite:
it is applied only up to `max_correction_rank`, and the far tail falls back to
\(B_1\).  The shrinkage parameter \(\alpha\) satisfies:

- \(\alpha=0\): exactly \(B_1\);
- \(\alpha=1\): full finite consecutive correction.

Sanity command:

```powershell
python experiments\rpi_b2_consecutive_ladder.py --min-exp 12 --max-exp 15 --train-windows 2 --b1-y 11 --tuple-y 11 --ie-order 2 --consecutive-alpha 0 --symbol-mod 64 --depth 1 --max-rank 64 --nulls 2 --out experiments\results_b2_consecutive_alpha0_sanity
```

Result: with \(\alpha=0\), `B2consec` matches \(B_1(11)\) bit-for-bit on the
tested windows, confirming the normalization and shrinkage baseline.

Full-correction pilot command:

```powershell
python experiments\rpi_b2_consecutive_ladder.py --min-exp 12 --max-exp 16 --train-windows 3 --b1-y 11 --tuple-y 11 --ie-order 2 --consecutive-alpha 1 --symbol-mod 64 --depth 1 --max-rank 64 --max-correction-rank 20 --nulls 2 --out experiments\results_b2_consecutive_y11_r2_alpha1_pilot
```

Selected results:

| Baseline | \(X\) | gaps | baseline bits/gap | residual gain |
|---|---:|---:|---:|---:|
| \(B_1(11)\) | \(2^{15}\) | 3030 | 2.226882 | -0.000330 |
| \(B_{2,\mathrm{consec}}\), \(\alpha=1\) | \(2^{15}\) | 3030 | 2.300715 | 0.024746 |
| \(B_1(11)\) | \(2^{16}\) | 5709 | 2.340799 | -0.000175 |
| \(B_{2,\mathrm{consec}}\), \(\alpha=1\) | \(2^{16}\) | 5709 | 2.416149 | 0.038836 |

The full correction is worse than \(B_1\), and the residual expert then gains
against it.  This should be interpreted as residual detection of
miscalibration, not as deep residual prime-gap information.

Alpha calibration command:

```powershell
python experiments\rpi_b2_consecutive_alpha_scan.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --ie-order 2 --max-rank 64 --max-correction-rank 20 --alpha-grid 0,0.03125,0.0625,0.125,0.25,0.5,0.75,1 --out experiments\results_b2_consecutive_alpha_scan_y11_r2
```

Selected-alpha results:

| \(X\) | gaps | selected \(\alpha\) | selected gain vs \(B_1\) | oracle \(\alpha\) | oracle gain vs \(B_1\) |
|---:|---:|---:|---:|---:|---:|
| 32768 | 3030 | 0 | 0.000000 | 0 | 0.000000 |
| 65536 | 5709 | 0 | 0.000000 | 0 | 0.000000 |
| 131072 | 10749 | 0 | 0.000000 | 0 | 0.000000 |
| 262144 | 20390 | 0 | 0.000000 | 0 | 0.000000 |

At \(X=2^{18}\), every positive alpha in the tested grid worsened exact
prequential code length relative to \(B_1\); for example alpha \(0.03125\)
lost about \(0.00037\) bits/gap and alpha \(1\) lost about \(0.07325\)
bits/gap.

Conclusion: the project now has a consecutive-specific \(B_2\) prototype, and
it passes the \(\alpha=0\) sanity check.  However, this finite
inclusion-exclusion correction does not yet produce a stronger baseline than
\(B_1(11)\).  The next refinement should calibrate the no-intermediate-prime
hazard more gently, perhaps by learning one or two shrinkage parameters on
earlier windows or by separating endpoint-pair and intermediate-exclusion
terms.

## Two-Parameter \(B_2\) Calibration

Follow-up script:

`experiments/rpi_b2_consecutive_two_alpha_scan.py`

This separates the two effects that were entangled in the first consecutive
prototype:

- `pair_alpha`: shrinkage on the endpoint Hardy-Littlewood pair factor;
- `exclusion_alpha`: shrinkage on the no-intermediate-prime
  inclusion-exclusion factor.

Thus `(pair_alpha, exclusion_alpha) = (0, 0)` is exactly \(B_1\), while
positive values test progressively stronger finite \(B_2\) corrections.

Sanity command:

```powershell
python experiments\rpi_b2_consecutive_two_alpha_scan.py --min-exp 12 --max-exp 15 --train-windows 2 --b1-y 11 --tuple-y 11 --ie-order 2 --max-rank 32 --max-correction-rank 12 --pair-grid 0 --exclusion-grid 0 --out experiments\results_b2_consecutive_two_alpha_zero_sanity
```

Result: the zero-zero model reproduces \(B_1\) exactly on held-out windows.

Main two-parameter scan:

```powershell
python experiments\rpi_b2_consecutive_two_alpha_scan.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --ie-order 2 --max-rank 64 --max-correction-rank 20 --pair-grid 0,0.015625,0.03125,0.0625,0.125 --exclusion-grid 0,0.015625,0.03125,0.0625,0.125 --out experiments\results_b2_consecutive_two_alpha_scan_y11_r2
```

Selected-alpha results:

| \(X\) | gaps | selected pair | selected exclusion | selected gain vs \(B_1\) | oracle pair | oracle exclusion | oracle gain vs \(B_1\) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 32768 | 3030 | 0.125 | 0 | -0.001608 | 0 | 0 | 0.000000 |
| 65536 | 5709 | 0.015625 | 0 | -0.000109 | 0 | 0 | 0.000000 |
| 131072 | 10749 | 0 | 0 | 0.000000 | 0 | 0 | 0.000000 |
| 262144 | 20390 | 0 | 0 | 0.000000 | 0 | 0 | 0.000000 |

At \(X=2^{18}\), the best grid point is exactly \(B_1\).  The next closest
candidate, `(pair_alpha, exclusion_alpha) = (0.015625, 0)`, loses about
`0.000090` bits/gap, and `(0, 0.015625)` loses about `0.000174` bits/gap.

Sensitivity check:

```powershell
python experiments\rpi_b2_consecutive_two_alpha_scan.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --ie-order 1 --max-rank 64 --max-correction-rank 8 --pair-grid 0,0.015625,0.03125,0.0625,0.125 --exclusion-grid 0,0.015625,0.03125,0.0625,0.125 --out experiments\results_b2_consecutive_two_alpha_scan_y11_r1_head8
```

The gentler first-order/head-8 correction gives the same selected and oracle
result: `(0, 0)` is best on the later held-out windows.

Conclusion: separating endpoint-pair and intermediate-exclusion shrinkage did
not rescue this finite \(B_2\) family at the tested scale.  The evidence now
points away from raw singular-series reweighting of first-hit ranks and
toward either a different generative calibration of the hazard, larger-scale
testing, or a baseline that models the candidate process more directly rather
than as a finite multiplicative correction to \(B_1\).

## Final Interpretation

For the tested baseline hierarchy and residual coders, the main empirical
answer is:

\[
R(X)>0\text{ beyond }B_1(11)?
\]

No.  The final completed pilots do not detect positive residual predictive
information beyond the wheel-first-hit baseline \(B_1(11)\).

This is not merely a failure to find a pattern.  The positive controls show
that the framework can detect known arithmetic structure: rank-mod and
gap-residue residual coders obtain large gains against \(B_0\), and those
gains disappear when the wheel structure is built into \(B_1(11)\).  The
subsequent \(B_2\) attempts then act as calibration tests.  Naive pair
singular-series reweighting, residue-transition calibration, finite
consecutive-prime inclusion-exclusion, and two-parameter endpoint/exclusion
shrinkage all fail to improve exact prequential code length over \(B_1(11)\)
at the tested scales.  When these baselines are miscalibrated, the residual
expert can gain against them, but that gain should be read as detection of
baseline error, not as evidence for deep residual prime-gap information.

The current best empirical summary is therefore:

- Known wheel structure is strongly visible and correctly removed by \(B_1\).
- No tested residual model finds stable positive code gain beyond \(B_1(11)\).
- No tested finite \(B_2\) correction improves on \(B_1(11)\).
- The strong residual hypothesis is not supported by these pilots.
- The broader program remains meaningful as a falsifiable protocol.

## Stop-Time Null Follow-Up

The main B1 residual run and the rank-mod CTW positive control were rerun
with synthetic windows generated until the synthetic prime path exits each
dyadic interval, rather than conditioning on the real number of gaps in the
window.

Commands:

```powershell
python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 21 --train-windows 3 --nulls 12 --null-mode stop-time --y 11 --depth 4 --out experiments\results_b1_y11_depth4_stop_time
python experiments\rpi_ctw_symbol_ladder.py --min-exp 12 --max-exp 20 --train-windows 3 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 12 --null-mode stop-time --out experiments\results_ctw_rank64_depth1_stop_time
```

Results:

- At \(X=2^{21}\), the B1 bucket residual remains
  \(-0.000007126\) bits/gap.  The stop-time null mean is
  \(-0.000007118\), with 5-95% range
  \([-0.000007145,-0.000007095]\).
- At \(X=2^{20}\), the rank-mod CTW positive control remains large against
  \(B_0\): \(0.267172\) bits/gap, while the stop-time null p95 is
  \(-0.000014\).
- Against \(B_1(11)\), the same rank-mod CTW run remains at the mixture
  penalty: \(-0.000014\) bits/gap, matching the stop-time null behavior.

Conclusion: the main negative result beyond \(B_1(11)\), and the positive
control against \(B_0\), do not depend on the older fixed-count synthetic null
protocol.

## Limitations

- The tested range is modest: up to \(X=2^{21}\) in the main completed
  residual run, and up to \(X=2^{18}\) for the slower \(B_2\) calibration
  scans.
- The implemented \(B_2\) families are finite, truncated, and not canonical.
  They are best viewed as falsifiable prototypes rather than final arithmetic
  null models.
- No \(B_3\)-style global analytic correction has been implemented.
- \(U_1\) and the CTW residual experts are intentionally conservative and use
  limited symbolizations.
- Stop-time synthetic nulls are now implemented for the main B1 and rank-mod
  CTW checks.  Some older auxiliary pilots still use fixed-count nulls.
- The current prime generation uses a simple in-memory sieve with a fixed
  upper buffer, not a large-scale segmented sieve.
- The synthetic null variance is often nearly zero because the residual
  expert is consistently rejected by the mixture, leaving only the one-bit
  expert cost.

## Final Artifacts

The compact final report is generated by:

```powershell
python experiments\rpi_final_report.py
```

It writes:

- `experiments/final_report.md`
- `experiments/final_metrics.json`

The reproducibility driver is:

```powershell
powershell -ExecutionPolicy Bypass -File experiments\run_final_suite.ps1
```

Use `-SkipRuns` to compile all scripts and regenerate the final report from
the existing CSV artifacts without rerunning the longer pilots.
