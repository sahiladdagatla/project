import React from 'react';
import { ShieldAlert, Info, Sparkles, ArrowRight } from 'lucide-react';

interface RouteComparisonPanelProps {
  comparisonData: any;
  activePolicy: string;
  setActivePolicy: (pol: string) => void;
  onViewExplanation?: () => void;
}

export const RouteComparisonPanel: React.FC<RouteComparisonPanelProps> = ({
  comparisonData,
  activePolicy,
  setActivePolicy,
  onViewExplanation
}) => {
  if (!comparisonData?.policies) {
    return (
      <div className="glass-panel p-6 text-center text-slate-400 text-xs">
        Select Origin & Destination and click <b>Compare 4 Routing Policies</b> to view risk-aware comparative analysis.
      </div>
    );
  }

  const { policies, comparison_summary } = comparisonData;

  const policyMeta: Record<string, { title: string; color: string; border: string; desc: string }> = {
    shortest_fastest: {
      title: '1. Shortest / Fastest Path',
      color: 'text-rose-400',
      border: 'border-rose-900/40',
      desc: 'Free-flow Dijkstra (Google Maps model). Oblivious to flood state.'
    },
    departure_time_avoidance: {
      title: '2. Departure-Time Avoidance',
      color: 'text-amber-400',
      border: 'border-amber-700/40',
      desc: 'Avoids segments flooded at departure time. Static assumption.'
    },
    traversal_time_deterministic: {
      title: '3. Traversal-Time Deterministic',
      color: 'text-cyan-400',
      border: 'border-cyan-700/40',
      desc: 'Evaluates each road segment at vehicle arrival time tau(e).'
    },
    proposed_risk_aware: {
      title: '4. Proposed Risk-Aware (FloodTwinAI)',
      color: 'text-emerald-400',
      border: 'border-emerald-600/60',
      desc: 'Arrival time q90 depth + elevated flyover preference + transparent abstention.'
    }
  };

  return (
    <div className="flex flex-col gap-3 text-slate-100 max-h-[90vh] overflow-y-auto pr-1">
      {/* Verdict Banner */}
      <div className="glass-card p-3 border-l-4 border-l-emerald-400 bg-slate-900/90">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Info className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <div className="text-xs font-semibold text-slate-200">Comparative Verdict</div>
          </div>
          {onViewExplanation && (
            <button
              onClick={onViewExplanation}
              className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 hover:text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900/80 px-2 py-0.5 rounded border border-emerald-700 transition"
              title="Open Explainable AI Decision Audit"
            >
              <Sparkles className="w-3 h-3" />
              <span>Why this Path? (XAI)</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>
        <p className="text-[11px] text-slate-300 mt-1.5 leading-relaxed">
          {comparison_summary.verdict}
        </p>
      </div>

      {/* Filter / Focus Buttons */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] text-slate-400">Focus on Map:</span>
        <button
          onClick={() => setActivePolicy('all')}
          className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
            activePolicy === 'all' ? 'bg-slate-700 text-white font-bold' : 'bg-slate-900 text-slate-400'
          }`}
        >
          All Policies
        </button>
        {Object.keys(policies).map((key) => (
          <button
            key={key}
            onClick={() => setActivePolicy(key)}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              activePolicy === key ? 'bg-cyan-500 text-slate-950 font-semibold' : 'bg-slate-900 text-slate-400'
            }`}
          >
            {key.split('_')[0].toUpperCase()}
          </button>
        ))}
      </div>

      {/* 4 Policy Comparison Cards */}
      <div className="flex flex-col gap-2.5">
        {Object.entries(policies).map(([polKey, res]: [string, any]) => {
          const meta = policyMeta[polKey] || { title: polKey, color: 'text-white', border: 'border-slate-700', desc: '' };
          const isSelected = activePolicy === 'all' || activePolicy === polKey;
          const isDanger = res.max_encountered_depth_m >= 0.30;
          const isAbstained = res.abstained;

          return (
            <div
              key={polKey}
              onClick={() => setActivePolicy(polKey)}
              className={`p-3 rounded-lg cursor-pointer transition glass-card border ${meta.border} ${
                isSelected ? 'ring-1 ring-cyan-500/50 shadow-md' : 'opacity-70 hover:opacity-100'
              }`}
            >
              <div className="flex items-center justify-between border-b border-slate-700/60 pb-1.5">
                <div>
                  <h3 className={`text-xs font-bold ${meta.color}`}>{meta.title}</h3>
                  <p className="text-[10px] text-slate-400">{meta.desc}</p>
                </div>
                <div>
                  {isAbstained ? (
                    <span className="badge badge-rose">ABSTAINED</span>
                  ) : isDanger ? (
                    <span className="badge badge-rose">UNSAFE / STALL</span>
                  ) : res.route_available ? (
                    <span className="badge badge-green">ROUTE SAFE</span>
                  ) : (
                    <span className="badge badge-slate">NO PATH</span>
                  )}
                </div>
              </div>

              {/* Metrics Grid */}
              {res.route_available ? (
                <div className="grid grid-cols-4 gap-2 mt-2 pt-1 text-center">
                  <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                    <span className="text-[9px] uppercase tracking-wider text-slate-400 block">Duration</span>
                    <span className="text-xs font-bold font-mono text-cyan-300">
                      {(res.total_duration_s / 60).toFixed(1)}m
                    </span>
                  </div>
                  <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                    <span className="text-[9px] uppercase tracking-wider text-slate-400 block">Distance</span>
                    <span className="text-xs font-bold font-mono text-slate-200">
                      {(res.total_length_m / 1000).toFixed(1)}km
                    </span>
                  </div>
                  <div className={`p-1.5 rounded border ${isDanger ? 'bg-rose-950/40 border-rose-800' : 'bg-slate-900/80 border-slate-800'}`}>
                    <span className="text-[9px] uppercase tracking-wider text-slate-400 block">Flooded Exp</span>
                    <span className={`text-xs font-bold font-mono ${res.total_inundated_exposure_m > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {res.total_inundated_exposure_m.toFixed(0)}m
                    </span>
                  </div>
                  <div className={`p-1.5 rounded border ${isDanger ? 'bg-rose-950/40 border-rose-800' : 'bg-slate-900/80 border-slate-800'}`}>
                    <span className="text-[9px] uppercase tracking-wider text-slate-400 block">Max Depth</span>
                    <span className={`text-xs font-bold font-mono ${res.max_encountered_depth_m >= 0.30 ? 'text-rose-400' : res.max_encountered_depth_m >= 0.15 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {res.max_encountered_depth_m.toFixed(2)}m ({Math.round(res.max_encountered_depth_m * 100)}cm)
                    </span>
                  </div>
                </div>
              ) : (
                <div className="mt-2 p-2 bg-rose-950/20 border border-rose-900/50 rounded text-xs text-rose-300">
                  <div className="font-semibold text-rose-400">Declined Recommendation</div>
                  <div className="text-[11px] text-slate-300 mt-0.5">
                    Reason: <code className="text-rose-300 font-mono text-[10px]">{res.abstention_reason}</code>
                  </div>
                </div>
              )}

              {/* Auditable Explanation */}
              {res.explanation?.summary && (
                <div className="mt-2 text-[11px] text-slate-300 bg-slate-900/60 p-2 rounded border border-slate-800">
                  <span className="text-slate-400 font-medium">Auditable Decision: </span>
                  {res.explanation.summary}
                </div>
              )}

              {/* Danger Warning if Submerged */}
              {res.explanation?.critical_warning && (
                <div className="mt-1.5 text-[11px] text-rose-300 bg-rose-950/40 p-2 rounded border border-rose-800 font-semibold flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-rose-400 flex-shrink-0" />
                  <span>{res.explanation.critical_warning}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
