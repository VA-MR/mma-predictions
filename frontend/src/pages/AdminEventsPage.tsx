import React, { useState, useEffect } from 'react';
import { AdminTable, Column } from '../components/AdminTable';
import { AdminModal } from '../components/AdminModal';
import { FightResultModal } from '../components/FightResultModal';
import {
  getAdminEvents,
  createAdminEvent,
  updateAdminEvent,
  deleteAdminEvent,
  getEventFights,
  createAdminFight,
  deleteAdminFight,
  Event,
  EventCreateUpdate,
  Fight,
  FightCreateUpdate,
  Fighter,
  getAdminFighters,
} from '../api/client';
import './AdminPage.css';

export function AdminEventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'fights'>('details');
  
  // Filters and sorting
  const [statusFilter, setStatusFilter] = useState<'all' | 'upcoming' | 'past'>('all');
  const [organizationFilter, setOrganizationFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<'closest' | 'newest' | 'oldest'>('closest');
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // Resolve popup
  const [isResolveFightsOpen, setIsResolveFightsOpen] = useState(false);
  const [resolveEvent, setResolveEvent] = useState<Event | null>(null);
  
  const [formData, setFormData] = useState<EventCreateUpdate>({
    name: '',
    organization: '',
    url: '',
    slug: '',
    is_upcoming: true,
  });

  // Fights tab state
  const [eventFights, setEventFights] = useState<Fight[]>([]);
  const [loadingFights, setLoadingFights] = useState(false);
  const [isFightModalOpen, setIsFightModalOpen] = useState(false);
  const [isResultModalOpen, setIsResultModalOpen] = useState(false);
  const [selectedFight, setSelectedFight] = useState<Fight | null>(null);
  const [fighters, setFighters] = useState<Fighter[]>([]);
  const [fightFormData, setFightFormData] = useState<FightCreateUpdate>({
    event_id: 0,
    fighter1_id: null,
    fighter2_id: null,
    card_type: 'main',
    weight_class: null,
    rounds: 3,
    scheduled_time: null,
    fight_order: null,
  });

  useEffect(() => {
    loadEvents();
    loadFighters();
  }, []);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await getAdminEvents(0, 100);
      setEvents(data);
    } catch (error) {
      console.error('Failed to load events:', error);
      alert('Ошибка загрузки событий');
    } finally {
      setLoading(false);
    }
  };

  const loadFighters = async () => {
    try {
      const data = await getAdminFighters(0, 500);
      setFighters(data);
    } catch (error) {
      console.error('Failed to load fighters:', error);
    }
  };

  const loadEventFights = async (eventId: number) => {
    try {
      setLoadingFights(true);
      const data = await getEventFights(eventId);
      setEventFights(data);
    } catch (error) {
      console.error('Failed to load fights:', error);
      alert('Ошибка загрузки боёв');
    } finally {
      setLoadingFights(false);
    }
  };

  const handleCreate = () => {
    setEditingEvent(null);
    setActiveTab('details');
    setEventFights([]); // Clear fights list for new event
    setFormData({
      name: '',
      organization: '',
      url: '',
      slug: '',
      is_upcoming: true,
    });
    setIsModalOpen(true);
  };

  const handleEdit = (event: Event) => {
    setEditingEvent(event);
    setActiveTab('details');
    setFormData({
      name: event.name,
      organization: event.organization,
      event_date: event.event_date || null,
      time_msk: event.time_msk || null,
      location: event.location || null,
      url: event.url,
      slug: event.slug,
      is_upcoming: event.is_upcoming,
    });
    setIsModalOpen(true);
    
    // Load fights for this event
    loadEventFights(event.id);
  };

  const handleDelete = async (event: Event) => {
    if (!confirm(`Удалить событие ${event.name}?`)) return;

    try {
      await deleteAdminEvent(event.id);
      loadEvents();
    } catch (error) {
      console.error('Failed to delete event:', error);
      alert('Ошибка удаления события');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingEvent) {
        await updateAdminEvent(editingEvent.id, formData);
      } else {
        const newEvent = await createAdminEvent(formData);
        setEditingEvent(newEvent);
      }
      loadEvents();
    } catch (error) {
      console.error('Failed to save event:', error);
      alert('Ошибка сохранения события');
    }
  };

  // Fight management handlers
  const handleAddFight = () => {
    if (!editingEvent) return;
    
    setFightFormData({
      event_id: editingEvent.id,
      fighter1_id: null,
      fighter2_id: null,
      card_type: 'main',
      weight_class: null,
      rounds: 3,
      scheduled_time: null,
      fight_order: null,
    });
    setIsFightModalOpen(true);
  };

  const handleDeleteFight = async (fight: Fight) => {
    if (!confirm(`Удалить бой ${fight.fighter1?.name || 'TBA'} vs ${fight.fighter2?.name || 'TBA'}?`)) return;

    try {
      await deleteAdminFight(fight.id);
      if (editingEvent) {
        loadEventFights(editingEvent.id);
      }
    } catch (error) {
      console.error('Failed to delete fight:', error);
      alert('Ошибка удаления боя');
    }
  };

  const handleEnterResult = (fight: Fight) => {
    setSelectedFight(fight);
    setIsResultModalOpen(true);
  };

  const handleResultSuccess = () => {
    if (resolveEvent) {
      loadEventFights(resolveEvent.id).then(() => {
        setIsResolveFightsOpen(true); // Reopen the resolve modal
      });
    }
    if (editingEvent) {
      loadEventFights(editingEvent.id);
    }
    loadEvents(); // Reload events to update status
  };

  const handleResolve = (event: Event) => {
    setResolveEvent(event);
    loadEventFights(event.id).then(() => {
      setIsResolveFightsOpen(true);
    });
  };

  // Get unique organizations for filter
  const organizations = Array.from(new Set(events.map(e => e.organization))).sort();

  // Filter and sort events
  const filteredAndSortedEvents = events
    .filter(event => {
      // Status filter
      if (statusFilter === 'upcoming' && !event.is_upcoming) return false;
      if (statusFilter === 'past' && event.is_upcoming) return false;
      
      // Organization filter
      if (organizationFilter !== 'all' && event.organization !== organizationFilter) return false;
      
      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesName = event.name.toLowerCase().includes(query);
        const matchesOrg = event.organization.toLowerCase().includes(query);
        const matchesLocation = event.location?.toLowerCase().includes(query);
        if (!matchesName && !matchesOrg && !matchesLocation) return false;
      }
      
      return true;
    })
    .sort((a, b) => {
      // Sort by date
      const dateA = a.event_date ? new Date(a.event_date).getTime() : Infinity;
      const dateB = b.event_date ? new Date(b.event_date).getTime() : Infinity;
      const now = Date.now();
      
      if (sortOrder === 'closest') {
        // Sort by closest to current date (upcoming events first, then past events)
        const diffA = Math.abs(dateA - now);
        const diffB = Math.abs(dateB - now);
        return diffA - diffB;
      } else if (sortOrder === 'newest') {
        return dateB - dateA;
      } else {
        return dateA - dateB;
      }
    });

  const handleFightSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await createAdminFight(fightFormData);
      setIsFightModalOpen(false);
      if (editingEvent) {
        loadEventFights(editingEvent.id);
      }
    } catch (error) {
      console.error('Failed to save fight:', error);
      alert('Ошибка сохранения боя');
    }
  };

  const columns: Column<Event>[] = [
    { header: 'ID', accessor: 'id', width: '60px' },
    { header: 'Название', accessor: 'name', width: '300px' },
    { header: 'Организация', accessor: 'organization', width: '120px' },
    { 
      header: 'Дата', 
      accessor: (event) => event.event_date || 'TBA',
      width: '120px',
    },
    { header: 'Локация', accessor: 'location', width: '200px' },
    { 
      header: 'Статус', 
      accessor: (event) => event.is_upcoming ? 'Предстоящее' : 'Прошедшее',
      width: '120px',
    },
  ];

  const renderEventActions = (event: Event) => (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
      <button
        onClick={() => handleResolve(event)}
        className="admin-icon-btn"
        title="Внести результаты"
        style={{ 
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontSize: '20px',
          padding: '4px 8px',
          color: '#3b82f6'
        }}
      >
        ✅
      </button>
      <button
        onClick={() => handleEdit(event)}
        className="admin-icon-btn"
        title="Изменить"
        style={{ 
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontSize: '18px',
          padding: '4px 8px',
          color: '#3b82f6'
        }}
      >
        ✏️
      </button>
      <button
        onClick={() => handleDelete(event)}
        className="admin-icon-btn"
        title="Удалить"
        style={{ 
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontSize: '18px',
          padding: '4px 8px',
          color: '#ef4444'
        }}
      >
        🗑️
      </button>
    </div>
  );

  const fightColumns: Column<Fight>[] = [
    { header: 'ID', accessor: 'id', width: '60px' },
    { 
      header: 'Боец 1', 
      accessor: (fight) => fight.fighter1?.name || 'TBA',
      width: '200px',
    },
    { 
      header: 'Боец 2', 
      accessor: (fight) => fight.fighter2?.name || 'TBA',
      width: '200px',
    },
    { header: 'Вес. категория', accessor: 'weight_class', width: '150px' },
    { header: 'Раунды', accessor: 'rounds', width: '80px' },
    { header: 'Тип', accessor: 'card_type', width: '100px' },
  ];

  const renderFightActions = (fight: Fight) => (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
      <button
        className="admin-btn admin-btn-primary"
        onClick={() => handleEnterResult(fight)}
        style={{ padding: '6px 12px', fontSize: '13px' }}
      >
        Результат
      </button>
      <button
        onClick={() => handleDeleteFight(fight)}
        className="admin-icon-btn"
        title="Удалить бой"
        style={{ 
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontSize: '18px',
          padding: '4px 8px',
          color: '#ef4444'
        }}
      >
        🗑️
      </button>
    </div>
  );

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Управление событиями</h1>
        <button className="admin-btn admin-btn-primary" onClick={handleCreate}>
          Создать событие
        </button>
      </div>

      {/* Filters */}
      <div className="admin-filters" style={{ 
        display: 'flex', 
        gap: '16px', 
        marginBottom: '24px',
        flexWrap: 'wrap',
        alignItems: 'center',
        padding: '16px',
        background: 'var(--bg-card)',
        borderRadius: '8px',
        border: '1px solid var(--border-color)'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: '1', minWidth: '200px' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Поиск
          </label>
          <input
            type="text"
            placeholder="Поиск по названию, организации..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              fontSize: '0.9rem',
            }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Статус
          </label>
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              fontSize: '0.9rem',
              minWidth: '150px'
            }}
          >
            <option value="all">Все</option>
            <option value="upcoming">Предстоящее</option>
            <option value="past">Прошедшее</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Организация
          </label>
          <select 
            value={organizationFilter}
            onChange={(e) => setOrganizationFilter(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              fontSize: '0.9rem',
              minWidth: '150px'
            }}
          >
            <option value="all">Все организации</option>
            {organizations.map(org => (
              <option key={org} value={org}>{org}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Сортировка по дате
          </label>
          <select 
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              fontSize: '0.9rem',
              minWidth: '150px'
            }}
          >
            <option value="closest">Ближайшие первыми</option>
            <option value="newest">Новые первыми</option>
            <option value="oldest">Старые первыми</option>
          </select>
        </div>

        <div style={{ 
          marginLeft: 'auto', 
          display: 'flex', 
          alignItems: 'flex-end',
          paddingBottom: '4px'
        }}>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Найдено: <strong style={{ color: 'var(--text-primary)' }}>{filteredAndSortedEvents.length}</strong> событий
          </span>
        </div>
      </div>

      <AdminTable
        data={filteredAndSortedEvents}
        columns={columns}
        loading={loading}
        keyExtractor={(event) => event.id}
        customActions={renderEventActions}
      />

      <AdminModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingEvent ? 'Редактировать событие' : 'Создать событие'}
      >
        {/* Tab Navigation */}
        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === 'details' ? 'active' : ''}`}
            onClick={() => setActiveTab('details')}
          >
            Детали события
          </button>
          {editingEvent && (
            <button
              className={`admin-tab ${activeTab === 'fights' ? 'active' : ''}`}
              onClick={() => setActiveTab('fights')}
            >
              Бои ({eventFights.length})
            </button>
          )}
        </div>

        {/* Details Tab */}
        {activeTab === 'details' && (
          <form onSubmit={handleSubmit} className="admin-form">
            <div className="admin-form-group">
              <label>Название *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div className="admin-form-row">
              <div className="admin-form-group">
                <label>Организация *</label>
                <input
                  type="text"
                  required
                  value={formData.organization}
                  onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                />
              </div>
              <div className="admin-form-group">
                <label>Дата</label>
                <input
                  type="date"
                  value={formData.event_date || ''}
                  onChange={(e) => setFormData({ ...formData, event_date: e.target.value || null })}
                />
              </div>
            </div>

            <div className="admin-form-row">
              <div className="admin-form-group">
                <label>Время (МСК)</label>
                <input
                  type="time"
                  value={formData.time_msk || ''}
                  onChange={(e) => setFormData({ ...formData, time_msk: e.target.value || null })}
                />
              </div>
              <div className="admin-form-group">
                <label>Локация</label>
                <input
                  type="text"
                  value={formData.location || ''}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value || null })}
                />
              </div>
            </div>

            <div className="admin-form-group">
              <label>URL *</label>
              <input
                type="text"
                required
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              />
            </div>

            <div className="admin-form-group">
              <label>Slug *</label>
              <input
                type="text"
                required
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              />
            </div>

            <div className="admin-form-group">
              <label className="admin-checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_upcoming}
                  onChange={(e) => setFormData({ ...formData, is_upcoming: e.target.checked })}
                />
                Предстоящее событие
              </label>
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
        )}

        {/* Fights Tab */}
        {activeTab === 'fights' && (
          <div className="admin-fights-tab">
            {!editingEvent ? (
              <div className="admin-empty">
                Сохраните событие сначала, чтобы добавить бои
              </div>
            ) : (
              <>
                <div className="admin-fights-header">
                  <button className="admin-btn admin-btn-primary" onClick={handleAddFight}>
                    Добавить бой
                  </button>
                </div>

                {loadingFights ? (
                  <div className="admin-loading">Загрузка боёв...</div>
                ) : eventFights.length === 0 ? (
                  <div className="admin-empty">Нет боёв для этого события</div>
                ) : (
                  <AdminTable
                    data={eventFights}
                    columns={fightColumns}
                    onDelete={handleDeleteFight}
                    loading={loadingFights}
                    keyExtractor={(fight) => fight.id}
                    customActions={renderFightActions}
                  />
                )}
              </>
            )}
          </div>
        )}
      </AdminModal>

      {/* Fight Creation Modal */}
      <AdminModal
        isOpen={isFightModalOpen}
        onClose={() => setIsFightModalOpen(false)}
        title="Добавить бой"
      >
        <form onSubmit={handleFightSubmit} className="admin-form">
          <div className="admin-form-group">
            <label>Боец 1 *</label>
            <select
              required
              value={fightFormData.fighter1_id || ''}
              onChange={(e) => setFightFormData({ ...fightFormData, fighter1_id: e.target.value ? parseInt(e.target.value) : null })}
            >
              <option value="">Выберите бойца</option>
              {fighters.map(fighter => (
                <option key={fighter.id} value={fighter.id}>
                  {fighter.name} ({fighter.record})
                </option>
              ))}
            </select>
          </div>

          <div className="admin-form-group">
            <label>Боец 2 *</label>
            <select
              required
              value={fightFormData.fighter2_id || ''}
              onChange={(e) => setFightFormData({ ...fightFormData, fighter2_id: e.target.value ? parseInt(e.target.value) : null })}
            >
              <option value="">Выберите бойца</option>
              {fighters.map(fighter => (
                <option key={fighter.id} value={fighter.id}>
                  {fighter.name} ({fighter.record})
                </option>
              ))}
            </select>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Весовая категория</label>
              <input
                type="text"
                value={fightFormData.weight_class || ''}
                onChange={(e) => setFightFormData({ ...fightFormData, weight_class: e.target.value || null })}
                placeholder="напр. Lightweight"
              />
            </div>
            <div className="admin-form-group">
              <label>Раунды</label>
              <input
                type="number"
                min="1"
                max="5"
                value={fightFormData.rounds || 3}
                onChange={(e) => setFightFormData({ ...fightFormData, rounds: parseInt(e.target.value) || 3 })}
              />
            </div>
          </div>

          <div className="admin-form-row">
            <div className="admin-form-group">
              <label>Тип карты</label>
              <select
                value={fightFormData.card_type}
                onChange={(e) => setFightFormData({ ...fightFormData, card_type: e.target.value })}
              >
                <option value="main">Main Card</option>
                <option value="prelim">Prelims</option>
              </select>
            </div>
            <div className="admin-form-group">
              <label>Порядок боя</label>
              <input
                type="number"
                min="1"
                value={fightFormData.fight_order || ''}
                onChange={(e) => setFightFormData({ ...fightFormData, fight_order: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
          </div>

          <div className="admin-form-actions">
            <button type="button" className="admin-btn" onClick={() => setIsFightModalOpen(false)}>
              Отмена
            </button>
            <button type="submit" className="admin-btn admin-btn-primary">
              Добавить
            </button>
          </div>
        </form>
      </AdminModal>

      {/* Fight Result Modal */}
      <FightResultModal
        isOpen={isResultModalOpen}
        onClose={() => setIsResultModalOpen(false)}
        fight={selectedFight}
        onSuccess={handleResultSuccess}
      />

      {/* Resolve Fights Popup */}
      <AdminModal
        isOpen={isResolveFightsOpen}
        onClose={() => setIsResolveFightsOpen(false)}
        title={`Внести результаты: ${resolveEvent?.name || ''}`}
      >
        <div style={{ padding: '16px 0' }}>
          {loadingFights ? (
            <div className="admin-loading">Загрузка боёв...</div>
          ) : eventFights.length === 0 ? (
            <div className="admin-info">
              <p>Нет боёв для этого события</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {eventFights.map(fight => {
                const hasResult = !!fight.result;
                
                const getWinnerName = () => {
                  if (!fight.result) return null;
                  if (fight.result.winner === 'fighter1') return fight.fighter1?.name || 'Fighter 1';
                  if (fight.result.winner === 'fighter2') return fight.fighter2?.name || 'Fighter 2';
                  if (fight.result.winner === 'draw') return 'Ничья';
                  if (fight.result.winner === 'no_contest') return 'No Contest';
                  return null;
                };

                const getMethodEmoji = () => {
                  if (!fight.result) return null;
                  const emojiMap: Record<string, string> = {
                    'ko_tko': '🥊',
                    'submission': '🤼',
                    'decision': '⚖️',
                    'dq': '⛔'
                  };
                  return emojiMap[fight.result.method] || '';
                };

                const getMethodText = () => {
                  if (!fight.result) return null;
                  const methodMap: Record<string, string> = {
                    'ko_tko': 'KO/TKO',
                    'submission': 'Submission',
                    'decision': 'Decision',
                    'dq': 'Disqualification'
                  };
                  return methodMap[fight.result.method] || fight.result.method;
                };

                return (
                  <div 
                    key={fight.id}
                    style={{
                      padding: '20px',
                      background: hasResult 
                        ? 'linear-gradient(135deg, #e8f5e9 0%, #f1f8f4 100%)' 
                        : 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
                      borderRadius: '12px',
                      border: hasResult ? '2px solid #4caf50' : '2px solid #e0e0e0',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '20px',
                      boxShadow: hasResult 
                        ? '0 4px 12px rgba(76, 175, 80, 0.15)' 
                        : '0 2px 8px rgba(0, 0, 0, 0.08)',
                      transition: 'all 0.2s ease',
                      position: 'relative',
                      overflow: 'hidden'
                    }}
                  >
                    {/* Status indicator dot */}
                    {hasResult && (
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '6px',
                        height: '100%',
                        background: 'linear-gradient(180deg, #4caf50 0%, #66bb6a 100%)'
                      }} />
                    )}

                    <div style={{ flex: 1, paddingLeft: hasResult ? '12px' : '0' }}>
                      {/* Fight matchup */}
                      <div style={{ 
                        fontSize: '1.1rem', 
                        fontWeight: 700, 
                        color: '#212529',
                        marginBottom: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <span>{fight.fighter1?.name || 'TBA'}</span>
                        <span style={{ 
                          fontSize: '0.9rem', 
                          color: '#6c757d',
                          fontWeight: 500 
                        }}>vs</span>
                        <span>{fight.fighter2?.name || 'TBA'}</span>
                      </div>

                      {/* Fight details */}
                      <div style={{ 
                        fontSize: '0.85rem', 
                        color: '#6c757d',
                        marginBottom: hasResult ? '10px' : '0',
                        display: 'flex',
                        gap: '12px',
                        flexWrap: 'wrap'
                      }}>
                        {fight.weight_class && (
                          <span style={{ 
                            display: 'inline-flex', 
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            ⚖️ {fight.weight_class}
                          </span>
                        )}
                        <span style={{ 
                          display: 'inline-flex', 
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          🥋 {fight.rounds} раундов
                        </span>
                        <span style={{
                          padding: '2px 8px',
                          background: fight.card_type === 'main' ? '#e3f2fd' : '#fff3e0',
                          color: fight.card_type === 'main' ? '#1976d2' : '#f57c00',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase'
                        }}>
                          {fight.card_type}
                        </span>
                      </div>

                      {/* Winner display */}
                      {hasResult && (
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '10px 14px',
                          background: 'rgba(76, 175, 80, 0.12)',
                          borderRadius: '8px',
                          border: '1px solid rgba(76, 175, 80, 0.3)'
                        }}>
                          <span style={{ fontSize: '1.3rem' }}>🏆</span>
                          <div style={{ flex: 1 }}>
                            <div style={{
                              fontSize: '0.95rem',
                              fontWeight: 700,
                              color: '#2e7d32'
                            }}>
                              {getWinnerName()}
                            </div>
                            <div style={{
                              fontSize: '0.8rem',
                              color: '#558b2f',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              marginTop: '2px'
                            }}>
                              <span>{getMethodEmoji()}</span>
                              <span>{getMethodText()}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Action button */}
                    <button
                      onClick={() => {
                        setSelectedFight(fight);
                        setIsResolveFightsOpen(false);
                        setIsResultModalOpen(true);
                      }}
                      title={hasResult ? 'Изменить результат' : 'Внести результат'}
                      style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '12px',
                        border: 'none',
                        background: hasResult 
                          ? 'linear-gradient(135deg, #ffa726 0%, #fb8c00 100%)'
                          : 'linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%)',
                        color: 'white',
                        fontSize: '1.5rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                        transition: 'all 0.2s ease',
                        flexShrink: 0
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.05)';
                        e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.2)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                      }}
                    >
                      {hasResult ? '✏️' : '➕'}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </AdminModal>
    </div>
  );
}
