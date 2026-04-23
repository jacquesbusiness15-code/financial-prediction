'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { formatPct, formatPctSigned, t } from '@/lib/i18n';
import type { SimulateTeamSizeResponse } from '@/lib/types';

export function WhatIfSimulator({
  datasetId,
  costCenterId,
  baselineHeadcount,
  teamSizeSuggestion,
  period,
}: {
  datasetId: string;
  costCenterId: string;
  baselineHeadcount: number;
  teamSizeSuggestion: number;
  period?: string;
}) {
  const initialBl = Math.max(1, Math.round(baselineHeadcount) || 100);
  const initialNew = Math.max(0, teamSizeSuggestion);

  const [baseline, setBaseline] = useState<number>(initialBl);
  const [target, setTarget] = useState<number>(initialNew);
  const [result, setResult] = useState<SimulateTeamSizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setBaseline(initialBl);
    setTarget(initialNew);
    setResult(null);
    setError(null);
  }, [initialBl, initialNew, costCenterId, datasetId]);

  useEffect(() => {
    let cancelled = false;
    const id = setTimeout(async () => {
      try {
        const res = await api.simulateTeamSize(datasetId, {
          cost_center_id: costCenterId,
          new_headcount: target,
          baseline_headcount: baseline,
          period: period ?? null,
        });
        if (!cancelled) {
          setResult(res);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError((e as Error).message);
        }
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(id);
    };
  }, [datasetId, costCenterId, target, baseline, period]);

  return (
    <section className="wisag-section-card">
      <div className="wisag-section-head">
        <div>
          <h3 className="wisag-section-title">{t('overview.whatif')}</h3>
          <p className="wisag-section-sub">{t('overview.whatif_sub')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 mt-4 md:grid-cols-[3fr_2fr_2fr] md:items-center">
        <div>
          <div className="flex items-end gap-3">
            <div>
              <label className="wisag-kpi-label block mb-1">{t('overview.team_size')}</label>
              <input
                type="number"
                className="wisag-number-input"
                value={baseline}
                min={1}
                step={1}
                onChange={(e) => setBaseline(Math.max(1, Number(e.target.value) || 1))}
              />
            </div>
            <div className="text-2xl text-wisag-gray500 pb-2">→</div>
            <div>
              <label className="wisag-kpi-label block mb-1 invisible">·</label>
              <input
                type="number"
                className="wisag-number-input"
                value={target}
                min={0}
                step={1}
                onChange={(e) => setTarget(Math.max(0, Number(e.target.value) || 0))}
              />
            </div>
            <div className="text-sm text-wisag-gray600 pb-3 ml-1">
              {t('overview.employees')}
            </div>
          </div>
          {result && (
            <div className="mt-3">
              <span className="wisag-pill wisag-pill-pos">
                {t('overview.productivity_gain', {
                  p: formatPctSigned(result.productivity_gain_pct),
                })}
              </span>
            </div>
          )}
          {error && <p className="text-neg-dark text-xs mt-2">{error}</p>}
        </div>

        <div>
          <div className="wisag-kpi-label">{t('overview.new_margin')}</div>
          <div className="text-3xl font-bold text-wisag-navy tabular-nums">
            {result ? formatPct(result.new_margin) : '—'}
          </div>
          {result && (
            <div
              className={
                'text-sm font-semibold tabular-nums mt-0.5 ' +
                (result.delta_margin >= 0 ? 'text-pos-dark' : 'text-neg-dark')
              }
            >
              {t('overview.vs_current', { p: formatPctSigned(result.delta_margin) })}
            </div>
          )}
        </div>

        <Link href="/chat" className="wisag-explore-card no-underline">
          <span className="wisag-icon-tile wisag-icon-tile-purple wisag-icon-tile-sm">💡</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-wisag-navy m-0">
              {t('overview.explore_more')}
            </p>
            <p className="text-xs text-wisag-gray600 m-0 mt-0.5">
              {t('overview.explore_more_sub')}
            </p>
          </div>
          <span className="wisag-row-chev">›</span>
        </Link>
      </div>
    </section>
  );
}
