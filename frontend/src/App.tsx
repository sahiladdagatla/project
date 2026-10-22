import React, { useState, useEffect } from 'react';
import { MapView } from './components/MapView';
import { ControlPanel } from './components/ControlPanel';
import { RouteComparisonPanel } from './components/RouteComparisonPanel';
import { AccessibilityPanel } from './components/AccessibilityPanel';
import { SatellitePanel } from './components/SatellitePanel';
import { ResearchDashboard } from './components/ResearchDashboard';

export const App: React.FC = () => {
  const [operatingMode, setOperatingMode] = useState<string>('exploratory_thane_scenario');
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('thane_exploratory_pluvial_95mm');
  const [currentTimestepIdx, setCurrentTimestepIdx] = useState<number>(2);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const [originNodeId, setOriginNodeId] = useState<string>('TH_STATION');
  const [destNodeId, setDestNodeId] = useState<string>('CADBURY_JUNCTION');

  const [networkGeojson, setNetworkGeojson] = useState<any>(null);
  const [facilitiesGeojson, setFacilitiesGeojson] = useState<any>(null);
  const [boundaryGeojson, setBoundaryGeojson] = useState<any>(null);
  const [places, setPlaces] = useState<any[]>([]);
  const [floodLayerGeojson, setFloodLayerGeojson] = useState<any>(null);

  const [comparisonData, setComparisonData] = useState<any>(null);
  const [activePolicy, setActivePolicy] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'routes' | 'accessibility' | 'satellite' | 'research'>('routes');
  const [isRoutingLoading, setIsRoutingLoading] = useState<boolean>(false);

  // 1. Initial Data Fetch
  useEffect(() => {
    fetch('/api/scenarios')
      .then(r => r.json())
      .then(data => {
        setScenarios(data);
        if (data.length > 0) {
          const defaultSc = data.find((s: any) => s.scenario_id === 'thane_exploratory_pluvial_95mm') || data[0];
          setSelectedScenarioId(defaultSc.scenario_id);
        }
      })
      .catch(err => console.error('Failed to load scenarios:', err));

    fetch('/api/network/geojson')
      .then(r => r.json())
      .then(data => setNetworkGeojson(data))
      .catch(err => console.error('Failed to load road network:', err));

    fetch('/api/facilities/geojson')
      .then(r => r.json())
      .then(data => setFacilitiesGeojson(data))
      .catch(err => console.error('Failed to load facilities:', err));

    fetch('/api/boundary/geojson')
      .then(r => r.json())
      .then(data => setBoundaryGeojson(data))
      .catch(err => console.error('Failed to load boundary:', err));

    fetch('/api/places')
      .then(r => r.json())
      .then(data => setPlaces(data))
      .catch(err => console.error('Failed to load places:', err));
  }, []);

  // 2. Fetch Flood Layer on Scenario or Timestep change
  useEffect(() => {
    if (!selectedScenarioId) return;
    fetch(`/api/flood-layer?scenario_id=${selectedScenarioId}&timestep_idx=${currentTimestepIdx}`)
      .then(r => r.json())
      .then(data => setFloodLayerGeojson(data))
      .catch(err => console.error('Failed to fetch flood layer:', err));
  }, [selectedScenarioId, currentTimestepIdx]);

  // 3. Auto-play timeline timer
  useEffect(() => {
    if (!isPlaying) return;
    const timer = setInterval(() => {
      setCurrentTimestepIdx(prev => {
        const next = prev + 1;
        if (next >= 12) {
          setIsPlaying(false);
          return 0;
        }
        return next;
      });
    }, 2200);
    return () => clearInterval(timer);
  }, [isPlaying]);

  // 4. Trigger Route Comparison with actual Thane coordinates
  const handleRunComparison = () => {
    setIsRoutingLoading(true);

    // Resolve lat/lon for selected origin and destination
    let origLat = 19.1846, origLon = 72.9710;
    let destLat = 19.2046, destLon = 72.9688;

    if (places && places.length > 0) {
      const origMatch = places.find(p => p.node_id === originNodeId);
      const destMatch = places.find(p => p.node_id === destNodeId);
      if (origMatch) {
        origLat = origMatch.lat;
        origLon = origMatch.lon;
      }
      if (destMatch) {
        destLat = destMatch.lat;
        destLon = destMatch.lon;
      }
    }

    fetch('/api/route/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario_id: selectedScenarioId,
        origin_lat: origLat,
        origin_lon: origLon,
        dest_lat: destLat,
        dest_lon: destLon,
        timestep_idx: currentTimestepIdx,
        operating_mode: operatingMode
      })
    })
      .then(r => r.json())
      .then(data => {
        setComparisonData(data);
        setIsRoutingLoading(false);
      })
      .catch(err => {
        console.error('Failed to execute route comparison:', err);
        setIsRoutingLoading(false);
      });
  };

  // Run initial comparison on mount once scenarios ready
  useEffect(() => {
    if (scenarios.length > 0) {
      handleRunComparison();
    }
  }, [scenarios]);

  return (
    <div
      className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans"
      style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden', background: '#0a0f1d' }}
    >
      {/* Left Sidebar: Controls & Scenarios */}
      <div
        className="w-[360px] flex-shrink-0 h-full p-3 z-10"
        style={{ width: '360px', flexShrink: 0, height: '100%', padding: '12px', zIndex: 10, boxSizing: 'border-box' }}
      >
        <ControlPanel
          operatingMode={operatingMode}
          setOperatingMode={setOperatingMode}
          scenarios={scenarios}
          selectedScenarioId={selectedScenarioId}
          setSelectedScenarioId={setSelectedScenarioId}
          currentTimestepIdx={currentTimestepIdx}
          setCurrentTimestepIdx={setCurrentTimestepIdx}
          isPlaying={isPlaying}
          setIsPlaying={setIsPlaying}
          originNodeId={originNodeId}
          setOriginNodeId={setOriginNodeId}
          destNodeId={destNodeId}
          setDestNodeId={setDestNodeId}
          places={places}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onRunComparison={handleRunComparison}
          isRoutingLoading={isRoutingLoading}
        />
      </div>

      {/* Center: Interactive Map */}
      <div
        className="flex-1 h-full relative z-0"
        style={{ flex: 1, height: '100%', position: 'relative' }}
      >
        <MapView
          networkGeojson={networkGeojson}
          facilitiesGeojson={facilitiesGeojson}
          floodLayerGeojson={floodLayerGeojson}
          boundaryGeojson={boundaryGeojson}
          places={places}
          policyResults={comparisonData?.policies}
          activePolicy={activePolicy}
          originNodeId={originNodeId}
          destNodeId={destNodeId}
          onSelectNode={(nodeId, role) => {
            if (role === 'origin') setOriginNodeId(nodeId);
            else setDestNodeId(nodeId);
          }}
        />
      </div>

      {/* Right Drawer: Contextual Panels */}
      <div
        className="w-[430px] flex-shrink-0 h-full p-3 z-10"
        style={{ width: '430px', flexShrink: 0, height: '100%', padding: '12px', zIndex: 10, boxSizing: 'border-box' }}
      >
        <div className="glass-panel h-full p-3 flex flex-col" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {activeTab === 'routes' && (
            <RouteComparisonPanel
              comparisonData={comparisonData}
              activePolicy={activePolicy}
              setActivePolicy={setActivePolicy}
            />
          )}

          {activeTab === 'accessibility' && (
            <AccessibilityPanel
              scenarioId={selectedScenarioId}
              timestepIdx={currentTimestepIdx}
              originNodeId={originNodeId}
            />
          )}

          {activeTab === 'satellite' && (
            <SatellitePanel />
          )}

          {activeTab === 'research' && (
            <ResearchDashboard />
          )}
        </div>
      </div>
    </div>
  );
};
