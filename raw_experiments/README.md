# raw_experiments

Отдельная зона для прогонов, где сохраняются только исходные артефакты
симуляторов без постобработки и без производных CSV/PNG/summary.

## Что здесь лежит

- `truck_lane_change_5glena_raw/`
  - raw-only launcher для сценария с грузовиком и перестроением;
  - запускает тот же базовый lane-change кейс, что и `valid_scenario`,
    но напрямую, без `--csv-log` и без аналитических скриптов;
  - по умолчанию использует `5G-LENA + SUMO` без Sionna.

## Куда пишутся результаты

По умолчанию:

`raw_experiments/runs/<YYYY-MM-DD>/truck_lane_change_5glena_raw-<HHMMSS>/`

Внутри run-директории остаются только raw-файлы симуляторов:

- `v2v-emergencyVehicleAlert-nrv2x.log`
- `eva-netstate.xml`
- `eva-collision.xml` (если включен collision-output)

Никакие `*-MSG.csv`, `*-CTRL.csv`, `*-PROFILE.csv`, графики,
`collision_risk/*.csv` и прочие постпроцессированные артефакты сюда
не пишутся.
