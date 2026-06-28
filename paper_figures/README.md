# Paper Figures

Paper-facing figures are generated from committed paper-scale artifacts.

Run from the repository root:

```powershell
python experiments\rpi_paper_figures.py
```

For each figure, the script writes three formats:

- `.pdf`: primary paper/manuscript vector format.
- `.svg`: repository/web vector format.
- `.png`: high-resolution preview/fallback format.

Expected outputs:

- `figure_1_b1_residual_stop_time.pdf`
- `figure_1_b1_residual_stop_time.svg`
- `figure_1_b1_residual_stop_time.png`
- `figure_2_ctw_positive_control.pdf`
- `figure_2_ctw_positive_control.svg`
- `figure_2_ctw_positive_control.png`
- `figure_3_baseline_ladder_bits.pdf`
- `figure_3_baseline_ladder_bits.svg`
- `figure_3_baseline_ladder_bits.png`

The script reads only the pinned paper-scale CSV artifacts. It does not rerun
long calculations.
