import Link from 'next/link';

interface NavCardProps {
  href: string;
  icon: string;
  title: string;
  desc: string;
}

export function NavCard({ href, icon, title, desc }: NavCardProps) {
  return (
    <Link href={href} className="wisag-nav-card">
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-base font-semibold text-wisag-navy mb-1">{title}</div>
      <div className="text-sm text-wisag-gray600 leading-relaxed">{desc}</div>
    </Link>
  );
}
