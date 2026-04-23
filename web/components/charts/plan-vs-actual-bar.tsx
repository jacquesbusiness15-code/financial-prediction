'use client';

import type { PlanVsActualMonth } from '@/lib/types';
import { formatEur } from '@/lib/i18n';
import { PlotlyChart } from './plotly-chart';

export function PlanVsActualBar({ months }: { months: PlanVsActualMonth[] }) {
  if (!months.length) return <p className="text-wisag-gray600 text-sm">—</p>;
  const x = months.map((m) => m.period);
  const y = months.map((m) => m.gap_eur);
  const colors = y.map((v) => (v < -50_000 ? '#C62828' : v > 50_000 ? '#2E7D32' : '#9E9E9E'));

  return (
    <div className="w-full" style={{ height: 380 }}>
      <PlotlyChart
        data={[
          {
            type: 'bar',
            x, y,
            marker: { color: colors },
            text: y.map((v) => formatEur(v, true)),
            textposition: 'outside',
          },
        ]}
        layout={{
          title: { text: 'Monatliche DB-Abweichung (Ist − Plan, €)' },
          showlegend: false,
          yaxis: { title: { text: '€' }, zeroline: true, zerolinecolor: '#9E9E9E' },
          margin: { l: 60, r: 20, t: 60, b: 60 },
        }}
      />
    </div>
  );
}
