# Repo Cleanup & Reorganization — Design

**Date:** 2026-05-03
**Branch:** `bootstrap/dev-onboarding`
**Goal:** Полная переразбивка рабочего пространства NEWWAY в «сдаваемый и защищаемый» вид: все эксперименты — под одной крышей, evidence — централизованно, инструменты — в `tools/`, ВСЕ тексты ВКР — в архив, агентские .md явно скрывают `archive/` от ИИ.

## Context

Репозиторий — overlay вокруг VaN3Twin/ns-3 для исследования по влиянию потерь NR-V2X на поведение CAV. Накопились наслоения:

- 4 «валидированные» scenario-папки (`valid_*`) и их 4 алиаса в `my_scenarios/` (5-строчные wrapper-ы с дипломно-понятными именами).
- 5+ launcher-папок в `scenarios/` (operational examples).
- `hardwork/` — свежая (apr 15) активная переработка intersection-кейса.
- `raw_experiments/`, `strict_sionna_vkr/` — отдельные experiment-зоны.
- `analysis/` (824MB) — мешанина: тексты ВКР, evidence (`scenario_runs/`), скрипты-генераторы, smoke-runs, docx-черновики, GIF-арт, отдельные эксперименты (`mode2_loss/`).
- `cycle7_fizulin_av/` — отчёт цикла практики, дублируется в `archive/legacy/` (отличие: archive имеет `lena_db_dataset/`, live имеет более свежие .md).
- `conference/` — 5 docx, две явно «transitional» версии.
- `WORKSPACE_MAP.md` устарел (упоминает `vkr_final/`, `output/`, которых нет на диске).
- Единственный агентский файл — `codex.md`.

## Decisions (зафиксированы по Q1–Q5)

- **Q1.** Тексты ВКР (главы, bibliography, appendices, tables, conclusion, front_matter, inventory, PLAN, CHAPTER_DRAFT, `valid_scenario/VKR_SCENARIO_TEXT.md`, `analysis/vkr_extract/`, `analysis/chapter1_reference_fix_package.{md,docx}`, `analysis/*.docx` черновики) — **в архив целиком**. В репозитории остаются только скрипты-генераторы. Ссылки внутри архивных текстов **не обновляются** (текст замороженный).
- **Q2.** Evidence из `analysis/scenario_runs/` → корневой `runs/`. Один централизованный путь.
- **Q3.** `cycle7_fizulin_av/` (live) и `archive/legacy/.../cycle7_variant_from_root_1/` сливаются: live `.md` приоритетнее, `lena_db_dataset/` из архивной копии добавляется. Результат → `reports/cycle7_fizulin_av/`. Архивная копия в `archive/legacy/` остаётся как есть (исторический snapshot).
- **Q4.** Один большой коммит. Атомарно, легче revert.
- **Q5.** `WORKSPACE_MAP.md` уходит в архив, в корне создаётся новый `README.md`-раздел или отдельная карта `REPO_LAYOUT.md`.

## Target structure

