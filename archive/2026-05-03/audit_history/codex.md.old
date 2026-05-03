# CODEx Guide for NEWWAY

Актуально для состояния репозитория на 2026-03-22.

## Что это за репозиторий

NEWWAY - это overlay поверх `ns-3-dev`, а не самодостаточный standalone-проект.

- Источник истины для правок: корень этого репозитория.
- Исполняемое disposable-дерево для запуска: `.bootstrap-ns3/repo/ns-3-dev`.
- Большинство `run.sh` не требуют вручную искать `ns-3-dev`: они вызывают `scripts/ensure-ns3-dev.sh`, а затем синхронизируют overlay через `scripts/sync-overlay-into-bootstrap-ns3.sh`.
- Если `ns-3-dev` не найден, скрипты могут автоматически поднять локальную disposable-копию.

Практическое правило:

- Редактируй код и документацию в корне репозитория.
- Не редактируй `.bootstrap-ns3/repo/ns-3-dev` как primary source, если задача не про отладку bootstrap-механики.

## Безопасные границы правок

По умолчанию не трогай эти пути:

- `.bootstrap-ns3/`
- `analysis/scenario_runs/`
- `analysis/scenario_runs/chatgpt_exports/`
- `$HOME/NEWWAY_runs/`
- `src/vehicle-visualizer/js/node_modules/`
- любые уже сгенерированные `artifacts/`, `figures/`, `visualizations/`, export-бандлы и копии run-артефактов

Исключение только одно: задача явно относится к generated outputs, воспроизведению старого прогона или обслуживанию кэша/bootstrap-дерева.

Дополнительно:

- Репозиторий может быть грязным. Не откатывай несвязанные пользовательские изменения.
- Если в файлах, которые ты трогаешь, уже есть локальные правки, сначала прочитай их и встройся в текущее состояние, а не переписывай его.
- Для запуска сценариев предпочитай repo-level `run.sh`, а не сырой `./ns3 run`, потому что обвязка уже умеет bootstrap, configure, sync overlay, retries, export и plotting.

## Окружение и сборка

### Основные каталоги и окружения

- `./.venv` - основное Python-окружение для analysis/plotting/Streamlit.
- `./.venv_sionna` - отдельное окружение под Sionna/TensorFlow-стек.
- `.bootstrap-ns3/repo/ns-3-dev` - локальное disposable `ns-3-dev`, уже найденное в этом дереве.

### Базовый bootstrap

Из корня репозитория:

```bash
printf '\n' | ./sandbox_builder.sh
```

Вариант для первой установки зависимостей:

```bash
printf '\n' | ./sandbox_builder.sh install-dependencies
```

### Конфигурация `ns-3`

Если работаешь руками внутри `ns-3-dev`:

```bash
cd .bootstrap-ns3/repo/ns-3-dev
./ns3 configure --build-profile=optimized --enable-examples --enable-tests --disable-python --disable-werror
```

Но в обычном случае вручную это не нужно: `run.sh` сам проверит конфиг и при необходимости выполнит `./ns3 configure`.

### Сборка

Пример минимальной ручной сборки:

```bash
cd .bootstrap-ns3/repo/ns-3-dev
./ns3 build -j 2 v2v-simple-cam-exchange-80211p
```

### Тесты

Для `ns-3`-дерева не используй `./ns3 test`. Здесь нужен `test.py`:

```bash
cd .bootstrap-ns3/repo/ns-3-dev
./test.py --list
./test.py --no-build --suite=<suite-name>
```

### Root-shell запуск

Если сценарий запускается из root-shell, repo-level wrappers умеют использовать:

- `NS3_USER_OVERRIDE`

Пример:

```bash
NS3_USER_OVERRIDE=ns3 scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh
```

## Auto-bootstrap и sync overlay

### `scripts/ensure-ns3-dev.sh`

Скрипт проверяет по порядку:

1. `NS3_DIR`
2. `<repo>/ns-3-dev`
3. `<repo>/.bootstrap-ns3/repo/ns-3-dev`

Если валидное дерево не найдено, при `AUTO_BOOTSTRAP_NS3=1` поднимается disposable bootstrap-репозиторий.

### `scripts/sync-overlay-into-bootstrap-ns3.sh`

Если используется именно disposable bootstrap tree, скрипт синхронизирует:

