# Mode 2 Visual + Proof Workflow

## Live visualization (SUMO + web map)

Run:

```bash
analysis/mode2_loss/run_live_visual_demo.sh
```

While simulation is running:

- SUMO GUI is enabled (`--sumo-gui=1`)
- Web vehicle visualizer is enabled (`--vehicle-visualizer=1`)
- Open `http://localhost:8080`

Optional parameters:

```bash
SIM_TIME=60 TX_POWER=10 MCS=14 analysis/mode2_loss/run_live_visual_demo.sh my_live_run
```

## Generated evidence

The live script writes:

- raw run logs and CSVs in `analysis/mode2_loss/data/live/<run_id>`
- processed metrics in `analysis/mode2_loss/data/live/<run_id>/results`
- figures in `analysis/mode2_loss/data/live/<run_id>/figures`
- SUMO netstate dump in `analysis/mode2_loss/data/live/<run_id>/sumo_netstate.xml`

`make_plots.py` also generates packet-specific visuals:

- `packet_activity_<run_id>.png` (TX/RX rates and window PRR over time)
- `packet_link_heatmap_<run_id>.png` (TX->RX reception matrix)
- `packet_flights_map_<run_id>.png` (vehicle trajectories + packet flight segments)

And updates the proof report:

- `analysis/mode2_loss/REPORT_mode2_loss.md`

## CARLA + Sionna + NR-V2X

If CARLA/OpenCDA and Sionna are installed, run:

```bash
analysis/mode2_loss/run_carla_sionna_nrv2x.sh /path/to/ns-3-dev
```

The script checks:

- `CARLA-OpenCDA.conf` existence and required keys
- `CARLA_HOME`, `OpenCDA_HOME`, `Python_Interpreter` paths
- `tensorflow` and `sionna` modules in the configured Python interpreter
- availability of `ns3-dev-v2v-carla-nrv2x-optimized` (builds target if missing)

Useful overrides:

```bash
SIM_TIME=30s SIONNA_GPU=0 OPENCDA_CONFIG=ms_van3t_example analysis/mode2_loss/run_carla_sionna_nrv2x.sh /path/to/ns-3-dev
```
