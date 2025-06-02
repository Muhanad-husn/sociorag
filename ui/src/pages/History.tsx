import { useState, useEffect } from 'preact/hooks';
import { getHistory, deleteHistoryRecord } from '../lib/api';
import { useAppStore } from '../hooks/useLocalState';
import { useAsyncRequest } from '../hooks/useAsyncRequest';
import { t } from '../lib/i18n';
import { Card } from '../components/ui/Card';
import { Copy, Trash2, Clock, MessageSquare } from 'lucide-preact';
import { toast } from 'sonner';

interface HistoryItem {
  id: number;
  query: string;
  timestamp: string;
  token_count: number;
  context_count: number;
  metadata: any;
}

export function History() {
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const { language } = useAppStore();
  const { execute: executeDelete } = useAsyncRequest<{ success: boolean; message: string }>();

  useEffect(() => {
    loadHistory();
  }, []);
  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await getHistory(1, 15);
      setHistoryItems(response.records);
    } catch (error) {
      console.error('Failed to load history:', error);
      toast.error(t('history.loadFailed', language));
    } finally {
      setLoading(false);
    }
  };
  const handleCopyQuery = async (query: string) => {
    try {
      await navigator.clipboard.writeText(query);
      toast.success(t('history.queryCopied', language));
    } catch (err) {
      console.error('Copy error:', err);
      toast.error(t('history.copyFailed', language));
    }
  };
  const handleDeleteRecord = async (item: HistoryItem) => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      `${t('history.deleteConfirm', language)}\n\n"${item.query.substring(0, 100)}${item.query.length > 100 ? '...' : ''}"`
    );
    
    if (!confirmed) {
      return;
    }
    
    setDeletingId(item.id);
    
    try {
      const response = await executeDelete(() => deleteHistoryRecord(item.id));
      if (response?.success) {
        toast.success(t('history.deleteSuccess', language));
        // Remove the item from the local state
        setHistoryItems(items => items.filter(i => i.id !== item.id));
      } else {
        toast.error(response?.message || t('history.deleteFailed', language));
      }
    } catch (err) {
      console.error('Delete error:', err);
      toast.error(t('history.deleteFailed', language));
    } finally {
      setDeletingId(null);
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
        <div className="space-y-6">
          {/* Header skeleton */}
          <div className="flex items-center justify-between">
            <div className="skeleton h-8 w-32"></div>
            <div className="skeleton h-9 w-24"></div>
          </div>
          
          {/* History items skeleton */}
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Card key={i} className="p-4">
                <div className="space-y-3">
                  <div className="skeleton h-6 w-3/4"></div>
                  <div className="flex items-center space-x-4">
                    <div className="skeleton h-4 w-24"></div>
                    <div className="skeleton h-5 w-16"></div>
                  </div>
                  <div className="skeleton h-16 w-full"></div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-6">
        {/* Header */}        <div className="flex items-center justify-between">
          <h1 className="text-2xl sm:text-3xl font-bold">{t('history.title', language)}</h1>          <button
            onClick={loadHistory}
            className="btn-secondary hover-scale active-press focus-ring-enhanced"
          >
            {t('history.refresh', language)}
          </button>
        </div>{/* History List */}
        {historyItems.length === 0 ? (
          <Card className="p-12 text-center">
            <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">{t('history.empty', language)}</h3>
            <p className="text-muted-foreground">
              {t('history.emptyDesc', language)}
            </p>
          </Card>
        ) : (
          <div className="space-y-4">            {historyItems.map((item, index) => (
              <Card key={item.id || index} className="p-4 card-interactive">
                <div className="space-y-3">
                  {/* Query */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-lg mb-1">{item.query}</p>                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{formatTimestamp(item.timestamp)}</span>
                        </div>
                        <span className="px-2 py-1 bg-accent rounded text-xs">
                          {item.token_count} tokens
                        </span>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center space-x-2">                      <button
                        onClick={() => handleCopyQuery(item.query)}
                        className="btn-primary h-8 px-3 text-xs hover-scale active-press focus-ring-enhanced"
                        title={t('history.copyQuery', language)}
                      >
                        <Copy className="h-3 w-3 mr-1" />
                        {t('history.copyQuery', language)}
                      </button>                      <button
                        onClick={() => handleDeleteRecord(item)}
                        className="btn-destructive h-8 w-8 p-0 hover-scale active-press focus-ring-enhanced"
                        title={t('history.delete', language)}
                        disabled={deletingId === item.id}
                      >                        {deletingId === item.id ? (
                          <div className="animate-spin h-4 w-4 border-2 border-t-transparent rounded-full pulse-enhanced"></div>) : (
                          <Trash2 className="h-3 w-3" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
