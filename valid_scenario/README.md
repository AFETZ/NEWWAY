# valid_scenario

Валидированный сценарий для диплома/ВКР: доказуемый **bidirectional coupling ns-3 <-> SUMO**.

## Цель сценария

В одном прогоне получить причинно-связанную цепочку:

1. `veh3` (профиль `23 dBm`, target `PRR=0.95`) получает предупреждения и перестраивается в безопасную полосу.
2. `veh4` (профиль `-20 dBm`, target `PRR=0.077`) получает `DROP_PHY -> drop_decision_no_action` и сталкивается с `veh2`.
3. `veh2` и `veh4` после столкновения **не исчезают** (формируют место ДТП/затор).
4. `veh5` (профиль `0 dBm`, target `PRR=0.693`) позже перестраивается, обходя образовавшееся препятствие.

## Как запустить

Из корня репозитория:

```bash
valid_scenario/run.sh
```

Live GUI:

```bash
SUMO_GUI=1 valid_scenario/run.sh
```

Примечание для Sionna: `valid_scenario/run.sh` по умолчанию запускает сценарий с `USE_SIONNA=1`, поэтому Sionna server должен быть доступен на `SIONNA_SERVER_IP` (по умолчанию `127.0.0.1`).

Headless:

```bash
SUMO_GUI=0 valid_scenario/run.sh
```

Fallback без Sionna:

```bash
USE_SIONNA=0 valid_scenario/run.sh
```

Куда пишутся результаты по умолчанию:

- `$HOME/NEWWAY_runs/<YYYY-MM-DD>/valid_scenario`

## Что именно фиксируется параметрами

- `--sumo-config=.../map_incident_threeflow.sumo.cfg`
  - 3 машины позади инцидентного `veh2` в его полосе (`veh3`,`veh4`,`veh5`)
- `--per-vehicle-prr-profile=...`
  - задает по машине `rxDropPhyCam + equiv dBm + target PRR`:
    - `veh3 -> (23 dBm, 0.95)`
    - `veh4 -> (-20 dBm, 0.077)`
    - `veh5 -> (0 dBm, 0.693)`
- `USE_SIONNA=1` + `--sionna=1`
  - PHY рассчитывается через Sionna; далее применяется per-vehicle профиль потерь на приемнике
- `--drop-triggered-reaction-enable=0`
  - strict режим: drop-события не вызывают «скрытый» маневр, только `drop_decision_no_action`
- `--incident-setstop-enable=0`
  - инцидент удерживается на месте без `setStop`-сдвига вперед по маршруту
- `--reaction-force-lane-change-enable=1`
  - детерминирует lane-change по реакции
- `COLLISION_ACTION=warn` + `COLLISION_STOPTIME_S=1000`
  - столкнувшиеся авто остаются на дороге

## Артефакты для доказательства

После запуска формируются:

- `artifacts/eva-collision.xml` — факты столкновений в SUMO
- `artifacts/drop_decision_timeline/*` — ID-aware `pkt_uid: DROP_PHY -> DECISION`
- `artifacts/collision_causality/*` — causal report `loss -> no_action -> collision`
- `artifacts/eva-veh*-PROFILE.csv` — зафиксированный профиль `dBm/target PRR/drop-prob` по каждому ТС
- `artifacts/valid_scenario_story/*` — дипломные графики «под капотом»

## Подкапотные графики (автоматически)

`valid_scenario/run.sh` вызывает:

- `analysis/scenario_runs/build_valid_scenario_story_plots.py`
- `analysis/scenario_runs/build_valid_scenario_intuitive_plots.py`

и строит:

- `speed_lane_timeseries.png` — скорости/полосы `veh2..veh5`
- `gap_ttc_timeseries.png` — динамика gap/TTC для пар `veh4->veh2`, `veh5->veh4`
- `ns3_events_per_second.png` — DROP_PHY, no_action и lane-change решения по времени
- `event_chain_timeline.png` — сводная шкала `incident -> lane change -> collision -> lane change`
- `event_chain.csv` — та же шкала в табличной форме

## Наглядные графики (CSV-only, проще читать)

Отдельно формируются графики в `artifacts/valid_scenario_intuitive/`:

- `intuitive_prr_summary.csv` — итоговый PRR по каждому автомобилю относительно грузовика (`tx_id=2`)
- `intuitive_prr_cumulative.png` — PRR по времени (накопительно)
- `intuitive_packet_raster.png` — по времени: получен/потерян пакет + моменты lane-change + collision
- `intuitive_truck_speed_observed.png` — какую скорость грузовика реально «видел» каждый автомобиль по принятым CAM
- `intuitive_key_events.csv` — ключевые времена (`veh3 lane-change`, `collision`, `veh5 lane-change`)
- `intuitive_dbm_prr_maneuver_chain.csv` — явная цепочка `equiv dBm -> target PRR -> observed PRR -> decision -> collision`
  (`decision_outcome`: `maneuver_before_collision` / `no_maneuver_before_collision` / `late_maneuver_after_collision`)
- `intuitive_dbm_prr_maneuver_chain.png` — наглядный график той же цепочки

## Для текста ВКР

Готовый расширенный текст сценария: `valid_scenario/VKR_SCENARIO_TEXT.md`.
