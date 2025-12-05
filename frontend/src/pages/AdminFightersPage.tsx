import { useState, useEffect } from 'react';
import { AdminTable, Column } from '../components/AdminTable';
import { AdminModal } from '../components/AdminModal';
import FighterModal from '../components/FighterModal';
import {
  getAdminFighters,
  createAdminFighter,
  updateAdminFighter,
  deleteAdminFighter,
  FighterDetail,
  FighterCreateUpdate,
} from '../api/client';
import './AdminPage.css';

export function AdminFightersPage() {
  const [fighters, setFighters] = useState<FighterDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFighter, setEditingFighter] = useState<FighterDetail | null>(null);
  const [viewFighterId, setViewFighterId] = useState<number | null>(null);
  const [formData, setFormData] = useState<FighterCreateUpdate>({
    name: '',
    wins: 0,
    losses: 0,
    draws: 0,
  });

  useEffect(() => {
    loadFighters();
  }, [searchQuery]);

  const loadFighters = async () => {
    try {
      setLoading(true);
      const data = await getAdminFighters(0, 100, searchQuery || undefined);
      setFighters(data);
    } catch (error) {
      console.error('Failed to load fighters:', error);
      alert('Ошибка загрузки бойцов');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingFighter(null);
    setFormData({
      name: '',
      wins: 0,
      losses: 0,
      draws: 0,
    });
    setIsModalOpen(true);
  };

  const handleEdit = (fighter: FighterDetail) => {
    setEditingFighter(fighter);
    setFormData({
      name: fighter.name,
      name_english: fighter.name_english,
      country: fighter.country,
      wins: fighter.wins,
      losses: fighter.losses,
      draws: fighter.draws,
      age: fighter.age,
      height_cm: fighter.height_cm,
      weight_kg: fighter.weight_kg,
      reach_cm: fighter.reach_cm,
      style: fighter.style,
      weight_class: fighter.weight_class,
      ranking: fighter.ranking,
      wins_ko_tko: fighter.wins_ko_tko,
      wins_submission: fighter.wins_submission,
      wins_decision: fighter.wins_decision,
      losses_ko_tko: fighter.losses_ko_tko,
      losses_submission: fighter.losses_submission,
      losses_decision: fighter.losses_decision,
      profile_url: fighter.profile_url,
      profile_scraped: fighter.profile_scraped,
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (fighter: FighterDetail) => {
    if (!confirm(`Удалить бойца ${fighter.name}?`)) return;

    try {
      await deleteAdminFighter(fighter.id);
      loadFighters();
    } catch (error) {
      console.error('Failed to delete fighter:', error);
      alert('Ошибка удаления бойца');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingFighter) {
        await updateAdminFighter(editingFighter.id, formData);
      } else {
        await createAdminFighter(formData);
      }
      setIsModalOpen(false);
      loadFighters();
    } catch (error) {
      console.error('Failed to save fighter:', error);
      alert('Ошибка сохранения бойца');
    }
  };

  const handleViewFighter = (fighter: FighterDetail, e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation();
    }
    console.log('AdminFightersPage: opening modal for fighter ID:', fighter.id);
    setViewFighterId(fighter.id);
  };

  const columns: Column<FighterDetail>[] = [
    { header: 'ID', accessor: 'id', width: '60px' },
    { 
      header: 'Имя', 
      accessor: 'name', 
      width: '200px',
      render: (fighter) => (
        <span 
          onClick={(e) => handleViewFighter(fighter, e)}
          style={{ 
            cursor: 'pointer', 
            color: '#00d4ff',
            textDecoration: 'underline',
            textDecorationColor: 'transparent',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.textDecorationColor = '#00d4ff';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.textDecorationColor = 'transparent';
          }}
        >
          {fighter.name}
        </span>
      )
    },
    { header: 'Страна', accessor: 'country', width: '100px' },
    {
      header: 'Рекорд',
      accessor: (fighter) => `${fighter.wins}-${fighter.losses}-${fighter.draws}`,
      width: '100px',
    },
    { header: 'Весовая категория', accessor: 'weight_class', width: '150px' },
  ];

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Управление бойцами</h1>
        <button className="admin-btn admin-btn-primary" onClick={handleCreate}>
          Создать бойца
        </button>
      </div>

      <div className="admin-search">
        <input
          type="text"
          placeholder="Поиск по имени..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="admin-search-input"
        />
      </div>

      <AdminTable
        data={fighters}
        columns={columns}
        onEdit={handleEdit}
        onDelete={handleDelete}
        loading={loading}
        keyExtractor={(fighter) => fighter.id}
      />

      <AdminModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingFighter ? 'Редактировать бойца' : 'Создать бойца'}
      >
        <form onSubmit={handleSubmit} className="admin-form">
          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Имя *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className="admin-form-group">
              <label>Имя (English)</label>
              <input
                type="text"
                value={formData.name_english || ''}
                onChange={(e) => setFormData({ ...formData, name_english: e.target.value || null })}
              />
            </div>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Страна</label>
              <input
                type="text"
                value={formData.country || ''}
                onChange={(e) => setFormData({ ...formData, country: e.target.value || null })}
              />
            </div>
            <div className="admin-form-group">
              <label>Возраст</label>
              <input
                type="number"
                value={formData.age || ''}
                onChange={(e) => setFormData({ ...formData, age: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Победы</label>
              <input
                type="number"
                value={formData.wins}
                onChange={(e) => setFormData({ ...formData, wins: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div className="admin-form-group">
              <label>Поражения</label>
              <input
                type="number"
                value={formData.losses}
                onChange={(e) => setFormData({ ...formData, losses: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div className="admin-form-group">
              <label>Ничьи</label>
              <input
                type="number"
                value={formData.draws}
                onChange={(e) => setFormData({ ...formData, draws: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Рост (см)</label>
              <input
                type="number"
                value={formData.height_cm || ''}
                onChange={(e) => setFormData({ ...formData, height_cm: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
            <div className="admin-form-group">
              <label>Вес (кг)</label>
              <input
                type="number"
                step="0.1"
                value={formData.weight_kg || ''}
                onChange={(e) => setFormData({ ...formData, weight_kg: e.target.value ? parseFloat(e.target.value) : null })}
              />
            </div>
            <div className="admin-form-group">
              <label>Размах рук (см)</label>
              <input
                type="number"
                value={formData.reach_cm || ''}
                onChange={(e) => setFormData({ ...formData, reach_cm: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Стиль</label>
              <input
                type="text"
                value={formData.style || ''}
                onChange={(e) => setFormData({ ...formData, style: e.target.value || null })}
              />
            </div>
            <div className="admin-form-group">
              <label>Весовая категория</label>
              <input
                type="text"
                value={formData.weight_class || ''}
                onChange={(e) => setFormData({ ...formData, weight_class: e.target.value || null })}
              />
            </div>
            <div className="admin-form-group">
              <label>Рейтинг</label>
              <input
                type="text"
                value={formData.ranking || ''}
                onChange={(e) => setFormData({ ...formData, ranking: e.target.value || null })}
              />
            </div>
          </div>

          <div className="admin-form-group">
            <label>URL профиля</label>
            <input
              type="text"
              value={formData.profile_url || ''}
              onChange={(e) => setFormData({ ...formData, profile_url: e.target.value || null })}
            />
          </div>

          <div className="admin-form-actions">
            <button type="button" className="admin-btn" onClick={() => setIsModalOpen(false)}>
              Отмена
            </button>
            <button type="submit" className="admin-btn admin-btn-primary">
              Сохранить
            </button>
          </div>
        </form>
      </AdminModal>

      {/* Fighter View Modal */}
      {viewFighterId && (
        <FighterModal
          fighterId={viewFighterId}
          isOpen={viewFighterId !== null}
          onClose={() => setViewFighterId(null)}
          useAdminEndpoint={true}
        />
      )}
    </div>
  );
}

