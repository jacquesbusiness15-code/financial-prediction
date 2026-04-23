'use client';

import dynamic from 'next/dynamic';
import type { Data, Layout, Config } from 'plotly.js-dist-min';

// Dynamically import so Plotly never runs during SSR.
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export const FONT = { family: 'Manrope, Inter, system-ui, sans-serif', color: '#DDE6F7' };

export const BASE_LAYOUT: Partial<Layout> = {
  plot_bgcolor: 'transparent',
  paper_bgcolor: 'transparent',
  font: FONT,
  margin: { l: 40, r: 20, t: 60, b: 40 },
  xaxis: {
    gridcolor: 'rgba(255,255,255,0.08)',
    zerolinecolor: 'rgba(255,255,255,0.14)',
    linecolor: 'rgba(255,255,255,0.16)',
    tickfont: { color: '#A6B1C6' },
  },
  yaxis: {
    gridcolor: 'rgba(255,255,255,0.08)',
    zerolinecolor: 'rgba(255,255,255,0.14)',
    linecolor: 'rgba(255,255,255,0.16)',
    tickfont: { color: '#A6B1C6' },
  },
};

export const BASE_CONFIG: Partial<Config> = {
  displaylogo: false,
  responsive: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
};

export function PlotlyChart({
  data, layout, config, style, className,
}: {
  data: Data[];
  layout: Partial<Layout>;
  config?: Partial<Config>;
  style?: React.CSSProperties;
  className?: string;
}) {
  return (
    <Plot
      data={data}
      layout={{ ...BASE_LAYOUT, ...layout }}
      config={{ ...BASE_CONFIG, ...config }}
      useResizeHandler
      style={{ width: '100%', height: '100%', ...style }}
      className={className}
    />
  );
}
