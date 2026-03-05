# my_scenarios

Отдельная папка с фиксированными дипломными сценариями.

## Структура

- `truck_lane_change_scenario/`
  - сценарий с грузовиком, перестроениями и lossy-машиной
  - запуск: `./run.sh` (делегирует в `valid_scenario/run.sh`)
  - `output/` содержит CSV для графиков и доказательной части

- `intersection_crash_scenario/`
  - сценарий ДТП на приоритетном перекрестке
  - запуск: `./run.sh` (делегирует в `valid_intersection_scenario/run.sh`)
  - `output/` содержит CSV для графиков и причинной связки

## Примечание

`output/source_run.txt` в каждой папке указывает исходный run-dir, из которого были скопированы CSV.
