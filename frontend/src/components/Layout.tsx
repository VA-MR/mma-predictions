import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useAdminAuth } from '../hooks/useAdminAuth';
import AuthModal from './AuthModal';
import './Layout.css';

export default function Layout() {
  const { user, isAuthenticated, logout, openAuthModal } = useAuth();
  const { isAdminAuthenticated, adminLogout } = useAdminAuth();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    // Logout from both auth systems
    logout();
    adminLogout();
  };

  // User is considered logged in if either Telegram or Admin auth is active
  const isLoggedIn = isAuthenticated || isAdminAuthenticated;
  
  // Display name for the user
  const displayName = isAdminAuthenticated 
    ? 'Admin' 
    : (user?.username || user?.first_name || 'User');

  return (
    <div className="layout">
      <header className="header">
        <div className="header-top">
          <div className="container">
            <div className="header-content">
              <Link to="/" className="logo">
                <div className="logo-icon">ΜΣΤΑ</div>
                <span className="logo-text">MMA</span>
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
                {/* Only show Admin link if logged in as admin */}
                {isAdminAuthenticated && (
                  <Link 
                    to="/admin" 
                    className={`nav-link admin-link ${isActive('/admin') ? 'active' : ''}`}
                  >
                    Админ
                  </Link>
                )}
              </nav>

              <div className="auth-section">
                {isLoggedIn ? (
                  <div className="user-menu">
                    {isAdminAuthenticated ? (
                      <div className="admin-badge">🔐</div>
                    ) : user?.photo_url ? (
                      <img 
                        src={user.photo_url} 
                        alt={user.username || 'User'} 
                        className="user-avatar" 
                      />
                    ) : null}
                    <span className="user-name">{displayName}</span>
                    <button onClick={handleLogout} className="logout-btn">
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
