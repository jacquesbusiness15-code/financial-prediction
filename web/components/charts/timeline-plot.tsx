'use client';

import type { TimelinePoint } from '@/lib/types';
import { PlotlyChart } from './plotly-chart';

export function TimelinePlot({
  points, title,
}: {
  points: TimelinePoint[];
  title?: string;
}) {
  if (!points.length) return <p className="text-wisag-gray600 text-sm">—</p>;
  const x = points.map((p) => p.period);
  const actual = points.map((p) => p.cm_db);
  const planned = points.map((p) => p.cm_planned);
  const hasPlan = planned.some((v) => v != null);

  return (
    <div className="w-full" style={{ height: 380 }}>
      <PlotlyChart
        data={[
          {
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Ist-DB (€)',
            x, y: actual,
            line: { color: '#7BFF86', width: 3 },
            marker: { size: 7 },
          },
          ...(hasPlan ? [{
            type: 'scatter' as const,
            mode: 'lines' as const,
            name: 'Plan-DB (€)',
            x, y: planned,
            line: { color: '#6FB4FF', width: 2, dash: 'dash' as const },
          }] : []),
        ]}
        layout={{
          title: { text: title ?? 'DB im Zeitverlauf' },
          hovermode: 'x unified',
          yaxis: { title: { text: '€' } },
          legend: { orientation: 'h', y: -0.15 },
          margin: { l: 60, r: 20, t: 60, b: 40 },
        }}
      />
    </div>
  );
}
