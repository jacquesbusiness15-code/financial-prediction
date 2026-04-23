import { t } from '@/lib/i18n';

export function EmptyState({ messageKey = 'data.no_data_page' }: { messageKey?: string }) {
  return (
    <div className="hero-panel max-w-3xl">
      <span className="eyebrow-chip">Get Started</span>
      <p className="mt-4 text-base leading-7 text-wisag-navy whitespace-pre-line">{t(messageKey)}</p>
    </div>
  );
}
