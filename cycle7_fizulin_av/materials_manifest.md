# Materials Manifest

## Что находится в этой папке

Папка `run-out/cycle7_fizulin_av/` содержит итоговые документы по задаче Физулина А.В. на цикл №7 и компактные артефакты, на которых основан отчет.

## Итоговые документы

| Файл | Назначение | Статус |
|------|------------|--------|
| `cycle7_assignment.md` | Готовый блок для документа с распределением задач на цикл №7 | Новый deliverable |
| `tracker_card.md` | Готовый текст карточки для трекера | Новый deliverable |
| `notion_report.md` | Большой отчет для Notion | Новый deliverable |
| `materials_manifest.md` | Опись пакета материалов | Новый deliverable |
| `source_digest.md` | Краткий конспект происхождения материалов | Новый deliverable |

## Скопированные компактные материалы-основания

| Файл в этой папке | Исходный путь | Роль в отчете | Что делать при публикации |
|------|------|------|------|
| `README.md` | `run-out/README.md` | Краткая англоязычная выжимка по EVA-экспериментам и командам запуска | Можно приложить как техническую заметку |
| `chapter2_razrabotka.md` | `run-out/chapter2_razrabotka.md` | Методика, матрица экспериментов, система метрик | Использовать как методическую основу |
| `chapter3_experiment.md` | `run-out/chapter3_experiment.md` | Развернутые результаты и аналитика | Использовать как основу раздела Results |
| `summary-all-runs.csv` | `run-out/summary-all-runs.csv` | Главная сводная таблица по шести прогонам | Прикладывать/линковать обязательно |
| `per-vehicle-cam-from-ev.csv` | `run-out/per-vehicle-cam-from-ev.csv` | Распределение числа CAM от emergency vehicle по машинам; покрывает `good`, `medium`, `bad`, `vbad`, `noretx` | Прикладывать при построении box plot |
| `inter-cam-gaps.csv` | `run-out/inter-cam-gaps.csv` | Интервалы между соседними CAM от emergency vehicle; покрывает `good`, `medium`, `bad`, `vbad` | Прикладывать при построении CDF |
| `eva-good-speed-timeseries.csv` | `run-out/eva-good-speed-timeseries.csv` | Временные ряды скоростей для baseline | Опционально прикладывать |
| `eva-bad-speed-timeseries.csv` | `run-out/eva-bad-speed-timeseries.csv` | Временные ряды скоростей для high loss | Опционально прикладывать |
| `eva-vbad-speed-timeseries.csv` | `run-out/eva-vbad-speed-timeseries.csv` | Временные ряды скоростей для very high loss | Опционально прикладывать |
| `eva-lowpen-speed-timeseries.csv` | `run-out/eva-lowpen-speed-timeseries.csv` | Временные ряды скоростей для low penetration | Опционально прикладывать |
| `chatgpt-prompt-graphs.md` | `run-out/chatgpt-prompt-graphs.md` | Готовый prompt для генерации графиков по CSV | Использовать как вспомогательный инструмент |

## Важные raw-артефакты, которые не дублировались массово

Во избежание раздувания пакета сотнями файлов сырые артефакты оставлены на исходном месте в `run-out/`.

| Группа файлов | Где лежит | Назначение |
|------|------|------|
| `run-out/eva-*-veh*-CAM.csv` | исходная папка `run-out/` | Детализация приема CAM по каждому ТС |
| `run-out/eva-*-netstate.xml` | исходная папка `run-out/` | Полный `SUMO netstate dump` по основным EVA-прогонам |
| `run-out/*-netstate.xml` по collision-настройкам | исходная папка `run-out/` | Проверка good/bad режимов и промежуточных тюнингов collision-сценария |
| `run-out/*veh*-CAM.csv` по collision-настройкам | исходная папка `run-out/` | Детализация обмена сообщениями для collision-серии |

## Что прикладывать в Notion в первую очередь

1. `notion_report.md`
2. `summary-all-runs.csv`
3. `per-vehicle-cam-from-ev.csv`
4. `inter-cam-gaps.csv`
5. При необходимости: `eva-good-speed-timeseries.csv`, `eva-vbad-speed-timeseries.csv`, `eva-lowpen-speed-timeseries.csv`

## Замечания

- В папку специально не переносились все `netstate.xml` и все `veh*-CAM.csv`, потому что это технические raw-логи, а не итоговые deliverables.
- Не все derived-CSV покрывают одинаковый набор прогонов; это отражено в описаниях файлов выше.
- Если для публикации в Notion понадобятся отдельные XML- или per-vehicle CSV-файлы, их лучше добавлять точечно под конкретный график или приложение, а не копировать весь массив целиком.
