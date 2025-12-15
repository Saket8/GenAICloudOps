/**
 * Test setup file for Jest and React Testing Library
 * Configures global test environment and utilities
 */

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, afterAll } from '@jest/globals';
import { server } from './mocks/server';

// Global test configuration
beforeAll(() => {
  // Start MSW server for API mocking
  server.listen({
    onUnhandledRequest: 'error'
  });
  
  // Mock window.matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });

  // Mock ResizeObserver
  global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  }));

  // Mock IntersectionObserver
  global.IntersectionObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  }));

  // Mock localStorage
  const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  };
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock
  });

  // Mock sessionStorage
  const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  };
  Object.defineProperty(window, 'sessionStorage', {
    value: sessionStorageMock
  });

  // Mock console methods in tests
  global.console = {
    ...console,
    warn: jest.fn(),
    error: jest.fn(),
  };
});

afterEach(() => {
  // Cleanup DOM after each test
  cleanup();
  
  // Reset MSW handlers
  server.resetHandlers();
  
  // Clear all mocks
  jest.clearAllMocks();
});

afterAll(() => {
  // Stop MSW server
  server.close();
});

// Custom Jest matchers
expect.extend({
  toHaveAccessibleName(received: HTMLElement, expected: string) {
    const accessibleName = received.getAttribute('aria-label') || 
                          received.getAttribute('aria-labelledby') ||
                          received.textContent;
    
    const pass = accessibleName === expected;
    
    if (pass) {
      return {
        message: () => `Expected element not to have accessible name "${expected}"`,
        pass: true,
      };
    } else {
      return {
        message: () => `Expected element to have accessible name "${expected}", but got "${accessibleName}"`,
        pass: false,
      };
    }
  },

  toBeLoadingState(received: HTMLElement) {
    const hasLoadingIndicator = received.querySelector('[data-testid="loading"]') !== null ||
                               received.querySelector('.animate-spin') !== null ||
                               received.getAttribute('aria-busy') === 'true';
    
    const pass = hasLoadingIndicator;
    
    if (pass) {
      return {
        message: () => 'Expected element not to be in loading state',
        pass: true,
      };
    } else {
      return {
        message: () => 'Expected element to be in loading state',
        pass: false,
      };
    }
  },

  toHaveErrorState(received: HTMLElement) {
    const hasErrorIndicator = received.querySelector('[data-testid="error"]') !== null ||
                              received.querySelector('.text-red-') !== null ||
                              received.getAttribute('aria-invalid') === 'true';
    
    const pass = hasErrorIndicator;
    
    if (pass) {
      return {
        message: () => 'Expected element not to have error state',
        pass: true,
      };
    } else {
      return {
        message: () => 'Expected element to have error state',
        pass: false,
      };
    }
  }
});

// Extend Jest matchers type
declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveAccessibleName(expected: string): R;
      toBeLoadingState(): R;
      toHaveErrorState(): R;
    }
  }
}

// Global test utilities
export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const waitForNextTick = () => new Promise(resolve => process.nextTick(resolve));

// Performance testing helper
export const measurePerformance = async (fn: () => Promise<void> | void) => {
  const start = performance.now();
  await fn();
  const end = performance.now();
  return end - start;
};

// Accessibility testing helper
export const checkAccessibility = async (container: HTMLElement) => {
  const { toHaveNoViolations } = await import('jest-axe');
  expect.extend(toHaveNoViolations);
  
  const axe = await import('axe-core');
  const results = await axe.run(container);
  expect(results).toHaveNoViolations();
};

// Test data helpers
export const createMockUser = (overrides: Partial<any> = {}) => ({
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  is_active: true,
  roles: ['user'],
  ...overrides
});

export const createMockApiResponse = <T>(data: T, overrides: Partial<any> = {}) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {},
  ...overrides
});

// Query client test helper
export const createTestQueryClient = () => {
  const { QueryClient } = require('@tanstack/react-query');
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
};

// Router test helper
export const createTestRouter = (initialEntries: string[] = ['/']) => {
  const { createMemoryRouter } = require('react-router-dom');
  const React = require('react');
  return createMemoryRouter(
    [
      {
        path: '*',
        element: React.createElement('div', null, 'Test Route'),
      },
    ],
    {
      initialEntries,
    }
  );
}; 