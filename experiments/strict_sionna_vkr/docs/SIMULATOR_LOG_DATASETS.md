# Simulator Log Datasets

This catalog answers a practical question for the thesis work: which datasets
can be extracted from the simulator stack, what type of data each file stores,
and what each dataset is for.

The reference strict run used for concrete examples is:

- `/home/afetz/work/clean/NEWWAY/analysis/strict_runs_smoke_full/strict_intersection/radar_good/seed-017`

The paper
`Rethinking Persistent Scheduling in 5G New Radio Vehicle-to-Everything Sidelink Communications`
is useful here mainly because its PDF metadata already highlights the exact
themes that match our logs: `semi-persistent scheduling`, `autonomous resource
selection`, `persistence`, and `age of information`. That is why fields such as
`reservation_period_ms`, `max_num_per_reserve`, `resource_reselection_counter`,
`tbler`, and `prr` should be treated as first-class thesis variables.

## 1. Dataset view

| Название | Тип | Назначение | Пример |
| --- | --- | --- | --- |
| `run_manifest.json` | JSON manifest | Полная конфигурация прогона: сценарий, mode, SUMO config, Sionna scene, radio knobs, focus vehicle | `seed-017/run_manifest.json` |
| `run_summary.json` | JSON summary | Короткая итоговая сводка по seed | `seed-017/run_summary.json` |
| `seed_summary.csv` | Tabular summary | Thesis-ready KPI на один seed | `seed-017/seed_summary.csv` |
| `behavior/v2v-emergencyVehicleAlert-nrv2x.log` | Text log | Старт/завершение app run, handshake с Sionna, агрегаты по vehicle | `behavior/v2v-emergencyVehicleAlert-nrv2x.log` |
| `behavior/artifacts/eva-netstate.xml` | XML time series | Ground-truth траектории из SUMO по timestep | `behavior/artifacts/eva-netstate.xml` |
| `behavior/artifacts/eva-collision.xml` | XML events | Ground-truth столкновения из SUMO | `behavior/artifacts/eva-collision.xml` |
| `behavior/artifacts/eva-veh*-CAM.csv` | Per-vehicle CSV | Содержимое CAM на app side | `behavior/artifacts/eva-veh3-CAM.csv` |
| `behavior/artifacts/eva-veh*-MSG.csv` | Per-vehicle CSV | Леджер TX/RX сообщений на app side | `behavior/artifacts/eva-veh3-MSG.csv` |
| `behavior/artifacts/eva-veh*-CTRL.csv` | Per-vehicle CSV | Реакции контроллера на предупреждения и сенсоры | `behavior/artifacts/eva-veh3-CTRL.csv` |
| `behavior/artifacts/eva-veh*-PROFILE.csv` | Per-vehicle CSV | Снимок профиля приема и guardrail против legacy shims | `behavior/artifacts/eva-veh3-PROFILE.csv` |
| `behavior/artifacts/eva-veh*-PHY.csv` | Per-vehicle CSV | PHY-метрики, поднятые в app layer | `behavior/artifacts/eva-veh3-PHY.csv` |
| `collision_risk_timeseries.csv` | Time-series CSV | Минимальный gap и TTC по времени | `collision_risk/collision_risk_timeseries.csv` |
| `collision_risk_summary.csv` | Summary CSV | Safety summary по netstate | `collision_risk/collision_risk_summary.csv` |
| `drop_decision_timeline/event_timeline.csv` | Event CSV | Связка packet-drop -> later decision | `drop_decision_timeline/event_timeline.csv` |
| `drop_decision_timeline/summary.csv` | Summary CSV | Насколько хорошо drop events объясняют решения | `drop_decision_timeline/summary.csv` |
| `collision_causality.csv` | Event CSV | Структурная причинность для collision cases | `collision_causality/collision_causality.csv` |
| `collision_causality.md` | Markdown report | Читаемый отчет по collision causality | `collision_causality/collision_causality.md` |
| `native_nr/native_nr-pscch.csv` | Radio RX CSV | Прием `PSCCH`, декодирование SCI stage 1, reservation metadata | `native_nr/native_nr-pscch.csv` |
| `native_nr/native_nr-pscch-tx.csv` | Radio TX CSV | Передача `PSCCH`, структура reserve/retransmission | `native_nr/native_nr-pscch-tx.csv` |
| `native_nr/native_nr-pssch.csv` | Radio RX CSV | Прием `PSSCH`, TB corruption, SCI2 corruption, RB usage | `native_nr/native_nr-pssch.csv` |
| `native_nr/native_nr-pssch-tx.csv` | Radio TX CSV | Передача `PSSCH`, HARQ/NDI, L2 ids, reselection counters | `native_nr/native_nr-pssch-tx.csv` |
| `native_nr/native_nr-cam.csv` | Radio RX CSV | Радиопроба по каждому принятому CAM | `native_nr/native_nr-cam.csv` |
| `native_nr/native_nr-prr.csv` | Summary CSV | PRR по node id | `native_nr/native_nr-prr.csv` |
| `native_nr/native_nr-summary.txt` | Text summary | Короткая сводка native 5G-LENA sidecar | `native_nr/native_nr-summary.txt` |
| `native_nr/v2v-5g-phy-metrics-experiment.log` | Text log | Ход нативного PHY-эксперимента и список выведенных trace-файлов | `native_nr/v2v-5g-phy-metrics-experiment.log` |
| `sionna-server.log` | Text log | Запуск сервера Sionna, ready state, ray-matching latency | `analysis/thesis_campaign_calibration_smoke/.../sionna-server.log` |

## 2. Which simulator produces which data

### SUMO

