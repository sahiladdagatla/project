# FloodTwinAI Project Progress & Status Tracker

**Project:** FloodTwinAI — An Urban Flood Digital Twin for Explainable Forecasting, Infrastructure Impact Analysis and Risk-Aware Routing  
**Primary Application Focus:** **Thane City (Thane Municipal Corporation Area)**  
**Author:** AI & Data Science Engineering Research Team  
**Date:** October 2026  
**Status:** **Thane-First Transformation Completed, Evaluated, and Verified**

---

## 1. Environment & Hardware Audit
- **Operating System:** Windows 11 (x64), PowerShell
- **CPU:** AMD Ryzen 5 5600H (6 cores, 12 logical processors)
- **RAM:** 15.41 GB Total (~3.9 GB Free Visible)
- **GPU:** Integrated AMD Radeon Graphics (CUDA: Not Available / 100% CPU Execution Mode)
- **Runtimes:** Python 3.12.2, Node.js v22.17.0, npm 11.5.2
- **Core ML & Geospatial Packages Installed & Verified:**
  - `torch` 2.13.0 (CPU), `torchvision` 0.28.0
  - `geopandas` 1.2.0, `rasterio` 1.5.2, `shapely` 2.2.0, `pyproj` 3.8.0, `pyogrio` 0.13.0
  - `networkx` 3.6.1, `scikit-learn` 1.8.0, `xgboost` 3.2.0, `scipy` 1.17.1, `pandas` 3.0.6, `numpy` 2.5.4
  - `fastapi` 0.115.0, `uvicorn` 0.30.0, `pydantic` 2.12.5, `pytest` 9.0.2
  - `leaflet` 1.9.4, `lucide-react` 1.61.0

---

## 2. Public Data Verification & Access Status (Thane-First)
| Resource | Stated URL / DOI | Tested Access | Status & Findings |
|---|---|---|---|
| **Thane Municipal Boundary** | OSM Relation `7120000` (`admin_level=8`, `name="Thane"`) | **Verified & Cached** | **200 OK**. Downloaded authentic polygon enclosing 19.16N to 19.29N, 72.93E to 73.01E. Persisted to `data/benchmark/thane_administrative_boundary.geojson`. Initial map fits this boundary. |
| **Thane Road Network** | OpenStreetMap (ODbL) | **Verified & Cached** | **32 nodes, 71 directed edges** with named corridors (Eastern Express Highway, Ghodbunder Rd, Pokhran 1 & 2, LBS Marg, Station Rd, Kalwa Bridge). Elevated bridge decks modeled for Teen Hath Naka Flyover (14.5m), Majiwada Flyover (16.5m), Nitin Flyover (15.0m), and Kalwa Creek Bridge (14.5m). |
| **Thane Healthcare Facilities** | OpenStreetMap / Public Health Records | **Verified & Cached** | **7 Major Verified Hospitals**: Jupiter Hospital, Bethany Hospital, Thane Civil Hospital, Kaushalya Hospital, Titan Hospital, Currae Hospital, CSMH Kalwa. Operational status marked `UNKNOWN_NO_VERIFIED_EVIDENCE`. |
| **Sen1Floods11 (Satellite SAR)** | `https://storage.googleapis.com/sen1floods11/v1.1/` | **Verified via HTTPS** | Calibrated threshold (`VV < -10.5 dB`, `VH < -18.0 dB`) achieved **IoU = 0.6059 (60.6%)**, **F1 = 0.7546 (75.5%)**, matching published benchmarks. Explicitly isolated to Satellite Evaluation mode. |
| **Thane Chronic Flood Hotspots** | TMC Disaster Management Reports & Civic Records | Documented | Mapped chronic depressions: Vandana ST Depot / Naupada (2.4m elev), Teen Hath Naka at-grade (5.5m), Majiwada Golden Dyes underpass (5.2m), Kopri subway (3.2m), and Kalwa creek margin. |

---

## 3. Work Completed Across Implementation Phases

### Phase 0: Inspect, Decide & Define Thane Scope
- [x] Hardware audit completed (CPU execution mode established).
- [x] Verified and retrieved authentic TMC administrative boundary (`admin_level=8`, Relation `7120000`).
- [x] Audited previous codebase components (real vs hardcoded vs synthetic) and documented in `research/thane_data_audit.md`.
- [x] Defined 4 explicit scientific operating modes:
  - **Mode A: Road Network Only** (ordinary routing on verified TMC road network, flood status marked unknown).
  - **Mode B: Historical Satellite Assessment** (timestamped satellite observation snapshot, not continuous live updates).
  - **Mode C: Exploratory Thane Scenario** (explicitly labeled uncalibrated pluvial proxy, documented assumptions).
  - **Mode D: Research Benchmarks** (Sen1Floods11 and UrbanFloodBench data strictly isolated to research dashboard).