```
NEWWAY/
├── README.md, LICENSE, Makefile, AUTHORS, CHANGES.md, RELEASE_NOTES.md, ...   # как было
├── REPO_LAYOUT.md                         # NEW: карта репозитория (заменяет WORKSPACE_MAP.md)
├── AGENTS.md                              # NEW: инструкции для ИИ-агентов (Claude/Codex/Gemini)
├── CLAUDE.md → AGENTS.md                  # NEW: ссылка/копия для совместимости
├── src/                                   # ns-3/VaN3Twin overlay (НЕ ТРОГАЕМ)
├── docs/                                  # ns-3 official docs (НЕ ТРОГАЕМ)
├── tools/                                 # ВСЕ скрипты-инструменты
│   ├── README.md                          # карта инструментов
│   ├── plots/                             # build_*_plots.py, plot_*.py, render_*.py
│   ├── analysis/                          # analyze_*.py, summarize_runs.py, build_*_summary.py
│   ├── vkr/                               # build_final_vkr.py, generate_chapter3_figures.py,
│   │                                       #   render_final_vkr_pdf.py, verify_bibliography.py,
│   │                                       #   implement_revised_final3_review.py, generate_figure_2_1.py,
│   │                                       #   insert_chapter3_into_docx.py
│   ├── scenario_manager/                  # как было
│   └── results_pipeline/                  # как было
├── experiments/                           # ВСЕ эксперименты под одной крышей
│   ├── README.md                          # обзор: что делает каждый эксперимент
│   ├── truck_lane_change/                 # ← valid_scenario + my_scenarios/truck_lane_change_scenario
│   │   ├── scripts/run.sh, scripts/start_sionna_server.sh
│   │   └── docs/README.md
│   ├── intersection_crash/                # ← valid_intersection_scenario + my_scenarios/intersection_crash_scenario
│   ├── intersection_radar_comm/           # ← valid_intersection_radar_comm_scenario + my_scenarios/...
│   │   ├── scripts/run.sh, run_radar_*.sh, start_sionna_server.sh
│   │   ├── docs/README.md
│   │   ├── tools/analyze_outputs.py, summarize_runs.py
│   │   ├── sumo/                          # net/route файлы
│   │   └── results/artifacts/             # figure_3_8..3_12.png + sweep CSV
│   ├── cpm_perception/                    # ← valid_cpm_perception_scenario + my_scenarios/cpm_perception_scenario
│   ├── compare_tech/                      # ← my_scenarios/compare_tech
│   ├── intersection_v2x_awareness/        # ← hardwork/ (свежая работа)
│   ├── operational/                       # ← scenarios/ (общие launcher'ы для C++ примеров)
│   │   ├── 5g-phy-metrics/, cttc-nr-v2x-demo-simple/, nr-v2x-west-to-east-highway/,
│   │   ├── v2v-cam-exchange-sionna-nrv2x/, v2v-coexistence-80211p-nrv2x/,
│   │   └── v2v-emergencyVehicleAlert-nrv2x/
│   ├── strict_sionna_vkr/                 # ← strict_sionna_vkr/
│   └── raw/                               # ← raw_experiments/
├── runs/                                  # ← analysis/scenario_runs/ (evidence)
│   ├── README.md
│   ├── 2026-02-18/ ... 2026-03-20/
│   └── chatgpt_exports/
├── reports/                               # учебные/рабочие отчёты (не ВКР, не статьи)
│   ├── cycle7_fizulin_av/                 # ← cycle7_fizulin_av/ + lena_db_dataset из архивной копии
│   └── web_ui_scenario_manager/           # ← analysis/web_ui_scenario_manager_report/
├── conference/                            # docx статьи; transitional → archive
│   └── Fizulin_Romanov_MAIN2026_NRV2X_CoSim.docx + Italian_MAIN_conference_FizulinAV.docx
├── archive/                               # ВСЕ скрытое от ИИ
│   ├── README.md                          # инструкция: «не читать ИИ-агентам»
│   ├── 2026-05-03/                        # эта уборка
│   │   ├── vkr_manuscript/                # все тексты ВКР + figures
│   │   │   ├── chapters/, bibliography/, tables/, appendices/, figures/, ...
│   │   │   └── valid_scenario_VKR_SCENARIO_TEXT.md
│   │   ├── superseded/                    # transitional docx, дубли
│   │   │   ├── conference/Italian_MAIN_transitional.docx
│   │   │   ├── conference/Paper_Title6_transitional.docx
│   │   │   ├── conference/Paper Title6.docx
│   │   │   └── analysis_docx/{1.before_citations,1.citations_preview,
│   │   │       chapter1_reference_fix_package,отчет.*}.docx
│   │   ├── analysis_misc/                 # докс-черновики, vkr_extract, разовые скрипты
│   │   │   ├── vkr_extract/
│   │   │   ├── markdown_to_docx_package.py, rebuild_simple_a3_docx.py, docx_audit.py
│   │   │   ├── integrate_ch1_revision_into_report.py
│   │   │   ├── one_docx_reference_revision.txt
│   │   │   ├── thesis_campaign.log
│   │   │   ├── Rethinking_Persistent_Scheduling_in_5G_New_Radio_Vehicle_to_Everything.pdf
│   │   │   └── chapter1_reference_fix_package.md
│   │   ├── smoke_runs/                    # strict_runs_smoke, strict_runs_smoke_full,
│   │   │                                   #   thesis_campaign_calibration_smoke, thesis_campaign_runs_smoke
│   │   ├── intersection_3d_animation/     # GIF-арт, не для защиты
│   │   ├── mode2_loss/                    # отдельный CARLA-эксперимент
│   │   ├── audit_history/                 # CODE_TRIAGE_2026-04-19, WORKSPACE_CLEANUP_2026-04-19,
│   │   │                                   #   WORKSPACE_MAP.md (старый), REPO_AUDIT_2026-02-27,
│   │   │                                   #   LOG_AUDIT_2026-02-27, codex.md (старый)
│   │   └── before-cleanup-tree.txt        # снимок дерева до уборки
│   └── legacy/                            # уже существует, НЕ ТРОГАЕМ
└── (.venv*, .bootstrap-ns3, .optix-wsl остаются как есть, gitignored)
```

