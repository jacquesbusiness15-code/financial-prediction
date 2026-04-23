'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { DatasetProvider } from '@/lib/dataset-context';

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
  }));
  return (
    <QueryClientProvider client={client}>
      <DatasetProvider>{children}</DatasetProvider>
    </QueryClientProvider>
  );
}
