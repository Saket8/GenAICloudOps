/**
 * Mock Service Worker (MSW) server setup for testing
 * Provides API mocking for all test scenarios
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Create MSW server with all API handlers
export const server = setupServer(...handlers);

// Configure server for different test scenarios
export const configureServer = {
  // Configure for success scenarios
  success: () => {
    server.use(...handlers);
  },

  // Configure for error scenarios
  error: () => {
    const { http, HttpResponse } = require('msw');
    
    server.use(
      // Override all endpoints to return errors
      http.get('*/api/*', () => {
        return HttpResponse.json(
          { detail: 'Internal server error' },
          { status: 500 }
        );
      }),
      http.post('*/api/*', () => {
        return HttpResponse.json(
          { detail: 'Internal server error' },
          { status: 500 }
        );
      }),
      http.put('*/api/*', () => {
        return HttpResponse.json(
          { detail: 'Internal server error' },
          { status: 500 }
        );
      }),
      http.delete('*/api/*', () => {
        return HttpResponse.json(
          { detail: 'Internal server error' },
          { status: 500 }
        );
      })
    );
  },

  // Configure for network errors
  networkError: () => {
    const { http, HttpResponse } = require('msw');
    
    server.use(
      http.get('*/api/*', () => {
        return HttpResponse.error();
      }),
      http.post('*/api/*', () => {
        return HttpResponse.error();
      })
    );
  },

  // Configure for slow responses
  slow: (delay: number = 3000) => {
    const { http, HttpResponse, delay: msw_delay } = require('msw');
    
    server.use(
      http.get('*/api/*', async () => {
        await msw_delay(delay);
        return HttpResponse.json({ message: 'Slow response' });
      })
    );
  },

  // Configure for authentication errors
  unauthorized: () => {
    const { http, HttpResponse } = require('msw');
    
    server.use(
      http.get('*/api/*', () => {
        return HttpResponse.json(
          { detail: 'Unauthorized' },
          { status: 401 }
        );
      }),
      http.post('*/api/*', () => {
        return HttpResponse.json(
          { detail: 'Unauthorized' },
          { status: 401 }
        );
      })
    );
  }
}; 