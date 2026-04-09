# Оформление воспроизводимых сценариев NEWWAY, доказательных артефактов и подробного отчета по V2X-экспериментам

Подготовлен и систематизирован пакет материалов по наработкам в репозитории `NEWWAY` для последующей передачи в `Notion`.

Выполненные блоки работ:

- собрана карта репозитория и сценариев `scenarios/*`, `valid_*`, `my_scenarios/*`, `raw_experiments/*`
- оформлены команды запуска, зависимости и структура выходных артефактов
- зафиксированы пользовательские и валидированные кейсы:
  - `truck_lane_change_scenario`
  - `intersection_crash_scenario`
  - подготовленные контуры `compare_tech`, `cpm_perception_scenario`, `intersection_radar_comm_scenario`
- собраны подтвержденные результаты по lane-change и intersection кейсам
- встроен дополнительный EVA-блок из 6 прогонов `v2v-emergencyVehicleAlert-nrv2x` с derived CSV по `PRR`, `latency`, `CAM from EV` и `inter-CAM gaps`
- добавлен low-level блок по raw `5G-LENA / cttc-nr-v2x-demo-simple` с SQLite inventory и sample CSV-экспортами
- описаны аналитические скрипты, export-бандлы и `results_pipeline`
- подготовлен подробный отчет с таблицами, графиками, артефактами и ограничениями

Ключевые результаты:

- оформлен подробный отчет для `Notion`
- собран пакет evidence-артефактов `CSV/PNG/GIF`
- добавлена отдельная подтвержденная EVA-серия с 6 прогонами и поведенческими timeseries
- добавлен raw dataset-блок по `cttc-nr-v2x-demo-simple` для low-level трассировки PHY/MAC событий
- подготовлена карта сценариев и команд запуска
- выделены подтвержденные численные результаты и ограничения

Оценка затраченных часов: `48 ч`

Ссылка на отчет в Notion: `https://www.notion.so/33dd56dc3dd681838105effc04f8a31b`
