import type { WarningRow } from '@/lib/types';
import { t } from '@/lib/i18n';
import { ImpactPill } from './impact-pill';
import { SeverityBadge } from './severity-badge';
import clsx from 'clsx';

interface Props {
  row: WarningRow;
  selected?: boolean;
  onSelect?: () => void;
}

export function WarningCard({ row, selected, onSelect }: Props) {
  const content = (
    <>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-wisag-navy">
              {t(`signal.${row.signal}`)}
            </span>
          </div>
          <div className="text-xs text-wisag-gray600 mb-1.5">
            {row.cost_center_name || row.cost_center_id}
            {row.region ? ` · ${row.region}` : ''} · {row.period}
          </div>
          <div className="text-sm text-wisag-navy/90">{row.detail}</div>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <SeverityBadge level={row.severity} />
          <ImpactPill eur={row.impact_eur} />
        </div>
      </div>
    </>
  );
  if (onSelect) {
    return (
      <button
        type="button"
        onClick={onSelect}
        className={clsx(
          'wisag-card wisag-card-accent w-full text-left transition',
          selected ? 'border-wisag-orange ring-2 ring-wisag-orangeLight' : '',
        )}
      >
        {content}
      </button>
    );
  }
  return <div className="wisag-card wisag-card-accent">{content}</div>;
}