### Дополнительное решение

`analysis/cycle7_fizulin_av_report/` — это отчёт по cycle7 (отдельный от `cycle7_fizulin_av/`, более организованный, со своим `evidence/`). По логике он сросся с `cycle7_fizulin_av/`. **Решение:** переехать в `reports/cycle7_fizulin_av_v2/`, сохранить как «вторую версию» отчёта. Не сливать сейчас — пользователь решит вручную позже.

## Mapping (старое → новое) — final

| Старое | Новое | Тип |
|---|---|---|
| `valid_scenario/{run.sh, README.md, start_sionna_server.sh}` | `experiments/truck_lane_change/{scripts/, docs/}` | move |
| `valid_scenario/VKR_SCENARIO_TEXT.md` | `archive/2026-05-03/vkr_manuscript/` | archive |
| `valid_intersection_scenario/` | `experiments/intersection_crash/` | move |
| `valid_cpm_perception_scenario/` | `experiments/cpm_perception/` | move (вкл. summarize_runs.py → in-experiment tools) |
| `valid_intersection_radar_comm_scenario/` | `experiments/intersection_radar_comm/` | move (вкл. analyze_outputs.py, sumo/) |
| `my_scenarios/{truck_lane_change,intersection_crash,cpm_perception,intersection_radar_comm}_scenario/` | сливаются в соответствующие `experiments/<name>/`; wrapper run.sh удаляются (один настоящий run.sh на эксперимент); `output/` подпапки → `experiments/<name>/results/` | merge |
| `my_scenarios/intersection_radar_comm_scenario/artifacts/` | `experiments/intersection_radar_comm/results/artifacts/` | move |
| `my_scenarios/compare_tech/` | `experiments/compare_tech/` | move |
| `hardwork/` | `experiments/intersection_v2x_awareness/` | rename (`run_intersection_natural.sh` → `scripts/run.sh`, `compare_old_vs_new.sh` → `scripts/compare_old_vs_new.sh`, `visualize_collision_causality.py` → `tools/visualize_collision_causality.py`, `CHANGES.md` → `docs/CHANGES.md`) |
| `scenarios/` | `experiments/operational/` | move целиком |
| `raw_experiments/` | `experiments/raw/` | move целиком |
| `strict_sionna_vkr/` | `experiments/strict_sionna_vkr/` | move целиком |
| `analysis/scenario_runs/` (даты + chatgpt_exports + README) | `runs/` | move evidence-часть |
| `analysis/scenario_runs/{build_*,analyze_*,make_plots,export_results_bundle,export_diploma_timeline,compare_incident_baseline_loss}.py` | `tools/{plots,analysis}/` (split по природе) | move + path-update |
| `analysis/scenario_runs/{LOG_AUDIT,log_audit_summary}_*` | `archive/2026-05-03/audit_history/` | archive |
| `analysis/vkr/{VKR_*.md, PLAN.md, CHAPTER_DRAFT.md, figures/}` | `archive/2026-05-03/vkr_manuscript/` | archive (Q1) |
| `analysis/vkr/{build_final_vkr,generate_chapter3_figures,generate_figure_2_1,implement_revised_final3_review,insert_chapter3_into_docx,render_final_vkr_pdf,verify_bibliography}.py` | `tools/vkr/` | move + path-update |
| `analysis/{render_sionna_animation,visualize_sionna_3d}.py` | `tools/plots/` | move |
| `analysis/{plot_5g_phy_metrics,analyze_phy_safety}.py` | `tools/{plots,analysis}/` | move |
| `analysis/cycle7_fizulin_av_report/` | `reports/cycle7_fizulin_av_v2/` | move |
| `analysis/web_ui_scenario_manager_report/` | `reports/web_ui_scenario_manager/` | move |
| `analysis/intersection_3d_animation/` | `archive/2026-05-03/intersection_3d_animation/` | archive |
| `analysis/mode2_loss/` | `archive/2026-05-03/mode2_loss/` | archive |
| `analysis/{strict_runs_smoke,strict_runs_smoke_full,thesis_campaign_*}/` | `archive/2026-05-03/smoke_runs/` | archive |
| `analysis/vkr_extract/` | `archive/2026-05-03/analysis_misc/vkr_extract/` | archive |
| `analysis/*.docx, analysis/Rethinking_*.pdf, analysis/chapter1_reference_fix_package.md` | `archive/2026-05-03/{superseded,analysis_misc}/` | archive |
| `analysis/{markdown_to_docx_package,rebuild_simple_a3_docx,docx_audit,integrate_ch1_revision_into_report}.py, analysis/one_docx_reference_revision.txt, analysis/thesis_campaign.log` | `archive/2026-05-03/analysis_misc/` | archive (одноразовые) |
| `analysis/{CODE_TRIAGE_2026-04-19,WORKSPACE_CLEANUP_2026-04-19,REPO_AUDIT_2026-02-27}.md` | `archive/2026-05-03/audit_history/` | archive |
| `cycle7_fizulin_av/` | `reports/cycle7_fizulin_av/` (+ `lena_db_dataset/` из архивной копии) | merge per Q3 |
| `archive/legacy/2026-04-19/cycle7_variant_from_root_1/` | оставить как есть | keep |
| `conference/Fizulin_Romanov_MAIN2026_NRV2X_CoSim.docx` | `conference/` (в корне) | keep |
| `conference/Italian_MAIN_conference_FizulinAV.docx` | `conference/` (в корне) | keep |
| `conference/Italian_MAIN_transitional.docx`, `conference/Paper_Title6_transitional.docx`, `conference/Paper Title6.docx` | `archive/2026-05-03/superseded/conference/` | archive |
| `conference/generate_ieee_paper.py` | `tools/vkr/generate_ieee_paper.py` | move |
| `WORKSPACE_MAP.md` | `archive/2026-05-03/audit_history/WORKSPACE_MAP.md` | archive (per Q5) |
| `codex.md` | `archive/2026-05-03/audit_history/codex.md.old` + `AGENTS.md` (новый) | replace |

