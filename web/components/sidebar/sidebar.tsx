'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { DatasetSource } from './dataset-source';
import { Filters } from './filters';
import { t } from '@/lib/i18n';

type NavItem = { href: string; labelKey: string; icon: string };

const NAV: NavItem[] = [
  { href: '/',               labelKey: 'nav.home',          icon: '🏠' },
  { href: '/portfolio',      labelKey: 'nav.portfolio',     icon: '📈' },
  { href: '/deep-dive',      labelKey: 'nav.deepdive',      icon: '🔎' },
  { href: '/early-warnings', labelKey: 'nav.warnings',      icon: '⚠️' },
  { href: '/plan-vs-actual', labelKey: 'nav.plan_vs_actual', icon: '📐' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 bg-white border-r border-wisag-gray300 px-4 py-5 overflow-y-auto sidebar-scroll flex flex-col">
      <div className="mb-6">
        <div className="text-xl font-bold text-wisag-orange tracking-tight">WISAG</div>
        <div className="text-xs text-wisag-gray600 uppercase tracking-wider">Co-Pilot</div>
      </div>

      <nav className="mb-6">
        <ul className="space-y-0.5">
          {NAV.map((n) => {
            const active = pathname === n.href;
            return (
              <li key={n.href}>
                <Link
                  href={n.href}
                  className={clsx(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition',
                    active
                      ? 'bg-wisag-orangeLight text-wisag-orangeDark font-semibold'
                      : 'text-wisag-navy hover:bg-wisag-gray100',
                  )}
                >
                  <span className="text-base leading-none w-5 text-center" aria-hidden>
                    {n.icon}
                  </span>
                  <span className="flex-1">{t(n.labelKey)}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <details className="mb-4 group">
        <summary className="text-xs font-semibold text-wisag-gray600 uppercase tracking-wider cursor-pointer select-none hover:text-wisag-navy">
          {t('sidebar.settings')}
        </summary>
        <div className="mt-3 space-y-4">
          <DatasetSource />
          <Filters />
        </div>
      </details>

      <div className="mt-auto pt-4 border-t border-wisag-gray200">
        <Link
          href="/chat"
          className={clsx(
            'wisag-ask-ai',
            pathname === '/chat' && 'bg-wisag-orangeLight',
          )}
        >
          <span className="flex items-center gap-2">
            <span aria-hidden>✨</span>
            {t('overview.ask_ai')}
          </span>
          <span aria-hidden>→</span>
        </Link>
      </div>
    </aside>
  );
}
