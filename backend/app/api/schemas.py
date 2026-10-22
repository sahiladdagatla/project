"""
Pydantic API Request and Response Schemas.

Enforces strict type validation and explicit data contracts.
"""

from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel, Field
from backend.app.config import OperatingMode, RoutingPolicyType
from backend.app.routing.models import RouteResult, PolicyComparisonResult
from backend.app.accessibility.facility_analysis import NetworkAccessibilitySummary
from backend.app.accessibility.critical_roads import CriticalRoadsRankingResult


class SystemStatusResponse(BaseModel):
    project_name: str = "FloodTwinAI"
    version: str = "1.0.0"
    operating_mode: OperatingMode
    cpu_only_mode: bool = True
    active_catchment: str
    num_road_nodes: int
    num_road_edges: int
    num_facilities: int
    num_scenarios: int
    provenance_doi: str


class RouteComparisonRequest(BaseModel):
    scenario_id: str = "thane_exploratory_pluvial_95mm"
    origin_lat: float = Field(default=19.1846, description="Origin latitude (default: Thane Station)")
    origin_lon: float = Field(default=72.9710, description="Origin longitude (default: Thane Station)")
    dest_lat: float = Field(default=19.2046, description="Destination latitude (default: Cadbury Junction / Jupiter Hospital)")
    dest_lon: float = Field(default=72.9688, description="Destination longitude (default: Cadbury Junction / Jupiter Hospital)")
    departure_time_iso: Optional[str] = None
    timestep_idx: Optional[int] = Field(default=2, description="Simulation timestep index (0 to 11)")
    operating_mode: OperatingMode = OperatingMode.EXPLORATORY_THANE_SCENARIO


class ScenarioMetadataResponse(BaseModel):
    scenario_id: str
    name: str
    description: str
    total_rainfall_mm: float
    timesteps: List[str]
    num_cells: int


class FloodLayerCellResponse(BaseModel):
    cell_id: str
    coordinates: List[Tuple[float, float]]
    water_depth_m: float
    p90_depth_m: float
    status: str  # 'dry', 'caution', 'impassable'
    water_surface_elev_m: float
    ground_elevation_m: float
