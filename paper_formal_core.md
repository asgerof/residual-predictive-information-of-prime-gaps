# Formal Paper Core

This note collects the most important reviewer-facing material that should be integrated into the manuscript before submission. It is intentionally conservative: it strengthens the definitions and claim discipline without changing any experiment outputs.

## 1. Formal Definitions to Integrate

### Definition 1. Dyadic prime-gap block

Let \(p_1<p_2<\cdots\) be the sequence of primes and let
\[
g_n=p_{n+1}-p_n
\]
be the consecutive prime gaps. For \(X\geq 2\), define
\[
I_X=\{n:X\leq p_n<2X\}
\]
and
\[
G_X=(g_n)_{n\in I_X}.
\]
The block \(G_X\) is the object on which all prequential code lengths are evaluated.

### Definition 2. Online arithmetic baseline

An arithmetic baseline \(B_k\) is an online predictive distribution that assigns, before \(g_n\) is observed, a probability
\[
B_{k,n}(g\mid\mathcal F_{n,k})
\]
to each possible next gap \(g\). The information field \(\mathcal F_{n,k}\) contains only the arithmetic information declared at level \(k\), together with information available before \(g_n\) is revealed.

The baseline must be normalized:
\[
\sum_g B_{k,n}(g\mid\mathcal F_{n,k})=1.
\]

### Definition 3. Admissible residual predictor

A residual predictor \(U_k\) is admissible relative to \(B_k\) if it may use the same declared arithmetic information as \(B_k\), together with previous gap-derived symbols, but may not use future gaps, future primes, primality testing of candidate offsets in the target window, direct sieving outside the declared finite modulus set, or any table/compressed representation of the target block \(G_X\).

A convenient sufficient form is
\[
U_k(g\mid\text{history},p_n)=U_s(s(g,p_n)\mid\text{history},p_n)B_k(g\mid p_n,s(g,p_n)),
\]
where \(s(g,p_n)\) is a declared residual symbol and \(B_k(g\mid p_n,s(g,p_n))\) is the baseline distribution conditional on that symbol. This allows sequential reweighting of residual symbols without letting the residual model become a hidden prime generator.

### Definition 4. Prequential residual code gain

For any online predictor \(Q\), define the prequential code length
\[
L_Q(G_X)=\sum_{n\in I_X}-\log_2 Q_n(g_n\mid\mathcal F_{n,k}).
\]
The residual predictive information statistic is
\[
R_k(X)=\frac{L_{B_k}(G_X)-L_{U_k}(G_X)}{|I_X|}.
\]
Positive values mean that the residual predictor improves on the arithmetic baseline after paying its online complexity cost. Null-level or negative values mean that no residual gain is detected for the tested baseline, scale, and residual model class.

### Definition 5. Stop-time synthetic null

A stop-time synthetic null sequence for baseline \(B_k\) is generated online from \(B_k\) until the same endpoint scale is reached as in the corresponding real dyadic window. The residual statistic is then evaluated on the synthetic sequence using the same residual machinery as for the real gaps.

Stop-time nulls avoid conditioning away the number of gaps in the window unless such conditioning is explicitly part of the null hypothesis.

## 2. Reviewer-Facing \(B_1(y)\) Normalization and Support Checklist

For the wheel-first-hit baseline \(B_1(y)\), the manuscript should explicitly verify the following.

Let
\[
W_y=\prod_{q\leq y}q.
\]
For a current prime residue \(r=p_n\bmod W_y\), define the admissible offset set
\[
\mathcal A_y(r)=\{m>0:\gcd(r+m,W_y)=1\}.
\]
The implementation orders these offsets by increasing size and assigns first-hit probabilities over that ordered admissible set. A reviewer should be able to check that:

1. forbidden offsets receive probability zero;
2. admissible offsets receive nonnegative probability;
3. the assigned probabilities sum to one for each current residue class;
4. the hit/hazard parameter is fixed before evaluating the target gap;
5. the calibration uses only the declared local scale information;
6. the residual predictor preserves the baseline distribution conditional on the residual symbol.

Suggested manuscript wording:

> The role of \(B_1(y)\) is not to model all arithmetic structure in prime gaps. Its narrower role is to remove the most elementary finite congruence obstructions before any residual learner is credited with predictive gain. The residual test is therefore a test beyond this declared wheel-first-hit baseline, not beyond all possible Hardy--Littlewood or global analytic corrections.

## 3. Claim-Discipline Table for the Manuscript

| Statement | Paper status |
|---|---|
| The protocol detects omitted arithmetic structure under a weak local-density baseline. | Supported by the \(B_0\) positive control. |
| Positive residual predictive information survives \(B_1(11)\). | Not supported at \(X\leq2^{26}\) by the tested residual predictors. |
| Prime gaps contain no residual information. | Not claimed. |
| The finite-scale result proves an asymptotic theorem. | Not claimed. |
| Implemented \(B_2\)-style diagnostics exhaust tuple-corrected arithmetic baselines. | Not claimed. |
| The contribution is a falsifiable empirical protocol plus a controlled negative result. | Main framing. |

## 4. Minimum Correctness Tests to Add Next

The current reproducibility checks validate artifacts and regenerate reports. Before submission, add a small unit-test layer that checks the mathematical core directly.

Recommended tests:

```text
tests/test_prime_gap_generation.py
tests/test_b0_distribution.py
tests/test_b1_wheel_support.py
tests/test_b1_normalization.py
tests/test_prequential_no_future_access.py
tests/test_stop_time_null_generation.py
tests/test_final_metrics_recompute.py
```

The most important tests are the \(B_1\) support/normalization tests and the final metrics recomputation test, because they defend the central negative result.

## 5. Safe Abstract/Conclusion Language

Use language like this:

> Under the tested online residual predictors and through \(X=2^{26}\), no positive residual predictive information is detected beyond the \(B_1(11)\) wheel-first-hit baseline.

Avoid language like this:

> Prime gaps contain no residual predictive information.

The first sentence is supported by the current artifacts. The second is substantially stronger than the evidence and should not appear in the paper.
