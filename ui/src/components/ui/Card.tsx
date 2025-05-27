import type { ComponentChildren } from 'preact';
import clsx from 'clsx';

interface CardProps {
  children: ComponentChildren;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={clsx('card', className)}>
      {children}
    </div>
  );
}
