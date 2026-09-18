import './styles/global.css';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Providers } from './app/Providers';
import { ToastProvider } from './components/ui';
import App from './App';

const rootEl = document.getElementById('root');
if (!rootEl) {
  throw new Error('#root element not found');
}

createRoot(rootEl).render(
  <StrictMode>
    <BrowserRouter>
      <Providers>
        <ToastProvider>
          <App />
        </ToastProvider>
      </Providers>
    </BrowserRouter>
  </StrictMode>,
);
