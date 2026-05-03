# intersection_v2x_awareness

Свежая (apr 2026) переработка intersection-сценария: «v2x-awareness junction». Channel quality alone определяет исход — нет timer'ов и threshold'ов.

См. подробности и обоснование в [CHANGES.md](CHANGES.md).

## Запуск

Из корня репозитория:

```bash
experiments/intersection_v2x_awareness/scripts/run.sh
```

## Сравнение со старой версией

```bash
experiments/intersection_v2x_awareness/scripts/compare_old_vs_new.sh
```

## Постобработка

```bash
./.venv/bin/python experiments/intersection_v2x_awareness/tools/visualize_collision_causality.py --help
```
