"""
Infrastructure & Critical Facility Accessibility Analysis.

Section 5.5 requirements:
- Distinguish:
  1. A facility existing on the map.
  2. A facility being reachable in the network model.
  3. A facility actually operating (status unknown without empirical proof).
- Evaluates travel times to mapped hospitals as flood evolves.
- Quantifies reachability loss and identifies isolated network zones.
"""

from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import numpy as np
import networkx as nx
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.core.road_network import RoadNetwork
from backend.app.core.flood_grid import FloodGridScenario


class Facility(BaseModel):
    """Represents a critical infrastructure asset, primarily emergency hospitals."""
    facility_id: str
    name: str
    facility_type: str = "hospital"
    lat: float
    lon: float
    nearest_node_id: str
    existing_on_map: bool = True
    operational_status: str = "UNKNOWN_NO_VERIFIED_EVIDENCE"  # Section 5.5 constraint


class FacilityReachabilityResult(BaseModel):
    """Accessibility assessment for a specific facility at a specific timestamp."""
    facility_id: str
    name: str
    facility_type: str
    lat: float
    lon: float
    existing_on_map: bool
    is_reachable: bool
    travel_time_min: Optional[float]
    shortest_path_nodes: List[str] = Field(default_factory=list)
    encountered_max_depth_m: float = 0.0
    operational_status: str = "UNKNOWN"
    notes: str = ""


class NetworkAccessibilitySummary(BaseModel):
    """System-level infrastructure accessibility metrics across time."""
    timestamp: str
    timestep_idx: int
    total_facilities_count: int
    reachable_facilities_count: int
    accessibility_percentage: float
    average_travel_time_min: Optional[float]
    severed_road_segments_count: int
    isolated_nodes_count: int
    facility_reports: List[FacilityReachabilityResult]


class AccessibilityAnalyzer:
    """Computes dynamic reachability from an origin to mapped facilities."""

    def __init__(self, road_network: RoadNetwork, flood_grid: FloodGridScenario):
        self.network = road_network
        self.flood_grid = flood_grid
        self.facilities: Dict[str, Facility] = {}

    def register_facility(self, facility: Facility):
        self.facilities[facility.facility_id] = facility

    def evaluate_accessibility_at_time(
        self,
        origin_node_id: str,
        query_time: datetime
    ) -> NetworkAccessibilitySummary:
        """
        Evaluates reachability from origin_node_id to all registered facilities at query_time.
        Excludes roads with depth >= critical_depth_m.
        """
        ts_idx = self.flood_grid.get_closest_timestep_idx(query_time)

        # Filter out flooded edges to create open navigable subgraph
        open_graph = nx.DiGraph()
        for node_id, node in self.network.nodes.items():
            open_graph.add_node(node_id)

        severed_edges = 0
        for u, v, data in self.network.graph.edges(data=True):
            edge_id = data["edge_id"]
            edge = self.network.edges[edge_id]
            inundation = self.flood_grid.evaluate_edge_inundation(
                edge.geometry_coords,
                query_time,
                is_bridge=edge.is_bridge,
                bridge_deck_elevation_m=edge.bridge_deck_elevation_m
            )
            max_d = inundation["max_depth_m"]

            if max_d >= settings.critical_depth_m:
                severed_edges += 1
                continue  # Edge closed due to deep flooding

            weight = edge.free_flow_time_s
            if max_d >= settings.caution_depth_m:
                weight /= settings.caution_speed_factor

            open_graph.add_edge(u, v, weight=weight, max_depth=max_d)

        facility_reports: List[FacilityReachabilityResult] = []
        reachable_count = 0
        travel_times = []

        for fid, fac in self.facilities.items():
            target_node = fac.nearest_node_id
            if target_node not in open_graph:
                facility_reports.append(FacilityReachabilityResult(
                    facility_id=fid,
                    name=fac.name,
                    facility_type=fac.facility_type,
                    lat=fac.lat,
                    lon=fac.lon,
                    existing_on_map=True,
                    is_reachable=False,
                    travel_time_min=None,
                    encountered_max_depth_m=0.0,
                    operational_status="UNKNOWN_NO_VERIFIED_EVIDENCE",
                    notes="Target junction node severed from network."
                ))
                continue

            try:
                length, path = nx.single_source_dijkstra(open_graph, origin_node_id, target_node, weight="weight")
                reachable_count += 1
                time_min = round(length / 60.0, 1)
                travel_times.append(time_min)

                facility_reports.append(FacilityReachabilityResult(
                    facility_id=fid,
                    name=fac.name,
                    facility_type=fac.facility_type,
                    lat=fac.lat,
                    lon=fac.lon,
                    existing_on_map=True,
                    is_reachable=True,
                    travel_time_min=time_min,
                    shortest_path_nodes=path,
                    encountered_max_depth_m=0.0,
                    operational_status="UNKNOWN_NO_VERIFIED_EVIDENCE",
                    notes="Reachable via currently open routes."
                ))
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                facility_reports.append(FacilityReachabilityResult(
                    facility_id=fid,
                    name=fac.name,
                    facility_type=fac.facility_type,
                    lat=fac.lat,
                    lon=fac.lon,
                    existing_on_map=True,
                    is_reachable=False,
                    travel_time_min=None,
                    encountered_max_depth_m=0.0,
                    operational_status="UNKNOWN_NO_VERIFIED_EVIDENCE",
                    notes="Road access completely submerged or severed."
                ))

        # Isolated nodes count in open graph
        isolated_nodes = sum(1 for node in open_graph.nodes() if open_graph.degree(node) == 0)

        total_fac = max(1, len(self.facilities))
        avg_time = float(np.mean(travel_times)) if travel_times else None

        return NetworkAccessibilitySummary(
            timestamp=query_time.isoformat(),
            timestep_idx=ts_idx,
            total_facilities_count=len(self.facilities),
            reachable_facilities_count=reachable_count,
            accessibility_percentage=round((reachable_count / total_fac) * 100.0, 1),
            average_travel_time_min=round(avg_time, 1) if avg_time else None,
            severed_road_segments_count=severed_edges,
            isolated_nodes_count=isolated_nodes,
            facility_reports=facility_reports
        )
