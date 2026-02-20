# Отчет по прогонам сценариев (2026-02-19, batch-main-161949)

## 1) Что выполнено

Запущены и проанализированы сценарии:

1. `cttc-nr-v2x-demo-simple`
2. `nr-v2x-west-to-east-highway`
3. `v2v-cam-exchange-sionna-nrv2x`
4. `v2v-coexistence-80211p-nrv2x`
5. `v2v-cam-exchange-sionna-nrv2x/run_compare_backends.sh` (non-Sionna baseline; Sionna stack отсутствует)
6. `v2v-emergencyVehicleAlert-nrv2x/run_loss_sweep.sh` (incident-mode, `rx-drop-prob-cam=0.0/0.4/0.8`)

Дополнительно:
- В `v2v-emergencyVehicleAlert-nrv2x.cc` добавлена устойчивая инъекция инцидента с явными маркерами в логе:
  - `INCIDENT-APPLIED,...`
  - `INCIDENT-RELEASED,...`
- Для sweep добавлены временные метрики реакции управления:
  - `first_control_action_s`
  - `p50_control_action_s`
  - `p90_control_action_s`
  - `last_control_action_s`

Сводка KPI: `analysis/scenario_runs/2026-02-19/batch-main-161949/run_summary.csv`

## 2) Практически полезные графики

Для выводов оставлены графики, напрямую отвечающие на исследовательские вопросы:

- Базовая NR Mode 2 валидация:
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/cttc-nr-v2x-demo-simple/figures/cttc-nr-v2x-demo-simple/cttc_prr_over_time.png`
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/cttc-nr-v2x-demo-simple/figures/cttc-nr-v2x-demo-simple/cttc_pssch_sinr_distribution.png`

- Многопользовательский highway (источник потерь/конкуренции):
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/nr-v2x-west-to-east-highway/figures/nr-v2x-west-to-east-highway/highway_prr_per_tx.png`
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/nr-v2x-west-to-east-highway/figures/nr-v2x-west-to-east-highway/highway_pir_vs_distance.png`
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/nr-v2x-west-to-east-highway/figures/nr-v2x-west-to-east-highway/highway_overlap_and_tb_fail_ratio.png`

- Coexistence 802.11p vs NR-V2X:
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/v2v-coexistence-80211p-nrv2x/figures/v2v-coexistence-80211p-nrv2x/coexistence_prr_latency_by_tech.png`
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/v2v-coexistence-80211p-nrv2x/figures/v2v-coexistence-80211p-nrv2x/coexistence_prr_per_node.png`
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/v2v-coexistence-80211p-nrv2x/figures/v2v-coexistence-80211p-nrv2x/coexistence_sinr_cdf_by_tech.png`

- CAM benchmark NR:
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/v2v-cam-exchange-sionna-nrv2x/figures/v2v-cam-exchange-sionna-nrv2x/cam_sionna_prr_per_node.png`
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/v2v-cam-exchange-sionna-nrv2x/figures/v2v-cam-exchange-sionna-nrv2x/cam_sionna_phy_vs_distance.png`

