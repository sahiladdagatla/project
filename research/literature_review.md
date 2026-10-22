# FloodTwinAI: Academic Literature Review & Theoretical Foundation

**Project:** FloodTwinAI: An Urban Flood Digital Twin for Explainable Forecasting, Infrastructure Impact Analysis and Risk-Aware Routing  
**Field:** AI & Data Science / Urban Hydrological Modeling / Intelligent Transportation Systems  
**Date:** October 2026  

---

## 1. Primary Research Question & Candidate Contribution

### Primary Research Question
> *"Does uncertainty-aware, arrival-time-based routing reduce exposure to inundated roads while preserving useful accessibility compared with shortest-path and deterministic flood-aware routing?"*

### Candidate Contribution
Existing urban flood navigation systems predominantly exhibit two major deficiencies:
1. **Departure-Time Static Assumption:** Most flood-aware routing algorithms query flood extents solely at the vehicle's departure time $t_{dep}$ and compute a static path, implicitly assuming the flood state remains frozen throughout the journey. In dynamic pluvial or fluvial events where inundation spreads rapidly, this assumption leads to severe vehicle entrapment on roads that become submerged during traversal.
2. **Deterministic Overconfidence:** Existing surrogate models predict point estimates of water depth without quantifying predictive uncertainty. A router relying on deterministic point forecasts risks directing vehicles onto hazardous corridors when small errors push actual depths above vehicle stalling thresholds. Furthermore, existing systems lack transparent abstention policies, frequently outputting misleading or hazardous trajectories when forecast confidence is critically degraded.

**The Proposed Contribution:**
FloodTwinAI introduces a risk-aware, time-dependent routing framework that:
- Evaluates road segment inundation dynamically at the vehicle's estimated arrival time $\tau(e)$ rather than departure time $t_{dep}$.
- Couples predictive flood surrogate models with quantile uncertainty estimation ($q_{50}, q_{90}$) and calibrated risk exceedance probabilities $P(d_e(\tau) > \theta_{crit})$.
- Applies conservative exclusions and explicit, transparent abstention rules: when all candidate paths exceed acceptable risk bounds or travel time extends beyond the reliable forecast horizon, the system explicitly declines to recommend a route and provides an auditable explanation.
- Formulates and evaluates the multi-objective Pareto trade-off between flood exposure duration, additional travel time (detour), accessibility preservation, and unnecessary refusals.

---

## 2. Literature Review Matrix

| Paper & Authors | Core Focus & Methodology | Operating Setting | Handling of Traversal Timing | Handling of Uncertainty | Key Limitations Addressed by FloodTwinAI |
|---|---|---|---|---|---|
| **Shafiee Roudbari et al. (2024)**  <br>*Scientific Reports* [1] | GNN-based flood forecasting (*LocalFloodNet*) coupled with interactive Digital Twin visualization | Greater Montreal Area, Canada | Static forecast snapshots | Deterministic point forecasts | Visualizes flood evolution on digital twins but does not integrate dynamic road routing or risk-aware vehicle routing. |
| **Yuan, Xu, Li, & Mostafavi (2022)**  <br>*Computers, Env. & Urban Systems* [2] | Spatio-Temporal GCN (STGCN) with elevation blocks predicting microscopic road inundation from traffic speeds | Hurricane Harvey, Harris County, TX | Static road status prediction | Deterministic classification (flooded / non-flooded) | Uses traffic slowdown as a flood proxy; does not perform forward multi-step time-dependent routing under forecast uncertainty. |
| **Ghosh, Shastri, Ghosh, & Karmakar (2023)**  <br>*J. Geophys. Res. Atmos.* [3] | Response Priority Framework linking global weather forecasts to coastal hydrodynamic models | Mithi River Catchment, Mumbai, India | Static sub-catchment priority tiers | Multi-model downscaled ensemble | Focuses on institutional macro-level asset deployment priorities; does not support dynamic individual vehicle routing. |
| **Lim, Herath, Acosta, et al. (2026)**  <br>*Env. Modelling & Software* [4] | *UrbanFloodBench*: Standardized benchmark for coupled 1D–2D urban flood surrogate models | Multi-catchment hydrodynamic simulations (HEC-RAS) | Node/cell water level time-series | Variance-aware evaluation metrics (NRMSE) | Benchmarks surrogate modeling accuracy at grid nodes; does not extend predictions to transportation graphs or routing decisions. |
| **Bonafilia, Tellman, et al. (2020)**  <br>*IEEE/CVF CVPRW* [5] | *Sen1Floods11*: Georeferenced Sentinel-1 SAR dataset and deep learning flood segmentation | 11 global flood disaster events | Single-timestamp satellite overpasses | Softmax class probabilities | Satellite imagery is fundamentally periodic (discrete snapshots); cannot provide continuous time-dependent forward routing. |
| **Pyatkova et al. (2019) / Kermanshah & Derrible (2017)** [6, 7] | Flood impact on urban road networks and accessibility disruption | London, UK / New York, USA | Static flood depth overlay | Deterministic scenario depths | Evaluates static network vulnerability; does not incorporate probabilistic forecast uncertainty or dynamic arrival-time routing. |
| **FloodTwinAI (This Work)** | **Integrated Digital Twin:** Quantile flood forecasting + Time-expanded risk-aware routing + Auditable abstention + Accessibility analysis | Benchmark urban catchments & Satellite SAR | **Dynamic traversal-time evaluation $\tau(e)$** | **Quantile estimation ($q_{50}, q_{90}$), calibrated exceedance risk** | **Solves both entrapment and overconfidence through time-dependent uncertainty routing with transparent abstention.** |