## Path/reference updates

### Внутри `experiments/<name>/scripts/run.sh`

В каждом скрипте `valid_*/run.sh` и `hardwork/run_intersection_natural.sh` есть строка:
```bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
```
После переезда в `experiments/<name>/scripts/run.sh` нужно заменить на:
```bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
```
(подняться на 3 уровня вместо 1).

Также проверить:
- `OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/<scenario_name>}"` — обновить scenario_name под новое имя (`truck_lane_change` вместо `valid_scenario`).
- `SIONNA_START_SCRIPT="${SIONNA_START_SCRIPT:-$ROOT/valid_scenario/start_sionna_server.sh}"` — обновить на `$ROOT/experiments/truck_lane_change/scripts/start_sionna_server.sh`.
- `EXPORT_BASE="$ROOT/analysis/scenario_runs/chatgpt_exports"` (если есть) → `$ROOT/runs/chatgpt_exports`.
- `BIN_DIR="$ROOT/.bootstrap-ns3/.../examples/automotive/"` — относительные пути к C++ binary остаются (через `$ROOT`).

### `tools/scenario_manager/scenarios.py`

Использует `my_scenarios/`. Обновить на новые пути `experiments/<name>/scripts/run.sh`.

### `tools/scenario_manager/run_*.sh`

Если ссылаются на `scenarios/` → `experiments/operational/`.

