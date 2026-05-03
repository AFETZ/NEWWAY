# Архитектура NR Sidelink

## Стек в этом репозитории

```
SUMO mobility → TraCI synchronization → ms-van3t application logic
    → 5G-LENA NR sidelink Mode 2 → Sionna RT channel backend → analysis
```

### Разделение ответственности

| Компонент | Что делает |
|---|---|
| **5G-LENA** | Sidelink bearer setup, RRC preconfiguration, Mode 2 resource selection, SCI handling, HARQ/blind retransmission, SINR/TBLER evaluation, decode success/failure |
| **Sionna** | Только channel-space: path gain, propagation delay, LOS/NLOS state |

## Что значит NR V2X Mode 2

Ключевой code path: `NrSlHelper`, `NrSlUeMac`, `NrSlCommPreconfigResourcePoolFactory`, пример `v2v-emergencyVehicleAlert-nrv2x`.

Проект использует **out-of-coverage NR sidelink** с:

- Broadcast/groupcast communication
- UE-selected Mode 2 resource selection
- Blind retransmissions
- Fixed MCS scheduling
- TDD sidelink pools (preconfigured через RRC)

## Resource Pool параметры

Строгий пакет (`strict_sionna_vkr`) делает следующие параметры явными, т.к. они материально влияют на timing пакетов, коллизии и decode probability:

| Параметр | Описание |
|---|---|
| `txPower` | Мощность передачи |
| `numerologyBwpSl` | Numerology для sidelink BWP |
| `tddPattern` | TDD паттерн (DL/UL/SL slots) |
| `slBitMap` | Bitmap доступных sidelink слотов |
| `slSensingWindow` | Окно sensing для Mode 2 |
| `slSelectionWindow` | Окно выбора ресурсов |
| `slSubchannelSize` | Размер подканала |
| `slMaxNumPerReserve` | Макс. резерваций на одно SCI |
| `slProbResourceKeep` | Вероятность удержания ресурса |
| `slMaxTxTransNumPssch` | Макс. число PSSCH передач |
| `ReservationPeriod` | Период резервирования |
| `enableSensing` | Включить sensing-based selection |
| `t1`, `t2` | Границы окна выбора |
| `slThresPsschRsrp` | Порог RSRP для PSSCH |
| `mcs` | Modulation and coding scheme |
| `enableChannelRandomness` | Случайность канала |
| `channelUpdatePeriod` | Период обновления канала |

Строгие defaults заморожены в `experiments/strict_sionna_vkr/manifests/strict_defaults.json`.

## PSCCH и PSSCH

### PSCCH (Physical Sidelink Control Channel)

Несёт **SCI stage 1**. Влияет на:
- Sensing-based resource selection у соседних UE
- Понимание приёмником, где и когда появятся PSSCH передачи и ретрансмиссии

Ключевые поля в trace:
- Priority, MCS, reservation period
- Total subchannels, start subchannel, subchannel length
- Max reservations per SCI
- Retransmission gaps

### PSSCH (Physical Sidelink Shared Channel)

Несёт **SCI stage 2 + data (transport block)**. Это канал, по которому передаются:
- CAM (Cooperative Awareness Messages)
- DENM (Decentralized Environmental Notification Messages)
- CPM (Collective Perception Messages)

## Связь с экспериментами

В нестрогих сценариях (`truck_lane_change`, `intersection_crash`) используются **per-vehicle профили** (`equiv_tx_power_dbm`, `target PRR`) для детерминированного управления потерями.

В строгих сценариях (`strict_sionna_vkr`) все потери определяются исключительно **PHY/MAC + Sionna**, без искусственных шимов.
