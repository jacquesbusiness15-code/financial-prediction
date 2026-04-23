import clsx from 'clsx';

type Tint = 'purple' | 'orange' | 'red' | 'green' | 'blue' | 'gray';

export function IconTile({
  icon,
  tint = 'gray',
  size = 'md',
  className,
}: {
  icon: string;
  tint?: Tint;
  size?: 'sm' | 'md';
  className?: string;
}) {
  return (
    <span
      className={clsx(
        'wisag-icon-tile',
        `wisag-icon-tile-${tint}`,
        size === 'sm' && 'wisag-icon-tile-sm',
        className,
      )}
      aria-hidden
    >
      {icon}
    </span>
  );
}
