# v2v-emergencyVehicleAlert-nrv2x

NR-V2X Mode 2 сценарий с поведенческой реакцией на экстренное ТС (`changeLane` + `setMaxSpeed`).

- Исходник: `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc`
- Логика реакции на CAM/CPM: `src/automotive/model/Applications/emergencyVehicleAlert.cc`

## Что добавлено для исследования потерь

- `--rx-drop-prob-cam` и `--rx-drop-prob-cpm`:
  управляемый application-level fault injection для приема CAM/CPM.
- `--rx-drop-prob-phy-cam` и `--rx-drop-prob-phy-cpm`:
  управляемый drop до приложения (в GeoNet, до учета `MetricSupervisor::signalReceivedPacket`),
  поэтому влияет на PRR как на канальном уровне.
- Логи управления `*-CTRL.csv`:
  фиксируют моменты и типы маневров (`lane0_slowdown` / `lane1_speedup`).
- В `*-MSG.csv` для PHY-level инжекции пишутся события `CAM_DROP_PHY` / `CPM_DROP_PHY`
  (это позволяет строить временные графики потерь не только для `CAM_DROP_APP`).
- Incident-mode для "сломавшегося" автомобиля:
  - `--incident-enable=1`
  - `--incident-vehicle-id=<vehX>`
  - `--incident-time-s=<t>`
  - `--incident-stop-duration-s=<sec>`
  - `--incident-recover-max-speed-mps=<v>` (отрицательное значение = восстановить исходную скорость)

## Запуск одного прогона

```bash
scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh
```

## Локальный запуск в Docker (Ubuntu + GPU)

Для быстрого развёртывания на чистой Ubuntu есть готовая обвязка:

```bash
scripts/docker-run-eva-sionna.sh
```

Для "одной команды" (установка Docker/toolkit + сборка + первый прогон):

```bash
scripts/quickstart-ubuntu-gpu.sh
```

Детальные шаги установки Docker/NVIDIA toolkit и дополнительные команды:
`docs/DOCKER_UBUNTU_GPU.md`.

По умолчанию:
- `--sumo-gui=0 --sim-time=40 --met-sup=1`
- включен `--netstate-dump-file` и анализ safety-прокси (`min gap`, `min TTC`, risky events)
- строятся графики

Полезные env-переменные:
- `RUN_ARGS` — доп. аргументы сценария
- `EXTRA_ARGS` — добавка к `RUN_ARGS`
- `CSV_PREFIX` — префикс CSV артефактов
- `NETSTATE_FILE` — путь к netstate XML
- `RISK_GAP_THRESHOLD`, `RISK_TTC_THRESHOLD` — пороги risky events
- `ENABLE_COLLISION_OUTPUT=0|1` — включить SUMO collision-output (`artifacts/eva-collision.xml`)
- `COLLISION_ACTION` — действие SUMO при collision (`warn`/`remove`/`teleport`)
- `EXPORT_RESULTS=0|1` — дублировать результаты в export-папку
- `EXPORT_ROOT` — корень export-папки (по умолчанию `analysis/scenario_runs/chatgpt_exports`)
- `EXPORT_INCLUDE_RAW_CSV=0|1` — включать все CSV (может быть много файлов)

## Sweep baseline vs lossy

```bash
scenarios/v2v-emergencyVehicleAlert-nrv2x/run_loss_sweep.sh
```

По умолчанию sweep по `LOSS_PROBS="0.0 0.3 0.6"`.
По умолчанию incident-mode включен через `INCIDENT_ARGS` в `run_loss_sweep.sh`.

Выбор слоя инжекции:
- `DROP_LAYER=app` (по умолчанию): использует `--rx-drop-prob-cam`
- `DROP_LAYER=phy`: использует `--rx-drop-prob-phy-cam`
- `DROP_LAYER=both`: использует оба

## Baseline vs lossy с общей тайм-линией

```bash
scenarios/v2v-emergencyVehicleAlert-nrv2x/run_baseline_vs_lossy_visual.sh
```

Скрипт:
- запускает baseline и lossy с одинаковым `RngRun`;
- строит сравнительный таймлайн:
  - `comparison/comparison_timeline.png`
  - `comparison/comparison_timeline.csv`
  - `comparison/comparison_summary.csv`
- `COMMON_EXTRA_ARGS` позволяет передать общие CLI-аргументы в оба прогона
  (например, `--sumo-config=/abs/path/aggressive.sumo.cfg`)
- для PHY-сценария доступны:
  - `BASE_DROP_PHY_CAM`, `LOSSY_DROP_PHY_CAM`
  - `BASE_DROP_PHY_CPM`, `LOSSY_DROP_PHY_CPM`

## RSSI -> safety sweep

```bash
scenarios/v2v-emergencyVehicleAlert-nrv2x/run_rssi_safety_sweep.sh
```

Для каждой точки `txPower` скрипт:
- запускает `v2v-cam-exchange-sionna-nrv2x` (без Sionna) и берет `RSSI/SNR/PRR`;
- запускает `v2v-emergencyVehicleAlert-nrv2x` и берет safety-метрики;
- строит:
  - `rssi_safety_summary.csv`
  - `rssi_safety_summary.png`
- `CAM_EXTRA_ARGS` / `EVA_EXTRA_ARGS` позволяют добавить общие аргументы для CAM/EVA прогонов

## Incident sweep c Sionna (terrain-aware channel)

```bash
scenarios/v2v-emergencyVehicleAlert-nrv2x/run_sionna_incident_sweep.sh
```

Скрипт:
- проверяет Python-зависимости `tensorflow/sionna/mitsuba/grpc`;
- поднимает локальный `sionna_v1_server_script.py`;
- запускает `v2v-emergencyVehicleAlert-nrv2x` с `--sionna=1` по сетке `TX_POWERS`;
- опционально добавляет контрольную ветку `non_sionna` (`COMPARE_NON_SIONNA=1`);
- строит:
  - `sionna_incident_summary.csv`
  - `sionna_incident_summary.png`

## Что сохраняется

- Лог: `analysis/scenario_runs/<date>/.../v2v-emergencyVehicleAlert-nrv2x.log`
- CSV по каждому ТС:
  - `*-CAM.csv`
  - `*-MSG.csv`
  - `*-CTRL.csv`
- Safety-прокси:
  - `artifacts/collision_risk/collision_risk_summary.csv`
  - `artifacts/collision_risk/collision_risk_timeseries.csv`
  - `artifacts/collision_risk/collision_risk_timeseries.png`
  - (опционально) `artifacts/eva-collision.xml` при `ENABLE_COLLISION_OUTPUT=1`
- Графики сценария:
  - `figures/v2v-emergencyVehicleAlert-nrv2x/*.png`
- Для sweep:
  - `loss_sweep_summary.csv`
  - `loss_sweep_summary.png`
  - `loss_sweep_behavior_timing.png` (first/P90 control-action time, [s])
- Экспорт для загрузки в внешние инструменты:
  - `analysis/scenario_runs/chatgpt_exports/<run_path>/`
  - `EXPORT_MANIFEST.csv` внутри export-папки
