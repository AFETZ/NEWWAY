# v2v-coexistence-80211p-nrv2x

Сценарий сосуществования 802.11p и NR-V2X в одном трафике с отдельными KPI по технологиям.

- Исходник: `src/automotive/examples/v2v-coexistence-80211p-nrv2x.cc`
- Ключевые строки: `:84`, `:501`, `:971`, `:1032`
- Особый режим сборки/запуска: `README.md:203`

## Запуск

```bash
scenarios/v2v-coexistence-80211p-nrv2x/run.sh
```

По умолчанию сценарий запускается с `--sumo-gui=0 --sim-time=20`.
Скрипт сам включает/выключает interference-mode.

## Что сохраняется

- Лог: `analysis/scenario_runs/<date>/v2v-coexistence-80211p-nrv2x.log`
- Артефакты:
  - `analysis/scenario_runs/<date>/artifacts/prr_latency_ns3_coexistence_11p.csv`
  - `analysis/scenario_runs/<date>/artifacts/prr_latency_ns3_coexistence_nrv2x.csv`
  - `analysis/scenario_runs/<date>/artifacts/sinr_ni.csv`
- Графики: `analysis/scenario_runs/<date>/figures/v2v-coexistence-80211p-nrv2x/*.png`
