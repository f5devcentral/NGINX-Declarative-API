import './Header.css';

export const Header = () => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div>
            <h1>NGINX Declarative API</h1>
            <p className="header-subtitle">Configuration Builder</p>
          </div>
        </div>
      </div>
    </header>
  );
};
