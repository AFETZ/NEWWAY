# Триаж соседних checkout от 2026-04-19

Цель: понять, какие незакоммиченные изменения рядом с каноническим проектом могут относиться к ВКР.

## `/home/afetz/NEWWAY`

Ветка: `van3t-ms-copy`.

Найдено 4 измененных файла:

- `src/automotive/model/Facilities/BSContainer.h`
- `src/automotive/model/Facilities/BSContainer.cc`
- `src/automotive/examples/v2v-coexistence-80211p-ltev2x.cc`
- `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc`

Смысл изменений:

- добавляется `MCBasicService`, callback для `MCM`, `getMCBasicService()`, `getLDM()`, `getVDP()`;
- `setupContainer()` расширяется параметрами `MCMBasicService_enabled` и `security_enabled`;
- исправляется проверка "zero basic services";
- добавляется `m_gn->setSecurity(security_enabled)`;
- в `v2v-emergencyVehicleAlert-nrv2x.cc` добавляется параметр `--sumo-wait-for-socket`.

Важный риск: файл `v2v-emergencyVehicleAlert-nrv2x.cc` в `/home/afetz/NEWWAY` старее канонического файла из `/home/afetz/NEWWAY_VKR` и не содержит текущий большой блок ВКР-логики/статистики. Его нельзя копировать целиком поверх канонического проекта.

Рекомендация: переносить только точечные изменения по `BSContainer` и `sumo-wait-for-socket`, вручную через diff/cherry-pick, после проверки совместимости с текущей ВКР-версией.

## `/home/afetz/NEWWAY-sandbox-setup/ns-3-dev`

Ветка: `van3t-ms-copy`, origin указывает на `/home/afetz/NEWWAY`.

Измененные tracked-файлы:

- `src/automotive/CMakeLists.txt`
- `src/automotive/examples/CMakeLists.txt`
- `src/automotive/model/ASN1/full-v1-v2/asn_system.h`
- `src/traci/model/traci-client.cc`

Новые untracked-файлы:

- `src/automotive/examples/v2v-degradation-collision-nrv2x.cc`
- `src/automotive/helper/degradationCollision-helper.cc`
- `src/automotive/helper/degradationCollision-helper.h`
- `src/automotive/model/Applications/degradationCollision.cc`
- `src/automotive/model/Applications/degradationCollision.h`
- `src/automotive/examples/sumo_files_v2v_map/cars_collision.rou.xml`
- `src/automotive/examples/sumo_files_v2v_map/map_collision.sumo.cfg`
- `run-out/` с результатами запусков.

Смысл изменений:

- отдельная экспериментальная линия `degradationCollision`;
- улучшения запуска SUMO в `traci-client.cc` через поиск executable/SUMO root;
- изменения CMake для сборки нового сценария и OpenSSL;
- правка `asn_system.h`, которая откатывает более безопасную guard-проверку из канонического проекта.

Рекомендация:

1. `degradationCollision` переносить как отдельную feature-ветку или пакет, не смешивая с текущим `valid_scenario`.
2. `traci-client.cc` изучить отдельно: там может быть полезная переносимая логика SUMO discovery.
3. `asn_system.h` из sandbox не переносить без причины: каноническая версия безопаснее для C++ компилятора.
4. `run-out/` считать результатами запусков, а не исходниками; при необходимости переносить только итоговые CSV/выводы в `analysis/scenario_runs/`.
