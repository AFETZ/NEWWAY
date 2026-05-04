# NEWWAY Results Pipeline — пользовательский комплект

Эта папка является пользовательской точкой входа в results pipeline проекта NEWWAY.

Пользователю не нужно изучать внутренние Python-модули, тесты или developer-документацию.
Рабочая схема простая:

1. Положить выходные файлы моделирования во входную папку.
2. Запустить интерактивный PowerShell-скрипт.
3. Выбрать источник данных.
4. Получить сформированные CSV-артефакты в выходной папке.

## Основной запуск

Рекомендуемый способ запуска для пользователя:

```powershell
.\scripts\results_pipeline\run.ps1
```

После запуска скрипт предложит выбрать источник данных:

```text
1 — VaN3Twin / ns-3 CAM logs
2 — Simu5G / OMNeT++ scavetool CSV
q — выход
```

Далее можно нажимать Enter, чтобы использовать sample inputs и sample outputs по умолчанию, либо ввести собственные пути.
Если пользователь вводит неправильный путь, скрипт не падает сразу, а просит ввести путь заново.

## Поддерживаемые входные данные

### VaN3Twin / ns-3 CAM logs

Ожидаемые входные файлы:

```text
test_1_p0005-veh1-CAM.csv
test_1_p0005-veh2-CAM.csv
```

Ожидаемые колонки:

```text
messageId,camId,timestamp,latitude,longitude,heading,speed,acceleration
```

Прямой запуск примера без интерактивного меню:

```powershell
.\scripts\results_pipeline\run_van3twin_cam.ps1
```

Запуск со своими путями:

```powershell
.\scripts\results_pipeline\run_van3twin_cam.ps1 `
  -InputPath ".\path\to\cam_csv_folder" `
  -OutputPath ".\path\to\output_folder" `
  -Scenario "my_van3twin_scenario" `
  -RunId "my_van3twin_run_001"
```

Выходные артефакты:

```text
normalized_events.csv
normalized_metrics.csv
aggregates_overall.csv
diagnostics.csv
run_metadata.json
run_metadata.yaml
```

Поддерживаемые CAM-метрики:

```text
cam_rx_count
speed_mps
acceleration_mps2
```

Важное ограничение: строгий PRR/PDR не считается только по CAM receiver logs.
Для строгого PRR/PDR нужен отдельный TX/generation log.

---

### Simu5G / OMNeT++ scavetool CSV

Ожидаемый входной файл:

```text
output_all.csv
```

Ожидаемые колонки:

```text
run,type,module,name,attrname,attrvalue,vectime,vecvalue
```

Прямой запуск примера без интерактивного меню:

```powershell
.\scripts\results_pipeline\run_simu5g.ps1
```

Запуск со своими путями:

```powershell
.\scripts\results_pipeline\run_simu5g.ps1 `
  -InputPath ".\path\to\output_all.csv" `
  -OutputPath ".\path\to\output_folder" `
  -Scenario "my_simu5g_scenario" `
  -RunId "my_simu5g_run_001"
```

Выходные артефакты:

```text
normalized_events.csv
normalized_metrics.csv
aggregates_by_metric.csv
aggregates_overall.csv
diagnostics.csv
run_metadata.json
run_metadata.yaml
```

Поддерживаемая нормализация vector-метрик:

```text
measuredSinrDl:vector -> sinr_db
measuredSinrUl:vector -> sinr_db
rcvdSinrDl:vector     -> sinr_db
rcvdSinrUl:vector     -> sinr_db
rcvdSinrD2D:vector    -> sinr_db
```

## Главный выходной файл

Центральный файл результата:

```text
normalized_metrics.csv
```

Это единый слой метрик для последующего анализа, отчётов, графиков и сравнения разных симуляторов.

## Проверка результата

После запуска нужно открыть:

```text
diagnostics.csv
```

Если в файле только header:

```text
issue_type,count,details,sample_ref
```

значит критических проблем при обработке не найдено.
