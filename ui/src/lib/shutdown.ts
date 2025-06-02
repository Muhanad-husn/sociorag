// Browser shutdown handler for SocioRAG
// This module handles the cleanup when the user closes the browser tab or window

import { getApiUrl } from './api';

/**
 * Initiates shutdown of the SocioRAG application servers
 * by calling the backend shutdown endpoint
 */
async function shutdownApplication(): Promise<void> {
  try {
    const apiUrl = getApiUrl();
    
    // Use sendBeacon for reliable delivery during page unload
    // This is more reliable than fetch() during beforeunload events
    const shutdownUrl = `${apiUrl}/api/admin/shutdown`;
    const data = JSON.stringify({ source: 'browser_close' });
    
    if (navigator.sendBeacon) {
      // sendBeacon is the most reliable method for unload events
      const blob = new Blob([data], { type: 'application/json' });
      navigator.sendBeacon(shutdownUrl, blob);
    } else {
      // Fallback for browsers that don't support sendBeacon
      // Note: This may not always work during page unload
      fetch(shutdownUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: data,
        keepalive: true, // Attempt to keep request alive during page unload
      }).catch(() => {
        // Ignore errors during shutdown - we're already leaving
      });
    }
  } catch (error) {
    // Silently ignore errors during shutdown
    console.warn('Failed to trigger application shutdown:', error);
  }
}

/**
 * Sets up the browser event listeners to detect when the user
 * is closing the tab or window
 */
export function setupShutdownTrigger(): void {
  // Handle beforeunload event (when user tries to close/refresh the page)
  window.addEventListener('beforeunload', (event) => {
    // Only shutdown if this appears to be an intentional close
    // (not a refresh or navigation within the app)
    if (event.type === 'beforeunload') {
      shutdownApplication();
    }
  });

  // Handle visibilitychange as a backup
  // This fires when the tab becomes hidden (e.g., when closing the tab)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      // Use a small delay to distinguish between tab switching and closing
      setTimeout(() => {
        if (document.visibilityState === 'hidden') {
          shutdownApplication();
        }
      }, 100);
    }
  });

  // Handle pagehide event as another backup
  // This fires when the page is being unloaded
  window.addEventListener('pagehide', (event) => {
    // Only trigger on actual page unload, not when going into back/forward cache
    if (!event.persisted) {
      shutdownApplication();
    }
  });
}

/**
 * Manually trigger application shutdown
 * Can be called from UI elements like a "Shutdown" button
 */
export async function manualShutdown(): Promise<boolean> {
  try {
    const apiUrl = getApiUrl();
    const response = await fetch(`${apiUrl}/api/admin/shutdown`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ source: 'manual_shutdown' }),
    });

    if (response.ok) {
      const result = await response.json();
      return result.success;
    }
    return false;
  } catch (error) {
    console.error('Manual shutdown failed:', error);
    return false;
  }
}
