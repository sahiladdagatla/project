"""
Auditable Routing Explanation Engine.

Section 5.8: "Routing explanation:
- Segments excluded.
- Timing of expected exposure.
- Travel-time tradeoffs.
- Uncertainty-related decisions.
- Reason for declining to recommend a route.
Use deterministic, auditable explanation templates initially."
"""

from typing import Dict, Any, List, Optional
from backend.app.config import RoutingPolicyType, settings


def build_routing_explanation(
    policy: RoutingPolicyType,
    route_available: bool,
    abstained: bool,
    abstention_reason: Optional[str],
    total_duration_s: Optional[float],
    free_flow_duration_s: float,
    total_exposure_m: float,
    max_depth_m: float,
    excluded_edges_count: int,
    segments: List[Any],
    policy_params: Dict[str, Any]
) -> Dict[str, Any]:
    """Generates structured deterministic explanations for the route decision."""

    details = {
        "policy": policy.value,
        "summary": "",
        "segments_excluded_count": excluded_edges_count,
        "exposure_assessment": {
            "total_flooded_distance_m": round(total_exposure_m, 1),
            "max_encountered_depth_m": round(max_depth_m, 3),
            "critical_threshold_m": settings.critical_depth_m,
            "caution_threshold_m": settings.caution_depth_m
        },
        "timing_and_tradeoffs": {},
        "abstention_analysis": {}
    }

    if abstained or not route_available:
        details["summary"] = f"No recommended route under {policy.value}: {abstention_reason or 'No connected path exists.'}"
        details["abstention_analysis"] = {
            "abstained": True,
            "reason_code": abstention_reason or "NO_PATH_FOUND",
            "explanation": (
                "The system explicitly declined to recommend a route because "
                + (_format_abstention_text(abstention_reason))
            )
        }
        return details

    detour_s = max(0.0, total_duration_s - free_flow_duration_s) if total_duration_s else 0.0
    detour_ratio = (total_duration_s / max(1.0, free_flow_duration_s)) if total_duration_s else 1.0

    details["timing_and_tradeoffs"] = {
        "estimated_duration_min": round(total_duration_s / 60.0, 1) if total_duration_s else None,
        "free_flow_baseline_min": round(free_flow_duration_s / 60.0, 1),
        "additional_detour_min": round(detour_s / 60.0, 1),
        "detour_factor": round(detour_ratio, 2)
    }

    if policy == RoutingPolicyType.SHORTEST_FASTEST:
        details["summary"] = (
            f"Computed shortest free-flow path without querying flood state. "
            f"Encountered max predicted flood depth of {max_depth_m:.2f}m along the route."
        )
        if max_depth_m >= settings.critical_depth_m:
            details["critical_warning"] = (
                f"DANGER: Shortest path enters roadway segments with predicted depth ({max_depth_m:.2f}m) "
                f"exceeding passenger vehicle stalling limit ({settings.critical_depth_m:.2f}m). Route is unsafe!"
            )

    elif policy == RoutingPolicyType.DEPARTURE_TIME_AVOIDANCE:
        details["summary"] = (
            f"Avoided segments flooded at departure time. Assumes static conditions during journey. "
            f"Detour of {round(detour_s / 60.0, 1)} min over baseline."
        )
        if max_depth_m >= settings.critical_depth_m:
            details["critical_warning"] = (
                f"TRAP DETECTED: This route appeared safe at departure time, but flood evolution during traversal "
                f"submerged later segments up to {max_depth_m:.2f}m! Demonstrates the danger of departure-only routing."
            )

    elif policy == RoutingPolicyType.TRAVERSAL_TIME_DETERMINISTIC:
        details["summary"] = (
            f"Evaluated each segment at actual vehicle arrival time using deterministic point forecasts. "
            f"Successfully circumvents forward-evolving flood wave."
        )

    elif policy == RoutingPolicyType.PROPOSED_RISK_AWARE:
        details["summary"] = (
            f"Proposed uncertainty-aware route evaluating 90th percentile depth (q90) and exceedance risk at arrival times. "
            f"Hard-excluded high-risk links. Total detour: {round(detour_s / 60.0, 1)} min."
        )

    return details


def _format_abstention_text(reason: Optional[str]) -> str:
    if not reason:
        return "all available road connections between origin and destination are physically impassable or submerged."
    if "forecast_horizon" in reason:
        return "the projected trip duration extends past the verified 3-hour forecast horizon; unvalidated extrapolation was rejected."
    if "detour" in reason:
        return "the required detour exceeds acceptable safety/fuel limits (>3.5x free flow duration)."
    if "risk_tolerance" in reason:
        return "all navigable paths exceed the conservative uncertainty tolerance threshold (risk of severe entrapment)."
    return reason
