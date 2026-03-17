#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="$(date +%F)"
OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/compare_tech}"
TECHS_CSV="${TECHS_CSV:-80211p,ltev2x,nrv2x}"
SCENARIOS_CSV="${SCENARIOS_CSV:-truck,intersection}"
COMPARE_MODE="${COMPARE_MODE:-channel}"

SUMO_GUI="${SUMO_GUI:-0}"
TX_POWER_DBM="${TX_POWER_DBM:-23}"
SIM_TIME_TRUCK="${SIM_TIME_TRUCK:-40}"
SIM_TIME_INTERSECTION="${SIM_TIME_INTERSECTION:-20}"
SUMO_WAIT_SOCKET_S="${SUMO_WAIT_SOCKET_S:-5}"
RUN_RETRIES="${RUN_RETRIES:-3}"
JOBS="${JOBS:-8}"

if [[ "$OUT_DIR" != /* ]]; then
  OUT_DIR="$ROOT/$OUT_DIR"
fi
mkdir -p "$OUT_DIR"

NS3_DIR="${NS3_DIR:-}"
NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
"$ROOT/scripts/sync-overlay-into-bootstrap-ns3.sh" --root "$ROOT" --ns3-dir "$NS3_DIR"

cd "$NS3_DIR"
if [[ "$EUID" -eq 0 ]]; then
  NS3_USER_OVERRIDE="${NS3_USER_OVERRIDE:-ns3}"
  run_ns3() { USER="$NS3_USER_OVERRIDE" ./ns3 "$@"; }
else
  run_ns3() { ./ns3 "$@"; }
fi

CONFIG_STATE="$(run_ns3 show config 2>/dev/null | sed -r 's/\x1B\[[0-9;]*[mK]//g' || true)"
if ! grep -Eq 'Examples[[:space:]]*:[[:space:]]*ON' <<<"$CONFIG_STATE" || \
   ! grep -Eq 'Build profile[[:space:]]*:[[:space:]]*optimized' <<<"$CONFIG_STATE"; then
  run_ns3 configure --enable-examples --build-profile=optimized --disable-werror
fi

IFS=',' read -r -a TECHS <<< "$TECHS_CSV"
IFS=',' read -r -a SCENARIOS <<< "$SCENARIOS_CSV"

declare -A TECH_BIN=(
  ["80211p"]="v2v-emergencyVehicleAlert-80211p"
  ["ltev2x"]="v2v-emergencyVehicleAlert-ltev2x"
  ["nrv2x"]="v2v-emergencyVehicleAlert-nrv2x"
)

for tech in "${TECHS[@]}"; do
  if [[ -z "${TECH_BIN[$tech]+x}" ]]; then
    echo "Unknown tech '$tech'. Valid: 80211p,ltev2x,nrv2x"
    exit 1
  fi
done

build_targets=()
for tech in "${TECHS[@]}"; do
  build_targets+=("${TECH_BIN[$tech]}")
done
run_ns3 build -j "$JOBS" "${build_targets[@]}"

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

run_case() {
  local scenario="$1"
  local tech="$2"
  local binary="${TECH_BIN[$tech]}"
  local run_dir="$OUT_DIR/$scenario/$tech"
  local artifacts="$run_dir/artifacts"
  local log_file="$run_dir/${binary}.log"
  local csv_prefix="$artifacts/eva"
  local netstate_file="$artifacts/eva-netstate.xml"
  local sumo_folder=""
  local mob_trace=""
  local sumo_config=""
  local sim_time=""
  local focus_vehicle=""
  local tx_focus_id="2"
  local per_vehicle_prr_profile=""
  local met_sup="1"
  local extra_attrs=()

  mkdir -p "$artifacts"
  rm -f "$artifacts"/eva-veh*-CAM.csv "$artifacts"/eva-veh*-MSG.csv \
        "$artifacts"/eva-veh*-CTRL.csv "$artifacts"/eva-veh*-PROFILE.csv \
        "$netstate_file" "$artifacts"/run_meta.env 2>/dev/null || true

  case "$scenario" in
    truck)
      sumo_folder="src/automotive/examples/sumo_files_v2v_map/"
      mob_trace="cars_incident_threeflow_staticstop.rou.xml"
      sumo_config="src/automotive/examples/sumo_files_v2v_map/map_incident_threeflow_staticstop.sumo.cfg"
      sim_time="$SIM_TIME_TRUCK"
      focus_vehicle="veh4"
      if [[ "$COMPARE_MODE" == "scenario_replay" ]]; then
        per_vehicle_prr_profile="veh3:0.050000:23:0.95,veh4:0.923000:-20:0.077,veh5:0.307000:0:0.693"
      else
        per_vehicle_prr_profile="veh3:0:23:0.95,veh4:0:-20:0.077,veh5:0:0:0.693"
      fi
      extra_attrs+=(
        "--ns3::emergencyVehicleAlert::ReactionDistanceThreshold=22"
        "--ns3::emergencyVehicleAlert::ReactionHeadingThreshold=130"
        "--ns3::emergencyVehicleAlert::ReactionTargetLane=1"
        "--ns3::emergencyVehicleAlert::ReactionSpeedFactorTargetLane=0.10"
        "--ns3::emergencyVehicleAlert::ReactionSpeedFactorOtherLane=1.0"
        "--ns3::emergencyVehicleAlert::ReactionActionDurationS=2.5"
        "--ns3::emergencyVehicleAlert::ReactionForceLaneChangeEnable=true"
        "--ns3::emergencyVehicleAlert::CpmReactionDistanceThreshold=0"
        "--ns3::emergencyVehicleAlert::CpmReactionTtcThresholdS=0"
        "--ns3::emergencyVehicleAlert::CamSilenceDropInferenceEnable=false"
        "--ns3::emergencyVehicleAlert::CrashModeEnable=true"
        "--ns3::emergencyVehicleAlert::CrashModeVehicleId=veh4"
        "--ns3::emergencyVehicleAlert::CrashModeNoActionThreshold=10"
        "--ns3::emergencyVehicleAlert::CrashModeForceSpeedMps=30"
        "--ns3::emergencyVehicleAlert::CrashModeDurationS=6"
        "--ns3::emergencyVehicleAlert::CrashModeMinTimeS=6"
      )
      ;;
    intersection)
      sumo_folder="src/automotive/examples/sumo_files_v2i_map/"
      mob_trace="cars_intersection_priority.rou.xml"
      sumo_config="src/automotive/examples/sumo_files_v2i_map/map_intersection_priority.sumo.cfg"
      sim_time="$SIM_TIME_INTERSECTION"
      focus_vehicle="veh3"
      if [[ "$COMPARE_MODE" == "scenario_replay" ]]; then
        per_vehicle_prr_profile="veh2:0:23:0.95,veh3:0.980000:-30:0.02,veh4:0:23:0.95"
      else
        per_vehicle_prr_profile="veh2:0:23:0.95,veh3:0:-30:0.02,veh4:0:23:0.95"
      fi
      extra_attrs+=(
        "--ns3::emergencyVehicleAlert::ReactionDistanceThreshold=90"
        "--ns3::emergencyVehicleAlert::ReactionHeadingThreshold=130"
        "--ns3::emergencyVehicleAlert::ReactionTargetLane=0"
        "--ns3::emergencyVehicleAlert::ReactionSpeedFactorTargetLane=0.10"
        "--ns3::emergencyVehicleAlert::ReactionSpeedFactorOtherLane=1.0"
        "--ns3::emergencyVehicleAlert::ReactionActionDurationS=2.5"
        "--ns3::emergencyVehicleAlert::ReactionForceLaneChangeEnable=false"
        "--ns3::emergencyVehicleAlert::CpmReactionDistanceThreshold=0"
        "--ns3::emergencyVehicleAlert::CpmReactionTtcThresholdS=0"
        "--ns3::emergencyVehicleAlert::CamSilenceDropInferenceEnable=true"
        "--ns3::emergencyVehicleAlert::CamSilenceFocusTxId=2"
        "--ns3::emergencyVehicleAlert::CamSilenceExpectedPeriodMs=600"
        "--ns3::emergencyVehicleAlert::CamSilenceTimeoutS=0.95"
        "--ns3::emergencyVehicleAlert::CamSilenceBootstrapTimeS=2.2"
        "--ns3::emergencyVehicleAlert::CrashModeEnable=true"
        "--ns3::emergencyVehicleAlert::CrashModeVehicleId=veh3"
        "--ns3::emergencyVehicleAlert::CrashModeNoActionThreshold=3"
        "--ns3::emergencyVehicleAlert::CrashModeForceSpeedMps=30"
        "--ns3::emergencyVehicleAlert::CrashModeDurationS=3"
        "--ns3::emergencyVehicleAlert::CrashModeMinTimeS=3.8"
      )
      ;;
    *)
      echo "Unknown scenario '$scenario'. Valid: truck,intersection"
      return 1
      ;;
  esac

  local args=(
    "--sumo-gui=$SUMO_GUI"
    "--sim-time=$sim_time"
    "--met-sup=$met_sup"
    "--penetrationRate=1"
    "--sumo-folder=$sumo_folder"
    "--mob-trace=$mob_trace"
    "--sumo-config=$sumo_config"
    "--csv-log=$csv_prefix"
    "--netstate-dump-file=$netstate_file"
    "--ns3::emergencyVehicleAlert::DropTriggeredReactionEnable=false"
    "--ns3::emergencyVehicleAlert::RxDropProbPhyCam=0"
    "--ns3::emergencyVehicleAlert::RxDropProbPhyCpm=0"
    "--ns3::emergencyVehicleAlert::PerVehiclePrrProfile=$per_vehicle_prr_profile"
  )
  args+=("${extra_attrs[@]}")

  local sumo_port="$((30000 + (RANDOM % 20000)))"
  if [[ "$tech" == "nrv2x" ]]; then
    args+=("--txPower=$TX_POWER_DBM" "--sumo-port=$sumo_port" "--sionna=0")
  else
    if [[ "$COMPARE_MODE" == "scenario_replay" && "$tech" == "ltev2x" ]]; then
      # LTE MetricSupervisor may abort under heavy forced drops (PRR > 1 assertion path).
      # Replay mode keeps comparability via CSV-level metrics, so disable met-sup only here.
      args[2]="--met-sup=0"
      met_sup="0"
    fi
    args+=("--tx-power=$TX_POWER_DBM" "--sumo-port=$sumo_port" "--sumo-wait-for-socket-s=$SUMO_WAIT_SOCKET_S")
  fi

  local cmd="$binary ${args[*]}"
  local attempt=1
  local run_status="ok"
  while true; do
    set +e
    run_ns3 run --no-build "$cmd" > "$log_file" 2>&1
    local rc=$?
    set -e
    if [[ $rc -eq 0 ]]; then
      break
    fi
    if [[ $attempt -ge $RUN_RETRIES ]] || ! rg -q "Connection refused|Can not connect to sumo via traci" "$log_file"; then
      run_status="failed"
      echo "Run failed: scenario=$scenario tech=$tech (see $log_file)"
      break
    fi
    attempt=$((attempt + 1))
    sumo_port="$((30000 + (RANDOM % 20000)))"
    if [[ "$tech" == "nrv2x" ]]; then
      cmd="$(sed -E "s/--sumo-port=[0-9]+/--sumo-port=$sumo_port/" <<< "$cmd")"
    else
      cmd="$(sed -E "s/--sumo-port=[0-9]+/--sumo-port=$sumo_port/" <<< "$cmd")"
    fi
    sleep 2
  done

  if [[ -f "$netstate_file" ]]; then
    "$PY_BIN" "$ROOT/analysis/scenario_runs/analyze_netstate_collision_risk.py" \
      --netstate "$netstate_file" \
      --out-dir "$artifacts/collision_risk" \
      --gap-threshold-m 2.0 \
      --ttc-threshold-s 1.5 >/dev/null 2>&1 || true
  fi

  cat > "$artifacts/run_meta.env" <<EOF
scenario=$scenario
tech=$tech
binary=$binary
compare_mode=$COMPARE_MODE
focus_vehicle=$focus_vehicle
tx_focus_id=$tx_focus_id
run_status=$run_status
sumo_config=$sumo_config
mob_trace=$mob_trace
sim_time=$sim_time
met_sup=$met_sup
EOF

  echo "DONE scenario=$scenario tech=$tech status=$run_status out=$run_dir"
}

for scenario in "${SCENARIOS[@]}"; do
  for tech in "${TECHS[@]}"; do
    run_case "$scenario" "$tech"
  done
done

"$PY_BIN" "$ROOT/analysis/scenario_runs/build_compare_tech_summary.py" \
  --matrix-root "$OUT_DIR" \
  --out-csv "$OUT_DIR/compare_tech_summary.csv"

echo "COMPARE_TECH_DONE: $OUT_DIR"
echo "SUMMARY_CSV: $OUT_DIR/compare_tech_summary.csv"
