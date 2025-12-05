import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { getFighter, getAdminFighter, getFighterFights, Fighter, Fight } from '../api/client';
import { getCountryFlag } from '../utils/formatters';
import './FighterModal.css';

interface FighterModalProps {
  fighterId: number;
  isOpen: boolean;
  onClose: () => void;
  useAdminEndpoint?: boolean;
}

export default function FighterModal({ fighterId, isOpen, onClose, useAdminEndpoint = false }: FighterModalProps) {
  const [fighter, setFighter] = useState<Fighter | null>(null);
  const [fights, setFights] = useState<Fight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !fighterId || fighterId <= 0) {
      console.log('FighterModal: skipping fetch', { isOpen, fighterId });
      return;
    }

    console.log('FighterModal: fetching fighter with ID:', fighterId, 'using admin endpoint:', useAdminEndpoint);

    const fetchFighter = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [fighterData, fightsData] = await Promise.all([
          useAdminEndpoint 
            ? getAdminFighter(fighterId)
            : getFighter(fighterId),
          getFighterFights(fighterId, 10).catch(() => [] as Fight[])
        ]);
        
        console.log('FighterModal: successfully loaded fighter:', fighterData.name);
        setFighter(fighterData);
        setFights(fightsData);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load fighter';
        console.error('FighterModal: error loading fighter:', errorMessage, err);
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFighter();
  }, [fighterId, isOpen, useAdminEndpoint]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        className="fighter-modal-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={handleBackdropClick}
      >
        <motion.div
          className="fighter-modal"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          <button className="modal-close" onClick={onClose}>
            ✕
          </button>

          {isLoading && (
            <div className="modal-loading">
              <div className="loading-spinner" />
              <p>Загрузка данных бойца...</p>
            </div>
          )}

          {error && (
            <div className="modal-error">
              <p>❌ {error}</p>
            </div>
          )}

          {fighter && !isLoading && !error && (
            <>
              <div className="modal-header">
                <div className="fighter-avatar-large">
                  🥊
                  <span className="fighter-flag-large">{getCountryFlag(fighter.country)}</span>
                </div>
                <div className="fighter-header-info">
                  <h2 className="fighter-name-modal">{fighter.name}</h2>
                  {fighter.name_english && fighter.name_english !== fighter.name && (
                    <p className="fighter-name-english">{fighter.name_english}</p>
                  )}
                  <div className="fighter-record-modal">{fighter.record}</div>
                  {fighter.country && (
                    <div className="fighter-country-modal">
                      {getCountryFlag(fighter.country)} {fighter.country}
                    </div>
                  )}
                </div>
              </div>

              <div className="modal-body">
                {/* Basic Info */}
                <section className="info-section">
                  <h3 className="section-title">Основная информация</h3>
                  <table className="fighter-table">
                    <tbody>
                      <tr>
                        <td className="label">Рекорд:</td>
                        <td className="value">{fighter.record}</td>
                      </tr>
                      <tr>
                        <td className="label">Победы:</td>
                        <td className="value">{fighter.wins}</td>
                      </tr>
                      <tr>
                        <td className="label">Поражения:</td>
                        <td className="value">{fighter.losses}</td>
                      </tr>
                      <tr>
                        <td className="label">Ничьи:</td>
                        <td className="value">{fighter.draws}</td>
                      </tr>
                      {fighter.weight_class && (
                        <tr>
                          <td className="label">Весовая категория:</td>
                          <td className="value">{fighter.weight_class}</td>
                        </tr>
                      )}
                      {fighter.ranking && (
                        <tr>
                          <td className="label">Рейтинг:</td>
                          <td className="value">{fighter.ranking}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </section>

                {/* Physical Stats */}
                {(fighter.age || fighter.height_cm || fighter.weight_kg || fighter.reach_cm) ? (
                  <section className="info-section">
                    <h3 className="section-title">Физические данные</h3>
                    <table className="fighter-table">
                      <tbody>
                        {fighter.age && (
                          <tr>
                            <td className="label">Возраст:</td>
                            <td className="value">{fighter.age} лет</td>
                          </tr>
                        )}
                        {fighter.height_cm && (
                          <tr>
                            <td className="label">Рост:</td>
                            <td className="value">{fighter.height_cm} см</td>
                          </tr>
                        )}
                        {fighter.weight_kg && (
                          <tr>
                            <td className="label">Вес:</td>
                            <td className="value">{fighter.weight_kg} кг</td>
                          </tr>
                        )}
                        {fighter.reach_cm && (
                          <tr>
                            <td className="label">Размах рук:</td>
                            <td className="value">{fighter.reach_cm} см</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </section>
                ) : (
                  <section className="info-section">
                    <div className="no-data-message">
                      <span className="no-data-icon">ℹ️</span>
                      <p>Детальные физические данные отсутствуют</p>
                    </div>
                  </section>
                )}

                {/* Fighting Style */}
                {fighter.style && (
                  <section className="info-section">
                    <h3 className="section-title">Боевой стиль</h3>
                    <table className="fighter-table">
                      <tbody>
                        <tr>
                          <td className="label">Стиль:</td>
                          <td className="value">{fighter.style}</td>
                        </tr>
                      </tbody>
                    </table>
                  </section>
                )}

                {/* Win Methods */}
                {fighter.wins > 0 && (
                  <section className="info-section">
                    <h3 className="section-title">Методы побед</h3>
                    <table className="fighter-table">
                      <tbody>
                        {fighter.wins_ko_tko !== null && fighter.wins_ko_tko !== undefined && (
                          <tr>
                            <td className="label">KO/TKO:</td>
                            <td className="value">{fighter.wins_ko_tko}</td>
                          </tr>
                        )}
                        {fighter.wins_submission !== null && fighter.wins_submission !== undefined && (
                          <tr>
                            <td className="label">Сабмишны:</td>
                            <td className="value">{fighter.wins_submission}</td>
                          </tr>
                        )}
                        {fighter.wins_decision !== null && fighter.wins_decision !== undefined && (
                          <tr>
                            <td className="label">Решения:</td>
                            <td className="value">{fighter.wins_decision}</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </section>
                )}

                {/* Loss Methods */}
                {fighter.losses > 0 && (
                  <section className="info-section">
                    <h3 className="section-title">Методы поражений</h3>
                    <table className="fighter-table">
                      <tbody>
                        {fighter.losses_ko_tko !== null && fighter.losses_ko_tko !== undefined && (
                          <tr>
                            <td className="label">KO/TKO:</td>
                            <td className="value">{fighter.losses_ko_tko}</td>
                          </tr>
                        )}
                        {fighter.losses_submission !== null && fighter.losses_submission !== undefined && (
                          <tr>
                            <td className="label">Сабмишны:</td>
                            <td className="value">{fighter.losses_submission}</td>
                          </tr>
                        )}
                        {fighter.losses_decision !== null && fighter.losses_decision !== undefined && (
                          <tr>
                            <td className="label">Решения:</td>
                            <td className="value">{fighter.losses_decision}</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </section>
                )}

                {/* Recent Fights */}
                {fights && fights.length > 0 && (
                  <section className="info-section">
                    <h3 className="section-title">Последние бои ({fights.length})</h3>
                    <div className="fights-list">
                      {fights.map((fight) => (
                        <Link
                          key={fight.id}
                          to={`/fights/${fight.id}`}
                          className="fight-item"
                          onClick={() => onClose()}
                        >
                          <div className="fight-item-header">
                            <span className="fight-org">{fight.organization || 'N/A'}</span>
                            {fight.event_date && (
                              <span className="fight-date">
                                {new Date(fight.event_date).toLocaleDateString('ru-RU', {
                                  day: 'numeric',
                                  month: 'short',
                                  year: 'numeric'
                                })}
                              </span>
                            )}
                          </div>
                          <div className="fight-matchup">
                            <span className={fight.fighter1?.id === fighterId ? 'fighter-name highlight' : 'fighter-name'}>
                              {fight.fighter1?.name || 'TBA'}
                            </span>
                            <span className="vs-small">vs</span>
                            <span className={fight.fighter2?.id === fighterId ? 'fighter-name highlight' : 'fighter-name'}>
                              {fight.fighter2?.name || 'TBA'}
                            </span>
                          </div>
                          {fight.weight_class && (
                            <div className="fight-weight">{fight.weight_class}</div>
                          )}
                        </Link>
                      ))}
                    </div>
                  </section>
                )}

                {/* Profile Link */}
                {fighter.profile_url && (
                  <section className="info-section">
                    <a
                      href={fighter.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="profile-link"
                    >
                      Просмотреть полный профиль →
                    </a>
                  </section>
                )}
              </div>
            </>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

