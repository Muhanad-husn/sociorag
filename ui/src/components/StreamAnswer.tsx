import { useEffect, useRef, useState } from 'preact/hooks';
import { detectLanguage, getDirection, t } from '../lib/i18n';
import { Copy, Check, Download } from 'lucide-preact';
import clsx from 'clsx';
import { toast } from 'sonner';
import { useAppStore } from '../hooks/useLocalState';
import { downloadAndSavePDF } from '../lib/api';

interface StreamAnswerProps {
  html?: string;  // Pre-rendered HTML content
  markdown?: string;  // Fallback markdown for backward compatibility
  isComplete?: boolean;
  error?: string | null;
  pdfUrl?: string;
  isLoading?: boolean;
}

export function StreamAnswer({ html, markdown, isComplete = false, error, pdfUrl, isLoading = false }: StreamAnswerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [language, setLanguage] = useState<'en' | 'ar' | 'mixed'>('en');
  const [downloading, setDownloading] = useState(false);
  const { language: appLanguage } = useAppStore();

  // Use HTML if available, otherwise fall back to markdown (for backward compatibility)
  const content = html || markdown || '';

  useEffect(() => {
    if (content) {
      const detectedLang = detectLanguage(content);
      setLanguage(detectedLang);
    }
  }, [content]);
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [content]);

  const handleCopy = async () => {
    try {
      // Copy the original content (markdown if available, otherwise extract text from HTML)
      const textToCopy = markdown || content;
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };  const handleDownloadPdf = async () => {
    if (!pdfUrl) return;
    
    setDownloading(true);
    try {
      // Extract filename from the pdfUrl (e.g., "/static/saved/answer_20250531_123456.pdf")
      const filename = pdfUrl.split('/').pop();
      if (!filename) {
        throw new Error('Could not extract filename from PDF URL');
      }
      
      const success = await downloadAndSavePDF(filename, `answer-${Date.now()}.pdf`);
      
      if (success) {
        toast.success(t('common.downloadStarted', appLanguage));
      }
    } catch (error: any) {
      console.error('PDF save failed:', error);
      toast.error(t('common.downloadFailed', appLanguage));
    } finally {
      setDownloading(false);
    }
  };

  if (error) {
    return (
      <div className="card p-4 border-destructive">
        <div className="flex items-center space-x-2 text-destructive">
          <span className="font-medium">Error:</span>
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!markdown && !isLoading) {
    return null;
  }

  // Show loading skeleton when in loading state with no content yet
  if (isLoading && !markdown) {
    return (
      <div className="card">
        <div className="flex items-center justify-between p-3 border-b">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Answer</span>
          </div>
        </div>
        <div className="p-4 animate-pulse space-y-2">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/5"></div>
        </div>
      </div>
    );  }

  const direction = getDirection(language);
  // Use pre-rendered HTML if available, otherwise display as plain text
  const renderedContent = html || content;

  return (
    <div className="space-y-4">
      {/* Answer container */}
      <div className="card">        <div className="flex items-center justify-between p-3 border-b">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Answer</span>
            {language === 'ar' && (
              <span className="text-xs bg-accent text-accent-foreground px-2 py-1 rounded">
                العربية
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {pdfUrl && isComplete && (
              <button
                onClick={handleDownloadPdf}
                disabled={downloading || isLoading}
                className={clsx(
                  "btn-secondary h-8 px-3 text-xs",
                  (downloading || isLoading) && "opacity-50 cursor-not-allowed"
                )}
                title={t('common.downloadPdf', appLanguage)}
              >
                {downloading ? (
                  <div className="animate-spin rounded-full h-3 w-3 border-b border-gray-600 mr-1" />
                ) : (
                  <Download className="h-3 w-3 mr-1" />
                )}
                {t('common.downloadPdf', appLanguage)}
              </button>
            )}
            <button
              onClick={handleCopy}
              disabled={isLoading}
              className={clsx(
                "btn-secondary h-8 w-8 p-0",
                isLoading && "opacity-50 cursor-not-allowed"
              )}
              title="Copy to clipboard"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-600" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
          <div
          ref={containerRef}
          className={clsx(
            'p-4 max-h-96 overflow-y-auto',
            'prose prose-sm max-w-none',
            'dark:prose-invert',
            direction === 'rtl' && 'text-right prose-rtl',
            language === 'ar' && 'prose-rtl'
          )}
          dir={direction}
          style={{
            fontFamily: language === 'ar' ? 'var(--font-arabic)' : 'var(--font-inter)'
          }}
        >
          {/* Streaming typing effect */}          <div
            className={clsx(
              'whitespace-pre-wrap',
              !isComplete && 'typing-animation'
            )}
            dangerouslySetInnerHTML={{ __html: renderedContent }}
          />
          
          {/* Cursor for typing effect */}
          {!isComplete && (
            <span className="inline-block w-2 h-5 bg-primary animate-pulse ml-1" />
          )}
        </div>
      </div>
        {/* Status indicator */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {isComplete ? 'Response complete' : 'Generating response...'}
        </span>        <div className="flex items-center space-x-4">
          <span>
            {content.length} characters
          </span>
          {pdfUrl && isComplete && (
            <span className="text-green-600">
              {t('common.pdfReady', appLanguage)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
