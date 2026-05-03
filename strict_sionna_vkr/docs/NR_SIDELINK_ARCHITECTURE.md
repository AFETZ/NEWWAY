# NR_SIDELINK_ARCHITECTURE

## Stack In This Repo

The strict thesis stack in this repository is:

`SUMO mobility -> TraCI synchronization -> ms-van3t application logic -> 5G-LENA NR sidelink Mode 2 -> Sionna RT channel backend -> analysis`

The important architectural split is:

- `5G-LENA` performs sidelink bearer setup, RRC preconfiguration, Mode 2 resource
  selection, SCI handling, HARQ/blind retransmission logic, SINR/TBLER evaluation,
  and decode success/failure.
- `Sionna` only replaces channel-space quantities for a node pair:
  - path gain
  - propagation delay
  - LOS/NLOS state

## What NR V2X Mode 2 Means Here

The relevant code path is centered around `NrSlHelper`, `NrSlUeMac`,
`NrSlCommPreconfigResourcePoolFactory`, and the example
`v2v-emergencyVehicleAlert-nrv2x`.

This repo uses out-of-coverage NR sidelink with:

- broadcast/groupcast communication;
- UE-selected Mode 2 resource selection;
- blind retransmissions;
- fixed MCS scheduling;
- TDD sidelink pools preconfigured through RRC.

## Resource Pool And Scheduling Parameters

The strict package makes the following parameters explicit because they materially
change packet timing, collisions, and decode probability:

- `txPower`
- `numerologyBwpSl`
- `tddPattern`
- `slBitMap`
- `slSensingWindow`
- `slSelectionWindow`
- `slSubchannelSize`
- `slMaxNumPerReserve`
- `slProbResourceKeep`
- `slMaxTxTransNumPssch`
- `ReservationPeriod`
- `enableSensing`
- `t1`
- `t2`
- `slThresPsschRsrp`
- `mcs`
- `enableChannelRandomness`
- `channelUpdatePeriod`

Strict defaults are frozen in `manifests/strict_defaults.json`.

## PSCCH And PSSCH Roles

### PSCCH

`PSCCH` carries SCI stage 1. In this repo it directly influences two things:

- sensing-based resource selection at neighboring UEs;
- the receiver-side understanding of where and when the corresponding `PSSCH`
  transmission and retransmissions may appear.

Key fields visible in the trace path include:

- priority
- MCS
- reservation period
- total subchannels
- start subchannel
- subchannel length
- max reservations per SCI
- retransmission gaps

### PSSCH

`PSSCH` carries SCI stage 2 and the actual CAM/CPM payload. In strict scenarios,
this is the final gate before a cooperative warning reaches the vehicle controller.

If `PSSCH` fails, the application never sees a valid CAM/CPM event even if the
channel reservation was visible through `PSCCH`.

## Sensing-Based SPS In This Repo

The core logic sits in `NrSlUeMac`:

- the MAC builds a future candidate window from `T1`, `T2`, current slot, pool, and reservation period;
- if sensing is enabled, the MAC expands received SCI into future reservation candidates;
- candidates that fully overlap occupied subchannels and exceed the RSRP threshold
  are removed;
- if too few candidates remain, the threshold is gradually relaxed;
- the scheduler then picks slot/subchannel allocations and creates SPS grants.

This means strict “good” and “bad” radio profiles should come from native knobs
such as `txPower`, `slThresPsschRsrp`, density, and load, not from manual packet drops.

## Critical Audit Finding

The legacy thesis wrappers around `v2v-emergencyVehicleAlert-nrv2x` did not expose
the full Mode 2 configuration explicitly. In practice, many of them inherited the
example defaults. The most important consequence is that the example default
`enableSensing=false` made several previous runs closer to random selection than to
strict sensing-based Mode 2 SPS.

The strict package fixes this by:

- freezing all radio defaults in manifests;
- rejecting hidden legacy shims;
- requiring `enableSensing=1` in every strict manifest.

## Native Radio Evidence

The strict package captures native NR V2X evidence through a sidecar run of
`v2v-5g-phy-metrics-experiment` configured with the same SUMO and radio parameters.

The sidecar exports:

- `pscch.csv`
- `pscch-tx.csv`
- `pssch.csv`
- `pssch-tx.csv`
- `cam.csv`
- `prr.csv`

This allows the strict summaries to report:

- observed PRR;
- `PSCCH` corruption;
- `PSSCH` TB corruption;
- `SCI2` corruption;
- overlapping `PSSCH` TX opportunities derived from native TX scheduling traces.

## Sionna Role And Limitation

Sionna integration is active through the propagation loss and propagation delay
models plus periodic `LOC_UPDATE` synchronization from TraCI.

Strict conclusions may claim:

- geometry-sensitive path gain;
- LOS/NLOS dependence;
- propagation delay from Sionna.

Strict conclusions must not claim:

- Doppler realism driven by orientation/velocity updates,
because the current Sionna bridge still carries a FIXME around those updates.
