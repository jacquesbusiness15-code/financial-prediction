'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { IconTile } from '@/components/icon-tile';
import { KpiTile } from '@/components/kpi-tile';
import { api } from '@/lib/api';
import { useDataset } from '@/lib/dataset-context';
import { formatEur, formatPct, t } from '@/lib/i18n';

function facilityEmoji(name?: string | null, region?: string | null): string {
  const s = `${name ?? ''} ${region ?? ''}`.toLowerCase();
  if (s.includes('airport') || s.includes('flug')) return '✈';
  if (s.includes('klinik') || s.includes('hospital') || s.includes('medi')) return '🏥';
  if (s.includes('sicher') || s.includes('security')) return '🛡';
  if (s.includes('reinig') || s.includes('clean')) return '🧹';
  if (s.includes('cater') || s.includes('verpfleg')) return '🍽';
  if (s.includes('bau') || s.includes('technik')) return '🛠';
  if (s.includes('schul') || s.includes('bildung')) return '🎓';
  return '🏢';
}

function statusFor(cmPct: number | null): 'critical' | 'warn' | 'healthy' {
  if (cmPct == null) return 'warn';
  if (cmPct < 0) return 'critical';
  if (cmPct < 0.03) return 'warn';
  return 'healthy';
}

export default function HomePage() {
  const { dataset, filters } = useDataset();

  const portfolioQuery = useQuery({
    queryKey: ['portfolio-home', dataset?.dataset_id, filters],
    queryFn: () => api.getPortfolio(dataset!.dataset_id, {
      regions: filters.regions ?? undefined,
      services: filters.services ?? undefined,
      start: filters.start ?? undefined,
      end: filters.end ?? undefined,
    }),
    enabled: !!dataset,
  });

  const warningsQuery = useQuery({
    queryKey: ['warnings-home', dataset?.dataset_id, filters],
    queryFn: () => api.getWarnings(dataset!.dataset_id, {
      regions: filters.regions ?? undefined,
      services: filters.services ?? undefined,
      start: filters.start ?? undefined,
      end: filters.end ?? undefined,
    }),
    enabled: !!dataset,
  });

  const leadAnomaly = portfolioQuery.data?.top_anomalies[0];
  const leadWarning = warningsQuery.data?.warnings[0];
  const currentMonth = dataset?.summary.period_max
    ? new Date(dataset.summary.period_max).toLocaleString('en-US', { month: 'long', year: 'numeric' })
    : 'Current overview';

  return (
    <div className="app-page">
      <header className="app-header">
        <div>
          <div className="app-kicker">Executive dashboard</div>
          <h1 className="app-title">{currentMonth} Overview</h1>
          <p className="app-subtitle">
            Focus the team on margin health, major deviations, and the next actions worth taking.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="eyebrow-chip">Live filters applied</span>
          {dataset?.summary.period_max && (
            <span className="eyebrow-chip">Latest period {dataset.summary.period_max}</span>
          )}
        </div>
      </header>

      {!dataset ? (
        <div className="hero-panel max-w-3xl">
          <span className="eyebrow-chip">Dataset needed</span>
          <p className="mt-4 text-base leading-7 text-wisag-navy whitespace-pre-line">{t('data.no_data_warn')}</p>
        </div>
      ) : (
        <>
          <section className="grid grid-cols-2 gap-4 xl:grid-cols-4">
            <KpiTile
              label={t('kpi.revenue')}
              value={formatEur(dataset.summary.revenue_total)}
            />
            <KpiTile
              label={t('kpi.cm')}
              value={formatEur(dataset.summary.cm_db_total)}
            />
            <KpiTile
              label={t('kpi.cost_centers')}
              value={String(dataset.summary.cost_centers ?? '—')}
            />
            <KpiTile
              label={t('filter.period')}
              value={`${dataset.summary.period_min ?? '—'} → ${dataset.summary.period_max ?? '—'}`}
            />
          </section>

          <section className="hero-grid">
            <div className="hero-panel">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="soft-label">Priority view</div>
                  <h2 className="mt-2 text-2xl font-bold text-wisag-navy">
                    What is happening in the portfolio this month?
                  </h2>
                </div>
                <Link href="/portfolio" className="wisag-secondary-btn">
                  Open portfolio
                </Link>
              </div>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-wisag-gray600">
                The app ranks cost centers by margin pressure and euro impact, then lets you drill into
                the operational drivers behind each movement. Use this as the management starting point
                before going into detailed investigation.
              </p>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <div className="surface-card-subtle">
                  <div className="soft-label">Top anomaly</div>
                  {leadAnomaly ? (
                    <>
                      <div className="mt-2 text-lg font-semibold text-wisag-navy">
                        {leadAnomaly.cost_center_name ?? leadAnomaly.cost_center_id}
                      </div>
                      <p className="mt-2 text-sm leading-6 text-wisag-gray600">
                        {leadAnomaly.anomaly_reasons}
                      </p>
                    </>
                  ) : (
                    <p className="mt-2 text-sm text-wisag-gray600">No high-impact anomaly under current filters.</p>
                  )}
                </div>
                <div className="surface-card-subtle">
                  <div className="soft-label">Early warning</div>
                  {leadWarning ? (
                    <>
                      <div className="mt-2 text-lg font-semibold text-wisag-navy">{leadWarning.signal}</div>
                      <p className="mt-2 text-sm leading-6 text-wisag-gray600">{leadWarning.detail}</p>
                    </>
                  ) : (
                    <p className="mt-2 text-sm text-wisag-gray600">No major warning signal in the latest slice.</p>
                  )}
                </div>
              </div>
            </div>

            <div className="surface-card space-y-4">
              <div>
                <div className="soft-label">Smart insights</div>
                <h2 className="mt-2 text-xl font-bold text-wisag-navy">Quick management prompts</h2>
              </div>
              <div className="space-y-3">
                <Link href="/deep-dive" className="block rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-wisag-orange">
                  <div className="text-sm font-semibold text-wisag-navy">Deep dive the weakest operation</div>
                  <p className="mt-1 text-sm leading-6 text-wisag-gray600">
                    Review the monthly bridge, peer comparison, and AI explanation for the current leader in risk.
                  </p>
                </Link>
                <Link href="/early-warnings" className="block rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-wisag-orange">
                  <div className="text-sm font-semibold text-wisag-navy">Review proactive warnings</div>
                  <p className="mt-1 text-sm leading-6 text-wisag-gray600">
                    Catch weak contracts, absences, and subcontractor creep before the month closes.
                  </p>
                </Link>
                <Link href="/chat" className="block rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-wisag-orange">
                  <div className="text-sm font-semibold text-wisag-navy">Ask the Co-Pilot directly</div>
                  <p className="mt-1 text-sm leading-6 text-wisag-gray600">
                    Natural-language Q&A over the filtered dataset without switching tools.
                  </p>
                </Link>
              </div>
            </div>
          </section>

          {portfolioQuery.data && (
            <section>
              <div className="flex items-center justify-between gap-3 mb-3">
                <h2 className="wisag-section-title">{t('portfolio.top_cc')}</h2>
                <Link href="/portfolio" className="text-sm text-wisag-gray600 hover:text-white">
                  Full portfolio →
                </Link>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                {portfolioQuery.data.top_cost_centers.slice(0, 9).map((cc) => {
                  const status = statusFor(cc.cm_db_pct);
                  return (
                    <Link
                      key={cc.cost_center_id}
                      href={`/deep-dive?cc=${encodeURIComponent(cc.cost_center_id)}`}
                      className="wisag-nav-card"
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <IconTile icon={facilityEmoji(cc.cost_center_name, cc.region)} tint="purple" />
                        <div className="min-w-0 flex-1">
                          <div className="font-semibold text-wisag-navy truncate">
                            {cc.cost_center_name ?? cc.cost_center_id}
                          </div>
                          <div className="text-xs text-wisag-gray600 truncate">{cc.region ?? '—'}</div>
                        </div>
                        <span
                          className={
                            'wisag-status-pill wisag-status-' + status
                          }
                        >
                          {t(`overview.status.${status === 'warn' ? 'warn' : status}`)}
                        </span>
                      </div>
                      <div className="flex items-end justify-between">
                        <div>
                          <div className="wisag-kpi-label">{t('overview.margin')}</div>
                          <div className="text-2xl font-bold text-wisag-navy tabular-nums">
                            {formatPct(cc.cm_db_pct)}
                          </div>
                        </div>
                        <div className="text-xs text-wisag-gray600 text-right">
                          <div>{t('kpi.revenue')}</div>
                          <div className="font-semibold text-wisag-navy tabular-nums">
                            {formatEur(cc.revenue_total)}
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
