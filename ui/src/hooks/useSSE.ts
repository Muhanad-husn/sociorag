import { useEffect, useState, useRef } from 'preact/hooks';

export interface SSEOptions {
  onComplete?: () => void;
  onError?: (error: Event) => void;
}

export function useSSE(source: EventSource | null, options: SSEOptions = {}) {
  const [text, setText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textRef = useRef('');

  useEffect(() => {
    if (!source) {
      setText('');
      setIsComplete(false);
      setError(null);
      textRef.current = '';
      return;
    }

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token' && data.content) {
          textRef.current += data.content;
          setText(textRef.current);
        } else if (data.type === 'complete') {
          setIsComplete(true);
          options.onComplete?.();
        } else if (data.type === 'error') {
          setError(data.message || 'An error occurred');
          options.onError?.(event);
        }
      } catch (e) {
        // Fallback for simple text tokens
        textRef.current += event.data;
        setText(textRef.current);
      }
    };

    const handleError = (event: Event) => {
      setError('Connection error');
      options.onError?.(event);
    };

    const handleOpen = () => {
      setError(null);
    };

    source.addEventListener('message', handleMessage);
    source.addEventListener('error', handleError);
    source.addEventListener('open', handleOpen);

    return () => {
      source.removeEventListener('message', handleMessage);
      source.removeEventListener('error', handleError);
      source.removeEventListener('open', handleOpen);
      source.close();
    };
  }, [source, options.onComplete, options.onError]);

  return { text, isComplete, error };
}

export function useProgressSSE(source: EventSource | null) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!source) {
      setProgress(0);
      setStatus('');
      setIsComplete(false);
      return;
    }

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.progress !== undefined) {
          setProgress(data.progress);
        }
        
        if (data.status) {
          setStatus(data.status);
        }
        
        if (data.complete) {
          setIsComplete(true);
        }
      } catch (e) {
        console.error('Failed to parse progress data:', e);
      }
    };

    source.addEventListener('message', handleMessage);

    return () => {
      source.removeEventListener('message', handleMessage);
      source.close();
    };
  }, [source]);

  return { progress, status, isComplete };
}
