// Browser shutdown handler for SocioRAG
// This module handles the cleanup when the user closes the browser tab or window

import { getApiUrl } from './api';

/**
 * Initiates shutdown of the SocioRAG application servers
 * by calling the backend shutdown endpoint
 */
async function shutdownApplication(): Promise<void> {
  try {
    // Check if processing is currently active
    // Access the store state directly to avoid import cycles
    const processingState = localStorage.getItem('sociograph-storage');
    if (processingState) {
      const state = JSON.parse(processingState);
      if (state?.state?.isProcessing) {
        console.warn('Shutdown prevented: System is currently processing files');
        return;
      }
    }

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
  // Track if shutdown has already been triggered to prevent multiple calls
  let shutdownTriggered = false;
  let isNavigating = false;
    // Track navigation events to distinguish between browser close and page navigation
  window.addEventListener('beforeunload', () => {
    // Only trigger shutdown if this is likely a real browser close
    // Additional checks to prevent false positives:
    
    // Check if we're in the middle of processing
    const processingState = localStorage.getItem('sociograph-storage');
    if (processingState) {
      const state = JSON.parse(processingState);
      if (state?.state?.isProcessing) {
        console.warn('Shutdown prevented: System is currently processing files');
        return;
      }
    }
    
    // Only shutdown if we haven't already triggered it and we're not navigating
    if (!shutdownTriggered && !isNavigating) {
      shutdownTriggered = true;
      shutdownApplication();
    }
  });

  // Track when user starts navigating within the app
  // This helps distinguish between navigation and browser close
  window.addEventListener('popstate', () => {
    isNavigating = true;
    // Reset after a short delay
    setTimeout(() => {
      isNavigating = false;
    }, 1000);
  });

  // Note: Removed pagehide listener as it was also too aggressive
  // Only relying on beforeunload for more precise detection
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
