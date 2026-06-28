# Paper Tables

These tables are paper-ready summaries of the completed paper-scale suite.
They are derived from the pinned artifacts in `experiments/final_manifest.json`
and the compact metrics in `experiments/final_metrics.json`.

## Table 1. Completed Paper-Scale Artifact Suite

| Experiment | Artifact directory | Range | Nulls/checkpoints | Null mode | Purpose |
|---|---:|---:|---:|---:|---|
| \(B_1(11)\) bucket residual | `experiments/paper_b1_y11_depth4_stop_time_x26_n200/` | \(X=2^{15}\) to \(2^{26}\) | 200 | stop-time | Main residual test beyond wheel-first-hit baseline |
| rank-mod-64 CTW residual | `experiments/paper_ctw_rank64_depth1_stop_time_x26_n200/` | \(X=2^{15}\) to \(2^{26}\) | 200 | stop-time | Positive control under \(B_0\), same machinery checked under \(B_1(11)\) |
| Exact B0/B1 ladder | `experiments/paper_ladder_b0_b1_y11_x26_n200/` | \(X=2^{15}\) to \(2^{26}\) | 200 | checkpointed synthetic nulls | Quantifies baseline code lengths and \(B_0\rightarrow B_1(11)\) improvement |

## Table 2. Headline Results at \(X=2^{26}\)

| Test | Baseline | \(n\) gaps | \(R\) bits/gap | Total gain bits | Null reference | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| Main bucket residual | \(B_1(11)\) | 3,645,744 | \(-2.7429243523407067\times 10^{-7}\) | approximately \(-1\) | \(z=-0.31818465586295164\) | No positive residual signal |
| CTW residual control | \(B_0\) | 3,645,744 | \(0.2674244536300398\) | \(974{,}961.0972749958\) | empirical \(p_{\geq}=0.004975124378109453\) | Positive control passes |
| CTW residual control | \(B_1(11)\) | 3,645,744 | \(-2.742924352340597\times 10^{-7}\) | approximately \(-1\) | empirical \(p_{\geq}=0.6119402985074627\) | Signal disappears under wheel-first-hit baseline |

## Table 3. Main \(B_1(11)\) Bucket-Residual Stop-Time Null Summary

| \(X\) | \(n\) gaps | Real \(R\) bits/gap | Null mean | Null 5% | Null 95% | \(z\) |
|---:|---:|---:|---:|---:|---:|---:|
| 32,768 | 3,030 | -0.0003300330033003296 | -0.0003287503729932419 | -0.00033579583613163263 | -0.000321646831778706 | -0.2975448686526256 |
| 65,536 | 5,709 | -0.00017516202487300787 | -0.00017488532169331535 | -0.00017793594306049834 | -0.00017220595832615802 | -0.15671083364704752 |
| 131,072 | 10,749 | -0.00009303190994511115 | -0.00009290635092744125 | -0.00009403799134850503 | -0.00009170946441672745 | -0.19480732245104584 |
| 262,144 | 20,390 | -0.00004904364884747404 | -0.000049040806897660563 | -0.000049465769687376126 | -0.00004854604592455939 | -0.009909586760082661 |
| 524,288 | 38,635 | -0.00002588326646822828 | -0.00002586225974140724 | -0.000026036242449489663 | -0.000025710245532844862 | -0.2127494390956222 |
| 1,048,576 | 73,586 | -0.000013589541488870198 | -0.000013591584704702405 | -0.00001365653806759982 | -0.0000135299688810716 | 0.052544280272994445 |
| 2,097,152 | 140,336 | -0.0000071257553300649776 | -0.000007124148661452677 | -0.000007150774071293196 | -0.0000070999531403092285 | -0.10314831966273086 |
| 4,194,304 | 268,216 | -0.0000037283383541623186 | -0.000003727446282642109 | -0.0000037373676971835195 | -0.0000037167398244955316 | -0.14519313137348971 |
| 8,388,608 | 513,708 | -0.0000019466311601143114 | -0.000001946294652586626 | -0.0000019503176092226532 | -0.0000019421284562603516 | -0.14439913596859255 |
| 16,777,216 | 985,818 | -0.0000010143860225721128 | -0.000001014469677713691 | -0.0000010157564134859888 | -0.0000010129454427584502 | 0.09804801891683818 |
| 33,554,432 | 1,894,120 | -0.0000005279496547209225 | -0.0000005278819915614196 | -0.0000005284861988471614 | -0.0000005273613527451509 | -0.2094636213117804 |
| 67,108,864 | 3,645,744 | -0.00000027429243523407067 | -0.00000027425414055848714 | -0.00000027445474076652 | -0.00000027406420776259464 | -0.31818465586295164 |

## Table 4. Exact Baseline Ladder at \(X=2^{26}\)

| Baseline | Exact baseline bits/gap | Residual exact bits/gap | \(R\) bits/gap | Null mean |
|---|---:|---:|---:|---:|
| \(B_0\) | 4.563439906212204 | 4.563292269169895 | 0.00014763704241220558 | \(-2.742924352340716\times 10^{-7}\) |
| \(B_1(11)\) | 3.1704284777012335 | 3.170428751993669 | \(-2.7429243523407067\times 10^{-7}\) | \(-2.7429243523406993\times 10^{-7}\) |
| \(B_0-B_1(11)\) | 1.3930114285109703 | — | — | — |

## Table 5. Claim Discipline

| Statement | Paper status |
|---|---|
| The protocol detects missing structure under a weak baseline. | Supported by the \(B_0\) CTW positive control. |
| Positive residual information survives \(B_1(11)\). | Not supported at \(X\leq 2^{26}\) by these tests. |
| The strong residual-information hypothesis is false asymptotically. | Not claimed. |
| Implemented \(B_2\)-style prototypes exhaust tuple-corrected arithmetic nulls. | Not claimed. |
| The paper contributes a falsifiable empirical protocol. | Main framing. |

## Table 6. B2-Style Diagnostics: Safe Wording

| Prototype family | How to report it |
|---|---|
| Pair singular-series reweighting | Auxiliary finite diagnostic; did not improve exact prequential log-loss over \(B_1(11)\) in tested runs. |
| Residue-transition calibration | Auxiliary finite diagnostic; useful for checking whether simple transition effects explain residuals. |
| Finite consecutive-prime inclusion-exclusion | Prototype only; not a canonical tuple-corrected baseline. |
| Two-parameter endpoint/exclusion shrinkage | Sensitivity diagnostic; should not be presented as exhaustive. |
| Any stronger \(B_2\) or \(B_3\) model | Future work unless implemented with predeclared, non-oracular rules. |
