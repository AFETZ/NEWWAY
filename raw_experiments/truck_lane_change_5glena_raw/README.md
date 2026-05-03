# truck_lane_change_5glena_raw

Raw-only запуск фиксированного lane-change сценария.

## Цель

Получить только штатные артефакты симуляторов и приложения:

- официальный `5G-LENA / CTTC` `SQLite` DB;
- лог `ns-3 / 5G-LENA` из stdout/stderr;
- официальный `ms-van3t` `--csv-log` набор (`*-CAM/MSG/CTRL/PHY/PROFILE.csv`);
- `SUMO netstate.xml`;
- `SUMO collision.xml`.

Без:

- export-бандлов;
- аналитических Python-скриптов;
- графиков;
- производных CSV поверх штатных логов.

## Запуск

Из корня репозитория:

```bash
raw_experiments/truck_lane_change_5glena_raw/run.sh
```

По умолчанию сценарий идёт в headless-режиме и с `USE_SIONNA=0`,
то есть как raw `5G-LENA + SUMO` прогон без внешнего ray-tracing backend.

## Основные env overrides

- `OUT_DIR` — каталог raw-выходов
- `SIM_TAG` — префикс имени official `SQLite` DB
- `ENABLE_MSVAN3T_CSV=0|1` — включить/отключить штатные `ms-van3t` CSV (`1` по умолчанию)
- `SUMO_GUI=1` — включить GUI
- `USE_SIONNA=1` — вернуть Sionna
- `SIM_TIME=40`
- `TX_POWER_DBM=23`
- `EXTRA_RUN_ARGS="..."`
