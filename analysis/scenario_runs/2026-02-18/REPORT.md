# Отчет по прогонам сценариев (2026-02-18)

## Что было запущено

1. `cttc-nr-v2x-demo-simple`
2. `nr-v2x-west-to-east-highway`
3. `v2v-cam-exchange-sionna-nrv2x` (с `--sumo-gui=0 --sim-time=20`)
4. `v2v-coexistence-80211p-nrv2x` (с `--sumo-gui=0 --sim-time=20`, interference-mode ON на время запуска)

Логи: `analysis/scenario_runs/2026-02-18/*.log`  
Артефакты: `analysis/scenario_runs/2026-02-18/artifacts/`  
Сводка KPI: `analysis/scenario_runs/2026-02-18/run_summary.csv`
Графики: `analysis/scenario_runs/2026-02-18/figures/`

## Наглядные графики по сценариям

- `cttc-nr-v2x-demo-simple`
  - `analysis/scenario_runs/2026-02-18/figures/cttc-nr-v2x-demo-simple/cttc_prr_over_time.png`
  - `analysis/scenario_runs/2026-02-18/figures/cttc-nr-v2x-demo-simple/cttc_pssch_sinr_distribution.png`

- `nr-v2x-west-to-east-highway`
  - `analysis/scenario_runs/2026-02-18/figures/nr-v2x-west-to-east-highway/highway_prr_per_tx.png`
  - `analysis/scenario_runs/2026-02-18/figures/nr-v2x-west-to-east-highway/highway_pir_vs_distance.png`
  - `analysis/scenario_runs/2026-02-18/figures/nr-v2x-west-to-east-highway/highway_top_links_throughput.png`
  - `analysis/scenario_runs/2026-02-18/figures/nr-v2x-west-to-east-highway/highway_overlap_and_tb_fail_ratio.png`

- `v2v-cam-exchange-sionna-nrv2x`
  - `analysis/scenario_runs/2026-02-18/figures/v2v-cam-exchange-sionna-nrv2x/cam_sionna_prr_per_node.png`
  - `analysis/scenario_runs/2026-02-18/figures/v2v-cam-exchange-sionna-nrv2x/cam_sionna_phy_vs_distance.png`

- `v2v-coexistence-80211p-nrv2x`
  - `analysis/scenario_runs/2026-02-18/figures/v2v-coexistence-80211p-nrv2x/coexistence_prr_latency_by_tech.png`
  - `analysis/scenario_runs/2026-02-18/figures/v2v-coexistence-80211p-nrv2x/coexistence_prr_per_node.png`
  - `analysis/scenario_runs/2026-02-18/figures/v2v-coexistence-80211p-nrv2x/coexistence_sinr_cdf_by_tech.png`

## Ключевые результаты

- `cttc-nr-v2x-demo-simple`
  - PRR: `1.000`
  - PIR: `0.100765 s`
  - Throughput: `16.0 kbps`
  - Интерпретация: базовая Mode 2 цепочка в "чистом" 2-UE случае работает без потерь.

- `nr-v2x-west-to-east-highway`
  - Средний PRR: `0.988333` (min `0.976667`, max `1.000`)
  - Средний PIR: `0.101536 s`
  - Средний throughput: `15.813333 kbps`
  - Доля overlap PSSCH Tx: `0.054667`
  - Доля PSSCH TB ошибок: `0.031573`
  - Интерпретация: при многопользовательской highway-нагрузке появляются коллизии и PHY-ошибки, но деградация KPI умеренная.

- `v2v-cam-exchange-sionna-nrv2x`
  - Средний PRR (MetricSupervisor): `0.946519`
  - Средняя latency: `11.7862 ms`
  - Доп. наблюдение: по `prr_with_sionna_nrv2x.csv` среднее per-node PRR `0.942897`, min `0.794484`.
  - Backend compare pipeline подготовлен и проверен:
    `analysis/scenario_runs/2026-02-18/cam-sionna-backend-compare-1600/non_sionna/`.
    Sionna-run не выполнен из-за отсутствия зависимостей `tensorflow/sionna/mitsuba` в окружении.
  - Интерпретация: в SUMO/CAM-потоке PRR ниже "идеальных" NR-демо, и есть заметная неравномерность по узлам.

- `v2v-coexistence-80211p-nrv2x`
  - 802.11p: PRR `0.924245`, latency `0.491460 ms`
  - NR-V2X: PRR `0.965817`, latency `12.442200 ms`
  - Per-node PRR:
    - 802.11p: avg `0.920307`, min `0.788732`
  - NR-V2X: avg `0.962061`, min `0.826042`
  - Интерпретация: в смешанном трафике NR-V2X показал более высокий PRR, но более высокую E2E latency, чем 802.11p.

- `v2v-emergencyVehicleAlert-nrv2x` (loss sweep: `rx-drop-prob-cam=0.0/0.4/0.8`)
  - Артефакты: `analysis/scenario_runs/2026-02-18/eva-loss-sweep-1550/`
  - Наблюдаемый CAM drop ratio: `0.000 -> 0.405 -> 0.805`
  - Control actions: `78 -> 42 -> 15`
  - MetricSupervisor PRR/latency: почти без изменений (`~0.952`, `~12 ms`)
  - Safety proxy (пороги 2.0 м / 1.5 с): risky events = `0`, min TTC `3.669..4.439 s`
  - Интерпретация: рост потерь CAM уже в этой постановке заметно уменьшает число поведенческих реакций, даже если средние сетевые KPI выглядят стабильными.

## Выводы для цели исследования (влияние потерь сообщений NR Mode 2 на CAV/AV поведение)

1. Потери в NR Mode 2 прямо связаны с ростом задержек восприятия событий.
2. Даже при хорошем среднем PRR (`~0.95-0.99`) есть "хвост" по узлам с существенно худшим PRR (`~0.79-0.83`), что критично для safety-кейсов.
3. На highway-нагрузке основная причина деградации — конкуренция за ресурсы (overlap) и TB corruption; это механизм, через который потери переходят в поведенческую нестабильность.
4. По ранее собранному sweep (`analysis/mode2_loss`): при падении PRR с `0.938` до `0.077` p90 reaction delay рос с `3.984 s` до `18.094 s`; это уже уровень, который может менять траектории/торможение и повышать риск конфликтных маневров.
5. По `eva-loss-sweep-1550` потери CAM напрямую снижают количество реакций автомобилей (`78 -> 15`), то есть влияние потерь на поведение подтверждено даже без заметного сдвига среднего PRR/latency канала.

## Практическое значение

- Для валидации CAV/AV алгоритмов недостаточно проверять только средний PRR.
- Нужны ограничения на хвостовые метрики (`p90/p95` задержки, минимальный per-node PRR, overlap/corruption), иначе деградация связи может не проявиться в "средних" KPI, но проявится в критических ситуациях.
- Для демонстрации именно аварийного исхода в текущем репозитории нужен более конфликтный дорожный кейс (stalled-vehicle/lane-blocking), иначе min gap/TTC остаются в безопасной зоне.
