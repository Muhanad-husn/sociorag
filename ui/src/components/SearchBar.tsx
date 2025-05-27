import { useState } from 'preact/hooks';
import { Search, Send } from 'lucide-preact';
import { useAppStore } from '../hooks/useLocalState';
import { t } from '../lib/i18n';
import clsx from 'clsx';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export function SearchBar({ value, onChange, onSubmit, disabled = false }: SearchBarProps) {
  const { settings, updateSettings } = useAppStore();
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSubmit = (e: Event) => {
    e.preventDefault();
    if (value.trim() && !disabled) {
      onSubmit();
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full space-y-4">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <textarea
            value={value}
            onChange={(e) => onChange((e.target as HTMLTextAreaElement).value)}
            onKeyDown={handleKeyDown}
            placeholder={t('search.placeholder')}
            disabled={disabled}
            className={clsx(
              'input pl-10 pr-12 resize-none min-h-[44px] max-h-32',
              'transition-all duration-200',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            rows={1}
            onFocus={() => setIsExpanded(true)}
            onBlur={() => setIsExpanded(false)}
            style={{
              height: isExpanded ? 'auto' : '44px',
              minHeight: '44px'
            }}
          />
          <button
            type="submit"
            disabled={!value.trim() || disabled}
            className={clsx(
              'absolute right-2 top-1/2 transform -translate-y-1/2',
              'btn-primary h-8 w-8 p-0',
              'transition-all duration-200',
              (!value.trim() || disabled) && 'opacity-50 cursor-not-allowed'
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>

      <div className="flex items-center justify-between">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.translateToArabic}
            onChange={(e) => updateSettings({ translateToArabic: (e.target as HTMLInputElement).checked })}
            className="rounded border text-primary focus:ring-primary"
          />
          <span className="text-sm text-muted-foreground">
            {t('search.translate')}
          </span>
        </label>

        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <span>Press Enter to search</span>
        </div>
      </div>
    </div>
  );
}
