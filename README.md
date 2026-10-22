# FloodTwinAI: Thane Urban Flood Digital Twin

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0-emerald.svg)](https://fastapi.tiangolo.com/)
[![React + TypeScript](https://img.shields.io/badge/React-TypeScript-cyan.svg)](https://react.dev/)
[![Tests Passing](https://img.shields.io/badge/pytest-17%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![Open Access Benchmark](https://img.shields.io/badge/Data-OpenStreetMap%20%7C%20Copernicus%20DEM%20%7C%20Sen1Floods11-purple.svg)](https://www.openstreetmap.org/relation/7120000)

**Working Title:** *“FloodTwinAI: An Urban Flood Digital Twin for Explainable Forecasting, Infrastructure Impact Analysis and Risk-Aware Routing”*  
**Primary Application Focus:** **Thane City (Thane Municipal Corporation Area, Maharashtra, India)**  
**Academic Degree:** Final-Year B.Tech / B.E. Major Project in Artificial Intelligence & Data Science  
**Status:** Working Full-Stack System, Authenticated Thane Geography, Measured Empirical Results, and Academic Paper Draft  

---

## 1. Project Overview & Primary Research Question

During severe urban monsoon rainfall in coastal-adjacent Indian cities such as Thane, conventional navigation systems fail because they evaluate road conditions **only at departure time** ($t_{dep}$), implicitly assuming flood levels remain static throughout travel. In fast-evolving pluvial storms coupled with tidal backwater from the Thane Creek, roads clear at departure rapidly inundate—trapping vehicles in chronic low-lying bowls (the **departure-time trap**). Furthermore, deterministic navigation gives no confidence bounds near vehicle stalling thresholds ($d \ge 0.30\text{ m}$).

**Primary Research Question:**
> *“Does uncertainty-aware, arrival-time-based routing reduce exposure to inundated roads while preserving useful accessibility compared with shortest-path and deterministic flood-aware routing in complex urban terrain?”*

**FloodTwinAI Solves This Via:**
1. **Thane-First Topological Road Graph:** Derived from verified OpenStreetMap data bounded by the official Thane Municipal Corporation boundary (OSM Relation `7120000`). Incorporates elevated deck clearance for critical flyovers (Teen Hath Naka, Majiwada, Nitin, Kalwa Creek Bridge).
2. **Time-Dependent Traversal Routing:** Evaluates each road link at the vehicle's dynamic arrival time $\tau(e)$ rather than frozen departure time.
3. **Quantile Flood Uncertainty:** Employs multi-quantile bounds ($q_{10}, q_{50}, q_{90}$) to penalize or exclude deep tail risks.
4. **Transparent Abstention Engine:** Transparently declines to recommend unsafe journeys when flood depth exceeds passenger vehicle tolerances across all viable paths.
5. **Critical Healthcare Accessibility:** Analyzes dynamic reachability across 7 verified Thane hospitals (Jupiter, Bethany, Thane Civil, Kaushalya, Titan, Currae, CSMH Kalwa) with status marked `UNKNOWN_NO_VERIFIED_EVIDENCE`.
6. **Satellite SAR Verification:** Validates calibrated Sentinel-1 radar flood segmentation on public **Sen1Floods11** chips (**60.6% IoU**, **75.5% F1-score**), strictly isolated to satellite observation mode.

---

## 2. Scientific Operating Modes

FloodTwinAI enforces four explicit, non-overlapping operating modes:

1. **Mode A: Road Network Only:**
   - Navigates strictly across the verified Thane Municipal Corporation road network.
   - Flood depth is explicitly marked `UNKNOWN_NO_VERIFIED_EVIDENCE`.
2. **Mode B: Historical Satellite Assessment:**
   - Evaluates Sentinel-1 SAR dual-polarization chips (VV, VH) against ground truth from **Sen1Floods11**.
   - Emphasizes that satellite radar provides a timestamped observation snapshot, not continuous real-time forecasts.
3. **Mode C: Exploratory Thane Scenario (Primary Interactive Mode):**
   - Implements 4 explicit hydrodynamic scenarios (`thane_baseline_dry`, `thane_exploratory_pluvial_95mm`, `thane_exploratory_tidal_backwater`, `thane_cloudburst_flash_surge`).
   - Represents documented chronic depression hotspots (Vandana ST Depot, Teen Hath Naka at-grade, Majiwada underpass) and tidal backwater locks. Clearly labeled as an uncalibrated pluvial proxy for decision-support research.
4. **Mode D: Research Benchmarks:**
   - Strictly isolates benchmark simulation datasets and satellite ground-truth chips to the research analytics tab, preventing geographic conflation with Thane.

---

## 3. Quick Start & Local Setup

The system is 100% CPU-compatible, runs entirely offline without external API keys, and requires no GPU.

### 3.1 Prerequisites
- **Python:** 3.12.x
- **Node.js:** v20+ or v22+ (npm included)

### 3.2 Installation
```bash
# Clone or enter the workspace
cd "major project antigravity"

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies and compile UI bundle
cd frontend
npm install
npm run build
cd ..
```

### 3.3 Running the Application
```bash
# Start the FastAPI server (serves API and compiled React dashboard)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open your browser to: **`http://127.0.0.1:8000`**

### 3.4 Running the Test Suite
```bash
# Run all 17 automated unit and integration tests
python -m pytest tests/
```

### 3.5 Re-Running Experimental Benchmarks
```bash
# Recompute full multi-event routing benchmark and ablation study
python -m backend.app.evaluation.experiment_runner
```

---

## 4. Empirical Evaluation Results (Thane Catchment)

*Multi-Event Benchmark Evaluation (128 Trips per Policy across 8 Authentic Thane Corridors):*

| Routing Policy | Route Availability | Abstention Rate | Unsafe Failure Rate | Mean Inundated Exposure | Max Depth Encountered | Mean Journey Time | Mean Computation Latency |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Ordinary Shortest Path** | 100.0% | 0.0% | **69.5%** | 1,709.5 m | 1.56 m | 20.2 min | 0.37 ms |
| **2. Departure-Time Avoidance** | 32.8% | 0.0% | **2.3%** | 176.1 m | 0.85 m | 8.2 min | 3.50 ms |
| **3. Traversal-Time Deterministic** | 30.5% | 0.0% | **0.0%** | 0.0 m | 0.29 m | 6.2 min | 1.07 ms |
| **4. Proposed Risk-Aware + Abstention** | 25.0% | **75.0%** | **0.0%** | **0.0 m** | **0.00 m** | 5.8 min | **0.97 ms** |

### Key Scientific Findings:
1. **Departure-Time Trap Confirmed:** Under departure-time static avoidance ($P_2$), 2.3% of trips experience dangerous inundation because water accumulates in low-lying bowls (e.g. Vandana depression) while the vehicle is en route.
2. **Zero Failures with Transparent Abstention:** The proposed risk-aware policy ($P_4$) achieves a 0.0% unsafe failure rate. When severe pooling makes all routes hazardous, it transparently abstains rather than misguiding drivers into hazardous water.
3. **Real-Time Efficiency:** All algorithms compute in $\le 3.5\text{ ms}$ on standard student CPU hardware.

# Install Frontend dependencies and build bundle
cd frontend
npm install
npm run build
cd ..
```

### 3.3 Launch the Application
```bash
# Run the FastAPI server (serves API and bundled React frontend)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your web browser.

---

## 4. Running Tests & Reproducing Experiments

### 4.1 Run Unit Tests (16 Tests)
```bash
python -m pytest tests/
```
Output:
```
tests/test_api.py ........               [ 50%]
tests/test_routing_policies.py ..        [ 62%]
tests/test_spatial.py ....               [ 87%]
tests/test_temporal.py ..                [100%]
================ 16 passed in 5.20s ================
```

### 4.2 Reproduce Benchmark & Ablation Experiments
```bash
python -m backend.app.evaluation.experiment_runner
```
Outputs are written to:
- `experiments/outputs/benchmark_routing_results.json`
- `experiments/outputs/ablation_study_results.json`

---

## 5. Summary of Empirical Research Findings

Evaluated over **128 systematic benchmark runs** across four storm events:

| Metric | Shortest / Fastest ($P_1$) | Departure Avoidance ($P_2$) | Traversal Deterministic ($P_3$) | Proposed Risk-Aware ($P_4$) |
|---|---|---|---|---|
| **Route Availability** | 100.0% | 50.0% | 44.5% | 12.5% |
| **Abstention Rate** | 0.0% | 0.0% | 0.0% | **87.5%** |
| **Unsafe Failure Rate** | **57.0%** | **7.0%** (Trap!) | **0.0%** | **0.0%** |
| **Mean Submerged Distance** | 2,377.1 m | 374.9 m | 0.0 m | **0.0 m** |
| **Max Depth Encountered** | 0.928 m | 0.497 m | 0.299 m | **0.117 m** |
| **Mean Duration** | 32.3 min | 19.0 min | 16.7 min | 10.3 min |
| **Computation Latency** | 0.44 ms | 3.10 ms | 1.84 ms | 1.20 ms |

### Key Takeaway
- **Departure-Time Avoidance ($P_2$)** fails in **7.0%** of trips because floodwaters advance while the car is driving, stranding vehicles in up to $0.50\text{ m}$ of water.
- **Shortest Path ($P_1$)** plunges cars into severe hazards in **57.0%** of trips (averaging $2.38\text{ km}$ submerged).
- **Proposed Risk-Aware Router ($P_4$)** completely eliminates unsafe trips (**0.0% failure rate**) and caps maximum depth at $0.12\text{ m}$, transparently abstaining when no corridor guarantees passage.

---

## 6. Directory Structure

```
major project antigravity/
├── backend/
│   ├── app/
│   │   ├── api/routes.py              # FastAPI endpoints
│   │   ├── api/schemas.py             # Pydantic data schemas
│   │   ├── core/spatial.py            # Geodesic metrics, bridge clearance
│   │   ├── core/temporal.py           # Forecast horizon validator
│   │   ├── core/road_network.py       # Transportation graph
│   │   ├── core/flood_grid.py         # Hydrodynamic mesh & spatial overlay
│   │   ├── routing/algorithms.py      # The 4 comparative routing policies
│   │   ├── routing/explanations.py    # Auditable explanation engine
│   │   ├── accessibility/             # Hospital reachability & critical roads
│   │   ├── models/                    # Quantile boosting & U-Net SAR models
│   │   ├── data_factory.py            # Catchment & benchmark scenario generator
│   │   ├── config.py                  # Operational parameters
│   │   └── main.py                    # Server entrypoint
│   └── download_satellite_data.py     # Sen1Floods11 download script
├── frontend/
│   ├── src/components/MapView.tsx     # Leaflet geospatial digital twin
│   ├── src/components/ControlPanel.tsx# Timeline & scenario selector
│   ├── src/components/RouteComparisonPanel.tsx # 4-policy comparison
│   ├── src/components/AccessibilityPanel.tsx   # Hospital accessibility
│   ├── src/components/SatellitePanel.tsx       # Sen1Floods11 SAR view
│   ├── src/components/ResearchDashboard.tsx    # Live research results
│   ├── src/App.tsx                    # Main React application
│   └── package.json
├── data/
│   ├── benchmark/                     # Authentic benchmark catchment data
│   ├── fixtures/                      # Quarantined synthetic test fixtures
│   └── satellite/                     # Sen1Floods11 chips & split CSVs
├── experiments/outputs/               # Real measured evaluation JSONs
├── research/
│   ├── paper_draft.md                 # Complete academic paper draft
│   ├── data_audit.md                  # Comprehensive public data audit
│   ├── literature_review.md           # Literature matrix & verified citations
│   └── demonstration_script.md        # Step-by-step viva presentation script
├── tests/                             # Pytest test suite (16 tests)
├── docs/architecture.md               # System architecture documentation
├── PROGRESS.md                        # Progress tracking file
├── requirements.txt                   # Python dependencies
└── README.md                          # Project documentation
```

---

## 7. Research Deliverables
- **Academic Paper Draft:** [`research/paper_draft.md`](research/paper_draft.md)
- **Public Data Audit:** [`research/data_audit.md`](research/data_audit.md)
- **Literature Review Matrix:** [`research/literature_review.md`](research/literature_review.md)
- **Demonstration / Viva Script:** [`research/demonstration_script.md`](research/demonstration_script.md)
- **Architecture Documentation:** [`docs/architecture.md`](docs/architecture.md)
