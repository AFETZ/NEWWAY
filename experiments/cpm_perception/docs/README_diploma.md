# cpm_perception_scenario

Фиксированный сценарий для сравнения локального сенсора и cooperative perception через CPM.

Полный прогон всех трех режимов:

```bash
my_scenarios/cpm_perception_scenario/run.sh
```

Отдельные режимы:

```bash
my_scenarios/cpm_perception_scenario/run_sensor_only.sh
my_scenarios/cpm_perception_scenario/run_sensor_good_cpm.sh
my_scenarios/cpm_perception_scenario/run_sensor_bad_cpm.sh
```

Перед запуском должен быть поднят Sionna server:

```bash
valid_cpm_perception_scenario/start_sionna_server.sh
```

Скрипт делегирует в:

- `valid_cpm_perception_scenario/run.sh`
