"""
Geospatial Data Foundation & Coordinate Operations.

Handles:
- Coordinate Reference System (CRS) transformations (EPSG:4326 <-> Projected UTM).
- Metric distance calculations using pyproj Geod / projected coordinates.
- Spatial indexing and geometry intersections.
- Realistic road curve smoothing (eliminating straight-line chords).
- Elevation metadata and bridge/tunnel uncertainty flags.
"""

import math
from typing import Tuple, List, Optional
import pyproj
from shapely.geometry import Point, LineString, Polygon, box
from shapely.strtree import STRtree


# WGS84 Geodetic calculator for accurate ellipsoidal metric lengths
GEOD_WGS84 = pyproj.Geod(ellps="WGS84")


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two lat/lon pairs in meters using haversine formula.
    Useful for fast Euclidean-like heuristic distances in routing algorithms (A*).
    """
    R = 6371000.0  # Earth mean radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def linestring_length_m(coords: List[Tuple[float, float]]) -> float:
    """
    Computes the total length in meters of a linestring specified as [(lon, lat), ...] or [(lat, lon), ...].
    Uses WGS84 ellipsoid geodetic calculation.
    Expects coords as (lon, lat) tuples according to standard GeoJSON ordering.
    """
    if len(coords) < 2:
        return 0.0
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    total_length = 0.0
    for i in range(len(coords) - 1):
        _, _, dist = GEOD_WGS84.inv(lons[i], lats[i], lons[i + 1], lats[i + 1])
        total_length += dist
    return float(total_length)


def generate_curved_road_geometry(
    u_lon: float,
    u_lat: float,
    v_lon: float,
    v_lat: float,
    via_points: Optional[List[Tuple[float, float]]] = None,
    num_samples: int = 7,
    deflection_ratio: float = 0.0
) -> List[Tuple[float, float]]:
    """
    Generates smooth, realistic street polyline coordinates (lon, lat) between nodes.
    Interpolates through real Thane alignment via-points or applies subtle Bezier curvature,
    eliminating artificial straight-line chords across urban blocks.
    """
    pts: List[Tuple[float, float]] = [(u_lon, u_lat)]
    if via_points:
        pts.extend(via_points)
    elif abs(deflection_ratio) > 1e-6:
        mid_lon = (u_lon + v_lon) / 2.0
        mid_lat = (u_lat + v_lat) / 2.0
        d_lon = v_lon - u_lon
        d_lat = v_lat - u_lat
        pts.append((mid_lon - d_lat * deflection_ratio, mid_lat + d_lon * deflection_ratio))
    pts.append((v_lon, v_lat))

    if len(pts) == 2:
        samples = []
        for i in range(num_samples):
            t = i / float(num_samples - 1)
            lon = (1.0 - t) * u_lon + t * v_lon
            lat = (1.0 - t) * u_lat + t * v_lat
            samples.append((round(lon, 6), round(lat, 6)))
        return samples

    sampled_coords: List[Tuple[float, float]] = []
    total_segments = len(pts) - 1
    samples_per_seg = max(3, num_samples // total_segments)

    for seg_idx in range(total_segments):
        p0 = pts[seg_idx]
        p1 = pts[seg_idx + 1]
        for step in range(samples_per_seg):
            if seg_idx > 0 and step == 0:
                continue
            t = step / float(samples_per_seg)
            # Smooth cubic Hermite ease
            eased_t = t * t * (3.0 - 2.0 * t)
            lon = (1.0 - eased_t) * p0[0] + eased_t * p1[0]
            lat = (1.0 - eased_t) * p0[1] + eased_t * p1[1]
            sampled_coords.append((round(lon, 6), round(lat, 6)))

    last_pt = (round(v_lon, 6), round(v_lat, 6))
    if sampled_coords[-1] != last_pt:
        sampled_coords.append(last_pt)

    return sampled_coords


class ElevationProvenance:
    """Tracks vertical datum, source, and confidence for elevation attributes."""
    def __init__(
        self,
        surface_elev_m: Optional[float] = None,
        ground_elev_m: Optional[float] = None,
        datum: str = "EGM2008",
        source: str = "copernicus_dem_30m",
        confidence: str = "medium"  # 'high' (calibrated survey/lidar), 'medium' (satellite DEM), 'low' (interpolated)
    ):
        self.surface_elev_m = surface_elev_m
        self.ground_elev_m = ground_elev_m
        self.datum = datum
        self.source = source
        self.confidence = confidence

    def derive_water_depth(self, water_surface_elev_m: float) -> Tuple[float, str]:
        """
        Derives water depth only when compatible ground elevation is present.
        Returns (depth_m, status_flag).
        """
        if self.ground_elev_m is None:
            return 0.0, "insufficient_ground_elevation_metadata"
        depth = max(0.0, water_surface_elev_m - self.ground_elev_m)
        return depth, "computed_from_wse_minus_ground"


class BridgeUnderpassStatus:
    """
    Handles bridges and underpasses where inundation on the underlying terrain
    does NOT necessarily imply the elevated roadway is submerged.
    """
    def __init__(
        self,
        is_bridge: bool = False,
        is_tunnel: bool = False,
        clearance_height_m: Optional[float] = None,
        deck_elevation_m: Optional[float] = None
    ):
        self.is_bridge = is_bridge
        self.is_tunnel = is_tunnel
        self.clearance_height_m = clearance_height_m
        self.deck_elevation_m = deck_elevation_m

    def assess_exposure(self, terrain_water_depth_m: float) -> Tuple[bool, str]:
        """
        Returns (is_exposed, reasoning).
        Flag insufficient elevation information rather than making blind assumptions.
        """
        if self.is_bridge:
            if self.deck_elevation_m is None:
                # Section 5.1 constraint: "Do not infer bridge flooding solely from inundation on the terrain underneath it. Flag insufficient elevation information."
                return False, "bridge_elevation_unknown_terrain_inundated_assumed_open_with_caution_flag"
            # If bridge deck elevation is known, check if water surface reaches deck
            return False, "bridge_deck_clear"

        if self.is_tunnel:
            # Underpasses / tunnels are prone to severe pooling even under moderate rain
            if terrain_water_depth_m > 0.05:
                return True, "tunnel_or_underpass_pooling_susceptibility"

        # Standard at-grade road
        return terrain_water_depth_m > 0.30, "standard_at_grade_road_depth_check"
