import { useState, useEffect } from 'react';
import { AdminTable, Column } from '../components/AdminTable';
import { getAdminOrganizations, Organization } from '../api/client';
import './AdminPage.css';

export function AdminOrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      setLoading(true);
      const data = await getAdminOrganizations(0, 100);
      setOrganizations(data);
    } catch (error) {
      console.error('Failed to load organizations:', error);
      alert('Ошибка загрузки организаций');
    } finally {
      setLoading(false);
    }
  };

  const columns: Column<Organization>[] = [
    { header: 'Название', accessor: 'name', width: '300px' },
    { header: 'Количество событий', accessor: 'event_count', width: '200px' },
  ];

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Организации</h1>
      </div>

      <div className="admin-info">
        Организации автоматически создаются из событий. 
        Чтобы добавить организацию, создайте событие с нужной организацией.
      </div>

      <AdminTable
        data={organizations}
        columns={columns}
        loading={loading}
        keyExtractor={(org) => org.name}
      />
    </div>
  );
}

