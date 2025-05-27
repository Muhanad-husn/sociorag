import { useEffect, useRef, useState } from 'preact/hooks';
import MarkdownIt from 'markdown-it';
import { detectLanguage, getDirection } from '../lib/i18n';
import { Copy, Check } from 'lucide-preact';
import clsx from 'clsx';

interface StreamAnswerProps {
  markdown: string;
  isComplete?: boolean;
  error?: string | null;
}

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
  typographer: true,
});

export function StreamAnswer({ markdown, isComplete = false, error }: StreamAnswerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [language, setLanguage] = useState<'en' | 'ar' | 'mixed'>('en');

  useEffect(() => {
    if (markdown) {
      const detectedLang = detectLanguage(markdown);
      setLanguage(detectedLang);
    }
  }, [markdown]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [markdown]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
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

  if (!markdown) {
    return null;
  }

  const direction = getDirection(language);
  const renderedMarkdown = md.render(markdown);

  return (
    <div className="space-y-4">
      {/* Answer container */}
      <div className="card">
        <div className="flex items-center justify-between p-3 border-b">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Answer</span>
            {language === 'ar' && (
              <span className="text-xs bg-accent text-accent-foreground px-2 py-1 rounded">
                العربية
              </span>
            )}
          </div>
          <button
            onClick={handleCopy}
            className="btn-secondary h-8 w-8 p-0"
            title="Copy to clipboard"
          >
            {copied ? (
              <Check className="h-4 w-4 text-green-600" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </button>
        </div>
        
        <div
          ref={containerRef}
          className={clsx(
            'p-4 max-h-96 overflow-y-auto',
            'prose prose-sm max-w-none',
            'dark:prose-invert',
            direction === 'rtl' && 'text-right'
          )}
          dir={direction}
          style={{
            fontFamily: language === 'ar' ? 'var(--font-arabic)' : 'var(--font-inter)'
          }}
        >
          {/* Streaming typing effect */}
          <div
            className={clsx(
              'whitespace-pre-wrap',
              !isComplete && 'typing-animation'
            )}
            dangerouslySetInnerHTML={{ __html: renderedMarkdown }}
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
        </span>
        <span>
          {markdown.length} characters
        </span>
      </div>
    </div>
  );
}
