import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import AuthModal from './AuthModal';
import './Layout.css';

export default function Layout() {
  const { user, isAuthenticated, logout, openAuthModal } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-top">
          <div className="container">
            <div className="header-content">
              <Link to="/" className="logo">
                <div className="logo-icon">🥊</div>
                <span className="logo-text">
                  META<span>RATINGS</span>
                </span>
              </Link>

              <nav className="nav">
                <Link 
                  to="/" 
                  className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
                >
                  События
                </Link>
                {isAuthenticated && (
                  <Link 
                    to="/profile" 
                    className={`nav-link ${isActive('/profile') ? 'active' : ''}`}
                  >
                    Мой профиль
                  </Link>
                )}
              </nav>

              <div className="auth-section">
                {isAuthenticated && user ? (
                  <div className="user-menu">
                    {user.photo_url && (
                      <img 
                        src={user.photo_url} 
                        alt={user.username || 'User'} 
                        className="user-avatar" 
                      />
                    )}
                    <span className="user-name">{user.username || 'User'}</span>
                    <button onClick={logout} className="logout-btn">
                      Выйти
                    </button>
                  </div>
                ) : (
                  <button className="login-btn" onClick={openAuthModal}>
                    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    Войти
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

      </header>

      <AuthModal />

      <main className="main">
        <Outlet />
      </main>

      <footer className="footer">
        <div className="container">
          <div className="footer-bottom">
            <p>MMA Events & Fighter Statistics</p>
            <p className="footer-sub">© 2025 METARATINGS</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
