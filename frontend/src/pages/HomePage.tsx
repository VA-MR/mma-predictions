import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { getEvents, Event } from '../api/client';
import EventCard from '../components/EventCard';
import { formatDate } from '../utils/formatters';
import './HomePage.css';

export default function HomePage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const data = await getEvents(true);
        setEvents(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load events');
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvents();
  }, []);

  const featuredEvent = events[0];
  const otherEvents = events.slice(1);

  return (
    <div className="container">
      <motion.div
        className="page-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <span className="page-header-badge">
          🔥 Прогнозы на MMA
        </span>
        <h1 className="page-title">
          Предстоящие <span>События</span>
        </h1>
        <p className="page-subtitle">
          Выберите событие для просмотра карда боёв и сделайте свои прогнозы
        </p>
      </motion.div>

      {isLoading && (
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Загрузка событий...</p>
        </div>
      )}

      {error && (
        <div className="error-state">
          <p>❌ {error}</p>
          <button onClick={() => window.location.reload()}>
            Попробовать снова
          </button>
        </div>
      )}

      {!isLoading && !error && events.length === 0 && (
        <div className="empty-state">
          <p>Предстоящих событий не найдено</p>
          <p className="empty-hint">Загляните позже для новых событий</p>
        </div>
      )}

      {!isLoading && !error && events.length > 0 && (
        <>
          {/* Featured Event */}
          {featuredEvent && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Link to={`/events/${featuredEvent.slug}`} className="featured-event">
                <div className="featured-event-image">
                  🏆
                </div>
                <div className="featured-event-content">
                  <span className="featured-badge">
                    ⭐ Главное событие
                  </span>
                  <h2 className="featured-event-name">{featuredEvent.name}</h2>
                  <p className="featured-event-meta">
                    {featuredEvent.organization} • {formatDate(featuredEvent.event_date)}
                    {featuredEvent.location && ` • ${featuredEvent.location}`}
                  </p>
                  <span className="featured-cta">
                    Смотреть кард ({featuredEvent.fight_count} боёв) →
                  </span>
                </div>
              </Link>
            </motion.div>
          )}

          {/* Other Events */}
          {otherEvents.length > 0 && (
            <section className="events-section">
              <div className="section-header">
                <h2 className="section-title">
                  <span className="section-title-icon">📅</span>
                  Ближайшие события
                  <span className="section-count">{otherEvents.length}</span>
                </h2>
                <a href="#" className="view-all-link">
                  Показать все →
                </a>
              </div>
              <div className="events-grid">
                {otherEvents.map((event, index) => (
                  <EventCard key={event.id} event={event} index={index} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
