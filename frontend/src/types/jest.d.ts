/**
 * TypeScript declarations for custom Jest matchers
 */

import '@testing-library/jest-dom';

declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveAccessibleName(expected: string): R;
      toBeLoadingState(): R;
      toHaveErrorState(): R;
    }
  }
}

export {}; 