# SCENARIO_ROLE_MATRIX

## Common Interpretation

Across all strict scenarios:

- `PSCCH` determines how other UEs sense the medium and foresee future reserved slots.
- `PSSCH` determines whether a useful warning reaches the receiving controller.
- `Sionna` determines pairwise path gain, LOS, and propagation delay.
- SUMO local dynamics determine whether an early or late warning becomes a lane change,
  braking action, missed gap, or collision.

## strict_lane_obstacle

### Physical Situation

- `veh2` is the emergency lead vehicle and becomes the incident source.
- `veh4` is the critical follower.
- surrounding background vehicles create or close a merge window on the adjacent lane.

### Network Role

- `veh2` broadcasts CAM over NR sidelink.
- `veh4` is the key receiver whose reaction timing decides whether the merge window
  is used in time.

### Controller Meaning

- early `PSSCH` success means `veh4` reacts while a lane-change window still exists;
- late or missing `PSSCH` means the adjacent lane has already closed or the stopping
  distance is insufficient.

### KPIs

- first useful CAM warning at `veh4`
- first control action at `veh4`
- first lane change time
- `veh4 <- veh2` observed PRR
- collision / min gap / min TTC

## strict_intersection

### Physical Situation

- `veh2` approaches on the major stream;
- `veh3` approaches from the minor stream;
- local radar is available on `veh3`.

### Network Role

- `radar_only`: V2X behavior path is disabled, only local sensing can trigger action;
- `radar_bad`: radar stays enabled, but NR sidelink delivery is degraded using native radio knobs only;
- `radar_good`: radar stays enabled and NR sidelink remains favorable.

### Controller Meaning

- `PSCCH` and `PSSCH` success control how early `veh3` can learn about the conflict
  before the object is locally visible by radar alone.
- radar remains the local fallback, not the communication path.

### KPIs

- first CAM-driven reaction at `veh3`
- first radar-driven reaction at `veh3`
- `veh3 <- veh2` observed PRR
- `PSCCH` corruption / `PSSCH` corruption
- collision / min gap / min TTC

## strict_onramp_merge

### Physical Situation

- `veh2` travels on the mainline as the emergency broadcaster;
- `veh3` enters from the ramp and is the critical merge vehicle;
- mainline background flow creates a seed-dependent merge opportunity.

### Network Role

- `veh3` receives CAM over NR sidelink while still on the ramp approach.
- the warning timing changes whether `veh3` slows before the merge point or enters the
  conflict zone under poor awareness.

### Controller Meaning

- successful early `PSSCH` decode turns the maneuver into a controlled merge or merge abort;
- missing/late delivery produces a late reaction and a tighter merge conflict.

### KPIs

- first useful CAM warning at `veh3`
- first control action at `veh3`
- merge success / collision
- `veh3 <- veh2` observed PRR
- `PSCCH` corruption / `PSSCH` corruption
- min gap / min TTC / first lane change
