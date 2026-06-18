param(
    [int]$MaxExp = 26,
    [int]$Nulls = 200
)

$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    $logDir = Join-Path $PSScriptRoot "paper_logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $transcript = Join-Path $logDir "paper_suite_x${MaxExp}_n${Nulls}_${stamp}.log"
    Start-Transcript -Path $transcript | Out-Null

    Write-Host "Paper suite started at $(Get-Date -Format o)"
    Write-Host "max_exp=$MaxExp nulls=$Nulls"

    python experiments\rpi_runtime_estimate.py --kind b1_stop_time --max-exp $MaxExp --nulls $Nulls
    python experiments\rpi_runtime_estimate.py --kind ctw_rank64_stop_time --max-exp $MaxExp --nulls $Nulls

    python experiments\rpi_b1_u1.py `
        --min-exp 12 `
        --max-exp $MaxExp `
        --train-windows 3 `
        --nulls $Nulls `
        --null-mode stop-time `
        --checkpoint-nulls `
        --resume `
        --checkpoint-every-seconds 120 `
        --y 11 `
        --depth 4 `
        --out experiments\paper_b1_y11_depth4_stop_time_x${MaxExp}_n${Nulls}

    python experiments\rpi_ctw_symbol_ladder.py `
        --min-exp 12 `
        --max-exp $MaxExp `
        --train-windows 3 `
        --symbolizer rank_mod `
        --symbol-mod 64 `
        --depth 1 `
        --nulls $Nulls `
        --null-mode stop-time `
        --checkpoint-nulls `
        --resume `
        --checkpoint-every-seconds 120 `
        --out experiments\paper_ctw_rank64_depth1_stop_time_x${MaxExp}_n${Nulls}

    python experiments\rpi_baseline_ladder.py `
        --min-exp 12 `
        --max-exp $MaxExp `
        --train-windows 3 `
        --nulls $Nulls `
        --checkpoint-nulls `
        --resume `
        --checkpoint-every-seconds 120 `
        --b1-y 11 `
        --depth 4 `
        --out experiments\paper_ladder_b0_b1_y11_x${MaxExp}_n${Nulls}

    Write-Host "Paper suite completed at $(Get-Date -Format o)"
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
    Pop-Location
}
