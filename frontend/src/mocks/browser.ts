/**
 * Mock Service Worker (MSW) browser setup
 * Provides API mocking in development environment
 */

import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

// Create MSW worker with all API handlers
export const worker = setupWorker(...handlers);

// Start worker with proper configuration
export const startMocking = async () => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    await worker.start({
      onUnhandledRequest: 'warn',
      serviceWorker: {
        url: '/mockServiceWorker.js'
      }
    });
    
    console.log('🎭 MSW: Mock API server started successfully');
    console.log(`🎭 MSW: ${handlers.length} handlers registered`);
    
    // Add debugging for unhandled requests
    worker.events.on('request:unhandled', ({ request }) => {
      console.warn(`🎭 MSW: Unhandled ${request.method} request to ${request.url}`);
    });
    
  } catch (error) {
    console.error('🎭 MSW: Failed to start mock worker:', error);
  }
}; 