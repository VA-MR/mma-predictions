import { motion } from 'framer-motion';
import { Fight, PredictionStats, ScorecardStats } from '../api/client';
import './CrowdWisdom.css';

interface CrowdWisdomProps {
  fight: Fight;
  predictionStats: PredictionStats | null;
  scorecardStats: ScorecardStats | null;
}

const WIN_METHOD_LABELS: Record<string, string> = {
  ko_tko: 'KO/TKO',
  submission: 'Submission',
  decision: 'Decision',
  dq: 'DQ',
};

export default function CrowdWisdom({
  fight,
  predictionStats,
  scorecardStats,
}: CrowdWisdomProps) {
  const hasPredictions = predictionStats && predictionStats.total_predictions > 0;
  const hasScorecards = scorecardStats && scorecardStats.total_scorecards > 0;

  if (!hasPredictions && !hasScorecards) {
    return (
      <div className="crowd-wisdom empty">
        <h3>Crowd Wisdom</h3>
        <p className="empty-message">No picks yet. Be the first to make a prediction!</p>
      </div>
    );
  }

  return (
    <div className="crowd-wisdom">
      <h3>Crowd Wisdom</h3>

      {/* Prediction Stats */}
      {hasPredictions && (
        <motion.div
          className="stats-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h4 className="stats-title">
            Predictions
            <span className="stats-count">{predictionStats.total_predictions} picks</span>
          </h4>

          {/* Winner Bar */}
          <div className="winner-bar-container">
            <div className="winner-labels">
              <span className="fighter1">{fight.fighter1?.name}</span>
              <span className="fighter2">{fight.fighter2?.name}</span>
            </div>
            <div className="winner-bar">
              <motion.div
                className="bar-fill fighter1"
                initial={{ width: 0 }}
                animate={{ width: `${predictionStats.fighter1_percentage}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
              <motion.div
                className="bar-fill fighter2"
                initial={{ width: 0 }}
                animate={{ width: `${predictionStats.fighter2_percentage}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>
            <div className="winner-percentages">
              <span className="fighter1">{predictionStats.fighter1_percentage}%</span>
              <span className="fighter2">{predictionStats.fighter2_percentage}%</span>
            </div>
          </div>

          {/* Method Breakdown */}
          <div className="method-breakdown">
            <h5>By Method</h5>
            <div className="method-grid">
              {Object.entries(predictionStats.methods).map(([method, counts]) => {
                const total = counts.fighter1 + counts.fighter2;
                if (total === 0) return null;
                return (
                  <div key={method} className="method-item">
                    <span className="method-label">{WIN_METHOD_LABELS[method]}</span>
                    <div className="method-counts">
                      <span className="fighter1">{counts.fighter1}</span>
                      <span className="divider">-</span>
                      <span className="fighter2">{counts.fighter2}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>
      )}

      {/* Scorecard Stats */}
      {hasScorecards && (
        <motion.div
          className="stats-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h4 className="stats-title">
            Scorecards
            <span className="stats-count">{scorecardStats.total_scorecards} cards</span>
          </h4>

          {/* Round-by-Round Average */}
          <div className="round-averages">
            {Object.entries(scorecardStats.rounds).map(([round, data]) => (
              <div key={round} className="round-avg-row">
                <div className="round-avg fighter1">
                  <span className="avg-score">{data.average_fighter1.toFixed(1)}</span>
                  <span className="round-wins">({data.fighter1_round_wins} wins)</span>
                </div>
                <div className="round-label">R{round}</div>
                <div className="round-avg fighter2">
                  <span className="avg-score">{data.average_fighter2.toFixed(1)}</span>
                  <span className="round-wins">({data.fighter2_round_wins} wins)</span>
                </div>
              </div>
            ))}
          </div>

          {/* Consensus Totals */}
          <div className="consensus-totals">
            <div className="consensus-row">
              <span className="consensus-label">Average Total Score</span>
              <div className="consensus-scores">
                <span className="fighter1">{scorecardStats.average_total_fighter1}</span>
                <span className="divider">-</span>
                <span className="fighter2">{scorecardStats.average_total_fighter2}</span>
              </div>
            </div>
          </div>

          {/* Win Distribution */}
          <div className="win-distribution">
            <h5>Scorecard Winners</h5>
            <div className="distribution-bar">
              <div
                className="dist-segment fighter1"
                style={{ width: `${scorecardStats.fighter1_win_percentage}%` }}
              >
                {scorecardStats.fighter1_wins > 0 && (
                  <span>{scorecardStats.fighter1_wins}</span>
                )}
              </div>
              {scorecardStats.draws > 0 && (
                <div
                  className="dist-segment draw"
                  style={{ width: `${(scorecardStats.draws / scorecardStats.total_scorecards) * 100}%` }}
                >
                  <span>{scorecardStats.draws}</span>
                </div>
              )}
              <div
                className="dist-segment fighter2"
                style={{ width: `${scorecardStats.fighter2_win_percentage}%` }}
              >
                {scorecardStats.fighter2_wins > 0 && (
                  <span>{scorecardStats.fighter2_wins}</span>
                )}
              </div>
            </div>
            <div className="distribution-legend">
              <span className="fighter1">{fight.fighter1?.name}</span>
              <span className="fighter2">{fight.fighter2?.name}</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

