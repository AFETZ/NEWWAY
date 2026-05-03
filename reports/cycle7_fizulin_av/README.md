# Emergency Vehicle Alert — NR V2X Mode 2 Simulation Results

## Scenario

**v2v-emergencyVehicleAlert-nrv2x** (ms-van3t / ns-3)

An emergency vehicle (veh1) broadcasts CAM messages via 5G NR V2X Mode 2 sidelink.
Passenger vehicles receiving the CAM within 75 m and heading difference < 45 deg react:
- Lane 0: slow down to 50% max speed + attempt lane change
- Lane 1: speed up to 150% + hold lane
- Timeout: 3 s — if no new CAM, revert to normal speed

20 vehicles on a 2-lane loop road (SUMO), simulation time 100 s.

---

## Experiment Matrix

| Run | Label | TxPower (dBm) | MCS | Retx | BW (MHz) | Shadowing | PenRate | PRR | Latency (ms) |
|-----|-------|---------------|-----|------|-----------|-----------|---------|-----|--------------|
| 1 | good | 23 | 14 | 5 | 400 | OFF | 1.0 | 99.2% | 11.4 |
| 2 | medium | 10 | 14 | 5 | 400 | ON | 1.0 | 97.5% | 17.8 |
| 3 | bad | 5 | 20 | 5 | 400 | ON | 1.0 | 89.9% | 29.1 |
| 4 | vbad | 0 | 20 | 1 | 10 | ON | 1.0 | 48.7% | 33.1 |
| 5 | noretx | 23 | 14 | 1 | 400 | ON | 1.0 | 99.2% | 12.4 |
| 6 | lowpen | 23 | 14 | 5 | 400 | OFF | 0.3 | 98.6% | 12.1 |

### Commands used

```bash
# 1. good (baseline)
./ns3 run "v2v-emergencyVehicleAlert-nrv2x --txPower=23 --mcs=14 --enableChannelRandomness=false --penetrationRate=1.0 --simTime=100 --sumo-gui=false --csv-log=run-out/eva-good --csv-log-cumulative=run-out/eva-good-cumul --netstate-dump-file=run-out/eva-good-netstate.xml --met-sup=true --baseline=150"

# 2. medium (reduced power + shadowing)
./ns3 run "v2v-emergencyVehicleAlert-nrv2x --txPower=10 --mcs=14 --enableChannelRandomness=true --channelUpdatePeriod=100 --penetrationRate=1.0 --simTime=100 --sumo-gui=false --csv-log=run-out/eva-medium --csv-log-cumulative=run-out/eva-medium-cumul --netstate-dump-file=run-out/eva-medium-netstate.xml --met-sup=true --baseline=150"

# 3. bad (low power + high MCS + shadowing)
./ns3 run "v2v-emergencyVehicleAlert-nrv2x --txPower=5 --mcs=20 --enableChannelRandomness=true --channelUpdatePeriod=100 --penetrationRate=1.0 --simTime=100 --sumo-gui=false --csv-log=run-out/eva-bad --csv-log-cumulative=run-out/eva-bad-cumul --netstate-dump-file=run-out/eva-bad-netstate.xml --met-sup=true --baseline=150"

# 4. vbad (extreme: no retx + narrow BW + 0 dBm)
./ns3 run "v2v-emergencyVehicleAlert-nrv2x --txPower=0 --mcs=20 --slMaxTxTransNumPssch=1 --bandwidthBandSl=10 --enableChannelRandomness=true --channelUpdatePeriod=100 --penetrationRate=1.0 --simTime=100 --sumo-gui=false --csv-log=run-out/eva-vbad --csv-log-cumulative=run-out/eva-vbad-cumul --netstate-dump-file=run-out/eva-vbad-netstate.xml --met-sup=true --baseline=150"

# 5. noretx (only disable retransmissions)
./ns3 run "v2v-emergencyVehicleAlert-nrv2x --txPower=23 --mcs=14 --slMaxTxTransNumPssch=1 --enableChannelRandomness=true --channelUpdatePeriod=100 --penetrationRate=1.0 --simTime=100 --sumo-gui=false --csv-log=run-out/eva-noretx --csv-log-cumulative=run-out/eva-noretx-cumul --netstate-dump-file=run-out/eva-noretx-netstate.xml --met-sup=true --baseline=150"

# 6. lowpen (30% equipped vehicles)
./ns3 run "v2v-emergencyVehicleAlert-nrv2x --txPower=23 --mcs=14 --enableChannelRandomness=false --penetrationRate=0.3 --simTime=100 --sumo-gui=false --csv-log=run-out/eva-lowpen --csv-log-cumulative=run-out/eva-lowpen-cumul --netstate-dump-file=run-out/eva-lowpen-netstate.xml --met-sup=true --baseline=150"
```

