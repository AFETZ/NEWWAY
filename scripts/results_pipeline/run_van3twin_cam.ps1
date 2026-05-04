param(
    [string]$InputPath = ".\scripts\results_pipeline\sample_inputs\van3twin_cam",
    [string]$OutputPath = ".\scripts\results_pipeline\sample_outputs\van3twin_cam",
    [string]$Scenario = "van3twin_cam_user_sample",
    [string]$RunId = "van3twin_cam_user_sample_001"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}

python -m tools.results_pipeline.cli build `
    --source van3twin_ns3 `
    --input $InputPath `
    --output $OutputPath `
    --scenario $Scenario `
    --run-id $RunId

Write-Host ""
Write-Host "VaN3Twin CAM output written to: $OutputPath"
Write-Host "Open normalized_metrics.csv, aggregates_overall.csv, diagnostics.csv"
