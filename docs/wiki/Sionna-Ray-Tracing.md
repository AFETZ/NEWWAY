# Sionna Ray-Tracing

## Обзор

[NVIDIA Sionna](https://nvlabs.github.io/sionna/) используется как **физический канальный движок** вместо стандартной log-distance модели. Sionna выполняет ray-tracing для вычисления реалистичных характеристик канала между узлами V2X.

## Что делает Sionna в этом проекте

Sionna заменяет channel-space quantities для каждой пары узлов:

| Параметр | Описание |
|---|---|
| **Path gain** | Затухание сигнала по всем лучам |
| **Propagation delay** | Задержка распространения |
| **LOS/NLOS state** | Прямая видимость или нет |

Всё остальное (sidelink bearer setup, Mode 2 resource selection, SINR/TBLER evaluation, decode success/failure) выполняется **5G-LENA** на стороне ns-3.

## Архитектура

```
ns-3 (5G-LENA NR sidelink)
    ↕ socket (port 8103)
Sionna RT server (GPU)
    ↕ ray-tracing
Mitsuba XML scene (Blender 3.6.22)
```

## Установка

```bash
pip install sionna   # v0.19.0 или v1.0
```

## Запуск Sionna-сервера

В отдельном терминале (или на GPU-машине):

```bash
./.venv_sionna/bin/python src/sionna/sionna_v1_server_script.py \
  --path-to-xml-scenario src/sionna/scenarios/SionnaCircleScenario/scene.xml \
  --local-machine --verbose
```

Дождитесь сообщения `Setup complete.` перед запуском сценариев.

## Запуск сценария с Sionna

```bash
USE_SIONNA=1 SIONNA_SERVER_IP=127.0.0.1 \
  experiments/truck_lane_change/scripts/run.sh
```

Подтверждение подключения: строка `SUCCESS! ns-3 is now locally connected to Sionna` в логе.

## Sionna-сцены

Сцены в формате **Mitsuba XML** создаются в **Blender 3.6.22** с аддоном [mitsuba-blender](https://github.com/mitsuba-renderer/mitsuba-blender).

Расположение сцен:
- `src/sionna/scenarios/SionnaCircleScenario/scene.xml` — базовая urban сцена
- `experiments/strict_sionna_vkr/sionna_scenes/` — per-scenario сцены для строгих прогонов

## Работа без Sionna

Все сценарии поддерживают fallback-режим без ray-tracing:

```bash
USE_SIONNA=0 experiments/truck_lane_change/scripts/run.sh
```

В этом случае используется стандартная log-distance модель ns-3.

## Ключевые переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `USE_SIONNA` | Включить Sionna (1/0) | `1` |
| `SIONNA_SERVER_IP` | IP адрес Sionna-сервера | `127.0.0.1` |
| `CHECK_SIONNA_LISTENER` | Проверять UDP-listener перед запуском | `0` |
| `PHY_ONLY` | Только физический канал, без ручных drop | зависит от сценария |

## Калибровка

Для строгих прогонов доступен скрипт калибровки:

```bash
python3 experiments/strict_sionna_vkr/scripts/run_radio_calibration.py \
  --manifest experiments/strict_sionna_vkr/manifests/strict_intersection/radar_good.json \
  --out-root analysis/strict_calibration
```

## Strict Sionna (для ВКР)

Пакет `experiments/strict_sionna_vkr/` обеспечивает строгие гарантии:
- Все manifests явно задают Mode 2 параметры
- Запрещены legacy shims (`per-vehicle-prr-profile`, `equiv_tx_power_dbm`, `crash-mode`)
- `enableSensing=1` принудительно

Подробнее: [[Сценарии экспериментов]]
