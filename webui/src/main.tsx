import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Apply stored theme before first render to avoid flash
const stored = localStorage.getItem('theme');
document.documentElement.dataset.theme = stored === 'light' ? 'light' : 'dark';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