- `src/`
- top-level helper scripts `switch_ms-van3t-interference.sh`, `switch_ms-van3t-CARLA.sh`, `enable_v2x_emulator.sh`

Это нужно, чтобы локальные правки overlay попадали в запускаемый `ns-3-dev`.

Полезные env-переменные:

- `AUTO_BOOTSTRAP_NS3=0|1`
- `NS3_BOOTSTRAP_FORCE=0|1`
- `NS3_BOOTSTRAP_COPY_SOURCE=0|1`
- `NS3_SYNC_OVERLAY=0|1`
- `NS3_DIR=/path/to/ns-3-dev`

## Карта репозитория

### Основные зоны

- `src/` - исходники модулей `automotive`, `nr`, `cv2x`, `sionna`, `traci`, `vehicle-visualizer`
- `scenarios/` - operational wrappers для запуска и воспроизводимых сценариев
- `valid_*` - фиксированные дипломные/валидированные кейсы
- `my_scenarios/` - пользовательские/дипломные композиции и матричные сценарии
- `analysis/` - аналитика, plotting, отчёты, выгрузки для ВКР
- `tools/scenario_manager/` - Streamlit UI для запуска и просмотра результатов
- `tools/results_pipeline/` - CSV-first normalized pipeline
- `tests/` - smoke/unit tests для tooling
- `docs/` - дополнительная документация

### Что обычно запускать, а что редактировать

- Если задача про исследовательский прогон: смотри `scenarios/`, `valid_*`, `my_scenarios/`
- Если задача про графики и постобработку: смотри `analysis/` и `tools/scenario_manager/visualizer.py`
- Если задача про поведение аварийного ТС и связь drop -> decision -> collision: смотри `src/automotive/model/Applications/emergencyVehicleAlert.*`

## Точки входа сценариев

Ниже перечислены рекомендуемые команды запуска из корня репозитория.

| Команда | Что делает | Режим Sionna | Куда пишет по умолчанию |
| --- | --- | --- | --- |
| `bash tools/scenario_manager/launch.sh` | Streamlit UI для запуска и просмотра прогонов | UI сам вызывает сценарии; зависит от выбранного сценария | `analysis/scenario_runs/<date>/...` |
| `scenarios/cttc-nr-v2x-demo-simple/run.sh` | CTTC demo на NR-V2X | без Sionna | `analysis/scenario_runs/<date>/` |
| `scenarios/nr-v2x-west-to-east-highway/run.sh` | highway NR-V2X сценарий | без Sionna | `analysis/scenario_runs/<date>/` |
| `scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh` | CAM exchange, опциональный Sionna backend | опционально; режим задаётся аргументами сценария | `analysis/scenario_runs/<date>/` |
| `scenarios/v2v-coexistence-80211p-nrv2x/run.sh` | coexistence 802.11p + NR-V2X | без Sionna, но с interference-mode | `analysis/scenario_runs/<date>/` |
| `scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh` | основной EVA сценарий с CSV/PRR/control/safety артефактами | нейтральный wrapper; `--sionna=1/0` передаётся через `RUN_ARGS` | `analysis/scenario_runs/<date>/` |
| `scenarios/5g-phy-metrics/run.sh` | эксперимент по PHY-метрикам 5G NR-V2X | `USE_SIONNA=0` по умолчанию, `1` поддерживается | `$HOME/NEWWAY_runs/<date>/5g-phy-metrics` |
| `valid_scenario/run.sh` | фиксированный thesis-ready lane-change кейс | `USE_SIONNA=1` по умолчанию, `USE_SIONNA=0` поддерживается | `$HOME/NEWWAY_runs/<date>/valid_scenario` |
| `valid_intersection_scenario/run.sh` | фиксированный priority-intersection кейс | `USE_SIONNA=1` по умолчанию, `USE_SIONNA=0` поддерживается | `$HOME/NEWWAY_runs/<date>/valid_intersection_scenario` |
| `valid_cpm_perception_scenario/run.sh` | `sensor_only` / `sensor_good_cpm` / `sensor_bad_cpm` | только Sionna | `$HOME/NEWWAY_runs/<date>/valid_cpm_perception_scenario` |
| `valid_intersection_radar_comm_scenario/run.sh` | `radar_bad_link` / `radar_only` / `radar_good_link` | только Sionna | `$HOME/NEWWAY_runs/<date>/valid_intersection_radar_comm_scenario` |
| `my_scenarios/compare_tech/run.sh` | матричное сравнение `80211p`, `ltev2x`, `nrv2x` на `truck` и `intersection` | текущая реализация гоняет `nrv2x` с `--sionna=0` | `$HOME/NEWWAY_runs/<date>/compare_tech` |

