# cttc-nr-v2x-demo-simple

Минимальный NR sidelink сценарий (2 UE, out-of-coverage, один Tx и один Rx).

- Исходник: `src/nr/examples/nr-v2x-examples/cttc-nr-v2x-demo-simple.cc`
- Ключевые строки: `:25`, `:39`

## Запуск

```bash
scenarios/cttc-nr-v2x-demo-simple/run.sh
```

## Что сохраняется

- Лог: `analysis/scenario_runs/<date>/cttc-nr-v2x-demo-simple.log`
- SQLite: `analysis/scenario_runs/<date>/artifacts/<simTag>-nr-v2x-simple-demo.db`
- Графики: `analysis/scenario_runs/<date>/figures/cttc-nr-v2x-demo-simple/*.png`
