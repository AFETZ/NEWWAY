# Манифест исходных артефактов

## 1. Базовые документы и точки входа

| Категория | Путь | Роль в отчете |
|---|---|---|
| Главный обзор проекта | `README.md` | общая архитектура, установка, ограничения, основные подсистемы |
| Developer bootstrap | `DEVELOPMENT.md` | практический workflow установки, configure, build, test |
| Карта сценариев | `scenarios/README.md` | основные launchers, env-переменные, output-пути |
| Пользовательские сценарии | `my_scenarios/README.md` | фиксированные дипломные и исследовательские wrapper-сценарии |
| Raw-эксперименты | `raw_experiments/README.md` | режим raw-only без постобработки |
| Results pipeline | `docs/results_schema.md` | схема outputs pipeline и нормализованные поля |
| Аналитика прогонов | `analysis/scenario_runs/README.md` | scripts, export, plots, audit |

## 2. Основные сценарные README и launchers

| Путь | Назначение |
|---|---|
| `scenarios/cttc-nr-v2x-demo-simple/README.md` | минимальный NR sidelink кейс |
| `scenarios/nr-v2x-west-to-east-highway/README.md` | highway-сценарий с KPI в SQLite |
| `scenarios/v2v-cam-exchange-sionna-nrv2x/README.md` | CAM exchange с optional Sionna |
| `scenarios/v2v-coexistence-80211p-nrv2x/README.md` | coexistence 802.11p и NR-V2X |
| `scenarios/v2v-emergencyVehicleAlert-nrv2x/README.md` | основной scenario `loss -> decision -> behavior` |
| `valid_scenario/README.md` | валидированный lane-change кейс |
| `valid_intersection_scenario/README.md` | валидированный junction crash кейс |
| `valid_cpm_perception_scenario/README.md` | sensor vs CPM |
| `valid_intersection_radar_comm_scenario/README.md` | radar + V2X intersection |
| `my_scenarios/truck_lane_change_scenario/README.md` | упакованный пользовательский lane-change кейс |
| `my_scenarios/intersection_crash_scenario/README.md` | упакованный пользовательский intersection кейс |
| `my_scenarios/compare_tech/README.md` | сравнение технологий |
| `my_scenarios/cpm_perception_scenario/README.md` | wrapper для CPM perception |
| `my_scenarios/intersection_radar_comm_scenario/README.md` | wrapper для radar/comm |
| `raw_experiments/truck_lane_change_5glena_raw/README.md` | raw-only 5G-LENA кейс |

## 3. Подтвержденные summary CSV

| Исходный путь | Локальная копия | Назначение |
|---|---|---|
| `my_scenarios/truck_lane_change_scenario/output/intuitive_prr_summary.csv` | `evidence/csv/lane_change/intuitive_prr_summary.csv` | итоговый PRR и исходы по ключевым авто |
| `my_scenarios/truck_lane_change_scenario/output/intuitive_dbm_prr_maneuver_chain.csv` | `evidence/csv/lane_change/intuitive_dbm_prr_maneuver_chain.csv` | цепочка `dBm -> PRR -> решение -> исход` |
| `my_scenarios/truck_lane_change_scenario/output/intuitive_key_events.csv` | `evidence/csv/lane_change/intuitive_key_events.csv` | ключевые времена инцидента, lane change и collision |
| `my_scenarios/truck_lane_change_scenario/output/drop_decision_summary.csv` | `evidence/csv/lane_change/drop_decision_summary.csv` | strict match по `DROP_PHY -> DECISION` |
| `my_scenarios/truck_lane_change_scenario/output/collision_causality.csv` | `evidence/csv/lane_change/collision_causality.csv` | strongest causal window `loss -> no_action -> collision` для lane-change кейса |
| `my_scenarios/truck_lane_change_scenario/output/collision_risk_summary.csv` | `evidence/csv/lane_change/collision_risk_summary.csv` | safety summary для lane-change кейса |
| `my_scenarios/intersection_crash_scenario/output/intersection_summary.csv` | `evidence/csv/intersection/intersection_summary.csv` | компактная сводка junction кейса |
| `my_scenarios/intersection_crash_scenario/output/drop_decision_summary.csv` | `evidence/csv/intersection/drop_decision_summary.csv` | strict match по junction кейсу |
| `my_scenarios/intersection_crash_scenario/output/collision_causality.csv` | `evidence/csv/intersection/collision_causality.csv` | strongest causal window `loss -> no_action -> collision` для junction кейса |
| `my_scenarios/intersection_crash_scenario/output/collision_risk_summary.csv` | `evidence/csv/intersection/collision_risk_summary.csv` | вспомогательный safety summary для junction кейса; `min_gap/min_ttc` в данном run-е заполнены не полностью |
| `analysis/scenario_runs/chatgpt_exports/2026-02-19/rssi-safety-tx23-vs-5-181716/rssi_safety_summary.csv` | `evidence/csv/sweeps/rssi_safety_summary.csv` | RSSI/SNR/PRR/latency sweep |
| `analysis/scenario_runs/chatgpt_exports/2026-02-20/eva-short-sionna-gpu-only-tx23-223837/sionna_incident_summary.csv` | `evidence/csv/sweeps/sionna_incident_summary_success.csv` | успешный Sionna incident sweep |
| `analysis/scenario_runs/chatgpt_exports/2026-02-20/eva-non-sionna-then-sionna-gpu-184930/sionna_incident_summary.csv` | `evidence/csv/sweeps/sionna_incident_summary_zero_attempt.csv` | пример промежуточной/неудачной попытки |

