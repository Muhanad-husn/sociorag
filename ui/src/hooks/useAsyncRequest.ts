import { useCallback, useEffect, useState } from 'preact/hooks';

export interface AsyncRequestOptions {
  onComplete?: (data: any) => void;
  onError?: (error: Error) => void;
}

export function useAsyncRequest<T>(options: AsyncRequestOptions = {}) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (requestFn: () => Promise<T>) => {
    setLoading(true);
    setError(null);

    try {
      const result = await requestFn();
      setData(result);
      options.onComplete?.(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      options.onError?.(err instanceof Error ? err : new Error(errorMessage));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [options.onComplete, options.onError]);

  return { data, loading, error, execute };
}


export function useProgressPolling(
  pollFn: (() => Promise<any>) | null,
  interval: number = 1000
) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pollFn) {
      setProgress(0);
      setStatus('');
      setIsComplete(false);
      setError(null);
      return;
    }

    const poll = async () => {
      try {
        const data = await pollFn();
        
        if (data.progress !== undefined) {
          setProgress(data.progress);
        }
        
        if (data.status) {
          setStatus(data.status);
        }
        
        if (data.status === 'completed' || data.status === 'error') {
          setIsComplete(true);
          return;
        }
        
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);
        setIsComplete(true);
      }
    };

    // Initial poll
    poll();

    // Set up polling interval if not complete
    const intervalId = setInterval(() => {
      if (!isComplete) {
        poll();
      }
    }, interval);

    return () => {
      clearInterval(intervalId);
    };
  }, [pollFn, interval, isComplete]);

  return { progress, status, isComplete, error };
}
