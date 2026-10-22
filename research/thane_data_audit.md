# FloodTwinAI: Comprehensive Thane Data & Hydrological Audit

**Project:** FloodTwinAI: An Urban Flood Digital Twin for Explainable Forecasting, Infrastructure Impact Analysis and Risk-Aware Routing  
**Target Geography:** Thane City, Thane Municipal Corporation (TMC) Area, Maharashtra, India  
**Date:** October 2026  
**Auditor Status:** Comprehensive Public Resource & Hydrological Audit Completed  

---

## 1. Audit of Previous Implementation

Before implementing the Thane-first platform, an audit of the previous codebase was conducted to distinguish real data, model outputs, hardcoded values, and synthetic development fixtures:

| Component | Previous Implementation | Classification | Action in Thane-First System |
|---|---|---|---|
| **Study Area Geography** | Artificial 21-node graph placed at Mumbai coordinates `(19.02-19.08N, 72.83-72.90E)` | **Hardcoded / Generic Fixture** | **Replaced.** Shifted completely to Thane City within TMC boundaries `(19.16N-19.28N, 72.93E-73.01E)` with verified coordinates. |
| **Node Naming** | Generic identifiers (`N01`, `N10`, `N13`) | **Generic Mock Labels** | **Replaced.** Human-readable Thane landmarks and junctions (`Thane_Station`, `Teen_Hath_Naka`, `Majiwada_Jct`, `Vartak_Nagar`, `Manpada`, etc.). |
| **Flood Grid** | Regular 50-cell grid (`C001-C050`) with synthetic elevations | **Synthetic Development Fixture** | **Replaced.** Real physical topography (Yeoor Hills ridge, central drainage basin, Thane Creek tidal mudflats) with documented chronic waterlogging zones. |
| **Scenario Labels** | "50-Year Severe Design Storm (95mm)" claiming canal breach at T+30m | **Unsupported Claim** | **Corrected.** Relabeled transparently as *"Exploratory pluvial scenario: 95mm over 3 hours (uncalibrated hydrodynamic proxy)"*. Unsupported breach claims removed. |
| **Satellite Module** | Ghana chip from Sen1Floods11 (`Ghana_319168`) overlaid in panel | **Geographically Disconnected** | **Separated.** Quarantined to dedicated Research Benchmark Mode. Thane map displays only real Thane layers. |
| **Routing Engine** | Time-dependent dynamic Dijkstra, quantile pruning, abstention logic | **Real Algorithmic Logic** | **Preserved & Adapted.** Re-keyed to the authentic Thane road network and flyover hierarchy. |
| **Quantile Model** | Scikit-learn HistGradientBoostingRegressor ($q_{10}, q_{50}, q_{90}$) | **Real Machine Learning Model** | **Preserved.** Operates on physical catchment features and antecedent rainfall. |
| **Accessibility & Centrality** | NetworkX betweenness centrality and shortest-path reachability | **Real Graph Algorithms** | **Preserved & Applied.** Evaluated on verified Thane emergency hospitals. |

---

## 2. Geographical Scope Definition: Thane Municipal Corporation (TMC)

- **Administrative Boundary:** OpenStreetMap Administrative Boundary Relation **`ID: 7120000`** (`admin_level=8`, `boundary=administrative`, `name="Thane"`).
- **Bounding Box (TMC & Buffer):**
  - South: $19.1600^\circ\text{N}$ (Anand Nagar / Mulund Check Naka entrance from Mumbai)
  - North: $19.2850^\circ\text{N}$ (Ovala / Gaimukh / Ghodbunder Creek threshold)
  - West: $72.9300^\circ\text{E}$ (Yeoor Hills / Sanjay Gandhi National Park boundary)
  - East: $73.0100^\circ\text{E}$ (Kalwa / Thane Creek / Vitawa)
- **Map Center:** $19.2150^\circ\text{N}, 72.9700^\circ\text{E}$ (Majiwada - Vartak Nagar central hub).

---

## 3. Thane Public Data Inventory

