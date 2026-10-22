"""
Routing Request and Result Data Schemas.

Defines:
- Input specifications (origin, destination, departure time, operating mode, policy).
- Segment-level traversal intervals and flood exposures.
- Abstention declarations and explanations.
- Multi-policy comparison structures.
"""

from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.config import RoutingPolicyType, OperatingMode


class RouteSegmentTraversal(BaseModel):
    """Detailed traversal record for an individual road segment along a route."""
    edge_id: str
    u: str
    v: str
    length_m: float
    highway_type: str
    speed_kmh: float
    traversal_start_time: str
    traversal_end_time: str
    duration_s: float
    predicted_depth_m: float
    predicted_p90_depth_m: float
    inundation_prob: float
    status: str  # 'passable', 'caution', 'impassable'
    is_submerged: bool
    coordinates: List[Tuple[float, float]]


class RouteResult(BaseModel):
    """Result of a routing execution under a specific policy."""
    policy: RoutingPolicyType
    policy_name: str
    origin_node_id: str
    destination_node_id: str
    departure_time: str
    arrival_time: Optional[str] = None
    total_duration_s: Optional[float] = None
    total_length_m: Optional[float] = None
    route_available: bool
    abstained: bool = False
    abstention_reason: Optional[str] = None
    abstention_details: Optional[Dict[str, Any]] = None
    segments: List[RouteSegmentTraversal] = Field(default_factory=list)
    total_inundated_exposure_m: float = 0.0
    max_encountered_depth_m: float = 0.0
    caution_exposure_m: float = 0.0
    route_geometry: List[Tuple[float, float]] = Field(default_factory=list)
    explanation: Dict[str, Any] = Field(default_factory=dict)


class PolicyComparisonResult(BaseModel):
    """Side-by-side comparison of the 4 routing policies required by Section 5.4."""
    scenario_id: str
    departure_time: str
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    origin_node_id: str
    destination_node_id: str
    operating_mode: OperatingMode
    policies: Dict[RoutingPolicyType, RouteResult]
    comparison_summary: Dict[str, Any]
