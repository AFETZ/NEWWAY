# runs/

Централизованное хранилище evidence-прогонов сценариев. Каждая дата — отдельная папка `<YYYY-MM-DD>/`, внутри — конкретные run-директории с `*.log`, `artifacts/`, `figures/`, `run_summary.csv`, `REPORT.md`.

## Структура

- `runs/<YYYY-MM-DD>/<run_dir>/` — данные одного прогона
- `runs/chatgpt_exports/` — компактные export-бандлы (опциональны, формируются `EXPORT_RESULTS=1` в run.sh сценариев)

## Постобработка

Скрипты лежат в `tools/`:

```bash
# Дипломные story-графики по lane-change кейсу
./.venv/bin/python tools/plots/build_valid_scenario_story_plots.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# Интуитивные CSV-only графики
./.venv/bin/python tools/plots/build_valid_scenario_intuitive_plots.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# Drop → decision timeline
./.venv/bin/python tools/plots/build_drop_decision_timeline.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# Полный аудит логов по всем прогонам
./.venv/bin/python tools/analysis/analyze_all_logs.py \
  --root runs --out-dir runs --tag <YYYY-MM-DD>
```

## Управление объёмом

`runs/` может разрастаться. Правила:

1. Сохраняем только прогоны, которые упомянуты в защитных артефактах (тексты ВКР, статьи, отчёты).
2. Лишние черновые прогоны — переносим в `archive/<date>/runs/` (не удаляем).
3. Никогда не лезем руками в чужие даты — только добавляем новые.
