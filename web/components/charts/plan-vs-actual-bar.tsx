'use client';

import type { PlanVsActualMonth } from '@/lib/types';
import { formatEur } from '@/lib/i18n';
import { PlotlyChart } from './plotly-chart';

export function PlanVsActualBar({ months }: { months: PlanVsActualMonth[] }) {
  if (!months.length) return <p className="text-wisag-gray600 text-sm">—</p>;
  const x = months.map((m) => m.period);
  const y = months.map((m) => m.gap_eur);
  const colors = y.map((v) => (v < -50_000 ? '#FF6B7A' : v > 50_000 ? '#7BFF86' : '#7F8AA3'));

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
          yaxis: { title: { text: '€' }, zeroline: true, zerolinecolor: 'rgba(255,255,255,0.16)' },
          margin: { l: 60, r: 20, t: 60, b: 60 },
        }}
      />
    </div>
  );
}
