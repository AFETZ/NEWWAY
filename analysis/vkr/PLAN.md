# План ВКР

Тема: **Исследование влияния потерь сообщений в 5G NR Mode 2 sidelink на поведение подключенного и беспилотного транспорта**

## Глава 1. Введение

- Актуальность задачи CAV/AV в условиях ненадежной V2X-связи.
- Проблема: средние network-KPI часто не отражают поведенческий риск.
- Цель, объект, предмет, гипотезы.
- Научная новизна и практическая значимость.

## Глава 2. Обзор и постановка задачи

- NR-V2X sidelink Mode 2: базовые механизмы, источники потерь.
- Метрики связи: PRR, latency, PIR, SINR, overlap, TB fail.
- Поведенческие метрики: reaction delay, control actions, surrogate safety metrics.
- Формальная постановка задачи и критерии валидации гипотез.

## Глава 3. Методика и экспериментальный стенд

- Стек: ns-3 + SUMO + ms-van3t overlay.
- Сценарии репозитория:
  - `cttc-nr-v2x-demo-simple`
  - `nr-v2x-west-to-east-highway`
  - `v2v-cam-exchange-sionna-nrv2x`
  - `v2v-coexistence-80211p-nrv2x`
  - `v2v-emergencyVehicleAlert-nrv2x` (incident-mode + loss sweep)
- План экспериментов:
  - baseline,
  - sweep по `rx-drop-prob-cam`,
  - backend compare (после установки Sionna).
- Обоснование выбора KPI и процедур анализа.

## Глава 4. Результаты экспериментов

- Базовая валидация NR Mode 2 (2 UE).
- Нагрузка highway и механизмы деградации (overlap/TB fail).
- Сравнение NR и 802.11p в coexistence.
- Поведенческий sweep в incident-сценарии:
  - связь CAM loss -> reaction metrics.
- Анализ статистической устойчивости выводов.

## Глава 5. Интерпретация для CAV/AV

- Почему недостаточно смотреть только average PRR/latency.
- Как переводить network-loss в поведенческий риск.
- Практические требования к проектированию/валидации V2X для автоматизированного транспорта.

## Глава 6. Заключение

- Основные результаты по гипотезам.
- Ограничения работы.
- Направления дальнейших исследований.

## Матрица "артефакт -> глава"

- `analysis/scenario_runs/.../run_summary.csv` -> главы 3-4
- `analysis/scenario_runs/.../REPORT.md` -> главы 4-5
- `analysis/scenario_runs/.../figures/*.png` -> главы 4-5
- `analysis/scenario_runs/.../eva-loss-sweep-incident-v2/loss_sweep_summary.csv` -> глава 4
- `analysis/scenario_runs/.../eva-loss-sweep-incident-v2/loss_sweep_behavior_timing.png` -> главы 4-5

