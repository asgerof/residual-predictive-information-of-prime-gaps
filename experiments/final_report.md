# Final Experiment Report

Date: 2026-06-16.

## Bottom Line

The implemented pilots do not detect positive residual predictive information beyond the wheel-first-hit baseline `B1(11)`.  The framework does detect known wheel structure against `B0`, and that signal disappears once `B1(11)` is used.

## Key Metrics

- B1 bucket residual at `X=4194304`: `R=-0.000004` bits/gap (null mean `-0.000004`).
- B1 stop-time null at `X=4194304`: real `R=-0.000003728`, null mean `-0.000003727`, null 5-95% `[-0.000003733, -0.000003722]` bits/gap.
- Baseline exact code length at `X=2097152`: `B0=4.242864`, `B1(11)=2.814953`, gain `1.427910` bits/gap.
- Positive control rank-mod CTW at `X=1048576`: `R(B0)=0.267172`, `R(B1)=-0.000014` bits/gap.
- Stop-time rank-mod CTW control at `X=1048576`: `R(B0)=0.267172` (null p95 `-0.000014`), `R(B1)=-0.000014` (null p95 `-0.000014`).
- Positive control gap-mod-210 depth 1 at `X=1048576`: `R(B0)=0.249686`, `R(B1)=-0.000014` bits/gap.

## B2 Attempts

- Pair singular-series alpha scan at `X=262144`: selected `alpha=0`, oracle `alpha=0`, oracle gain `0.000000` bits/gap.
- Residue-transition calibration at `X=262144` with `lambda=0.01`: transition gain `-0.000468` bits/gap.
- Consecutive finite IE alpha scan at `X=262144`: selected `alpha=0`, oracle `alpha=0`.
- Two-alpha scan at `X=262144`: selected `(0, 0)`, oracle `(0, 0)`.
- Gentle head-8 sensitivity at `X=262144`: oracle `(0, 0)`.

## Interpretation

The tested B2 families are useful negative controls: when they are miscalibrated, the residual CTW expert gains against them, but exact prequential log-loss shows that they are worse than `B1(11)`.  Chronological and oracle calibration both collapse back to `B1(11)` in the final tested windows.

## Remaining Limits

- The largest main B1 residual run reaches only `X=2^22`.
- Stop-time synthetic nulls are now included for the main B1 and rank-mod CTW checks; some older auxiliary pilots still use fixed-count nulls.
- The B2 attempts are finite, truncated, and not canonical.
- No B3 analytic correction has been implemented.
- Real prime windows now use segmented streaming prime-pair generation; the full paper-scale runs still need to be executed.

## Reproducibility

The compact report is generated from the pinned artifact manifest `experiments/final_manifest.json`.
