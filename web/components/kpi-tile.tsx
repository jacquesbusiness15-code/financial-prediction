import clsx from 'clsx';

interface KpiTileProps {
  label: string;
  value: string;
  delta?: string | null;
  deltaKind?: 'pos' | 'neg' | 'neu' | null;
}

export function KpiTile({ label, value, delta, deltaKind }: KpiTileProps) {
  return (
    <div className="wisag-card">
      <div className="wisag-kpi-label">{label}</div>
      <div className="wisag-kpi-value">{value}</div>
      {delta ? (
        <div
          className={clsx('wisag-kpi-delta', {
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