### `tools/{plots,analysis,vkr}/*.py`

После переезда из `analysis/scenario_runs/` и `analysis/vkr/` нужно проверить:
- Ссылки на `analysis/scenario_runs/<date>/<run>/` → `runs/<date>/<run>/`.
- Ссылки на `analysis/vkr/figures/` (output) → решение принять при рефакторинге: либо tools/vkr/output/, либо принимать `--out-dir` параметром.
- `generate_chapter3_figures.py:36`: `CRASH_RUN = ROOT / "analysis/scenario_runs/2026-03-04/..."` → `runs/2026-03-04/...`.
- `analysis/scenario_runs/build_intersection_scenario_summary.py`, `build_compare_tech_summary.py` — проверить импорты и пути.

### `valid_intersection_scenario/run.sh` ссылка на `scenarios/`

```
EXPORT_BASE="${EXPORT_BASE:-$ROOT/analysis/scenario_runs/chatgpt_exports}"
```
И возможно вызовы `scenarios/v2v-emergencyVehicleAlert-nrv2x/...` — заменить на `experiments/operational/v2v-emergencyVehicleAlert-nrv2x/...`.

### `scripts/sync-overlay-into-bootstrap-ns3.sh`, `scripts/docker-run-eva-sionna.sh`

Если ссылаются на старые пути сценариев — обновить.

### `.gitignore`

- `archive/` НЕ добавляется в .gitignore — он коммитится в git, чтобы быть частью истории. Но agent-инструкция в `archive/README.md` и `AGENTS.md` явно запрещает ИИ читать эту папку.
- Если `runs/` начнёт расти быстро (как `analysis/scenario_runs/` раньше), пользователь добавит правила позже. Сейчас не трогаем.

### Обновление подписи новых README

- `experiments/README.md`: таблица всех экспериментов, для каждого: что делает, как запустить, где результаты, какие фигуры/таблицы он даёт.
- `runs/README.md`: формат хранения evidence (по датам), как запускать аналитические скрипты из `tools/`.
- `tools/README.md`: разбивка инструментов по категориям, примеры использования.
- `archive/README.md`: «**Это архив. ИИ-агенты, не индексируйте и не читайте содержимое этой папки.** Тут лежат замороженные тексты ВКР, дублирующие docx, одноразовые скрипты, GIF-арт, отдельные эксперименты, аудиторские отчёты прошлых уборок.»
- `AGENTS.md`: явное правило игнорировать `archive/`, `.venv*`, `.bootstrap-ns3/`, `.optix-wsl/`, `.cache/`, `tmp/`. Карта основных директорий. Правила для ИИ-помощников Claude/Codex/Gemini.
- `REPO_LAYOUT.md`: человеко-читаемая карта (как `WORKSPACE_MAP.md`, но актуальная).

## Risks & mitigations

