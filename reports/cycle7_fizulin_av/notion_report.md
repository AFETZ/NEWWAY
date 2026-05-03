# Цикл №7: экспериментальный блок Физулина А.В. по VaN3Twin / ns-3 / NR-V2X

## 1. О чем этот блок

В рамках цикла №7 был оформлен отдельный исследовательский блок по `VaN3Twin / ns-3 / NR-V2X`, без искусственного притягивания работы к `Simu5G`. Цель блока состояла в том, чтобы привести в воспроизводимый и отчетный вид уже выполненную серию экспериментов по сценарию `Emergency Vehicle Alert`, собрать результаты в единый пакет материалов и подготовить основу для следующего этапа сравнения `VaN3Twin/ns-3` с `Simu5G`.

На выходе сформирован пакет, который решает сразу три задачи:

- фиксирует, что именно было сделано в цикле;
- дает команде воспроизводимый набор команд и артефактов;
- переводит исследовательские результаты в формат, пригодный для страницы в Notion и карточки в трекере.

## 2. Что сделано в цикле №7

В рамках данного блока были выполнены следующие работы:

- оформлен и зафиксирован основной экспериментальный сценарий `v2v-emergencyVehicleAlert-nrv2x`;
- зафиксирована матрица из шести прогонов с варьированием параметров канала и penetration rate;
- систематизированы результаты по сетевым, информационным и поведенческим метрикам;
- отдельно верифицирован custom-сценарий `v2v-degradation-collision-nrv2x`, в котором качество связи влияет на исход взаимодействия между автомобилем экстренных служб и лидирующим автомобилем;
- подготовлен пакет итоговых материалов: отчет, карточка для трекера, блок распределения задач, сводные CSV и опись артефактов.

## 3. Рабочая среда

Фактические эксперименты, описанные в этом пакете, выполнялись в следующей среде:

- `VaN3Twin / ns-3-dev` как основная кодовая база;
- `Linux 6.6`, `WSL2`;
- `SUMO 1.26.0`;
- режим запуска `--sumo-gui=false` для основной серии прогонов;
- шаг `SUMO`: `0.01 с`;
- время моделирования для основной EVA-серии: `100 с`.

Дополнительно важно учитывать эксплуатационную оговорку из `README.md`: `Ubuntu 24.04` в репозитории не заявлена как officially supported среда для `VaN3Twin`. Это не мешает использовать уже полученные результаты, но при переносе окружения на новую машину лучше ориентироваться на версии ОС и зависимостей, ближе к тем, которые уже подтверждены документацией проекта.

## 4. Источники и база отчета

Отчет собран на основе следующих источников внутри репозитория и набора артефактов:

- `README.md`
- `docs/Applications.rst`
- `docs/Simulation.rst`
- `run-out/README.md`
- `run-out/chapter2_razrabotka.md`
- `run-out/chapter3_experiment.md`
- `run-out/summary-all-runs.csv`
- `run-out/per-vehicle-cam-from-ev.csv`
- `run-out/inter-cam-gaps.csv`
- `run-out/eva-*-speed-timeseries.csv`

Отдельно были перепроверены реальные target-ы сценариев и параметры запуска по:

- `src/automotive/examples/CMakeLists.txt`
- `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc`
- `src/automotive/examples/v2v-degradation-collision-nrv2x.cc`

## 5. Как устроен основной сценарий

Основной сценарий блока: `v2v-emergencyVehicleAlert-nrv2x`.

Связка работает следующим образом:

- `SUMO` отвечает за дорожную сеть, маршруты, скорости, полосы и состояние транспортных средств;
- `TraCI` синхронизирует транспортную часть и сетевую часть;
- `ns-3` и модуль `NR` моделируют беспроводной обмен по `NR-V2X Mode 2`;
- прикладная логика на стороне транспортных средств реализована в `emergencyVehicleAlert.cc`;
- метрики `PRR` и `latency` собираются через `MetricSupervisor`.

Для основного V2V-сценария используются следующие ключевые файлы:

