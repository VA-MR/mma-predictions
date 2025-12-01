import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  getMyPredictions,
  getMyScorecards,
  getCurrentUserStats,
  Prediction,
  Scorecard,
  UserStats,
} from '../api/client';
import { useAuth } from '../hooks/useAuth';
import './ProfilePage.css';

const WIN_METHOD_LABELS: Record<string, string> = {
  ko_tko: 'KO/TKO',
  submission: 'Submission',
  decision: 'Decision',
  dq: 'DQ',
};

export default function ProfilePage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [scorecards, setScorecards] = useState<Scorecard[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'predictions' | 'scorecards'>('predictions');

  useEffect(() => {
    const fetchData = async () => {
      if (!isAuthenticated) return;
      
      try {
        const [preds, scs, userStats] = await Promise.all([
          getMyPredictions(),
          getMyScorecards(),
          getCurrentUserStats(),
        ]);
        setPredictions(preds);
        setScorecards(scs);
        setStats(userStats);
      } catch (error) {
        console.error('Failed to fetch user data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (!authLoading) {
      fetchData();
    }
  }, [isAuthenticated, authLoading]);

  // Redirect if not authenticated
  if (!authLoading && !isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (authLoading || isLoading) {
    return (
      <div className="container">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading your picks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <motion.div
        className="profile-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="user-info">
          {user?.photo_url && (
            <img src={user.photo_url} alt="" className="profile-avatar" />
          )}
          <div className="user-details">
            <h1 className="profile-name">{user?.display_name}</h1>
            {user?.username && (
              <span className="profile-username">@{user.username}</span>
            )}
          </div>
        </div>

        {stats && (
          <div className="stats-summary">
            <div className="stat-item">
              <span className="stat-value">{stats.total_predictions}</span>
              <span className="stat-label">Predictions</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{stats.total_scorecards}</span>
              <span className="stat-label">Scorecards</span>
            </div>
          </div>
        )}
      </motion.div>

      {/* Tabs */}
      <div className="profile-tabs">
        <button
          className={`profile-tab ${activeTab === 'predictions' ? 'active' : ''}`}
          onClick={() => setActiveTab('predictions')}
        >
          My Predictions ({predictions.length})
        </button>
        <button
          className={`profile-tab ${activeTab === 'scorecards' ? 'active' : ''}`}
          onClick={() => setActiveTab('scorecards')}
        >
          My Scorecards ({scorecards.length})
        </button>
      </div>

      {/* Tab Content */}
      <motion.div
        className="picks-list"
        key={activeTab}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {activeTab === 'predictions' && (
          <>
            {predictions.length === 0 ? (
              <div className="empty-picks">
                <p>You haven't made any predictions yet</p>
                <p className="empty-hint">
                  Go to an event and make your first pick!
                </p>
              </div>
            ) : (
              predictions.map((prediction, index) => {
                const fight = prediction.fight;
                const winnerName = prediction.predicted_winner === 'fighter1' 
                  ? fight?.fighter1?.name || 'Fighter 1'
                  : fight?.fighter2?.name || 'Fighter 2';
                
                return (
                  <motion.div
                    key={prediction.id}
                    className="pick-card"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <div className="pick-info">
                      <span className="pick-type">Prediction</span>
                      <span className="pick-date">
                        {new Date(prediction.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {fight && (
                      <div className="pick-fight">
                        <span className="fighter-name">{fight.fighter1?.name || 'TBA'}</span>
                        <span className="vs">vs</span>
                        <span className="fighter-name">{fight.fighter2?.name || 'TBA'}</span>
                      </div>
                    )}
                    <div className="pick-details">
                      <span className={`pick-winner ${prediction.predicted_winner}`}>
                        {winnerName}
                      </span>
                      <span className="pick-method">
                        by {WIN_METHOD_LABELS[prediction.win_method]}
                      </span>
                      {prediction.confidence && (
                        <span className="pick-confidence">
                          Confidence: {prediction.confidence}/5
                        </span>
                      )}
                    </div>
                  </motion.div>
                );
              })
            )}
          </>
        )}

        {activeTab === 'scorecards' && (
          <>
            {scorecards.length === 0 ? (
              <div className="empty-picks">
                <p>You haven't submitted any scorecards yet</p>
                <p className="empty-hint">
                  Watch a fight and score it round by round!
                </p>
              </div>
            ) : (
              scorecards.map((scorecard, index) => {
                const fight = scorecard.fight;
                
                return (
                  <motion.div
                    key={scorecard.id}
                    className="pick-card scorecard-card"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <div className="pick-info">
                      <span className="pick-type">Scorecard</span>
                      <span className="pick-date">
                        {new Date(scorecard.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {fight && (
                      <div className="pick-fight">
                        <span className="fighter-name">{fight.fighter1?.name || 'TBA'}</span>
                        <span className="vs">vs</span>
                        <span className="fighter-name">{fight.fighter2?.name || 'TBA'}</span>
                      </div>
                    )}
                    <div className="scorecard-summary">
                      <div className="scorecard-total">
                        <span className="score fighter1">{scorecard.total_fighter1}</span>
                        <span className="score-divider">-</span>
                        <span className="score fighter2">{scorecard.total_fighter2}</span>
                      </div>
                      <div className="round-scores">
                        {scorecard.round_scores.map((rs) => (
                          <span key={rs.round_number} className="round-score">
                            R{rs.round_number}: {rs.fighter1_score}-{rs.fighter2_score}
                          </span>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                );
              })
            )}
          </>
        )}
      </motion.div>
    </div>
  );
}