## Быстрые команды запуска

### Scenario Manager UI

```bash
bash tools/scenario_manager/launch.sh
```

После старта открыть:

```text
http://localhost:8501
```

UI умеет:

- запускать сценарии из `tools/scenario_manager/scenarios.py`
- читать готовые run-директории
- генерировать `visualizations/<case>/...` из уже существующих `artifacts/`

### Базовые operational сценарии

```bash
scenarios/cttc-nr-v2x-demo-simple/run.sh
scenarios/nr-v2x-west-to-east-highway/run.sh
scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh
scenarios/v2v-coexistence-80211p-nrv2x/run.sh
scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh
scenarios/5g-phy-metrics/run.sh
```

### Валидированные thesis-ready сценарии

```bash
valid_scenario/run.sh
valid_intersection_scenario/run.sh
valid_cpm_perception_scenario/run.sh
valid_intersection_radar_comm_scenario/run.sh
```

### Матрица по технологиям

```bash
my_scenarios/compare_tech/run.sh
```

## Sionna режимы

### Сценарии с fallback `USE_SIONNA=0`

- `valid_scenario/run.sh`
- `valid_intersection_scenario/run.sh`
- `scenarios/5g-phy-metrics/run.sh`

Примеры:

```bash
USE_SIONNA=0 valid_scenario/run.sh
USE_SIONNA=0 valid_intersection_scenario/run.sh
USE_SIONNA=0 scenarios/5g-phy-metrics/run.sh
```

### Сценарии с `USE_SIONNA=1` по умолчанию

- `valid_scenario/run.sh`
- `valid_intersection_scenario/run.sh`

У обоих сценариев есть auto-start/wait логика для локального listener-а, но успешность зависит от наличия рабочего Sionna server script и Python/Sionna stack.

### Sionna-only сценарии

- `valid_cpm_perception_scenario/run.sh`
- `valid_intersection_radar_comm_scenario/run.sh`

Они завершаются ошибкой, если `USE_SIONNA != 1` или listener не найден.

### Wrapper-режим без отдельной `USE_SIONNA` переменной

- `scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh`

Этот скрипт сам по себе нейтрален: режим Sionna задаётся через `RUN_ARGS`, например:

```bash
RUN_ARGS="--sumo-gui=0 --sim-time=40 --met-sup=1 --sionna=0" \
scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh
```

### Опциональный Sionna backend

- `scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh`
- `scenarios/v2v-cam-exchange-sionna-nrv2x/run_compare_backends.sh`

README для этого сценария прямо описывает backend comparison `non-Sionna vs Sionna`.

## Куда складываются результаты

### Repo-local runs

Обычно это operational сценарии из `scenarios/` и UI-driven прогоны.

Типичный шаблон:

```text
analysis/scenario_runs/<YYYY-MM-DD>/
analysis/scenario_runs/<YYYY-MM-DD>/<scenario-id-or-run-name>/
```

Обычно внутри:

- `*.log`
- `artifacts/`
- `figures/`
- иногда `visualizations/`
- иногда summary CSV/PNG на уровне run-root

### Fixed-scenario runs

`valid_*` и `my_scenarios/compare_tech` чаще по умолчанию пишут в домашний каталог:

```text
$HOME/NEWWAY_runs/<YYYY-MM-DD>/...
```

Типичные примеры:

- `$HOME/NEWWAY_runs/<date>/valid_scenario`
- `$HOME/NEWWAY_runs/<date>/valid_intersection_scenario`
- `$HOME/NEWWAY_runs/<date>/valid_cpm_perception_scenario`
- `$HOME/NEWWAY_runs/<date>/valid_intersection_radar_comm_scenario`
- `$HOME/NEWWAY_runs/<date>/compare_tech`
- `$HOME/NEWWAY_runs/<date>/5g-phy-metrics`

### Принудительное переназначение

Почти все wrappers поддерживают `OUT_DIR` или `OUT_ROOT`.

