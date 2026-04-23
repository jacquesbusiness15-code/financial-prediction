import './globals.css';
import type { Metadata } from 'next';
import { Sidebar } from '@/components/sidebar/sidebar';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'WISAG Financial Co-Pilot',
  description: 'KI-gestützter Deckungsbeitrags-Copilot für WISAG Facility Services.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 px-6 py-6 overflow-x-hidden">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
