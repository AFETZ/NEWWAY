# Манифест артефактов по Web UI

## Исходные файлы реализации

| Путь | Роль |
|---|---|
| `tools/scenario_manager/app.py` | основной Streamlit UI |
| `tools/scenario_manager/scenarios.py` | реестр сценариев, параметров и метаданных |
| `tools/scenario_manager/runner.py` | запуск сценариев и потоковый лог |
| `tools/scenario_manager/visualizer.py` | построение графиков и dashboards |
| `tools/scenario_manager/launch.sh` | launcher локального UI |
| `tools/scenario_manager/README.md` | документация по назначению и запуску |
| `tests/test_scenario_manager.py` | базовые unit-тесты UI-контракта |

## Evidence-подтверждения

| Локальный файл | Что подтверждает |
|---|---|
| `evidence/test_scenario_manager.txt` | успешный прогон 5 unit-тестов |
| `evidence/streamlit_launch_probe.txt` | реальный локальный старт Streamlit UI |
| `evidence/streamlit_http_probe.txt` | HTTP `200 OK` от поднятого UI |
