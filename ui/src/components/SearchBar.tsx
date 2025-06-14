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
  language?: 'en' | 'ar';
}

export function SearchBar({ value, onChange, onSubmit, disabled = false, language }: SearchBarProps) {
  const { settings, updateSettings, language: appLanguage } = useAppStore();
  const currentLanguage = language || appLanguage;
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
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />          <textarea
            value={value}
            onChange={(e) => onChange((e.target as HTMLTextAreaElement).value)}
            onKeyDown={handleKeyDown}
            placeholder={t('search.placeholder', currentLanguage)}
            disabled={disabled}
            className={clsx(
              'w-full px-3 py-2 text-sm rounded-md border border-input bg-background',
              'input-enhanced pl-10 pr-12 resize-none min-h-[44px] max-h-32',
              'transition-all duration-200 ring-offset-background',
              'placeholder:text-muted-foreground',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              disabled && 'opacity-50 cursor-not-allowed disabled:cursor-not-allowed'
            )}
            rows={5}
            onFocus={() => setIsExpanded(true)}
            onBlur={() => setIsExpanded(false)}
            style={{
              height: isExpanded ? 'auto' : 'auto',
              minHeight: '44px'
            }}
          /><button
            type="submit"
            disabled={!value.trim() || disabled}
            className={clsx(
              'absolute right-2 top-1/2 transform -translate-y-1/2',
              'btn-primary h-8 w-8 p-0 hover-scale active-press focus-ring-enhanced',
              (!value.trim() || disabled) && 'opacity-50 cursor-not-allowed'
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>

      <div className="flex items-center justify-between">        <label className="flex items-center space-x-2 cursor-pointer hover-lift">
          <input
            type="checkbox"
            checked={settings.translateToArabic}
            onChange={(e) => updateSettings({ translateToArabic: (e.target as HTMLInputElement).checked })}
            className="rounded border text-primary focus:ring-primary focus-ring-enhanced"
          />
          <span className="text-sm text-muted-foreground">
            {t('search.translate', currentLanguage)}
          </span>
        </label>

        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <span>{t('search.enterHint', currentLanguage)}</span>
        </div>
      </div>
    </div>
  );
}
