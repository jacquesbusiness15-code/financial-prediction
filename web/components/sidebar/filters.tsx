'use client';

import { useDataset } from '@/lib/dataset-context';
import { t } from '@/lib/i18n';

export function Filters() {
  const { dataset, filters, setFilters } = useDataset();
  if (!dataset) return null;
  const { regions, services, period_min, period_max } = dataset.facets;

  return (
    <section className="border-t border-wisag-gray200 pt-4">
      <h3 className="text-xs font-semibold text-wisag-gray600 uppercase tracking-wider mb-2">
        {t('sidebar.filters')}
      </h3>

      {regions.length > 0 && (
        <MultiFilter
          label={t('filter.region')}
          options={regions}
          selected={filters.regions ?? regions}
          onChange={(sel) => setFilters({ regions: sel.length === regions.length ? null : sel })}
        />
      )}

      {services.length > 0 && (
        <MultiFilter
          label={t('filter.service')}
          options={services}
          selected={filters.services ?? services}
          onChange={(sel) => setFilters({ services: sel.length === services.length ? null : sel })}
        />
      )}

      {period_min && period_max && (
        <div className="mt-3">
          <label className="text-xs font-medium text-wisag-gray600 block mb-1">
            {t('filter.period')}
          </label>
          <div className="flex items-center gap-2">
            <input
              type="date"
              className="wisag-input text-xs"
              value={filters.start ?? period_min}
              min={period_min}
              max={period_max}
              onChange={(e) => setFilters({ start: e.target.value || null })}
            />
            <span className="text-xs text-wisag-gray600">→</span>
            <input
              type="date"
              className="wisag-input text-xs"
              value={filters.end ?? period_max}
              min={period_min}
              max={period_max}
              onChange={(e) => setFilters({ end: e.target.value || null })}
            />
          </div>
        </div>
      )}
    </section>
  );
}

function MultiFilter({
  label, options, selected, onChange,
}: {
  label: string;
  options: string[];
  selected: string[];
  onChange: (sel: string[]) => void;
}) {
  const toggle = (opt: string) => {
    if (selected.includes(opt)) onChange(selected.filter((o) => o !== opt));
    else onChange([...selected, opt]);
  };
  return (
    <div className="mt-3">
      <div className="text-xs font-medium text-wisag-gray600 mb-1">{label}</div>
      <div className="max-h-40 overflow-y-auto space-y-0.5 sidebar-scroll">
        {options.map((opt) => (
          <label
            key={opt}
            className="flex items-center gap-2 text-xs cursor-pointer px-1.5 py-1 rounded hover:bg-wisag-gray100"
          >
            <input
              type="checkbox"
              checked={selected.includes(opt)}
              onChange={() => toggle(opt)}
              className="accent-wisag-orange"
            />
            <span className="truncate">{opt}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
