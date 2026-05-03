# Пакет материалов по циклу 7 — Физулин А.В.

Этот каталог содержит локально собранный пакет материалов для оформления
персональной задачи на цикл 7, карточки в трекере и подробного отчета для
страницы в Notion по наработкам в репозитории `NEWWAY`.

## Состав пакета

- `cycle7_task.md` — задача на цикл 7 в формате распределения задач.
- `tracker_card.md` — короткая карточка для трекера.
- `notion_report.md` — подробный технический отчет для Notion.
- `hours_estimate.md` — оценка затраченных часов с разбивкой.
- `artifact_manifest.md` — перечень исходных материалов и путей.
- `figures_tables_manifest.md` — список фигур и таблиц для отчета.
- `evidence/` — компактные копии ключевых CSV, PNG и GIF.

Дополнительно в пакет встроен отдельный EVA-блок из каталога
`cycle7_fizulin_av/`:

- серия из 6 прогонов `v2v-emergencyVehicleAlert-nrv2x`;
- derived-таблицы по `PRR`, `latency`, `CAM from EV`, `inter-CAM gaps`;
- временные ряды скоростей для поведенческого сравнения режимов.

Также в пакет добавлен low-level блок из каталога `1/`:

- raw SQLite dataset по стоковому `cttc-nr-v2x-demo-simple`;
- `dataset_inventory.csv` с инвентарем таблиц и временных диапазонов;
- sample CSV-экспорты `pktTxRx` и `psschRxUePhy` для быстрого просмотра без SQLite.

## Как использовать

1. Открыть `notion_report.md` и использовать его как основной текст отчета.
2. Открыть `cycle7_task.md` и `tracker_card.md` для переноса в задачу и трекер.
3. При публикации в Notion вставить картинки из `evidence/img/` и при
   необходимости приложить таблицы/CSV из `evidence/csv/`.
4. При необходимости свериться с `artifact_manifest.md`, если нужно найти
   исходный артефакт в репозитории или в run-директориях.

## Опубликовано в Notion

- основной отчет:
  `https://www.notion.so/33dd56dc3dd681838105effc04f8a31b`
- приложение A — артефакты, figures и evidence-манифест:
  `https://www.notion.so/33dd56dc3dd681f2a588e38243171052`
- приложение B — задача цикла, карточка и оценка часов:
  `https://www.notion.so/33dd56dc3dd68104b244c2dc3bc2439f`

## Примечание по источникам

- Основные подтвержденные численные результаты в этом пакете берутся из:
  - `my_scenarios/truck_lane_change_scenario/output/*`
  - `my_scenarios/intersection_crash_scenario/output/*`
  - `analysis/scenario_runs/chatgpt_exports/*`
- Основные иллюстрации для lane-change кейса берутся из:
  - `analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2/`
- Основные иллюстрации для intersection кейса берутся из:
  - `analysis/scenario_runs/2026-03-20/intersection_crash-111609/`

## Итоговая оценка

- Оценка затраченных часов: `48 ч`
