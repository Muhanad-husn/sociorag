import { useEffect, useRef, useState } from 'preact/hooks';
import { detectLanguage, getDirection } from '../lib/i18n';
import { Copy, Check } from 'lucide-preact';
import clsx from 'clsx';

interface StreamAnswerProps {
  html?: string;  // Pre-rendered HTML content
  markdown?: string;  // Fallback markdown for backward compatibility
  isComplete?: boolean;
  error?: string | null;
  isLoading?: boolean;
}

export function StreamAnswer({ html, markdown, isComplete = false, error, isLoading = false }: StreamAnswerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [language, setLanguage] = useState<'en' | 'ar' | 'mixed'>('en');

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
  };
  if (error) {
    return (
      <div className="card p-4 border-destructive animate-error">
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
        <div className="p-4 space-y-2">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 skeleton-shimmer"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full skeleton-shimmer"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6 skeleton-shimmer"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/5 skeleton-shimmer"></div>
        </div>
      </div>
    );  }

  const direction = getDirection(language);
  // Use pre-rendered HTML if available, otherwise display as plain text
  const renderedContent = html || content;

  return (
    <div className="space-y-4">      {/* Answer container */}
      <div className="card card-interactive">        <div className="flex items-center justify-between p-3 border-b">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Answer</span>
            {language === 'ar' && (
              <span className="text-xs bg-accent text-accent-foreground px-2 py-1 rounded status-indicator">
                العربية
              </span>
            )}
          </div>          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              disabled={isLoading}
              className={clsx(
                "btn-secondary h-8 w-8 p-0 hover-scale active-press focus-ring-enhanced",
                isLoading && "opacity-50 cursor-not-allowed"
              )}
              title="Copy to clipboard"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-600 animate-success" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
          <div
          ref={containerRef}          className={clsx(
            'p-4 max-h-96 overflow-y-auto',
            'prose prose-sm sm:prose-base lg:prose-lg max-w-none',
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
        </div>
      </div>
    </div>
  );
}
