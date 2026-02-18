# v2v-cam-exchange-sionna-nrv2x

SUMO-сценарий обмена CAM для NR-V2X с опциональной интеграцией Sionna.

- Исходник: `src/automotive/examples/v2v-cam-exchange-sionna-nrv2x.cc`
- Ключевые строки: `:89`, `:116`, `:181`, `:538`

## Запуск

```bash
scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh
```

По умолчанию сценарий запускается с `--sumo-gui=0 --sim-time=20`.

## Сравнение backends (non-Sionna vs Sionna)

```bash
scenarios/v2v-cam-exchange-sionna-nrv2x/run_compare_backends.sh
```

Что делает скрипт:
- запускает baseline без Sionna;
- при наличии `tensorflow+sionna+mitsuba` поднимает локальный Sionna server и запускает Sionna-вариант;
- сохраняет сравнение в:
  - `.../backend_compare_summary.csv`
  - `.../backend_compare_summary.png`

## Что сохраняется

- Лог: `analysis/scenario_runs/<date>/v2v-cam-exchange-sionna-nrv2x.log`
- Артефакты:
  - `analysis/scenario_runs/<date>/artifacts/v2v-cam-exchange-sionna-nrv2x_output.txt`
  - `analysis/scenario_runs/<date>/artifacts/phy_with_sionna_nrv2x.csv`
  - `analysis/scenario_runs/<date>/artifacts/prr_with_sionna_nrv2x.csv`
- Графики: `analysis/scenario_runs/<date>/figures/v2v-cam-exchange-sionna-nrv2x/*.png`