- `eva-netstate.xml`
  Purpose: authoritative mobility truth.
  Structure: `netstate -> timestep -> edge -> lane -> vehicle`.
  Example row-equivalent: at `t=0.20`, `veh3` is on `c1_to_w_0` with
  `pos=42.00`, `speed=15.70`, while `veh2` is on `s1_to_w_0` with
  `pos=80.00`, `speed=16.40`.
- `eva-collision.xml`
  Purpose: authoritative collision truth.
  Structure: `collisions -> collision`.
  In the reference run it is empty, which matches `collision_flag=0`.

### ms-van3t / application layer

- `eva-veh*-MSG.csv`
  Purpose: message ledger at application level.
  Key fields: `vehicle_id,msg_seq,tx_t_s,rx_t_s,rx_ok,msg_type,tx_id,rx_id,cam_gdt_ms,pkt_uid`.
  Read it as: who transmitted, who received, when, and whether the payload made
  it to the app.
- `eva-veh*-CTRL.csv`
  Purpose: actual behavior decisions.
  Key fields:
  `time_s,vehicle_id,event_type,source_id,msg_seq,pkt_uid,distance_m,heading_diff_deg,lane_before,lane_after,target_speed_mps`.
  This is the key bridge between communication and vehicle behavior.
- `eva-veh*-PHY.csv`
  Purpose: PHY measurements promoted up to the app logs.
  Key fields:
  `sinr_dB,snr_dB,rssi_dBm,rsrp_dBm,pkt_size,distance_m,rx_ok`.
- `eva-veh*-CAM.csv`
  Purpose: decoded CAM payload content.
  Key fields:
  `messageId,camId,timestamp,latitude,longitude,heading,speed,acceleration`.
- `behavior/v2v-emergencyVehicleAlert-nrv2x.log`
  Purpose: quick sanity log for the full app run.
  It shows Sionna handshake plus per-vehicle totals such as
  `CAM-SENT`, `CAM-RECEIVED`, `CPM-RECEIVED`, and `CONTROL-ACTIONS`.

### 5G-LENA NR sidelink

- `native_nr-pscch.csv`
  Purpose: received control-channel trace.
  Key fields:
  `sinr_db,tbler,corrupt,priority,reservation_period_ms,total_subchannels,start_subchannel,length_subchannel,max_num_per_reserve`.
  This is where we see whether SCI stage 1 and resource reservation information
  survived interference and propagation.
- `native_nr-pscch-tx.csv`
  Purpose: transmitted control grants.
  Key fields:
  `priority,mcs,tb_size_bytes,reservation_period_ms,total_subchannels,start_subchannel,length_subchannel,max_num_per_reserve,gap_retx1,gap_retx2`.
- `native_nr-pssch.csv`
  Purpose: received data-channel trace.
  Key fields:
  `sinr_db,tbler,corrupt,ndi,tbler_sci2,sci2_corrupted,rb_start,rb_end,rb_assigned,dst_l2_id,src_l2_id`.
  This is the direct radio explanation for payload delivery or payload loss.
- `native_nr-pssch-tx.csv`
  Purpose: transmitted data-channel trace.
  Key fields:
  `harq_id,ndi,rv,src_l2_id,dst_l2_id,resource_reselection_counter,c_reselection_counter`.
  These counters are especially valuable for studying persistent scheduling and
  reselection behavior.
- `native_nr-cam.csv`
  Purpose: per-received CAM radio sample.
  Key fields:
  `tx_id,rx_id,distance_m,rssi_dbm,snr_db`.
- `native_nr-prr.csv`
  Purpose: node-level packet reception ratio.
  Key fields: `node_id,prr`.
- `native_nr-summary.txt`
  Purpose: compact radio experiment digest.
  Typical content:
  `MCS`, `Numerology`, `TX Power`, `Sensing`, `Sionna`, `Average PRR`,
  `Average latency`, `RX packets`, `TX packets`.

### Sionna RT

- `sionna-server.log`
  Purpose: channel backend execution log.
  Typical visible lines:
  `Setup complete. Working at 5.89 GHz, bandwidth ...`,
  `Matching took: ... ms`.
- Verbose request/response protocol
  Source: `src/sionna/sionna_v1_server_script.py`.
  Message families:
  `LOC_UPDATE`,
  `CALC_REQUEST_PATHGAIN` -> `CALC_DONE_PATHGAIN`,
  `CALC_REQUEST_DELAY` -> `CALC_DONE_DELAY`,
  `CALC_REQUEST_LOS` -> `CALC_DONE_LOS`.
  This is the cleanest dataset for proving what Sionna actually contributes:
  path gain, propagation delay, and LOS state.

## 3. Minimum cross-layer bundle for explaining behavior

If we want to explain one behavioral outcome rigorously, the minimum bundle is:

1. `eva-netstate.xml`
   For geometry truth and actual closing distance.
2. `native_nr-pscch.csv` and `native_nr-pssch.csv`
   For radio control/data decoding outcome.
3. `eva-veh*-MSG.csv` and `eva-veh*-CTRL.csv`
   For message delivery at app side and the resulting vehicle decision.
4. `seed_summary.csv` or `run_summary.json`
   For final KPI reporting.

## 4. What to analyze first in the thesis

For the persistent scheduling question, the highest-value fields are:

- `reservation_period_ms`
- `total_subchannels`
- `start_subchannel`
- `length_subchannel`
- `max_num_per_reserve`
- `resource_reselection_counter`
- `c_reselection_counter`
- `tbler`
- `corrupt`
- `sci2_corrupted`
- `prr`

These are the fields that most directly connect SPS behavior to packet loss,
warning usefulness, and finally to control actions or safety outcomes.
