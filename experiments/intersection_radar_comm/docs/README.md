# intersection_radar_comm

Сценарий перекрестка для трех режимов:

1. `radar_bad_link` - локальный радар включен, V2X тоже включен, но у `veh3`
   ухудшен link budget; ожидаемый исход: ДТП.
2. `radar_only` - локальный радар включен, поведенческая реакция по V2X выключена;
   ожидаемый исход: ДТП.
3. `radar_good_link` - локальный радар включен, V2X канал штатный;
   ожидаемый исход: ДТП нет.

Что важно для методологии:

- сценарий запускается только через `Sionna + ns-3 + SUMO`;
- `rx-drop-prob-*`, `target-loss-profile-*` и `crash-mode-*` не используются;
- различие между `good_link` и `bad_link` задается не искусственными packet-drop
  данными, а через receiver-side link-budget degradation (`equiv_tx_power_dbm`),
  после чего судьба пакетов определяется штатным PHY/MAC + Sionna;
- локальный "радар" моделируется через `SUMO` sensor / `sensor_reaction`.

Текущая оговорка: по умолчанию используется уже имеющаяся в репозитории
`Sionna`-сцена `src/sionna/scenarios/SionnaCircleScenario/scene.xml`.
Это физически вычисляемый urban ray-tracing backend, но он еще не геометрически
зарегистрирован с конкретным `SUMO` junction этого сценария. Для следующей
итерации стоит собрать отдельную intersection-scene под эту карту.

## Запуск

Сначала поднять `Sionna` server:

```bash
experiments/intersection_radar_comm/scripts/start_sionna_server.sh
```

Потом запускать нужный режим:

```bash
experiments/intersection_radar_comm/scripts/run_radar_bad_link.sh
experiments/intersection_radar_comm/scripts/run_radar_only.sh
experiments/intersection_radar_comm/scripts/run_radar_good_link.sh
```

Или все три подряд:

```bash
experiments/intersection_radar_comm/scripts/run.sh
```

## Параметры по умолчанию

- `SUMO_GUI=1`
- `SIM_TIME=20`
- `RNG_RUN=17`
- `TX_POWER_DBM=23`
- `SENSOR_RANGE_M=30`
- `SENSOR_REACTION_DISTANCE_M=14`
- `SENSOR_REACTION_TTC_S=1.0`
- `CAM_REACTION_DISTANCE_M=95`
- `CAM_REACTION_HEADING_DEG=140`
- `VEH2_EQ_DBM=23`
- `VEH3_GOOD_EQ_DBM=23`
- `VEH3_BAD_EQ_DBM=-30`

## Артефакты

По каждому режиму:

- `$OUT_ROOT/<mode>/v2v-emergencyVehicleAlert-nrv2x.log`
- `$OUT_ROOT/<mode>/artifacts/eva-collision.xml`
- `$OUT_ROOT/<mode>/artifacts/eva-netstate.xml`
- `$OUT_ROOT/<mode>/artifacts/eva-veh2-*.csv`
- `$OUT_ROOT/<mode>/artifacts/eva-veh3-*.csv`
- `$OUT_ROOT/<mode>/artifacts/collision_risk/collision_risk_summary.csv`

Сводка по режимам:

- `$OUT_ROOT/summary/intersection_radar_comm_mode_summary.csv`

Ключевые поля сводки:

- факт и время collision `veh3 <-> veh2`;
- наблюдаемый PRR `veh3` по CAM от `veh2`;
- время первого `cam_reaction`;
- время первого `sensor_reaction`;
- `min_gap_m` и `min_ttc_s`.
