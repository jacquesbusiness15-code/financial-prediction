'use client';

import { useQuery } from '@tanstack/react-query';
import { AnomalyCard } from '@/components/anomaly-card';
import { HeatmapPlot } from '@/components/charts/heatmap-plot';
import { EmptyState } from '@/components/empty-state';
import { KpiTile } from '@/components/kpi-tile';
import { api } from '@/lib/api';
import { useDataset } from '@/lib/dataset-context';
import { formatEur, formatPct, t } from '@/lib/i18n';

export default function PortfolioPage() {
  const { dataset, filters } = useDataset();

  const query = useQuery({
    queryKey: ['portfolio', dataset?.dataset_id, filters],
    queryFn: () => api.getPortfolio(dataset!.dataset_id, {
      regions: filters.regions ?? undefined,
      services: filters.services ?? undefined,
      start: filters.start ?? undefined,
      end: filters.end ?? undefined,
    }),
    enabled: !!dataset,
  });

  if (!dataset) return <EmptyState />;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-wisag-navy">{t('portfolio.title')}</h1>
        <p className="text-wisag-gray600">{t('portfolio.subtitle')}</p>
      </header>

      {query.isLoading && <p className="text-wisag-gray600">Laden…</p>}
      {query.isError && (
        <p className="text-neg-dark">
          {t('data.load_failed', { err: (query.error as Error).message })}
        </p>
      )}

      {query.data && (
        <>
          <section className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <KpiTile label={t('kpi.revenue')}      value={formatEur(query.data.kpis.revenue)} />
            <KpiTile label={t('kpi.cm')}           value={formatEur(query.data.kpis.cm_db)} />
            <KpiTile label={t('kpi.cm_planned')}   value={formatEur(query.data.kpis.cm_planned)} />
            <KpiTile
              label={t('kpi.plan_gap')}
              value={formatEur(query.data.kpis.plan_gap, true)}
              deltaKind={query.data.kpis.plan_gap >= 0 ? 'pos' : 'neg'}
            />
            <KpiTile
              label={t('kpi.cost_centers')}
              value={`${query.data.kpis.cost_centers}`}
              delta={`${query.data.kpis.anomalies_count} ${t('kpi.anomalies')}`}
            />
          </section>

          <section className="wisag-card">
            <p className="text-xs text-wisag-gray600 mb-2">{t('portfolio.heatmap_legend')}</p>
            <HeatmapPlot data={query.data.heatmap} />
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="wisag-card lg:col-span-1">
              <h2 className="font-semibold text-wisag-navy mb-3">{t('portfolio.top_cc')}</h2>
              <table className="w-full text-sm">
                <thead className="text-wisag-gray600 text-left">
                  <tr>
                    <th className="font-medium py-1">Kostenstelle</th>
                    <th className="font-medium py-1 text-right">Umsatz</th>
                    <th className="font-medium py-1 text-right">DB %</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.top_cost_centers.map((cc) => (
                    <tr key={cc.cost_center_id} className="border-t border-wisag-gray200">
                      <td className="py-1.5 truncate max-w-[12rem]">
                        <div className="font-medium">{cc.cost_center_name ?? cc.cost_center_id}</div>
                        <div className="text-xs text-wisag-gray600">{cc.region}</div>
                      </td>
                      <td className="py-1.5 text-right tabular-nums">{formatEur(cc.revenue_total)}</td>
                      <td className="py-1.5 text-right tabular-nums">{formatPct(cc.cm_db_pct)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="lg:col-span-2">
              <h2 className="font-semibold text-wisag-navy mb-3">{t('portfolio.anomalies_title')}</h2>
              {query.data.top_anomalies.length === 0 ? (
                <p className="text-wisag-gray600 text-sm">{t('portfolio.anomalies_empty')}</p>
              ) : (
                <div className="space-y-3">
                  {query.data.top_anomalies.map((a) => (
                    <AnomalyCard key={`${a.cost_center_id}-${a.period}`} row={a} />
                  ))}
                </div>
              )}
              <p className="text-xs text-wisag-gray600 mt-3">{t('portfolio.anomalies_hint')}</p>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
