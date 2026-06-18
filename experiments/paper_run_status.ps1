param(
    [int]$MaxExp = 26,
    [int]$Nulls = 200
)

$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    Write-Host "Processes:"
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -like "*run_paper_suite_x${MaxExp}_n${Nulls}.ps1*" -or
            $_.CommandLine -like "*paper_*_x${MaxExp}_n${Nulls}*" -or
            $_.CommandLine -like "*--max-exp $MaxExp*--nulls $Nulls*"
        } |
        Select-Object ProcessId, ParentProcessId, Name, CommandLine |
        Format-Table -AutoSize -Wrap

    Write-Host ""
    Write-Host "Latest logs:"
    Get-ChildItem experiments\paper_logs -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 5 Name, Length, LastWriteTime |
        Format-Table -AutoSize

    Write-Host ""
    Write-Host "Checkpoint counts:"
    $checkpointRows = @(
        Get-ChildItem experiments -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "paper_*_x${MaxExp}_n${Nulls}" } |
        ForEach-Object {
            $dir = $_
            Get-ChildItem $dir.FullName -Filter "*checkpoint*.csv" -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $rows = Import-Csv $_.FullName
                    $done = @($rows | Select-Object -ExpandProperty null_index -Unique).Count
                    [pscustomobject]@{
                        Directory = $dir.Name
                        Checkpoint = $_.Name
                        NullsDone = $done
                        NullsTotal = $Nulls
                        Percent = if ($Nulls -gt 0) { [math]::Round(100.0 * $done / $Nulls, 2) } else { 0.0 }
                        Rows = @($rows).Count
                        LastWriteTime = $_.LastWriteTime
                    }
                }
        }
    )
    $checkpointRows |
        Format-Table -AutoSize

    Write-Host ""
    Write-Host "Expected checkpoint series:"
    $expected = @(
        [pscustomobject]@{
            Directory = "paper_b1_y11_depth4_stop_time_x${MaxExp}_n${Nulls}"
            Checkpoint = "b1_u1_null_checkpoint.csv"
        },
        [pscustomobject]@{
            Directory = "paper_ctw_rank64_depth1_stop_time_x${MaxExp}_n${Nulls}"
            Checkpoint = "ctw_symbol_ladder_null_checkpoint_B0.csv"
        },
        [pscustomobject]@{
            Directory = "paper_ctw_rank64_depth1_stop_time_x${MaxExp}_n${Nulls}"
            Checkpoint = "ctw_symbol_ladder_null_checkpoint_B1_11.csv"
        },
        [pscustomobject]@{
            Directory = "paper_ladder_b0_b1_y11_x${MaxExp}_n${Nulls}"
            Checkpoint = "baseline_ladder_null_checkpoint_B0.csv"
        },
        [pscustomobject]@{
            Directory = "paper_ladder_b0_b1_y11_x${MaxExp}_n${Nulls}"
            Checkpoint = "baseline_ladder_null_checkpoint_B1_11.csv"
        }
    )

    $progressRows = foreach ($item in $expected) {
        $match = $checkpointRows |
            Where-Object {
                $_.Directory -eq $item.Directory -and $_.Checkpoint -eq $item.Checkpoint
            } |
            Select-Object -First 1
        if ($match) {
            [pscustomobject]@{
                Directory = $item.Directory
                Checkpoint = $item.Checkpoint
                NullsDone = $match.NullsDone
                NullsTotal = $Nulls
                Percent = $match.Percent
                Status = if ($match.NullsDone -ge $Nulls) { "complete" } else { "in progress/checkpointed" }
            }
        }
        else {
            [pscustomobject]@{
                Directory = $item.Directory
                Checkpoint = $item.Checkpoint
                NullsDone = 0
                NullsTotal = $Nulls
                Percent = 0.0
                Status = "not checkpointed yet"
            }
        }
    }
    $progressRows | Format-Table -AutoSize

    $totalDone = ($progressRows | Measure-Object -Property NullsDone -Sum).Sum
    $totalExpected = $Nulls * $expected.Count
    $totalPercent = if ($totalExpected -gt 0) {
        [math]::Round(100.0 * $totalDone / $totalExpected, 2)
    }
    else {
        0.0
    }
    Write-Host ""
    Write-Host "Overall checkpoint progress: $totalDone / $totalExpected null series-units ($totalPercent%)"
}
finally {
    Pop-Location
}
