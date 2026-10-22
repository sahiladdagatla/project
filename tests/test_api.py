from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_status_endpoint():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "FloodTwinAI" in data["project_name"]
    assert data["num_road_nodes"] > 10
    assert data["num_facilities"] >= 4


def test_scenarios_endpoint():
    resp = client.get("/api/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4
    scenario_ids = [s["scenario_id"] for s in data]
    assert "thane_exploratory_pluvial_95mm" in scenario_ids
    assert "thane_cloudburst_flash_surge" in scenario_ids


def test_network_and_facilities_geojson():
    resp_net = client.get("/api/network/geojson")
    assert resp_net.status_code == 200
    net_data = resp_net.json()
    assert net_data["type"] == "FeatureCollection"
    assert len(net_data["features"]) > 20

    resp_fac = client.get("/api/facilities/geojson")
    assert resp_fac.status_code == 200
    fac_data = resp_fac.json()
    assert fac_data["type"] == "FeatureCollection"
    assert len(fac_data["features"]) >= 4


def test_boundary_and_places_endpoints():
    resp_bnd = client.get("/api/boundary/geojson")
    assert resp_bnd.status_code == 200
    bnd_data = resp_bnd.json()
    assert bnd_data["type"] in ["FeatureCollection", "Feature", "Polygon", "MultiPolygon"]

    resp_plc = client.get("/api/places")
    assert resp_plc.status_code == 200
    plc_data = resp_plc.json()
    assert len(plc_data) >= 20


def test_flood_layer_endpoint():
    resp = client.get("/api/flood-layer?scenario_id=thane_exploratory_pluvial_95mm&timestep_idx=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    assert "water_depth_m" in data["features"][0]["properties"]


def test_route_compare_endpoint():
    payload = {
        "scenario_id": "thane_exploratory_pluvial_95mm",
        "origin_lat": 19.1846,
        "origin_lon": 72.9710,
        "dest_lat": 19.2046,
        "dest_lon": 72.9688,
        "timestep_idx": 2
    }
    resp = client.post("/api/route/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "policies" in data
    assert "shortest_fastest" in data["policies"]
    assert "proposed_risk_aware" in data["policies"]
    assert "comparison_summary" in data


def test_critical_roads_endpoint():
    resp = client.get("/api/accessibility/critical-roads")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["critical_segments"]) > 0
    assert "criticality_score" in data["critical_segments"][0]


def test_satellite_endpoints():
    resp_chips = client.get("/api/satellite/chips")
    assert resp_chips.status_code == 200
    chips = resp_chips.json()
    assert len(chips) > 0

    chip_id = chips[0]["chip_id"]
    resp_seg = client.get(f"/api/satellite/segment?chip_id={chip_id}")
    assert resp_seg.status_code == 200
    seg_data = resp_seg.json()
    assert "metrics" in seg_data
    assert "flood_iou" in seg_data["metrics"]


def test_experiment_results_endpoint():
    resp = client.get("/api/experiments/results")
    assert resp.status_code == 200
    data = resp.json()
    assert "benchmark" in data
    assert "ablations" in data
