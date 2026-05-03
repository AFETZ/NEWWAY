# Strict Intersection Scenario: `radar_good`

This note documents one strict thesis-ready scenario end to end, using the
completed headless run:

- run directory:
  `/home/afetz/work/clean/NEWWAY/analysis/strict_runs_smoke_full/strict_intersection/radar_good/seed-017`
- scenario id: `strict_intersection`
- mode: `radar_good`
- seed: `17`

## 1. Research role

This scenario is the cleanest cross-layer example for the thesis because all
four layers are visible in one run:

1. `SUMO` provides the ground-truth intersection geometry and vehicle motion.
2. `ms-van3t` application logic turns received warnings into vehicle control
   reactions.
3. `5G-LENA NR sidelink` decides whether `PSCCH` and `PSSCH` are decoded.
4. `Sionna RT` provides channel-side path gain, delay, and LOS information.

The scenario answers the question: does a yielding vehicle on the minor road
react early enough to a connected emergency vehicle on the major road when the
radio link is good and radar support is also enabled?

## 2. Road geometry and actors

The SUMO configuration is:

- net: `src/automotive/examples/sumo_files_v2i_map/map.net.xml`
- route file:
  `strict_sionna_vkr/scenarios/intersection/sumo/cars_intersection_strict.rou.xml`
- step length: `0.05 s`
- collision checks:
  `collision.mingap-factor=1.2`,
  `collision.check-junctions.mingap=1.0`

The active actors are:

- `veh2`: type `EmergencyMajor`, route `s1_to_w -> w_to_n1 -> n1_to_c1`,
  depart `0.2 s`, depart speed `16.4 m/s`.
- `veh3`: type `YieldMinor`, route `c1_to_w -> w_to_s1 -> s1_to_c1`,
  depart `0.2 s`, depart speed `15.7 m/s`.
- `veh4`: type `YieldMinor`, route `n1_to_w -> w_to_s1 -> s1_to_c1`,
  depart `0.6 s`, depart speed `14.8 m/s`.

The scenario is not hard-forced into one outcome. SUMO stochasticity is present
in the route file through:

- `sigma`
- `tau`
- `speedDev`
- `jmIgnoreFoeProb=0.05` for yielding vehicles

That means the exact timing remains seed-reproducible, but the behavior is not
scripted with a forced crash or forced lane change.

## 3. Strict radio setup

The strict manifest pins the NR sidelink parameters explicitly:

- `enableSensing=1`
- `numerologyBwpSl=2`
- `txPower=23 dBm`
- `mcs=14`
- `ReservationPeriod=20 ms`
- `slSensingWindow=100 ms`
- `slSelectionWindow=5`
- `slSubchannelSize=10 RB`
- `slMaxNumPerReserve=3`
- `slMaxTxTransNumPssch=5`
- `slProbResourceKeep=0`
- `slThresPsschRsrp=-126 dBm`
- `t1=2`, `t2=81`
- `tddPattern=UL|...|UL`
- `slBitMap=1|1|...|1`
- `enableChannelRandomness=1`
- `channelUpdatePeriod=100 ms`

So this run is a sensing-based Mode 2 SPS run, not a legacy profile-driven
drop experiment.

## 4. How the scenario works

The control loop is:

1. `SUMO` updates positions every `50 ms` and writes ground-truth state into
   `eva-netstate.xml`.
2. `TraCI + ms-van3t` push vehicle positions into ns-3 and the app stack.
3. `Sionna` receives `LOC_UPDATE` messages, refreshes the ray-traced scene, and
   answers `CALC_REQUEST_PATHGAIN`, `CALC_REQUEST_DELAY`, and
   `CALC_REQUEST_LOS`.
4. `5G-LENA` uses those channel conditions plus sidelink resource selection to
   schedule `PSCCH` and `PSSCH`.
5. The emergency vehicle broadcasts warnings. The yielding vehicle reacts only
   if the warning survives the full chain up to the app layer.
6. Radar remains available as a local sensing fallback, but in this run the
   first useful control action is communication-driven.

## 5. What happened in seed 17

The key outcome metrics are:

- `collision_flag = 0`
- `first_useful_warning_s = 2.29808`
- `first_control_action_s = 2.29808`
- `observed_prr_focus_vehicle = 1.0`
- `min_gap_m = 33.65`
- `min_ttc_s = 44.078`
- `pscch_corrupt_rate = 0.00341`
- `pssch_corrupt_rate = 0.05212`
- `pssch_overlap_pairs = 5`

The causal reading of this run is:

1. At `t = 0.20 s`, `veh2` and `veh3` are already present in the netstate on
   different incoming roads.
2. Native 5G-LENA traces show active `PSCCH` and `PSSCH` scheduling from about
   `2006.5 ms`.
3. At `t = 2.29808 s`, `veh3` logs the first `cam_reaction` to source station
   `2` at distance `51.3648 m` with a target speed of `3.3 m/s`.
4. `veh3` keeps reacting to later CAMs, which means the warning stream remains
   useful and timely.
5. SUMO reports no collision rows in `eva-collision.xml`, and the minimum gap
   remains safely above zero.

## 6. Why this scenario is useful for the thesis

This run gives a full causal chain that can be defended in the thesis:

- geometry truth comes from `SUMO`
- warning availability comes from `5G-LENA` decode outcomes
- channel realism comes from `Sionna`
- behavior change comes from `CTRL` events
- safety result comes from `netstate/collision`

Because the same run also exports native `PSCCH` and `PSSCH` traces, we can
explain *why* a warning was useful:

- `PSCCH` tells us whether SCI stage 1 and reservation information were decoded
- `PSSCH` tells us whether the payload TB reached the receiver
- `CTRL` tells us whether the receiver changed behavior

That is exactly the chain needed for a thesis chapter on how message losses in
NR sidelink propagate into connected and autonomous vehicle behavior.
