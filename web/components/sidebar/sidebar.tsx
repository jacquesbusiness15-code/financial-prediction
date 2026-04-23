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
  { href: '/chat',           labelKey: 'nav.chat',          icon: '✨' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar-scroll border-b border-white/10 bg-[#06101D]/92 px-4 py-4 backdrop-blur-xl lg:h-screen lg:w-80 lg:shrink-0 lg:border-b-0 lg:border-r lg:border-white/10 lg:px-5 lg:py-5 lg:sticky lg:top-0 lg:overflow-y-auto">
      <div className="flex h-full flex-col gap-5">
        <div className="surface-card p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-wisag-orange/30 bg-wisag-orange/12 text-lg font-bold text-white">
              W
            </div>
            <div className="min-w-0">
              <div className="text-lg font-extrabold tracking-tight text-wisag-navy">WISAG Co-Pilot</div>
              <div className="text-xs uppercase tracking-[0.28em] text-wisag-gray600">
                Finance Command Center
              </div>
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-wisag-gray600">
            Executive view for margin, risk drivers, and action planning in one place.
          </p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="surface-card-subtle">
              <div className="soft-label">Mode</div>
              <div className="mt-1 text-sm font-semibold text-wisag-navy">Live prototype</div>
            </div>
            <div className="surface-card-subtle">
              <div className="soft-label">Focus</div>
              <div className="mt-1 text-sm font-semibold text-wisag-navy">Margin health</div>
            </div>
          </div>
        </div>

        <nav className="surface-card p-3">
          <div className="soft-label mb-3 px-2">Navigation</div>
          <ul className="space-y-1.5">
            {NAV.map((n) => {
              const active = pathname === n.href;
              return (
                <li key={n.href}>
                  <Link
                    href={n.href}
                    className={clsx(
                      'flex items-center gap-3 rounded-2xl px-3 py-3 text-sm transition',
                      active
                        ? 'bg-white/[0.08] text-white ring-1 ring-wisag-orange/30'
                        : 'text-wisag-gray600 hover:bg-white/[0.05] hover:text-white',
                    )}
                  >
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.06] text-base leading-none" aria-hidden>
                      {n.icon}
                    </span>
                    <span className="flex-1 font-medium">{t(n.labelKey)}</span>
                    {active && <span className="text-xs font-semibold text-wisag-orange">Live</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <details className="surface-card group open:shadow-[0_18px_44px_rgba(0,0,0,0.22)]">
          <summary className="flex cursor-pointer list-none items-center justify-between select-none rounded-2xl px-1 text-sm font-semibold text-wisag-navy">
            <span>Controls</span>
            <span className="text-wisag-gray600 transition group-open:rotate-180">⌄</span>
          </summary>
          <div className="mt-4 space-y-4">
            <DatasetSource />
            <Filters />
          </div>
        </details>

        <div className="surface-card mt-auto p-4">
          <div className="soft-label mb-2">Co-Pilot</div>
          <p className="mb-4 text-sm leading-6 text-wisag-gray600">
            Ask direct questions about weak regions, plan gaps, and operational drivers.
          </p>
          <Link
            href="/chat"
            className={clsx(
              'wisag-ask-ai',
              pathname === '/chat' && 'bg-wisag-orange/20',
            )}
          >
            <span className="flex items-center gap-2">
              <span aria-hidden>✨</span>
              {t('overview.ask_ai')}
            </span>
            <span aria-hidden>→</span>
          </Link>
        </div>
      </div>
    </aside>
  );
}