Пример:

```bash
OUT_DIR="$PWD/analysis/scenario_runs/$(date +%F)/manual-valid-scenario" valid_scenario/run.sh
```

## Как получить графики автоматически

### Через `PLOT=1`

Для многих `run.sh` plotting включен по умолчанию:

- `scenarios/cttc-nr-v2x-demo-simple/run.sh`
- `scenarios/nr-v2x-west-to-east-highway/run.sh`
- `scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh`
- `scenarios/v2v-coexistence-80211p-nrv2x/run.sh`
- `scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh`
- `scenarios/5g-phy-metrics/run.sh`

Если внутри конкретного wrapper-а `PLOT=0` по умолчанию, его можно включить явно:

```bash
PLOT=1 valid_scenario/run.sh
PLOT=1 valid_intersection_scenario/run.sh
```

### Автоматические графики, которые уже умеют строиться

- `analysis/scenario_runs/make_plots.py` строит scenario-specific PNG в `figures/<scenario>/`
- `valid_scenario/run.sh` дополнительно вызывает:
  - `analysis/scenario_runs/build_valid_scenario_story_plots.py`
  - `analysis/scenario_runs/build_valid_scenario_intuitive_plots.py`
- `scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh` при `PHY_ANALYSIS=1` вызывает:
  - `analysis/analyze_phy_safety.py`
- `scenarios/5g-phy-metrics/run.sh` вызывает:
  - `analysis/plot_5g_phy_metrics.py`

### Через Scenario Manager UI

UI умеет сгенерировать и сохранить в существующий `run_dir`:

- `visualizations/<case>/network_kpi_dashboard.png`
- `visualizations/<case>/behavioral_dashboard.png`
- `visualizations/<case>/transport_safety_dashboard.png`
- `visualizations/<case>/cross_layer_causal_chain.png`
- `visualizations/<case>/vehicle_profiles.png`
- при наличии данных - packet raster и интерактивные Plotly views

Это особенно удобно, если сценарий был запущен с `PLOT=0`, но `artifacts/` сохранились.

## Как пересобрать графики вручную

### 1. Универсальные scenario-specific графики из `artifacts/`

```bash
./.venv/bin/python analysis/scenario_runs/make_plots.py \
  --run-dir analysis/scenario_runs/<YYYY-MM-DD>/<run_dir> \
  --scenario <name|all>
```

Поддерживаемые значения `--scenario`:

- `cttc-nr-v2x-demo-simple`
- `nr-v2x-west-to-east-highway`
- `v2v-cam-exchange-sionna-nrv2x`
- `v2v-coexistence-80211p-nrv2x`
- `v2v-emergencyVehicleAlert-nrv2x`
- `all`

### 2. PHY-safety графики для EVA: SINR / SNR / RSSI / RSRP

Это основной ручной рецепт для графиков уровня signal-to-noise ratio.

```bash
./.venv/bin/python analysis/analyze_phy_safety.py \
  --run-dir analysis/scenario_runs/<YYYY-MM-DD>/<run_dir> \
  --out-dir analysis/scenario_runs/<YYYY-MM-DD>/<run_dir>/artifacts/phy_analysis
```

Ищет `*-PHY.csv` внутри `artifacts/` и строит:

- `phy_sinr_histogram.png`
- `phy_sinr_vs_distance.png`
- `phy_sinr_timeline.png`
- `phy_sinr_cdf.png`
- `phy_four_metrics.png`
- `phy_distance_reception.png`

Если нужный прогон лежит в `$HOME/NEWWAY_runs/...`, просто подставь этот путь в `--run-dir`.

### 3. 5G PHY metrics plots

Для сценария `scenarios/5g-phy-metrics/run.sh` префикс CSV обычно такой:

```text
$HOME/NEWWAY_runs/<date>/5g-phy-metrics/artifacts/phy-metrics
```

Ручной запуск:

```bash
./.venv/bin/python analysis/plot_5g_phy_metrics.py \
  --prefix "$HOME/NEWWAY_runs/<YYYY-MM-DD>/5g-phy-metrics/artifacts/phy-metrics" \
  --out-dir "$HOME/NEWWAY_runs/<YYYY-MM-DD>/5g-phy-metrics/plots"
```

Скрипт строит:

