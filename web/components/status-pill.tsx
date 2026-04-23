import clsx from 'clsx';
import type { FacilityStatus } from '@/lib/types';
import { t } from '@/lib/i18n';

const LABEL_KEY: Record<FacilityStatus, string> = {
  critical: 'overview.status.critical',
  warn: 'overview.status.warn',
  healthy: 'overview.status.healthy',
};

export function StatusPill({ status, className }: { status: FacilityStatus; className?: string }) {
  return (
    <span
      className={clsx('wisag-status-pill', `wisag-status-${status}`, className)}
      role="status"
    >
      {t(LABEL_KEY[status])}
    </span>
  );
}
