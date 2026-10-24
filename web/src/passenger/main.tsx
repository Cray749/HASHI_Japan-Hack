import '@fontsource/noto-sans/400.css';
import '@fontsource/noto-sans/700.css';
import '@fontsource/noto-serif/700.css';
import '@fontsource/noto-sans-devanagari/400.css';
import '@fontsource/noto-sans-devanagari/700.css';
import '@fontsource/noto-sans-gurmukhi/400.css';
import '@fontsource/noto-sans-gurmukhi/700.css';
import '@fontsource/noto-sans-tamil/400.css';
import '@fontsource/noto-sans-tamil/700.css';
import '@fontsource/noto-sans-telugu/400.css';
import '@fontsource/noto-sans-telugu/700.css';
import '@fontsource/noto-sans-bengali/400.css';
import '@fontsource/noto-sans-bengali/700.css';
import '@fontsource/noto-sans-gujarati/400.css';
import '@fontsource/noto-sans-gujarati/700.css';
import '@fontsource/noto-sans-kannada/400.css';
import '@fontsource/noto-sans-kannada/700.css';
import '@fontsource/noto-sans-malayalam/400.css';
import '@fontsource/noto-sans-malayalam/700.css';
import '@fontsource/noto-sans-thai/400.css';
import '@fontsource/noto-sans-thai/700.css';
import '@fontsource/noto-sans-khmer/400.css';
import '@fontsource/noto-sans-khmer/700.css';
import '@fontsource/noto-sans-myanmar/400.css';
import '@fontsource/noto-sans-myanmar/700.css';
import '../shared/theme.css';
import './passenger.css';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

// Offline support: the worker caches the app so it opens even if the Wi-Fi drops.
if ('serviceWorker' in navigator && window.isSecureContext) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/p/sw.js', { scope: '/p/' }).catch(() => undefined);
  });
}
