import type { AnomalyRow } from '@/lib/types';
import { formatEur, formatPct } from '@/lib/i18n';
import { ImpactPill } from './impact-pill';
import { SeverityBadge } from './severity-badge';
import Link from 'next/link';

export function AnomalyCard({ row }: { row: AnomalyRow }) {
  const href = `/deep-dive?cc=${encodeURIComponent(row.cost_center_id)}`;
  return (
    <Link
      href={href}
      className="wisag-card wisag-card-accent block hover:border-wisag-orange transition"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-wisag-navy truncate">
              {row.cost_center_name || row.cost_center_id}
            </span>
            <span className="rounded-full bg-white/[0.05] px-2 py-0.5 text-[11px] text-wisag-gray600">
              {row.cost_center_id}
            </span>
          </div>
          <div className="text-xs text-wisag-gray600 mb-2">
            {row.region ?? '—'}
            {row.service_type ? ` · ${row.service_type}` : ''} · {row.period}
          </div>
          <div className="text-sm text-wisag-navy/90 leading-snug">
            <span className="text-wisag-gray600">DB </span>
            <span className="font-semibold tabular-nums">{formatEur(row.cm_db)}</span>
            {row.cm_db_pct != null && (
              <span className="text-wisag-gray600 ml-1">({formatPct(row.cm_db_pct)})</span>
            )}
          </div>
          <div className="text-xs text-wisag-gray600 mt-1 line-clamp-2">{row.anomaly_reasons}</div>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <SeverityBadge level={row.severity} />
          <ImpactPill eur={row.impact_eur} />
        </div>
      </div>
    </Link>
  );
}
