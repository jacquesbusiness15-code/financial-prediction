// Typed fetch wrappers around the FastAPI backend.

import type {
  BaselineMode,
  DeepDiveResponse,
  FacilityOverviewResponse,
  LoadDatasetResponse,
  PlanVsActualResponse,
  PortfolioResponse,
  SimulateTeamSizeRequest,
  SimulateTeamSizeResponse,
  WarningsResponse,
} from './types';

const BASE = ''; // same-origin via next.config.js rewrites

type QsValue = string | string[] | undefined | null;

function qs(params: Record<string, QsValue> | FilterParams): string {
  const parts: string[] = [];
  for (const [k, v] of Object.entries(params) as [string, QsValue][]) {
    if (v == null) continue;
    if (Array.isArray(v)) {
      for (const item of v) parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(item)}`);
    } else {
      parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
    }
  }
  return parts.length ? '?' + parts.join('&') : '';
}

async function okOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      detail = await res.text();
    }
    throw new Error(`${res.status}: ${detail || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export interface FilterParams {
  regions?: string[];
  services?: string[];
  start?: string;
  end?: string;
}

export const api = {
  async postDataset(source: string): Promise<LoadDatasetResponse> {
    const res = await fetch(`${BASE}/api/datasets`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ source }),
    });
    return okOrThrow<LoadDatasetResponse>(res);
  },

  async getSummary(datasetId: string): Promise<LoadDatasetResponse> {
    const res = await fetch(`${BASE}/api/datasets/${datasetId}/summary`);
    return okOrThrow<LoadDatasetResponse>(res);
  },

  async getPortfolio(datasetId: string, f: FilterParams): Promise<PortfolioResponse> {
    const res = await fetch(`${BASE}/api/datasets/${datasetId}/portfolio${qs(f)}`);
    return okOrThrow<PortfolioResponse>(res);
  },

  async getDeepDive(
    datasetId: string,
    costCenterId: string,
    mode: BaselineMode,
    period?: string | null,
  ): Promise<DeepDiveResponse> {
    const res = await fetch(
      `${BASE}/api/datasets/${datasetId}/deep-dive/${encodeURIComponent(costCenterId)}` +
      qs({ mode, period: period ?? undefined }),
    );
    return okOrThrow<DeepDiveResponse>(res);
  },

  async getWarnings(datasetId: string, f: FilterParams): Promise<WarningsResponse> {
    const res = await fetch(`${BASE}/api/datasets/${datasetId}/early-warnings${qs(f)}`);
    return okOrThrow<WarningsResponse>(res);
  },

  async getPlanVsActual(datasetId: string, f: FilterParams): Promise<PlanVsActualResponse> {
    const res = await fetch(`${BASE}/api/datasets/${datasetId}/plan-vs-actual${qs(f)}`);
    return okOrThrow<PlanVsActualResponse>(res);
  },

  async getFacilityOverview(
    datasetId: string,
    cc?: string | null,
    period?: string | null,
  ): Promise<FacilityOverviewResponse> {
    const res = await fetch(
      `${BASE}/api/datasets/${datasetId}/facility-overview` +
      qs({ cc: cc ?? undefined, period: period ?? undefined }),
    );
    return okOrThrow<FacilityOverviewResponse>(res);
  },

  async simulateTeamSize(
    datasetId: string,
    body: SimulateTeamSizeRequest,
  ): Promise<SimulateTeamSizeResponse> {
    const res = await fetch(
      `${BASE}/api/datasets/${datasetId}/simulate-team-size`,
      {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      },
    );
    return okOrThrow<SimulateTeamSizeResponse>(res);
  },
};

/** Consume an SSE stream from a POST. Calls `onDelta` for each event, onDone
 *  when the `done` event arrives, and onError on transport failure. */
export async function streamSSE(
  url: string,
  init: RequestInit,
  handlers: {
    onDelta: (text: string) => void;
    onDone?: () => void;
    onError?: (message: string) => void;
  },
): Promise<void> {
  const res = await fetch(url, init);
  if (!res.ok || !res.body) {
    const msg = `${res.status}: ${await res.text().catch(() => res.statusText)}`;
    handlers.onError?.(msg);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let splitAt: number;
    while ((splitAt = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, splitAt);
      buffer = buffer.slice(splitAt + 2);

      let event = 'message';
      let data = '';
      for (const line of raw.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        else if (line.startsWith('data:')) data += line.slice(5).trim();
      }
      if (!data) continue;

      if (event === 'delta') {
        try {
          const parsed = JSON.parse(data) as { text?: string };
          if (parsed.text) handlers.onDelta(parsed.text);
        } catch {
          handlers.onDelta(data);
        }
      } else if (event === 'done') {
        handlers.onDone?.();
      } else if (event === 'error') {
        try {
          const parsed = JSON.parse(data) as { message?: string };
          handlers.onError?.(parsed.message ?? data);
        } catch {
          handlers.onError?.(data);
        }
      }
    }
  }
}
