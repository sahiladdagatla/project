"""
Implementation of the Four Comparative Routing Policies.

Section 5.4 requirements:
1. Ordinary shortest or fastest path.
2. Routing that avoids flooding at departure time.
3. Routing using predicted conditions at traversal times.
4. Proposed routing using predictions, uncertainty, and explicit exclusion or abstention rules.

All routing methods are evaluated along their actual traversal intervals.
"""

import heapq
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from backend.app.config import settings, RoutingPolicyType
from backend.app.core.road_network import RoadNetwork, RoadEdge
from backend.app.core.flood_grid import FloodGridScenario
from backend.app.core.spatial import haversine_distance_m
from backend.app.core.temporal import parse_iso_timestamp, format_iso_timestamp, ForecastHorizonValidator
from backend.app.routing.models import RouteResult, RouteSegmentTraversal
from backend.app.routing.explanations import build_routing_explanation


class FloodRouter:
    """Core routing engine implementing all four routing policies."""

    def __init__(self, road_network: RoadNetwork, flood_grid: FloodGridScenario):
        self.network = road_network
        self.flood_grid = flood_grid
        self.horizon_validator = ForecastHorizonValidator(max_horizon_seconds=settings.max_forecast_horizon_minutes * 60)

    def route(
        self,
        policy: RoutingPolicyType,
        origin_node: str,
        dest_node: str,
        departure_time_str: str,
        issue_time_str: Optional[str] = None
    ) -> RouteResult:
        """Dispatches routing to the requested policy."""
        dep_dt = parse_iso_timestamp(departure_time_str)
        issue_dt = parse_iso_timestamp(issue_time_str) if issue_time_str else dep_dt

        # Validate nodes exist in network
        if origin_node not in self.network.nodes or dest_node not in self.network.nodes:
            return RouteResult(
                policy=policy,
                policy_name=policy.value,
                origin_node_id=origin_node,
                destination_node_id=dest_node,
                departure_time=format_iso_timestamp(dep_dt),
                route_available=False,
                abstained=True,
                abstention_reason="origin_or_destination_node_not_found_in_network"
            )

        # Baseline free-flow calculation for detour reference
        free_flow_res = self._compute_shortest_fastest(origin_node, dest_node, dep_dt)
        free_flow_duration_s = free_flow_res.total_duration_s or 1.0

        if policy == RoutingPolicyType.SHORTEST_FASTEST:
            return free_flow_res

        elif policy == RoutingPolicyType.DEPARTURE_TIME_AVOIDANCE:
            return self._compute_departure_avoidance(origin_node, dest_node, dep_dt, free_flow_duration_s)

        elif policy == RoutingPolicyType.TRAVERSAL_TIME_DETERMINISTIC:
            return self._compute_traversal_deterministic(origin_node, dest_node, dep_dt, free_flow_duration_s)

        elif policy == RoutingPolicyType.PROPOSED_RISK_AWARE:
            return self._compute_proposed_risk_aware(origin_node, dest_node, dep_dt, issue_dt, free_flow_duration_s)

        raise ValueError(f"Unknown policy: {policy}")

    def _compute_shortest_fastest(
        self,
        origin_node: str,
        dest_node: str,
        dep_dt: datetime
    ) -> RouteResult:
        """
        Policy 1: Ordinary shortest/fastest path.
        Ignores flood conditions entirely during path selection.
        Then evaluates the chosen path against actual traversal times to measure encountered exposure.
        """
        distances: Dict[str, float] = {origin_node: 0.0}
        predecessors: Dict[str, Tuple[str, str]] = {}  # {node: (prev_node, edge_id)}
        pq = [(0.0, origin_node)]

        while pq:
            curr_dist, u = heapq.heappop(pq)
            if curr_dist > distances.get(u, float("inf")):
                continue
            if u == dest_node:
                break

            for v in self.network.graph.neighbors(u):
                edge_data = self.network.graph.get_edge_data(u, v)
                edge_id = edge_data["edge_id"]
                weight = edge_data["free_flow_time_s"]
                new_dist = curr_dist + weight
                if new_dist < distances.get(v, float("inf")):
                    distances[v] = new_dist
                    predecessors[v] = (u, edge_id)
                    heapq.heappush(pq, (new_dist, v))

        if dest_node not in predecessors and origin_node != dest_node:
            return RouteResult(
                policy=RoutingPolicyType.SHORTEST_FASTEST,
                policy_name="Ordinary Shortest/Fastest Path",
                origin_node_id=origin_node,
                destination_node_id=dest_node,
                departure_time=format_iso_timestamp(dep_dt),
                route_available=False,
                abstained=False,
                abstention_reason="no_path_exists_in_graph"
            )

        # Reconstruct path and evaluate traversal exposure
        edges_sequence = self._reconstruct_edge_sequence(dest_node, origin_node, predecessors)
        return self._evaluate_route_traversal(
            RoutingPolicyType.SHORTEST_FASTEST,
            "Ordinary Shortest/Fastest Path",
            origin_node,
            dest_node,
            edges_sequence,
            dep_dt,
            free_flow_duration_s=distances.get(dest_node, 0.0),
            excluded_count=0
        )

    def _compute_departure_avoidance(
        self,
        origin_node: str,
        dest_node: str,
        dep_dt: datetime,
        free_flow_duration_s: float
    ) -> RouteResult:
        """
        Policy 2: Departure-time flood avoidance.
        Evaluates flood depths at departure time t_dep ONLY.
        Assumes static conditions throughout the journey.
        """
        excluded_edges = set()
        edge_weights = {}

        # Evaluate all edges at dep_dt
        for edge_id, edge in self.network.edges.items():
            inundation = self.flood_grid.evaluate_edge_inundation(
                edge.geometry_coords,
                dep_dt,
                is_bridge=edge.is_bridge,
                bridge_deck_elevation_m=edge.bridge_deck_elevation_m
            )
            max_d = inundation["max_depth_m"]
            if max_d >= settings.critical_depth_m:
                excluded_edges.add(edge_id)
            elif max_d >= settings.caution_depth_m:
                # Slower speed on caution segments
                edge_weights[edge_id] = edge.free_flow_time_s / settings.caution_speed_factor
            else:
                edge_weights[edge_id] = edge.free_flow_time_s

        distances: Dict[str, float] = {origin_node: 0.0}
        predecessors: Dict[str, Tuple[str, str]] = {}
        pq = [(0.0, origin_node)]

        while pq:
            curr_dist, u = heapq.heappop(pq)
            if curr_dist > distances.get(u, float("inf")):
                continue
            if u == dest_node:
                break

            for v in self.network.graph.neighbors(u):
                edge_data = self.network.graph.get_edge_data(u, v)
                edge_id = edge_data["edge_id"]
                if edge_id in excluded_edges:
                    continue  # Hard closure constraint

                weight = edge_weights.get(edge_id, edge_data["free_flow_time_s"])
                new_dist = curr_dist + weight
                if new_dist < distances.get(v, float("inf")):
                    distances[v] = new_dist
                    predecessors[v] = (u, edge_id)
                    heapq.heappush(pq, (new_dist, v))

        if dest_node not in predecessors and origin_node != dest_node:
            return RouteResult(
                policy=RoutingPolicyType.DEPARTURE_TIME_AVOIDANCE,
                policy_name="Departure-Time Flood Avoidance",
                origin_node_id=origin_node,
                destination_node_id=dest_node,
                departure_time=format_iso_timestamp(dep_dt),
                route_available=False,
                abstained=False,
                abstention_reason="all_candidate_paths_blocked_at_departure_time"
            )

        edges_sequence = self._reconstruct_edge_sequence(dest_node, origin_node, predecessors)
        return self._evaluate_route_traversal(
            RoutingPolicyType.DEPARTURE_TIME_AVOIDANCE,
            "Departure-Time Flood Avoidance",
            origin_node,
            dest_node,
            edges_sequence,
            dep_dt,
            free_flow_duration_s=free_flow_duration_s,
            excluded_count=len(excluded_edges)
        )

    def _compute_traversal_deterministic(
        self,
        origin_node: str,
        dest_node: str,
        dep_dt: datetime,
        free_flow_duration_s: float
    ) -> RouteResult:
        """
        Policy 3: Traversal-time deterministic routing.
        Evaluates each edge at the vehicle's arrival time tau(u).
        Uses deterministic point forecast of flood depth.
        """
        # Dijkstra with arrival times: priority queue stores (arrival_time_s, u)
        arrival_times: Dict[str, float] = {origin_node: 0.0}
        predecessors: Dict[str, Tuple[str, str]] = {}
        pq = [(0.0, origin_node)]
        excluded_edges_count = 0

        while pq:
            curr_time_s, u = heapq.heappop(pq)
            if curr_time_s > arrival_times.get(u, float("inf")):
                continue
            if u == dest_node:
                break

            curr_dt = dep_dt + timedelta(seconds=curr_time_s)

            for v in self.network.graph.neighbors(u):
                edge_data = self.network.graph.get_edge_data(u, v)
                edge_id = edge_data["edge_id"]
                edge = self.network.edges[edge_id]

                # Query flood condition at traversal time curr_dt
                inundation = self.flood_grid.evaluate_edge_inundation(
                    edge.geometry_coords,
                    curr_dt,
                    is_bridge=edge.is_bridge,
                    bridge_deck_elevation_m=edge.bridge_deck_elevation_m
                )
                max_d = inundation["max_depth_m"]

                # Exclude if inundated beyond critical threshold at traversal time
                if max_d >= settings.critical_depth_m:
                    excluded_edges_count += 1
                    continue

                # Speed penalty if in caution depth range
                if max_d >= settings.caution_depth_m:
                    traversal_s = edge.free_flow_time_s / settings.caution_speed_factor
                else:
                    traversal_s = edge.free_flow_time_s

                new_arrival_s = curr_time_s + traversal_s
                if new_arrival_s < arrival_times.get(v, float("inf")):
                    arrival_times[v] = new_arrival_s
                    predecessors[v] = (u, edge_id)
                    heapq.heappush(pq, (new_arrival_s, v))

        if dest_node not in predecessors and origin_node != dest_node:
            return RouteResult(
                policy=RoutingPolicyType.TRAVERSAL_TIME_DETERMINISTIC,
                policy_name="Traversal-Time Deterministic Routing",
                origin_node_id=origin_node,
                destination_node_id=dest_node,
                departure_time=format_iso_timestamp(dep_dt),
                route_available=False,
                abstained=False,
                abstention_reason="all_dynamic_paths_submerged_during_traversal"
            )

        edges_sequence = self._reconstruct_edge_sequence(dest_node, origin_node, predecessors)
        return self._evaluate_route_traversal(
            RoutingPolicyType.TRAVERSAL_TIME_DETERMINISTIC,
            "Traversal-Time Deterministic Routing",
            origin_node,
            dest_node,
            edges_sequence,
            dep_dt,
            free_flow_duration_s=free_flow_duration_s,
            excluded_count=excluded_edges_count
        )

    def _compute_proposed_risk_aware(
        self,
        origin_node: str,
        dest_node: str,
        dep_dt: datetime,
        issue_dt: datetime,
        free_flow_duration_s: float
    ) -> RouteResult:
        """
        Policy 4: Proposed uncertainty-aware routing with explicit abstention.
        Evaluates segments at arrival time tau(u).
        Uses quantile depth (q90) and exceedance probability.
        Applies conservative exclusion and explicit abstention rules.
        """
        arrival_times: Dict[str, float] = {origin_node: 0.0}
        predecessors: Dict[str, Tuple[str, str]] = {}
        pq = [(0.0, origin_node)]
        excluded_edges_count = 0
        max_horizon_s = settings.max_forecast_horizon_minutes * 60

        while pq:
            curr_time_s, u = heapq.heappop(pq)
            if curr_time_s > arrival_times.get(u, float("inf")):
                continue
            if u == dest_node:
                break

            # Abstention Check 1: If current search branch exceeds max forecast horizon, prune branch
            if curr_time_s > max_horizon_s:
                continue

            curr_dt = dep_dt + timedelta(seconds=curr_time_s)

            for v in self.network.graph.neighbors(u):
                edge_data = self.network.graph.get_edge_data(u, v)
                edge_id = edge_data["edge_id"]
                edge = self.network.edges[edge_id]

                # Query flood condition with uncertainty at traversal time curr_dt
                inundation = self.flood_grid.evaluate_edge_inundation(
                    edge.geometry_coords,
                    curr_dt,
                    is_bridge=edge.is_bridge,
                    bridge_deck_elevation_m=edge.bridge_deck_elevation_m
                )
                p90_d = inundation["p90_depth_m"]
                inundation_prob = inundation["inundation_prob"]

                # Conservative Exclusion Rule:
                # Exclude if 90th percentile depth >= critical depth OR exceedance probability > tolerance
                if p90_d >= settings.critical_depth_m or inundation_prob > settings.risk_tolerance_probability:
                    excluded_edges_count += 1
                    continue

                # Speed penalty if in caution depth range
                if p90_d >= settings.caution_depth_m:
                    traversal_s = edge.free_flow_time_s / settings.caution_speed_factor
                else:
                    traversal_s = edge.free_flow_time_s

                new_arrival_s = curr_time_s + traversal_s
                if new_arrival_s < arrival_times.get(v, float("inf")):
                    arrival_times[v] = new_arrival_s
                    predecessors[v] = (u, edge_id)
                    heapq.heappush(pq, (new_arrival_s, v))

        # Abstention Check 2: No route found
        if dest_node not in predecessors and origin_node != dest_node:
            return RouteResult(
                policy=RoutingPolicyType.PROPOSED_RISK_AWARE,
                policy_name="Proposed Risk-Aware Uncertainty Routing",
                origin_node_id=origin_node,
                destination_node_id=dest_node,
                departure_time=format_iso_timestamp(dep_dt),
                route_available=False,
                abstained=True,
                abstention_reason="risk_tolerance_exceeded_no_viable_path",
                explanation=build_routing_explanation(
                    RoutingPolicyType.PROPOSED_RISK_AWARE,
                    route_available=False,
                    abstained=True,
                    abstention_reason="risk_tolerance_exceeded_no_viable_path",
                    total_duration_s=None,
                    free_flow_duration_s=free_flow_duration_s,
                    total_exposure_m=0.0,
                    max_depth_m=0.0,
                    excluded_edges_count=excluded_edges_count,
                    segments=[],
                    policy_params={"risk_quantile": settings.risk_quantile}
                )
            )

        total_duration_s = arrival_times.get(dest_node, 0.0)

        # Abstention Check 3: Detour ratio exceeds maximum allowable threshold
        detour_ratio = total_duration_s / max(1.0, free_flow_duration_s)
        if detour_ratio > settings.max_allowable_detour_factor:
            return RouteResult(
                policy=RoutingPolicyType.PROPOSED_RISK_AWARE,
                policy_name="Proposed Risk-Aware Uncertainty Routing",
                origin_node_id=origin_node,
                destination_node_id=dest_node,
                departure_time=format_iso_timestamp(dep_dt),
                route_available=False,
                abstained=True,
                abstention_reason=f"detour_ratio_{detour_ratio:.1f}x_exceeds_maximum_threshold_{settings.max_allowable_detour_factor}x",
                explanation=build_routing_explanation(
                    RoutingPolicyType.PROPOSED_RISK_AWARE,
                    route_available=False,
                    abstained=True,
                    abstention_reason=f"excessive_detour_ratio_{detour_ratio:.1f}x",
                    total_duration_s=total_duration_s,
                    free_flow_duration_s=free_flow_duration_s,
                    total_exposure_m=0.0,
                    max_depth_m=0.0,
                    excluded_edges_count=excluded_edges_count,
                    segments=[],
                    policy_params={"detour_ratio": detour_ratio}
                )
            )

        # Abstention Check 4: Horizon validation
        est_arrival_dt = dep_dt + timedelta(seconds=total_duration_s)
        is_valid_horizon, horizon_reason = self.horizon_validator.validate_journey_window(
            issue_dt, dep_dt, est_arrival_dt
        )
        if not is_valid_horizon:
            return RouteResult(
                policy=RoutingPolicyType.PROPOSED_RISK_AWARE,
                policy_name="Proposed Risk-Aware Uncertainty Routing",
                origin_node_id=origin_node,
                destination_node_id=dest_node,
                departure_time=format_iso_timestamp(dep_dt),
                route_available=False,
                abstained=True,
                abstention_reason=horizon_reason,
                explanation=build_routing_explanation(
                    RoutingPolicyType.PROPOSED_RISK_AWARE,
                    route_available=False,
                    abstained=True,
                    abstention_reason=horizon_reason,
                    total_duration_s=total_duration_s,
                    free_flow_duration_s=free_flow_duration_s,
                    total_exposure_m=0.0,
                    max_depth_m=0.0,
                    excluded_edges_count=excluded_edges_count,
                    segments=[],
                    policy_params={}
                )
            )

        edges_sequence = self._reconstruct_edge_sequence(dest_node, origin_node, predecessors)
        return self._evaluate_route_traversal(
            RoutingPolicyType.PROPOSED_RISK_AWARE,
            "Proposed Risk-Aware Uncertainty Routing",
            origin_node,
            dest_node,
            edges_sequence,
            dep_dt,
            free_flow_duration_s=free_flow_duration_s,
            excluded_count=excluded_edges_count
        )

    def _reconstruct_edge_sequence(
        self,
        dest_node: str,
        origin_node: str,
        predecessors: Dict[str, Tuple[str, str]]
    ) -> List[str]:
        """Reconstructs ordered list of edge IDs from predecessors map."""
        edges = []
        curr = dest_node
        while curr != origin_node:
            prev, edge_id = predecessors[curr]
            edges.append(edge_id)
            curr = prev
        edges.reverse()
        return edges

    def _evaluate_route_traversal(
        self,
        policy: RoutingPolicyType,
        policy_name: str,
        origin_node: str,
        dest_node: str,
        edge_ids: List[str],
        dep_dt: datetime,
        free_flow_duration_s: float,
        excluded_count: int
    ) -> RouteResult:
        """
        Evaluates each edge of an established route along its actual traversal window.
        Tracks true encountered water depth, submerged length, and risk.
        """
        curr_dt = dep_dt
        traversal_segments: List[RouteSegmentTraversal] = []
        route_coords: List[Tuple[float, float]] = []
        total_len_m = 0.0
        total_flooded_m = 0.0
        caution_flooded_m = 0.0
        max_encountered_depth = 0.0

        for edge_id in edge_ids:
            edge = self.network.edges[edge_id]
            total_len_m += edge.length_m

            # Add coordinates (skip duplicate consecutive node coords)
            if not route_coords:
                route_coords.extend(edge.geometry_coords)
            else:
                route_coords.extend(edge.geometry_coords[1:])

            # Query condition at entry time curr_dt
            inundation = self.flood_grid.evaluate_edge_inundation(
                edge.geometry_coords,
                curr_dt,
                is_bridge=edge.is_bridge,
                bridge_deck_elevation_m=edge.bridge_deck_elevation_m
            )
            depth = inundation["mean_depth_m"]
            max_d = inundation["max_depth_m"]
            p90_d = inundation["p90_depth_m"]
            prob = inundation["inundation_prob"]

            if max_d > max_encountered_depth:
                max_encountered_depth = max_d

            # Traversal speed and duration calculation
            if max_d >= settings.critical_depth_m:
                # Submerged segment (vehicle enters water >= 30cm)
                speed_kmh = max(5.0, edge.speed_limit_kmh * 0.15)
                is_sub = True
                total_flooded_m += edge.length_m
            elif max_d >= settings.caution_depth_m:
                speed_kmh = edge.speed_limit_kmh * settings.caution_speed_factor
                is_sub = False
                caution_flooded_m += edge.length_m
            else:
                speed_kmh = edge.speed_limit_kmh
                is_sub = False

            duration_s = (edge.length_m / (speed_kmh * 1000.0 / 3600.0))
            end_dt = curr_dt + timedelta(seconds=duration_s)

            traversal_segments.append(RouteSegmentTraversal(
                edge_id=edge_id,
                u=edge.u,
                v=edge.v,
                length_m=round(edge.length_m, 1),
                highway_type=edge.highway_type,
                speed_kmh=round(speed_kmh, 1),
                traversal_start_time=format_iso_timestamp(curr_dt),
                traversal_end_time=format_iso_timestamp(end_dt),
                duration_s=round(duration_s, 1),
                predicted_depth_m=round(depth, 3),
                predicted_p90_depth_m=round(p90_d, 3),
                inundation_prob=round(prob, 3),
                status=inundation["status"],
                is_submerged=is_sub,
                coordinates=edge.geometry_coords
            ))

            curr_dt = end_dt

        total_duration_s = (curr_dt - dep_dt).total_seconds()
        explanation = build_routing_explanation(
            policy=policy,
            route_available=True,
            abstained=False,
            abstention_reason=None,
            total_duration_s=total_duration_s,
            free_flow_duration_s=free_flow_duration_s,
            total_exposure_m=total_flooded_m,
            max_depth_m=max_encountered_depth,
            excluded_edges_count=excluded_count,
            segments=traversal_segments,
            policy_params={"critical_depth_m": settings.critical_depth_m}
        )

        return RouteResult(
            policy=policy,
            policy_name=policy_name,
            origin_node_id=origin_node,
            destination_node_id=dest_node,
            departure_time=format_iso_timestamp(dep_dt),
            arrival_time=format_iso_timestamp(curr_dt),
            total_duration_s=round(total_duration_s, 1),
            total_length_m=round(total_len_m, 1),
            route_available=True,
            abstained=False,
            abstention_reason=None,
            segments=traversal_segments,
            total_inundated_exposure_m=round(total_flooded_m, 1),
            max_encountered_depth_m=round(max_encountered_depth, 3),
            caution_exposure_m=round(caution_flooded_m, 1),
            route_geometry=route_coords,
            explanation=explanation
        )