- `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc` — главный файл сценария;
- `src/automotive/model/Applications/emergencyVehicleAlert.cc` — прикладная логика реакции на CAM от emergency vehicle;
- `src/automotive/examples/sumo_files_v2v_map/map.sumo.cfg` — конфигурация SUMO;
- `src/automotive/examples/sumo_files_v2v_map/cars.rou.xml` — маршруты транспортных средств;
- `src/automotive/examples/sumo_files_v2v_map/map.net.xml` — дорожная сеть.

### Логика EVA-сценария

В сценарии участвуют 20 транспортных средств на кольцевой дорожной сети. Автомобиль экстренных служб рассылает CAM-сообщения. Обычные транспортные средства, получившие CAM, проверяют:

- расстояние до emergency vehicle;
- близость по направлению движения.

Если расстояние меньше `75 м`, а разница по heading находится в пределах порога, то срабатывает прикладная реакция:

- если машина находится на одной полосе с emergency vehicle, она ускоряется и пытается освободить путь;
- если машина находится на другой полосе, она снижает скорость и удерживает безопасное поведение;
- если в течение `3 с` новых CAM не приходит, машина возвращается к штатному режиму.

Именно поэтому данный сценарий хорошо подходит для исследования цепочки:

`параметры канала -> сетевые метрики -> информационное состояние -> поведенческий эффект`.

## 6. Базовый цикл сборки и запуска

Рабочий каталог при запуске должен быть корнем репозитория, потому что сценарии используют относительные пути к файлам `SUMO`.

### Базовая сборка

```bash
./ns3 configure --build-profile=optimized --enable-examples --enable-tests --disable-werror
./ns3 build
```

Если нужно собирать только целевые примеры:

```bash
./ns3 build v2v-emergencyVehicleAlert-nrv2x
./ns3 build v2v-degradation-collision-nrv2x
```

### Быстрый smoke run

```bash
./ns3 run "v2v-emergencyVehicleAlert-nrv2x --simTime=30 --sumo-gui=false"
```

## 7. Серия из 6 основных EVA-экспериментов

### Матрица экспериментов

| № | Сценарий | Label | TxPower, dBm | MCS | Retx | BW, MHz | Shadowing | PenRate | PRR | Latency, ms |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| 1 | Baseline | `good` | 23 | 14 | 5 | 400 | OFF | 1.0 | 0.9916 | 11.43 |
| 2 | Medium loss | `medium` | 10 | 14 | 5 | 400 | ON | 1.0 | 0.9753 | 17.78 |
| 3 | High loss | `bad` | 5 | 20 | 5 | 400 | ON | 1.0 | 0.8993 | 29.10 |
| 4 | Very high loss | `vbad` | 0 | 20 | 1 | 10 | ON | 1.0 | 0.4868 | 33.05 |
| 5 | No retransmissions | `noretx` | 23 | 14 | 1 | 400 | ON | 1.0 | 0.9919 | 12.45 |
| 6 | Low penetration | `lowpen` | 23 | 14 | 5 | 400 | OFF | 0.3 | 0.9864 | 12.15 |

### Команды запуска

