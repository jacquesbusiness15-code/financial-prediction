'use client';

import { useQuery } from '@tanstack/react-query';
import { PlanVsActualBar } from '@/components/charts/plan-vs-actual-bar';
import { EmptyState } from '@/components/empty-state';
import { KpiTile } from '@/components/kpi-tile';
import { api } from '@/lib/api';
import { useDataset } from '@/lib/dataset-context';
import { formatEur, formatPct, t } from '@/lib/i18n';
import clsx from 'clsx';

export default function PlanVsActualPage() {
  const { dataset, filters } = useDataset();

  const query = useQuery({
    queryKey: ['plan-vs-actual', dataset?.dataset_id, filters],
    queryFn: () => api.getPlanVsActual(dataset!.dataset_id, {
      regions: filters.regions ?? undefined,
      services: filters.services ?? undefined,
      start: filters.start ?? undefined,
      end: filters.end ?? undefined,
    }),
    enabled: !!dataset,
  });

  if (!dataset) return <EmptyState />;

  return (
    <div className="app-page">
      <header className="app-header">
        <div>
          <div className="app-kicker">Performance tracking</div>
          <h1 className="app-title">{t('pva.title')}</h1>
          <p className="app-subtitle">{t('pva.subtitle')}</p>
        </div>
        <div className="eyebrow-chip">Monthly gap view</div>
      </header>

      {query.isLoading && <p className="text-wisag-gray600">Laden…</p>}
      {query.isError && (
        <p className="text-neg-dark">
          {t('data.load_failed', { err: (query.error as Error).message })}
        </p>
      )}

      {query.data && query.data.months.length === 0 && (
        <p className="text-wisag-gray600">{t('pva.missing_cols')}</p>
      )}

      {query.data && query.data.months.length > 0 && (
        <>
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <KpiTile label={t('kpi.total_actual')}  value={formatEur(query.data.total_actual)} />
            <KpiTile label={t('kpi.total_planned')} value={formatEur(query.data.total_planned)} />
            <KpiTile
              label={t('kpi.total_gap')}
              value={formatEur(query.data.total_gap, true)}
              deltaKind={query.data.total_gap >= 0 ? 'pos' : 'neg'}
            />
            <KpiTile label={t('kpi.worst_month')} value={query.data.worst_month ?? '—'} />
          </section>

          <section className="hero-panel">
            <PlanVsActualBar months={query.data.months} />
            <p className="text-xs text-wisag-gray600 mt-1">{t('pva.chart_caption')}</p>
          </section>

          <section className="wisag-card">
            <h2 className="font-semibold text-wisag-navy mb-2">{t('pva.table_title')}</h2>
            <div className="overflow-x-auto">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th className="font-medium py-1">{t('pva.col.month')}</th>
                    <th className="font-medium py-1 text-right">{t('pva.col.revenue')}</th>
                    <th className="font-medium py-1 text-right">{t('pva.col.planned')}</th>
                    <th className="font-medium py-1 text-right">{t('pva.col.actual')}</th>
                    <th className="font-medium py-1 text-right">{t('pva.col.gap_eur')}</th>
                    <th className="font-medium py-1 text-right">{t('pva.col.gap_pct')}</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.months.map((m) => {
                    const cls = clsx({
                      'bg-neg-light/60': m.gap_eur < -50_000,
                      'bg-pos-light/60': m.gap_eur > 50_000,
                    });
                    return (
                      <tr key={m.period} className={clsx('border-t border-wisag-gray200', cls)}>
                        <td className="py-1.5 font-medium">{m.period}</td>
                        <td className="py-1.5 text-right tabular-nums">{formatEur(m.revenue)}</td>
                        <td className="py-1.5 text-right tabular-nums">{formatEur(m.planned)}</td>
                        <td className="py-1.5 text-right tabular-nums">{formatEur(m.actual)}</td>
                        <td className="py-1.5 text-right tabular-nums font-semibold">
                          {formatEur(m.gap_eur, true)}
                        </td>
                        <td className="py-1.5 text-right tabular-nums">{formatPct(m.gap_pct)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
