import { useState } from 'preact/hooks';
import type { ComponentChildren } from 'preact';
import { ChevronDown } from 'lucide-preact';
import clsx from 'clsx';

interface AccordionProps {
  children: ComponentChildren;
  className?: string;
}

interface AccordionItemProps {
  value: string;
  children: ComponentChildren;
  className?: string;
}

interface AccordionTriggerProps {
  children: ComponentChildren;
  className?: string;
}

interface AccordionContentProps {
  children: ComponentChildren;
  className?: string;
}

interface AccordionContextType {
  openItems: Set<string>;
  toggleItem: (value: string) => void;
  currentValue?: string;
}

import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

const AccordionContext = createContext<AccordionContextType | null>(null);

export function Accordion({ children, className }: AccordionProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const toggleItem = (value: string) => {
    setOpenItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(value)) {
        newSet.delete(value);
      } else {
        newSet.add(value);
      }
      return newSet;
    });
  };

  return (
    <AccordionContext.Provider value={{ openItems, toggleItem }}>
      <div className={clsx('space-y-2', className)}>
        {children}
      </div>
    </AccordionContext.Provider>
  );
}

export function AccordionItem({ value, children, className }: AccordionItemProps) {
  const context = useContext(AccordionContext);
  if (!context) throw new Error('AccordionItem must be used within Accordion');

  return (
    <AccordionContext.Provider value={{ ...context, currentValue: value }}>
      <div className={clsx('border rounded-lg overflow-hidden', className)}>
        {children}
      </div>
    </AccordionContext.Provider>
  );
}

export function AccordionTrigger({ children, className }: AccordionTriggerProps) {
  const context = useContext(AccordionContext);
  if (!context) throw new Error('AccordionTrigger must be used within AccordionItem');

  const { openItems, toggleItem, currentValue } = context;
  const isOpen = currentValue ? openItems.has(currentValue) : false;

  return (
    <button
      onClick={() => currentValue && toggleItem(currentValue)}
      className={clsx(
        'flex w-full items-center justify-between px-4 py-3 text-left font-medium transition-soft hover:bg-muted/50',
        className
      )}
      aria-expanded={isOpen}
    >
      <span>{children}</span>
      <ChevronDown 
        className={clsx(
          'h-4 w-4 transition-transform duration-200',
          isOpen && 'rotate-180'
        )}
      />
    </button>
  );
}

export function AccordionContent({ children, className }: AccordionContentProps) {
  const context = useContext(AccordionContext);
  if (!context) throw new Error('AccordionContent must be used within AccordionItem');

  const { openItems, currentValue } = context;
  const isOpen = currentValue ? openItems.has(currentValue) : false;

  return (
    <div
      className={clsx(
        'overflow-hidden transition-all duration-200',
        isOpen ? 'animate-accordion-down' : 'animate-accordion-up h-0'
      )}
    >
      <div className={clsx('px-4 pb-4', className)}>
        {children}
      </div>
    </div>
  );
}
