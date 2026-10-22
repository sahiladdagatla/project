"""
Road Network Graph Representation and Connectivity Operations.

Represents:
- Road nodes (intersections, terminals) with geographic coordinates (lat, lon) and elevation.
- Directed road segments (edges) with geometry, length, speed limit, free-flow time,
  functional class, one-way constraints, and bridge/underpass metadata.
- Metric calculations and graph topology using NetworkX.
- Identification of strongly connected components and access restrictions.
"""

from typing import Dict, List, Tuple, Optional, Any
import networkx as nx
from pydantic import BaseModel, Field
from shapely.geometry import LineString, Point
from backend.app.core.spatial import linestring_length_m, haversine_distance_m
from backend.app.config import settings


class RoadNode(BaseModel):
    """Represents a junction or terminal in the road graph."""
    node_id: str
    lat: float
    lon: float
    elevation_m: float = 0.0
    tags: Dict[str, Any] = Field(default_factory=dict)


class RoadEdge(BaseModel):
    """Represents a directed road link between two nodes."""
    edge_id: str
    u: str
    v: str
    geometry_coords: List[Tuple[float, float]]  # [(lon, lat), ...]
    length_m: float
    highway_type: str = "primary"
    speed_limit_kmh: float = 50.0
    free_flow_time_s: float
    oneway: bool = False
    is_bridge: bool = False
    is_tunnel: bool = False
    bridge_deck_elevation_m: Optional[float] = None
    elevation_confidence: str = "medium"  # 'high', 'medium', 'unknown'


class RoadNetwork:
    """
    Directed transportation network graph.
    Separates transport connectivity from hydrological connectivity.
    """
    def __init__(self, name: str = "UrbanRoadNetwork"):
        self.name = name
        self.nodes: Dict[str, RoadNode] = {}
        self.edges: Dict[str, RoadEdge] = {}
        self.graph = nx.DiGraph()

    def add_node(self, node: RoadNode):
        self.nodes[node.node_id] = node
        self.graph.add_node(
            node.node_id,
            lat=node.lat,
            lon=node.lon,
            elevation_m=node.elevation_m
        )

    def add_edge(self, edge: RoadEdge):
        self.edges[edge.edge_id] = edge
        self.graph.add_edge(
            edge.u,
            edge.v,
            edge_id=edge.edge_id,
            length_m=edge.length_m,
            weight=edge.free_flow_time_s,
            free_flow_time_s=edge.free_flow_time_s,
            speed_limit_kmh=edge.speed_limit_kmh,
            highway_type=edge.highway_type,
            geometry_coords=edge.geometry_coords,
            is_bridge=edge.is_bridge,
            is_tunnel=edge.is_tunnel,
            bridge_deck_elevation_m=edge.bridge_deck_elevation_m
        )

    def find_nearest_node(self, lat: float, lon: float, max_dist_m: float = 1500.0) -> Tuple[Optional[str], float]:
        """Finds the nearest graph node to a query coordinate. Returns (node_id, distance_m)."""
        best_node = None
        min_dist = float("inf")
        for node_id, node in self.nodes.items():
            dist = haversine_distance_m(lat, lon, node.lat, node.lon)
            if dist < min_dist:
                min_dist = dist
                best_node = node_id
        if min_dist <= max_dist_m:
            return best_node, min_dist
        return None, min_dist

    def get_strongly_connected_subgraph(self) -> 'RoadNetwork':
        """
        Extracts the largest strongly connected component (SCC) to prevent dead-end or
        unreachable partition errors during pathfinding.
        """
        sccs = list(nx.strongly_connected_components(self.graph))
        if not sccs:
            return self
        largest_scc = max(sccs, key=len)
        sub_net = RoadNetwork(name=f"{self.name}_SCC")
        for node_id in largest_scc:
            sub_net.add_node(self.nodes[node_id])
        for u, v, data in self.graph.edges(data=True):
            if u in largest_scc and v in largest_scc:
                edge_id = data["edge_id"]
                sub_net.add_edge(self.edges[edge_id])
        return sub_net

    def to_geojson(self) -> Dict[str, Any]:
        """Exports the entire road network as standard GeoJSON LineStrings."""
        features = []
        for edge_id, edge in self.edges.items():
            features.append({
                "type": "Feature",
                "id": edge_id,
                "geometry": {
                    "type": "LineString",
                    "coordinates": edge.geometry_coords
                },
                "properties": {
                    "edge_id": edge_id,
                    "u": edge.u,
                    "v": edge.v,
                    "length_m": round(edge.length_m, 1),
                    "highway_type": edge.highway_type,
                    "speed_limit_kmh": edge.speed_limit_kmh,
                    "free_flow_time_s": round(edge.free_flow_time_s, 1),
                    "is_bridge": edge.is_bridge,
                    "is_tunnel": edge.is_tunnel
                }
            })
        return {
            "type": "FeatureCollection",
            "features": features
        }
