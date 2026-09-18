import type { ReactNode } from 'react';
import styles from './Badge.module.css';

export interface BadgeProps {
  tone?: 'neutral' | 'success' | 'danger' | 'warning' | 'info';
  children: ReactNode;
}

export function Badge({ tone = 'neutral', children }: BadgeProps) {
  return <span className={`${styles.badge} ${styles[tone]}`}>{children}</span>;
}
