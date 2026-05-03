# cpm_perception

Сценарий для сравнения:

1. `sensor_only` — только локальная реакция по сенсору (`sensor_reaction`), CPM-реакция выключена.
2. `sensor_good_cpm` — локальный сенсор + рабочий CPM канал.
3. `sensor_bad_cpm` — локальный сенсор + деградированный CPM канал у `veh4`.

Цель: показать, что cooperative perception через CPM расширяет горизонт восприятия и меняет исход.

По умолчанию используется конфигурация:

- `SUMO_CONFIG=src/automotive/examples/sumo_files_v2v_map/map_incident_threeflow_veh4lead.sumo.cfg`

В ней `veh4` является первым последователем за `veh2`, чтобы различие исходов было видно именно на `veh4`.

## Запуск

Сценарий работает только через Sionna.

Сначала в отдельном терминале поднять Sionna server:

```bash
cpm_perception/start_sionna_server.sh
```

Потом из корня репозитория запускать нужный режим.

Все три режима подряд:

```bash
cpm_perception/run.sh
```

Один режим за запуск:

```bash
MODE=sensor_only cpm_perception/run.sh
MODE=sensor_good_cpm cpm_perception/run.sh
MODE=sensor_bad_cpm cpm_perception/run.sh
```

Или через отдельные wrapper-скрипты:

```bash
cpm_perception/run_sensor_only.sh
cpm_perception/run_sensor_good_cpm.sh
cpm_perception/run_sensor_bad_cpm.sh
```

Если listener Sionna на `127.0.0.1:8103` не найден, сценарий завершается сразу с ошибкой до запуска ns-3/SUMO.

## Основные параметры

- `SENSOR_RANGE_M` (default `30`)
- `SENSOR_REACTION_DISTANCE_M` (default `10`)
- `SENSOR_REACTION_TTC_S` (default `1.0`)
- `CPM_REACTION_DISTANCE_M` (default `200`)
- `CPM_REACTION_TTC_S` (default `30.0`)
- `VEH4_BAD_CPM_DROP` (default `0.995`)
- `SUMO_CONFIG` (default `src/automotive/examples/sumo_files_v2v_map/map_incident_threeflow_veh4lead.sumo.cfg`)

## Выходные данные

Результаты по режимам:

- `$OUT_ROOT/sensor_only`
- `$OUT_ROOT/sensor_good_cpm`
- `$OUT_ROOT/sensor_bad_cpm`

Сводка:

- `$OUT_ROOT/summary/cpm_perception_mode_summary.csv`

При одиночном запуске сводка содержит только выбранный режим.

Ключевые поля сводки:

- наличие и время коллизии;
- время первого `sensor_reaction`, `cpm_reaction`, `cam_reaction` у `veh4`;
- число принятых/потерянных CPM у `veh4` (включая отдельный счетчик по `tx_id=3`).
