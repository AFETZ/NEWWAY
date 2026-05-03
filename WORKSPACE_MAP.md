# Карта рабочего пространства NEWWAY / ВКР

Главный рабочий проект ВКР сейчас находится здесь:

`/home/afetz/work/clean/NEWWAY`

Для быстрого входа создана ссылка:

`/home/afetz/NEWWAY_VKR -> /home/afetz/work/clean/NEWWAY`

## Что это за проект

Это рабочий overlay/repository вокруг VaN3Twin / ns-3-dev для ВКР по теме влияния потерь сообщений 5G NR-V2X на поведение подключенных беспилотных транспортных средств.

Главная ценность проекта лежит в трех слоях:

- `src/` - измененный код симулятора и модулей VaN3Twin/ns-3.
- `scenarios/`, `valid_*`, `my_scenarios/` - воспроизводимые сценарии и обертки запуска.
- `analysis/`, `vkr_final/`, `conference/`, `output/`, `raw_experiments/` - доказательная база, тексты ВКР, графики, отчеты и результаты прогонов.

## Рабочая структура

| Путь | Назначение |
|---|---|
| `src/automotive/` | Основные изменения ВКР: приложения, EVA/сценарии, обработка сообщений, логирование поведения. |
| `src/sionna/` | Интеграция с Sionna и обмен данными между ns-3 и внешним ray-tracing/PHY слоем. |
| `src/nr/` | NR / 5G-LENA код и примеры. Менять осторожно: это крупный upstream-модуль. |
| `scenarios/` | Операционные launchers: сборка, запуск, export результатов, переменные окружения. |
| `valid_scenario/` | Зафиксированный lane-change кейс для ВКР. |
| `valid_intersection_scenario/` | Зафиксированный intersection/crash кейс для ВКР. |
| `my_scenarios/` | Упакованные дипломные сценарии с понятными именами и локальными output. |
| `analysis/vkr/` | Markdown-исходники глав, библиография, таблицы, генераторы текста/рисунков. |
| `analysis/scenario_runs/` | История прогонов, артефакты, CSV и графики. Это evidence, а не исходный код. |
| `vkr_final/` | Главный входной пакет для финальной ВКР: исходники глав 2/3, supporting files, итоговые сборки. |
| `conference/` | Материалы статьи/конференции. |
| `tools/` | Локальные инструменты анализа и scenario manager. |
| `raw_experiments/` | Raw-only прогоны без постобработки. |
| `output/` | Производные документы, review-артефакты, PDF/DOCX сборки. |
| `archive/` | Legacy/cleanup материалы, которые не должны мешать рабочему корню. |

## Что лежит рядом с проектом

| Путь | Статус |
|---|---|
| `/home/afetz/NEWWAY` | Отдельный git checkout на ветке `van3t-ms-copy`. Это не основной ВКР-пакет; там есть несколько незакоммиченных C++ правок. |
| `/home/afetz/NEWWAY-sandbox-setup/ns-3-dev` | Сгенерированный/песочный ns-3-dev. Там есть отдельные незакоммиченные изменения по `degradationCollision`. |
| `/home/afetz/NEWWAY_runs` | Результаты запусков. Не смешивать с исходным кодом. |
| `/home/afetz/work/archive/2026-04-19/work-test/VaN3Twin*` | Старые upstream-клоны VaN3Twin, вынесены из рабочей зоны. |
| `/home/afetz/work/archive/2026-04-19/work-clean-legacy/` | Старые legacy-копии/заготовки из `/home/afetz/work/clean`. |
| `/home/afetz/work/clean/NEWWAY_archive_20260219_oldruns` | Старый root-owned архив запусков. Остался на месте, потому что у текущего пользователя нет прав на перенос. |
| `/home/afetz/work/cavise_*` | Отдельные проекты, не часть NEWWAY/VKR. |

## Практические правила

1. Новую работу по ВКР вести из `/home/afetz/NEWWAY_VKR`.
2. Не класть виртуальные окружения, кэши, `.bootstrap-ns3`, `.optix-wsl`, `tmp` и agent-local файлы в git.
3. Если прогон нужен как доказательство для ВКР, складывать его в `analysis/scenario_runs/` или `raw_experiments/runs/`, а итоговую выжимку переносить в `vkr_final/supporting_files/`.
4. Если материал старый, спорный или дублирует другой пакет, переносить его в `archive/legacy/`, а не оставлять в корне.
5. Перед удалением сценарных результатов проверять, не упоминаются ли они в `vkr_final/source_manifest.md`, `analysis/vkr/` или README соответствующего сценария.
