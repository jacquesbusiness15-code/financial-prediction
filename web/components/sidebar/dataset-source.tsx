'use client';

import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '@/lib/api';
import { useDataset } from '@/lib/dataset-context';
import { t } from '@/lib/i18n';

export function DatasetSource() {
  const { dataset, setDataset } = useDataset();
  const [source, setSource] = useState('');

  const mutation = useMutation({
    mutationFn: (src: string) => api.postDataset(src),
    onSuccess: (data) => setDataset(data),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (source.trim()) mutation.mutate(source.trim());
  };

  const report = dataset?.schema_report;

  return (
    <section className="border-t border-white/10 pt-4">
      <h3 className="text-xs font-semibold text-wisag-gray600 uppercase tracking-[0.24em] mb-2">
        {t('sidebar.data_source')}
      </h3>
      <p className="mb-3 text-xs leading-5 text-wisag-gray600">
        Paste a Google Sheets link or any local `.csv` / `.xlsx` path. Absolute paths work too.
      </p>
      <form onSubmit={submit} className="space-y-2">
        <input
          type="text"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder={t('sidebar.url_placeholder')}
          className="wisag-input"
        />
        <button
          type="submit"
          disabled={!source.trim() || mutation.isPending}
          className="wisag-primary-btn w-full"
        >
          {mutation.isPending ? '…' : t('sidebar.load')}
        </button>
      </form>
      <div className="mt-2 flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-full border border-white/10 px-3 py-1 text-xs text-wisag-gray600 transition hover:border-wisag-orange hover:text-white"
          onClick={() => setSource('data/Dataset_anoym.xlsx')}
        >
          Use repo sample path
        </button>
      </div>
      {mutation.isError && (
        <p className="mt-2 text-xs text-neg-dark">
          {t('data.load_failed', { err: (mutation.error as Error).message })}
        </p>
      )}

      {dataset && report && (
        <div className="mt-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs">
          {report.ok ? (
            <p className="text-pos-dark">
              {t('data.schema_ok', { m: report.matched.length, t: report.expected_total })}
            </p>
          ) : (
            <p className="text-neg-dark">
              {t('data.schema_error', {
                m: report.matched.length,
                t: report.expected_total,
                missing: report.missing_critical.join(', '),
              })}
            </p>
          )}
          {dataset.summary.period_min && (
            <p className="text-wisag-gray600 mt-1">
              {t('data.stats', {
                rows: dataset.summary.rows.toLocaleString('de-DE'),
                ccs: dataset.summary.cost_centers ?? '?',
                pmin: dataset.summary.period_min,
                pmax: dataset.summary.period_max ?? '?',
              })}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
