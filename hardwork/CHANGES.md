# De-hardcoding Intersection Crash Scenario

## Problem

The intersection scenario looked artificial:
- Vehicle IDs (`veh2`, `veh3`, `veh4`) were hardcoded across 30+ shell variables
- `crash-mode` forced speed to 30 m/s via `setSpeedMode(0)` + `setSpeed()` — a direct
  SUMO hack that bypasses all physics
- `unaware-mode` replaced crash-mode but still used counters ("3 missed CAMs → activate")
  which was still deterministic hardcoding
- `equiv_tx_power_dbm` and `target_prr` appeared to be decorative annotations

## What Was Already Good (Discovered During Analysis)

`equiv_tx_power_dbm` **already works at PHY level** — it adjusts the NR UE noise figure
in `v2v-emergencyVehicleAlert-nrv2x.cc:1199-1213`, causing real SINR degradation through
Sionna's channel model. This was not obvious from the shell script.

## Final Design: V2X Awareness Junction

The key insight: **channel quality alone should determine the outcome**. No counters,
no thresholds, no timers. The mechanism is simple:

1. Non-emergency vehicles start **without** junction right-of-way awareness
   (SUMO speedMode bit 3 = off, i.e. speedMode=23)
2. The **first received CAM** from an emergency vehicle grants junction awareness
   (speedMode bit 3 = on, i.e. speedMode=31)
3. If no CAM ever arrives (bad channel), the vehicle never yields → collision
4. If a CAM arrives (good channel), the vehicle yields → safe pass

This is a single boolean mechanism with zero tunable parameters.

### What Makes This NOT Hardcoded

| Aspect | Old (crash-mode) | Middle (unaware-mode) | New (v2x-awareness) |
|--------|------------------|-----------------------|--------------------|
| Trigger | N consecutive drops | N consecutive drops | **First CAM received** |
| Tunable params | 5 (threshold, duration, min-time, vehicle-id, force-speed) | 5 (threshold, duration, min-time, vehicle-id, enable) | **1** (enable) |
| Physics | SUMO safety disabled | SUMO speedMode bit 3 cleared | **Same bit 3, but restored by CAM** |
| Determinism | Forced at threshold | Forced at threshold | **Determined by channel** |
| Collision cause | Artificial speed | Timer-based | **Genuinely unknown to vehicle** |

### How the Experiment Works

To show "bad channel → collision, good channel → safe pass":

```bash
# Collision scenario: obstructed vehicle has degraded channel (-30 dBm equiv)
ROLE_OBSTRUCTED_EQ_DBM=-30 ./hardwork/run_intersection_natural.sh

# Safe scenario: all vehicles have good channel
ROLE_OBSTRUCTED_EQ_DBM=23 ./hardwork/run_intersection_natural.sh
```

The ONLY difference is `equiv_tx_power_dbm`. Everything else is identical.
The outcome (collision or safe pass) depends entirely on whether the NR PHY
channel delivers the emergency CAM to the obstructed vehicle.

## Changes Made

### 1. V2X Awareness Junction (C++ — `emergencyVehicleAlert.cc/.h`)

Single ns-3 attribute:
- `V2xAwarenessJunctionEnable` (bool, default false)

Single command-line argument:
- `--v2x-awareness-junction`

Implementation:
- `StartApplication`: sets speedMode=23 for non-emergency vehicles when enabled
- `GrantJunctionAwareness()`: called on first emergency CAM reception, restores speedMode=31
- `receiveCAM`: calls `GrantJunctionAwareness()` when receiving from emergency vehicle

Removed (from previous unaware-mode):
- `UnawareModeEnable`, `UnawareModeVehicleId`, `UnawareModeNoActionThreshold`,
  `UnawareModeDurationS`, `UnawareModeMinTimeS` — all 5 attributes
- `MaybeTriggerUnawareMode()` method and all its counter/timer logic
- All `m_unaware_mode_*` member variables

### 2. CAM Silence Inference Updated

Previously gated on `m_unaware_mode_enable`. Now gated on
`m_v2x_awareness_junction_enable` — silence inference works whenever the
junction awareness mechanism is active.

### 3. Role-Based Shell Configuration (`hardwork/run_intersection_natural.sh`)

| Old | New |
|-----|-----|
| `--unaware-mode-enable=1` | `--v2x-awareness-junction=1` |
| `--unaware-mode-vehicle-id=veh3` | *(removed — applies to ALL non-emergency)* |
| `--unaware-mode-no-action-threshold=3` | *(removed — no threshold)* |
| `--unaware-mode-duration-s=5.0` | *(removed — no duration)* |
| `--unaware-mode-min-time-s=3.8` | *(removed — no min time)* |

5 parameters replaced by 1.

## Files Modified

| File | Change |
|------|--------|
| `src/automotive/model/Applications/emergencyVehicleAlert.h` | Replaced unaware-mode fields with 2 v2x-awareness fields |
| `src/automotive/model/Applications/emergencyVehicleAlert.cc` | Implemented GrantJunctionAwareness, removed MaybeTriggerUnawareMode |
| `src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc` | Single --v2x-awareness-junction arg |
| `hardwork/run_intersection_natural.sh` | Updated to use --v2x-awareness-junction=1 |

## How to Use

```bash
# Natural scenario — channel quality determines outcome
cd /home/afetz/work/clean/NEWWAY
SUMO_GUI=1 USE_SIONNA=1 ./hardwork/run_intersection_natural.sh

# Override channel quality to test hypothesis:
# Bad channel → collision
ROLE_OBSTRUCTED_EQ_DBM=-30 ./hardwork/run_intersection_natural.sh

# Good channel → safe pass
ROLE_OBSTRUCTED_EQ_DBM=23 ./hardwork/run_intersection_natural.sh
```

## For VKR Presentation

The scenario demonstrates the hypothesis:
> "If V2X channel quality is below threshold X, the emergency CAM is not delivered,
> and the vehicle collides. If channel quality is above threshold Y, the CAM is
> delivered, and the vehicle yields safely."

The threshold is NOT set by us — it emerges from the NR PHY channel model (Sionna).
We only set `equiv_tx_power_dbm` to model different propagation conditions (LOS vs NLOS,
antenna impairment, interference). The PHY model decides whether the packet gets through.

## Backward Compatibility

- Old `crash-mode` is fully preserved and still works unchanged
- Old `valid_intersection_scenario/run.sh` works exactly as before
- New `v2x-awareness-junction` is opt-in via `--v2x-awareness-junction=1`
