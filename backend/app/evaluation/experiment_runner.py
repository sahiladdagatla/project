"""
Reproducible Experiment Runner and Ablation Study Suite.

Addresses Primary Research Question (Section 7):
"Does uncertainty-aware, arrival-time-based routing reduce exposure to inundated roads
while preserving useful accessibility compared with shortest-path and deterministic flood-aware routing?"

Evaluates:
1. Held-out benchmark simulation scenarios (10yr, 50yr, 100yr, and Flash Surge).
2. The 4 comparative routing policies.
3. System ablations (removing arrival time, removing uncertainty, removing abstention).
4. Saves actual measured metrics to experiments/outputs/.
"""

import json
import time
from typing import Dict, List, Tuple, Any
import numpy as np
from pathlib import Path

from backend.app.config import OUTPUTS_DIR, RoutingPolicyType, settings
from backend.app.thane_data_factory import generate_thane_catchment
from backend.app.routing.algorithms import FloodRouter


def run_comprehensive_routing_benchmark() -> Dict[str, Any]:
    """
    Executes all 4 policies across multiple Thane storm events and departure times.
    Evaluates every route against held-out simulation ground truth.
    """
    net, scenarios, facilities, _ = generate_thane_catchment()

    # Representative OD evaluation pairs across different Thane corridors
    od_pairs = [
        ("TH_STATION", "CADBURY_JUNCTION", "Thane Station to Jupiter Hospital (EEH Corridor)"),
        ("NAUPADA", "COURT_NAKA", "Naupada to Thane Civil Hospital"),
        ("WAGLE_ESTATE", "VARTAK_NAGAR", "Wagle Industrial Estate to Bethany Hospital"),
        ("TEEN_HATH_NAKA", "MANPADA", "Teen Hath Naka to Titan Hospital (Ghodbunder Spine)"),
        ("COURT_NAKA", "CSMH_KALWA_JCT", "Court Naka to CSMH Kalwa across Kalwa Bridge"),
        ("MULUND_TOLL", "HIRANANDANI_EST", "Mulund Entry to Hiranandani Estate"),
        ("VANDANA_CINEMA", "CADBURY_JUNCTION", "Vandana Depression Hotspot to Cadbury Junction"),
        ("UPVAN_LAKE", "CSMH_KALWA_JCT", "Upvan Foothills to Kalwa Municipal Hospital")
    ]

    departure_step_indices = [1, 2, 3, 4]  # T+15m, T+30m, T+45m, T+60m

    results_by_policy: Dict[str, List[Dict[str, Any]]] = {
        pol.value: [] for pol in RoutingPolicyType
    }

    start_bench_time = time.time()

    for sc_id, sc in scenarios.items():
        router = FloodRouter(net, sc)

        for ts_idx in departure_step_indices:
            dep_time = sc.timesteps[ts_idx].isoformat()

            for orig, dest, desc in od_pairs:
                for pol in RoutingPolicyType:
                    t0 = time.perf_counter()
                    res = router.route(pol, orig, dest, dep_time)
                    latency_ms = (time.perf_counter() - t0) * 1000.0

                    # Evaluate safety against simulation truth
                    # Unsafe if vehicle encountered depth >= critical_depth_m (0.30m)
                    is_unsafe = (res.max_encountered_depth_m >= settings.critical_depth_m) if res.route_available else False

                    results_by_policy[pol.value].append({
                        "scenario_id": sc_id,
                        "timestep_idx": ts_idx,
                        "departure_time": dep_time,
                        "origin": orig,
                        "destination": dest,
                        "description": desc,
                        "route_available": res.route_available,
                        "abstained": res.abstained,
                        "abstention_reason": res.abstention_reason,
                        "total_duration_s": res.total_duration_s,
                        "total_length_m": res.total_length_m,
                        "total_flooded_exposure_m": res.total_inundated_exposure_m,
                        "max_encountered_depth_m": res.max_encountered_depth_m,
                        "is_unsafe_failure": is_unsafe,
                        "latency_ms": round(latency_ms, 2)
                    })

    # Compute Aggregate Metrics per Policy
    summary_metrics = {}
    for pol_key, runs in results_by_policy.items():
        total_runs = len(runs)
        available_runs = [r for r in runs if r["route_available"]]
        abstained_runs = [r for r in runs if r["abstained"]]
        unsafe_runs = [r for r in runs if r["is_unsafe_failure"]]

        durations_min = [r["total_duration_s"] / 60.0 for r in available_runs if r["total_duration_s"] is not None]
        exposures_m = [r["total_flooded_exposure_m"] for r in available_runs]
        max_depths_m = [r["max_encountered_depth_m"] for r in available_runs]
        latencies_ms = [r["latency_ms"] for r in runs]

        summary_metrics[pol_key] = {
            "total_trips_evaluated": total_runs,
            "route_availability_rate": round(len(available_runs) / total_runs * 100.0, 1),
            "abstention_rate": round(len(abstained_runs) / total_runs * 100.0, 1),
            "unsafe_trip_rate": round(len(unsafe_runs) / total_runs * 100.0, 1),
            "mean_submerged_exposure_m": round(float(np.mean(exposures_m)), 1) if exposures_m else 0.0,
            "max_encountered_depth_overall_m": round(float(np.max(max_depths_m)), 3) if max_depths_m else 0.0,
            "mean_encountered_depth_m": round(float(np.mean(max_depths_m)), 3) if max_depths_m else 0.0,
            "mean_journey_duration_min": round(float(np.mean(durations_min)), 1) if durations_min else 0.0,
            "mean_computation_latency_ms": round(float(np.mean(latencies_ms)), 2)
        }

    benchmark_output = {
        "metadata": {
            "experiment_name": "Full Multi-Event Routing Benchmark",
            "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_scenarios_evaluated": len(scenarios),
            "total_od_pairs": len(od_pairs),
            "total_trips_per_policy": len(results_by_policy[RoutingPolicyType.SHORTEST_FASTEST.value]),
            "execution_time_s": round(time.time() - start_bench_time, 2)
        },
        "summary_table": summary_metrics,
        "detailed_runs": results_by_policy
    }

    # Save to file
    out_file = OUTPUTS_DIR / "benchmark_routing_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_output, f, indent=2)

    print(f"Benchmark results successfully saved to {out_file}")
    return benchmark_output


