import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Initialize MSW in development mode when explicitly enabled
const enableMocks = import.meta.env.VITE_ENABLE_MSW === 'true'

if (import.meta.env.DEV && enableMocks) {
  const { startMocking } = await import('./mocks/browser.ts')
  await startMocking()
} else if (import.meta.env.DEV) {
  console.info('MSW disabled; using live backend APIs')
}

// Add FontAwesome icons via CDN
const link = document.createElement('link');
link.rel = 'stylesheet';
link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
document.head.appendChild(link);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
) 