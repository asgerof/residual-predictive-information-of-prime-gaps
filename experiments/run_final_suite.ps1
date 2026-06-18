param(
    [switch]$SkipRuns
)

$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    python -m py_compile `
        experiments\rpi_b1_u1.py `
        experiments\rpi_baseline_ladder.py `
        experiments\rpi_symbol_ladder.py `
        experiments\rpi_ctw_symbol_ladder.py `
        experiments\rpi_b2_pair_ladder.py `
        experiments\rpi_b2_pair_alpha_scan.py `
        experiments\rpi_transition_calibration.py `
        experiments\rpi_b2_consecutive_ladder.py `
        experiments\rpi_b2_consecutive_alpha_scan.py `
        experiments\rpi_b2_consecutive_two_alpha_scan.py `
        experiments\rpi_runtime_estimate.py `
        experiments\rpi_final_report.py

    if (-not $SkipRuns) {
        python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 21 --train-windows 3 --nulls 12 --y 11 --depth 4 --out experiments\results_b1_y11_depth4_pilot

        python experiments\rpi_b1_u1.py --min-exp 12 --max-exp 21 --train-windows 3 --nulls 12 --null-mode stop-time --y 11 --depth 4 --out experiments\results_b1_y11_depth4_stop_time

        python experiments\rpi_baseline_ladder.py --min-exp 12 --max-exp 21 --train-windows 3 --nulls 12 --b1-y 11 --depth 4 --out experiments\results_ladder_b0_b1_y11

        python experiments\rpi_symbol_ladder.py --min-exp 12 --max-exp 20 --train-windows 3 --nulls 8 --symbol-mod 210 --depth 1 --b1-y 11 --out experiments\results_symbol_mod210_depth1

        python experiments\rpi_ctw_symbol_ladder.py --min-exp 12 --max-exp 20 --train-windows 3 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 12 --out experiments\results_ctw_rank64_depth1

        python experiments\rpi_ctw_symbol_ladder.py --min-exp 12 --max-exp 20 --train-windows 3 --symbolizer rank_mod --symbol-mod 64 --depth 1 --nulls 12 --null-mode stop-time --out experiments\results_ctw_rank64_depth1_stop_time

        python experiments\rpi_b2_pair_alpha_scan.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --alpha-grid 0,0.03125,0.0625,0.125,0.25,0.5,0.75,1 --out experiments\results_b2_pair_alpha_scan_y11

        python experiments\rpi_transition_calibration.py --min-exp 12 --max-exp 18 --train-windows 3 --y 11 --mod 30 --transition-lambda 0.01 --residual-depth 1 --out experiments\results_transition_mod30_lam001

        python experiments\rpi_b2_consecutive_alpha_scan.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --ie-order 2 --max-rank 64 --max-correction-rank 20 --alpha-grid 0,0.03125,0.0625,0.125,0.25,0.5,0.75,1 --out experiments\results_b2_consecutive_alpha_scan_y11_r2

        python experiments\rpi_b2_consecutive_two_alpha_scan.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --ie-order 2 --max-rank 64 --max-correction-rank 20 --pair-grid 0,0.015625,0.03125,0.0625,0.125 --exclusion-grid 0,0.015625,0.03125,0.0625,0.125 --out experiments\results_b2_consecutive_two_alpha_scan_y11_r2

        python experiments\rpi_b2_consecutive_two_alpha_scan.py --min-exp 12 --max-exp 18 --train-windows 3 --b1-y 11 --tuple-y 11 --ie-order 1 --max-rank 64 --max-correction-rank 8 --pair-grid 0,0.015625,0.03125,0.0625,0.125 --exclusion-grid 0,0.015625,0.03125,0.0625,0.125 --out experiments\results_b2_consecutive_two_alpha_scan_y11_r1_head8
    }

    python experiments\rpi_final_report.py
}
finally {
    Pop-Location
}
