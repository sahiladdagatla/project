"""
FastAPI Route Handlers for FloodTwinAI.

Serves:
- Status and metadata
- Road network and facilities GeoJSON
- Multi-step hydrodynamic flood mesh layer
- 4-policy comparative routing engine
- Dynamic facility accessibility & critical roads
- Satellite flood segmentation (Sen1Floods11)
- Real experimental results and ablation summaries
- Live Open-Meteo weather telemetry and dynamic live rainfall scenarios
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone

from backend.app.config import (
    OperatingMode, RoutingPolicyType, settings,
    BENCHMARK_DATA_DIR, OUTPUTS_DIR
)
from backend.app.thane_data_factory import generate_thane_catchment
from backend.app.live_weather import fetch_live_thane_weather, build_live_dynamic_scenario
from backend.app.routing.algorithms import FloodRouter
from backend.app.routing.models import PolicyComparisonResult, RouteResult
from backend.app.accessibility.facility_analysis import AccessibilityAnalyzer, NetworkAccessibilitySummary
from backend.app.accessibility.critical_roads import rank_critical_road_segments, CriticalRoadsRankingResult
from backend.app.models.satellite_segmentation.inference import SatelliteFloodService
from backend.app.api.schemas import (
    SystemStatusResponse, RouteComparisonRequest, ScenarioMetadataResponse,
    LiveWeatherResponse, SyncLiveWeatherRequest
)


router = APIRouter(prefix="/api")

# In-memory cached instances for fast, state-preserving responses
_network, _scenarios, _facilities, _places = generate_thane_catchment()
_satellite_service = SatelliteFloodService()

# Initialize dynamic live Open-Meteo weather scenario
_mesh_cells = list(next(iter(_scenarios.values())).cells.values())
_latest_live_weather = fetch_live_thane_weather()
_scenarios["thane_live_dynamic"] = build_live_dynamic_scenario(_mesh_cells, _latest_live_weather)


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status():
    """Returns current system health, active mode, and data provenance."""
    return SystemStatusResponse(
        project_name="FloodTwinAI (Thane-First Digital Twin)",
        version="2.0.0",
        operating_mode=settings.default_mode,
        cpu_only_mode=True,
        active_catchment="Thane City (TMC Administrative Boundary)",
        num_road_nodes=len(_network.nodes),
        num_road_edges=len(_network.edges),
        num_facilities=len(_facilities),
        num_scenarios=len(_scenarios),
        provenance_doi="OSM Relation 7120000 / Copernicus DEM / Sen1Floods11 (CC BY 4.0)"
    )


@router.get("/boundary/geojson")
def get_boundary_geojson():
    """Returns the verified Thane Municipal Corporation (TMC) boundary polygon."""
    boundary_path = BENCHMARK_DATA_DIR / "thane_administrative_boundary.geojson"
    if boundary_path.exists():
        with open(boundary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Thane administrative boundary GeoJSON not found on disk.")


@router.get("/places")
def get_places():
    """Returns verified Thane searchable places, junctions, landmarks, and hospitals."""
    return _places


@router.get("/weather/live", response_model=LiveWeatherResponse)
def get_live_weather():
    """Returns real-time Open-Meteo meteorological telemetry for Thane."""
    global _latest_live_weather
    _latest_live_weather = fetch_live_thane_weather()
    return _latest_live_weather


@router.post("/weather/sync")
def sync_live_weather(req: SyncLiveWeatherRequest):
    """
    Syncs live Open-Meteo weather and updates the dynamic live scenario in real time.
    Supports injecting live observed or projected rainfall intensities.
    """
    global _latest_live_weather, _scenarios
    _latest_live_weather = fetch_live_thane_weather()
    updated_sc = build_live_dynamic_scenario(_mesh_cells, _latest_live_weather, req.rain_override_mm)
    _scenarios["thane_live_dynamic"] = updated_sc
    return {
        "status": "success",
        "weather": _latest_live_weather,
        "scenario": {
            "scenario_id": updated_sc.scenario_id,
            "name": updated_sc.name,
            "description": updated_sc.rainfall_description,
            "total_rainfall_mm": updated_sc.total_rainfall_mm,
            "timesteps": [t.isoformat() for t in updated_sc.timesteps],
            "num_cells": len(updated_sc.cells)
        }
    }


@router.get("/scenarios", response_model=List[ScenarioMetadataResponse])
def get_scenarios():
    """Lists all supported benchmark and live hydrodynamic storm scenarios."""
    meta = []
    for sid, sc in _scenarios.items():
        meta.append(ScenarioMetadataResponse(
            scenario_id=sid,
            name=sc.name,
            description=sc.rainfall_description,
            total_rainfall_mm=sc.total_rainfall_mm,
            timesteps=[t.isoformat() for t in sc.timesteps],
            num_cells=len(sc.cells)
        ))
    return meta


@router.get("/network/geojson")
def get_road_network_geojson():
    """Returns the complete transportation road network in GeoJSON format."""
    return _network.to_geojson()


@router.get("/facilities/geojson")
def get_facilities_geojson():
    """Returns critical facility points (hospitals) in GeoJSON format."""
    features = []
    for fid, fac in _facilities.items():
        features.append({
            "type": "Feature",
            "id": fid,
            "geometry": {
                "type": "Point",
                "coordinates": [fac.lon, fac.lat]
            },
            "properties": {
                "facility_id": fid,
                "name": fac.name,
                "facility_type": fac.facility_type,
                "nearest_node_id": fac.nearest_node_id,
                "existing_on_map": True,
                "operational_status": fac.operational_status
            }
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/flood-layer")
def get_flood_layer(
    scenario_id: str = Query("thane_exploratory_pluvial_95mm", description="Scenario ID"),
    timestep_idx: int = Query(2, description="Timestep index (0 to 11)")
):
    """
    Returns the 2D hydrodynamic simulation mesh cells as a GeoJSON FeatureCollection
    at the specified scenario and timestep index.
    """
    if scenario_id not in _scenarios:
        scenario_id = "thane_exploratory_pluvial_95mm"
    if scenario_id not in _scenarios:
        scenario_id = next(iter(_scenarios.keys()))

    sc = _scenarios[scenario_id]
    timestep_idx = max(0, min(len(sc.timesteps) - 1, timestep_idx))
    valid_time = sc.timesteps[timestep_idx].isoformat()

    cell_states = sc.states.get(timestep_idx, {})
    features = []

    for cid, cell in sc.cells.items():
        st = cell_states.get(cid)
        depth = st.water_depth_m if st else 0.0
        p90_d = st.predicted_depth_p90_m if st else 0.0
        prob = st.inundation_prob if st else 0.0
        wse = st.water_surface_elev_m if st else cell.ground_elevation_m

        if depth >= settings.critical_depth_m:
            status = "impassable"
        elif depth >= settings.caution_depth_m:
            status = "caution"
        elif depth > 0.01:
            status = "shallow"
        else:
            status = "dry"

        features.append({
            "type": "Feature",
            "id": cid,
            "geometry": {
                "type": "Polygon",
                "coordinates": [cell.polygon_coords]
            },
            "properties": {
                "cell_id": cid,
                "water_depth_m": round(depth, 3),
                "p90_depth_m": round(p90_d, 3),
                "water_surface_elev_m": round(wse, 3),
                "ground_elevation_m": cell.ground_elevation_m,
                "inundation_prob": round(prob, 3),
                "status": status
            }
        })

    return {
        "type": "FeatureCollection",
        "scenario_id": scenario_id,
        "timestep_idx": timestep_idx,
        "valid_time": valid_time,
        "features": features
    }


@router.post("/route/compare", response_model=PolicyComparisonResult)
def compare_routing_policies(req: RouteComparisonRequest):
    """
    Core user-facing endpoint: Compares all 4 routing policies
    between origin and destination under the selected scenario and departure time.
    """
    scenario_id = req.scenario_id
    if scenario_id not in _scenarios:
        scenario_id = "thane_exploratory_pluvial_95mm"
    if scenario_id not in _scenarios:
        scenario_id = next(iter(_scenarios.keys()))

    sc = _scenarios[scenario_id]

    # Resolve nearest nodes to coordinates
    orig_node, dist_orig = _network.find_nearest_node(req.origin_lat, req.origin_lon)
    dest_node, dist_dest = _network.find_nearest_node(req.dest_lat, req.dest_lon)

    if not orig_node or not dest_node:
        raise HTTPException(
            status_code=400,
            detail=f"Origin ({req.origin_lat},{req.origin_lon}) or Destination ({req.dest_lat},{req.dest_lon}) outside network boundary."
        )

    # Determine departure time
    if req.departure_time_iso:
        dep_time_str = req.departure_time_iso
    else:
        ts_idx = max(0, min(len(sc.timesteps) - 1, req.timestep_idx or 2))
        dep_time_str = sc.timesteps[ts_idx].isoformat()

    router = FloodRouter(_network, sc)
    policy_results: Dict[RoutingPolicyType, RouteResult] = {}

    for pol in RoutingPolicyType:
        policy_results[pol] = router.route(pol, orig_node, dest_node, dep_time_str)

    # Comparison Trade-Off Summary
    ff_res = policy_results[RoutingPolicyType.SHORTEST_FASTEST]
    prop_res = policy_results[RoutingPolicyType.PROPOSED_RISK_AWARE]

    summary = {
        "origin_nearest_node": orig_node,
        "destination_nearest_node": dest_node,
        "departure_time": dep_time_str,
        "shortest_path_submerged_exposure_m": ff_res.total_inundated_exposure_m,
        "shortest_path_max_depth_m": ff_res.max_encountered_depth_m,
        "proposed_risk_aware_exposure_m": prop_res.total_inundated_exposure_m,
        "proposed_risk_aware_abstained": prop_res.abstained,
        "abstention_reason": prop_res.abstention_reason,
        "verdict": (
            "Proposed risk-aware method abstained to prevent hazardous entrapment."
            if prop_res.abstained else
            f"Proposed route reduced flood exposure from {ff_res.total_inundated_exposure_m:.1f}m to {prop_res.total_inundated_exposure_m:.1f}m."
        )
    }

    return PolicyComparisonResult(
        scenario_id=scenario_id,
        departure_time=dep_time_str,
        origin=(req.origin_lat, req.origin_lon),
        destination=(req.dest_lat, req.dest_lon),
        origin_node_id=orig_node,
        destination_node_id=dest_node,
        operating_mode=req.operating_mode,
        policies=policy_results,
        comparison_summary=summary
    )


@router.get("/accessibility", response_model=NetworkAccessibilitySummary)
def get_facility_accessibility(
    scenario_id: str = Query("thane_exploratory_pluvial_95mm"),
    timestep_idx: int = Query(2),
    origin_node_id: str = Query("TH_STATION")
):
    """Evaluates accessibility from an origin to all mapped hospitals."""
    if scenario_id not in _scenarios:
        scenario_id = "thane_exploratory_pluvial_95mm"
    if scenario_id not in _scenarios:
        scenario_id = next(iter(_scenarios.keys()))
    if origin_node_id not in _network.nodes:
        origin_node_id = "TH_STATION"

    sc = _scenarios[scenario_id]
    ts_idx = max(0, min(len(sc.timesteps) - 1, timestep_idx))
    query_dt = sc.timesteps[ts_idx]

    analyzer = AccessibilityAnalyzer(_network, sc)
    for fid, fac in _facilities.items():
        analyzer.register_facility(fac)

    return analyzer.evaluate_accessibility_at_time(origin_node_id, query_dt)


@router.get("/accessibility/critical-roads", response_model=CriticalRoadsRankingResult)
def get_critical_roads():
    """Returns ranked list of critical road connections based on accessibility loss."""
    return rank_critical_road_segments(_network, _facilities, top_k=10)


@router.get("/satellite/chips")
def list_satellite_chips():
    """Lists available Sen1Floods11 chips for satellite observation mode."""
    return _satellite_service.list_available_chips()


@router.get("/satellite/segment")
def segment_satellite_chip(chip_id: str = Query("Ghana_319168")):
    """Runs segmentation on a Sen1Floods11 chip and returns ground-truth IoU and water masks."""
    try:
        return _satellite_service.segment_chip(chip_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/experiments/results")
def get_experiment_results():
    """Returns actual measured benchmark evaluation results and ablation tables."""
    bench_file = OUTPUTS_DIR / "benchmark_routing_results.json"
    abl_file = OUTPUTS_DIR / "ablation_study_results.json"

    bench_data = json.loads(bench_file.read_text(encoding="utf-8")) if bench_file.exists() else {}
    abl_data = json.loads(abl_file.read_text(encoding="utf-8")) if abl_file.exists() else {}

    return {
        "benchmark": bench_data,
        "ablations": abl_data
    }
