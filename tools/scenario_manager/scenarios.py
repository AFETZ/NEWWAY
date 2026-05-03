"""
Scenario registry — defines all available experiments with metadata,
parameters, and execution configuration.
"""
from __future__ import annotations

import dataclasses as dc
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@dc.dataclass
class ScenarioParam:
    """Single tuneable parameter exposed to the UI."""
    name: str
    label: str
    description: str
    default: Any
    type: str = "str"  # str | int | float | bool | choice
    choices: list[str] | None = None
    min_val: float | None = None
    max_val: float | None = None


@dc.dataclass
class Scenario:
    """Scenario descriptor."""
    id: str
    title: str
    title_ru: str
    description: str
    description_ru: str
    scientific_goal: str
    scientific_goal_ru: str
    hypothesis: str
    hypothesis_ru: str
    run_script: str  # relative to ROOT
    params: list[ScenarioParam]
    expected_artifacts: list[str]  # globs relative to output directory
    tags: list[str]
    estimated_runs: int = 1  # how many sub-runs inside a sweep
    output_env_var: str = "OUT_BASE"


# ---------------------------------------------------------------------------
# Scenario 1: Burst Loss vs Random Loss
# ---------------------------------------------------------------------------
BURST_VS_RANDOM = Scenario(
    id="burst_vs_random_loss",
    title="Burst Loss vs Random Loss Patterns",
    title_ru="Пакетные потери vs случайные потери",
    description=(
        "Compares the impact of temporally-clustered message degradation versus "
        "uniform random loss at the same nominal packet drop level. The scenario "
        "keeps the same incident geometry and measures how the loss pattern "
        "changes control actions and safety margins."
    ),
    description_ru=(
        "Сравнение влияния кластерных деградаций сообщений и равномерно-случайных "
        "потерь при одинаковом номинальном уровне drop probability. Геометрия "
        "дорожной ситуации фиксирована, сравниваются реакции ТС и safety-метрики."
    ),
    scientific_goal=(
        "Show that identical average communication quality does not imply "
        "identical behavioral outcome when loss timing differs."
    ),
    scientific_goal_ru=(
        "Показать, что одинаковое среднее качество связи не гарантирует "
        "одинаковый поведенческий результат, если меняется временная структура потерь."
    ),
    hypothesis=(
        "Clustered degradation will reduce or delay evasive actions more than "
        "uniform random loss with the same average drop probability."
    ),
    hypothesis_ru=(
        "Кластерная деградация приведет к более поздним или пропущенным "
        "манёврам уклонения по сравнению с равномерно-случайными потерями "
        "при том же среднем уровне потерь."
    ),
    run_script="tools/scenario_manager/run_burst_vs_random.sh",
    params=[
        ScenarioParam(
            "TARGET_DROP_PROBS",
            "Target drop probabilities",
            "Space-separated average drop rates to test",
            "0.2 0.4 0.6",
            "str",
        ),
        ScenarioParam(
            "BURST_LENGTH",
            "Burst length (packets)",
            "Number of consecutive packets represented by the burst case label",
            "5",
            "int",
            min_val=2,
            max_val=20,
        ),
        ScenarioParam(
            "SIM_TIME",
            "Simulation time (s)",
            "",
            "40",
            "int",
            min_val=10,
            max_val=120,
        ),
        ScenarioParam(
            "SUMO_GUI",
            "SUMO GUI",
            "Show SUMO window",
            "0",
            "choice",
            choices=["0", "1"],
        ),
    ],
    expected_artifacts=[
        "*/artifacts/*-MSG.csv",
        "*/artifacts/*-CTRL.csv",
        "*/artifacts/collision_risk/*.csv",
        "burst_vs_random_summary.csv",
        "burst_vs_random_summary.png",
    ],
    tags=["loss-pattern", "safety", "PRR", "behavioral"],
    estimated_runs=6,
)