Практически важная оговорка по силе доказательства:

- для `lane-change` и `intersection` strongest evidence — это связка
  `summary + drop_decision_summary + collision_causality`;
- `collision_risk_summary` полезен как дополняющий слой, но для junction-кейса
  не должен использоваться как единственная опора для количественного вывода.

## 3a. Дополнительный EVA-блок из `cycle7_fizulin_av`

| Исходный путь | Локальная копия | Назначение |
|---|---|---|
| `cycle7_fizulin_av/summary-all-runs.csv` | `evidence/csv/eva_series/summary-all-runs.csv` | сводка по 6 прогонам EVA-серии |
| `cycle7_fizulin_av/per-vehicle-cam-from-ev.csv` | `evidence/csv/eva_series/per-vehicle-cam-from-ev.csv` | распределение числа CAM от emergency vehicle по автомобилям |
| `cycle7_fizulin_av/inter-cam-gaps.csv` | `evidence/csv/eva_series/inter-cam-gaps.csv` | интервалы между соседними CAM от emergency vehicle |
| `cycle7_fizulin_av/eva-good-speed-timeseries.csv` | `evidence/csv/eva_series/eva-good-speed-timeseries.csv` | baseline speed/lane timeseries |
| `cycle7_fizulin_av/eva-bad-speed-timeseries.csv` | `evidence/csv/eva_series/eva-bad-speed-timeseries.csv` | high-loss speed/lane timeseries |
| `cycle7_fizulin_av/eva-vbad-speed-timeseries.csv` | `evidence/csv/eva_series/eva-vbad-speed-timeseries.csv` | very-high-loss speed/lane timeseries |
| `cycle7_fizulin_av/eva-lowpen-speed-timeseries.csv` | `evidence/csv/eva_series/eva-lowpen-speed-timeseries.csv` | low-penetration speed/lane timeseries |

С этим блоком связаны также текстовые материалы в исходной папке:

- `cycle7_fizulin_av/README.md`
- `cycle7_fizulin_av/notion_report.md`
- `cycle7_fizulin_av/chapter2_razrabotka.md`
- `cycle7_fizulin_av/chapter3_experiment.md`
- `cycle7_fizulin_av/source_digest.md`

Практически важная оговорка:

- `v2v-emergencyVehicleAlert-nrv2x` подтверждается текущим деревом и
  `src/automotive/examples/CMakeLists.txt`;
- отдельный collision-блок из старого пакета с упоминанием
  `v2v-degradation-collision-nrv2x` оставлен как историческая/рабочая заметка,
  поскольку в текущем проверенном `CMakeLists.txt` target с таким именем не
  подтвержден.

## 3b. Дополнительный raw dataset-блок из каталога `1`

| Исходный путь | Локальная копия | Назначение |
|---|---|---|
| `1/lena_db_dataset/dataset_inventory.csv` | `evidence/csv/lena_db_dataset_inventory.csv` | инвентарь SQLite-таблиц, числа строк и временных диапазонов по двум raw `.db` |
| `1/lena_db_dataset/csv/ide-test-nr-v2x-simple-demo/pktTxRx.csv` | `evidence/csv/lena_pktTxRx_ide.csv` | sample экспорт прикладной/сетевой таблицы `tx/rx` для быстрого просмотра без SQLite |
| `1/lena_db_dataset/csv/ide-test-nr-v2x-simple-demo/psschRxUePhy.csv` | `evidence/csv/lena_psschRxUePhy_ide.csv` | sample экспорт PHY-таблицы с `SINR`, `TBLER`, `corrupt` |

С этим блоком связаны также текстовые материалы в исходной папке:

- `1/README.md`
- `1/notion_report.md`
- `1/chapter2_razrabotka.md`
- `1/chapter3_experiment.md`
- `1/materials_manifest.md`
- `1/source_digest.md`

Практически важный вывод по этому набору:

- он усиливает отчет не новыми high-level KPI, а низкоуровневой доказательной
  базой по стоковому `5G-LENA` примеру `cttc-nr-v2x-demo-simple`;
- через него можно быстро показать, какие именно таблицы доступны в raw `.db`
  и как они стыкуются с дальнейшей унификацией результатов.

## 4. Основные run-директории с графиками

