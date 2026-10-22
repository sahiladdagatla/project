import React, { useEffect, useState } from 'react';
import { ShieldAlert } from 'lucide-react';

export const SatellitePanel: React.FC = () => {
  const [chips, setChips] = useState<any[]>([]);
  const [selectedChipId, setSelectedChipId] = useState<string>('Ghana_319168');
  const [segmentResult, setSegmentResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    fetch('/api/satellite/chips')
      .then(r => r.json())
      .then(data => {
        setChips(data);
        if (data.length > 0) {
          runSegmentation(data[0].chip_id);
        }
      })
      .catch(err => console.error('Failed to load chips:', err));
  }, []);

  const runSegmentation = (chipId: string) => {
    setSelectedChipId(chipId);
    setLoading(true);
    fetch(`/api/satellite/segment?chip_id=${chipId}`)
      .then(r => r.json())
      .then(data => {
        setSegmentResult(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Segmentation failed:', err);
        setLoading(false);
      });
  };

  return (
    <div className="flex flex-col gap-3 text-slate-100 max-h-[90vh] overflow-y-auto pr-1">
      {/* Scientific Boundary Notice (Section 4 & 5.6) */}
      <div className="glass-card p-3 border-l-4 border-l-amber-500 bg-amber-950/20 text-xs">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span className="font-semibold text-amber-300">Data Boundary Notice</span>
        </div>
        <p className="text-[11px] text-slate-300 mt-1">
          Satellite radar provides a <b>timestamped snapshot</b> at satellite overpass. It does <b>NOT</b> equal continuous real-time forecasting. This mode verifies our U-Net radar baseline against public Sen1Floods11 ground truth.
        </p>
      </div>

      {/* Chip Selector */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Sen1Floods11 Sentinel-1 SAR Chip
        </label>
        <select
          value={selectedChipId}
          onChange={(e) => runSegmentation(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-md p-2 text-xs text-white focus:outline-none focus:border-cyan-400"
        >
          {chips.map(c => (
            <option key={c.chip_id} value={c.chip_id}>
              {c.chip_id} ({c.location} Flood Disaster)
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="glass-panel p-6 text-center text-slate-400 text-xs">
          <span className="inline-block animate-spin mr-1">↻</span> Executing U-Net inference on Sentinel-1 SAR bands (VV, VH)...
        </div>
      ) : segmentResult ? (
        <div className="flex flex-col gap-2.5">
          {/* Real Metrics Grid */}
          <div className="grid grid-cols-2 gap-2">
            <div className="glass-card p-2.5 text-center">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Flood-Class IoU</span>
              <span className="text-xl font-bold font-mono text-cyan-400">
                {segmentResult.metrics?.flood_iou ?? 'N/A'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Primary Benchmark Metric</span>
            </div>
            <div className="glass-card p-2.5 text-center">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">F1-Score</span>
              <span className="text-xl font-bold font-mono text-emerald-400">
                {segmentResult.metrics?.f1_score ?? 'N/A'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Harmonic Mean (Prec & Rec)</span>
            </div>
            <div className="glass-card p-2.5 text-center">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Precision</span>
              <span className="text-lg font-bold font-mono text-slate-200">
                {segmentResult.metrics?.precision ?? 'N/A'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">True Water / Pred Water</span>
            </div>
            <div className="glass-card p-2.5 text-center">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Recall</span>
              <span className="text-lg font-bold font-mono text-slate-200">
                {segmentResult.metrics?.recall ?? 'N/A'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">True Water / Actual Water</span>
            </div>
          </div>

          {/* Provenance Card */}
          <div className="glass-card p-3 text-xs flex flex-col gap-1.5">
            <div className="font-semibold text-slate-200 border-b border-slate-700 pb-1 flex items-center justify-between">
              <span>Sensor & Provenance Details</span>
              <span className="badge badge-blue">Verified Public Data</span>
            </div>
            <div className="text-[11px] text-slate-300 grid grid-cols-2 gap-2">
              <div>
                <span className="text-slate-400 block text-[10px]">Sensor:</span>
                <b>{segmentResult.provenance?.sensor}</b>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Polarization:</span>
                <b>VV & VH (2 Channels)</b>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Ground Resolution:</span>
                <b>{segmentResult.provenance?.resolution}</b>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Ground Truth QC:</span>
                <b>{segmentResult.provenance?.ground_truth_label}</b>
              </div>
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-1 pt-1 border-t border-slate-800">
              CRS: {segmentResult.crs} | Valid Pixels Evaluated: {segmentResult.metrics?.valid_pixels_count?.toLocaleString()}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
