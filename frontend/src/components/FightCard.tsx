import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Fight } from '../api/client';
import './FightCard.css';

interface FightCardProps {
  fight: Fight;
  index: number;
}

export default function FightCard({ fight, index }: FightCardProps) {
  const fighter1 = fight.fighter1;
  const fighter2 = fight.fighter2;

  const getCountryFlag = (country: string | null | undefined) => {
    if (!country) return '🌍';
    const flags: Record<string, string> = {
      'USA': '🇺🇸', 'United States': '🇺🇸', 'US': '🇺🇸',
      'Russia': '🇷🇺', 'RU': '🇷🇺',
      'Brazil': '🇧🇷', 'BR': '🇧🇷',
      'Mexico': '🇲🇽', 'MX': '🇲🇽',
      'UK': '🇬🇧', 'United Kingdom': '🇬🇧', 'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
      'Ireland': '🇮🇪', 'IE': '🇮🇪',
      'Japan': '🇯🇵', 'JP': '🇯🇵',
      'China': '🇨🇳', 'CN': '🇨🇳',
      'Poland': '🇵🇱', 'PL': '🇵🇱',
      'Australia': '🇦🇺', 'AU': '🇦🇺',
      'Canada': '🇨🇦', 'CA': '🇨🇦',
      'Nigeria': '🇳🇬', 'NG': '🇳🇬',
      'Cameroon': '🇨🇲', 'CM': '🇨🇲',
      'Georgia': '🇬🇪', 'GE': '🇬🇪',
      'Dagestan': '🇷🇺',
      'Netherlands': '🇳🇱', 'NL': '🇳🇱',
      'France': '🇫🇷', 'FR': '🇫🇷',
      'Germany': '🇩🇪', 'DE': '🇩🇪',
    };
    return flags[country] || '🌍';
  };

  const isChampionship = fight.rounds === 5 || fight.weight_class?.toLowerCase().includes('title');

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Link to={`/fights/${fight.id}`} className="fight-card">
        <div className="fight-card-header">
          {fight.weight_class && (
            <span className="weight-class">{fight.weight_class}</span>
          )}
          {isChampionship && (
            <span className="championship-badge">
              🏆 Титульный бой
            </span>
          )}
          <span className="rounds">{fight.rounds || 3} раундов</span>
        </div>

        <div className="fighters-container">
          {/* Fighter 1 */}
          <div className="fighter fighter-1">
            <div className="fighter-info">
              <div className="fighter-avatar">
                🥊
                <span className="fighter-flag">{getCountryFlag(fighter1?.country)}</span>
              </div>
              <div className="fighter-details">
                <h4 className="fighter-name">
                  {fighter1?.name || 'TBA'}
                </h4>
                <span className="fighter-record">
                  {fighter1?.record || '0-0-0'}
                </span>
                {fighter1?.country && (
                  <span className="fighter-country">{fighter1.country}</span>
                )}
              </div>
            </div>
          </div>

          {/* VS Badge */}
          <div className="vs-badge">VS</div>

          {/* Fighter 2 */}
          <div className="fighter fighter-2">
            <div className="fighter-info">
              <div className="fighter-details">
                <h4 className="fighter-name">
                  {fighter2?.name || 'TBA'}
                </h4>
                <span className="fighter-record">
                  {fighter2?.record || '0-0-0'}
                </span>
                {fighter2?.country && (
                  <span className="fighter-country">{fighter2.country}</span>
                )}
              </div>
              <div className="fighter-avatar">
                🥊
                <span className="fighter-flag">{getCountryFlag(fighter2?.country)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="fight-card-footer">
          <div className="fight-stats">
            <div className="fight-stat">
              <span className="fight-stat-value">—</span>
              <span className="fight-stat-label">Прогнозов</span>
            </div>
            <div className="fight-stat">
              <span className="fight-stat-value">—</span>
              <span className="fight-stat-label">Скоркард</span>
            </div>
          </div>
          <span className="score-prompt">Сделать прогноз →</span>
        </div>
      </Link>
    </motion.div>
  );
}