```bash
# 1. Baseline
./ns3 run "v2v-emergencyVehicleAlert-nrv2x \
  --txPower=23 \
  --mcs=14 \
  --enableChannelRandomness=false \
  --penetrationRate=1.0 \
  --simTime=100 \
  --sumo-gui=false \
  --csv-log=run-out/eva-good \
  --csv-log-cumulative=run-out/eva-good-cumul \
  --netstate-dump-file=run-out/eva-good-netstate.xml \
  --met-sup=true \
  --baseline=150"

# 2. Medium loss
./ns3 run "v2v-emergencyVehicleAlert-nrv2x \
  --txPower=10 \
  --mcs=14 \
  --enableChannelRandomness=true \
  --channelUpdatePeriod=100 \
  --penetrationRate=1.0 \
  --simTime=100 \
  --sumo-gui=false \
  --csv-log=run-out/eva-medium \
  --csv-log-cumulative=run-out/eva-medium-cumul \
  --netstate-dump-file=run-out/eva-medium-netstate.xml \
  --met-sup=true \
  --baseline=150"

# 3. High loss
./ns3 run "v2v-emergencyVehicleAlert-nrv2x \
  --txPower=5 \
  --mcs=20 \
  --enableChannelRandomness=true \
  --channelUpdatePeriod=100 \
  --penetrationRate=1.0 \
  --simTime=100 \
  --sumo-gui=false \
  --csv-log=run-out/eva-bad \
  --csv-log-cumulative=run-out/eva-bad-cumul \
  --netstate-dump-file=run-out/eva-bad-netstate.xml \
  --met-sup=true \
  --baseline=150"

# 4. Very high loss
./ns3 run "v2v-emergencyVehicleAlert-nrv2x \
  --txPower=0 \
  --mcs=20 \
  --slMaxTxTransNumPssch=1 \
  --bandwidthBandSl=10 \
  --enableChannelRandomness=true \
  --channelUpdatePeriod=100 \
  --penetrationRate=1.0 \
  --simTime=100 \
  --sumo-gui=false \
  --csv-log=run-out/eva-vbad \
  --csv-log-cumulative=run-out/eva-vbad-cumul \
  --netstate-dump-file=run-out/eva-vbad-netstate.xml \
  --met-sup=true \
  --baseline=150"

# 5. No retransmissions
./ns3 run "v2v-emergencyVehicleAlert-nrv2x \
  --txPower=23 \
  --mcs=14 \
  --slMaxTxTransNumPssch=1 \
  --enableChannelRandomness=true \
  --channelUpdatePeriod=100 \
  --penetrationRate=1.0 \
  --simTime=100 \
  --sumo-gui=false \
  --csv-log=run-out/eva-noretx \
  --csv-log-cumulative=run-out/eva-noretx-cumul \
  --netstate-dump-file=run-out/eva-noretx-netstate.xml \
  --met-sup=true \
  --baseline=150"

# 6. Low penetration
./ns3 run "v2v-emergencyVehicleAlert-nrv2x \
  --txPower=23 \
  --mcs=14 \
  --enableChannelRandomness=false \
  --penetrationRate=0.3 \
  --simTime=100 \
  --sumo-gui=false \
  --csv-log=run-out/eva-lowpen \
  --csv-log-cumulative=run-out/eva-lowpen-cumul \
  --netstate-dump-file=run-out/eva-lowpen-netstate.xml \
  --met-sup=true \
  --baseline=150"
```

## 8. Результаты по основной серии

### Сводка по метрикам

| Сценарий | PRR | Latency, ms | Avg CAM from EV | Min CAM from EV | Max CAM from EV | Median gap, ms | P95 gap, ms | Max gap, ms | Gaps > 1000 ms, % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.992 | 11.4 | 185 | 170 | 199 | 200 | 600 | 2400 | 0.3 |
| Medium loss | 0.975 | 17.8 | 171 | 157 | 199 | 400 | 1000 | 4000 | 2.2 |
| High loss | 0.899 | 29.1 | 132 | 94 | 197 | 564 | 1200 | 7936 | 7.0 |
| Very high loss | 0.487 | 33.1 | 51 | 11 | 189 | 600 | 2400 | 28500 | 14.2 |
| No retransmissions | 0.992 | 12.4 | 182 | 172 | 198 | 200 | 600 | 2400 | 0.3 |
| Low penetration | 0.986 | 12.1 | 0* | 0* | 0* | 0* | 0* | 0* | 0* |

\* Для `lowpen` в сводном `summary-all-runs.csv` поля по `CAM from EV` и gap-метрикам стоят нулевыми. Это не означает отсутствие сетевой активности в принципе; это означает, что данный derived-summary не содержит сопоставимого агрегирования для сценария с частичным оснащением. Поэтому `lowpen` нужно интерпретировать прежде всего через `PRR`, `latency` и качественный поведенческий эффект.

### Основные наблюдения

#### 1. Сетевые метрики деградируют нелинейно

