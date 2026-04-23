import clsx from 'clsx';
import { IconTile } from './icon-tile';

export function DriverRow({
  icon,
  tint,
  title,
  subtitle,
  pctLabel,
  variant,
}: {
  icon: string;
  tint: 'red' | 'green' | 'orange' | 'purple' | 'blue' | 'gray';
  title: string;
  subtitle: string;
  pctLabel: string;
  variant: 'pos' | 'neg';
}) {
  return (
    <div className="wisag-row rounded-2xl px-2 transition hover:bg-white/[0.04]">
      <IconTile icon={icon} tint={tint} />
      <div className="flex-1 min-w-0">
        <div className="wisag-row-title truncate">{title}</div>
        <div className="wisag-row-sub truncate">{subtitle}</div>
      </div>
      <span
        className={clsx('wisag-row-pct', variant === 'pos' ? 'wisag-row-pct-pos' : 'wisag-row-pct-neg')}
      >
        {pctLabel}
      </span>
      <span className="wisag-row-chev">›</span>
    </div>
  );
}
