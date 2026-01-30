*** Begin Patch
*** Delete File: README.md
*** Add File: README.md
+# Sionna–SUMO 3D Ray‑Tracing V2X Simulation
+
+This repository contains the operational code, scenario assets, and helper scripts used to generate **3D ray‑tracing RSSI / path‑loss traces** by coupling **SUMO** (microscopic traffic simulation) with **Sionna RT** (GPU‑accelerated ray tracing for wireless propagation). It is the reference implementation for the experiments reported in our IEEE Access paper.
+
+## Overview and Architecture
+
+The simulation pipeline orchestrates two components:
+
+1. **Mobility generation** – SUMO runs as a remote server to produce vehicle positions over time based on a road network and traffic configuration. Vehicle coordinates are read from SUMO via the TraCI interface.
+2. **Propagation modelling** – Sionna RT loads a 3D scene (environment and terrain meshes) and computes propagation paths between vehicles using the `PathSolver`. The solver returns complex path gains, which are post‑processed to derive received power (RSSI) and path‑loss metrics. Optional rendering produces per‑frame images of the scene.
+
+Each simulation step consists of advancing the SUMO simulation, obtaining the positions of transmitting and receiving vehicles, computing propagation paths via Sionna RT, and logging RSSI/path‑loss values. The process repeats for the duration of the SUMO scenario.
+
+## Repository Contents
+
+- `scenarios/` – Scenario folders containing road network definitions (`sumo_dir/osm.sumocfg`), 3D scene descriptions (`scenario.xml`), and terrain meshes (`terrain.xml`). Each scenario is self‑contained.
+- `signal_propagation_3d_RT.py` – Main Python script that orchestrates SUMO and Sionna RT. It spawns SUMO as a subprocess, connects via TraCI, loads the Sionna scene, and steps through the simulation, computing ray‑tracing metrics and optional renders.
+- `requirements.txt` – Pinned Python dependencies to reproduce the environment (including `sionna==1.0.1`, `sionna-rt==1.0.1`, `tensorflow==2.19.0`, `mitsuba==3.6.2`, `drjit==1.0.3`, and SUMO Python bindings).
+- `test.ipynb` – Jupyter notebook with exploratory examples.
+- `blender_auto.py` and `blender_projection.py` – Helper scripts for importing OpenStreetMap data into Blender and projecting vehicle trajectories onto terrain meshes.
+- `path_loss_graphs.py` and `graphs_handler.py` – Plotting utilities for the generated trace data.
+- `frames2video.py` – Utility to assemble rendered frames into a video.
+
+## Prerequisites
+
+- **Python** 3.8 or higher.
+- **SUMO** ≥ 1.22 installed and accessible via the `sumo` command.
+- **CUDA‑capable GPU** (recommended for Sionna RT). Sionna RT can fall back to CPU execution (LLVM backend) if no compatible GPU is available, but performance will be significantly reduced.
+- (Optional) **Blender** ≥ 4.4 with the Blosm add‑on, if you wish to build or modify 3D scenes.
+
+## Installation
+
+1. Create and activate a virtual environment:
+   ```bash
+   python -m venv .venv
+   source .venv/bin/activate  # on Windows use .venv\\Scripts\\activate
+   pip install --upgrade pip
+   ```
+
+2. Install the pinned dependencies:
+   ```bash
+   pip install -r requirements.txt
+   ```
+
+   The `requirements.txt` file specifies exact package versions to ensure reproducibility.
+
+## Scenario Folder Convention
+
+Each scenario resides under `scenarios/<scenario_name>/` and must contain at least:
+
+- `sumo_dir/osm.sumocfg` – SUMO configuration file defining the road network and traffic.
+- `scenario.xml` – Sionna RT scene description, including buildings, vegetation, and materials.
+- `terrain.xml` – Terrain mesh used by Sionna RT to model ground relief.
+
+During simulation, the script will create two subfolders in each scenario:
+
+- `render_frames/` – Contains per‑frame images if rendering is enabled.
+- `output_data/` – Contains CSV/NumPy files with RSSI/path‑loss traces.
+
+## Running the Simulation
+
+To generate propagation traces for a given scenario:
+
+```bash
+python signal_propagation_3d_RT.py
+```
+
+The script prompts you to select a scenario and confirm the simulation. It then:
+
+1. Launches SUMO using the configuration found in `scenarios/<scenario>/sumo_dir/osm.sumocfg`.
+2. Loads the Sionna RT scene (`scenario.xml` and `terrain.xml`).
+3. For each SUMO time step:
+   - Retrieves the positions of all vehicles via TraCI.
+   - Computes propagation paths between every transmitter–receiver pair using `PathSolver` with `max_depth=4` and a fixed `seed=42`.
+   - Aggregates the complex gains to compute received power (RSSI) and logs the values.
+   - Optionally renders the scene to `render_frames/`.
+
+Simulation continues until SUMO reaches the end of the configured scenario.
+
+## Outputs
+
+- **CSV/NumPy trace files** in `output_data/` containing per‑step RSSI or path‑loss values for each link.
+- **Rendered frames** (optional) in `render_frames/` which can be converted to a video using `frames2video.py`.
+- **Plots** generated via `path_loss_graphs.py` and `graphs_handler.py` to visualise the differences between 2D and 3D propagation models.
+
+## Reproducibility
+
+Reproducibility is a core goal of this repository:
+
+- All Python dependencies are pinned in `requirements.txt`.
+- The main script sets the `PathSolver` random seed to `42` and uses a fixed maximum interaction depth (`max_depth=4`) to ensure deterministic behaviour for a given scene and mobility trace.
+- Scenarios are self‑contained; using the same `scenario.xml`, `terrain.xml`, and SUMO configuration will yield identical results.
+- A CPU fallback is available via the Dr.Jit LLVM backend if no GPU is detected, though performance will be slower.
+
+## Code Availability for Paper Reuse
+
+This repository accompanies the experiments reported in our IEEE Access submission. The scripts and scenarios provided here allow other researchers to reproduce the RSSI/path‑loss traces, plots, and conclusions presented in the paper. If you use this code in your own work, please cite our paper and link to this repository.
+
+## Citation
+
+Please cite the associated IEEE Access paper when using this repository in academic work. A typical BibTeX entry might look like:
+
+```bibtex
+@article{stepanyants2026sionna,
+  title   = {3D Ray‑Tracing for V2X Communications: Accurate Terrain and Mobility Modelling with SUMO and Sionna RT},
+  author  = {Stepanyants, V. G. and others},
+  journal = {IEEE Access},
+  year    = {2026},
+  note    = {Code available at \\url{https://github.com/Chartist-1/Sionna_SUMO_simu}}
+}
+```
+
+---
+
+© 2026 Chartist‑1 / AFETZ. Licensed under the repository’s LICENSE file.
*** End Patch
