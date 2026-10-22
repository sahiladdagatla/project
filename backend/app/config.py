"""
FloodTwinAI Application Configuration and Operational Parameters.

Defines:
- Physical and experimental thresholds (e.g., passenger car critical flood depth)
- Routing policy weights and penalty multipliers
- Abstention rules and uncertainty quantile settings
- Scientific operating modes
- File system paths for data, models, and evaluation outputs
"""

import os
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
BENCHMARK_DATA_DIR = DATA_DIR / "benchmark"
FIXTURES_DATA_DIR = DATA_DIR / "fixtures"
SATELLITE_DATA_DIR = DATA_DIR / "satellite"
EXPERIMENTS_DIR = BASE_DIR / "experiments"
OUTPUTS_DIR = EXPERIMENTS_DIR / "outputs"

for p in [BENCHMARK_DATA_DIR, FIXTURES_DATA_DIR, SATELLITE_DATA_DIR, OUTPUTS_DIR]:
    p.mkdir(parents=True, exist_ok=True)


class OperatingMode(str, Enum):
    """
    Explicit scientific operating modes:
    - Mode A: Road Network Only (ordinary routing on verified Thane network, flood status marked unknown)
    - Mode B: Historical Satellite Assessment (timestamped satellite observation snapshot, not continuous live updates)
    - Mode C: Exploratory Thane Scenario (explicitly labeled uncalibrated pluvial proxy, documented assumptions)
    - Mode D: Research Benchmarks (Sen1Floods11 and UrbanFloodBench data strictly isolated to research dashboard)
    """
    ROAD_NETWORK_ONLY = "road_network_only"
    SATELLITE_OBSERVATION = "satellite_observation"
    EXPLORATORY_THANE_SCENARIO = "exploratory_thane_scenario"
    RESEARCH_BENCHMARKS = "research_benchmarks"

    # Backwards-compatible aliases
    BENCHMARK_SIMULATION = "benchmark_simulation"
    DEVELOPMENT_DEMONSTRATION = "development_demonstration"


class RoutingPolicyType(str, Enum):
    """The four comparative routing policies required by Section 5.4."""
    SHORTEST_FASTEST = "shortest_fastest"
    DEPARTURE_TIME_AVOIDANCE = "departure_time_avoidance"
    TRAVERSAL_TIME_DETERMINISTIC = "traversal_time_deterministic"
    PROPOSED_RISK_AWARE = "proposed_risk_aware"


class SystemSettings(BaseModel):
    """Configurable system settings and experimental policy parameters."""

    # Default operating mode (Thane exploratory scenario)
    default_mode: OperatingMode = OperatingMode.EXPLORATORY_THANE_SCENARIO

    # Experimental Flood Inundation Policy Parameters
    # Typical passenger vehicles encounter water ingestion/stalling between 0.20m and 0.35m.
    # We set default critical depth to 0.30m (30 cm). This is an experimental policy parameter,
    # NOT a universal claim of physical safety.
    critical_depth_m: float = Field(
        default=0.30,
        description="Depth above which a road segment is deemed impassable for passenger vehicles."
    )

    # Moderate flood warning depth: 0.15m (15 cm)
    # Slows travel speed significantly (water dragging resistance)
    caution_depth_m: float = Field(
        default=0.15,
        description="Depth above which passenger vehicle speed is reduced due to water resistance."
    )

    # Speed reduction factor on cautioned segments (0.15m <= depth < 0.30m)
    caution_speed_factor: float = Field(
        default=0.40,
        description="Speed multiplier on roads with caution-level water depth (40% of free-flow speed)."
    )

    # Risk-Aware Routing & Uncertainty Parameters
    risk_quantile: float = Field(
        default=0.90,
        description="Quantile of predicted flood depth distribution used for conservative decision-making (e.g. 90th percentile)."
    )

    risk_tolerance_probability: float = Field(
        default=0.25,
        description="Maximum acceptable probability of encountering critical depth d >= critical_depth_m."
    )

    # Explicit Abstention Policy Parameters
    # When travel time extends beyond supported forecast horizon, or when no route meets risk tolerance.
    max_forecast_horizon_minutes: int = Field(
        default=180,
        description="Maximum reliable forward forecast horizon (3 hours). Trips exceeding this trigger abstention."
    )

    max_allowable_detour_factor: float = Field(
        default=3.5,
        description="Maximum ratio of flood-avoidance travel time to free-flow baseline before recommending abstention."
    )

    # Time discretization interval (15 minutes = 900 seconds)
    timestep_interval_s: int = Field(
        default=900,
        description="Interval between simulation/forecast time steps in seconds (15 minutes)."
    )

    # Default passenger vehicle free-flow speeds by OSM highway type (km/h)
    free_flow_speeds_kmh: dict[str, float] = {
        "motorway": 80.0,
        "trunk": 60.0,
        "primary": 50.0,
        "secondary": 40.0,
        "tertiary": 30.0,
        "residential": 25.0,
        "unclassified": 25.0,
        "service": 15.0
    }

    # API Server Settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000


settings = SystemSettings()
