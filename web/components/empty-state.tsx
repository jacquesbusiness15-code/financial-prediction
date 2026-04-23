import { t } from '@/lib/i18n';

export function EmptyState({ messageKey = 'data.no_data_page' }: { messageKey?: string }) {
  return (
    <div className="wisag-card max-w-2xl">
      <p className="text-wisag-navy whitespace-pre-line">{t(messageKey)}</p>
    </div>
  );
}
