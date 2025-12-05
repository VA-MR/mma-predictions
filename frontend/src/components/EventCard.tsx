import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Event } from '../api/client';
import PromotionLogo from './PromotionLogo';
import { formatDateShort, getFightWord } from '../utils/formatters';
import './EventCard.css';

interface EventCardProps {
  event: Event;
  index: number;
}

export default function EventCard({ event, index }: EventCardProps) {
  const getOrgClass = (org: string) => {
    const orgLower = org.toLowerCase();
    if (orgLower.includes('ufc')) return 'ufc';
    if (orgLower.includes('one')) return 'one';
    if (orgLower.includes('bellator')) return 'bellator';
    if (orgLower.includes('pfl')) return 'pfl';
    if (orgLower.includes('aca')) return 'aca';
    if (orgLower.includes('ksw')) return 'ksw';
    return '';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Link to={`/events/${event.slug}`} className="event-card">
        <div className="event-card-body">
          <div className="event-card-header">
            <PromotionLogo organization={event.organization} size="md" />
            <span className={`event-org ${getOrgClass(event.organization)}`}>
              {event.organization}
            </span>
            {!event.is_upcoming && (
              <span className="event-status-badge completed">
                ✓ Завершено
              </span>
            )}
          </div>

          <h3 className="event-name">{event.name}</h3>

          <div className="event-info-grid">
            <div className="event-info-item">
              <span className="info-icon">📅</span>
              <span className="info-text">{formatDateShort(event.event_date)}</span>
            </div>

            {event.location && (
              <div className="event-info-item">
                <span className="info-icon">📍</span>
                <span className="info-text">{event.location}</span>
              </div>
            )}

            {event.time_msk && (
              <div className="event-info-item">
                <span className="info-icon">🕐</span>
                <span className="info-text">{event.time_msk} МСК</span>
              </div>
            )}

            <div className="event-info-item">
              <span className="info-icon">🥊</span>
              <span className="info-text">{event.fight_count} {getFightWord(event.fight_count)}</span>
            </div>
          </div>

          {event.main_event && (event.main_event.fighter1_name || event.main_event.fighter2_name) && (
            <div className="main-event-block">
              <span className="main-event-label">Главный бой</span>
              <div className="main-event-fighters">
                <span className="fighter-name">{event.main_event.fighter1_name || 'TBA'}</span>
                <span className="vs-badge">vs</span>
                <span className="fighter-name">{event.main_event.fighter2_name || 'TBA'}</span>
              </div>
              {event.main_event.weight_class && (
                <span className="weight-class">{event.main_event.weight_class}</span>
              )}
            </div>
          )}

          <div className="event-card-footer">
            <span className="view-card">Смотреть кард →</span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
