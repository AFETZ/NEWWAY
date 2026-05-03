# tools/

Инструменты разработки и анализа. Не путать с in-experiment tools (`experiments/<name>/tools/`), которые специфичны для одного сценария.

## Структура

- `plots/` — генераторы графиков и анимаций (`build_*_plots.py`, `make_plots.py`, `render_*.py`, `visualize_*.py`, `plot_*.py`).
- `analysis/` — analyzers и aggregators (`analyze_*.py`, `compare_*.py`, `export_*.py`).
- `vkr/` — генераторы ВКР: фигуры (`generate_chapter*_figures.py`), сборка docx/pdf (`build_final_vkr.py`, `render_final_vkr_pdf.py`), bibliography (`verify_bibliography.py`), IEEE статья (`generate_ieee_paper.py`).
- `scenario_manager/` — модуль для централизованного запуска / sweep сценариев.
- `results_pipeline/` — пайплайн агрегации результатов.

## Типичные команды

```bash
# График из конкретного прогона
./.venv/bin/python tools/plots/build_valid_scenario_story_plots.py --run-dir runs/2026-03-04/<run>

# Аудит всех логов
./.venv/bin/python tools/analysis/analyze_all_logs.py --root runs --out-dir runs --tag <date>

# Регенерация фигур ВКР главы 3
./.venv/bin/python tools/vkr/generate_chapter3_figures.py
```

## Среды

В репозитории есть `.venv/`, `.venv_sionna/`, `.venv_docs/`. Большинство скриптов работают с `.venv/`.