| Dataset / Feature | Source URL / Authority | Access / License | Resolution / Coverage | Status | Role in FloodTwinAI | Limitations |
|---|---|---|---|---|---|---|
| **TMC Boundary** | OSM Relation 7120000 / Nominatim | Open Database License (ODbL) | Vector Polygon, TMC administrative boundary | **Verified & Cached** | Defines study boundary and clip extent | General administrative polygon; ward-level shapefiles require municipal FOI. |
| **Road Network** | OpenStreetMap (`highway=*`) | ODbL 1.0 | Vector LineStrings with names, functional class, bridges | **Verified & Packaged** | Directed routing graph with flyover deck heights | Variable speed-limit tags; default speed rules applied based on highway class. |
| **Emergency Hospitals** | OpenStreetMap / Nominatim | ODbL 1.0 | Point coordinates of 7 verified Thane hospitals | **Verified & Cached** | Target destinations for emergency accessibility | Operational status unknown without verified real-time municipal health feeds. |
| **Topography (DEM)** | Copernicus DEM GLO-30 | Open Copernicus OpenTopography | 30m grid, vertical units: meters | **Verified Public Data** | Captures Yeoor Hills (350m) to Creek flats (2m) | Surface model (DSM); canopy/buildings elevate apparent heights over street curbs. |
| **Water Bodies & Lakes** | OSM (`natural=water`, `water=lake`) | ODbL 1.0 | Masunda Lake, Upvan Lake, Thane Creek | **Verified Public Data** | Visual water features & hydrological boundaries | Lake bathymetry and overflow weir discharge capacities are unmapped in open data. |
| **Historical Inundation Hotspots** | TMC Disaster Management Plan / Civic News Archives | Public domain reporting | Point locations of recurring chronic waterlogging | **Verified Empirical Evidence** | Calibrates exploratory scenario waterlogging centroids | General locations only; does not provide timestamped sensor telemetry. |
| **Subterranean Storm Drains** | Municipal Drainage Department | Restricted / Internal municipal records | Pipe diameters, invert levels, invert slopes | **UNAVAILABLE** | Noted in limitations | Underground pipe flow cannot be physically simulated without closed records. |
| **Tidal Gauge Data** | Mumbai Port Trust / Survey of India (Apollo Bunder / Thane Creek) | Public tide tables | Semi-diurnal tidal heights (0.5m to 4.5m) | **Derived Parameter** | Boundary condition for creek outfall stagnation | Dynamic creek wave modeling requires coupled estuarine hydrodynamic model. |
| **Sentinel-1 SAR Imagery** | ESA Copernicus Open Access Hub / Google Earth Engine | Free & Open Public Access | 10m GRD, C-band SAR (VV, VH) | **Verified Public Data** | Satellite Observation Mode | Periodic satellite passes (revisit 6-12 days); no continuous live monitoring. |

---

## 4. Hydrological Data Audit & Physics of Flooding in Thane

Flooding in Thane City is governed by three coupled physical mechanisms:

1. **Topographic Funneling from Yeoor Hills:**
   - The western margin of Thane is bounded by the steep Yeoor Hills (part of Sanjay Gandhi National Park), rising from $15\text{ m}$ to over $350\text{ m}$ within $2\text{ km}$.
   - Heavy monsoon downpours generate rapid overland runoff with minimal infiltration on steep rocky slopes, cascading directly into low-lying urban plains (Vartak Nagar, Pokhran Road, Upvan, and Ghodbunder Road).
2. **Low-Lying Depression Bottlenecks:**
   - **Vandana Talkies / ST Depot (Naupada):** Natural topographic bowl (elevation $\sim 2.5\text{ m}$) where runoff accumulates from Naupada and Panchpakhadi.
   - **Teen Hath Naka & Nitin Company Grade-Level Intersections:** Sits in low depressions where service roads collect stormwater, while elevated flyovers remain open above.
   - **Majiwada Golden Dyes:** Confluence of regional drainage where highway underpasses pool water.
3. **Tidal Lock & Creek Backwater Stagnation:**
   - All major open nallas in southern and central Thane (Panchpakhadi Nalla, Rabodi Nalla, Kopri Nalla) discharge eastward into **Thane Creek**.
   - During spring high tides (water levels $> 4.0\text{ m}$ above Chart Datum), tidal backwater pushes up the nallas. When high tide coincides with intense rainfall, gravity drainage halts entirely, causing extensive pluvial flooding regardless of drain width.

### Drainage Data Completeness Gate:
- **Verified Public Data:** Topographic elevation, natural surface water bodies, and chronic hotspot locations.
- **Derived Estimates:** Overland flow accumulation, slope vectors, and tidal backwater zones.
- **Assumed Scenario Parameters:** Tidal height boundary condition and rainfall intensity.
- **Unavailable:** Underground pipe network connectivity, siltation/blockage percentages, pump capacities, and culvert invert elevations.

**Scientific Gate Conclusion:** Because subterranean pipe geometry and live pump telemetry are unavailable in public records, local flood depths in Thane are presented strictly under **Mode C: Exploratory Thane Scenario** with documented assumptions. We explicitly refrain from claiming uncalibrated physics simulation as a certified real-time local depth forecast.
