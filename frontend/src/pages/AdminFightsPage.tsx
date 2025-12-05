import React, { useState, useEffect } from 'react';
import { AdminTable, Column } from '../components/AdminTable';
import { AdminModal } from '../components/AdminModal';
import {
  getAdminFights,
  createAdminFight,
  updateAdminFight,
  deleteAdminFight,
  getAdminEvents,
  getAdminFighters,
  Fight,
  FightCreateUpdate,
  Event,
  FighterDetail,
} from '../api/client';
import './AdminPage.css';

export function AdminFightsPage() {
  const [fights, setFights] = useState<Fight[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [fighters, setFighters] = useState<FighterDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFight, setEditingFight] = useState<Fight | null>(null);
  const [formData, setFormData] = useState<FightCreateUpdate>({
    event_id: 0,
    card_type: 'main',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [fightsData, eventsData, fightersData] = await Promise.all([
        getAdminFights(0, 100),
        getAdminEvents(0, 1000),
        getAdminFighters(0, 1000),
      ]);
      setFights(fightsData);
      setEvents(eventsData);
      setFighters(fightersData);
    } catch (error) {
      console.error('Failed to load data:', error);
      alert('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingFight(null);
    setFormData({
      event_id: events[0]?.id || 0,
      card_type: 'main',
    });
    setIsModalOpen(true);
  };

  const handleEdit = (fight: Fight) => {
    setEditingFight(fight);
    setFormData({
      event_id: fight.event_id,
      fighter1_id: fight.fighter1?.id || null,
      fighter2_id: fight.fighter2?.id || null,
      card_type: fight.card_type,
      weight_class: fight.weight_class || null,
      rounds: fight.rounds || null,
      scheduled_time: fight.scheduled_time || null,
      fight_order: fight.fight_order || null,
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (fight: Fight) => {
    const fighter1Name = fight.fighter1?.name || 'TBA';
    const fighter2Name = fight.fighter2?.name || 'TBA';
    if (!confirm(`Удалить бой ${fighter1Name} vs ${fighter2Name}?`)) return;

    try {
      await deleteAdminFight(fight.id);
      loadData();
    } catch (error) {
      console.error('Failed to delete fight:', error);
      alert('Ошибка удаления боя');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingFight) {
        await updateAdminFight(editingFight.id, formData);
      } else {
        await createAdminFight(formData);
      }
      setIsModalOpen(false);
      loadData();
    } catch (error) {
      console.error('Failed to save fight:', error);
      alert('Ошибка сохранения боя');
    }
  };

  const columns: Column<Fight>[] = [
    { header: 'ID', accessor: 'id', width: '60px' },
    { 
      header: 'Событие', 
      accessor: (fight) => fight.event_name || `Event #${fight.event_id}`,
      width: '250px',
    },
    { 
      header: 'Боец 1', 
      accessor: (fight) => fight.fighter1?.name || 'TBA',
      width: '150px',
    },
    { 
      header: 'Боец 2', 
      accessor: (fight) => fight.fighter2?.name || 'TBA',
      width: '150px',
    },
    { header: 'Категория', accessor: 'weight_class', width: '120px' },
    { header: 'Раунды', accessor: 'rounds', width: '80px' },
    { 
      header: 'Карта', 
      accessor: (fight) => fight.card_type === 'main' ? 'Основная' : 'Прелиминары',
      width: '100px',
    },
  ];

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Управление боями</h1>
        <button className="admin-btn admin-btn-primary" onClick={handleCreate}>
          Создать бой
        </button>
      </div>

      <AdminTable
        data={fights}
        columns={columns}
        onEdit={handleEdit}
        onDelete={handleDelete}
        loading={loading}
        keyExtractor={(fight) => fight.id}
      />

      <AdminModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingFight ? 'Редактировать бой' : 'Создать бой'}
      >
        <form onSubmit={handleSubmit} className="admin-form">
          <div className="admin-form-group">
            <label>Событие *</label>
            <select
              required
              value={formData.event_id}
              onChange={(e) => setFormData({ ...formData, event_id: parseInt(e.target.value) })}
            >
              <option value="">Выберите событие</option>
              {events.map((event) => (
                <option key={event.id} value={event.id}>
                  {event.name} ({event.organization})
                </option>
              ))}
            </select>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Боец 1</label>
              <select
                value={formData.fighter1_id || ''}
                onChange={(e) => setFormData({ ...formData, fighter1_id: e.target.value ? parseInt(e.target.value) : null })}
              >
                <option value="">TBA</option>
                {fighters.map((fighter) => (
                  <option key={fighter.id} value={fighter.id}>
                    {fighter.name} ({fighter.record})
                  </option>
                ))}
              </select>
            </div>
            <div className="admin-form-group">
              <label>Боец 2</label>
              <select
                value={formData.fighter2_id || ''}
                onChange={(e) => setFormData({ ...formData, fighter2_id: e.target.value ? parseInt(e.target.value) : null })}
              >
                <option value="">TBA</option>
                {fighters.map((fighter) => (
                  <option key={fighter.id} value={fighter.id}>
                    {fighter.name} ({fighter.record})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Тип карты</label>
              <select
                value={formData.card_type}
                onChange={(e) => setFormData({ ...formData, card_type: e.target.value })}
              >
                <option value="main">Основная</option>
                <option value="prelim">Прелиминары</option>
              </select>
            </div>
            <div className="admin-form-group">
              <label>Раунды</label>
              <input
                type="number"
                min="1"
                max="5"
                value={formData.rounds || ''}
                onChange={(e) => setFormData({ ...formData, rounds: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Весовая категория</label>
              <input
                type="text"
                value={formData.weight_class || ''}
                onChange={(e) => setFormData({ ...formData, weight_class: e.target.value || null })}
              />
            </div>
            <div className="admin-form-group">
              <label>Порядок боя</label>
              <input
                type="number"
                value={formData.fight_order || ''}
                onChange={(e) => setFormData({ ...formData, fight_order: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
          </div>

          <div className="admin-form-group">
            <label>Время (МСК)</label>
            <input
              type="time"
              value={formData.scheduled_time || ''}
              onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value || null })}
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
    </div>
  );
}

