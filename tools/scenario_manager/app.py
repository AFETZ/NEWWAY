"""
NEWWAY Scenario Manager — Streamlit UI

Launch:
    cd /path/to/NEWWAY
    .venv/bin/streamlit run tools/scenario_manager/app.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import streamlit as st

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.scenario_manager.scenarios import list_scenarios, get_scenario, Scenario, ROOT as PROJECT_ROOT
from tools.scenario_manager.runner import run_scenario, find_latest_run
from tools.scenario_manager import visualizer

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NEWWAY Scenario Manager",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .scenario-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 16px;
        margin: 8px 0;
        background: linear-gradient(135deg, #667eea11, #764ba211);
    }
    .metric-box {
        text-align: center;
        padding: 12px;
        border-radius: 8px;
        background: #f8f9fa;
    }
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        background: #e3f2fd;
        color: #1565c0;
        font-size: 0.8em;
        margin: 2px;
    }
    .status-running { color: #f57c00; font-weight: bold; }
    .status-done { color: #2e7d32; font-weight: bold; }
    .status-error { color: #c62828; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar: Scenario selection ──────────────────────────────────────────────

st.sidebar.title("🔬 NEWWAY Scenario Manager")
st.sidebar.markdown("---")
st.sidebar.markdown("**V2X Experiment Platform**")
st.sidebar.markdown("Select a scenario, configure parameters, run, and analyze results.")

scenarios = list_scenarios()
scenario_options = {s.title: s.id for s in scenarios}
selected_title = st.sidebar.selectbox(
    "Select experiment",
    options=list(scenario_options.keys()),
    index=0,
)
selected_id = scenario_options[selected_title]
scenario = get_scenario(selected_id)

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["📋 Description", "⚙️ Configure & Run", "📊 Results & Visualizations", "📁 Browse Past Runs"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Tags:** {' '.join(f'`{t}`' for t in scenario.tags)}"
)
st.sidebar.markdown(f"**Estimated sub-runs:** {scenario.estimated_runs}")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_summary_csvs(run_dir: Path) -> list[Path]:
    return sorted(
        [p for p in run_dir.rglob("*_summary.csv") if p.is_file()],
        key=lambda p: (len(p.relative_to(run_dir).parts), str(p.relative_to(run_dir))),
    )


# ── Page: Description ────────────────────────────────────────────────────────

def page_description(s: Scenario):
    st.title(f"📋 {s.title}")
    st.caption(s.title_ru)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Description")
        st.markdown(s.description)
        st.markdown("---")
        st.subheader("Описание (RU)")
        st.markdown(s.description_ru)

    with col2:
        st.subheader("🎯 Scientific Goal")
        st.info(s.scientific_goal)
        st.markdown("**Научная цель:**")
        st.info(s.scientific_goal_ru)

        st.subheader("🔬 Hypothesis")
        st.warning(s.hypothesis)
        st.markdown("**Гипотеза:**")
        st.warning(s.hypothesis_ru)

    st.markdown("---")

    # Architecture diagram
    st.subheader("Experiment Architecture")
    st.markdown("""
    ```
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │   SUMO       │◄───►│   ns-3       │◄───►│  Sionna RT   │
    │  (Mobility)  │     │  (Network)   │     │  (Channel)   │
    └──────┬───────┘     └──────┬───────┘     └──────────────┘
           │                    │
           ▼                    ▼
    ┌──────────────┐     ┌──────────────┐
    │  Netstate    │     │  MSG/CTRL    │
    │  (positions) │     │  CSV logs    │
    └──────┬───────┘     └──────┬───────┘
           │                    │
           └─────────┬──────────┘
                     ▼
              ┌──────────────┐
              │  Analysis    │
              │  Pipeline    │
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │Visualizations│
              │ & Reports    │
              └──────────────┘
    ```
    """)

    # Parameters preview
    st.subheader("Configurable Parameters")
    for p in s.params:
        st.markdown(f"- **{p.label}** (`{p.name}`): {p.description or 'No description'} — default: `{p.default}`")


# ── Page: Configure & Run ────────────────────────────────────────────────────

def page_configure_run(s: Scenario):
    st.title(f"⚙️ Configure & Run: {s.title}")

    st.subheader("Parameters")

    params: dict[str, str] = {}
    cols = st.columns(2)
    for i, p in enumerate(s.params):
        with cols[i % 2]:
            if p.type == "choice" and p.choices:
                val = st.selectbox(p.label, options=p.choices,
                                    index=p.choices.index(p.default) if p.default in p.choices else 0,
                                    key=f"param_{s.id}_{p.name}")
            elif p.type == "int":
                val = st.number_input(p.label, value=int(p.default),
                                       min_value=int(p.min_val) if p.min_val is not None else None,
                                       max_value=int(p.max_val) if p.max_val is not None else None,
                                       key=f"param_{s.id}_{p.name}")
                val = str(int(val))
            elif p.type == "float":
                val = st.number_input(p.label, value=float(p.default),
                                       min_value=float(p.min_val) if p.min_val is not None else None,
                                       max_value=float(p.max_val) if p.max_val is not None else None,
                                       key=f"param_{s.id}_{p.name}")
                val = str(val)
            elif p.type == "bool":
                val = st.checkbox(p.label, value=p.default.lower() in ("true", "1", "yes"),
                                   key=f"param_{s.id}_{p.name}")
                val = "1" if val else "0"
            else:
                val = st.text_input(p.label, value=p.default, key=f"param_{s.id}_{p.name}")
            params[p.name] = str(val)

    st.markdown("---")

    # Run button
    col_run, col_status = st.columns([1, 3])
    with col_run:
        run_clicked = st.button("🚀 Run Experiment", type="primary", use_container_width=True)

    if run_clicked:
        with col_status:
            st.markdown('<span class="status-running">⏳ Running...</span>', unsafe_allow_html=True)

        # Create log area
        log_container = st.container()
        log_area = log_container.empty()
        progress_bar = st.progress(0, text="Starting experiment...")

        log_lines: list[str] = []

        def on_line(line: str):
            log_lines.append(line)
            # Keep last 50 lines visible
            display_text = "\n".join(log_lines[-50:])
            log_area.code(display_text, language="bash")

            # Crude progress estimation
            if "DONE" in line or "Done" in line:
                n_done = sum(1 for l in log_lines if "DONE" in l or "Done:" in l)
                pct = min(n_done / max(s.estimated_runs, 1), 0.95)
                progress_bar.progress(pct, text=f"Completed {n_done}/{s.estimated_runs} runs")

        t0 = time.time()
        result = run_scenario(s, params, on_line=on_line)
        elapsed = time.time() - t0

        progress_bar.progress(1.0, text="Complete!")

        if result.ok:
            st.success(f"Experiment completed successfully in {elapsed:.1f}s")
            st.session_state["last_run_dir"] = result.out_dir
            st.session_state["last_scenario_id"] = s.id
            st.balloons()
        else:
            st.error(f"Experiment failed (exit code {result.return_code}) after {elapsed:.1f}s")
            st.code("\n".join(result.log_lines[-30:]), language="bash")

        st.markdown(f"**Output directory:** `{result.out_dir}`")


# ── Page: Results & Visualizations ───────────────────────────────────────────

def page_results(s: Scenario):
    st.title(f"📊 Results: {s.title}")

    # Determine which run to show
    run_dir = None
    if "last_run_dir" in st.session_state and st.session_state.get("last_scenario_id") == s.id:
        run_dir = Path(st.session_state["last_run_dir"])
    else:
        run_dir = find_latest_run(s.id)

    if run_dir is None or not run_dir.exists():
        st.warning("No run results found. Run the experiment first!")
        return

    st.info(f"**Showing results from:** `{run_dir}`")

    # ── Tab 1: Summary CSV ──
    tab_summary, tab_static, tab_interactive, tab_logs = st.tabs([
        "📈 Summary Data", "🖼️ Static Plots", "🔄 Interactive Charts", "📝 Logs"
    ])

    with tab_summary:
        # Find summary CSVs
        summary_csvs = _find_summary_csvs(run_dir)
        if summary_csvs:
            for csv_path in summary_csvs:
                rel_path = csv_path.relative_to(run_dir)
                st.subheader(csv_path.stem.replace("_", " ").title())
                st.caption(str(rel_path))
                df = visualizer._safe_read_csv(csv_path)
                if df is not None:
                    st.dataframe(df, use_container_width=True)

                    # Highlight key metrics
                    numeric_cols = df.select_dtypes(include="number").columns
                    if len(numeric_cols) > 0:
                        st.markdown("**Key metrics:**")
                        metric_cols = st.columns(min(len(numeric_cols), 5))
                        for i, col in enumerate(numeric_cols[:5]):
                            with metric_cols[i]:
                                val = df[col].mean()
                                st.metric(col, f"{val:.3f}")
        else:
            st.info("No summary CSVs found yet.")

    with tab_static:
        # Generate visualizations
        with st.spinner("Generating visualizations..."):
            plots = visualizer.generate_all_plots(run_dir)

        if not plots:
            # Check for pre-generated PNGs
            pngs = list(run_dir.rglob("*.png"))
            if pngs:
                st.subheader("Pre-generated Plots")
                for png in sorted(pngs):
                    st.image(str(png), caption=png.stem, use_container_width=True)
            else:
                st.warning("No visualization data available.")
        else:
            for category, paths in plots.items():
                st.subheader(category)
                for p in paths:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.image(str(p), caption=f"{p.parent.name}/{p.name}",
                                 use_container_width=True)
                    with col2:
                        st.markdown(f"**Case:** {p.parent.name}")
                        st.markdown(f"📁 `{p.name}`")

    with tab_interactive:
        # Summary sweep chart
        summary_csvs = _find_summary_csvs(run_dir)
        for csv_path in summary_csvs:
            fig = visualizer.plotly_sweep_summary(csv_path)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        # Per-case interactive charts
        artifact_dirs = sorted(run_dir.rglob("artifacts"))
        if artifact_dirs:
            selected_case = st.selectbox(
                "Select case for detailed view",
                options=[str(d.parent.name) for d in artifact_dirs],
            )
            if selected_case:
                art_dir = [d for d in artifact_dirs if d.parent.name == selected_case]
                if art_dir:
                    # Sunburst
                    fig = visualizer.plotly_network_sunburst(art_dir[0])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                    # Timeline
                    fig = visualizer.plotly_timeline(art_dir[0])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

    with tab_logs:
        log_files = list(run_dir.rglob("*.log"))
        if log_files:
            selected_log = st.selectbox("Select log file",
                                         options=[str(f.relative_to(run_dir)) for f in log_files])
            if selected_log:
                log_path = run_dir / selected_log
                if log_path.exists():
                    content = log_path.read_text(errors="ignore")
                    st.code(content[-5000:] if len(content) > 5000 else content, language="bash")
        else:
            st.info("No log files found.")


# ── Page: Browse Past Runs ───────────────────────────────────────────────────

def page_browse():
    st.title("📁 Browse Past Runs")

    runs_root = PROJECT_ROOT / "analysis" / "scenario_runs"
    if not runs_root.exists():
        st.warning("No runs directory found.")
        return

    # List date directories
    date_dirs = sorted(
        [d for d in runs_root.iterdir() if d.is_dir() and not d.name.startswith(".")],
        reverse=True,
    )

    if not date_dirs:
        st.info("No past runs found.")
        return

    selected_date = st.selectbox("Select date", options=[d.name for d in date_dirs])
    date_dir = runs_root / selected_date

    run_dirs = sorted(
        [d for d in date_dir.iterdir() if d.is_dir()],
        reverse=True,
    )

    for rd in run_dirs:
        with st.expander(f"📁 {rd.name}"):
            # Show summary if available
            summaries = _find_summary_csvs(rd)
            for s_csv in summaries:
                df = visualizer._safe_read_csv(s_csv)
                if df is not None:
                    st.dataframe(df, use_container_width=True)

            # Show PNGs
            pngs = list(rd.rglob("*.png"))
            if pngs:
                cols = st.columns(min(len(pngs), 3))
                for i, png in enumerate(pngs[:6]):
                    with cols[i % 3]:
                        st.image(str(png), caption=png.stem, use_container_width=True)

            # Button to load this run
            if st.button(f"Load into viewer", key=f"load_{rd.name}"):
                st.session_state["last_run_dir"] = str(rd)
                st.rerun()


# ── Router ───────────────────────────────────────────────────────────────────

if page.startswith("📋"):
    page_description(scenario)
elif page.startswith("⚙️"):
    page_configure_run(scenario)
elif page.startswith("📊"):
    page_results(scenario)
elif page.startswith("📁"):
    page_browse()
