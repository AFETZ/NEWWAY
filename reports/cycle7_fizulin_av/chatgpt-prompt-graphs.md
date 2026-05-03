# Prompt for ChatGPT — IEEE-style Graphs

Copy the prompt below into ChatGPT (GPT-4o with code interpreter / Advanced Data Analysis). Upload the CSV files listed after the prompt.

---

## Files to Upload

1. `summary-all-runs.csv`
2. `per-vehicle-cam-from-ev.csv`
3. `inter-cam-gaps.csv`
4. `eva-good-speed-timeseries.csv`
5. `eva-vbad-speed-timeseries.csv`
6. `eva-lowpen-speed-timeseries.csv`

---

## Prompt

```
I have simulation results from an ns-3 NR V2X Mode 2 (5G sidelink) emergency vehicle alert scenario. I need 6 publication-quality figures in IEEE 2-column magazine style.

STYLE REQUIREMENTS:
- Figure width: 3.5 inches (single column) or 7 inches (double column)
- Font: Times New Roman or serif, 8-9 pt for labels, 7-8 pt for tick labels
- DPI: 300+
- Colors: use a colorblind-friendly palette (e.g., seaborn "colorblind" or tableau10). NO red-green only distinctions.
- Line width: 1.5 pt for data lines, 0.75 pt for grid
- Markers: distinct shapes per series (o, s, ^, D, v)
- Grid: light gray, dashed
- Legend: inside plot or below, compact
- No title on the figure (caption goes in LaTeX)
- Save each figure as PDF and PNG (300 DPI)
- Use matplotlib with rcParams set for IEEE style

CONTEXT:
- Scenario: emergency vehicle (veh1) broadcasts CAM via NR V2X Mode 2 sidelink
- 20 vehicles on a 2-lane loop, 100 s simulation
- Passenger vehicles react when they receive CAM from emergency vehicle within 75 m
- We varied: txPower (dBm), MCS, PSSCH retransmissions, bandwidth (MHz), shadowing, penetration rate
- Key metrics: PRR (Packet Reception Ratio), latency, inter-CAM gap, CAMs received

FIGURES TO CREATE:

### Figure 1: PRR and Latency vs Scenario (Dual-Axis Bar Chart)
- File: summary-all-runs.csv
- X-axis: scenario labels in order: "Baseline\n(23 dBm)", "Medium\n(10 dBm)", "High loss\n(5 dBm,\nMCS 20)", "Very high\n(0 dBm,\n1 retx,\n10 MHz)", "No retx\n(23 dBm,\n1 retx)"
- Left Y-axis: PRR (0.4 to 1.0), blue bars
- Right Y-axis: latency (ms, 0 to 40), red line with markers
- Annotate PRR values on top of each bar
- Single column width (3.5 in)

### Figure 2: CDF of Inter-CAM Gap from Emergency Vehicle
- File: inter-cam-gaps.csv
- X-axis: inter-arrival gap (ms), range 0–5000 ms
- Y-axis: CDF (0 to 1)
- One line per run: good, medium, bad, vbad
- Use legend labels: "Baseline (23 dBm)", "Medium (10 dBm)", "High loss (5 dBm)", "Very high (0 dBm)"
- Add vertical dashed lines at 100 ms (CAM period) and 1000 ms (1 s threshold) with small annotations
- Single column width (3.5 in)

### Figure 3: CAMs Received from Emergency Vehicle — Box Plot
- File: per-vehicle-cam-from-ev.csv
- Filter only runs: good, medium, bad, vbad
- X-axis: scenario labels (same as Fig 1, without "No retx")
- Y-axis: number of CAMs received from emergency vehicle (column: cams_from_ev)
- Box plot (matplotlib boxplot), show median, quartiles, outliers
- Annotate median value inside or above each box
- Single column width (3.5 in)

### Figure 4: Vehicle Speed Near Emergency Vehicle — Time Series Comparison
- Files: eva-good-speed-timeseries.csv, eva-vbad-speed-timeseries.csv, eva-lowpen-speed-timeseries.csv
- Plot speed of veh8 in all three runs on the same axes
- X-axis: simulation time (s), range 0–100
- Y-axis: speed (m/s)
- Three lines: "Baseline (PRR 99%)", "Very high loss (PRR 49%)", "Low penetration (30%)"
- If veh8 is absent at a given time, skip that point (don't interpolate)
- Double column width (7 in) or single column — your choice for clarity
- Add a shaded band marking the time window when veh8 is within 100m of veh1 (if detectable from position data)

### Figure 5: Parameter Sensitivity — Grouped Bar Chart
- File: summary-all-runs.csv
- Show three groups of bars: "PRR", "Normalized Latency", "Normalized CAMs from EV"
- Normalize latency and CAMs to baseline (good) values so all metrics are on 0–1 scale:
  - norm_latency = 1 - (latency / max_latency)  [higher = better]
  - norm_cams = avg_cam_ev / max(avg_cam_ev)
- Bars per scenario: Baseline, Medium, High loss, Very high loss
- Single column width (3.5 in)

### Figure 6: NR V2X Mode 2 Parameter Impact Summary (Radar/Spider Chart)
- File: summary-all-runs.csv
- Axes (5 spokes): PRR, 1/Latency (normalized), CAMs from EV (normalized), 1 - gaps_gt1000_pct/100, BW utilization (normalized)
- One polygon per scenario: Baseline, Medium, High loss, Very high loss
- Fill with alpha=0.15
- Single column width (3.5 in)

OUTPUT:
- Generate all 6 figures
- Show each figure inline
- Provide download links for PDF and PNG versions
- At the end, provide a LaTeX snippet with \includegraphics and \caption for each figure, suitable for a 2-column IEEE paper using IEEEtran class
```

---

## Alternative: Simpler 4-Figure Set

If 6 figures is too many for the paper, prioritize:
1. **Figure 1** (PRR + Latency) — the headline result
2. **Figure 2** (CDF of inter-CAM gap) — shows real-world impact on awareness
3. **Figure 3** (Box plot CAMs from EV) — shows per-vehicle variance
4. **Figure 4** (Speed time series) — connects to vehicle behavior

These 4 tell the complete story: channel degrades -> packets lost -> awareness gaps grow -> vehicle behavior affected.
