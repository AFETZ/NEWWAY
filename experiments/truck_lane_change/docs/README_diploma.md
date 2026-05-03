# truck_lane_change_scenario

Фиксированный сценарий "грузовик + смена полосы + lossy-авто".

## Запуск

Из корня репозитория:

```bash
my_scenarios/truck_lane_change_scenario/run.sh
```

Скрипт делегирует запуск в:

- `valid_scenario/run.sh`

## Что лежит в output

- `eva-veh2/3/4/5-{MSG,CTRL,PROFILE}.csv` - сетевые и decision события по ключевым авто.
- `drop_decision_event_timeline.csv`, `drop_decision_summary.csv` - строгая связка drop -> decision.
- `collision_causality.csv` - причинная выборка перед ДТП.
- `collision_risk_summary.csv`, `collision_risk_timeseries.csv` - safety-метрики.
- `story_event_chain.csv`, `story_vehicle_state_timeseries.csv` - story CSV.
- `intuitive_*.csv` - интуитивные агрегаты для графиков ВКР.
- `source_run.txt` - исходный run-dir.