# ---------------------------------------------------------------------------
# Scenario 2: Vehicle Density Scalability
# ---------------------------------------------------------------------------
DENSITY_SCALING = Scenario(
    id="density_scaling",
    title="Vehicle Density Impact on V2X Safety",
    title_ru="Влияние плотности транспортного потока на безопасность V2X",
    description=(
        "Sweeps low / medium / high traffic presets that reuse the same "
        "incident-based emergency-vehicle scenario with progressively denser "
        "SUMO traffic layouts."
    ),
    description_ru=(
        "Сценарий перебирает пресеты низкой / средней / высокой плотности, "
        "используя одну и ту же incident-постановку с более насыщенными "
        "SUMO-конфигурациями трафика."
    ),
    scientific_goal=(
        "Estimate the density level at which channel contention and traffic "
        "complexity begin to reduce the safety margin in the incident scenario."
    ),
    scientific_goal_ru=(
        "Оценить уровень плотности, при котором конкуренция за радиоресурс "
        "и сложность трафика начинают снижать запас безопасности."
    ),
    hypothesis=(
        "The dense preset will produce lower PRR and more delayed control "
        "actions than the light preset."
    ),
    hypothesis_ru=(
        "Плотный пресет даст более низкий PRR и более поздние управляющие "
        "воздействия по сравнению с лёгким пресетом."
    ),
    run_script="tools/scenario_manager/run_density_scaling.sh",
    params=[
        ScenarioParam(
            "DENSITIES",
            "Density presets",
            "Space-separated presets: 3(light), 5(medium), 8(dense)",
            "3 5 8",
            "str",
        ),
        ScenarioParam(
            "SIM_TIME",
            "Simulation time (s)",
            "",
            "40",
            "int",
            min_val=10,
            max_val=120,
        ),
        ScenarioParam(
            "TX_POWER",
            "TX power (dBm)",
            "",
            "23",
            "int",
            min_val=-10,
            max_val=33,
        ),
        ScenarioParam(
            "SUMO_GUI",
            "SUMO GUI",
            "Show SUMO window",
            "0",
            "choice",
            choices=["0", "1"],
        ),
    ],
    expected_artifacts=[
        "density_*/artifacts/*-MSG.csv",
        "density_*/artifacts/*-CTRL.csv",
        "density_*/artifacts/collision_risk/*.csv",
        "density_scaling_summary.csv",
        "density_scaling_summary.png",
    ],
    tags=["density", "congestion", "scalability", "NR-V2X"],
    estimated_runs=3,
)


# ---------------------------------------------------------------------------
# Scenario 3: Latency vs Loss Trade-off
# ---------------------------------------------------------------------------
LATENCY_VS_LOSS = Scenario(
    id="latency_vs_loss_tradeoff",
    title="Latency vs Loss Trade-off for V2X Safety",
    title_ru="Компромисс задержка / потери для безопасности V2X",
    description=(
        "Compares packet loss against an NR sidelink processing-delay proxy. "
        "The loss branch varies PHY drop probability, while the delay branch "
        "varies the supported `t1` scheduling parameter to introduce additional "
        "radio-side reaction delay."
    ),
    description_ru=(
        "Сравнение потерь пакетов и прокси-параметра задержки обработки NR "
        "sidelink. Ветвь loss варьирует PHY drop probability, а ветвь delay "
        "изменяет поддерживаемый параметр `t1`, который увеличивает "
        "радио-сторону задержки реакции."
    ),
    scientific_goal=(
        "Estimate whether safety degradation is more sensitive to packet loss "
        "or to added scheduling / processing delay in the same incident geometry."
    ),
    scientific_goal_ru=(
        "Оценить, что сильнее ухудшает безопасность в одной и той же "
        "incident-постановке: потери пакетов или добавленная задержка "
        "планирования / обработки."
    ),
    hypothesis=(
        "Increasing the supported processing-delay proxy will delay the first "
        "useful reaction even when average PRR remains high."
    ),
    hypothesis_ru=(
        "Рост поддерживаемого прокси-параметра задержки приведет к более "
        "поздней первой полезной реакции даже при высоком среднем PRR."
    ),
    run_script="tools/scenario_manager/run_latency_vs_loss.sh",
    params=[
        ScenarioParam(
            "LOSS_PROBS",
            "PHY loss probabilities",
            "Space-separated loss rates",
            "0.0 0.2 0.4",
            "str",
        ),
        ScenarioParam(
            "T1_DELAYS",
            "Processing delay proxy (t1 slots)",
            "Space-separated supported t1 values for the delay branch",
            "2 8 16",
            "str",
        ),
        ScenarioParam(
            "SIM_TIME",
            "Simulation time (s)",
            "",
            "40",
            "int",
            min_val=10,
            max_val=120,
        ),
        ScenarioParam(
            "SUMO_GUI",
            "SUMO GUI",
            "Show SUMO window",
            "0",
            "choice",
            choices=["0", "1"],
        ),
    ],
    expected_artifacts=[
        "loss_*/artifacts/*-MSG.csv",
        "delay_*/artifacts/*-MSG.csv",
        "latency_vs_loss_summary.csv",
        "latency_vs_loss_summary.png",
    ],
    tags=["latency", "loss", "QoS", "tradeoff", "behavioral"],
    estimated_runs=6,
)


