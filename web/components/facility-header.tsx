import type { FacilityOverviewResponse } from '@/lib/types';
import { formatPct, formatPctSigned, t } from '@/lib/i18n';
import { IconTile } from './icon-tile';
import { MiniTrendChart } from './mini-trend-chart';
import { StatusPill } from './status-pill';

export function FacilityHeader({ data }: { data: FacilityOverviewResponse }) {
  const mom = data.margin_mom_delta;
  const momNeg = typeof mom === 'number' && mom < 0;
  const momPos = typeof mom === 'number' && mom > 0;

  return (
    <section className="hero-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="eyebrow-chip">Facility signal</span>
        <span className="text-xs uppercase tracking-[0.24em] text-wisag-gray600">{data.period}</span>
      </div>
      <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-[2fr_1fr_1fr_2fr] md:items-center">
        <div className="flex items-center gap-4 min-w-0">
          <IconTile icon={data.icon} tint="purple" className="ring-1 ring-white/10" />
          <div className="min-w-0">
            <h2 className="text-2xl font-bold text-wisag-navy truncate">
              {data.cost_center_name ?? data.cost_center_id}
            </h2>
            <p className="text-sm text-wisag-gray600 truncate">{data.region ?? '—'}</p>
            <div className="mt-1">
              <StatusPill status={data.status} />
            </div>
          </div>
        </div>

        <div>
          <div className="wisag-kpi-label">{t('overview.margin')}</div>
          <div className="text-3xl font-bold text-wisag-navy tabular-nums">
            {formatPct(data.margin_pct)}
          </div>
        </div>

        <div>
          <div className="wisag-kpi-label">{t('overview.change_mom')}</div>
          <div
            className={
              'text-3xl font-bold tabular-nums ' +
              (momNeg ? 'text-neg-dark' : momPos ? 'text-pos-dark' : 'text-wisag-navy')
            }
          >
            {formatPctSigned(mom)}
            {momNeg ? ' ↓' : momPos ? ' ↑' : ''}
          </div>
        </div>

        <div className="wisag-trend-chart-mini">
          <MiniTrendChart points={data.sparkline} declining={momNeg} />
        </div>
      </div>
    </section>
  );
}
