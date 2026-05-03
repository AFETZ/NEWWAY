# Wiki

Документация проекта 1548-CAVISE2026_5GNR.

## Содержание

| Страница | Описание |
|---|---|
| [Home](Home.md) | Главная страница — обзор проекта |
| [Структура репозитория](Структура-репозитория.md) | Полная карта директорий и файлов |
| [Установка и сборка](Установка-и-сборка.md) | Пошаговая инструкция по развёртыванию |
| [Сценарии экспериментов](Сценарии-экспериментов.md) | Описание всех сценариев и как их запустить |
| [Sionna Ray-Tracing](Sionna-Ray-Tracing.md) | Интеграция NVIDIA Sionna |
| [Инструменты анализа](Инструменты-анализа.md) | Графики, анализаторы, генераторы ВКР |
| [Evidence-прогоны](Evidence-прогоны.md) | Хранение и воспроизведение результатов |
| [Scenario Manager UI](Scenario-Manager-UI.md) | Веб-интерфейс для управления сценариями |
| [Docker](Docker.md) | Контейнеризация и GPU-окружение |
| [Архитектура NR Sidelink](Архитектура-NR-Sidelink.md) | 5G-LENA sidelink Mode 2 |
| [Цитирование](Цитирование.md) | Как ссылаться на проект |

## Использование как GitHub Wiki

Эти файлы также могут быть использованы как [GitHub Wiki](https://docs.github.com/en/communities/documenting-your-project-with-wikis). Для этого:

1. Включите Wiki в настройках репозитория (Settings → Features → Wikis)
2. Скопируйте файлы из этой директории в wiki-репозиторий:
   ```bash
   git clone https://github.com/AFETZ/1548-CAVISE2026_5GNR.wiki.git
   cp docs/wiki/*.md 1548-CAVISE2026_5GNR.wiki/
   cd 1548-CAVISE2026_5GNR.wiki
   git add -A && git commit -m "Init wiki" && git push
   ```