- Ключевой сценарий влияния потерь на поведение:
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/eva-loss-sweep-incident-v2/loss_sweep_summary.png`
  - `analysis/scenario_runs/2026-02-19/batch-main-161949/eva-loss-sweep-incident-v2/loss_sweep_behavior_timing.png`

## 3) Ключевые численные результаты

### 3.1 Базовые сценарии

- `cttc-nr-v2x-demo-simple`
  - PRR: `1.000`
  - PIR: `0.100765 s`
  - Throughput: `16.0 kbps`

- `nr-v2x-west-to-east-highway`
  - Средний PRR: `0.988333` (min `0.976667`, max `1.000`)
  - Средний PIR: `0.101536 s`
  - Средний throughput: `15.813333 kbps`
  - Доля overlap PSSCH Tx: `0.054667`
  - Доля PSSCH TB fail: `0.031573`

- `v2v-cam-exchange-sionna-nrv2x` (non-Sionna)
  - Average PRR: `0.946519`
  - Average latency: `11.7862 ms`
  - Per-node PRR: среднее `0.942897`, минимум `0.794484`

- `v2v-coexistence-80211p-nrv2x`
  - 802.11p: средний PRR `0.920307`, latency `0.491827 ms`, min PRR `0.788732`
  - NR-V2X: средний PRR `0.962061`, latency `12.569867 ms`, min PRR `0.826042`

### 3.2 Incident loss sweep (`v2v-emergencyVehicleAlert-nrv2x`)

Источник: `analysis/scenario_runs/2026-02-19/batch-main-161949/eva-loss-sweep-incident-v2/loss_sweep_summary.csv`

- Наблюдаемый CAM drop ratio: `0.000 -> 0.406 -> 0.802`
- Average PRR (MetricSupervisor): `0.959643 -> 0.959382 -> 0.959371` (почти без изменений)
- Average latency: `12.3156 -> 12.3455 -> 12.2585 ms` (почти без изменений)
- Control actions: `99 -> 58 -> 13` (падение на `86.9%` между `drop=0.0` и `drop=0.8`)
- First control action time: `3.84 s -> 4.33 s -> 11.93 s` (существенная задержка реакции)
- `INCIDENT-APPLIED/RELEASED` в логах подтверждают фактическую инъекцию инцидента (`veh2`, окно `12..30 s`)

### 3.3 Почему PRR почти не меняется при большом числе `CAM_DROP_APP`

В текущей постановке `--rx-drop-prob-cam` реализован как **application-level fault injection**:
- пакет уже принят стеком связи;
- затем в `emergencyVehicleAlert::receiveCAM()` он может быть отброшен на уровне приложения как `CAM_DROP_APP`.

Из-за этого:
- метрика `Average PRR` (из `MetricSupervisor`) почти не меняется;
- но поведенческие метрики (`control_actions`, `first_control_action_s`) ухудшаются резко.

Это ожидаемое поведение модели и полезный результат для ВКР:
он демонстрирует, что усредненный link/network PRR может скрывать деградацию на уровне принятия решений транспортом.

### 3.4 Baseline vs lossy тайм-лайн (покадровое сравнение)

Собран сравнительный тайм-лайн для `drop_0p0` vs `drop_0p8`:
- `analysis/scenario_runs/2026-02-19/batch-main-161949/eva-loss-sweep-incident-v2/comparison_drop0p0_vs_0p8/comparison_summary.csv`
- `analysis/scenario_runs/2026-02-19/batch-main-161949/eva-loss-sweep-incident-v2/comparison_drop0p0_vs_0p8/comparison_timeline.csv`
- `analysis/scenario_runs/2026-02-19/batch-main-161949/eva-loss-sweep-incident-v2/comparison_drop0p0_vs_0p8/comparison_timeline.png`

По сравнению:
- `overall_cam_drop_ratio`: `0.000 -> 0.802`
- `total_control_actions`: `99 -> 13`
- `first_control_action_s`: `3.84 s -> 11.93 s`
- `collisions_count`: `0 -> 0` в текущей конфигурации.

## 4) Что это значит для цели исследования

Цель: оценить влияние потерь сообщений в 5G NR Mode 2 sidelink на поведение подключенного/беспилотного транспорта.

Выводы по текущим данным:

1. Потери CAM уже в этом репозитории демонстрируют выраженное поведенческое влияние.
   - При росте drop до ~0.8 количество управляющих реакций падает почти в 8 раз (`99 -> 13`).
   - Время первой реакции смещается в небезопасную сторону (`3.84 s -> 11.93 s`).

2. Средние сетевые KPI (PRR/latency по MetricSupervisor) могут маскировать поведенческую деградацию.
   - PRR и latency почти не меняются в sweep, но поведенческие метрики меняются резко.

3. Для доказательной части ВКР нужны не только communication KPI, но и behavior-aware KPI.
   - `control_actions`, `first/p90 reaction time`, `min per-node PRR`, `tail metrics`, `overlap/tb_fail`.

4. В текущей конфигурации SUMO жесткие аварийные события (risky gap/TTC) не возникли.
   - `risky_gap_events=0`, `risky_ttc_events=0`.
   - Это не опровергает влияние потерь; это означает, что нужно усиливать конфликтный дорожный кейс для демонстрации near-crash/crash.

## 5) Ограничения и следующий шаг

- Sionna backend comparison не завершен из-за отсутствия зависимостей (`tensorflow/sionna/mitsuba`).
- Для демонстрации «потеря сообщения -> авария/критический инцидент» требуется более агрессивный дорожный сценарий:
  - более плотный поток,
  - меньшие headway,
  - жесткий lane-blocking инцидент,
  - явные surrogate safety KPI (TTC/PET/DRAC/time-to-lane-change).
