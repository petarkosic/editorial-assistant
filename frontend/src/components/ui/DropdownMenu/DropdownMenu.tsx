import type { ReactNode } from 'react';
import * as RadixMenu from '@radix-ui/react-dropdown-menu';
import styles from './DropdownMenu.module.css';

export interface DropdownMenuItem {
  label: string;
  onSelect: () => void;
  tone?: 'default' | 'danger';
}

export interface DropdownMenuProps {
  trigger: ReactNode;
  items: DropdownMenuItem[];
  align?: 'start' | 'end';
}

export function DropdownMenu({ trigger, items, align = 'end' }: DropdownMenuProps) {
  return (
    <RadixMenu.Root>
      <RadixMenu.Trigger asChild>{trigger}</RadixMenu.Trigger>
      <RadixMenu.Portal>
        <RadixMenu.Content className={styles.content} align={align} sideOffset={6}>
          {items.map((item) => (
            <RadixMenu.Item
              key={item.label}
              className={styles.item}
              data-tone={item.tone ?? 'default'}
              onSelect={item.onSelect}
            >
              {item.label}
            </RadixMenu.Item>
          ))}
        </RadixMenu.Content>
      </RadixMenu.Portal>
    </RadixMenu.Root>
  );
}
