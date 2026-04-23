import { t } from '@/lib/i18n';
import clsx from 'clsx';

export function SeverityBadge({ level }: { level: string }) {
  const cls = {
    high: 'wisag-badge-high',
    medium: 'wisag-badge-medium',
    low: 'wisag-badge-low',
  }[level] ?? 'wisag-badge-low';
  return (
    <span className={clsx('wisag-badge', cls)}>
      {t(`severity.${level}`)}
    </span>
  );
}
