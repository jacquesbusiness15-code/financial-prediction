'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { EmptyState } from '@/components/empty-state';
import { KpiTile } from '@/components/kpi-tile';
import { WarningCard } from '@/components/warning-card';
import { api, streamSSE } from '@/lib/api';
import { useDataset } from '@/lib/dataset-context';
import { formatEur, t } from '@/lib/i18n';

export default function EarlyWarningsPage() {
  const { dataset, filters } = useDataset();
  const [selected, setSelected] = useState<number | null>(null);
  const [explanation, setExplanation] = useState('');
  const [explaining, setExplaining] = useState(false);

  const query = useQuery({
    queryKey: ['warnings', dataset?.dataset_id, filters],
    queryFn: () => api.getWarnings(dataset!.dataset_id, {
      regions: filters.regions ?? undefined,
      services: filters.services ?? undefined,
      start: filters.start ?? undefined,
      end: filters.end ?? undefined,
    }),
    enabled: !!dataset,
  });

  const runExplain = async () => {
    if (!dataset || selected == null || !query.data) return;
    const row = query.data.warnings[selected];
    if (!row) return;
    setExplanation('');
    setExplaining(true);
    try {
      // Convert yyyy-mm → yyyy-mm-01
      const period = row.period.length === 7 ? `${row.period}-01` : row.period;
      await streamSSE(
        `/api/datasets/${dataset.dataset_id}/explain`,
        {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            cost_center_id: row.cost_center_id,
            period,
            baseline_mode: 'mom',
          }),
        },
        {
          onDelta: (text) => setExplanation((prev) => prev + text),
          onDone: () => setExplaining(false),
          onError: (msg) => { setExplanation(`⚠️ ${msg}`); setExplaining(false); },
        },
      );
    } catch (e) {
      setExplanation(`⚠️ ${(e as Error).message}`);
      setExplaining(false);
    }
  };

  if (!dataset) return <EmptyState />;

  return (
    <div className="app-page">
      <header className="app-header">
        <div>
          <div className="app-kicker">Forward risk signals</div>
          <h1 className="app-title">{t('warnings.title')}</h1>
          <p className="app-subtitle">{t('warnings.subtitle')}</p>
        </div>
        <div className="eyebrow-chip">Rule-based warnings with AI action plans</div>
      </header>

      {query.isLoading && <p className="text-wisag-gray600">Laden…</p>}
      {query.isError && (
        <p className="text-neg-dark">
          {t('data.load_failed', { err: (query.error as Error).message })}
        </p>
      )}

      {query.data && (
        <>
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <KpiTile label={t('kpi.high_severity')}   value={String(query.data.counts.high ?? 0)} />
            <KpiTile label={t('kpi.medium_severity')} value={String(query.data.counts.medium ?? 0)} />
            <KpiTile label={t('kpi.low_severity')}    value={String(query.data.counts.low ?? 0)} />
            <KpiTile label={t('kpi.eur_at_stake')}    value={formatEur(query.data.total_impact_eur)} />
          </section>

          {query.data.warnings.length === 0 ? (
            <p className="text-wisag-gray600">{t('warnings.none')}</p>
          ) : (
            <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="space-y-3">
                {query.data.warnings.map((w, i) => (
                  <WarningCard
                    key={`${w.cost_center_id}-${w.signal}-${i}`}
                    row={w}
                    selected={selected === i}
                    onSelect={() => setSelected(i)}
                  />
                ))}
              </div>

              <div className="hero-panel">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="font-semibold text-wisag-navy">{t('warnings.action_title')}</h2>
                  <button
                    onClick={runExplain}
                    disabled={selected == null || explaining}
                    className="wisag-primary-btn"
                  >
                    {explaining ? t('deepdive.ai_asking') : t('warnings.ai_button')}
                  </button>
                </div>
                {explanation ? (
                  <div className="prose prose-sm max-w-none text-wisag-navy">
                    <ReactMarkdown>{explanation}</ReactMarkdown>
                  </div>
                ) : (
                  <div className="text-wisag-gray600 text-sm whitespace-pre-line">
                    {t('warnings.rules_body')}
                  </div>
                )}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
