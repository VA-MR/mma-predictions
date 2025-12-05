import { useState } from 'react';
import { motion } from 'framer-motion';
import { Fight, Prediction, createPrediction } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import './PredictionForm.css';

interface PredictionFormProps {
  fight: Fight;
  existingPrediction: Prediction | null;
  onPredictionSubmit: (prediction: Prediction) => void;
}

const WIN_METHODS = [
  { value: 'ko_tko', label: 'KO/TKO', icon: '👊' },
  { value: 'submission', label: 'Сабмишн', icon: '🔒' },
  { value: 'decision', label: 'Решение', icon: '📋' },
  { value: 'dq', label: 'DQ', icon: '🚫' },
] as const;

export default function PredictionForm({
  fight,
  existingPrediction,
  onPredictionSubmit,
}: PredictionFormProps) {
  const { isAuthenticated, openAuthModal } = useAuth();
  const [selectedWinner, setSelectedWinner] = useState<'fighter1' | 'fighter2' | null>(
    existingPrediction?.predicted_winner || null
  );
  const [selectedMethod, setSelectedMethod] = useState<string | null>(
    existingPrediction?.win_method || null
  );
  const [confidence, setConfidence] = useState<number>(
    existingPrediction?.confidence || 3
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    // If not authenticated, open auth modal
    if (!isAuthenticated) {
      openAuthModal();
      return;
    }

    if (!selectedWinner || !selectedMethod) {
      setError('Выберите победителя и способ победы');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const prediction = await createPrediction({
        fight_id: fight.id,
        predicted_winner: selectedWinner,
        win_method: selectedMethod as 'ko_tko' | 'submission' | 'decision' | 'dq',
        confidence,
      });
      onPredictionSubmit(prediction);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка отправки прогноза');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (existingPrediction) {
    const isResolved = existingPrediction.resolved_at !== null;
    const isCorrect = existingPrediction.is_correct;

    return (
      <div className="prediction-submitted">
        <h3>Ваш прогноз</h3>
        <div className="submitted-pick">
          <span className="pick-winner">
            {existingPrediction.predicted_winner === 'fighter1'
              ? fight.fighter1?.name
              : fight.fighter2?.name}
          </span>
          <span className="pick-method">
            {WIN_METHODS.find(m => m.value === existingPrediction.win_method)?.label}
          </span>
        </div>
        
        {isResolved && (
          <div className={`prediction-result ${isCorrect ? 'correct' : 'incorrect'}`}>
            {isCorrect ? (
              <>
                <span className="result-icon">✓</span>
                <span className="result-text">Правильный прогноз!</span>
              </>
            ) : (
              <>
                <span className="result-icon">✗</span>
                <span className="result-text">Неправильный прогноз</span>
              </>
            )}
          </div>
        )}
        
        {!isResolved && (
          <p className="locked-notice">Прогнозы нельзя изменить после отправки</p>
        )}
      </div>
    );
  }

  return (
    <div className="prediction-form">
      <h3>Сделать прогноз</h3>

      {/* Winner Selection */}
      <div className="form-section">
        <label className="form-label">Кто победит?</label>
        <div className="winner-buttons">
          <button
            type="button"
            className={`winner-btn fighter1 ${selectedWinner === 'fighter1' ? 'selected' : ''}`}
            onClick={() => setSelectedWinner('fighter1')}
          >
            <span className="fighter-name">{fight.fighter1?.name || 'TBA'}</span>
            <span className="fighter-record">{fight.fighter1?.record}</span>
          </button>
          <button
            type="button"
            className={`winner-btn fighter2 ${selectedWinner === 'fighter2' ? 'selected' : ''}`}
            onClick={() => setSelectedWinner('fighter2')}
          >
            <span className="fighter-name">{fight.fighter2?.name || 'TBA'}</span>
            <span className="fighter-record">{fight.fighter2?.record}</span>
          </button>
        </div>
      </div>

      {/* Method Selection */}
      <div className="form-section">
        <label className="form-label">Способ победы?</label>
        <div className="method-buttons">
          {WIN_METHODS.map((method) => (
            <button
              key={method.value}
              type="button"
              className={`method-btn ${selectedMethod === method.value ? 'selected' : ''}`}
              onClick={() => setSelectedMethod(method.value)}
            >
              <span className="method-icon">{method.icon}</span>
              <span className="method-label">{method.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Confidence */}
      <div className="form-section">
        <label className="form-label">
          Уверенность: {confidence}/5
        </label>
        <input
          type="range"
          min="1"
          max="5"
          value={confidence}
          onChange={(e) => setConfidence(Number(e.target.value))}
          className="confidence-slider"
        />
        <div className="confidence-labels">
          <span>Догадка</span>
          <span>Уверен</span>
        </div>
      </div>

      {error && <p className="form-error">{error}</p>}

      <motion.button
        type="button"
        className="submit-btn"
        onClick={handleSubmit}
        disabled={isSubmitting}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        {isSubmitting ? 'Отправка...' : isAuthenticated ? 'Отправить прогноз' : 'Войти и отправить'}
      </motion.button>

      {!isAuthenticated && (
        <p className="form-notice">🔐 Требуется авторизация через Telegram</p>
      )}
      {isAuthenticated && (
        <p className="form-notice">⚠️ Прогнозы нельзя изменить после отправки</p>
      )}
    </div>
  );
}

