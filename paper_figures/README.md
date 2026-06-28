# Paper Figures

Paper-facing figures are generated from committed paper-scale artifacts.

Run from the repository root:

```powershell
python experiments\rpi_paper_figures.py
```

This writes:

- `figure_1_b1_residual_stop_time.svg`
- `figure_2_ctw_positive_control.svg`
- `figure_3_baseline_ladder_bits.svg`

The script reads only the pinned paper-scale CSV artifacts. It does not rerun
long calculations.
