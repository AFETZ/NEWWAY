# REPO_LAYOUT.md — карта репозитория NEWWAY

Последняя реорганизация: 2026-05-03 (см. `docs/superpowers/specs/2026-05-03-repo-cleanup-design.md`).

## Корневые директории

| Путь | Назначение |
|---|---|
| `src/` | Overlay поверх ns-3 / VaN3Twin: C++ модули симулятора. Изменять осторожно. |
| `docs/` | Документация ns-3 upstream (rst). |
| `experiments/` | Все сценарии и эксперименты. См. `experiments/README.md`. |
| `runs/` | Evidence-прогоны (по датам). См. `runs/README.md`. |
| `reports/` | Учебные/рабочие отчёты (cycle7, scenario manager). |
| `conference/` | Финальные docx статей. |
| `tools/` | Генераторы графиков, analyzers, ВКР-сборка. См. `tools/README.md`. |
| `tests/` | Базовые тесты. |
| `scripts/` | Operational helpers (sync overlay, docker run и т.п.). |
| `emulation-support/` | CARLA / OpenCDA вспомогательные файлы. |
| `docker/` | Dockerfile-ы. |
| `tmp/` | Временные данные (gitignored). |
| `archive/` | **Не читать ИИ.** Замороженные тексты ВКР, дубликаты, audit-история. |
| `.venv/`, `.venv_sionna/`, `.venv_docs/` | Python virtualenvs (gitignored). |
| `.bootstrap-ns3/` | Sandboxed ns-3 build (gitignored). |
| `.optix-wsl/` | NVIDIA OptiX runtime (gitignored). |

## Корневые файлы

| Файл | Назначение |
|---|---|
| `README.md` | Описание проекта (от upstream). |
| `AGENTS.md` | Правила для всех ИИ-агентов. |
| `CLAUDE.md` | Указатель на AGENTS.md. |
| `REPO_LAYOUT.md` | Этот файл. |
| `Makefile`, `LICENSE`, `AUTHORS`, `CHANGES.md`, `RELEASE_NOTES.md` | Standard project files (от upstream). |
| `DEVELOPMENT.md` | Разработческие заметки. |
| `adapt_files.py`, `install_carla_opencda.sh`, `enable_v2x_emulator.sh`, `sandbox_builder.sh`, `switch_*.sh` | Operational scripts (от upstream + локальные). |
| `docker-compose.gpu.yml`, `*.cflags`, `*.cxxflags` | Build configs. |

## Куда что класть

| Что | Куда |
|---|---|
| Новый сценарий | `experiments/<name>/{scripts,docs,tools,results}/` |
| Новый прогон evidence | `runs/<YYYY-MM-DD>/<run_dir>/` |
| Новый аналитический скрипт | `tools/{plots,analysis,vkr}/` |
| Учебный/рабочий отчёт | `reports/<name>/` |
| Финальный docx статьи | `conference/` |
| Старая версия / транзишнл / черновик | `archive/<YYYY-MM-DD>/superseded/...` |
