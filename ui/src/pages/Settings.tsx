import { useState, useEffect } from 'preact/hooks';
import { useAppStore } from '../hooks/useLocalState';
import { resetCorpus, getSystemConfig, getSystemHealth, updateApiKeys, updateLLMSettings, getLLMSettings } from '../lib/api';
import type { SystemConfig, HealthStatus, ApiKeyUpdate } from '../lib/api';
import { t } from              <p className="text-xs text-muted-foreground">
                Number of top results to retrieve from vector store (5-250)
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="5"
                  max="250"/i18n';
import { Card } from '../components/ui/Card';
import { Moon, Sun, Settings as SettingsIcon, AlertTriangle, Save, Shield, CheckCircle, XCircle, RefreshCw } from 'lucide-preact';
import { toast } from 'sonner';
import clsx from 'clsx';

export function Settings() {
  const { isDark, toggleTheme, settings, updateSettings } = useAppStore();
  const [isResetting, setIsResetting] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [tempSettings, setTempSettings] = useState(settings);  // Admin state
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [loadingAdmin, setLoadingAdmin] = useState(false);
  
  // LLM settings loading state
  const [loadingLLMSettings, setLoadingLLMSettings] = useState(false);
  
  // API Key editing state
  const [editingApiKey, setEditingApiKey] = useState(false);
  const [newApiKey, setNewApiKey] = useState('');
  const [savingApiKey, setSavingApiKey] = useState(false);
  // Load admin data on component mount
  useEffect(() => {
    loadAdminData();
    loadLLMSettings();
  }, []);

  const loadAdminData = async () => {
    setLoadingAdmin(true);
    try {
      const [config, health] = await Promise.all([
        getSystemConfig(),
        getSystemHealth()
      ]);
      setSystemConfig(config);
      setHealthStatus(health);
    } catch (error) {
      console.error('Failed to load admin data:', error);
      toast.error('Failed to load system information');
    } finally {
      setLoadingAdmin(false);
    }
  };
  const loadLLMSettings = async () => {
    setLoadingLLMSettings(true);
    try {
      const response = await getLLMSettings();
      if (response.success) {
        // Update tempSettings with backend values if they exist        setTempSettings(prev => ({
          ...prev,
          entityModel: response.data.entity_llm_model || prev.entityModel,
          answerModel: response.data.answer_llm_model || prev.answerModel,
          translateModel: response.data.translate_llm_model || prev.translateModel,
          temperature: response.data.answer_llm_temperature !== undefined ? response.data.answer_llm_temperature : prev.temperature,
          maxTokensAnswer: response.data.answer_llm_max_tokens || prev.maxTokensAnswer,
          contextWindow: response.data.answer_llm_context_window || prev.contextWindow,
          topK: response.data.top_k || prev.topK,
          topKR: response.data.top_k_rerank || prev.topKR,
        }));
      }
    } catch (error) {
      console.error('Failed to load LLM settings:', error);
      toast.error('Failed to load LLM settings');
    } finally {
      setLoadingLLMSettings(false);
    }
  };const handleSaveSettings = async () => {
    // Update local settings
    updateSettings(tempSettings);
    
    // Update LLM settings on the backend
    try {
      // Only send changed LLM-related settings to the backend      const llmSettingsToUpdate = {
        entity_llm_model: tempSettings.entityModel !== settings.entityModel ? tempSettings.entityModel : undefined,
        answer_llm_model: tempSettings.answerModel !== settings.answerModel ? tempSettings.answerModel : undefined,
        translate_llm_model: tempSettings.translateModel !== settings.translateModel ? tempSettings.translateModel : undefined,
        answer_llm_temperature: tempSettings.temperature !== settings.temperature ? tempSettings.temperature : undefined,
        answer_llm_max_tokens: tempSettings.maxTokensAnswer !== settings.maxTokensAnswer ? tempSettings.maxTokensAnswer : undefined,
        answer_llm_context_window: tempSettings.contextWindow !== settings.contextWindow ? tempSettings.contextWindow : undefined,
        top_k: tempSettings.topK !== settings.topK ? tempSettings.topK : undefined,
        top_k_rerank: tempSettings.topKR !== settings.topKR ? tempSettings.topKR : undefined
      };
      
      // Only make API call if there are settings to update
      if (Object.values(llmSettingsToUpdate).some(val => val !== undefined)) {
        const response = await updateLLMSettings(llmSettingsToUpdate);
        if (response.success) {
          toast.success('Settings saved successfully on the server');
          // Reload LLM settings to confirm the update
          await loadLLMSettings();
        } else {
          toast.error('Failed to save LLM settings on the server');
        }
      } else {
        toast.success('Settings saved successfully');
      }
    } catch (error) {
      console.error('Failed to update LLM settings:', error);
      toast.error('Failed to save LLM settings on the server');
    }
  };  const handleResetDefaults = () => {
    const defaultSettings = {
      topK: 80,
      topKR: 15,
      temperature: 0.5,
      translateToArabic: false,
      entityModel: "google/gemini-flash-1.5",
      answerModel: "meta-llama/llama-3.3-70b-instruct:free",
      translateModel: "mistralai/mistral-nemo:free",
      maxTokensAnswer: 4000,
      contextWindow: 128000,
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

  const handleApiKeyUpdate = async () => {
    if (!newApiKey.trim()) {
      toast.error('Please enter a valid API key');
      return;
    }    setSavingApiKey(true);
    try {
      const apiKeyData: ApiKeyUpdate = {
        openrouter_api_key: newApiKey.trim()
      };
      const response = await updateApiKeys(apiKeyData);
      
      if (response.success) {
        toast.success(response.message || 'API key updated successfully');
        setEditingApiKey(false);
        setNewApiKey('');
        // Reload admin data to show updated status
        await loadAdminData();
      } else {
        toast.error('Failed to update API key');
      }
    } catch (error) {
      console.error('Failed to update API key:', error);
      toast.error('Failed to update API key');
    } finally {
      setSavingApiKey(false);
    }
  };

  const handleCancelApiKeyEdit = () => {
    setEditingApiKey(false);
    setNewApiKey('');
  };

  const hasUnsavedChanges = JSON.stringify(settings) !== JSON.stringify(tempSettings);
  // Helper function to check if model selections have changed
  const hasModelChanges = () => {
    return tempSettings.entityModel !== settings.entityModel ||
           tempSettings.answerModel !== settings.answerModel ||
           tempSettings.translateModel !== settings.translateModel;
  };

  // Helper function to validate model selections
  const validateModelSelections = () => {
    const errors = [];
    if (!tempSettings.entityModel.trim()) {
      errors.push("Entity extraction model cannot be empty");
    }
    if (!tempSettings.answerModel.trim()) {
      errors.push("Answer generation model cannot be empty");
    }
    if (!tempSettings.translateModel.trim()) {
      errors.push("Translation model cannot be empty");
    }
    return errors;
  };

  // Helper function to get default models
  const getDefaultModels = () => ({
    entityModel: "google/gemini-flash-1.5",
    answerModel: "meta-llama/llama-3.3-70b-instruct:free",
    translateModel: "mistralai/mistral-nemo:free"
  });

  // Handler for confirming model selection
  const handleConfirmModelSelection = async () => {
    // Validate model selections
    const validationErrors = validateModelSelections();
    if (validationErrors.length > 0) {
      toast.error(`Please fix the following issues:\n${validationErrors.join('\n')}`);
      return;
    }

    try {
      // Only update model-related settings
      const modelSettings = {
        entityModel: tempSettings.entityModel.trim(),
        answerModel: tempSettings.answerModel.trim(),
        translateModel: tempSettings.translateModel.trim()
      };
      
      // Update local settings
      updateSettings(modelSettings);
      
      // Update backend with LLM settings
      const llmSettingsToUpdate = {
        entity_llm_model: tempSettings.entityModel !== settings.entityModel ? tempSettings.entityModel.trim() : undefined,
        answer_llm_model: tempSettings.answerModel !== settings.answerModel ? tempSettings.answerModel.trim() : undefined,
        translate_llm_model: tempSettings.translateModel !== settings.translateModel ? tempSettings.translateModel.trim() : undefined
      };
      
      // Only make API call if there are model settings to update
      if (Object.values(llmSettingsToUpdate).some(val => val !== undefined)) {
        const response = await updateLLMSettings(llmSettingsToUpdate);
        if (response.success) {
          toast.success('Model selection confirmed successfully! Note: Server restart may be required for changes to take effect.');
          // Reload LLM settings to confirm the update
          await loadLLMSettings();
        } else {
          toast.error('Failed to save model selection to server');
        }
      } else {
        toast.success('Model selection confirmed!');
      }
    } catch (error) {
      console.error('Failed to confirm model selection:', error);
      toast.error('Failed to confirm model selection');
    }
  };

  // Handler for resetting model selections to defaults
  const handleResetModelsToDefaults = () => {
    const defaults = getDefaultModels();
    setTempSettings(prev => ({
      ...prev,
      ...defaults
    }));
    toast.success('Model selections reset to system defaults');
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-3">
          <SettingsIcon className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">{t('settings.title')}</h1>
        </div>        {/* Unsaved Changes Warning */}
        {hasUnsavedChanges && (
          <Card className="p-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20">
            <div className="flex items-center space-x-2 text-yellow-700 dark:text-yellow-300">
              <AlertTriangle className="h-4 w-4" />
              <div className="space-y-1">
                <span className="text-sm font-medium">You have unsaved changes</span>
                {hasModelChanges() && (
                  <p className="text-xs">
                    Model selections need to be confirmed. Use the "Confirm Selection" button in the Model Selection panel.
                  </p>
                )}
              </div>
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
          
          <div className="space-y-6">            {/* Top K */}            <div className="space-y-2">
              <label className="text-sm font-medium">{t('settings.topK')}</label>
              <p className="text-xs text-muted-foreground">
                Number of top results to retrieve from vector store (5-250)
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="5"
                  max="250"
                  value={tempSettings.topK}
                  onChange={(e) => setTempSettings(prev => ({ 
                    ...prev, 
                    topK: parseInt((e.target as HTMLInputElement).value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-12 text-center">
                  {tempSettings.topK}
                </span>
              </div>
            </div>{/* Top K Rerank */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('settings.topKR')}</label>              <p className="text-xs text-muted-foreground">
                Number of results to rerank and display (3-100)
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="3"
                  max="100"
                  value={tempSettings.topKR}
                  onChange={(e) => setTempSettings(prev => ({ 
                    ...prev, 
                    topKR: parseInt((e.target as HTMLInputElement).value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-12 text-center">
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
          </div>        </Card>        {/* Model Selection */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Model Selection</h2>
            {loadingLLMSettings && (
              <div className="animate-spin rounded-full h-4 w-4 border-b border-primary" />
            )}
          </div>
          
          <div className="space-y-6">            {/* Entities and Relationships Extraction Model */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Entities and Relationships Extraction Model</label>
              <p className="text-xs text-muted-foreground">
                Model used for extracting entities and relationships (Default: google/gemini-flash-1.5)
              </p>
              <input
                type="text"
                value={tempSettings.entityModel}
                onChange={(e) => setTempSettings(prev => ({ 
                  ...prev, 
                  entityModel: (e.target as HTMLInputElement).value 
                }))}
                placeholder="google/gemini-flash-1.5"
                className={clsx(
                  "w-full px-3 py-2 text-sm border rounded-md bg-background focus:ring-2 focus:ring-primary focus:border-transparent",
                  !tempSettings.entityModel.trim() ? "border-red-500" : "border-border"
                )}
              />
              {!tempSettings.entityModel.trim() && (
                <p className="text-xs text-red-500">Entity extraction model is required</p>
              )}
            </div>            {/* Answer Generation Model */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Answer Generation Model</label>
              <p className="text-xs text-muted-foreground">
                Model used for generating answers to questions (Default: meta-llama/llama-3.3-70b-instruct:free)
              </p>
              <input
                type="text"
                value={tempSettings.answerModel}
                onChange={(e) => setTempSettings(prev => ({ 
                  ...prev, 
                  answerModel: (e.target as HTMLInputElement).value 
                }))}
                placeholder="meta-llama/llama-3.3-70b-instruct:free"
                className={clsx(
                  "w-full px-3 py-2 text-sm border rounded-md bg-background focus:ring-2 focus:ring-primary focus:border-transparent",
                  !tempSettings.answerModel.trim() ? "border-red-500" : "border-border"
                )}
              />
              {!tempSettings.answerModel.trim() && (
                <p className="text-xs text-red-500">Answer generation model is required</p>
              )}
            </div>            {/* Translation Model */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Translation Model</label>
              <p className="text-xs text-muted-foreground">
                Model used for language translation (Default: mistralai/mistral-nemo:free)
              </p>
              <input
                type="text"
                value={tempSettings.translateModel}
                onChange={(e) => setTempSettings(prev => ({ 
                  ...prev, 
                  translateModel: (e.target as HTMLInputElement).value 
                }))}
                placeholder="mistralai/mistral-nemo:free"
                className={clsx(
                  "w-full px-3 py-2 text-sm border rounded-md bg-background focus:ring-2 focus:ring-primary focus:border-transparent",
                  !tempSettings.translateModel.trim() ? "border-red-500" : "border-border"
                )}
              />
              {!tempSettings.translateModel.trim() && (
                <p className="text-xs text-red-500">Translation model is required</p>
              )}
            </div>
          </div>          {/* Model Selection Confirmation */}
          <div className="flex items-center justify-between mt-6 pt-4 border-t">
            <div className="space-y-1">
              <p className="text-sm font-medium">Confirm Model Selection</p>
              <p className="text-xs text-muted-foreground">
                {hasModelChanges() ? 
                  "Click 'Confirm Selection' to apply your model choices" :
                  "Model selections are up to date"}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleResetModelsToDefaults}
                className="btn-secondary text-xs px-3 py-1"
                title="Reset to default models"
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Reset
              </button>
              <button
                onClick={handleConfirmModelSelection}
                disabled={!hasModelChanges() || loadingLLMSettings}
                className={clsx(
                  'btn-primary flex items-center',
                  !hasModelChanges() && 'opacity-50 cursor-not-allowed'
                )}
              >
                {loadingLLMSettings ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Confirm Selection
              </button>
            </div>
          </div>
        </Card>

        {/* Advanced Settings */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Advanced Settings</h2>
          
          <div className="space-y-6">
            {/* Max Tokens for Answer */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Tokens (Answer)</label>
              <p className="text-xs text-muted-foreground">
                Maximum tokens for answer generation (1000-8000)
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="1000"
                  max="8000"
                  step="500"
                  value={tempSettings.maxTokensAnswer}
                  onChange={(e) => setTempSettings(prev => ({ 
                    ...prev, 
                    maxTokensAnswer: parseInt((e.target as HTMLInputElement).value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-16 text-center">
                  {tempSettings.maxTokensAnswer}
                </span>
              </div>
            </div>

            {/* Context Window */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Context Window</label>
              <p className="text-xs text-muted-foreground">
                Context window size for large models (16K-128K)
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="16000"
                  max="128000"
                  step="16000"
                  value={tempSettings.contextWindow}
                  onChange={(e) => setTempSettings(prev => ({ 
                    ...prev, 
                    contextWindow: parseInt((e.target as HTMLInputElement).value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-16 text-center">
                  {Math.round(tempSettings.contextWindow / 1000)}K
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* System Configuration */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-primary" />
              <h2 className="text-xl font-semibold">System Configuration</h2>
            </div>
            <button
              onClick={loadAdminData}
              disabled={loadingAdmin}
              className="btn-secondary p-2"
              title="Refresh system information"
            >
              <RefreshCw className={clsx('h-4 w-4', loadingAdmin && 'animate-spin')} />
            </button>
          </div>

          {loadingAdmin ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b border-primary" />
              <span className="ml-2 text-sm text-muted-foreground">Loading system information...</span>
            </div>
          ) : (
            <div className="space-y-4">              {/* OpenRouter API Key Status */}
              <div className="p-3 bg-accent/50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">OpenRouter API Key</label>
                    <p className="text-xs text-muted-foreground">
                      Required for AI-powered responses
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {systemConfig?.config_values?.openrouter_api_key_configured ? (
                      <>
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <span className="text-sm font-medium text-green-700 dark:text-green-400">
                          Configured
                        </span>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-5 w-5 text-red-500" />
                        <span className="text-sm font-medium text-red-700 dark:text-red-400">
                          Not Configured
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* API Key Input/Edit Section */}
                {editingApiKey ? (
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-muted-foreground">
                        Enter OpenRouter API Key:
                      </label>
                      <input
                        type="password"
                        value={newApiKey}
                        onChange={(e) => setNewApiKey((e.target as HTMLInputElement).value)}
                        placeholder="sk-or-v1-..."
                        className="w-full px-3 py-2 text-sm border border-border rounded-md bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
                        disabled={savingApiKey}
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={handleApiKeyUpdate}
                        disabled={savingApiKey || !newApiKey.trim()}
                        className={clsx(
                          'btn-primary text-xs',
                          (savingApiKey || !newApiKey.trim()) && 'opacity-50 cursor-not-allowed'
                        )}
                      >
                        {savingApiKey ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border-b border-white mr-1" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="h-3 w-3 mr-1" />
                            Save Key
                          </>
                        )}
                      </button>
                      <button
                        onClick={handleCancelApiKeyEdit}
                        disabled={savingApiKey}
                        className="btn-secondary text-xs"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {systemConfig?.config_values?.openrouter_api_key_configured 
                        ? 'API key is configured and ready to use'
                        : 'No API key configured'
                      }
                    </span>
                    <button
                      onClick={() => setEditingApiKey(true)}
                      className="btn-secondary text-xs"
                    >
                      {systemConfig?.config_values?.openrouter_api_key_configured ? 'Update' : 'Configure'}
                    </button>
                  </div>
                )}
              </div>

              {/* System Status */}
              <div className="flex items-center justify-between p-3 bg-accent/50 rounded-lg">
                <div className="space-y-1">
                  <label className="text-sm font-medium">System Status</label>
                  <p className="text-xs text-muted-foreground">
                    Overall system health
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  {healthStatus?.status === 'healthy' ? (
                    <>
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <span className="text-sm font-medium text-green-700 dark:text-green-400">
                        Healthy
                      </span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                      <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                        {healthStatus?.status || 'Unknown'}
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Configuration Notice */}
              {!systemConfig?.config_values?.openrouter_api_key_configured && (
                <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                        API Key Required
                      </p>
                      <p className="text-xs text-yellow-700 dark:text-yellow-300">
                        The OPENROUTER_API_KEY must be configured in the .env file for AI responses to work. 
                        Contact your system administrator to configure this setting.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
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
