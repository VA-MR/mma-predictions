import { useState } from 'react';
import { motion } from 'framer-motion';
import { Fight, Scorecard, createScorecard } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import './ScorecardForm.css';

interface ScorecardFormProps {
  fight: Fight;
  existingScorecard: Scorecard | null;
  onScorecardSubmit: (scorecard: Scorecard) => void;
}

interface RoundScoreState {
  round_number: number;
  fighter1_score: number;
  fighter2_score: number;
}

const SCORES = [10, 9, 8, 7] as const;

export default function ScorecardForm({
  fight,
  existingScorecard,
  onScorecardSubmit,
}: ScorecardFormProps) {
  const { isAuthenticated, openAuthModal } = useAuth();
  const numRounds = fight.rounds || 3;

  const [roundScores, setRoundScores] = useState<RoundScoreState[]>(() => {
    if (existingScorecard) {
      return existingScorecard.round_scores.map(rs => ({
        round_number: rs.round_number,
        fighter1_score: rs.fighter1_score,
        fighter2_score: rs.fighter2_score,
      }));
    }
    return Array.from({ length: numRounds }, (_, i) => ({
      round_number: i + 1,
      fighter1_score: 10,
      fighter2_score: 9,
    }));
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateScore = (
    roundNumber: number,
    fighter: 'fighter1' | 'fighter2',
    score: number
  ) => {
    setRoundScores(prev =>
      prev.map(rs =>
        rs.round_number === roundNumber
          ? { ...rs, [`${fighter}_score`]: score }
          : rs
      )
    );
  };

  const totalFighter1 = roundScores.reduce((sum, rs) => sum + rs.fighter1_score, 0);
  const totalFighter2 = roundScores.reduce((sum, rs) => sum + rs.fighter2_score, 0);

  const handleSubmit = async () => {
    // If not authenticated, open auth modal
    if (!isAuthenticated) {
      openAuthModal();
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const scorecard = await createScorecard({
        fight_id: fight.id,
        round_scores: roundScores,
      });
      onScorecardSubmit(scorecard);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка отправки скоркарда');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSubmitted = !!existingScorecard;

  return (
    <div className="scorecard-form">
      <div className="scorecard-header">
        <h3>Скоркард по раундам</h3>
        <a
          href="https://verdictmma.com/guides/ufc-scoring-and-mma-scoring"
          target="_blank"
          rel="noopener noreferrer"
          className="scoring-guide-link"
        >
          Как судить →
        </a>
      </div>

      <p className="scoring-hint">
        10-баллная система: Победитель раунда — 10, проигравший — 9 (или 8 за доминирование)
      </p>

      {/* Fighter Names Header */}
      <div className="scorecard-fighters">
        <div className="fighter-col fighter1">
          <span className="fighter-name">{fight.fighter1?.name || 'TBA'}</span>
        </div>
        <div className="round-col">Раунд</div>
        <div className="fighter-col fighter2">
          <span className="fighter-name">{fight.fighter2?.name || 'TBA'}</span>
        </div>
      </div>

      {/* Round Scores */}
      <div className="rounds-container">
        {roundScores.map((rs) => (
          <motion.div
            key={rs.round_number}
            className="round-row"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: rs.round_number * 0.05 }}
          >
            {/* Fighter 1 Score */}
            <div className="score-buttons fighter1">
              {SCORES.map((score) => (
                <button
                  key={score}
                  type="button"
                  className={`score-btn ${rs.fighter1_score === score ? 'selected' : ''}`}
                  onClick={() => !isSubmitted && updateScore(rs.round_number, 'fighter1', score)}
                  disabled={isSubmitted}
                >
                  {score}
                </button>
              ))}
            </div>

            {/* Round Number */}
            <div className="round-number">R{rs.round_number}</div>

            {/* Fighter 2 Score */}
            <div className="score-buttons fighter2">
              {SCORES.map((score) => (
                <button
                  key={score}
                  type="button"
                  className={`score-btn ${rs.fighter2_score === score ? 'selected' : ''}`}
                  onClick={() => !isSubmitted && updateScore(rs.round_number, 'fighter2', score)}
                  disabled={isSubmitted}
                >
                  {score}
                </button>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Totals */}
      <div className="scorecard-totals">
        <div className={`total fighter1 ${totalFighter1 > totalFighter2 ? 'winner' : ''}`}>
          {totalFighter1}
        </div>
        <div className="total-label">ИТОГО</div>
        <div className={`total fighter2 ${totalFighter2 > totalFighter1 ? 'winner' : ''}`}>
          {totalFighter2}
        </div>
      </div>

      {/* Winner Display */}
      <div className="scorecard-winner">
        {totalFighter1 > totalFighter2 ? (
          <span className="winner-text fighter1">{fight.fighter1?.name} — победитель по вашей карте</span>
        ) : totalFighter2 > totalFighter1 ? (
          <span className="winner-text fighter2">{fight.fighter2?.name} — победитель по вашей карте</span>
        ) : (
          <span className="winner-text draw">Ничья по вашей карте</span>
        )}
      </div>

      {error && <p className="form-error">{error}</p>}

      {!isSubmitted && (
        <>
          <motion.button
            type="button"
            className="submit-btn"
            onClick={handleSubmit}
            disabled={isSubmitting}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isSubmitting ? 'Отправка...' : isAuthenticated ? 'Отправить скоркард' : 'Войти и отправить'}
          </motion.button>

          {!isAuthenticated && (
            <p className="form-notice">🔐 Требуется авторизация через Telegram</p>
          )}
          {isAuthenticated && (
            <p className="form-notice">⚠️ Скоркарды нельзя изменить после отправки</p>
          )}
        </>
      )}

      {isSubmitted && (
        <p className="locked-notice">Ваш скоркард отправлен и зафиксирован</p>
      )}
    </div>
  );
}

