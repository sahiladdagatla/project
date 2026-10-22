import pytest
from backend.app.core.spatial import haversine_distance_m, linestring_length_m, BridgeUnderpassStatus


def test_haversine_distance():
    # Distance between Mumbai Gateway of India (18.9220, 72.8347) and CSMT (18.9400, 72.8354) ~ 2.0 km
    d = haversine_distance_m(18.9220, 72.8347, 18.9400, 72.8354)
    assert 1900 < d < 2200


def test_linestring_length():
    coords = [(72.8347, 18.9220), (72.8354, 18.9400)]
    length = linestring_length_m(coords)
    assert 1900 < length < 2200


def test_bridge_elevation_clearance():
    bridge = BridgeUnderpassStatus(is_bridge=True, deck_elevation_m=15.0)
    # Terrain flooded underneath with 1.2m water, but bridge deck is elevated
    exposed, reason = bridge.assess_exposure(terrain_water_depth_m=1.2)
    assert exposed is False
    assert "bridge_deck_clear" in reason


def test_bridge_unknown_elevation():
    bridge = BridgeUnderpassStatus(is_bridge=True, deck_elevation_m=None)
    exposed, reason = bridge.assess_exposure(terrain_water_depth_m=0.8)
    # Must flag insufficient elevation information rather than assuming flooding
    assert exposed is False
    assert "bridge_elevation_unknown" in reason
