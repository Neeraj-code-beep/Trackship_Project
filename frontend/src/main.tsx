import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { AnalysisSessionProvider } from './state/AnalysisSessionContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AnalysisSessionProvider>
      <App />
    </AnalysisSessionProvider>
  </StrictMode>,
)
