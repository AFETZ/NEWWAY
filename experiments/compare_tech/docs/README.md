# compare_tech

Сценарный A/B (и опционально A/B/C) пакет для сравнения радиотехнологий на двух кейсах:

- `truck` (объезд/столкновение со статическим препятствием на трассе),
- `intersection` (приоритетный перекресток).

Поддерживаемые технологии:

- `80211p`
- `ltev2x`
- `nrv2x` (опционально, по умолчанию включен)

## Что делает run.sh

`my_scenarios/compare_tech/run.sh`:

1. Собирает нужные бинарники EVA (`80211p`, `ltev2x`, `nrv2x`);
2. Прогоняет обе сцены по всем выбранным технологиям;
3. Собирает `MSG/CTRL/PROFILE/netstate` артефакты;
4. Строит сводку `compare_tech_summary.csv`.

## Быстрый запуск

Из корня репозитория:

```bash
my_scenarios/compare_tech/run.sh
```

По умолчанию:

- `TECHS_CSV=80211p,ltev2x,nrv2x`
- `SCENARIOS_CSV=truck,intersection`
- `SUMO_GUI=0`

## Запуск только LTE vs 802.11p

```bash
TECHS_CSV=80211p,ltev2x \
SCENARIOS_CSV=truck,intersection \
my_scenarios/compare_tech/run.sh
```

## Полезные параметры

- `OUT_DIR` — директория результатов (по умолчанию `$HOME/NEWWAY_runs/<date>/compare_tech`)
- `SUMO_GUI` — `1` для GUI
- `TX_POWER_DBM` — мощность передатчика
- `SIM_TIME_TRUCK`, `SIM_TIME_INTERSECTION` — длительности сцен
- `RUN_RETRIES` — число ретраев при временном `Connection refused`
- `COMPARE_MODE`:
  - `channel` (по умолчанию): без ручных drop-override, сравнение в основном по каналу/MAC технологии
  - `scenario_replay`: включает ручные per-vehicle `rx_drop_prob_phy_cam` для воспроизведения "lossy vehicle" логики

Примечание: для `ltev2x` в `scenario_replay` режиме `met-sup` автоматически отключается из-за известного assertion-path в MetricSupervisor при экстремальных принудительных drop.

## Артефакты

Для каждого прогона:

- `<OUT_DIR>/<scenario>/<tech>/artifacts/eva-veh*-{MSG,CTRL,PROFILE}.csv`
- `<OUT_DIR>/<scenario>/<tech>/artifacts/eva-netstate.xml`
- `<OUT_DIR>/<scenario>/<tech>/artifacts/collision_risk/*`
- `<OUT_DIR>/<scenario>/<tech>/artifacts/run_meta.env`

Итоговая матрица:

- `<OUT_DIR>/compare_tech_summary.csv`
