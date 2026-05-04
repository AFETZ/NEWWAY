# Input contract для VaN3Twin / ns-3

Документ описывает поддерживаемые входные форматы VaN3Twin/ns-3 для NEWWAY results pipeline.

## Поддерживаемый формат CAM receiver logs

Pipeline поддерживает директорию с CAM receiver CSV-файлами.

Ожидаемый шаблон имени файла:

```text
test_1_p0005-veh1-CAM.csv
test_1_p0005-veh2-CAM.csv
```

Receiver vehicle id извлекается из имени файла:

```text
veh1 -> dst_id = 1
veh2 -> dst_id = 2
```

Ожидаемые колонки:

```text
messageId,camId,timestamp,latitude,longitude,heading,speed,acceleration
```

Текущий mapping:

```text
camId        -> src_id
vehN         -> dst_id
timestamp    -> ts_us
speed        -> speed_mps
acceleration -> acceleration_mps2
```

Текущее предположение по времени:

```text
timestamp задаётся в миллисекундах
ts_us = timestamp * 1000
```

## Формируемые метрики

```text
cam_rx_count
speed_mps
acceleration_mps2
```

## Ограничения

Строгий PRR/PDR не считается только по CAM receiver logs.
Для строгого расчёта PRR/PDR нужен отдельный TX/generation log.

SINR/BLER не извлекаются из CAM logs.
Для них нужен отдельный PHY/radio-quality источник VaN3Twin/ns-3.

## Пример запуска

```powershell
python -m tools.results_pipeline.cli build `
  --source van3twin_ns3 `
  --input .\scripts\results_pipeline\sample_inputs\van3twin_cam `
  --output .\scripts\results_pipeline\sample_outputs\van3twin_cam `
  --scenario van3twin_cam_user_sample `
  --run-id van3twin_cam_user_sample_001
```
