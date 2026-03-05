# intersection_crash_scenario

Фиксированный сценарий ДТП на приоритетном перекрестке.

## Запуск

Из корня репозитория:

```bash
my_scenarios/intersection_crash_scenario/run.sh
```

Скрипт делегирует запуск в:

- `valid_intersection_scenario/run.sh`

## Что лежит в output

- `intersection_summary.csv` - компактная сводка PRR/реакций/collision.
- `eva-veh2/3-{MSG,CTRL,PROFILE}.csv` - сетевые и decision события ключевых авто.
- `drop_decision_event_timeline.csv`, `drop_decision_summary.csv` - drop -> decision.
- `collision_causality.csv` - causality перед collision.
- `collision_risk_summary.csv`, `collision_risk_timeseries.csv` - safety-метрики.
- `source_run.txt` - исходный run-dir.
