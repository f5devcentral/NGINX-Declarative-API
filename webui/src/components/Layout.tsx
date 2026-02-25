import { Header } from './Header';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="layout">
      <Header />
      <main className="main-content">{children}</main>
    </div>
  );
};