- Переход от `23 dBm` к `10 dBm` снижает `PRR` умеренно: с `0.992` до `0.975`.
- Дальнейшее ужесточение параметров, особенно рост `MCS` и ослабление канала, ускоряет падение качества.
- Экстремальная конфигурация `vbad` приводит к `PRR = 0.487`, то есть к потере более половины пакетов.

#### 2. Latency растет быстрее, чем кажется по одному только PRR

- В `Baseline` средняя односторонняя задержка составляет `11.4 ms`.
- В `Medium loss` она растет до `17.8 ms`.
- В `High loss` и `Very high loss` достигает `29.1 ms` и `33.1 ms`.

Это важно, потому что поведение приложения зависит не только от факта приема сообщения, но и от своевременности этого приема.

#### 3. Информационное состояние деградирует сильнее, чем агрегированный PRR

- В baseline каждый автомобиль получает в среднем `185` CAM от emergency vehicle.
- В `High loss` это число падает до `132`.
- В `Very high loss` среднее падает до `51`, а разброс становится очень большим: одни машины получают почти полный поток, другие — лишь малую его часть.

С практической точки зрения это означает, что при деградированном канале транспортные средства оказываются в разных информационных состояниях и начинают принимать решения на разной базе данных.

#### 4. Межприемные интервалы становятся длиннее и опаснее

По `inter-cam-gaps.csv` видно, что:

- baseline держится около медианы `200 ms`;
- при ухудшении канала медиана смещается к `400-600 ms`;
- в `vbad` максимальный observed gap достигает `28.5 s`.

Это уже не просто ухудшение статистики приема, а реальный риск устаревания информации для прикладной логики с таймаутом `3 с`.

#### 5. Поведение устойчиво при умеренной деградации

По вашим главам и speed-timeseries видно, что поведенческий эффект почти не меняется между `good`, `medium` и `bad`, несмотря на ухудшение `PRR` и latency.

Практический вывод:

- пока надежная зона связи перекрывает зону прикладной реакции, поведение остается устойчивым;
- выраженная поведенческая деградация начинается, когда потери заходят в критическую зону принятия решения.

#### 6. Low penetration — отдельный тип деградации

Сценарий `lowpen` показывает важный отдельный эффект:

- связь между оснащенными машинами остается хорошей;
- но значительная часть транспортного потока просто не оснащена V2X.

С точки зрения прикладного эффекта это иной режим деградации, чем плохой канал: не потеря качества связи, а неравномерная доступность самой функции.

## 9. Верификация collision-сценария

Для дополнительной проверки и демонстрации влияния связи на итог поведения был откалиброван отдельный сценарий:

- target: `v2v-degradation-collision-nrv2x`
- файл сценария: `src/automotive/examples/v2v-degradation-collision-nrv2x.cc`
- маршруты: `src/automotive/examples/sumo_files_v2v_map/cars_collision.rou.xml`
- конфигурация SUMO: `src/automotive/examples/sumo_files_v2v_map/map_collision.sumo.cfg`

В этом сценарии:

- коэффициент проникновения фиксируется на `1.0`;
- обычные автомобили не полагаются только на штатную модель поведения;
- порог прикладной реакции уменьшается до `warningDistance = 9.65`;
- проверяется, успевает ли лидирующая машина освободить полосу до подхода emergency vehicle.

### Good-case

```bash
./ns3 run "v2v-degradation-collision-nrv2x \
  --sumo-gui=true \
  --simTime=12"
```

Ожидаемое поведение:

- столкновение не происходит;
- `DENM` не отправляется;
- лидирующая машина успевает освободить конфликтную полосу.

### Bad-case

```bash
./ns3 run "v2v-degradation-collision-nrv2x \
  --sumo-gui=true \
  --simTime=12 \
  --txPower=-10 \
  --mcs=24 \
  --bandwidthBandSl=100 \
  --slMaxTxTransNumPssch=1 \
  --enableChannelRandomness=true \
  --channelUpdatePeriod=100"
```

Ожидаемое поведение:

- emergency vehicle сталкивается с лидирующим автомобилем;
- в логике фиксируется `DENM-SENT:1`;
- после момента столкновения обе машины остаются заблокированными в полосе.

Практическая ценность этого сценария в том, что он дает более наглядный и бинарный исход: хороший канал и плохой канал приводят к разным результатам на уровне поведения, а не только на уровне метрик.

## 10. Каталог ключевых сценариев репозитория

Ниже приведен краткий рабочий каталог основных сценариев, на которые стоит ориентироваться в текущем репозитории.

### V2V-блок

| Scenario | Назначение | Как запускать |
|---|---|---|
| `v2v-emergencyVehicleAlert-nrv2x` | Основной NR-V2X EVA-сценарий | `./ns3 run "v2v-emergencyVehicleAlert-nrv2x"` |
| `v2v-emergencyVehicleAlert-80211p` | 802.11p версия EVA | `./ns3 run "v2v-emergencyVehicleAlert-80211p"` |
| `v2v-emergencyVehicleAlert-ltev2x` | LTE-V2X версия EVA | `./ns3 run "v2v-emergencyVehicleAlert-ltev2x"` |
| `v2v-degradation-collision-nrv2x` | Custom collision-сценарий для верификации деградации | `./ns3 run "v2v-degradation-collision-nrv2x --simTime=12"` |
| `v2v-simple-cam-exchange-80211p` | Базовый обмен CAM по 802.11p | `./ns3 run "v2v-simple-cam-exchange-80211p"` |
| `v2v-congestion-80211p` | Нагрузка и перегрузка канала в 802.11p | `./ns3 run "v2v-congestion-80211p"` |

Примечание: в документации репозитория встречается имя `v2v-emergencyVehicleAlert-cv2x`, но в текущем `src/automotive/examples/CMakeLists.txt` target называется `v2v-emergencyVehicleAlert-ltev2x`.

### V2I-блок

| Scenario | Назначение | Как запускать |
|---|---|---|
| `v2i-areaSpeedAdvisor-80211p` | V2I-сценарий с RSU и advisory-логикой на 802.11p | `./ns3 run "v2i-areaSpeedAdvisor-80211p"` |
| `v2i-areaSpeedAdvisor-lte` | LTE-вариант area speed advisor | `./ns3 run "v2i-areaSpeedAdvisor-lte"` |
| `v2i-emergencyVehicleWarning-80211p` | V2I warning-сценарий | `./ns3 run "v2i-emergencyVehicleWarning-80211p"` |
| `v2i-trafficManager-80211p` | Traffic Manager на 802.11p | `./ns3 run "v2i-trafficManager-80211p"` |
| `v2i-trafficManager-LTE` | Traffic Manager на LTE | `./ns3 run "v2i-trafficManager-LTE"` |

### Coexistence и interference mode

Для `v2v-coexistence-80211p-nrv2x` сначала нужно включить специальный режим:

```bash
./switch_ms-van3t-interference.sh on
./ns3 build v2v-coexistence-80211p-nrv2x
./ns3 run "v2v-coexistence-80211p-nrv2x"
./switch_ms-van3t-interference.sh off
```

Этот режим затрагивает модифицированные файлы в нескольких модулях, поэтому его нужно воспринимать не как обычный runtime flag, а как отдельный режим работы репозитория.

### Sionna

Для Sionna-сценариев сначала поднимается Python server, потом запускается ns-3 сценарий.

Пример:

```bash
cd src/sionna
python3 -u sionna_server_script.py --local-machine --verbose
```

После этого из корня репозитория:

```bash
./ns3 run "v2v-cam-exchange-sionna-80211p"
./ns3 run "v2v-cam-exchange-sionna-nrv2x"
./ns3 run "v2v-cam-exchange-sionna-ltev2x"
```

### CARLA

Если репозиторий находится в режиме CARLA/OpenCDA:

```bash
./ns3 run "v2v-carla-80211p"
./ns3 run "v2v-carla-nrv2x"
```

### Emulator

Эмуляционный режим запускается через:

```bash
./ns3 run "v2x-emulator --interface=<interface name>"
```

Здесь `<interface name>` должен соответствовать реальному сетевому интерфейсу машины.

## 11. Структура выходных данных

### Ключевые summary-файлы

| Файл | Что содержит | Как использовать |
|---|---|---|
| `summary-all-runs.csv` | Сводка по параметрам, PRR, latency и derived-метрикам | Главная таблица для отчета и графиков |
| `per-vehicle-cam-from-ev.csv` | Сколько CAM от emergency vehicle приняла каждая машина; покрывает `good`, `medium`, `bad`, `vbad`, `noretx` | Box plot / распределение информированности |
| `inter-cam-gaps.csv` | Интервалы между соседними CAM от emergency vehicle; покрывает `good`, `medium`, `bad`, `vbad` | CDF межприемных интервалов |
| `eva-*-speed-timeseries.csv` | Скорость и lane по времени для выбранных сценариев | Графики поведения |

### Raw-артефакты

| Группа файлов | Что содержит |
|---|---|
| `eva-*-cumul.csv` | Агрегированные PRR/latency из конкретного прогона |
| `eva-*-vehX-CAM.csv` | Детализация приема CAM по конкретному автомобилю |
| `eva-*-netstate.xml` | Полный дамп состояния транспортных средств из `SUMO` |
| `*-netstate.xml` по collision-серии | Проверка исходов для good/bad и промежуточных конфигураций |

### Практическая интерпретация

- если нужно быстро показать итог — достаточно `summary-all-runs.csv`;
- если нужно показать неоднородность информированности — нужен `per-vehicle-cam-from-ev.csv`;
- если нужно показать устаревание информации — нужен `inter-cam-gaps.csv`;
- если нужно показать, что деградация дошла до поведения — нужны `eva-*-speed-timeseries.csv` и при необходимости `netstate.xml`.

## 12. Ограничения

### Ограничения текущего пакета

- Пакет ориентирован на уже полученные результаты; код сценариев в рамках этой работы не менялся.
- Основной глубокий анализ сделан только по EVA- и collision-сценариям, потому что именно по ним в `run-out` есть полноценные артефакты и готовый аналитический материал.
- Каталог остальных сценариев репозитория носит обзорный характер и не означает, что по каждому из них уже выполнена такая же серия экспериментов.

### Ограничения самих экспериментов

- Топология сценария детерминированная и относительно простая;
- сценарий привязан к конкретной прикладной логике EVA;
- часть derived-файлов не содержит полного набора рядов для всех сценариев;
- поведенческие выводы нужно интерпретировать вместе с особенностями `SUMO` и прикладной логики, а не как универсальный закон для всех V2X-приложений.

## 13. Что делать дальше

Следующий логичный шаг после этого пакета:

1. Использовать текущий EVA-блок как baseline для сравнения с `Simu5G`.
2. Повторить близкую по смыслу матрицу экспериментов в `Simu5G`, насколько это позволяет стек.
3. Сопоставить:
   - управляемость параметров;
   - доступные метрики;
   - удобство воспроизведения;
   - пригодность для V2X-сценариев с поведенческой обратной связью.
4. Подготовить unified comparison table `VaN3Twin/ns-3 vs Simu5G`.

Таким образом, текущая работа закрывает не только документирование результатов, но и формирует аккуратную базу для следующего этапа интеграционного и сравнительного анализа.

## 14. Что входит в готовый пакет

В папке `run-out/cycle7_fizulin_av/` лежат:

- `cycle7_assignment.md` — блок для распределения задач;
- `tracker_card.md` — текст карточки для трекера;
- `notion_report.md` — этот отчет;
- `materials_manifest.md` — опись пакета;
- `source_digest.md` — конспект происхождения материалов;
- копии компактных summary-артефактов и исходных текстовых наработок.

Этого достаточно, чтобы:

- вставить блок в документ по циклу №7;
- завести карточку в трекере;
- опубликовать отчет на странице в Notion;
- передать команде воспроизводимую базу для дальнейшей работы.
