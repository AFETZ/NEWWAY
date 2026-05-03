# archive/

> **ИИ-агентам (Claude/Codex/Gemini/прочие): НЕ ЧИТАТЬ И НЕ ИНДЕКСИРОВАТЬ содержимое этой папки.** Здесь лежат замороженные тексты ВКР, дублирующие docx, одноразовые скрипты, GIF-арт, отдельные эксперименты, аудиторские отчёты прошлых уборок. Эти файлы не должны влиять на текущую работу и не дают актуального контекста.

## Структура

- `legacy/` — материалы от предыдущих уборок (в т.ч. `2026-04-19/`).
- `2026-05-03/` — текущая большая уборка (см. `docs/superpowers/specs/2026-05-03-repo-cleanup-design.md`):
  - `vkr_manuscript/` — все тексты ВКР (главы, bibliography, appendices, tables, conclusion, front matter, inventory, PLAN, CHAPTER_DRAFT) + figures.
  - `superseded/conference/` — transitional/older docx статьи.
  - `superseded/analysis_docx/` — старые отчётные docx и pre-citations версии.
  - `analysis_misc/` — vkr_extract/, одноразовые скрипты сборки docx, разовый log, pdf чужой статьи.
  - `smoke_runs/` — strict_runs_smoke, thesis_campaign_*.
  - `intersection_3d_animation/` — GIF / 3D-анимации.
  - `mode2_loss/` — отдельный CARLA-эксперимент (не часть основной линии ВКР).
  - `audit_history/` — старые audit-документы (CODE_TRIAGE, WORKSPACE_CLEANUP, REPO_AUDIT, LOG_AUDIT, WORKSPACE_MAP, codex.md.old).
  - `before-cleanup-tree.txt` — снимок дерева перед уборкой.

## Когда нужно вернуться сюда

Только в трёх случаях:

1. Восстановить замороженный фрагмент текста ВКР для обновления.
2. Поднять архивные evidence для проверки утверждения в защите.
3. Audit-расследование «когда и зачем что-то менялось».
