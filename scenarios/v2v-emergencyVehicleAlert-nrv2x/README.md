# v2v-emergencyVehicleAlert-nrv2x

NR-V2X Mode 2 сценарий с поведенческой реакцией на экстренное ТС (`changeLane` + `setMaxSpeed`).

- Исходник: `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc`
- Логика реакции на CAM/CPM: `src/automotive/model/Applications/emergencyVehicleAlert.cc`

## Что добавлено для исследования потерь

- `--rx-drop-prob-cam` и `--rx-drop-prob-cpm`:
  управляемый application-level fault injection для приема CAM/CPM.
- Логи управления `*-CTRL.csv`:
  фиксируют моменты и типы маневров (`lane0_slowdown` / `lane1_speedup`).

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

## Sweep baseline vs lossy

```bash
scenarios/v2v-emergencyVehicleAlert-nrv2x/run_loss_sweep.sh
```

По умолчанию sweep по `LOSS_PROBS="0.0 0.3 0.6"`.

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
