import clsx from 'clsx';

interface KpiTileProps {
  label: string;
  value: string;
  delta?: string | null;
  deltaKind?: 'pos' | 'neg' | 'neu' | null;
}

export function KpiTile({ label, value, delta, deltaKind }: KpiTileProps) {
  return (
    <div className="wisag-card overflow-hidden">
      <div className="flex items-center justify-between gap-3">
        <div className="wisag-kpi-label">{label}</div>
        <div className="h-9 w-9 rounded-2xl bg-white/[0.05]" />
      </div>
      <div className="wisag-kpi-value mt-3">{value}</div>
      {delta ? (
        <div
          className={clsx('wisag-kpi-delta mt-2', {
            'text-pos-dark': deltaKind === 'pos',
            'text-neg-dark': deltaKind === 'neg',
            'text-wisag-gray600': !deltaKind || deltaKind === 'neu',
          })}
        >
          {delta}
        </div>
      ) : null}
    </div>
  );
}
