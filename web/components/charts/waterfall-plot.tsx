'use client';

import type { WaterfallRow } from '@/lib/types';
import { formatEur } from '@/lib/i18n';
import { PlotlyChart } from './plotly-chart';

export function WaterfallPlot({
  rows, observedDelta, title,
}: {
  rows: WaterfallRow[];
  observedDelta: number;
  title?: string;
}) {
  if (!rows.length) return <p className="text-wisag-gray600 text-sm">—</p>;

  const labels = [...rows.map((r) => r.label), 'Beobachtete ΔDB'];
  const values = [...rows.map((r) => r.delta), observedDelta];
  const measure = [...rows.map(() => 'relative'), 'total'];
  const text = values.map((v) => formatEur(v, true));

  return (
    <div className="w-full" style={{ height: 460 }}>
      <PlotlyChart
        data={[
          {
            type: 'waterfall',
            orientation: 'v',
            x: labels,
            y: values,
            measure: measure as any,
            text,
            textposition: 'outside',
            connector: { line: { color: '#BDBDBD' } },
            increasing: { marker: { color: '#2E7D32' } },
            decreasing: { marker: { color: '#C62828' } },
            totals: { marker: { color: '#1D1D1B' } },
          } as any,
        ]}
        layout={{
          title: { text: title ?? 'Treiberzerlegung der ΔDB (€)' },
          showlegend: false,
          xaxis: { tickangle: -30 },
          yaxis: { title: { text: '€-Beitrag zur ΔDB' } },
          margin: { l: 40, r: 20, t: 60, b: 120 },
        }}
      />
    </div>
  );
}
