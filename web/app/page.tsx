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
  const { dataset } = useDataset();

  const portfolioQuery = useQuery({
    queryKey: ['portfolio-home', dataset?.dataset_id],
    queryFn: () => api.getPortfolio(dataset!.dataset_id, {}),
    enabled: !!dataset,
  });

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold text-wisag-navy">{t('app.welcome')}</h1>
        <p className="text-wisag-gray600">{t('app.welcome_sub')}</p>
      </header>

      {!dataset ? (
        <div className="wisag-card max-w-2xl">
          <p className="text-wisag-navy whitespace-pre-line">{t('data.no_data_warn')}</p>
        </div>
      ) : (
        <>
          <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
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

          {portfolioQuery.data && (
            <section>
              <h2 className="wisag-section-title mb-3">{t('portfolio.top_cc')}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
