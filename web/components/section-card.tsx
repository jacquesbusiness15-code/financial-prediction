import type { ReactNode } from 'react';

export function SectionCard({
  title,
  subtitle,
  hint,
  footer,
  children,
}: {
  title: string;
  subtitle?: string;
  hint?: string;
  footer?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="wisag-section-card">
      <div className="wisag-section-head">
        <div>
          <h3 className="wisag-section-title">{title}</h3>
          {subtitle && <p className="wisag-section-sub">{subtitle}</p>}
        </div>
        {hint && <div className="wisag-section-hint">{hint}</div>}
      </div>
      <div className="divide-y divide-wisag-gray200">{children}</div>
      {footer && <div className="mt-2 pt-3 border-t border-wisag-gray200">{footer}</div>}
    </section>
  );
}
