'use client';

import type { HeatmapPayload } from '@/lib/types';
import { PlotlyChart } from './plotly-chart';

const HEATMAP_SCALE: [number, string][] = [
  [0, '#FF6B7A'],
  [0.5, '#FFBE5C'],
  [1, '#7BFF86'],
];

export function HeatmapPlot({ data }: { data: HeatmapPayload }) {
  if (!data.rows.length) {
    return <p className="text-wisag-gray600 text-sm">Keine Daten.</p>;
  }
  const height = Math.max(420, 24 * data.rows.length + 120);
  const title = data.row_dim === 'region'
    ? 'Deckungsbeitrag % — Region × Monat'
    : `Deckungsbeitrag % — Top ${data.rows.length} Kostenstellen × Monat`;

  return (
    <div className="w-full" style={{ height }}>
      <PlotlyChart
        data={[
          {
            type: 'heatmap',
            z: data.z,
            x: data.columns,
            y: data.rows,
            colorscale: HEATMAP_SCALE,
            zmin: -0.1,
            zmax: 0.25,
            colorbar: { title: { text: 'DB %' }, tickfont: { color: '#A6B1C6' } },
            hovertemplate: '%{y}<br>%{x}<br>DB %%: %{z:.1%}<extra></extra>',
          } as any,
        ]}
        layout={{
          title: { text: title },
          xaxis: { type: 'category' },
          yaxis: { type: 'category', automargin: true },
          margin: { l: 100, r: 20, t: 60, b: 40 },
        }}
      />
    </div>
  );
}
