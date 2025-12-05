import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  getFight,
  getFightPredictionStats,
  getFightScorecardStats,
  getMyFightPrediction,
  getMyFightScorecard,
  Fight,
  Prediction,
  Scorecard,
  PredictionStats,
  ScorecardStats,
} from '../api/client';
import { useAuth } from '../hooks/useAuth';
import PredictionForm from '../components/PredictionForm';
import ScorecardForm from '../components/ScorecardForm';
import CrowdWisdom from '../components/CrowdWisdom';
import FighterModal from '../components/FighterModal';
import { getCountryFlag } from '../utils/formatters';
import './FightPage.css';

type Tab = 'prediction' | 'scorecard' | 'stats';

export default function FightPage() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated } = useAuth();
  
  const [fight, setFight] = useState<Fight | null>(null);
  const [myPrediction, setMyPrediction] = useState<Prediction | null>(null);
  const [myScorecard, setMyScorecard] = useState<Scorecard | null>(null);
  const [predictionStats, setPredictionStats] = useState<PredictionStats | null>(null);
  const [scorecardStats, setScorecardStats] = useState<ScorecardStats | null>(null);
  
  const [activeTab, setActiveTab] = useState<Tab>('prediction');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalFighterId, setModalFighterId] = useState<number | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      
      const fightId = parseInt(id, 10);
      
      try {
        // Fetch fight data
        const fightData = await getFight(fightId);
        setFight(fightData);
        
        // Fetch stats
        const [pStats, sStats] = await Promise.all([
          getFightPredictionStats(fightId),
          getFightScorecardStats(fightId),
        ]);
        setPredictionStats(pStats);
        setScorecardStats(sStats);
        
        // Fetch user's picks if authenticated
        if (isAuthenticated) {
          const [pred, sc] = await Promise.all([
            getMyFightPrediction(fightId),
            getMyFightScorecard(fightId),
          ]);
          setMyPrediction(pred);
          setMyScorecard(sc);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load fight');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [id, isAuthenticated]);

  const handlePredictionSubmit = async (prediction: Prediction) => {
    setMyPrediction(prediction);
    // Refresh stats
    if (id) {
      const stats = await getFightPredictionStats(parseInt(id, 10));
      setPredictionStats(stats);
    }
  };

  const handleScorecardSubmit = async (scorecard: Scorecard) => {
    setMyScorecard(scorecard);
    // Refresh stats
    if (id) {
      const stats = await getFightScorecardStats(parseInt(id, 10));
      setScorecardStats(stats);
    }
  };

  const handleFighterClick = (fighterId: number | undefined) => {
    if (!fighterId || fighterId <= 0) {
      return;
    }
    setModalFighterId(fighterId);
  };

  if (isLoading) {
    return (
      <div className="container">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading fight...</p>
        </div>
      </div>
    );
  }

  if (error || !fight) {
    return (
      <div className="container">
        <div className="error-state">
          <p>❌ {error || 'Fight not found'}</p>
          <Link to="/" className="back-link">← Back to Events</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <Link to="/" className="back-link">
        ← Назад к событиям
      </Link>

      {/* Fight Header */}
      <motion.div
        className="fight-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="matchup-display">
          {/* Fighter 1 */}
          <div 
            className="fighter-display fighter1"
            onClick={() => handleFighterClick(fight.fighter1?.id)}
            style={{ cursor: fight.fighter1 ? 'pointer' : 'default' }}
          >
            <div className="fighter-flag-large">
              {getCountryFlag(fight.fighter1?.country)}
            </div>
            <h2 className="fighter-name-large">
              {fight.fighter1?.name || 'TBA'}
            </h2>
            <span className="fighter-record-large">
              {fight.fighter1?.record || '0-0-0'}
            </span>
          </div>

          {/* VS */}
          <div className="vs-display">
            <span className="vs-text">VS</span>
            {fight.weight_class && (
              <span className="weight-class-badge">{fight.weight_class}</span>
            )}
            {fight.rounds && (
              <span className="rounds-badge">{fight.rounds} раундов</span>
            )}
          </div>

          {/* Fighter 2 */}
          <div 
            className="fighter-display fighter2"
            onClick={() => handleFighterClick(fight.fighter2?.id)}
            style={{ cursor: fight.fighter2 ? 'pointer' : 'default' }}
          >
            <div className="fighter-flag-large">
              {getCountryFlag(fight.fighter2?.country)}
            </div>
            <h2 className="fighter-name-large">
              {fight.fighter2?.name || 'TBA'}
            </h2>
            <span className="fighter-record-large">
              {fight.fighter2?.record || '0-0-0'}
            </span>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'prediction' ? 'active' : ''}`}
          onClick={() => setActiveTab('prediction')}
        >
          Прогноз
          {myPrediction && <span className="tab-badge">✓</span>}
        </button>
        <button
          className={`tab ${activeTab === 'scorecard' ? 'active' : ''}`}
          onClick={() => setActiveTab('scorecard')}
        >
          Скоркард
          {myScorecard && <span className="tab-badge">✓</span>}
        </button>
        <button
          className={`tab ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          Статистика
          {(predictionStats?.total_predictions || 0) > 0 && (
            <span className="tab-count">{predictionStats?.total_predictions}</span>
          )}
        </button>
      </div>

      {/* Tab Content */}
      <motion.div
        className="tab-content"
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === 'prediction' && (
          <PredictionForm
            fight={fight}
            existingPrediction={myPrediction}
            onPredictionSubmit={handlePredictionSubmit}
          />
        )}
        {activeTab === 'scorecard' && (
          <ScorecardForm
            fight={fight}
            existingScorecard={myScorecard}
            onScorecardSubmit={handleScorecardSubmit}
          />
        )}
        {activeTab === 'stats' && (
          <CrowdWisdom
            fight={fight}
            predictionStats={predictionStats}
            scorecardStats={scorecardStats}
          />
        )}
      </motion.div>

      {/* Fighter Modal */}
      {modalFighterId && (
        <FighterModal
          fighterId={modalFighterId}
          isOpen={modalFighterId !== null}
          onClose={() => setModalFighterId(null)}
        />
      )}
    </div>
  );
}

