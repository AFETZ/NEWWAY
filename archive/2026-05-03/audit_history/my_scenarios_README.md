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

- `compare_tech/`
  - матричный прогон `truck` + `intersection` по нескольким радиотехнологиям
  - запуск: `./run.sh`
  - итог: единая сводка `compare_tech_summary.csv`

- `cpm_perception_scenario/`
  - сравнение `sensor_only` vs `sensor+good_cpm` vs `sensor+bad_cpm`
  - запуск: `./run.sh` для всех трех режимов или `./run_sensor_only.sh`, `./run_sensor_good_cpm.sh`, `./run_sensor_bad_cpm.sh` по отдельности
  - итог: сводка `cpm_perception_mode_summary.csv` по выбранному режиму или по всем трем

- `intersection_radar_comm_scenario/`
  - сравнение `radar_bad_link` vs `radar_only` vs `radar_good_link` на перекрестке
  - запуск: `./run.sh` для всех трех режимов или `./run_radar_bad_link.sh`, `./run_radar_only.sh`, `./run_radar_good_link.sh` по отдельности
  - итог: сводка `intersection_radar_comm_mode_summary.csv`

## Примечание

`output/source_run.txt` в каждой папке указывает исходный run-dir, из которого были скопированы CSV.
