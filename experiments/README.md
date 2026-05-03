# experiments/

Все эксперименты и сценарии симуляции в одном месте. Каждый подпакет — самодостаточный сценарий со своими `scripts/`, `docs/`, опционально `tools/`, `sumo/`, `results/`.

## Карта экспериментов

| Папка | Что делает | Главный скрипт |
|---|---|---|
| `truck_lane_change/` | Lane-change объезд остановившегося лидера, с явной cause-effect цепочкой PRR → manoeuvre. | `scripts/run.sh` |
| `intersection_crash/` | Junction priority-конфликт с третьим автомобилем. Demo crash vs safe pass. | `scripts/run.sh` |
| `intersection_radar_comm/` | Перекрёсток с 3 режимами: радар + V2X comm, плюс sweep по equiv_tx_power. | `scripts/run.sh`, `scripts/run_radar_*.sh` |
| `cpm_perception/` | CPM / collective perception, 3 режима (sensor only / good CPM / bad CPM). | `scripts/run.sh`, `scripts/run_sensor_*.sh` |
| `compare_tech/` | Compare V2X стека (NR-V2X / 802.11p) на одном trace. | `scripts/run.sh` |
| `intersection_v2x_awareness/` | Свежая (apr 2026) переработка intersection без timer-hardcoding. | `scripts/run.sh` |
| `operational/` | Operational launchers для C++ примеров ms-van3t (cttc, west-to-east-highway, v2v-cam-exchange-sionna, v2v-coexistence-80211p, v2v-emergencyVehicleAlert, 5g-phy-metrics). | `<name>/run.sh` |
| `strict_sionna_vkr/` | Строгий Sionna-пакет с собственными manifests/scripts/scenes. | `scripts/...` |
| `raw/` | Raw-only прогоны без постобработки (для воспроизводимости). | `<name>/run.sh` |

## Где результаты

Все evidence-прогоны для ВКР и анализов лежат в `runs/<YYYY-MM-DD>/<run_dir>/`. См. [`runs/README.md`](../runs/README.md).

In-experiment artifacts (если есть) — в `experiments/<name>/results/`.

## Где инструменты

Постобработка / графики / агрегация — в `tools/`. См. [`tools/README.md`](../tools/README.md).
