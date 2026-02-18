# Scenarios

Этот каталог хранит "операционные" материалы по сценариям: как собрать, как запустить, куда смотреть артефакты.
Исходники самих сценариев остаются в стандартных местах `src/automotive/examples/` и `src/nr/examples/nr-v2x-examples/`.

## Быстрый старт

1. Подготовьте рабочее дерево `ns-3-dev` (bootstrap описан в `DEVELOPMENT.md`).
2. Укажите путь к нему:

```bash
export NS3_DIR=/path/to/ns-3-dev
```

3. Запустите нужный сценарий:

```bash
scenarios/cttc-nr-v2x-demo-simple/run.sh
scenarios/nr-v2x-west-to-east-highway/run.sh
scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh
scenarios/v2v-coexistence-80211p-nrv2x/run.sh
scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh
```

Общие переменные окружения:
- `NS3_DIR` — путь к `ns-3-dev`
- `OUT_DIR` — куда складывать лог/артефакты
- `PLOT=0|1` — строить ли графики после прогона (по умолчанию `1`)

Для сценария `v2v-emergencyVehicleAlert-nrv2x`:
- есть `run_loss_sweep.sh` для baseline/lossy sweep по `--rx-drop-prob-cam`
- автоматически считается safety-прокси из SUMO netstate (`min gap`, `min TTC`, risky events)

## Где результаты

- Логи и артефакты складываются в `analysis/scenario_runs/<YYYY-MM-DD>/`.
- Базы SQLite (`.db`) и CSV-артефакты попадают в `analysis/scenario_runs/<YYYY-MM-DD>/artifacts/`.
- После каждого `run.sh` автоматически строятся графики в `analysis/scenario_runs/<YYYY-MM-DD>/figures/`.

## Для исследовательских экспериментов

- Готовый список практических сценариев/модификаций для доказательства влияния потерь на поведение:
  `scenarios/RESEARCH_SCENARIOS.md`