---

## 3. Verified Bibliographic References

1. **Shafiee Roudbari, N., Punekar, S. R., Patterson, Z., Eicker, U., & Poullis, C.** (2024). *From data to action in flood forecasting leveraging graph neural networks and digital twin visualization.* Scientific Reports, 14(1), 18452. DOI: [10.1038/s41598-024-69022-7](https://doi.org/10.1038/s41598-024-69022-7).
2. **Yuan, F., Xu, Y., Li, Q., & Mostafavi, A.** (2022). *Spatio-Temporal Graph Convolutional Networks for Road Network Inundation Status Prediction during Urban Flooding.* Computers, Environment and Urban Systems, 97, 101859. DOI: [10.1016/j.compenvurbsys.2022.101859](https://doi.org/10.1016/j.compenvurbsys.2022.101859).
3. **Ghosh, M., Shastri, H., Ghosh, S., & Karmakar, S.** (2023). *A Novel Response Priority Framework for an Urban Coastal Catchment Using Global Weather Forecasts-Based Improved Flood Risk Estimates.* Journal of Geophysical Research: Atmospheres, 128(18), e2023JD038876. DOI: [10.1029/2023JD038876](https://doi.org/10.1029/2023JD038876).
4. **Lim, J. Y., Herath, V., Acosta, C. M., Rasnayaka, S., Saha, A., & Marshall, L.** (2026). *UrbanFloodBench: Bridging AI and hydrology through benchmarking of coupled 1D–2D urban flood surrogate models.* Environmental Modelling & Software, 107154. DOI: [10.1016/j.envsoft.2026.107154](https://doi.org/10.1016/j.envsoft.2026.107154).
5. **Bonafilia, D., Tellman, B., Anderson, T., & Issenberg, E.** (2020). *Sen1Floods11: a georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1.* IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW 2020), 210–211. DOI: [10.1109/CVPRW50498.2020.00111](https://doi.org/10.1109/CVPRW50498.2020.00111).
6. **Pyatkova, K., Chen, A. S., Butler, D., Vojinović, Z., & Djordjević, S.** (2019). *Assessing the impact of flood duration on transport network vulnerability.* Urban Water Journal, 16(8), 600–611.
7. **Kermanshah, A., & Derrible, S.** (2017). *Geographical and machine learning resilience analysis of road networks to extreme flooding events.* Computer-Aided Civil and Infrastructure Engineering, 32(11), 936–949.
8. **Acosta, C. M., Herath, V., Lim, J. Y., Saha, A., Rasnayaka, S., & Marshall, L.** (2026). *DUALFloodGNN: Physics-informed Graph Neural Networks for Operational Flood Modeling.* IJCAI-ECAI 2026. arXiv:2512.23964.
9. **Boeing, G.** (2017). *OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks.* Computers, Environment and Urban Systems, 65, 126–139.