| Исходный путь | Роль |
|---|---|
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/` | основной комплект PNG и CSV для lane-change кейса |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/` | dashboards и causal figures для intersection кейса |
| `/root/NEWWAY_runs/2026-03-05/valid_scenario_smoke_lowprr_safeflow_sionna_002111` | исходный run для `my_scenarios/truck_lane_change_scenario/output` |
| `/root/NEWWAY_runs/2026-03-05/intersection_conflict_crash_eqm25` | исходный run для `my_scenarios/intersection_crash_scenario/output` |

## 5. Графики и GIF, скопированные в пакет

| Исходный путь | Локальная копия |
|---|---|
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/collision_risk/collision_risk_timeseries.png` | `evidence/img/lane_change/collision_risk_timeseries.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/drop_decision_timeline/decision_delay_scatter.png` | `evidence/img/lane_change/decision_delay_scatter.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/drop_decision_timeline/decision_type_counts.png` | `evidence/img/lane_change/decision_type_counts.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/valid_scenario_intuitive/intuitive_dbm_prr_maneuver_chain.png` | `evidence/img/lane_change/intuitive_dbm_prr_maneuver_chain.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/valid_scenario_intuitive/intuitive_packet_raster.png` | `evidence/img/lane_change/intuitive_packet_raster.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/valid_scenario_intuitive/intuitive_prr_cumulative.png` | `evidence/img/lane_change/intuitive_prr_cumulative.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/valid_scenario_intuitive/intuitive_truck_speed_observed.png` | `evidence/img/lane_change/intuitive_truck_speed_observed.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/valid_scenario_story/event_chain_timeline.png` | `evidence/img/lane_change/event_chain_timeline.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/valid_scenario_story/gap_ttc_timeseries.png` | `evidence/img/lane_change/gap_ttc_timeseries.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/valid_scenario_story/ns3_events_per_second.png` | `evidence/img/lane_change/ns3_events_per_second.png` |
| `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/artifacts/valid_scenario_story/speed_lane_timeseries.png` | `evidence/img/lane_change/speed_lane_timeseries.png` |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/visualizations/intersection_crash-111609/behavioral_dashboard.png` | `evidence/img/intersection/behavioral_dashboard.png` |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/visualizations/intersection_crash-111609/cross_layer_causal_chain.png` | `evidence/img/intersection/cross_layer_causal_chain.png` |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/visualizations/intersection_crash-111609/network_kpi_dashboard.png` | `evidence/img/intersection/network_kpi_dashboard.png` |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/visualizations/intersection_crash-111609/transport_safety_dashboard.png` | `evidence/img/intersection/transport_safety_dashboard.png` |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/visualizations/intersection_crash-111609/vehicle_profiles.png` | `evidence/img/intersection/vehicle_profiles.png` |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/artifacts/collision_risk/collision_risk_timeseries.png` | `evidence/img/intersection/intersection_collision_risk_timeseries.png` |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/artifacts/drop_decision_timeline/decision_delay_scatter.png` | `evidence/img/intersection/intersection_decision_delay_scatter.png` |
| `analysis/scenario_runs/2026-03-20/intersection_crash-111609/artifacts/drop_decision_timeline/decision_type_counts.png` | `evidence/img/intersection/intersection_decision_type_counts.png` |
| `analysis/intersection_3d_animation/circle_v2v/animation.gif` | `evidence/img/extras/circle_v2v_animation.gif` |
| `analysis/intersection_3d_animation/intersection_v2i/animation.gif` | `evidence/img/extras/intersection_v2i_animation.gif` |

## 5a. Графики, сгенерированные для EVA-серии

| Основа | Локальная фигура | Назначение |
|---|---|---|
| `evidence/csv/eva_series/summary-all-runs.csv` | `evidence/img/eva_series/eva_prr_latency_summary.png` | сравнение `PRR` и `latency` по режимам |
| `evidence/csv/eva_series/summary-all-runs.csv` | `evidence/img/eva_series/eva_cam_gap_summary.png` | сравнение CAM from EV и max inter-CAM gap |
| `evidence/csv/eva_series/eva-good-speed-timeseries.csv` | `evidence/img/eva_series/eva_good_speed_timeline.png` | baseline speed timeline |
| `evidence/csv/eva_series/eva-vbad-speed-timeseries.csv` | `evidence/img/eva_series/eva_vbad_speed_timeline.png` | very-bad speed timeline |
| `evidence/csv/eva_series/eva-lowpen-speed-timeseries.csv` | `evidence/img/eva_series/eva_lowpen_speed_timeline.png` | low-penetration speed timeline |

## 6. Дополнительные исследовательские материалы

| Путь | Роль |
|---|---|
| `analysis/mode2_loss/README.md` | смежный блок исследовательских наработок |
| `analysis/vkr/PLAN.md` | план ВКР |
| `analysis/vkr/VKR_inventory.md` | inventory рисунков и таблиц |
| `analysis/vkr/VKR_chapter2_tool_development.md` | draft главы по инструментальной среде |
