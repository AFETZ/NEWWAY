# valid_intersection_scenario

Детерминированный junction-кейс для ВКР на карте `sumo_files_v2i_map`:

- `veh2` (emergency, major stream) проходит priority junction.
- `veh3` (minor stream) должен уступить.
- `veh4` (third direction, connected safe stream) подходит с `n1_to_w`,
  не теряет пакеты, ждет конфликт и проходит безопасно после ДТП `veh3 <-> veh2`.
- при высоком PRR у `veh3` — безопасный пропуск;
- при низком PRR у `veh3` — `DROP_PHY -> drop_decision_no_action -> crash_mode_forced_speed -> collision`.
- геометрия усилена (более длинные кузова + tighter ETA), чтобы crash-кейс был визуально и логически устойчивым.
- `veh2` отображается как грузовик (`guiShape=truck`) и идет по главному направлению `s1 -> w -> n1`;
  `veh3` идет с второстепенного `c1 -> w -> s1` (справа налево к точке конфликта);
  `veh4` идет с третьего направления `n1 -> w -> s1 -> c1` (сверху вниз, затем поворот на `c1`).

## Быстрый запуск

Из корня репозитория:

```bash
valid_intersection_scenario/run.sh
```

Сценарий по умолчанию запускается в **аварийном профиле** (`veh3 target PRR=0.02`, `VEH3_EQ_DBM=-30`) и с `USE_SIONNA=1`.
Для более аккуратной визуализации ДТП по умолчанию включены:
- `COLLISION_ACTION=warn`
- `collision.mingap-factor=1.8`
- `collision.check-junctions.mingap=1.5`

Примечание: проверка UDP-listener Sionna отключена по умолчанию (`CHECK_SIONNA_LISTENER=0`) из-за ограничений некоторых окружений с `ss`; фактическое подключение подтверждается строкой `SUCCESS! ns-3 is now locally connected to Sionna` в `v2v-emergencyVehicleAlert-nrv2x.log`.

## Sionna GPU

Перед запуском `valid_intersection_scenario/run.sh` должен быть поднят Sionna server на `127.0.0.1:8103`.

## A/B режимы

Safe (высокий PRR у `veh3`):

```bash
USE_SIONNA=1 SUMO_GUI=1 \
PHY_ONLY=1 ALLOW_MANUAL_RX_DROP=0 \
VEH3_EQ_DBM=23 VEH3_TARGET_PRR=0.95 \
valid_intersection_scenario/run.sh
```

Crash (низкий PRR у `veh3`):

```bash
USE_SIONNA=1 SUMO_GUI=1 \
PHY_ONLY=1 ALLOW_MANUAL_RX_DROP=0 \
VEH3_EQ_DBM=-30 VEH3_TARGET_PRR=0.02 \
valid_intersection_scenario/run.sh
```

Важно: в режиме `PHY_ONLY=1` ручные `rx_drop` отключены.
Потери определяются каналом (Sionna + PHY), а `drop_decision_no_action` строится ID-aware по `tx_id/msg_seq`.

## Артефакты

- `artifacts/eva-collision.xml` — collisions в SUMO (включая junction).
- `artifacts/drop_decision_timeline/*` — строгая связка `DROP_PHY -> DECISION` по `pkt_uid`.
- `artifacts/collision_causality/*` — причинная выборка событий перед collision.
- `artifacts/intersection_summary.csv` — компактная сводка по `veh3`:
  - target/configured/observed PRR;
  - первые `cam_reaction`, `drop_decision_no_action`, `crash_mode_forced_speed`;
  - факт и время collision `veh3 <-> veh2`.

## Карта и маршруты

- SUMO config: `src/automotive/examples/sumo_files_v2i_map/map_intersection_priority.sumo.cfg`
- Routes: `src/automotive/examples/sumo_files_v2i_map/cars_intersection_priority.rou.xml`
