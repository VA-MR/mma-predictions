import { useState, useEffect } from 'react';
import { Navigate, Link } from 'react-router-dom';
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
import { formatDateShort } from '../utils/formatters';
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
  const [filterStatus, setFilterStatus] = useState<'all' | 'correct' | 'incorrect'>('all');

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

  // Sort predictions/scorecards by event date (upcoming first, then finished)
  const sortedPredictions = [...predictions].sort((a, b) => {
    const dateA = a.fight?.event_date ? new Date(a.fight.event_date).getTime() : 0;
    const dateB = b.fight?.event_date ? new Date(b.fight.event_date).getTime() : 0;
    const now = Date.now();
    
    // Determine if finished based on result or date
    const aHasResult = a.fight?.result != null;
    const bHasResult = b.fight?.result != null;
    const aFinished = aHasResult || dateA < now;
    const bFinished = bHasResult || dateB < now;
    
    // Upcoming events first, then finished events
    if (aFinished !== bFinished) {
      return aFinished ? 1 : -1;
    }
    
    // Within each group, sort by date (upcoming: earliest first, finished: latest first)
    if (aFinished) {
      return dateB - dateA; // Finished: most recent first
    } else {
      return dateA - dateB; // Upcoming: soonest first
    }
  });

  const sortedScorecards = [...scorecards].sort((a, b) => {
    const dateA = a.fight?.event_date ? new Date(a.fight.event_date).getTime() : 0;
    const dateB = b.fight?.event_date ? new Date(b.fight.event_date).getTime() : 0;
    const now = Date.now();
    
    // Determine if finished based on result or date
    const aHasResult = a.fight?.result != null;
    const bHasResult = b.fight?.result != null;
    const aFinished = aHasResult || dateA < now;
    const bFinished = bHasResult || dateB < now;
    
    if (aFinished !== bFinished) {
      return aFinished ? 1 : -1;
    }
    
    if (aFinished) {
      return dateB - dateA;
    } else {
      return dateA - dateB;
    }
  });

  // Filter predictions/scorecards based on result
  const filteredPredictions = sortedPredictions.filter((p) => {
    if (filterStatus === 'all') return true;
    if (filterStatus === 'correct') return p.resolved_at && p.is_correct === true;
    if (filterStatus === 'incorrect') return p.resolved_at && p.is_correct === false;
    return true;
  });

  const filteredScorecards = sortedScorecards.filter((s) => {
    if (filterStatus === 'all') return true;
    if (!s.resolved_at || s.total_rounds === 0) return false;
    const accuracy = s.correct_rounds / s.total_rounds;
    if (filterStatus === 'correct') return accuracy >= 0.5;
    if (filterStatus === 'incorrect') return accuracy < 0.5;
    return true;
  });

  // Calculate overall accuracy
  const calculateOverallAccuracy = () => {
    const resolvedPredictions = predictions.filter(p => p.resolved_at);
    const correctPredictions = resolvedPredictions.filter(p => p.is_correct).length;
    
    const resolvedScorecards = scorecards.filter(s => s.resolved_at && s.total_rounds > 0);
    const totalScorecardRounds = resolvedScorecards.reduce((sum, s) => sum + s.total_rounds, 0);
    const correctScorecardRounds = resolvedScorecards.reduce((sum, s) => sum + s.correct_rounds, 0);
    
    const totalItems = resolvedPredictions.length + totalScorecardRounds;
    const correctItems = correctPredictions + correctScorecardRounds;
    
    if (totalItems === 0) return null;
    
    return {
      percentage: Math.round((correctItems / totalItems) * 100),
      correct: correctItems,
      total: totalItems
    };
  };

  const overallAccuracy = calculateOverallAccuracy();

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

        <div className="stats-summary">
          {stats && (
            <>
              <div className="stat-item">
                <span className="stat-value">{stats.total_predictions}</span>
                <span className="stat-label">Predictions</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{stats.total_scorecards}</span>
                <span className="stat-label">Scorecards</span>
              </div>
            </>
          )}
          {overallAccuracy && (
            <div className="stat-item stat-accuracy">
              <span className="stat-value">{overallAccuracy.percentage}%</span>
              <span className="stat-label">Accuracy</span>
            </div>
          )}
        </div>

        {/* Accuracy Stats */}
        {(predictions.some(p => p.resolved_at) || scorecards.some(s => s.resolved_at)) && (
          <div className="accuracy-stats">
            {predictions.some(p => p.resolved_at) && (
              <div className="accuracy-card">
                <div className="accuracy-header">
                  <span className="accuracy-icon">🎯</span>
                  <span className="accuracy-title">Prediction Accuracy</span>
                </div>
                <div className="accuracy-body">
                  {(() => {
                    const resolved = predictions.filter(p => p.resolved_at);
                    const correct = resolved.filter(p => p.is_correct).length;
                    const total = resolved.length;
                    const percentage = total > 0 ? Math.round((correct / total) * 100) : 0;
                    
                    return (
                      <>
                        <div className="accuracy-percentage">{percentage}%</div>
                        <div className="accuracy-detail">
                          {correct} correct out of {total} resolved
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}

            {scorecards.some(s => s.resolved_at) && (
              <div className="accuracy-card">
                <div className="accuracy-header">
                  <span className="accuracy-icon">📋</span>
                  <span className="accuracy-title">Scorecard Accuracy</span>
                </div>
                <div className="accuracy-body">
                  {(() => {
                    const resolved = scorecards.filter(s => s.resolved_at);
                    const totalRounds = resolved.reduce((sum, s) => sum + s.total_rounds, 0);
                    const correctRounds = resolved.reduce((sum, s) => sum + s.correct_rounds, 0);
                    const percentage = totalRounds > 0 ? Math.round((correctRounds / totalRounds) * 100) : 0;
                    
                    return (
                      <>
                        <div className="accuracy-percentage">{percentage}%</div>
                        <div className="accuracy-detail">
                          {correctRounds} correct rounds out of {totalRounds}
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
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

      {/* Filters */}
      <div className="profile-filters">
        <button
          className={`filter-btn ${filterStatus === 'all' ? 'active' : ''}`}
          onClick={() => setFilterStatus('all')}
        >
          All
        </button>
        <button
          className={`filter-btn ${filterStatus === 'correct' ? 'active' : ''}`}
          onClick={() => setFilterStatus('correct')}
        >
          ✓ Correct
        </button>
        <button
          className={`filter-btn ${filterStatus === 'incorrect' ? 'active' : ''}`}
          onClick={() => setFilterStatus('incorrect')}
        >
          ✗ Missed
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
            ) : filteredPredictions.length === 0 ? (
              <div className="empty-picks">
                <p>No predictions match the selected filter</p>
              </div>
            ) : (
              filteredPredictions.map((prediction, index) => {
                const fight = prediction.fight;
                const winnerName = prediction.predicted_winner === 'fighter1' 
                  ? fight?.fighter1?.name || 'Fighter 1'
                  : fight?.fighter2?.name || 'Fighter 2';
                
                // Determine if fight is finished based on result or event date
                const hasResult = fight?.result != null;
                const eventDate = fight?.event_date ? new Date(fight.event_date) : null;
                const eventPassed = eventDate && eventDate.getTime() < Date.now();
                const isFinished = hasResult || eventPassed;
                
                return (
                  <motion.div
                    key={prediction.id}
                    className={`pick-card ${isFinished ? 'finished' : 'active'} ${prediction.resolved_at && prediction.is_correct !== null ? (prediction.is_correct ? 'correct' : 'incorrect') : ''}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <div className="pick-info">
                      <div className="pick-badges">
                        <span className="pick-type">Prediction</span>
                        <span className={`pick-status ${isFinished ? 'finished' : 'active'}`}>
                          {isFinished ? 'Finished' : 'Active'}
                        </span>
                        {prediction.resolved_at && prediction.is_correct !== null && (
                          <span className={`pick-result ${prediction.is_correct ? 'correct' : 'incorrect'}`}>
                            {prediction.is_correct ? '✓ Correct' : '✗ Incorrect'}
                          </span>
                        )}
                      </div>
                      <span className="pick-date">
                        {new Date(prediction.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {fight && (
                      <>
                        <div className="pick-event">
                          <span className="event-org">{fight.organization}</span>
                          <Link to={`/fights/${fight.id}`} className="event-name">
                            {fight.event_name}
                          </Link>
                          {fight.event_date && (
                            <span className="event-date">{formatDateShort(fight.event_date)}</span>
                          )}
                        </div>
                        <div className="pick-fight">
                          <span className="fighter-name">{fight.fighter1?.name || 'TBA'}</span>
                          <span className="vs">vs</span>
                          <span className="fighter-name">{fight.fighter2?.name || 'TBA'}</span>
                          {fight.weight_class && (
                            <span className="weight-class">{fight.weight_class}</span>
                          )}
                        </div>
                      </>
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
            ) : filteredScorecards.length === 0 ? (
              <div className="empty-picks">
                <p>No scorecards match the selected filter</p>
              </div>
            ) : (
              filteredScorecards.map((scorecard, index) => {
                const fight = scorecard.fight;
                
                // Determine if fight is finished based on result or event date
                const hasResult = fight?.result != null;
                const eventDate = fight?.event_date ? new Date(fight.event_date) : null;
                const eventPassed = eventDate && eventDate.getTime() < Date.now();
                const isFinished = hasResult || eventPassed;
                
                const scorecardAccuracy = scorecard.resolved_at && scorecard.total_rounds > 0
                  ? Math.round((scorecard.correct_rounds / scorecard.total_rounds) * 100)
                  : null;
                
                const isCorrect = scorecardAccuracy !== null && scorecardAccuracy >= 50;
                
                return (
                  <motion.div
                    key={scorecard.id}
                    className={`pick-card scorecard-card ${isFinished ? 'finished' : 'active'} ${scorecardAccuracy !== null ? (isCorrect ? 'correct' : 'incorrect') : ''}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <div className="pick-info">
                      <div className="pick-badges">
                        <span className="pick-type">Scorecard</span>
                        <span className={`pick-status ${isFinished ? 'finished' : 'active'}`}>
                          {isFinished ? 'Finished' : 'Active'}
                        </span>
                        {scorecard.resolved_at && scorecard.total_rounds > 0 && (
                          <span className={`pick-result ${isCorrect ? 'correct' : 'incorrect'}`}>
                            {scorecardAccuracy}% ({scorecard.correct_rounds}/{scorecard.total_rounds} rounds)
                          </span>
                        )}
                      </div>
                      <span className="pick-date">
                        {new Date(scorecard.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {fight && (
                      <>
                        <div className="pick-event">
                          <span className="event-org">{fight.organization}</span>
                          <Link to={`/fights/${fight.id}`} className="event-name">
                            {fight.event_name}
                          </Link>
                          {fight.event_date && (
                            <span className="event-date">{formatDateShort(fight.event_date)}</span>
                          )}
                        </div>
                        <div className="pick-fight">
                          <span className="fighter-name">{fight.fighter1?.name || 'TBA'}</span>
                          <span className="vs">vs</span>
                          <span className="fighter-name">{fight.fighter2?.name || 'TBA'}</span>
                          {fight.weight_class && (
                            <span className="weight-class">{fight.weight_class}</span>
                          )}
                        </div>
                      </>
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