# ---------------------------------------------------------------------------
# Scenario 4: Fixed lane-change thesis scenario
# ---------------------------------------------------------------------------
TRUCK_LANE_CHANGE = Scenario(
    id="truck_lane_change",
    title="Truck Lane Change Thesis Scenario",
    title_ru="Фиксированный сценарий: грузовик и перестроение",
    description=(
        "Runs the fixed thesis-ready lane-change scenario with the truck, "
        "lossy vehicle, and deterministic incident chain used for the diploma."
    ),
    description_ru=(
        "Запуск фиксированного дипломного сценария с грузовиком, lossy-авто "
        "и детерминированной цепочкой событий вокруг перестроения."
    ),
    scientific_goal=(
        "Provide a reproducible lane-change case for presentation, regression, "
        "and thesis-grade artifact generation."
    ),
    scientific_goal_ru=(
        "Обеспечить воспроизводимый сценарий перестроения для демонстрации, "
        "регрессии и формирования дипломных артефактов."
    ),
    hypothesis=(
        "With the fixed PRR profile, the designated lossy vehicle will miss "
        "the timely maneuver while the other vehicles still react coherently."
    ),
    hypothesis_ru=(
        "При фиксированном PRR-профиле целевое lossy-авто пропустит "
        "своевременный манёвр, тогда как остальные участники отреагируют согласованно."
    ),
    run_script="experiments/truck_lane_change/scripts/run.sh",
    params=[
        ScenarioParam(
            "SIM_TIME",
            "Simulation time (s)",
            "",
            "40",
            "int",
            min_val=10,
            max_val=120,
        ),
        ScenarioParam(
            "SUMO_GUI",
            "SUMO GUI",
            "Show SUMO window",
            "0",
            "choice",
            choices=["0", "1"],
        ),
        ScenarioParam(
            "USE_SIONNA",
            "Use Sionna RT",
            "Enable Sionna-based channel backend",
            "1",
            "choice",
            choices=["0", "1"],
        ),
        ScenarioParam(
            "TX_POWER_DBM",
            "TX power (dBm)",
            "",
            "23",
            "int",
            min_val=-10,
            max_val=33,
        ),
    ],
    expected_artifacts=[
        "artifacts/*-MSG.csv",
        "artifacts/*-CTRL.csv",
        "artifacts/*-PROFILE.csv",
        "artifacts/collision_risk/*.csv",
        "artifacts/truck_lane_change_story/*.png",
        "artifacts/truck_lane_change_intuitive/*.png",
    ],
    tags=["thesis", "lane-change", "truck", "fixed"],
    output_env_var="OUT_DIR",
)


# ---------------------------------------------------------------------------
# Scenario 5: Fixed intersection thesis scenario
# ---------------------------------------------------------------------------
INTERSECTION_CRASH = Scenario(
    id="intersection_crash",
    title="Priority Intersection Thesis Scenario",
    title_ru="Фиксированный сценарий: конфликт на перекрестке",
    description=(
        "Runs the fixed priority-intersection crash scenario used in the thesis, "
        "including the third vehicle that waits out the conflict safely."
    ),
    description_ru=(
        "Запуск фиксированного дипломного сценария приоритетного перекрёстка, "
        "включая третье ТС, которое безопасно пережидает конфликт."
    ),
    scientific_goal=(
        "Provide a reproducible intersection conflict case for regression and "
        "thesis-grade summary outputs."
    ),
    scientific_goal_ru=(
        "Обеспечить воспроизводимый сценарий конфликта на перекрёстке для "
        "регрессии и формирования дипломных сводок."
    ),
    hypothesis=(
        "The impaired conflicting vehicle will receive too little useful "
        "information to avoid the collision unless channel conditions are improved."
    ),
    hypothesis_ru=(
        "Деградированный конфликтующий участник получит недостаточно полезной "
        "информации, чтобы избежать столкновения, если качество канала не улучшить."
    ),
    run_script="experiments/intersection_crash/scripts/run.sh",
    params=[
        ScenarioParam(
            "SIM_TIME",
            "Simulation time (s)",
            "",
            "20",
            "int",
            min_val=10,
            max_val=120,
        ),
        ScenarioParam(
            "SUMO_GUI",
            "SUMO GUI",
            "Show SUMO window",
            "0",
            "choice",
            choices=["0", "1"],
        ),
        ScenarioParam(
            "USE_SIONNA",
            "Use Sionna RT",
            "Enable Sionna-based channel backend",
            "1",
            "choice",
            choices=["0", "1"],
        ),
        ScenarioParam(
            "TX_POWER_DBM",
            "TX power (dBm)",
            "",
            "23",
            "int",
            min_val=-10,
            max_val=33,
        ),
    ],
    expected_artifacts=[
        "artifacts/intersection_summary.csv",
        "artifacts/*-MSG.csv",
        "artifacts/*-CTRL.csv",
        "artifacts/*-PROFILE.csv",
        "artifacts/collision_risk/*.csv",
    ],
    tags=["thesis", "intersection", "fixed", "crash"],
    output_env_var="OUT_DIR",
)


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------
SCENARIO_REGISTRY: dict[str, Scenario] = {
    s.id: s
    for s in [
        BURST_VS_RANDOM,
        DENSITY_SCALING,
        LATENCY_VS_LOSS,
        TRUCK_LANE_CHANGE,
        INTERSECTION_CRASH,
    ]
}


def get_scenario(scenario_id: str) -> Scenario:
    return SCENARIO_REGISTRY[scenario_id]


def list_scenarios() -> list[Scenario]:
    return list(SCENARIO_REGISTRY.values())