def run_ablation_study() -> Dict[str, Any]:
    """
    Conducts the systematic ablation study required by Section 9:
    - Full Proposed Framework (Arrival Time + Quantile Uncertainty + Abstention)
    - Ablation 1: Remove Uncertainty (Deterministic Traversal Time)
    - Ablation 2: Remove Arrival-Time (Departure-Time Avoidance)
    - Ablation 3: Baseline Shortest Path
    """
    net, scenarios, facilities, _ = generate_thane_catchment()
    test_scenario = scenarios.get("thane_cloudburst_flash_surge", next(iter(scenarios.values())))
    router = FloodRouter(net, test_scenario)

    od_pairs = [
        ("TH_STATION", "CADBURY_JUNCTION"),
        ("NAUPADA", "COURT_NAKA"),
        ("WAGLE_ESTATE", "VARTAK_NAGAR"),
        ("TEEN_HATH_NAKA", "MANPADA"),
        ("COURT_NAKA", "CSMH_KALWA_JCT"),
        ("MULUND_TOLL", "HIRANANDANI_EST")
    ]

    ablation_results = {}

    for name, pol in [
        ("Full_Proposed_Method", RoutingPolicyType.PROPOSED_RISK_AWARE),
        ("Ablation_No_Uncertainty", RoutingPolicyType.TRAVERSAL_TIME_DETERMINISTIC),
        ("Ablation_No_Arrival_Time", RoutingPolicyType.DEPARTURE_TIME_AVOIDANCE),
        ("Baseline_Shortest_Path", RoutingPolicyType.SHORTEST_FASTEST)
    ]:
        exposures = []
        unsafe_count = 0
        abstained_count = 0
        durations = []

        for ts_idx in [1, 2, 3]:
            dep_time = test_scenario.timesteps[ts_idx].isoformat()
            for orig, dest in od_pairs:
                res = router.route(pol, orig, dest, dep_time)
                if res.abstained:
                    abstained_count += 1
                elif res.route_available:
                    exposures.append(res.total_inundated_exposure_m)
                    durations.append(res.total_duration_s / 60.0)
                    if res.max_encountered_depth_m >= settings.critical_depth_m:
                        unsafe_count += 1

        total = len(od_pairs) * 3
        ablation_results[name] = {
            "total_trips": total,
            "abstained_count": abstained_count,
            "abstention_rate": round(abstained_count / total * 100.0, 1),
            "unsafe_trips_count": unsafe_count,
            "unsafe_failure_rate": round(unsafe_count / total * 100.0, 1),
            "mean_flooded_exposure_m": round(float(np.mean(exposures)), 1) if exposures else 0.0,
            "mean_duration_min": round(float(np.mean(durations)), 1) if durations else 0.0
        }

    out_file = OUTPUTS_DIR / "ablation_study_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(ablation_results, f, indent=2)

    print(f"Ablation study completed and saved to {out_file}")
    return ablation_results


if __name__ == "__main__":
    run_comprehensive_routing_benchmark()
    run_ablation_study()
