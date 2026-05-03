# Evidence-прогоны

## Обзор

Директория `runs/` — централизованное хранилище evidence-прогонов сценариев. Каждая дата — отдельная папка, внутри — конкретные run-директории с логами, артефактами, фигурами и отчётами.

## Структура

```
runs/
├── 2026-02-18/          # Ранние sweep-прогоны
├── 2026-02-19/
├── 2026-02-20/
├── 2026-02-21/
├── 2026-02-27/
├── 2026-03-02/
├── 2026-03-04/          # Ключевые прогоны truck_lane_change
├── 2026-03-20/          # Intersection crash прогоны
├── chatgpt_exports/     # Компактные бандлы для анализа
└── README.md
```

## Содержимое run-директории

Каждый прогон (`runs/<YYYY-MM-DD>/<run_dir>/`) содержит:

| Файл | Описание |
|---|---|
| `*.log` | Логи симуляции ns-3/SUMO |
| `artifacts/` | Результаты: collision XML, decision timeline, causal reports |
| `figures/` | Сгенерированные графики |
| `run_summary.csv` | Компактная сводка прогона |
| `REPORT.md` | Описание прогона для воспроизведения |

## Постобработка

```bash
# Дипломные story-графики
./.venv/bin/python tools/plots/build_valid_scenario_story_plots.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# CSV-only графики
./.venv/bin/python tools/plots/build_valid_scenario_intuitive_plots.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# Drop → decision timeline
./.venv/bin/python tools/plots/build_drop_decision_timeline.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# Полный аудит логов
./.venv/bin/python tools/analysis/analyze_all_logs.py \
  --root runs --out-dir runs --tag <YYYY-MM-DD>
```

## Chatgpt Exports

`runs/chatgpt_exports/` содержит компактные export-бандлы, формируемые с `EXPORT_RESULTS=1` в run.sh сценариев. Предназначены для быстрого анализа.

## Правила управления

1. **Сохранять** только прогоны, упомянутые в защитных артефактах (тексты ВКР, статьи, отчёты)
2. **Лишние** черновые прогоны переносить в `archive/<date>/runs/` (не удалять!)
3. **Никогда** не модифицировать чужие даты — только добавлять новые

## Воспроизведение

Для воспроизведения конкретного прогона:
1. Откройте `REPORT.md` в директории прогона
2. Следуйте инструкциям по настройке окружения
3. Запустите указанный скрипт с параметрами из отчёта
