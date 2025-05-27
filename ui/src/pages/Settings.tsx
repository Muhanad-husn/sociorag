import { useState } from 'preact/hooks';
import { useAppStore } from '../hooks/useLocalState';
import { resetCorpus } from '../lib/api';
import { t } from '../lib/i18n';
import { Card } from '../components/ui/Card';
import { Moon, Sun, Settings as SettingsIcon, AlertTriangle, Save } from 'lucide-preact';
import { toast } from 'sonner';
import clsx from 'clsx';

export function Settings() {
  const { isDark, toggleTheme, settings, updateSettings } = useAppStore();
  const [isResetting, setIsResetting] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [tempSettings, setTempSettings] = useState(settings);

  const handleSaveSettings = () => {
    updateSettings(tempSettings);
    toast.success('Settings saved successfully');
  };

  const handleResetDefaults = () => {
    const defaultSettings = {
      topK: 5,
      topKR: 3,
      temperature: 0.7,
      translateToArabic: false,
    };
    setTempSettings(defaultSettings);
    updateSettings(defaultSettings);
    toast.success('Settings reset to defaults');
  };

  const handleResetCorpus = async () => {
    if (!showResetConfirm) {
      setShowResetConfirm(true);
      return;
    }

    setIsResetting(true);
    try {
      const response = await resetCorpus();
      if (response.success) {
        toast.success(response.message || 'Corpus reset successfully');
      } else {
        toast.error(response.message || 'Failed to reset corpus');
      }
    } catch (error) {
      console.error('Reset corpus error:', error);
      toast.error('Failed to reset corpus');
    } finally {
      setIsResetting(false);
      setShowResetConfirm(false);
    }
  };

  const hasUnsavedChanges = JSON.stringify(settings) !== JSON.stringify(tempSettings);

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-3">
          <SettingsIcon className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">{t('settings.title')}</h1>
        </div>

        {/* Unsaved Changes Warning */}
        {hasUnsavedChanges && (
          <Card className="p-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20">
            <div className="flex items-center space-x-2 text-yellow-700 dark:text-yellow-300">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">You have unsaved changes</span>
            </div>
          </Card>
        )}

        {/* Appearance Settings */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">{t('settings.appearance')}</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <label className="text-sm font-medium">{t('settings.darkMode')}</label>
                <p className="text-xs text-muted-foreground">
                  Switch between light and dark themes
                </p>
              </div>
              <button
                onClick={toggleTheme}
                className={clsx(
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                  isDark ? 'bg-primary' : 'bg-gray-200'
                )}
              >
                <span
                  className={clsx(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    isDark ? 'translate-x-6' : 'translate-x-1'
                  )}
                />
                {isDark ? (
                  <Moon className="absolute left-1 h-3 w-3 text-white" />
                ) : (
                  <Sun className="absolute right-1 h-3 w-3 text-gray-400" />
                )}
              </button>
            </div>
          </div>
        </Card>

        {/* Search Settings */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">{t('settings.search')}</h2>
          
          <div className="space-y-6">
            {/* Top K */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('settings.topK')}</label>
              <p className="text-xs text-muted-foreground">
                Number of top results to retrieve (1-20)
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={tempSettings.topK}
                  onChange={(e) => setTempSettings(prev => ({ 
                    ...prev, 
                    topK: parseInt((e.target as HTMLInputElement).value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-8 text-center">
                  {tempSettings.topK}
                </span>
              </div>
            </div>

            {/* Top K Rerank */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('settings.topKR')}</label>
              <p className="text-xs text-muted-foreground">
                Number of results to rerank (1-10)
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={tempSettings.topKR}
                  onChange={(e) => setTempSettings(prev => ({ 
                    ...prev, 
                    topKR: parseInt((e.target as HTMLInputElement).value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-8 text-center">
                  {tempSettings.topKR}
                </span>
              </div>
            </div>

            {/* Temperature */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('settings.temperature')}</label>
              <p className="text-xs text-muted-foreground">
                Controls randomness in responses (0.0-2.0)
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={tempSettings.temperature}
                  onChange={(e) => setTempSettings(prev => ({ 
                    ...prev, 
                    temperature: parseFloat((e.target as HTMLInputElement).value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-12 text-center">
                  {tempSettings.temperature.toFixed(1)}
                </span>
              </div>
            </div>
          </div>

          {/* Save/Reset Buttons */}
          <div className="flex items-center space-x-3 mt-6 pt-4 border-t">
            <button
              onClick={handleSaveSettings}
              disabled={!hasUnsavedChanges}
              className={clsx(
                'btn-primary',
                !hasUnsavedChanges && 'opacity-50 cursor-not-allowed'
              )}
            >
              <Save className="h-4 w-4 mr-2" />
              {t('common.save')}
            </button>
            <button
              onClick={handleResetDefaults}
              className="btn-secondary"
            >
              Reset to Defaults
            </button>
          </div>
        </Card>

        {/* Danger Zone */}
        <Card className="p-6 border-destructive">
          <h2 className="text-xl font-semibold mb-4 text-destructive">Danger Zone</h2>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="font-medium">{t('settings.reset')}</h3>
              <p className="text-sm text-muted-foreground">
                {t('settings.resetConfirm')}
              </p>
            </div>

            {showResetConfirm ? (
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleResetCorpus}
                  disabled={isResetting}
                  className="btn-destructive"
                >
                  {isResetting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2" />
                      Resetting...
                    </>
                  ) : (
                    'Confirm Reset'
                  )}
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="btn-secondary"
                >
                  {t('common.cancel')}
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowResetConfirm(true)}
                className="btn-destructive"
              >
                {t('settings.reset')}
              </button>
            )}
          </div>
        </Card>

        {/* Info */}
        <Card className="p-4 bg-accent/50">
          <h3 className="font-semibold mb-2">About Settings</h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>• Settings are automatically saved to your browser</li>
            <li>• Search settings affect the quality and speed of results</li>
            <li>• Higher Top K values may return more diverse results</li>
            <li>• Lower temperature values produce more focused responses</li>
            <li>• Resetting corpus will delete all uploaded documents</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