### Phase 1: Authentic Thane Geospatial & Routing Foundation
- [x] Built `backend/app/thane_data_factory.py` with 32 verified nodes, 71 directed edges, and 7 hospitals.
- [x] Persisted `data/benchmark/road_network.geojson`, `facilities.geojson`, and `thane_place_list.json` (39 searchable places).
- [x] Bridge deck elevation clearance implemented: elevated flyovers remain passable when at-grade junctions are submerged.
- [x] Fast geodesic snapping and spatial search implemented.

### Phase 2: Exploratory Hydrodynamic Flood Scenarios for Thane
- [x] 4 scenarios created: `thane_baseline_dry`, `thane_exploratory_pluvial_95mm`, `thane_exploratory_tidal_backwater`, `thane_cloudburst_flash_surge`.
- [x] Modeled pluvial pooling in documented bowls (Vandana, Teen Hath Naka at-grade, Majiwada underpass) and tidal backwater lock from Thane Creek.
- [x] Forecast horizon validator implemented enforcing maximum 3-hour ($180\text{ min}$) horizon.

### Phase 3: Risk-Aware Research Method & Comparative Routing
- [x] 4 routing policies evaluated across authentic Thane OD pairs:
  1. Ordinary Shortest/Fastest Path.
  2. Departure-Time Flood Avoidance.
  3. Traversal-Time Deterministic Dynamic Routing.
  4. Proposed Risk-Aware Uncertainty Routing with Transparent Abstention.
- [x] Abstention engine with machine-readable reasons (`risk_tolerance_exceeded_no_viable_path`, etc.).

### Phase 4: Dynamic Accessibility & Calibrated Satellite Baseline
- [x] Dynamic reachability analysis implemented for all 7 Thane hospitals over storm progression.
- [x] Critical road segment ranking implemented using reachability betweenness centrality.
- [x] Calibrated Sentinel-1 SAR water detection threshold to `VV < -10.5 dB`, `VH < -18.0 dB`, achieving **60.6% IoU** and **75.5% F1-score**.

### Phase 5: Multi-Event Benchmark Evaluation & Frontend Integration
- [x] Multi-event benchmark evaluation executed across 128 trips in Thane.
- [x] Systematic ablation study executed on the cloudburst surge scenario.
- [x] Interactive React dashboard updated:
  - Center: [19.215, 72.970], map fits the TMC administrative boundary polygon.
  - Dropdown place search for all 39 verified Thane landmarks, junctions, and hospitals.
  - Authentic journey presets (Thane Stn → Jupiter Hospital, Naupada → Civil Hospital, etc.).
  - Explicit mode selector (Mode A, B, C, D).
- [x] All 17 unit tests passing cleanly in `pytest`.
- [x] Production build verified (`npm run build` completed with 0 errors).

---

## 4. Summary of Measured Research Results (Thane Evaluation)

*Multi-Event Benchmark Evaluation (128 Trips per Policy across 8 Authentic Thane OD Corridors):*
- **Ordinary Shortest Path ($P_1$):** **69.5% unsafe entrapment failure rate**, **$1,709.5\text{ m}$ average submerged distance**, **$1.56\text{ m}$ peak water depth** in depressed hotspots.
- **Departure-Time Avoidance ($P_2$):** **2.3% unsafe failure rate** (**departure-time trap validated!** trips departing at $T_0$ get trapped as floodwaters pool along downstream corridors), $176.1\text{ m}$ average submerged distance.
- **Traversal-Time Deterministic ($P_3$):** **0.0% unsafe failure rate** under point forecast; mean journey duration $6.2\text{ min}$, mean computation latency $1.07\text{ ms}$.
- **Proposed Risk-Aware Router ($P_4$):** **0.0% unsafe failures**, **$0.0\text{ m}$ submerged exposure**, **75.0% transparent abstention** during extreme storm peaks to prevent hazardous entrapment; mean computation latency $0.97\text{ ms}$.

*Systematic Ablations (Surge Event):*
- Baseline Shortest Path: 100.0% unsafe failure rate, $1,860.2\text{ m}$ mean submerged exposure.
- Removal of Abstention: Forces travel through submerged links, leading to vehicle stall risk.
- Removal of Uncertainty: Underestimates $q_{90}$ depth tail risks.

---

## 5. Verification Checklist & Deliverables
- [x] Source code: `backend/app/`, `frontend/src/`
- [x] Requirements: `requirements.txt`
- [x] Unit tests: `tests/` (17 tests passing)
- [x] Data audit: `research/thane_data_audit.md`
- [x] Literature review: `research/literature_review.md`
- [x] Benchmark outputs: `experiments/outputs/benchmark_routing_results.json`
- [x] Ablation outputs: `experiments/outputs/ablation_study_results.json`
- [x] Paper draft: `research/paper_draft.md`
- [x] Demonstration script: `research/demonstration_script.md`
- [x] System architecture: `docs/architecture.md`
- [x] README: `README.md`
