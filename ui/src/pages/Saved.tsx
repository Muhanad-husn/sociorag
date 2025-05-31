import { useState, useEffect } from 'preact/hooks';
import { getSavedFiles } from '../lib/api';
import type { SavedFile } from '../lib/api';
import { useAppStore } from '../hooks/useLocalState';
import { t } from '../lib/i18n';
import { Card } from '../components/ui/Card';
import { File, ChevronUp, ChevronDown } from 'lucide-preact';
import { toast } from 'sonner';

type SortField = 'filename' | 'size' | 'created_at' | 'modified_at';
type SortOrder = 'asc' | 'desc';

export function Saved() {
  const [savedFiles, setSavedFiles] = useState<SavedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<SortField>('modified_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const { language } = useAppStore();
  
  useEffect(() => {
    loadSavedFiles();
  }, [sortField, sortOrder]);

  const loadSavedFiles = async () => {
    try {
      setLoading(true);
      const files = await getSavedFiles(sortField, sortOrder);
      setSavedFiles(files);
    } catch (error) {
      console.error('Failed to load saved files:', error);
      toast.error(t('saved.loadFailed', language));
    } finally {
      setLoading(false);
    }
  };
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };
  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return dateString;
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null;
    return sortOrder === 'desc' ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />;
  };

  const totalSize = savedFiles.reduce((sum, file) => sum + file.size, 0);
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-2">{t('common.loading', language)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">{t('saved.title', language)}</h1>
            <p className="text-muted-foreground mt-1">
              {savedFiles.length} PDF files • {formatFileSize(totalSize)} total
            </p>
          </div>
          <button
            onClick={loadSavedFiles}
            className="btn-secondary"
          >
            {t('saved.refresh', language)}
          </button>
        </div>        {/* Files Table */}
        {savedFiles.length === 0 ? (
          <Card className="p-12 text-center">
            <File className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">{t('saved.empty', language)}</h3>
            <p className="text-muted-foreground">
              {t('saved.emptyDesc', language)}
            </p>
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-border">
                <thead className="bg-muted/50">
                  <tr>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-muted/70 transition-colors"
                      onClick={() => handleSort('filename')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Filename</span>
                        {getSortIcon('filename')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-muted/70 transition-colors"
                      onClick={() => handleSort('size')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Size</span>
                        {getSortIcon('size')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-muted/70 transition-colors"
                      onClick={() => handleSort('created_at')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Created</span>
                        {getSortIcon('created_at')}
                      </div>
                    </th>                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-muted/70 transition-colors"
                      onClick={() => handleSort('modified_at')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Modified</span>
                        {getSortIcon('modified_at')}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-background divide-y divide-border">                  {savedFiles.map((file, index) => (
                    <tr 
                      key={index} 
                      className="hover:bg-muted/30 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center mr-3">
                            <File className="h-4 w-4 text-red-600" />
                          </div>
                          <div className="text-sm font-medium text-foreground truncate max-w-xs" title={file.filename}>
                            {file.filename}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-foreground">
                          {formatFileSize(file.size)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-foreground">
                          {formatDate(file.created_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-foreground">
                          {formatDate(file.modified_at)}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}        {/* Info Card */}
        <Card className="p-4 bg-accent/50">
          <h3 className="text-lg font-semibold mb-2">About Saved Files</h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>• View all your saved PDF files in one organized list</li>
            <li>• Click column headers to sort files by filename, size, or date</li>
            <li>• Files are automatically saved when you generate PDF responses</li>
            <li>• File sizes and creation dates are displayed for easy reference</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
