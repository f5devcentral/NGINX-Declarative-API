import { useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import './Header.css';

export const Header = () => {
  const [theme, setTheme] = useState<'dark' | 'light'>(
    () => (document.documentElement.dataset.theme as 'dark' | 'light') ?? 'dark'
  );

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('theme', next);
    setTheme(next);
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div>
            <h1>NGINX Declarative API</h1>
            <p className="header-subtitle">Configuration Builder</p>
          </div>
        </div>
        <button
          className="theme-toggle-btn"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
};
