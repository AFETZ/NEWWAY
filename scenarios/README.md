# Scenarios

Этот каталог хранит "операционные" материалы по сценариям: как собрать, как запустить, куда смотреть артефакты.
Исходники самих сценариев остаются в стандартных местах `src/automotive/examples/` и `src/nr/examples/nr-v2x-examples/`.

## Быстрый старт

1. (Опционально) укажите уже подготовленное дерево `ns-3-dev`:

```bash
export NS3_DIR=/path/to/ns-3-dev
```

2. Запустите нужный сценарий:

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
- `NS3_USER_OVERRIDE` — имя пользователя для вызова `./ns3` при запуске из root-shell (по умолчанию `ns3`)

## Автоподготовка `ns-3-dev`

Теперь `run.sh` сценариев умеют автоматически поднимать локальное рабочее дерево `ns-3-dev`, если оно не найдено:
- проверяются пути:
  - `NS3_DIR` (если задан)
  - `<repo>/ns-3-dev`
  - `<repo>/.bootstrap-ns3/repo/ns-3-dev`
- если ничего не найдено, запускается bootstrap в `<repo>/.bootstrap-ns3`.
- после обнаружения дерева `ns-3-dev`, `run.sh` проверяет конфиг и при необходимости выполняет
  `./ns3 configure --enable-examples`, чтобы целевые сценарии были доступны для сборки.

Управляющие переменные:
- `AUTO_BOOTSTRAP_NS3=0|1` — включить/выключить авто-bootstrap (по умолчанию `1`)
- `NS3_BOOTSTRAP_FORCE=0|1` — пересоздавать bootstrap-destination (по умолчанию `0`)
- `NS3_BOOTSTRAP_COPY_SOURCE=0|1` — копировать текущий overlay (включая uncommitted изменения, без `.git`) в disposable bootstrap repo (по умолчанию `1`)

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
