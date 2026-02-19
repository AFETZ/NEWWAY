# v2v-emergencyVehicleAlert-nrv2x

NR-V2X Mode 2 сценарий с поведенческой реакцией на экстренное ТС (`changeLane` + `setMaxSpeed`).

- Исходник: `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc`
- Логика реакции на CAM/CPM: `src/automotive/model/Applications/emergencyVehicleAlert.cc`

## Что добавлено для исследования потерь

- `--rx-drop-prob-cam` и `--rx-drop-prob-cpm`:
  управляемый application-level fault injection для приема CAM/CPM.
- Логи управления `*-CTRL.csv`:
  фиксируют моменты и типы маневров (`lane0_slowdown` / `lane1_speedup`).
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
- `EXPORT_RESULTS=0|1` — дублировать результаты в export-папку
- `EXPORT_ROOT` — корень export-папки (по умолчанию `analysis/scenario_runs/chatgpt_exports`)
- `EXPORT_INCLUDE_RAW_CSV=0|1` — включать все CSV (может быть много файлов)

## Sweep baseline vs lossy

```bash
scenarios/v2v-emergencyVehicleAlert-nrv2x/run_loss_sweep.sh
```

По умолчанию sweep по `LOSS_PROBS="0.0 0.3 0.6"`.
По умолчанию incident-mode включен через `INCIDENT_ARGS` в `run_loss_sweep.sh`.

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
- Графики сценария:
  - `figures/v2v-emergencyVehicleAlert-nrv2x/*.png`
- Для sweep:
  - `loss_sweep_summary.csv`
  - `loss_sweep_summary.png`
  - `loss_sweep_behavior_timing.png` (first/P90 control-action time, [s])
- Экспорт для загрузки в внешние инструменты:
  - `analysis/scenario_runs/chatgpt_exports/<run_path>/`
  - `EXPORT_MANIFEST.csv` внутри export-папки
