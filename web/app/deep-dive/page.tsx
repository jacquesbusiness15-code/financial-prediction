'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { BulletPlot } from '@/components/charts/bullet-plot';
import { TimelinePlot } from '@/components/charts/timeline-plot';
import { WaterfallPlot } from '@/components/charts/waterfall-plot';
import { DriverRow } from '@/components/driver-row';
import { EmptyState } from '@/components/empty-state';
import { FacilityHeader } from '@/components/facility-header';
import { SectionCard } from '@/components/section-card';
import { WhatIfSimulator } from '@/components/what-if-simulator';
import { api, streamSSE } from '@/lib/api';
import { useDataset } from '@/lib/dataset-context';
import { formatEur, formatPctSigned, t } from '@/lib/i18n';
import type { BaselineMode } from '@/lib/types';

export default function DeepDivePage() {
  return (
    <Suspense fallback={<p className="text-wisag-gray600">Laden…</p>}>
      <DeepDiveInner />
    </Suspense>
  );
}

function DeepDiveInner() {
  const { dataset } = useDataset();
  const router = useRouter();
  const params = useSearchParams();
  const ccFromUrl = params.get('cc');

  const portfolioQuery = useQuery({
    queryKey: ['portfolio-for-picker', dataset?.dataset_id],
    queryFn: () => api.getPortfolio(dataset!.dataset_id, {}),
    enabled: !!dataset,
  });

  const costCenters = useMemo(() => {
    if (!portfolioQuery.data) return [];
    const ids = new Map<string, string>();
    for (const cc of portfolioQuery.data.top_cost_centers) {
      ids.set(cc.cost_center_id, cc.cost_center_name ?? cc.cost_center_id);
    }
    for (const a of portfolioQuery.data.top_anomalies) {
      if (!ids.has(a.cost_center_id)) ids.set(a.cost_center_id, a.cost_center_name ?? a.cost_center_id);
    }
    return Array.from(ids.entries()).map(([id, name]) => ({ id, name }));
  }, [portfolioQuery.data]);

  const [cc, setCc] = useState<string | null>(ccFromUrl);

  useEffect(() => {
    setCc(ccFromUrl);
  }, [ccFromUrl]);

  useEffect(() => {
    if (!cc && costCenters.length) setCc(costCenters[0].id);
  }, [cc, costCenters]);

  useEffect(() => {
    if (cc && cc !== ccFromUrl) {
      const sp = new URLSearchParams(params.toString());
      sp.set('cc', cc);
      router.replace(`/deep-dive?${sp.toString()}`);
    }
  }, [cc, ccFromUrl, params, router]);

  const overviewQuery = useQuery({
    queryKey: ['facility-overview', dataset?.dataset_id, cc],
    queryFn: () => api.getFacilityOverview(dataset!.dataset_id, cc),
    enabled: !!dataset && !!cc,
  });

  const [showDetails, setShowDetails] = useState(false);
  const [mode, setMode] = useState<BaselineMode>('mom');

  const detailsQuery = useQuery({
    queryKey: ['deep-dive', dataset?.dataset_id, cc, mode],
    queryFn: () => api.getDeepDive(dataset!.dataset_id, cc!, mode),
    enabled: !!dataset && !!cc && showDetails,
  });

  const [explanation, setExplanation] = useState<string>('');
  const [explaining, setExplaining] = useState(false);

  const runExplain = async () => {
    if (!dataset || !cc || !detailsQuery.data) return;
    setExplanation('');
    setExplaining(true);
    try {
      await streamSSE(
        `/api/datasets/${dataset.dataset_id}/explain`,
        {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            cost_center_id: cc,
            period: detailsQuery.data.period,
            baseline_mode: mode,
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

  const data = overviewQuery.data;
  const lastUpdated = new Date().toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false,
  });

  return (
    <div className="app-page">
      {/* Topbar */}
      <header className="app-header">
        <div>
          <Link href="/" className="wisag-breadcrumb">
            {t('overview.back')}
          </Link>
          <div className="app-kicker mt-3">Operational diagnosis</div>
          <h1 className="app-title">Deep Dive</h1>
          <p className="app-subtitle">
            Inspect one cost center in detail, understand the margin bridge, and test improvement scenarios.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            className="wisag-input max-w-[14rem]"
            value={cc ?? ''}
            onChange={(e) => setCc(e.target.value || null)}
          >
            {costCenters.map((o) => (
              <option key={o.id} value={o.id}>{o.name} · {o.id}</option>
            ))}
          </select>
          <button
            className="wisag-secondary-btn inline-flex items-center gap-1.5"
            onClick={() => {
              if (!data) return;
              const blob = new Blob(
                [JSON.stringify(data, null, 2)],
                { type: 'application/json' },
              );
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `facility_${data.cost_center_id}_${data.period}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            ⬇ {t('overview.export')}
          </button>
        </div>
      </header>

      {overviewQuery.isError && (
        <p className="text-neg-dark">
          {t('data.load_failed', { err: (overviewQuery.error as Error).message })}
        </p>
      )}
      {overviewQuery.isLoading && <p className="text-wisag-gray600">Laden…</p>}

      {data && (
        <>
          <FacilityHeader data={data} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <SectionCard
              title={t('overview.why_drop')}
              subtitle={t('overview.why_drop_sub')}
              footer={
                <button
                  className="wisag-breadcrumb"
                  onClick={() => setShowDetails((v) => !v)}
                >
                  {t('overview.view_all_drivers')}
                </button>
              }
            >
              {data.worst_drivers.length === 0 ? (
                <div className="py-4 text-sm text-wisag-gray600">
                  {t('data.no_data_page')}
                </div>
              ) : (
                data.worst_drivers.map((d) => (
                  <DriverRow
                    key={d.class_key}
                    icon={d.icon}
                    tint="red"
                    title={t(d.title_key)}
                    subtitle={t(d.sub_key)}
                    pctLabel={
                      d.pct_change != null
                        ? formatPctSigned(d.pct_change)
                        : formatEur(Math.abs(d.delta_eur))
                    }
                    variant="neg"
                  />
                ))
              )}
            </SectionCard>

            <SectionCard
              title={t('overview.what_do')}
              subtitle={t('overview.what_do_sub')}
              hint={t('overview.potential_impact')}
              footer={
                <Link href="/early-warnings" className="wisag-breadcrumb">
                  {t('overview.view_all_actions')}
                </Link>
              }
            >
              {data.recommended_actions.map((a) => (
                <DriverRow
                  key={a.key}
                  icon={a.icon}
                  tint="green"
                  title={t(a.title_key)}
                  subtitle={t(a.sub_key)}
                  pctLabel={formatPctSigned(a.impact_pct)}
                  variant="pos"
                />
              ))}
            </SectionCard>
          </div>

          <WhatIfSimulator
            datasetId={dataset.dataset_id}
            costCenterId={data.cost_center_id}
            baselineHeadcount={data.baseline_headcount}
            teamSizeSuggestion={data.team_size_suggestion}
            period={data.period}
          />

          {showDetails && (
            <div className="space-y-5">
              <section className="wisag-section-card flex flex-wrap items-end gap-4">
                <div>
                  <label className="wisag-kpi-label block mb-1">
                    {t('deepdive.baseline')}
                  </label>
                  <div className="flex gap-1">
                    {(['mom', 'yoy', 'plan'] as BaselineMode[]).map((m) => (
                      <button
                        key={m}
                        onClick={() => setMode(m)}
                        className={
                          'px-3 py-1.5 text-sm rounded border transition ' +
                          (mode === m
                            ? 'bg-wisag-orange text-white border-wisag-orange'
                            : 'bg-white text-wisag-navy border-wisag-gray300 hover:border-wisag-orange')
                        }
                      >
                        {t(`deepdive.baseline_${m === 'mom' ? 'prior_month' : m === 'yoy' ? 'prior_year' : 'plan'}`)}
                      </button>
                    ))}
                  </div>
                </div>
              </section>

              {detailsQuery.isLoading && <p className="text-wisag-gray600">Laden…</p>}
              {detailsQuery.isError && (
                <p className="text-neg-dark">
                  {t('data.load_failed', { err: (detailsQuery.error as Error).message })}
                </p>
              )}

              {detailsQuery.data && (
                <>
                  <section className="wisag-section-card">
                    <TimelinePlot
                      points={detailsQuery.data.timeline}
                      title={t('deepdive.timeline_title', { cc: detailsQuery.data.cost_center_id })}
                    />
                  </section>
                  <section className="wisag-section-card">
                    <WaterfallPlot
                      rows={detailsQuery.data.waterfall}
                      observedDelta={detailsQuery.data.observed_delta}
                      title={t('deepdive.waterfall_title', {
                        baseline: detailsQuery.data.baseline_label,
                        delta: formatEur(detailsQuery.data.observed_delta, true),
                      })}
                    />
                  </section>
                  {detailsQuery.data.kpis_vs_peers.length > 0 && (
                    <section className="wisag-section-card">
                      <h2 className="wisag-section-title mb-2">{t('deepdive.kpi_peers')}</h2>
                      <BulletPlot kpis={detailsQuery.data.kpis_vs_peers} />
                    </section>
                  )}
                  <section className="wisag-section-card">
                    <div className="flex items-center justify-between mb-3">
                      <h2 className="wisag-section-title">{t('deepdive.ai_title')}</h2>
                      <button onClick={runExplain} disabled={explaining} className="wisag-primary-btn">
                        {explaining ? t('deepdive.ai_asking') : t('action.generate_explanation')}
                      </button>
                    </div>
                    {explanation ? (
                      <div className="prose prose-sm max-w-none text-wisag-navy">
                        <ReactMarkdown>{explanation}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-wisag-gray600 text-sm">{t('deepdive.ai_hint')}</p>
                    )}
                  </section>
                </>
              )}
            </div>
          )}

          <p className="text-xs text-wisag-gray600 pt-2">
            🕒 {t('overview.data_updated', { ts: lastUpdated })}
          </p>
        </>
      )}
    </div>
  );
}
