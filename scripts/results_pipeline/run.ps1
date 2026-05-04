$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}

function Read-WithDefault {
    param(
        [string]$PromptText,
        [string]$DefaultValue
    )

    $value = Read-Host "$PromptText [$DefaultValue]"
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $DefaultValue
    }
    return $value
}

function Read-ExistingDirectory {
    param(
        [string]$PromptText,
        [string]$DefaultValue
    )

    while ($true) {
        $value = Read-WithDefault $PromptText $DefaultValue

        if ($value -eq "q" -or $value -eq "Q") {
            Write-Host "Выход без запуска pipeline."
            exit 0
        }

        if (Test-Path $value -PathType Container) {
            return $value
        }

        Write-Host ""
        Write-Host "Ошибка: папка не найдена: $value" -ForegroundColor Yellow
        Write-Host "Введите корректный путь к папке или q для выхода."
        Write-Host ""
    }
}

function Read-ExistingCsvFile {
    param(
        [string]$PromptText,
        [string]$DefaultValue
    )

    while ($true) {
        $value = Read-WithDefault $PromptText $DefaultValue

        if ($value -eq "q" -or $value -eq "Q") {
            Write-Host "Выход без запуска pipeline."
            exit 0
        }

        if (-not (Test-Path $value -PathType Leaf)) {
            Write-Host ""
            Write-Host "Ошибка: файл не найден: $value" -ForegroundColor Yellow
            Write-Host "Введите корректный путь к CSV-файлу или q для выхода."
            Write-Host ""
            continue
        }

        if ([System.IO.Path]::GetExtension($value).ToLower() -ne ".csv") {
            Write-Host ""
            Write-Host "Ошибка: для Simu5G нужен файл с расширением .csv: $value" -ForegroundColor Yellow
            Write-Host "Введите корректный путь к CSV-файлу или q для выхода."
            Write-Host ""
            continue
        }

        return $value
    }
}

function Read-SourceChoice {
    while ($true) {
        Write-Host ""
        Write-Host "NEWWAY Results Pipeline"
        Write-Host "========================"
        Write-Host ""
        Write-Host "Выберите источник данных:"
        Write-Host "1 — VaN3Twin / ns-3 CAM logs"
        Write-Host "2 — Simu5G / OMNeT++ scavetool CSV"
        Write-Host "q — выход"
        Write-Host ""

        $choice = Read-Host "Ваш выбор (1/2/q)"

        if ($choice -eq "1" -or $choice -eq "2") {
            return $choice
        }

        if ($choice -eq "q" -or $choice -eq "Q") {
            Write-Host "Выход без запуска pipeline."
            exit 0
        }

        Write-Host ""
        Write-Host "Ошибка: нужно выбрать 1, 2 или q." -ForegroundColor Yellow
    }
}

$choice = Read-SourceChoice

if ($choice -eq "1") {
    $source = "van3twin_ns3"
    $inputPath = Read-ExistingDirectory "Путь к папке с CAM CSV" ".\scripts\results_pipeline\sample_inputs\van3twin_cam"
    $outputPath = Read-WithDefault "Путь к выходной папке" ".\scripts\results_pipeline\sample_outputs\van3twin_cam_interactive"
    $scenario = Read-WithDefault "Scenario name" "van3twin_cam_interactive"
    $runId = Read-WithDefault "Run ID" "van3twin_cam_interactive_001"
}
elseif ($choice -eq "2") {
    $source = "simu5g"
    $inputPath = Read-ExistingCsvFile "Путь к scavetool CSV-файлу" ".\scripts\results_pipeline\sample_inputs\simu5g_scavetool\output_all_sample.csv"
    $outputPath = Read-WithDefault "Путь к выходной папке" ".\scripts\results_pipeline\sample_outputs\simu5g_scavetool_interactive"
    $scenario = Read-WithDefault "Scenario name" "simu5g_vector_interactive"
    $runId = Read-WithDefault "Run ID" "simu5g_vector_interactive_001"
}

Write-Host ""
Write-Host "Запуск pipeline..."
Write-Host "source:   $source"
Write-Host "input:    $inputPath"
Write-Host "output:   $outputPath"
Write-Host "scenario: $scenario"
Write-Host "run_id:   $runId"
Write-Host ""

python -m tools.results_pipeline.cli build `
    --source $source `
    --input $inputPath `
    --output $outputPath `
    --scenario $scenario `
    --run-id $runId

Write-Host ""
Write-Host "Готово." -ForegroundColor Green
Write-Host "Результаты записаны в: $outputPath"
Write-Host "Главный файл: normalized_metrics.csv"
Write-Host "Проверьте diagnostics.csv: если там только header, критических проблем не найдено."
