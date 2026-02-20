# Scenario Runs

Каталог для воспроизводимых прогонов сценариев.

- Каждая дата хранится в отдельной папке: `analysis/scenario_runs/<YYYY-MM-DD>/`
- Внутри:
  - `*.log` — stdout/stderr конкретных запусков
  - `artifacts/` — SQLite/CSV и дополнительные выходные файлы сценариев
  - `figures/` — автоматически сгенерированные графики по сценариям
  - `run_summary.csv` — агрегированные KPI по запущенным сценариям
  - `REPORT.md` — интерпретация результатов под исследовательскую задачу

## Полезные утилиты

- `analysis/scenario_runs/make_plots.py` — построение графиков из `artifacts/`.
- `analysis/scenario_runs/analyze_netstate_collision_risk.py` — safety-прокси (`min gap`, `min TTC`, risky events) из SUMO `netstate`.
- `analysis/scenario_runs/compare_incident_baseline_loss.py` — сравнительный baseline/lossy таймлайн (drop ratio, control actions, gap/TTC, collisions).
- `analysis/scenario_runs/export_results_bundle.py` — дублирование графиков/логов/summary в компактный export-бандл.
- `scenarios/v2v-emergencyVehicleAlert-nrv2x/run_loss_sweep.sh` — готовый sweep baseline/lossy для сценария с реакцией на экстренное авто.

Для построения графиков нужен `matplotlib` (в этом репозитории используется `./.venv/bin/python`).

## Export-папка для выгрузки

- По умолчанию `run.sh` сценариев и `run_loss_sweep.sh` создают дубликат результатов в:
  `analysis/scenario_runs/chatgpt_exports/<relative_run_path>/`
- Внутри лежит `EXPORT_MANIFEST.csv` со списком выгруженных файлов.
- Отключение: `EXPORT_RESULTS=0`.
