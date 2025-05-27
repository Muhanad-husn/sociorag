import { useEffect, useState } from 'preact/hooks';
import { useProgressSSE } from '../hooks/useSSE';
import { createProgressStream } from '../lib/api';
import { t } from '../lib/i18n';
import { CheckCircle, Loader } from 'lucide-preact';
import clsx from 'clsx';

interface ProgressBarProps {
  isVisible: boolean;
  onComplete?: () => void;
}

export function ProgressBar({ isVisible, onComplete }: ProgressBarProps) {
  const [progressSource, setProgressSource] = useState<EventSource | null>(null);
  const { progress, status, isComplete } = useProgressSSE(progressSource);

  useEffect(() => {
    if (isVisible && !progressSource) {
      const source = createProgressStream();
      setProgressSource(source);
    } else if (!isVisible && progressSource) {
      progressSource.close();
      setProgressSource(null);
    }

    return () => {
      if (progressSource) {
        progressSource.close();
      }
    };
  }, [isVisible]);

  useEffect(() => {
    if (isComplete) {
      onComplete?.();
      // Auto-hide after completion
      setTimeout(() => {
        if (progressSource) {
          progressSource.close();
          setProgressSource(null);
        }
      }, 3000);
    }
  }, [isComplete, onComplete]);

  if (!isVisible && !isComplete) {
    return null;
  }

  return (
    <div className={clsx(
      'card p-4 transition-all duration-300',
      isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
    )}>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isComplete ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <Loader className="h-5 w-5 text-primary animate-spin" />
            )}
            <span className="font-medium">
              {t('processing.title')}
            </span>
          </div>
          <span className="text-sm text-muted-foreground">
            {Math.round(progress)}%
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-secondary rounded-full h-2">
          <div
            className={clsx(
              'h-2 rounded-full transition-all duration-500 ease-out',
              isComplete ? 'bg-green-600' : 'bg-primary'
            )}
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Status text */}
        {status && (
          <div className="text-sm text-muted-foreground">
            <span className="font-medium">{t('processing.status')}:</span> {status}
          </div>
        )}

        {/* Processing steps indicator */}
        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
          <div className={clsx(
            'w-2 h-2 rounded-full',
            progress > 0 ? 'bg-primary' : 'bg-muted'
          )} />
          <span>PDF Processing</span>
          
          <div className={clsx(
            'w-2 h-2 rounded-full',
            progress > 25 ? 'bg-primary' : 'bg-muted'
          )} />
          <span>Text Extraction</span>
          
          <div className={clsx(
            'w-2 h-2 rounded-full',
            progress > 50 ? 'bg-primary' : 'bg-muted'
          )} />
          <span>Chunking</span>
          
          <div className={clsx(
            'w-2 h-2 rounded-full',
            progress > 75 ? 'bg-primary' : 'bg-muted'
          )} />
          <span>Embedding</span>
          
          <div className={clsx(
            'w-2 h-2 rounded-full',
            isComplete ? 'bg-green-600' : 'bg-muted'
          )} />
          <span>Complete</span>
        </div>
      </div>
    </div>
  );
}
