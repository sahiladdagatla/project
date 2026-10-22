import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

interface MapViewProps {
  networkGeojson: any;
  facilitiesGeojson: any;
  floodLayerGeojson: any;
  boundaryGeojson?: any;
  places?: any[];
  policyResults: any;
  activePolicy: string;
  originNodeId: string;
  destNodeId: string;
  onSelectNode?: (nodeId: string, role: 'origin' | 'dest') => void;
}

export const MapView: React.FC<MapViewProps> = ({
  networkGeojson,
  facilitiesGeojson,
  floodLayerGeojson,
  boundaryGeojson,
  places = [],
  policyResults,
  activePolicy,
  originNodeId,
  destNodeId,
  onSelectNode
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const boundaryLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const floodLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const networkLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const facilitiesLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const routesLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const markersLayerGroupRef = useRef<L.LayerGroup | null>(null);

  // Initialize Map centered on Thane City
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [19.215, 72.970],
      zoom: 13,
      zoomControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    // Standard OpenStreetMap base tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | FloodTwinAI Thane Digital Twin',
      maxZoom: 18,
      minZoom: 10
    }).addTo(map);

    boundaryLayerGroupRef.current = L.layerGroup().addTo(map);
    floodLayerGroupRef.current = L.layerGroup().addTo(map);
    networkLayerGroupRef.current = L.layerGroup().addTo(map);
    routesLayerGroupRef.current = L.layerGroup().addTo(map);
    facilitiesLayerGroupRef.current = L.layerGroup().addTo(map);
    markersLayerGroupRef.current = L.layerGroup().addTo(map);

    mapRef.current = map;
    setTimeout(() => {
      map.invalidateSize();
    }, 250);

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Render Thane Administrative Boundary Polygon
  useEffect(() => {
    if (!mapRef.current || !boundaryLayerGroupRef.current || !boundaryGeojson) return;
    boundaryLayerGroupRef.current.clearLayers();

    const layer = L.geoJSON(boundaryGeojson, {
      style: {
        color: '#f59e0b',
        weight: 2.5,
        opacity: 0.9,
        dashArray: '6, 6',
        fillColor: '#f59e0b',
        fillOpacity: 0.04
      },
      onEachFeature: (feature, l) => {
        l.bindTooltip(
          `<div class="text-xs p-1">
            <strong>Thane Municipal Corporation (TMC)</strong><br/>
            Administrative Boundary (OSM Relation 7120000)<br/>
            <span class="text-amber-400">Study Area Scope: Thane City</span>
          </div>`,
          { sticky: true }
        );
      }
    }).addTo(boundaryLayerGroupRef.current);

    // Fit map view to study boundary
    try {
      const bounds = layer.getBounds();
      if (bounds.isValid()) {
        mapRef.current.fitBounds(bounds, { padding: [20, 20] });
      }
    } catch (e) {
      console.warn('Could not fit bounds to boundary:', e);
    }
  }, [boundaryGeojson]);

  // Update Flood Polygons
  useEffect(() => {
    if (!mapRef.current || !floodLayerGroupRef.current) return;
    floodLayerGroupRef.current.clearLayers();

    if (!floodLayerGeojson?.features) return;

    L.geoJSON(floodLayerGeojson, {
      style: (feature) => {
        const d = feature?.properties?.water_depth_m || 0;
        let fillColor = 'transparent';
        let fillOpacity = 0.0;
        let strokeColor = 'rgba(56, 189, 248, 0.15)';

        if (d >= 0.30) {
          fillColor = '#e11d48'; // Impassable / Deep Flood (Crimson)
          fillOpacity = 0.65;
          strokeColor = '#f43f5e';
        } else if (d >= 0.15) {
          fillColor = '#d97706'; // Caution depth (Amber)
          fillOpacity = 0.50;
          strokeColor = '#f59e0b';
        } else if (d > 0.02) {
          fillColor = '#0284c7'; // Shallow water (Blue)
          fillOpacity = 0.30;
          strokeColor = '#38bdf8';
        }

        return {
          fillColor,
          fillOpacity,
          color: strokeColor,
          weight: 1.0
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties;
        layer.bindTooltip(
          `<div class="text-xs p-1">
            <strong>Cell ${p.cell_id}</strong><br/>
            Depth: <b>${p.water_depth_m}m</b><br/>
            q90 Depth: <b>${p.p90_depth_m}m</b><br/>
            Status: <span class="capitalize">${p.status}</span>
          </div>`,
          { sticky: true }
        );
      }
    }).addTo(floodLayerGroupRef.current);
  }, [floodLayerGeojson]);

  // Update Road Network
  useEffect(() => {
    if (!mapRef.current || !networkLayerGroupRef.current) return;
    networkLayerGroupRef.current.clearLayers();

    if (!networkGeojson?.features) return;

    L.geoJSON(networkGeojson, {
      style: (feature) => {
        const isBridge = feature?.properties?.is_bridge;
        return {
          color: isBridge ? '#c084fc' : '#475569',
          weight: isBridge ? 4.5 : 2.5,
          opacity: isBridge ? 0.95 : 0.65,
          dashArray: isBridge ? '6, 4' : undefined
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties;
        layer.bindTooltip(
          `<div class="text-xs p-1">
            <strong>${p.highway_type.toUpperCase()} ${p.edge_id}</strong><br/>
            ${p.u} &rarr; ${p.v} | ${p.length_m}m<br/>
            Speed: ${p.speed_limit_kmh} km/h<br/>
            ${p.is_bridge ? '<b class="text-purple-400">Elevated Bridge Deck</b>' : 'At-grade roadway'}
          </div>`,
          { sticky: true }
        );
      }
    }).addTo(networkLayerGroupRef.current);
  }, [networkGeojson]);

  // Update Facilities (Hospitals)
  useEffect(() => {
    if (!mapRef.current || !facilitiesLayerGroupRef.current) return;
    facilitiesLayerGroupRef.current.clearLayers();

    if (!facilitiesGeojson?.features) return;

    facilitiesGeojson.features.forEach((feat: any) => {
      const [lon, lat] = feat.geometry.coordinates;
      const p = feat.properties;

      const icon = L.divIcon({
        className: 'custom-hosp-icon',
        html: `
          <div style="background:#dc2626; color:white; width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:14px; border:2px solid white; box-shadow:0 0 10px rgba(220,38,38,0.8);">
            +
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const marker = L.marker([lat, lon], { icon }).addTo(facilitiesLayerGroupRef.current!);
      marker.bindPopup(`
        <div style="padding:4px; font-size:12px;">
          <b style="color:#f43f5e; font-size:13px;">${p.name}</b><br/>
          Type: <i>${p.facility_type}</i><br/>
          Nearest Junction: <b>${p.nearest_node_id}</b><br/>
          Status: <span style="background:#334155; padding:2px 4px; border-radius:4px; font-size:10px;">UNKNOWN_OPERATIONAL_STATUS</span>
        </div>
      `);
    });
  }, [facilitiesGeojson]);

  // Update Routes
  useEffect(() => {
    if (!mapRef.current || !routesLayerGroupRef.current) return;
    routesLayerGroupRef.current.clearLayers();

    if (!policyResults) return;

    const policyStyles: Record<string, { color: string; weight: number; opacity: number; dash?: string }> = {
      shortest_fastest: { color: '#94a3b8', weight: 3.5, opacity: 0.85, dash: '5, 5' },
      departure_time_avoidance: { color: '#f59e0b', weight: 4.5, opacity: 0.9 },
      traversal_time_deterministic: { color: '#06b6d4', weight: 4.5, opacity: 0.9 },
      proposed_risk_aware: { color: '#10b981', weight: 5.5, opacity: 1.0 }
    };

    Object.entries(policyResults).forEach(([polKey, res]: [string, any]) => {
      if (!res?.route_available || !res?.route_geometry || res.route_geometry.length < 2) return;

      const isFocused = activePolicy === 'all' || activePolicy === polKey;
      const baseStyle = policyStyles[polKey] || { color: '#38bdf8', weight: 4, opacity: 0.8 };

      const latlngs = res.route_geometry.map((c: [number, number]) => [c[1], c[0]]);

      const polyline = L.polyline(latlngs, {
        color: baseStyle.color,
        weight: isFocused ? baseStyle.weight : 2.0,
        opacity: isFocused ? baseStyle.opacity : 0.25,
        dashArray: baseStyle.dash
      }).addTo(routesLayerGroupRef.current!);

      polyline.bindTooltip(
        `<div class="text-xs p-1">
          <strong>${res.policy_name}</strong><br/>
          Duration: <b>${(res.total_duration_s / 60).toFixed(1)}m</b><br/>
          Flooded Exp: <b>${res.total_inundated_exposure_m.toFixed(0)}m</b><br/>
          Max Depth: <b>${res.max_encountered_depth_m.toFixed(2)}m</b>
        </div>`,
        { sticky: true }
      );
    });
  }, [policyResults, activePolicy]);

  // Update Origin and Destination Markers
  useEffect(() => {
    if (!mapRef.current || !markersLayerGroupRef.current || !networkGeojson?.features) return;
    markersLayerGroupRef.current.clearLayers();

    networkGeojson.features.forEach((feat: any) => {
      const p = feat.properties;
      const uCoord = feat.geometry.coordinates[0];
      const isOrigin = p.u === originNodeId;
      const isDest = p.u === destNodeId;

      if (isOrigin || isDest) {
        const color = isOrigin ? '#10b981' : '#f43f5e';
        const label = isOrigin ? 'A' : 'B';

        const icon = L.divIcon({
          className: 'od-marker',
          html: `
            <div style="background:${color}; color:white; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:14px; border:2px solid white; box-shadow:0 0 12px ${color};">
              ${label}
            </div>
          `,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });

        L.marker([uCoord[1], uCoord[0]], { icon }).addTo(markersLayerGroupRef.current!);
      }
    });
  }, [networkGeojson, originNodeId, destNodeId]);

  return (
    <div className="relative w-full h-full" style={{ width: '100%', height: '100%' }}>
      <div
        ref={mapContainerRef}
        className="w-full h-full"
        style={{ width: '100%', height: '100%', minHeight: '100%', position: 'absolute', top: 0, left: 0 }}
      />

      {/* Floating Map Legend */}
      <div className="absolute bottom-6 left-6 z-[1000] glass-panel p-3 text-xs flex flex-col gap-2 max-w-xs shadow-2xl">
        <div className="font-semibold text-slate-200 border-b border-slate-700 pb-1 flex justify-between">
          <span>Map Legend</span>
          <span className="text-[10px] text-slate-400">EPSG:4326</span>
        </div>
        <div className="flex flex-col gap-1.5 text-slate-300">
          <div className="flex items-center gap-2">
            <span className="w-4 h-0.5 border-t-2 border-dashed border-amber-400 inline-block"></span>
            <span>Thane Study Area (TMC Boundary)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-3 rounded-sm bg-rose-600/70 border border-rose-500 inline-block"></span>
            <span>Impassable Inundation (&ge; 0.30m)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-3 rounded-sm bg-amber-500/60 border border-amber-400 inline-block"></span>
            <span>Caution Water (0.15m &ndash; 0.30m)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-3 rounded-sm bg-sky-500/40 border border-sky-400 inline-block"></span>
            <span>Shallow Runoff (&lt; 0.15m)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-1 rounded-sm bg-purple-400 inline-block border border-dashed border-purple-300"></span>
            <span>Elevated Bridge Corridor</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-3.5 rounded-full bg-red-600 text-white flex items-center justify-center font-bold text-[10px] border border-white">
              +
            </span>
            <span>Hospital / Emergency Facility</span>
          </div>
        </div>
      </div>
    </div>
  );
};
