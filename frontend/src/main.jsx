import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import AppErrorBoundary from './components/routing/AppErrorBoundary.jsx'
import { AuthenticationProvider } from './hooks/useAuth.js'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AppErrorBoundary>
      <BrowserRouter>
        <AuthenticationProvider>
          <App />
        </AuthenticationProvider>
      </BrowserRouter>
    </AppErrorBoundary>
  </StrictMode>,
)
