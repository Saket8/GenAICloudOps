/** @type {import('jest').Config} */
export default {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/test-setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': 'jest-transform-stub'
  },
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.(js|jsx)$': 'babel-jest'
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/test-setup.ts'
  ],
  coverageReporters: ['text', 'lcov', 'html'],
  coverageDirectory: 'coverage',
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx}'
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/dist/',
    '<rootDir>/e2e/'
  ],
  transformIgnorePatterns: [
    'node_modules/(?!(.*\\.mjs$|@testing-library/.*|@tanstack/.*|recharts/))'
  ],
  globals: {
    'ts-jest': {
      useESM: true,
      tsconfig: {
        jsx: 'react-jsx'
      }
    }
  },
  extensionsToTreatAsEsm: ['.ts', '.tsx'],
  testTimeout: 10000,
  maxWorkers: '50%',
  
  // Test categorization
  testNamePattern: process.env.TEST_NAME_PATTERN,
  
  // Custom reporters for CI/CD (only if jest-junit is available)
  reporters: process.env.CI ? [
    'default',
    ['jest-junit', {
      outputDirectory: 'test-results',
      outputName: 'jest-results.xml'
    }]
  ] : ['default']
}; 