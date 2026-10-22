# FloodTwinAI: System Architecture & Technical Specification

**Project:** FloodTwinAI: An Urban Flood Digital Twin for Explainable Forecasting, Infrastructure Impact Analysis and Risk-Aware Routing  
**Document:** System Architecture Specification  
**Version:** 1.0.0  
**Date:** October 2026  

---

## 1. High-Level Architecture Overview

FloodTwinAI is architected as an academic, CPU-compatible decision-support digital twin platform that couples hydrodynamic simulation benchmarks, multi-quantile surrogate forecasting, time-dependent routing, and interactive geospatial visualization.

```
+---------------------------------------------------------------------------------------+
|                                    PRESENTATION LAYER                                 |
|   Vite + React (TypeScript) + Leaflet Geospatial Canvas + Responsive Glassmorphism    |
|   - Interactive Map: Hydrodynamic Mesh Polygons, Road Network, Bridges, Hospitals    |
|   - Multi-Policy Route Comparison Panel (Shortest vs Departure vs Traversal vs Risk)  |
|   - Dynamic Timeline Playback & Scenario Scrubber (T+0m to T+165m)                    |
|   - Infrastructure Accessibility & Critical Road Ranking Views                        |
|   - Satellite SAR (Sen1Floods11) Segmentation & Ground-Truth Verification            |
|   - Live Empirical Research Results & Ablation Analysis Dashboard                     |
+---------------------------------------------------------------------------------------+
                                           |  HTTPS / JSON API
+---------------------------------------------------------------------------------------+
|                                  API & APPLICATION LAYER                              |
|   FastAPI REST Service (Uvicorn / Starlette / Pydantic Contracts)                    |
|   - /api/status                 - /api/network/geojson       - /api/facilities/geojson |
|   - /api/scenarios              - /api/flood-layer           - /api/route/compare      |
|   - /api/accessibility          - /api/critical-roads        - /api/satellite/segment  |
|   - /api/experiments/results                                                          |
+---------------------------------------------------------------------------------------+
         |                                |                                   |
         v                                v                                   v
+-----------------------+   +---------------------------+   +---------------------------+
|    ROUTING ENGINE     |   |   FORECASTING & SURROGATE |   |   ACCESSIBILITY & ASSETS  |
| - Time-Dependent      |   | - Persistence Baseline    |   | - Hospital Reachability   |
|   Dijkstra            |   | - Quantile HistGBM (q90)  |   | - Travel Time Evolution   |
| - 4 Policy Evaluator  |   | - Exceedance Probability  |   | - Betweenness Centrality  |
| - Conservative Pruning|   | - Lightweight UNet (SAR)  |   | - Critical Edge Ranking   |
| - Transparent         |   | - Nodata Masking (-1)     |   | - Operational Status:     |
|   Abstention Rules    |   | - Lead-Time Horizon Check |   |   UNKNOWN_NO_EVIDENCE     |
+-----------------------+   +---------------------------+   +---------------------------+
                                          |
+---------------------------------------------------------------------------------------+
|                             DATA FOUNDATION & STORAGE LAYER                           |
|   - Benchmark Simulation Catchment: 2D Hydrodynamic Mesh + Topographic Elevations    |
|   - Vector Transportation Network: NetworkX Directed DiGraph + Speed Attributes       |
|   - Satellite Dataset: Public Sen1Floods11 Sentinel-1 GeoTIFF Chips & Ground Truth   |
|   - Development Fixtures: Clearly Quarantined Synthetic Graphs (Non-Research)         |
|   - Experiment Artifacts: Evaluated Benchmark Metrics & Ablation Results (JSON)       |
+---------------------------------------------------------------------------------------+
```

---

## 2. Core Modules Description

### 2.1 Geospatial & Temporal Foundation (`backend/app/core/`)
- `spatial.py`: Handles WGS84 geodesic calculations (`pyproj.Geod`), Euclidean A* heuristics, and bridge elevation clearance rules. Explicitly enforces that water under an elevated bridge does not imply road closure.
- `temporal.py`: Validates ISO8601 timestamps and checks forecast horizons against maximum supported simulation windows ($H_{max} = 180\text{ min}$).
- `road_network.py`: Manages the directed graph $G = (V, E)$, functional speed hierarchies, and extracts the largest strongly connected component (SCC) to prevent dead-end routing faults.
- `flood_grid.py`: R-Tree spatial indexing (`shapely.STRtree`) for rapid overlay of road linestrings onto 2D hydrodynamic simulation cells. Computes mean depth, 90th percentile depth, and submergence ratios.

### 2.2 Risk-Aware Routing Engine (`backend/app/routing/`)
- `algorithms.py`: Implements all four comparative policies:
  1. *Ordinary Shortest/Fastest Path:* Baseline free-flow Dijkstra.
  2. *Departure-Time Avoidance:* Static Dijkstra querying flood conditions solely at $t_{dep}$.
  3. *Traversal-Time Deterministic:* Time-dependent dynamic Dijkstra querying conditions at arrival time $\tau(u) = t_{dep} + g(u)$.
  4. *Proposed Risk-Aware Uncertainty Router:* Time-dependent Dijkstra using $q_{90}$ upper bound depth and exceedance probability $P(d \ge \theta_{crit})$, with conservative hard exclusion and auditable abstention.
- `explanations.py`: Generates deterministic, structured explanations detailing excluded road segments, detour trade-offs, and reasons for declining recommendations.

### 2.3 Flood Forecasting & Surrogate Models (`backend/app/models/flood_forecasting/`)
- `baseline_persistence.py`: Baseline assuming $\hat{d}_{t+h} = d_t$.
- `boosted_model.py`: Multi-quantile gradient boosting predicting $q_{10}$, $q_{50}$, and $q_{90}$ depths, evaluating interval coverage and mean interval width.

### 2.4 Satellite Flood Detection (`backend/app/models/satellite_segmentation/`)
- `unet_model.py`: Lightweight PyTorch U-Net for Sentinel-1 2-band SAR chips (VV, VH backscatter in dB).
- `metrics.py`: Computes Flood-Class IoU, precision, recall, and F1, strictly masking out nodata (`-1`) pixels.
- `inference.py`: Reads Cloud-Optimized GeoTIFF chips and runs segmentation.

### 2.5 Critical Infrastructure Accessibility (`backend/app/accessibility/`)
- `facility_analysis.py`: Tracks dynamic reachability from an origin to mapped emergency hospitals across simulation timesteps.
- `critical_roads.py`: Ranks road links by shortest-path betweenness centrality to emergency healthcare, identifying critical chokepoints.

---

## 3. Data Contracts & Scientific Boundaries

1. **Operating Mode Isolation:**
   - `benchmark_simulation`: Primary research environment.
   - `satellite_observation`: Periodic satellite snapshots.
   - `development_demonstration`: Isolated synthetic fixtures.
2. **Operational Status Honesty:** Mapped facilities default to `UNKNOWN_NO_VERIFIED_EVIDENCE` to maintain academic integrity.
3. **Reproducibility:** All experiment outputs are saved to versioned JSON files in `experiments/outputs/`.