- `sinr_distribution.png`
- `tbler_vs_sinr.png`
- `mcs_usage.png`
- `tb_size_distribution.png`
- `prr_per_node.png`
- `corruption_over_time.png`
- `pscch_stats.png`

### 4. Story-графики для `valid_scenario`

```bash
./.venv/bin/python analysis/scenario_runs/build_valid_scenario_story_plots.py \
  --run-dir "$HOME/NEWWAY_runs/<YYYY-MM-DD>/valid_scenario" \
  --out-dir "$HOME/NEWWAY_runs/<YYYY-MM-DD>/valid_scenario/artifacts/valid_scenario_story"
```

### 5. Интуитивные CSV-only графики для `valid_scenario`

```bash
./.venv/bin/python analysis/scenario_runs/build_valid_scenario_intuitive_plots.py \
  --run-dir "$HOME/NEWWAY_runs/<YYYY-MM-DD>/valid_scenario" \
  --out-dir "$HOME/NEWWAY_runs/<YYYY-MM-DD>/valid_scenario/artifacts/valid_scenario_intuitive"
```

### 6. Drop -> decision timeline вручную

```bash
./.venv/bin/python analysis/scenario_runs/build_drop_decision_timeline.py \
  --run-dir analysis/scenario_runs/<YYYY-MM-DD>/<run_dir>
```

## Практический маршрут: как быстро получить SINR/SNR/RSSI графики

### Вариант A. Уже есть готовый EVA-прогон

1. Найди run-директорию, внутри которой есть `artifacts/eva-veh*-PHY.csv`
2. Запусти:

```bash
./.venv/bin/python analysis/analyze_phy_safety.py \
  --run-dir <run_dir> \
  --out-dir <run_dir>/artifacts/phy_analysis
```

3. Смотри:

- `<run_dir>/artifacts/phy_analysis/phy_sinr_histogram.png`
- `<run_dir>/artifacts/phy_analysis/phy_four_metrics.png`
- `<run_dir>/artifacts/phy_analysis/phy_sinr_cdf.png`

### Вариант B. Нужно сначала получить прогон

Пример для EVA:

```bash
PLOT=1 PHY_ANALYSIS=1 scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh
```

После завершения смотри:

- `analysis/scenario_runs/<date>/artifacts/phy_analysis/`
- `analysis/scenario_runs/<date>/figures/v2v-emergencyVehicleAlert-nrv2x/`

### Вариант C. Нужен чисто PHY-focused experiment

```bash
scenarios/5g-phy-metrics/run.sh
```

После завершения смотри:

- `$HOME/NEWWAY_runs/<date>/5g-phy-metrics/plots/`

## Output map

### `artifacts/`

Сырые и полуобработанные результаты конкретного прогона:

- CSV по машинам: `*-CAM.csv`, `*-MSG.csv`, `*-CTRL.csv`, `*-PROFILE.csv`, иногда `*-PHY.csv`
- `eva-netstate.xml`
- `eva-collision.xml`
- SQLite/DB файлы у некоторых сценариев
- summary CSV у фиксированных сценариев

### `figures/`

PNG, построенные `analysis/scenario_runs/make_plots.py` и related plotters.

Типично:

- `figures/<scenario>/*.png`
- `figures/manifest.csv`

### `visualizations/`

Дополнительные dashboard-ы, которые генерирует Scenario Manager из уже существующих `artifacts/`.

Типично:

- `visualizations/<case>/network_kpi_dashboard.png`
- `visualizations/<case>/behavioral_dashboard.png`
- `visualizations/<case>/transport_safety_dashboard.png`
- `visualizations/<case>/cross_layer_causal_chain.png`
- `visualizations/<case>/vehicle_profiles.png`

### `drop_decision_timeline/`

ID-aware связка `DROP_PHY -> DECISION`.

Типично:

- `event_timeline.csv`
- `summary.csv`
- `decision_delay_scatter.png`
- `decision_type_counts.png`

### `collision_risk/`

Safety-прокси из `netstate`.

Типично:

- `collision_risk_summary.csv`
- `collision_risk_timeseries.csv`
- `collision_risk_timeseries.png`

### `collision_causality/`

Причинный отчёт вокруг collision.

Типично:

- `collision_causality.csv`
- `collision_causality.md`

### `valid_scenario_story/`

Дипломные story-графики для `valid_scenario`.