---

## Key Findings

1. **PRR degrades gracefully**: 99.2% -> 97.5% -> 89.9% -> 48.7% as channel conditions worsen.
2. **Latency is more sensitive**: 11.4 ms -> 17.8 ms -> 29.1 ms -> 33.1 ms (x3 increase).
3. **CAMs from emergency vehicle**: avg 185 (good) -> 132 (bad) -> 51 (vbad). Some vehicles in vbad received only 11 CAMs (vs 185 baseline — 94% loss).
4. **Inter-CAM gaps grow**: median 200 ms (good) -> 600 ms (vbad); worst-case gap 2.4 s (good) -> 28.5 s (vbad).
5. **Vehicle behavior is robust at PRR > 89%**: lane changes and speed profiles are identical between good/medium/bad because the reaction triggers at <75 m where the signal is still strong.
6. **At PRR ~49% (vbad)**: behavioral differences start to appear.
7. **Penetration rate (lowpen)**: unequipped vehicles (70%) never react — most direct behavioral impact.

---

## Output Files

### Summary Data (for graphs)
- `summary-all-runs.csv` — consolidated table of all runs with PRR, latency, parameters
- `per-vehicle-cam-from-ev.csv` — CAMs received from emergency vehicle per vehicle per run
- `inter-cam-gaps.csv` — inter-arrival gaps between consecutive CAMs from emergency vehicle
- `eva-{run}-speed-timeseries.csv` — per-vehicle speed & lane every 1 s (runs: good, bad, vbad, lowpen)

### Raw Data
- `eva-{run}-cumul.csv` — aggregate PRR and latency
- `eva-{run}-vehX-CAM.csv` — per-vehicle received CAM details
- `eva-{run}-netstate.xml` — SUMO vehicle state dump (position, speed, lane every 0.01 s)

---

## Proposed Graphs

### Figure 1: PRR vs NR V2X Configuration (Bar Chart)
- X-axis: scenario labels (Baseline, Medium, High loss, Very high loss, No retx)
- Y-axis: Packet Reception Ratio (0–1)
- Shows impact of txPower, MCS, retransmissions, bandwidth on PRR
- Data source: `summary-all-runs.csv`

### Figure 2: End-to-End Latency vs Configuration (Bar Chart with Error Bars)
- X-axis: same scenarios
- Y-axis: average one-way latency (ms)
- Dual Y-axis or annotation with PRR for correlation
- Data source: `summary-all-runs.csv`

### Figure 3: CDF of Inter-CAM Gap from Emergency Vehicle
- X-axis: inter-arrival gap (ms), log scale
- Y-axis: CDF (0–1)
- One line per scenario (good, medium, bad, vbad)
- Shows how packet loss translates to awareness gaps
- Key thresholds: 100 ms (CAM generation), 500 ms, 1000 ms
- Data source: `inter-cam-gaps.csv`

### Figure 4: CAMs Received from Emergency Vehicle per Vehicle (Box Plot)
- X-axis: scenario
- Y-axis: number of CAMs received from emergency vehicle
- Box plot showing distribution across 19 vehicles
- Highlights variance (vbad: veh3=189 vs veh6=11)
- Data source: `per-vehicle-cam-from-ev.csv`

### Figure 5: Vehicle Speed Profiles Near Emergency Vehicle (Time Series)
- X-axis: simulation time (s)
- Y-axis: speed (m/s)
- Panel or overlay: good vs vbad vs lowpen
- Track 2-3 specific vehicles (veh8, veh15) that show clear differences
- Data source: `eva-{run}-speed-timeseries.csv`

### Figure 6: Parameter Sensitivity (Grouped Bar or Heatmap)
- Parameters: txPower, MCS, retx count, bandwidth
- Metrics: PRR, latency, avg CAMs from EV
- Shows which parameter has the strongest impact
- Data source: `summary-all-runs.csv`

---

## ChatGPT Prompt for Graph Generation

See `chatgpt-prompt-graphs.md` in this directory.
