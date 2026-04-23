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
          <div className="app-shell">
            <Sidebar />
            <main className="app-main">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