Типично:

- `speed_lane_timeseries.png`
- `gap_ttc_timeseries.png`
- `ns3_events_per_second.png`
- `event_chain_timeline.png`
- `event_chain.csv`

### `valid_scenario_intuitive/`

CSV-only графики и summary для `valid_scenario`.

Типично:

- `intuitive_prr_summary.csv`
- `intuitive_prr_cumulative.png`
- `intuitive_packet_raster.png`
- `intuitive_truck_speed_observed.png`
- `intuitive_dbm_prr_maneuver_chain.csv`
- `intuitive_dbm_prr_maneuver_chain.png`

### `phy_analysis/`

PHY-safety correlation outputs из `analysis/analyze_phy_safety.py`.

Типично:

- `phy_sinr_histogram.png`
- `phy_sinr_vs_distance.png`
- `phy_sinr_timeline.png`
- `phy_sinr_cdf.png`
- `phy_four_metrics.png`
- `phy_distance_reception.png`

### `plots/`

Используется, например, сценарием `scenarios/5g-phy-metrics/run.sh`.

Типично:

- `sinr_distribution.png`
- `tbler_vs_sinr.png`
- `mcs_usage.png`
- `prr_per_node.png`

## Troubleshooting

### `./ns3: No such file or directory`

Причина:

- нет готового `ns-3-dev`
- `NS3_DIR` указывает не туда

Что делать:

```bash
scripts/ensure-ns3-dev.sh --root "$PWD"
```

Или просто повторно запусти repo-level `run.sh`, который поднимет bootstrap-дерево сам.

### Не найден Sionna listener

Симптом:

- сценарий завершает работу до запуска `ns-3`

Что делать:

- подними соответствующий `start_sionna_server.sh`
- проверь порт `8103`
- используй правильное Python-окружение для Sionna

Примеры:

```bash
valid_scenario/start_sionna_server.sh
valid_intersection_scenario/start_sionna_server.sh
valid_cpm_perception_scenario/start_sionna_server.sh
valid_intersection_radar_comm_scenario/start_sionna_server.sh
```

### Ложный negative от `ss`

Некоторые README уже отмечают, что в отдельных окружениях `ss` может вести себя нестабильно.

Практика:

- ориентируйся не только на preflight-check, но и на лог сценария
- для intersection-кейса ищи строку вида `SUCCESS! ns-3 is now locally connected to Sionna`

### Нет `*-PHY.csv`, поэтому не строятся SINR/SNR/RSSI графики

Симптом:

- `analysis/analyze_phy_safety.py` пишет `No PHY CSV files found`

Причина:

- текущий сценарий не пишет PHY CSV
- или прогон был не тем wrapper-ом

Что делать:

- используй EVA-прогон, который сохраняет `*-PHY.csv`
- или `scenarios/5g-phy-metrics/run.sh`
- проверь фактическое содержимое `artifacts/`

### OUT_DIR не создаётся

`scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh` умеет fallback в:

```text
$HOME/NEWWAY_runs/<YYYY-MM-DD>/...
```

Если путь неожиданно сменился, проверь права на исходный `OUT_DIR` и лог запуска.

### Нет графиков, хотя сценарий отработал

Проверь по порядку:

1. был ли `PLOT=1`
2. есть ли входные `artifacts/*`
3. доступен ли `./.venv/bin/python`
4. можно ли вручную вызвать `analysis/scenario_runs/make_plots.py`
5. можно ли сгенерировать dashboard-ы через `bash tools/scenario_manager/launch.sh`

## Быстрый чек-лист для Codex

- Всегда сначала ищи repo-level wrapper в `scenarios/`, `valid_*` или `my_scenarios/`.
- Не запускай сырой `./ns3 run`, если ту же задачу уже покрывает `run.sh`.
- Не редактируй `.bootstrap-ns3`, `analysis/scenario_runs`, export-бандлы и `node_modules`, если задача не требует этого напрямую.
- После сценарных изменений проверяй не только код, но и артефакты: `artifacts/`, `figures/`, `visualizations/`, summary CSV/PNG.
- Для EVA-кейсов отдельно проверяй цепочку `DROP_PHY -> DECISION -> collision/no collision`.
- Если добавляешь новый сценарий или новый plotter, обновляй этот runbook сразу, пока команда запуска и output map свежи.
