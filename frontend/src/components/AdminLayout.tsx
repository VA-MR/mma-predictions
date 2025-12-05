import { Link, Outlet, useLocation, Navigate } from 'react-router-dom';
import { useAdminAuth } from '../hooks/useAdminAuth';
import './AdminLayout.css';

export function AdminLayout() {
  const location = useLocation();
  const { isAdminAuthenticated, isLoading, adminLogout } = useAdminAuth();

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const handleLogout = async () => {
    await adminLogout();
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="admin-loading">
        <div className="admin-loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAdminAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <h1>Admin Panel</h1>
          <Link to="/" className="admin-back-link">← На главную</Link>
        </div>
        <nav className="admin-nav">
          <Link 
            to="/admin" 
            className={`admin-nav-link ${location.pathname === '/admin' ? 'active' : ''}`}
          >
            📊 Дашборд
          </Link>
          <Link 
            to="/admin/organizations" 
            className={`admin-nav-link ${isActive('/admin/organizations') ? 'active' : ''}`}
          >
            🏢 Организации
          </Link>
          <Link 
            to="/admin/events" 
            className={`admin-nav-link ${isActive('/admin/events') ? 'active' : ''}`}
          >
            📅 События
          </Link>
          <Link 
            to="/admin/fights" 
            className={`admin-nav-link ${isActive('/admin/fights') ? 'active' : ''}`}
          >
            🥊 Бои
          </Link>
          <Link 
            to="/admin/fighters" 
            className={`admin-nav-link ${isActive('/admin/fighters') ? 'active' : ''}`}
          >
            👤 Бойцы
          </Link>
        </nav>
        <div className="admin-sidebar-footer">
          <button onClick={handleLogout} className="admin-logout-btn">
            🚪 Выйти
          </button>
        </div>
      </aside>
      <main className="admin-content">
        <Outlet />
      </main>
    </div>
  );
}
