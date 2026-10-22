import pytest
from backend.app.data_factory import generate_benchmark_catchment
from backend.app.routing.algorithms import FloodRouter
from backend.app.config import RoutingPolicyType, settings


@pytest.fixture
def benchmark_setup():
    net, scenarios, facilities = generate_benchmark_catchment()
    return net, scenarios, facilities


def test_four_policies_execution(benchmark_setup):
    net, scenarios, facilities = benchmark_setup
    sc = scenarios["event_50yr"]
    router = FloodRouter(net, sc)
    dep_time = sc.timesteps[2].isoformat()

    results = {}
    for pol in RoutingPolicyType:
        res = router.route(pol, "N01", "N10", dep_time)
        results[pol] = res
        assert res.policy == pol

    # Ordinary shortest path is available but dangerous
    p1 = results[RoutingPolicyType.SHORTEST_FASTEST]
    assert p1.route_available is True
    # In a 50-year storm, shortest path enters submerged corridors
    assert p1.total_inundated_exposure_m > 0.0 or p1.max_encountered_depth_m > 0.15

    # Proposed risk-aware router refuses unsafe exposure or abstains
    p4 = results[RoutingPolicyType.PROPOSED_RISK_AWARE]
    if p4.route_available:
        assert p4.total_inundated_exposure_m == 0.0
        assert p4.max_encountered_depth_m < settings.critical_depth_m
    else:
        assert p4.abstained is True
        assert p4.abstention_reason is not None


def test_no_path_handling(benchmark_setup):
    net, scenarios, facilities = benchmark_setup
    sc = scenarios["event_100yr"]
    router = FloodRouter(net, sc)
    # Query non-existent node
    res = router.route(RoutingPolicyType.PROPOSED_RISK_AWARE, "NON_EXISTENT", "N10", sc.timesteps[0].isoformat())
    assert res.route_available is False
    assert res.abstained is True
    assert "not_found" in res.abstention_reason
