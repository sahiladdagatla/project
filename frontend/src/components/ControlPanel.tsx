import React from 'react';
import { Play, Pause, RotateCcw, Activity, Navigation, Satellite, FileText } from 'lucide-react';

interface ControlPanelProps {
  operatingMode: string;
  setOperatingMode: (mode: string) => void;
  scenarios: any[];
  selectedScenarioId: string;
  setSelectedScenarioId: (id: string) => void;
  currentTimestepIdx: number;
  setCurrentTimestepIdx: (idx: number) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
  originNodeId: string;
  setOriginNodeId: (id: string) => void;
  destNodeId: string;
  setDestNodeId: (id: string) => void;
  places?: any[];
  activeTab: 'routes' | 'accessibility' | 'satellite' | 'research';
  setActiveTab: (tab: 'routes' | 'accessibility' | 'satellite' | 'research') => void;
  onRunComparison: () => void;
  isRoutingLoading: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  operatingMode,
  setOperatingMode,
  scenarios,
  selectedScenarioId,
  setSelectedScenarioId,
  currentTimestepIdx,
  setCurrentTimestepIdx,
  isPlaying,
  setIsPlaying,
  originNodeId,
  setOriginNodeId,
  destNodeId,
  setDestNodeId,
  places = [],
  activeTab,
  setActiveTab,
  onRunComparison,
  isRoutingLoading
}) => {
  const currentScenario = scenarios.find(s => s.scenario_id === selectedScenarioId) || scenarios[0];
  const maxTimesteps = currentScenario?.timesteps?.length || 12;

  // Authentic Thane Journey Presets
  const presets = [
    { label: 'Thane Stn → Jupiter Hospital', orig: 'TH_STATION', dest: 'CADBURY_JUNCTION', desc: 'EEH Spine; bypasses Vandana depression via Teen Hath Flyover' },
    { label: 'Naupada → Thane Civil Hospital', orig: 'NAUPADA', dest: 'COURT_NAKA', desc: 'Old Thane city corridor between commercial core & Civil Hospital' },
    { label: 'Wagle Estate → Bethany Hospital', orig: 'WAGLE_ESTATE', dest: 'VARTAK_NAGAR', desc: 'Connects industrial/IT belt to Pokhran Rd 1 healthcare facility' },
    { label: 'Teen Hath Naka → Titan Hospital', orig: 'TEEN_HATH_NAKA', dest: 'MANPADA', desc: 'Major arterial corridor northwards along Ghodbunder Road' },
    { label: 'Court Naka → CSMH Kalwa Bridge', orig: 'COURT_NAKA', dest: 'CSMH_KALWA_JCT', desc: 'Cross-creek emergency link via elevated Kalwa Creek Bridge' },
    { label: 'Mulund Toll → Hiranandani Estate', orig: 'MULUND_TOLL', dest: 'HIRANANDANI_EST', desc: 'South-to-North full transit across the TMC administrative corridor' },
    { label: 'Vandana Hotspot → Cadbury Junction', orig: 'VANDANA_CINEMA', dest: 'CADBURY_JUNCTION', desc: 'Chronic lowland depression bowl to EEH Cadbury junction' }
  ];

  return (
    <div className="flex flex-col gap-3 p-4 glass-panel text-slate-100 max-h-[95vh] overflow-y-auto">
      {/* Title & Brand */}
      <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse shadow-lg shadow-cyan-400/50"></div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
              FloodTwinAI <span className="text-xs font-mono font-normal text-amber-400 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-800">Thane City</span>
            </h1>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Urban Flood Digital Twin: Explainable Forecasting & Risk-Aware Routing
          </p>
          <div className="text-[10px] text-emerald-400 font-mono mt-1 flex items-center gap-1">
            <span>● Study Area: TMC Boundary (OSM 7120000)</span>
          </div>
        </div>
      </div>

      {/* Operating Mode Selector (Strict Mode Separation) */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>Operating Mode</span>
          <span className="text-[10px] text-cyan-400 font-mono">Mode A–D</span>
        </label>
        <div className="grid grid-cols-2 gap-1 bg-slate-900/90 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setOperatingMode('road_network_only')}
            className={`py-1.5 px-2 rounded text-[11px] font-medium transition ${
              operatingMode === 'road_network_only'
                ? 'bg-slate-700 text-white font-semibold shadow'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Mode A: Road Network Only (flood state unknown)"
          >
            A: Road Network Only
          </button>
          <button
            onClick={() => { setOperatingMode('satellite_observation'); setActiveTab('satellite'); }}
            className={`py-1.5 px-2 rounded text-[11px] font-medium transition ${
              operatingMode === 'satellite_observation'
                ? 'bg-cyan-500 text-slate-950 font-semibold shadow'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Mode B: Satellite SAR Observation Snapshot"
          >
            B: Satellite SAR
          </button>
          <button
            onClick={() => setOperatingMode('exploratory_thane_scenario')}
            className={`py-1.5 px-2 rounded text-[11px] font-medium transition ${
              operatingMode === 'exploratory_thane_scenario' || operatingMode === 'benchmark_simulation'
                ? 'bg-amber-500 text-slate-950 font-semibold shadow'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Mode C: Exploratory Thane Flood Scenario (Uncalibrated Proxy)"
          >
            C: Thane Scenario
          </button>
          <button
            onClick={() => { setOperatingMode('research_benchmarks'); setActiveTab('research'); }}
            className={`py-1.5 px-2 rounded text-[11px] font-medium transition ${
              operatingMode === 'research_benchmarks'
                ? 'bg-purple-500 text-white font-semibold shadow'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Mode D: Research Benchmarks (Isolated Ground-Truth)"
          >
            D: Research Benchmarks
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="grid grid-cols-4 gap-1 border-b border-slate-800 pb-2 pt-1">
        <button
          onClick={() => setActiveTab('routes')}
          className={`py-1.5 px-2 rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition ${
            activeTab === 'routes'
              ? 'bg-slate-800 text-cyan-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Navigation className="w-3.5 h-3.5" />
          Routes
        </button>
        <button
          onClick={() => setActiveTab('accessibility')}
          className={`py-1.5 px-2 rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition ${
            activeTab === 'accessibility'
              ? 'bg-slate-800 text-cyan-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Facilities
        </button>
        <button
          onClick={() => setActiveTab('satellite')}
          className={`py-1.5 px-2 rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition ${
            activeTab === 'satellite'
              ? 'bg-slate-800 text-cyan-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Satellite className="w-3.5 h-3.5" />
          SAR Map
        </button>
        <button
          onClick={() => setActiveTab('research')}
          className={`py-1.5 px-2 rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition ${
            activeTab === 'research'
              ? 'bg-slate-800 text-cyan-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          Research
        </button>
      </div>

      {/* Scenario Selector */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Storm Rainfall Scenario
        </label>
        <select
          value={selectedScenarioId}
          onChange={(e) => setSelectedScenarioId(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-md p-2 text-xs text-white focus:outline-none focus:border-cyan-400"
        >
          {scenarios.map(s => (
            <option key={s.scenario_id} value={s.scenario_id}>
              {s.name} ({s.total_rainfall_mm}mm)
            </option>
          ))}
        </select>
        <p className="text-[11px] text-slate-400 italic">
          {currentScenario?.description}
        </p>
      </div>

      {/* Timeline Controls */}
      <div className="flex flex-col gap-2 p-3 glass-card">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-300">Simulation Timeline</span>
          <span className="font-mono text-cyan-400 font-medium">
            T+{(currentTimestepIdx * 15)}m ({currentTimestepIdx + 1}/{maxTimesteps})
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-1.5 rounded-md bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold transition"
            title={isPlaying ? "Pause Playback" : "Play Timeline"}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button
            onClick={() => { setIsPlaying(false); setCurrentTimestepIdx(0); }}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Reset Timeline to T=0"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <input
            type="range"
            min={0}
            max={maxTimesteps - 1}
            value={currentTimestepIdx}
            onChange={(e) => {
              setIsPlaying(false);
              setCurrentTimestepIdx(parseInt(e.target.value));
            }}
            className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>T+0m (Dry)</span>
          <span>T+45m (Onset)</span>
          <span>T+75m (Peak)</span>
          <span>T+165m (Recede)</span>
        </div>
      </div>

      {/* OD Route Selection */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Journey Origin & Destination
          </label>
        </div>

        {/* Origin Dropdown / Input */}
        <div className="flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span> Origin (A)
            </span>
            <span className="font-mono text-emerald-400 text-[10px]">{originNodeId}</span>
          </span>
          {places.length > 0 ? (
            <select
              value={originNodeId}
              onChange={(e) => setOriginNodeId(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-emerald-300 focus:outline-none focus:border-emerald-500"
            >
              {places.map((pl) => (
                <option key={`orig-${pl.node_id}`} value={pl.node_id}>
                  {pl.name} ({pl.node_id})
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={originNodeId}
              onChange={(e) => setOriginNodeId(e.target.value.toUpperCase())}
              className="bg-slate-900 border border-slate-700 rounded p-1.5 text-xs font-mono font-semibold text-emerald-400"
            />
          )}
        </div>

        {/* Destination Dropdown / Input */}
        <div className="flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-500 inline-block"></span> Destination (B)
            </span>
            <span className="font-mono text-rose-400 text-[10px]">{destNodeId}</span>
          </span>
          {places.length > 0 ? (
            <select
              value={destNodeId}
              onChange={(e) => setDestNodeId(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-rose-300 focus:outline-none focus:border-rose-500"
            >
              {places.map((pl) => (
                <option key={`dest-${pl.node_id}`} value={pl.node_id}>
                  {pl.name} ({pl.node_id})
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={destNodeId}
              onChange={(e) => setDestNodeId(e.target.value.toUpperCase())}
              className="bg-slate-900 border border-slate-700 rounded p-1.5 text-xs font-mono font-semibold text-rose-400"
            />
          )}
        </div>

        {/* Mode A Notice */}
        {operatingMode === 'road_network_only' && (
          <div className="p-2 rounded bg-slate-900 border border-slate-700 text-[11px] text-slate-300">
            <b className="text-slate-100">Mode A (Road Only):</b> Routing runs strictly on verified TMC road network. Flood exposure is marked unknown.
          </div>
        )}

        {/* Mode C Notice */}
        {(operatingMode === 'exploratory_thane_scenario' || operatingMode === 'benchmark_simulation') && (
          <div className="p-2 rounded bg-amber-950/30 border border-amber-800/40 text-[11px] text-amber-200">
            <b className="text-amber-100">Mode C (Thane Scenario):</b> Exploratory pluvial proxy scenario based on documented depression hotspots (Vandana, Teen Hath Naka, Majiwada underpass).
          </div>
        )}

        {/* Preset Buttons */}
        <div className="flex flex-col gap-1 mt-1">
          <span className="text-[10px] text-slate-500 uppercase font-semibold">Evaluation Presets:</span>
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => { setOriginNodeId(p.orig); setDestNodeId(p.dest); }}
              className="text-left p-1.5 rounded glass-card hover:border-cyan-500/50 transition text-[11px] text-slate-300"
            >
              <div className="font-semibold text-slate-200">{p.label}</div>
              <div className="text-[10px] text-slate-400">{p.desc}</div>
            </button>
          ))}
        </div>

        <button
          onClick={onRunComparison}
          disabled={isRoutingLoading}
          className="mt-2 w-full py-2 px-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-900/40 transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isRoutingLoading ? (
            <span className="inline-block animate-spin mr-1">↻</span>
          ) : (
            <Navigation className="w-4 h-4" />
          )}
          Compare 4 Routing Policies
        </button>
      </div>
    </div>
  );
};
