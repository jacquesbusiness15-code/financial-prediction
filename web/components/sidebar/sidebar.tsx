'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { DatasetSource } from './dataset-source';
import { Filters } from './filters';
import { t } from '@/lib/i18n';

const NAV = [
  { href: '/',               labelKey: 'nav.home' },
  { href: '/portfolio',      labelKey: 'nav.portfolio' },
  { href: '/deep-dive',      labelKey: 'nav.deepdive' },
  { href: '/early-warnings', labelKey: 'nav.warnings' },
  { href: '/plan-vs-actual', labelKey: 'nav.plan_vs_actual' },
  { href: '/chat',           labelKey: 'nav.chat' },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-72 shrink-0 bg-white border-r border-wisag-gray300 px-4 py-5 overflow-y-auto sidebar-scroll">
      <div className="mb-5">
        <div className="text-lg font-bold text-wisag-orange tracking-tight">WISAG</div>
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
                    'block rounded-md px-3 py-2 text-sm transition',
                    active
                      ? 'bg-wisag-orangeLight text-wisag-orangeDark font-semibold border-l-4 border-wisag-orange pl-2'
                      : 'text-wisag-navy hover:bg-wisag-gray100',
                  )}
                >
                  {t(n.labelKey)}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <DatasetSource />

      <div className="mt-6">
        <Filters />
      </div>
    </aside>
  );
}
