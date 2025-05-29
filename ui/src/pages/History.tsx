import { useState, useEffect } from 'preact/hooks';
import { getHistory, askQuestion, type AskResponse } from '../lib/api';
import { useAsyncRequest } from '../hooks/useAsyncRequest';
import { useAppStore } from '../hooks/useLocalState';
import { StreamAnswer } from '../components/StreamAnswer';
import { t } from '../lib/i18n';
import { Card } from '../components/ui/Card';
import { Play, Trash2, Clock, MessageSquare } from 'lucide-preact';
import { toast } from 'sonner';

interface HistoryItem {
  id: string;
  query: string;
  answer: string;
  timestamp: string;
  language: string;
}

export function History() {
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
  const [rerunAnswer, setRerunAnswer] = useState('');
  const { settings, language } = useAppStore();
  const { execute: executeRerun, loading: isRerunning, error } = useAsyncRequest<AskResponse>();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await getHistory(1, 15);
      setHistoryItems(response.items);
    } catch (error) {
      console.error('Failed to load history:', error);
      toast.error(t('history.loadFailed', language));
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async (item: HistoryItem) => {
    setSelectedItem(item);
    setRerunAnswer('');
    
    try {
      const response = await executeRerun(() => askQuestion(item.query, settings));
      if (response) {
        setRerunAnswer(response.answer);
      }
    } catch (err) {
      console.error('Rerun error:', err);
      setRerunAnswer('');
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-2">{t('common.loading', language)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">{t('history.title', language)}</h1>
          <button
            onClick={loadHistory}
            className="btn-secondary"
          >
            {t('history.refresh', language)}
          </button>
        </div>

        {/* Rerun Results */}
        {selectedItem && (rerunAnswer || error) && (
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{t('history.rerunResults', language)}</h3>
                <button
                  onClick={() => {
                    setSelectedItem(null);
                    setRerunAnswer('');
                  }}
                  className="btn-secondary"
                >
                  {t('common.close', language)}
                </button>
              </div>
              
              <div className="p-3 bg-accent rounded border-l-4 border-primary">
                <p className="text-sm font-medium">{t('history.originalQuery', language)}:</p>
                <p className="text-sm">{selectedItem.query}</p>
              </div>
              
              <StreamAnswer
                markdown={rerunAnswer}
                isComplete={!isRerunning}
                error={error}
              />
            </div>
          </Card>
        )}

        {/* History List */}
        {historyItems.length === 0 ? (
          <Card className="p-12 text-center">
            <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">{t('history.empty', language)}</h3>
            <p className="text-muted-foreground">
              {t('history.emptyDesc', language)}
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {historyItems.map((item, index) => (
              <Card key={item.id || index} className="p-4 hover:shadow-md transition-shadow">
                <div className="space-y-3">
                  {/* Query */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-lg mb-1">{item.query}</p>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{formatTimestamp(item.timestamp)}</span>
                        </div>
                        {item.language && (
                          <span className="px-2 py-1 bg-accent rounded text-xs">
                            {item.language === 'ar' ? 'العربية' : 'English'}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleRerun(item)}
                        className="btn-primary h-8 px-3 text-xs"
                        title={t('history.rerun', language)}
                      >
                        <Play className="h-3 w-3 mr-1" />
                        {t('history.rerun', language)}
                      </button>
                      <button
                        onClick={() => {
                          // TODO: Implement delete functionality
                          toast.info(t('history.deleteComingSoon', language));
                        }}
                        className="btn-destructive h-8 w-8 p-0"
                        title={t('history.delete', language)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Answer Preview */}
                  {item.answer && (
                    <div className="p-3 bg-accent/50 rounded text-sm">
                      <p className="text-muted-foreground mb-1">{t('history.previousAnswer', language)}:</p>
                      <p className="line-clamp-3">
                        {item.answer.length > 200 
                          ? `${item.answer.substring(0, 200)}...` 
                          : item.answer
                        }
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
