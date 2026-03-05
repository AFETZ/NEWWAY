# intersection_crash_scenario

Фиксированный сценарий приоритетного перекрестка с третьей машиной (`veh4`):
- `veh2` и `veh3` формируют конфликт на junction `w`;
- `veh4` приходит с третьего направления, не теряет пакеты, ждет конфликт и проезжает безопасно после ДТП.

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
