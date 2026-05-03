# Research Scenarios for Loss -> Behavior Evidence

Цель: показать, как потери сообщений в NR Mode 2 переходят в поведенческие риски (задержка реакции, опасное сближение, потенциальная авария).

## Похожие кейсы, уже есть в репозитории

- `v2v-emergencyVehicleAlert-nrv2x`:
  - логика реакции на CAM от emergency-авто с `changeLane` и `setMaxSpeed`:
    `src/automotive/model/Applications/emergencyVehicleAlert.cc:460`
    `src/automotive/model/Applications/emergencyVehicleAlert.cc:480`
    `src/automotive/model/Applications/emergencyVehicleAlert.cc:495`
  - готовый сценарий с NR-V2X Mode 2:
    `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:681`

- `emergencyVehicleWarningClient80211p` (по IVIM):
  - обработка зоны релевантности и lane/speed adaptation:
    `src/automotive/model/Applications/emergencyVehicleWarningClient80211p.cc:316`
    `src/automotive/model/Applications/emergencyVehicleWarningClient80211p.cc:387`
    `src/automotive/model/Applications/emergencyVehicleWarningClient80211p.cc:414`

- `trafficManagerServer80211p`:
  - генерация DENM с ограничением скорости в целевой гео-области:
    `src/automotive/model/Applications/trafficManagerServer80211p.cc:96`
    `src/automotive/model/Applications/trafficManagerServer80211p.cc:167`

## Уже реализовано для доказательства "потеря -> аварийный исход"

1. В `emergencyVehicleAlert` добавлены fault-injection параметры:
   `--rx-drop-prob-cam` и `--rx-drop-prob-cpm`.
2. Добавлен явный лог управления:
   `*-CTRL.csv` с типом маневра и временем.
3. В `v2v-emergencyVehicleAlert-nrv2x` используется `--netstate-dump-file`
   и последующий расчет safety-прокси.
4. Готовые скрипты:
   - `scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh`
   - `scenarios/v2v-emergencyVehicleAlert-nrv2x/run_loss_sweep.sh`

## Минимальный воспроизводимый план эксперимента

1. Baseline (низкие потери):
   `txPower` высокий, `slThresPsschRsrp` мягкий.
2. Lossy режим:
   `txPower` низкий и/или жёсткий `slThresPsschRsrp`, можно отключить sensing.
3. Сравнить:
   PRR/latency/reaction delay + `min_gap_m`/`min_ttc_s`/`risky_*` из netstate.

## Сценарии, которые реально проделать здесь

1. `v2v-emergencyVehicleAlert-nrv2x` + sweep по `rx-drop-prob-cam` (и/или `txPower`, `enableSensing`, `slThresPsschRsrp`).
2. `v2v-coexistence-80211p-nrv2x` + sweep + сравнение хвостов per-node PRR/latency.
3. `v2v-cam-exchange-sionna-nrv2x`:
   - baseline без Sionna,
   - terrain-aware backend (Sionna) при наличии `tensorflow/sionna/mitsuba`.
4. `nr-v2x-west-to-east-highway`:
   - рост нагрузки (`numVehiclesPerLane`, `dataRateBe`) и анализ `overlap`/`TB fail`.

## Как приблизить кейс "потеря сообщения -> авария"

1. Stalled-vehicle вариант в `v2v-emergencyVehicleAlert-nrv2x`:
   - выбрать `incident vehicle`, принудительно остановить через TraCI (`setMaxSpeed(0)`/`setStop`),
   - держать CAM-передачу от этого авто активной,
   - для едущих сзади добавить маневр уклонения при получении CAM.
2. Прогонять пары режимов:
   - `rx-drop-prob-cam=0.0` (reference),
   - `rx-drop-prob-cam=0.5..0.8` (lossy).
3. Считать одинаковые KPI:
   - network: PRR/latency,
   - behavior: число/время evasive маневров (`*-CTRL.csv`),
   - safety: `min_gap_m`, `min_ttc_s`, `risky_*` из netstate.
4. Критерий "аварийности" задавать порогами:
   - например `min_gap_m < 1.0` и/или `min_ttc_s < 1.0`,
   - смотреть delta между reference и lossy.