| Риск | Митигация |
|---|---|
| Скрипт сценария ломается из-за `ROOT` | Найти все вхождения `ROOT="..."` через `grep`, переписать атомарно. После переезда — `bash -n experiments/*/scripts/run.sh` (lint). |
| Текст ВКР в архиве содержит ссылки на пути, которые поменялись | Не релевантно — текст заморожен. При воссоздании PDF позже — обновлять текст вручную. |
| Внешние пути из `tools/` не обновлены — графики не строятся | Запустить smoke-генерацию ключевых фигур (3.1, 3.8) и поправить если что. Не блокирующий шаг. |
| Конфликт имён в `experiments/` | Каждое имя в mapping уникально (проверено). |
| Большой коммит сложно ревьюить | Принято решение Q4. Для ревью оставить `archive/2026-05-03/before-cleanup-tree.txt` и подробный commit message. |
| Uncommitted changes (M-файлы в `git status`) сейчас в работе | Перед reorg — закоммитить их как **отдельный snapshot-коммит** на той же ветке. Reorg-коммит идёт следом. |
| `git mv` не трекает крупные перемещения если файл переименован И изменён | Использовать **только** `git mv` (без редактирования внутри того же коммита). Path-updates в скриптах — отдельным коммитом или в конце reorg-коммита. |
| `.bootstrap-ns3` symlinks/builds могут привязаны к старым путям | После reorg — пересборка не входит в задачу; пользователь сделает сам если нужно. Документировано. |
| `analysis/cycle7_fizulin_av_report/` vs `cycle7_fizulin_av/` (две версии отчёта) | Не сливаем автоматически. Live → `reports/cycle7_fizulin_av/`, organized → `reports/cycle7_fizulin_av_v2/`. Пользователь решит позже. |

## Out of scope

- Build / пересборка ns-3.
- Восстановление ВКР PDF после переезда.
- Удаление `.venv*`, `.bootstrap-ns3/` и других runtime-зон (они gitignored, не мешают).
- Ревью кода в `src/` и `tools/`.
- Перенос git-истории файлов между репозиториями.
- Удаление каких-либо файлов **окончательно** — всё, что «лишнее», уезжает в `archive/`, ничего не теряется.

## Acceptance criteria

1. Папок в корне: `src`, `docs`, `tools`, `experiments`, `runs`, `reports`, `conference`, `archive` + служебные (`tests`, `emulation-support`, `scripts`, `img`, `docker`, `.venv*`, `.bootstrap-ns3`, `.optix-wsl`, `.git`, `.vscode`, `.claude`).
2. Старые папки `valid_*`, `my_scenarios`, `scenarios`, `raw_experiments`, `hardwork`, `cycle7_fizulin_av`, `strict_sionna_vkr`, `analysis` — **отсутствуют** (содержимое распределено).
3. Все `experiments/<name>/scripts/run.sh` синтаксически валидны (`bash -n`).
4. `experiments/README.md`, `runs/README.md`, `tools/README.md`, `archive/README.md`, `AGENTS.md`, `REPO_LAYOUT.md` существуют и заполнены.
5. `archive/README.md` начинается с явного указания «не читать ИИ-агентам».
6. `AGENTS.md` содержит правило игнорировать `archive/`, `.venv*`, `.bootstrap-ns3/`, `.optix-wsl/`.
7. `git status` чист (только новый reorg-коммит и предыдущий snapshot-коммит).
8. `before-cleanup-tree.txt` зафиксирован в архиве для аудита.
9. Конференц-папка содержит только два финальных docx.

## Execution order

1. Snapshot uncommitted changes как первый коммит (например: `chore: snapshot before repo reorganization`).
2. Сделать `before-cleanup-tree.txt` (`tree -L 3`) и положить в `/tmp/`.
3. `mkdir -p experiments runs reports tools/{plots,analysis,vkr} archive/2026-05-03/{vkr_manuscript,superseded/conference,superseded/analysis_docx,analysis_misc/vkr_extract,smoke_runs,intersection_3d_animation,mode2_loss,audit_history,cycle7_fizulin_av_report}`.
4. Серия `git mv` по mapping-таблице. Группами для удобства revert внутри одного коммита.
5. Path-updates в `experiments/*/scripts/run.sh`, `tools/scenario_manager/scenarios.py`, `tools/{plots,analysis,vkr}/*.py`.
6. Создать новые `README.md` в `experiments/`, `runs/`, `tools/`, `archive/`.
7. Создать `AGENTS.md`, `CLAUDE.md`, `REPO_LAYOUT.md`.
8. Обновить `.gitignore`.
9. `bash -n` на всех run.sh.
10. Один большой reorg-коммит `chore(repo): reorganize into experiments/runs/tools/reports/archive layout`.

Detailed execution plan — в следующем артефакте через writing-plans skill.
