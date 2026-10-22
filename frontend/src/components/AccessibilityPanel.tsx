import React, { useEffect, useState } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';

interface AccessibilityPanelProps {
  scenarioId: string;
  timestepIdx: number;
  originNodeId: string;
}

export const AccessibilityPanel: React.FC<AccessibilityPanelProps> = ({
  scenarioId,
  timestepIdx,
  originNodeId
}) => {
  const [data, setData] = useState<any>(null);
  const [criticalRoads, setCriticalRoads] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`/api/accessibility?scenario_id=${scenarioId}&timestep_idx=${timestepIdx}&origin_node_id=${originNodeId}`).then(r => r.json()),
      fetch('/api/accessibility/critical-roads').then(r => r.json())
    ])
      .then(([accData, crData]) => {
        setData(accData);
        setCriticalRoads(crData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch accessibility:', err);
        setLoading(false);
      });
  }, [scenarioId, timestepIdx, originNodeId]);

  if (loading || !data) {
    return (
      <div className="glass-panel p-6 text-center text-slate-400 text-xs">
        <span className="inline-block animate-spin mr-1">↻</span> Calculating infrastructure reachability...
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 text-slate-100 max-h-[90vh] overflow-y-auto pr-1">
      {/* Header Stat Cards */}
      <div className="grid grid-cols-3 gap-2">
        <div className="glass-card p-2.5 text-center">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">Reachable Hospitals</span>
          <span className="text-base font-bold font-mono text-cyan-400">
            {data.reachable_facilities_count} / {data.total_facilities_count}
          </span>
          <span className="text-[10px] text-slate-400 block mt-0.5">({data.accessibility_percentage}%)</span>
        </div>
        <div className="glass-card p-2.5 text-center">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">Severed Roads</span>
          <span className="text-base font-bold font-mono text-rose-400">
            {data.severed_road_segments_count}
          </span>
          <span className="text-[10px] text-slate-400 block mt-0.5">links underwater</span>
        </div>
        <div className="glass-card p-2.5 text-center">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">Avg Travel Time</span>
          <span className="text-base font-bold font-mono text-emerald-400">
            {data.average_travel_time_min ? `${data.average_travel_time_min}m` : 'N/A'}
          </span>
          <span className="text-[10px] text-slate-400 block mt-0.5">to open facilities</span>
        </div>
      </div>

      {/* Hospital Reachability List */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Emergency Hospital Reachability
          </h3>
          <span className="text-[10px] text-slate-400">From Origin: {originNodeId}</span>
        </div>

        <div className="flex flex-col gap-1.5">
          {data.facility_reports?.map((fac: any) => (
            <div
              key={fac.facility_id}
              className={`p-2.5 rounded-lg glass-card border transition ${
                fac.is_reachable ? 'border-emerald-600/40' : 'border-rose-700/50 bg-rose-950/20'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{fac.name}</h4>
                  <div className="text-[10px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                    <span>Junction: <b>{fac.shortest_path_nodes?.[fac.shortest_path_nodes.length - 1] || 'Severed'}</b></span>
                    <span>&bull;</span>
                    <span className="capitalize">{fac.facility_type.replace('_', ' ')}</span>
                  </div>
                </div>
                <div>
                  {fac.is_reachable ? (
                    <span className="badge badge-green flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> {fac.travel_time_min} min
                    </span>
                  ) : (
                    <span className="badge badge-rose flex items-center gap-1">
                      <XCircle className="w-3 h-3" /> Disconnected
                    </span>
                  )}
                </div>
              </div>

              {/* Status Note & Constraint */}
              <div className="mt-1.5 pt-1.5 border-t border-slate-800 flex items-center justify-between text-[10px]">
                <span className="text-slate-400 italic">{fac.notes}</span>
                <span className="bg-slate-900 px-1.5 py-0.5 rounded text-[9px] text-slate-400 font-mono">
                  OP_STATUS: UNKNOWN
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Critical Road Ranking */}
      <div className="flex flex-col gap-2 mt-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Critical Road Connections (Top Ranked)
          </h3>
          <span className="text-[10px] text-slate-400">Loss Impact on Care</span>
        </div>

        <div className="flex flex-col gap-1.5">
          {criticalRoads?.critical_segments?.slice(0, 5).map((seg: any) => (
            <div key={seg.edge_id} className="p-2 glass-card rounded text-xs flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-cyan-400 font-mono">
                  #{seg.rank} {seg.edge_id} ({seg.u} &rarr; {seg.v})
                </span>
                <span className="text-[10px] font-semibold bg-cyan-950/70 border border-cyan-800 text-cyan-300 px-1.5 py-0.2 rounded">
                  Score: {seg.criticality_score}
                </span>
              </div>
              <p className="text-[10px] text-slate-300">
                {seg.reason}
              </p>
              <div className="flex items-center justify-between text-[9px] text-slate-400 font-mono">
                <span>BC: {seg.betweenness_centrality}</span>
                <span>Hospital Routes: {seg.servicing_hospitals_count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
