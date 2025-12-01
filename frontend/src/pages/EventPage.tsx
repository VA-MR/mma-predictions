import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getEvent, EventDetail } from '../api/client';
import FightCard from '../components/FightCard';
import './EventPage.css';

export default function EventPage() {
  const { slug } = useParams<{ slug: string }>();
  const [event, setEvent] = useState<EventDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvent = async () => {
      if (!slug) return;
      
      try {
        const data = await getEvent(slug);
        setEvent(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load event');
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvent();
  }, [slug]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Дата уточняется';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="container">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Загрузка события...</p>
        </div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="container">
        <div className="error-state">
          <p>❌ {error || 'Событие не найдено'}</p>
          <Link to="/" className="back-link">← Назад к событиям</Link>
        </div>
      </div>
    );
  }

  // Separate main card and prelims
  const mainCard = event.fights.filter(f => f.card_type === 'main');
  const prelims = event.fights.filter(f => f.card_type !== 'main');

  return (
    <div className="container">
      <Link to="/" className="back-link">← Назад к событиям</Link>

      <motion.div
        className="event-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <span className="event-org-badge">{event.organization}</span>
        <h1 className="event-title">{event.name}</h1>
        <div className="event-meta">
          <span className="event-date-large">{formatDate(event.event_date)}</span>
          {event.time_msk && <span className="event-time">{event.time_msk} MSK</span>}
          {event.location && (
            <span className="event-location-large">📍 {event.location}</span>
          )}
        </div>
      </motion.div>

      {mainCard.length > 0 && (
        <section className="card-section">
          <h2 className="section-title">
            <span className="section-badge main">Основной кард</span>
            <span className="section-fight-count">{mainCard.length} боёв</span>
          </h2>
          <div className="fights-list">
            {mainCard.map((fight, index) => (
              <FightCard key={fight.id} fight={fight} index={index} />
            ))}
          </div>
        </section>
      )}

      {prelims.length > 0 && (
        <section className="card-section">
          <h2 className="section-title">
            <span className="section-badge prelim">Прелимы</span>
            <span className="section-fight-count">{prelims.length} боёв</span>
          </h2>
          <div className="fights-list">
            {prelims.map((fight, index) => (
              <FightCard key={fight.id} fight={fight} index={index} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

