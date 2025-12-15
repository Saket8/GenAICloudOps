module.exports = {
  root: true,
  env: { 
    browser: true, 
    es2020: true,
    jest: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs', '**/*.test.*', '**/*.spec.*', 'test-setup.ts', 'mocks/**'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': 'off',
    'no-unused-vars': 'warn',
    'no-undef': 'off' // TypeScript handles this
  },
  overrides: [
    {
      files: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}', '**/test-setup.ts', 'mocks/**'],
      env: {
        jest: true,
      },
      rules: {
        'no-unused-vars': 'off',
        'no-undef': 'off'
      }
    }
  ]
}; 