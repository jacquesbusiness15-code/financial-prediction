'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { LoadDatasetResponse } from './types';

type Ctx = {
  dataset: LoadDatasetResponse | null;
  setDataset: (d: LoadDatasetResponse | null) => void;
  filters: {
    regions: string[] | null;
    services: string[] | null;
    start: string | null;
    end: string | null;
  };
  setFilters: (f: Partial<Ctx['filters']>) => void;
};

const DatasetContext = createContext<Ctx | null>(null);

const LS_KEY = 'wisag.dataset';

export function DatasetProvider({ children }: { children: React.ReactNode }) {
  const [dataset, setDatasetState] = useState<LoadDatasetResponse | null>(null);
  const [filters, setFiltersState] = useState<Ctx['filters']>({
    regions: null, services: null, start: null, end: null,
  });

  // Hydrate from localStorage on mount.
  useEffect(() => {
    try {
      const raw = typeof window !== 'undefined' ? localStorage.getItem(LS_KEY) : null;
      if (raw) setDatasetState(JSON.parse(raw) as LoadDatasetResponse);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    if (!dataset) return;
    setFiltersState((prev) => ({
      regions: prev.regions,
      services: prev.services,
      start: prev.start ?? dataset.facets.period_min,
      end: prev.end ?? dataset.facets.period_max,
    }));
  }, [dataset]);

  const setDataset = useCallback((d: LoadDatasetResponse | null) => {
    setDatasetState(d);
    if (typeof window !== 'undefined') {
      if (d) localStorage.setItem(LS_KEY, JSON.stringify(d));
      else localStorage.removeItem(LS_KEY);
    }
    // Reset filters to the dataset's full facet range.
    if (d) {
      setFiltersState({
        regions: null, services: null,
        start: d.facets.period_min,
        end: d.facets.period_max,
      });
    }
  }, []);

  const setFilters = useCallback((f: Partial<Ctx['filters']>) => {
    setFiltersState((prev) => ({ ...prev, ...f }));
  }, []);

  return (
    <DatasetContext.Provider value={{ dataset, setDataset, filters, setFilters }}>
      {children}
    </DatasetContext.Provider>
  );
}

export function useDataset() {
  const ctx = useContext(DatasetContext);
  if (!ctx) throw new Error('useDataset must be used inside DatasetProvider');
  return ctx;
}
