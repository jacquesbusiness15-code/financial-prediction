import type { SparklinePoint } from '@/lib/types';

/**
 * Lightweight inline SVG sparkline with axis labels on the right edge.
 * Colour: red when the trend is declining, green otherwise. Matches the
 * mockup's header trend line (no full Plotly grid needed).
 */
export function MiniTrendChart({
  points,
  declining,
  width = 320,
  height = 80,
}: {
  points: SparklinePoint[];
  declining?: boolean;
  width?: number;
  height?: number;
}) {
  if (!points.length) return null;

  const values = points.map((p) => p.margin);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const span = Math.max(hi - lo, 1e-9);

  const padT = 10;
  const padB = 20;
  const axisColWidth = 46;
  const chartWidth = width - axisColWidth;
  const yRange = height - padT - padB;
  const n = values.length;

  const xs = values.map((_, i) => (n > 1 ? i * (chartWidth / (n - 1)) : chartWidth / 2));
  const ys = values.map((v) => padT + (1 - (v - lo) / span) * yRange);

  const poly = xs.map((x, i) => `${x.toFixed(1)},${ys[i].toFixed(1)}`).join(' ');
  const areaPath =
    `M${xs[0].toFixed(1)},${(height - padB).toFixed(1)} ` +
    `L${poly} ` +
    `L${xs[n - 1].toFixed(1)},${(height - padB).toFixed(1)} Z`;

  const stroke = declining ? '#C62828' : '#2E7D32';
  const fill = declining ? 'rgba(198,40,40,0.18)' : 'rgba(46,125,50,0.18)';

  const pct = (v: number) => `${(v * 100).toFixed(0)}%`;
  const yMaxLabel = pct(hi);
  const yMidLabel = pct((hi + lo) / 2);
  const yMinLabel = pct(lo);

  // Month tick labels under the chart (short, e.g. "Jun")
  const monthOf = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString('en-US', { month: 'short' });
  };

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      preserveAspectRatio="none"
      aria-hidden
    >
      <g fontFamily="Inter, system-ui, sans-serif" fontSize={10} fill="#6B6B6B">
        <text x={chartWidth + 4} y={padT + 4}>{yMaxLabel}</text>
        <text x={chartWidth + 4} y={padT + yRange / 2 + 4}>{yMidLabel}</text>
        <text x={chartWidth + 4} y={padT + yRange + 4}>{yMinLabel}</text>
      </g>
      <path d={areaPath} fill={fill} stroke="none" />
      <polyline points={poly} fill="none" stroke={stroke} strokeWidth={2} />
      {xs.map((x, i) => (
        <circle
          key={i}
          cx={x}
          cy={ys[i]}
          r={2}
          fill={stroke}
        />
      ))}
      <g fontFamily="Inter, system-ui, sans-serif" fontSize={10} fill="#6B6B6B" textAnchor="middle">
        {points.map((p, i) => (
          <text key={i} x={xs[i]} y={height - 4}>{monthOf(p.period)}</text>
        ))}
      </g>
    </svg>
  );
}
