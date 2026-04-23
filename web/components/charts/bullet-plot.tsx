'use client';

import type { PeerKpi } from '@/lib/types';
import { PlotlyChart } from './plotly-chart';

export function BulletPlot({ kpis }: { kpis: PeerKpi[] }) {
  if (!kpis.length) return <p className="text-wisag-gray600 text-sm">—</p>;
  const y = kpis.map((k) => k.kpi);
  const value = kpis.map((k) => k.value);
  const peerMedian = kpis.map((k) => k.peer_median);

  const height = 40 * kpis.length + 120;

  return (
    <div className="w-full" style={{ height }}>
      <PlotlyChart
        data={[
          {
            type: 'bar',
            orientation: 'h',
            y, x: value,
            name: 'Diese Kostenstelle',
            marker: { color: '#E94E1B' },
            text: value.map((v) => v.toFixed(2)),
            textposition: 'outside',
          },
          {
            type: 'scatter',
            mode: 'markers',
            name: 'Regionaler Peer-Median',
            y, x: peerMedian,
            marker: { color: '#6FB4FF', symbol: 'line-ns-open', size: 18, line: { width: 3 } },
          },
        ]}
        layout={{
          title: { text: 'Kennzahlen vs. regionale Peers' },
          legend: { orientation: 'h', y: -0.2 },
          margin: { l: 200, r: 40, t: 60, b: 40 },
          yaxis: { automargin: true },
        }}
      />
    </div>
  );
}
