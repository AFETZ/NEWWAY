param(
    [string]$InputPath = ".\scripts\results_pipeline\sample_inputs\simu5g_scavetool\output_all_sample.csv",
    [string]$OutputPath = ".\scripts\results_pipeline\sample_outputs\simu5g_scavetool",
    [string]$Scenario = "simu5g_vector_user_sample",
    [string]$RunId = "simu5g_vector_user_sample_001"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}

python -m tools.results_pipeline.cli build `
    --source simu5g `
    --input $InputPath `
    --output $OutputPath `
    --scenario $Scenario `
    --run-id $RunId

Write-Host ""
Write-Host "Simu5G output written to: $OutputPath"
Write-Host "Open normalized_metrics.csv, aggregates_by_metric.csv, aggregates_overall.csv, diagnostics.csv"
