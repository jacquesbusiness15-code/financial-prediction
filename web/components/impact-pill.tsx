import clsx from 'clsx';
import { formatEur } from '@/lib/i18n';

export function ImpactPill({ eur }: { eur: number | null | undefined }) {
  if (eur == null) return <span className="wisag-pill wisag-pill-neu">—</span>;
  const kind = eur > 0 ? 'wisag-pill-pos' : eur < 0 ? 'wisag-pill-neg' : 'wisag-pill-neu';
  return <span className={clsx('wisag-pill', kind)}>{formatEur(eur, true)}</span>;
}
