# strict_sionna_vkr

Additive-only thesis package for strict `SUMO + ns-3/5G-LENA sidelink + Sionna RT`
experiments.

## What Is Here

- `docs/NR_SIDELINK_ARCHITECTURE.md`
  - repo-level audit of 5G-LENA sidelink, Mode 2 SPS, PSCCH/PSSCH, and Sionna role
- `docs/SCENARIO_ROLE_MATRIX.md`
  - strict mapping of network/channel/sensor roles into the three thesis scenarios
- `manifests/`
  - frozen scenario/mode definitions with explicit radio parameters
- `scenarios/`
  - strict SUMO assets
- `sionna_scenes/`
  - per-scenario Sionna scene entrypoints plus registration notes
- `scripts/`
  - strict runner, batch runner, calibration runner, summarizer, and native PHY sidecar runner

## Scenario Set

- `strict_lane_obstacle`
  - stopped emergency lead vehicle, following passenger reacts via NR sidelink
- `strict_intersection`
  - `radar_only`, `radar_bad`, `radar_good`
- `strict_onramp_merge`
  - mainline emergency vehicle + ramp merge conflict

## Strict Guarantees

- all manifests explicitly set Mode 2 parameters;
- all strict modes force `enableSensing=1`;
- forbidden legacy shims are rejected:
  - `per-vehicle-prr-profile`
  - `equiv_tx_power_dbm`
  - `target-loss-profile`
  - `rx-drop-prob-*`
  - `crash-mode`

## Usage

Run a single scenario/mode:

```bash
python3 strict_sionna_vkr/scripts/run_strict_scenario.py \
  --manifest strict_sionna_vkr/manifests/strict_intersection/radar_good.json \
  --out-root analysis/strict_runs
```

Run a batch over seeds:

```bash
python3 strict_sionna_vkr/scripts/run_strict_batch.py \
  --scenario strict_intersection \
  --out-root analysis/strict_runs \
  --seeds 11,12,13,14,15
```

Run native radio calibration sweep:

```bash
python3 strict_sionna_vkr/scripts/run_radio_calibration.py \
  --manifest strict_sionna_vkr/manifests/strict_intersection/radar_good.json \
  --out-root analysis/strict_calibration
```

Start Sionna with a strict scene:

```bash
strict_sionna_vkr/scripts/start_sionna_server.sh \
  strict_sionna_vkr/sionna_scenes/strict_intersection/scene.xml
```

Wait for `Setup complete.` in the Sionna server terminal before launching strict runs.

## Notes

- The behavior run is executed with `v2v-emergencyVehicleAlert-nrv2x`.
- Native `PSCCH/PSSCH` evidence is captured by a sidecar run using
  `v2v-5g-phy-metrics-experiment` under the same SUMO/radio settings.
- Current Sionna conclusions remain limited to path gain, propagation delay, and LOS.
  Doppler-level claims stay out of scope until the existing velocity/orientation FIXME
  is resolved in the Sionna bridge.
