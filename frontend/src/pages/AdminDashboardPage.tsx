import { Link } from 'react-router-dom';
import './AdminPage.css';

export function AdminDashboardPage() {
  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Админ панель</h1>
      </div>

      <div className="admin-dashboard">
        <Link to="/admin/organizations" className="admin-dashboard-card">
          <div className="admin-dashboard-icon">🏢</div>
          <h2>Организации</h2>
          <p>Просмотр всех организаций</p>
        </Link>

        <Link to="/admin/events" className="admin-dashboard-card">
          <div className="admin-dashboard-icon">📅</div>
          <h2>События</h2>
          <p>Управление событиями</p>
        </Link>

        <Link to="/admin/fights" className="admin-dashboard-card">
          <div className="admin-dashboard-icon">🥊</div>
          <h2>Бои</h2>
          <p>Управление боями</p>
        </Link>

        <Link to="/admin/fighters" className="admin-dashboard-card">
          <div className="admin-dashboard-icon">👤</div>
          <h2>Бойцы</h2>
          <p>Управление бойцами</p>
        </Link>
      </div>
    </div>
  );
}

