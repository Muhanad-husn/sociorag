import { useState, useEffect } from 'preact/hooks';
import { getSavedFiles, downloadSavedFile } from '../lib/api';
import { useAppStore } from '../hooks/useLocalState';
import { t } from '../lib/i18n';
import { Card } from '../components/ui/Card';
import { Download, File, FileText, Calendar, HardDrive } from 'lucide-preact';
import { toast } from 'sonner';
import clsx from 'clsx';

interface SavedFile {
  name: string;
  size: number;
  modified: string;
  url: string;
}

export function Saved() {
  const [savedFiles, setSavedFiles] = useState<SavedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingFiles, setDownloadingFiles] = useState<Set<string>>(new Set());
  const { language } = useAppStore();
  
  useEffect(() => {
    loadSavedFiles();
  }, []);

  const loadSavedFiles = async () => {
    try {
      setLoading(true);
      const files = await getSavedFiles();
      setSavedFiles(files);
    } catch (error) {
      console.error('Failed to load saved files:', error);
      toast.error(t('saved.loadFailed', language));
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (file: SavedFile) => {
    if (downloadingFiles.has(file.name)) return;

    setDownloadingFiles(prev => new Set(prev).add(file.name));

    try {
      const blob = await downloadSavedFile(file.name);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success(`${t('saved.downloadSuccess', language)} ${file.name}`);
    } catch (error) {
      console.error('Download failed:', error);
      toast.error(`${t('saved.downloadFailed', language)} ${file.name}`);
    } finally {
      setDownloadingFiles(prev => {
        const newSet = new Set(prev);
        newSet.delete(file.name);
        return newSet;
      });
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
      return date.toLocaleDateString();
    } catch {
      return dateString;
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
          <h1 className="text-3xl font-bold">{t('saved.title', language)}</h1>
          <button
            onClick={loadSavedFiles}
            className="btn-secondary"
          >
            {t('saved.refresh', language)}
          </button>
        </div>

        {/* Files Grid */}
        {savedFiles.length === 0 ? (
          <Card className="p-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">{t('saved.empty', language)}</h3>
            <p className="text-muted-foreground">
              {t('saved.emptyDesc', language)}
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {savedFiles.map((file, index) => (
              <Card key={index} className="p-4 hover:shadow-md transition-shadow">
                <div className="space-y-3">
                  {/* File Icon and Name */}
                  <div className="flex items-start space-x-3">
                    <File className="h-8 w-8 text-red-600 flex-shrink-0 mt-1" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm leading-tight break-words">
                        {file.name}
                      </h3>
                    </div>
                  </div>

                  {/* File Metadata */}
                  <div className="space-y-2 text-xs text-muted-foreground">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1">
                        <HardDrive className="h-3 w-3" />
                        <span>{t('saved.size', language)}</span>
                      </div>
                      <span>{formatFileSize(file.size)}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-3 w-3" />
                        <span>{t('saved.modified', language)}</span>
                      </div>
                      <span>{formatDate(file.modified)}</span>
                    </div>
                  </div>

                  {/* Download Button */}
                  <button
                    onClick={() => handleDownload(file)}
                    disabled={downloadingFiles.has(file.name)}
                    className={clsx(
                      'w-full btn-primary h-8 text-xs',
                      downloadingFiles.has(file.name) && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    {downloadingFiles.has(file.name) ? (
                      <>
                        <div className="animate-spin rounded-full h-3 w-3 border-b border-white mr-1" />
                        {t('saved.downloading', language)}...
                      </>
                    ) : (
                      <>
                        <Download className="h-3 w-3 mr-1" />
                        {t('saved.download', language)}
                      </>
                    )}
                  </button>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Info Card */}
        <Card className="p-4 bg-accent/50">
          <h3 className="text-lg font-semibold mb-2">{t('saved.aboutTitle', language)}</h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>• {t('saved.about1', language)}</li>
            <li>• {t('saved.about2', language)}</li>
            <li>• {t('saved.about3', language)}</li>
            <li>• {t('saved.about4', language)}</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
