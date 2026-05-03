# 1548-CAVISE2026_5GNR — Wiki

> **«Влияние потерь сообщений 5G NR-V2X Mode 2 на безопасность подключённых автономных транспортных средств»**

**Автор:** Физулин Андрей Владимирович · НИТУ МИСИС / HSE, JSC AVTOVAZ  
**Лицензия:** GPL-2.0 (наследует от ms-van3t)

---

## О проекте

**1548-CAVISE2026_5GNR** — исследовательский overlay поверх фреймворка [ms-van3t](https://github.com/ms-van3t-devs/ms-van3t) / [VaN3Twin](https://github.com/DriveX-devs/NEWWAY), реализующий co-simulation **ns-3 + SUMO + NVIDIA Sionna** для изучения причинно-следственной цепочки:

```
потеря CAM → деградация решений → дорожный инцидент
```

### Что делает этот проект

- Добавляет **оригинальные сценарии** для исследования цепочки: потеря CAM → ухудшение принятия решений → дорожный инцидент
- Интегрирует **NVIDIA Sionna** (ray-tracing канал) в петлю обратной связи ns-3 ↔ SUMO
- Предоставляет **инструменты постобработки** (графики PRR, временны́е шкалы drop → decision, аудит логов)
- Хранит **воспроизводимые evidence-прогоны** для защиты ВКР

### Иерархия upstream

```
ms-van3t (Politecnico di Torino / Milano)
    └── VaN3Twin (+ NVIDIA Sionna ray-tracing)
            └── 1548-CAVISE2026_5GNR overlay (Физулин А.В., ВКР 2026)
                    ├── src/automotive/  — доработки EVA, emergencyVehicleAlert
                    ├── src/sionna/      — расширение Sionna connection handler
                    └── experiments/     — оригинальные ВКР-сценарии
```

---

## Навигация по Wiki

| Страница | Описание |
|---|---|
| [[Структура репозитория]] | Полная карта директорий и файлов |
| [[Установка и сборка]] | Пошаговая инструкция по развёртыванию |
| [[Сценарии экспериментов]] | Описание всех сценариев и как их запустить |
| [[Sionna Ray-Tracing]] | Интеграция NVIDIA Sionna для физического канала |
| [[Инструменты анализа]] | Графики, анализаторы, генераторы ВКР |
| [[Evidence-прогоны]] | Хранение и воспроизведение результатов |
| [[Scenario Manager UI]] | Веб-интерфейс для управления сценариями |
| [[Docker]] | Контейнеризация и GPU-окружение |
| [[Архитектура NR Sidelink]] | 5G-LENA sidelink Mode 2 в этом проекте |
| [[Цитирование]] | Как ссылаться на проект |

---

## Ключевые ссылки

- **Upstream ms-van3t:** https://github.com/ms-van3t-devs/ms-van3t
- **Upstream VaN3Twin / NEWWAY:** https://github.com/DriveX-devs/NEWWAY
- **Документация ms-van3t:** https://ms-van3ts-documentation.readthedocs.io/en/master/
- **NVIDIA Sionna:** https://nvlabs.github.io/sionna/
