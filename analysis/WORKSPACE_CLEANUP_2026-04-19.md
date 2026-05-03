# Отчет по уборке рабочего пространства от 2026-04-19

## Канонический проект

Каноническим рабочим проектом ВКР считается:

`/home/afetz/work/clean/NEWWAY`

Для удобства создана ссылка:

`/home/afetz/NEWWAY_VKR`

Причина: именно в этом checkout находятся `analysis/vkr/`, `vkr_final/`, дипломные сценарии, инструменты анализа и большая часть материалов ВКР.

## Что было найдено

- `/home/afetz/NEWWAY` - отдельный checkout на ветке `van3t-ms-copy`; содержит 4 незакоммиченных C++ изменения.
- `/home/afetz/NEWWAY-sandbox-setup/ns-3-dev` - песочный ns-3-dev; содержит незакоммиченные изменения и новые файлы `degradationCollision`.
- `/home/afetz/work/clean/NEWWAY` - основной ВКР-пакет на ветке `bootstrap/dev-onboarding`; содержит документы, analysis, scenarios, tools и рабочие C++ изменения.
- `/home/afetz/work/test/VaN3Twin` и `/home/afetz/work/test/VaN3Twin_clean` - старые upstream-клоны VaN3Twin одного commit.
- `/home/afetz/work/clean/NEWWAY_boot`, `/home/afetz/work/clean/NEWWAY_damaged_20260219-160236`, `/home/afetz/work/clean/ms-van3t` - старые legacy-копии/заготовки.
- `/home/afetz/work/clean/NEWWAY_archive_20260219_oldruns` - старый архив запусков, владелец `root`.
- `/home/afetz/work/cavise_stageA` и `/home/afetz/work/cavise_5G_NR` - отдельные проекты, не часть NEWWAY/VKR.

## Выполненная уборка

- Удалены пользовательские кэши: `~/.cache/pip`, `~/.cache/ccache`, `~/.cache/ms-playwright`, `~/.cache/vscode-cpptools`, Mesa/matplotlib caches.
- Удалены проектные кэши: `.cache/`, `tmp/`, `__pycache__/`, `.pytest_cache/` внутри основного NEWWAY checkout.
- Удален точный дубль `conference/Paper.docx`; сохранен идентичный файл `conference/Fizulin_Romanov_MAIN2026_NRV2X_CoSim.docx`.
- Папка `1/` перенесена в `archive/legacy/2026-04-19/cycle7_variant_from_root_1/`, потому что она похожа на `cycle7_fizulin_av/`, но не является полным точным дублем.
- Старые клоны `/home/afetz/work/test/VaN3Twin*` перенесены в `/home/afetz/work/archive/2026-04-19/work-test/`.
- Legacy-папки `NEWWAY_boot`, `NEWWAY_damaged_20260219-160236`, `ms-van3t` перенесены в `/home/afetz/work/archive/2026-04-19/work-clean-legacy/`.
- Обновлен `.gitignore`, чтобы локальные окружения, кэши, временные папки и legacy-архивы не всплывали как рабочие файлы.
- Добавлен `WORKSPACE_MAP.md` с картой проекта и правилами дальнейшей работы.
- Добавлен `analysis/CODE_TRIAGE_2026-04-19.md` с разбором незакоммиченного кода из соседних checkout.

## Не удалялось

- Не удалялись git checkout с незакоммиченными изменениями.
- Не удалялись `analysis/scenario_runs/`, `raw_experiments/`, `output/`, `vkr_final/`, `conference/` и дипломные scenario-папки.
- Не удалялись `.venv`, `.venv_sionna`, `.optix-wsl`, `.bootstrap-ns3`: это локальные тяжелые runtime-зоны, но они могут быть нужны для воспроизводимых запусков.
- Не переносился `/home/afetz/work/clean/NEWWAY_archive_20260219_oldruns`: папка root-owned, `sudo` без пароля недоступен.

## Что стоит сделать следующим шагом

1. Перенести или cherry-pick нужные изменения из `/home/afetz/NEWWAY` и `/home/afetz/NEWWAY-sandbox-setup/ns-3-dev` в канонический `/home/afetz/NEWWAY_VKR`, если они действительно относятся к ВКР.
2. Проверить архив `/home/afetz/work/archive/2026-04-19/`; если старые клоны и legacy-копии точно не нужны, их можно удалить.
3. После проверки запусков можно удалить или пересоздать локальные `.venv*`, `.optix-wsl`, `.bootstrap-ns3`, если нужно освободить еще место.
