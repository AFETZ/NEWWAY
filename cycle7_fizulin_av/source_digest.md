# Source Digest

## Что взято из репозитория

### Код и реальные точки запуска

- Названия target-ов взяты из `src/automotive/examples/CMakeLists.txt`.
- Параметры и структура основных сценариев проверены по:
  - `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc`
  - `src/automotive/examples/v2v-degradation-collision-nrv2x.cc`
- Прикладная логика EVA и collision подтверждалась по:
  - `src/automotive/model/Applications/emergencyVehicleAlert.cc`
  - `src/automotive/model/Applications/degradationCollision.cc`

### Пользовательская документация репозитория

- Общие инструкции по сборке и запуску взяты из `README.md`.
- Описание жизненного цикла сценария и роли `MetricSupervisor` взято из `docs/Simulation.rst`.
- Описания V2V- и V2I-примеров взяты из `docs/Applications.rst` и `README.md`.
- Подсказки по запуску `Sionna`, `coexistence`, `CARLA` и `emulator` взяты из `README.md` и `CODEX.md`.

## Что взято из ваших наработок

- Методическая часть и постановка экспериментов взяты из `run-out/chapter2_razrabotka.md`.
- Основные результаты и аналитические выводы взяты из `run-out/chapter3_experiment.md`.
- Краткая сводка EVA-экспериментов и готовые команды запуска взяты из `run-out/README.md`.
- Численные итоговые значения взяты из `run-out/summary-all-runs.csv`.
- Дополнительные derived-таблицы взяты из:
  - `run-out/per-vehicle-cam-from-ev.csv`
  - `run-out/inter-cam-gaps.csv`
  - `run-out/eva-*-speed-timeseries.csv`

## Что было синтезировано при упаковке

- Новый блок распределения задач для цикла №7.
- Текст карточки для трекера в рабочем формате.
- Большой Notion-ready отчет, который собирает кодовую, методическую и результативную части в один документ.
- Опись материалов и конспект происхождения источников.
- Каталог ключевых сценариев репозитория с короткими командами запуска.

## Важная оговорка по названиям сценариев

- В `README.md` и `docs/Applications.rst` для LTE-V2X варианта V2V EVA встречается имя `v2v-emergencyVehicleAlert-cv2x`.
- В текущем дереве сборки, проверенном по `src/automotive/examples/CMakeLists.txt`, target называется `v2v-emergencyVehicleAlert-ltev2x`.
- В итоговом пакете приоритет отдан текущим именам target-ов из репозитория, чтобы команды были ближе к фактической конфигурации проекта.

## Что не добавлялось заново

- Код сценариев не менялся.
- Метрики и результаты не пересчитывались заново; использовались уже существующие артефакты из `run-out/`.
- Большой массив raw-файлов не копировался повторно, а был оставлен на исходном месте и перечислен в `materials_manifest.md`.

