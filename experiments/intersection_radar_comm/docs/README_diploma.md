# intersection_radar_comm_scenario

Фиксированный сценарий перекрестка для сравнения:

- `radar_bad_link`
- `radar_only`
- `radar_good_link`

Запуск всех трех режимов:

```bash
my_scenarios/intersection_radar_comm_scenario/run.sh
```

Отдельные режимы:

```bash
my_scenarios/intersection_radar_comm_scenario/run_radar_bad_link.sh
my_scenarios/intersection_radar_comm_scenario/run_radar_only.sh
my_scenarios/intersection_radar_comm_scenario/run_radar_good_link.sh
```

Перед запуском должен быть поднят `Sionna` server:

```bash
valid_intersection_radar_comm_scenario/start_sionna_server.sh
```

Скрипты делегируют в:

- `valid_intersection_radar_comm_scenario/run.sh`
