"""
Flood Grid and Hydrodynamic Mesh Representation.

Handles:
- 2D hydrodynamic simulation cells with polygon boundaries, ground elevation,
  water surface elevation (WSE), and derived water depth.
- Multi-step temporal evolution across storm scenarios.
- Spatial overlay between road segments and flood elements to compute
  traversal depth, maximum depth, submerged length, and inundation uncertainty.
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from pydantic import BaseModel, Field
from shapely.geometry import Polygon, LineString, Point, box
from shapely.strtree import STRtree
from backend.app.config import settings


class FloodCell(BaseModel):
    """Represents a 2D overland mesh cell or hydrodynamic grid element."""
    cell_id: str
    polygon_coords: List[Tuple[float, float]]  # [(lon, lat), ...]
    centroid_lat: float
    centroid_lon: float
    ground_elevation_m: float
    roughness_n: float = 0.035
    area_m2: float = 400.0  # 20m x 20m default mesh


class CellTimeStepState(BaseModel):
    """Dynamic hydraulic state of a cell at a specific simulation timestamp."""
    water_surface_elev_m: float
    water_depth_m: float  # Derived: max(0, WSE - ground_elev)
    water_volume_m3: float
    rainfall_intensity_mmh: float = 0.0
    predicted_depth_p50_m: Optional[float] = None
    predicted_depth_p90_m: Optional[float] = None
    inundation_prob: Optional[float] = None


class FloodGridScenario:
    """
    Manages spatial layout and multi-step time series of inundation depths
    for a specific storm scenario.
    """
    def __init__(
        self,
        scenario_id: str,
        name: str,
        rainfall_description: str,
        total_rainfall_mm: float,
        timesteps: List[datetime]
    ):
        self.scenario_id = scenario_id
        self.name = name
        self.rainfall_description = rainfall_description
        self.total_rainfall_mm = total_rainfall_mm
        self.timesteps = timesteps  # Ordered list of UTC datetimes
        self.cells: Dict[str, FloodCell] = {}
        # Mapping: {timestep_idx: {cell_id: CellTimeStepState}}
        self.states: Dict[int, Dict[str, CellTimeStepState]] = {}
        self._cell_polygons: List[Polygon] = []
        self._cell_ids: List[str] = []
        self._strtree: Optional[STRtree] = None

    def add_cell(self, cell: FloodCell):
        self.cells[cell.cell_id] = cell
        poly = Polygon(cell.polygon_coords)
        self._cell_polygons.append(poly)
        self._cell_ids.append(cell.cell_id)

    def build_spatial_index(self):
        """Builds an R-Tree spatial index for high-speed road intersection queries."""
        if self._cell_polygons:
            self._strtree = STRtree(self._cell_polygons)

    def set_cell_state(self, timestep_idx: int, cell_id: str, state: CellTimeStepState):
        if timestep_idx not in self.states:
            self.states[timestep_idx] = {}
        self.states[timestep_idx][cell_id] = state

    def get_closest_timestep_idx(self, query_time: datetime) -> int:
        """Finds the simulation timestep index closest to a query timestamp."""
        if not self.timesteps:
            return 0
        deltas = [abs((t - query_time).total_seconds()) for t in self.timesteps]
        return int(np.argmin(deltas))

    def evaluate_edge_inundation(
        self,
        edge_geometry_coords: List[Tuple[float, float]],
        query_time: datetime,
        is_bridge: bool = False,
        bridge_deck_elevation_m: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Overlays a road edge linestring onto intersecting flood cells at query_time.
        Computes reference simulation depth, AI predicted depth, and uncertainty quantiles.
        Accounts for bridge deck elevation (Section 5.1: Do not infer bridge flooding solely from terrain underneath).
        """
        ts_idx = self.get_closest_timestep_idx(query_time)
        cell_states = self.states.get(ts_idx, {})

        # If it is an elevated bridge with deck elevation known, check if water surface reaches the deck
        if is_bridge and bridge_deck_elevation_m is not None:
            # Check maximum water surface elevation in intersecting cells
            edge_line = LineString(edge_geometry_coords)
            if self._strtree is None:
                self.build_spatial_index()
            intersecting_indices = self._strtree.query(edge_line) if self._strtree else []
            wse_list = []
            for idx in intersecting_indices:
                cid = self._cell_ids[idx]
                st = cell_states.get(cid)
                if st:
                    wse_list.append(st.water_surface_elev_m)
            max_wse = max(wse_list) if wse_list else 0.0
            if max_wse < bridge_deck_elevation_m:
                # Bridge deck is elevated above flood water
                return {
                    "timestep_idx": ts_idx,
                    "valid_time": self.timesteps[ts_idx].isoformat() if self.timesteps else query_time.isoformat(),
                    "mean_depth_m": 0.0,
                    "max_depth_m": 0.0,
                    "p90_depth_m": 0.0,
                    "inundation_prob": 0.0,
                    "flooded_ratio": 0.0,
                    "status": "passable",
                    "bridge_elevated_clear": True
                }

        edge_line = LineString(edge_geometry_coords)
        if self._strtree is None:
            self.build_spatial_index()

        intersecting_indices = self._strtree.query(edge_line) if self._strtree else []

        if len(intersecting_indices) == 0:
            # Road segment outside active flood cell domain
            return {
                "timestep_idx": ts_idx,
                "valid_time": self.timesteps[ts_idx].isoformat() if self.timesteps else query_time.isoformat(),
                "mean_depth_m": 0.0,
                "max_depth_m": 0.0,
                "p90_depth_m": 0.0,
                "inundation_prob": 0.0,
                "flooded_ratio": 0.0,
                "status": "dry"
            }

        depths = []
        p90_depths = []
        probs = []
        for idx in intersecting_indices:
            cid = self._cell_ids[idx]
            state = cell_states.get(cid)
            if state:
                depths.append(state.water_depth_m)
                p90_depths.append(state.predicted_depth_p90_m if state.predicted_depth_p90_m is not None else state.water_depth_m * 1.15)
                probs.append(state.inundation_prob if state.inundation_prob is not None else (1.0 if state.water_depth_m >= settings.critical_depth_m else 0.0))

        if not depths:
            mean_d, max_d, p90_d, prob = 0.0, 0.0, 0.0, 0.0
        else:
            mean_d = float(np.mean(depths))
            max_d = float(np.max(depths))
            p90_d = float(np.max(p90_depths))
            prob = float(np.max(probs))

        flooded_ratio = sum(1 for d in depths if d >= settings.critical_depth_m) / max(1, len(depths))

        # Classify status
        if max_d >= settings.critical_depth_m:
            status = "impassable"
        elif max_d >= settings.caution_depth_m:
            status = "caution"
        else:
            status = "passable"

        return {
            "timestep_idx": ts_idx,
            "valid_time": self.timesteps[ts_idx].isoformat() if self.timesteps else query_time.isoformat(),
            "mean_depth_m": round(mean_d, 3),
            "max_depth_m": round(max_d, 3),
            "p90_depth_m": round(p90_d, 3),
            "inundation_prob": round(prob, 3),
            "flooded_ratio": round(flooded_ratio, 3),
            "status": status
        }
