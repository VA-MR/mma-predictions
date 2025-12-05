import React, { useState, useEffect } from 'react';
import { AdminModal } from './AdminModal';
import {
  Fight,
  FightResultCreate,
  FightResult,
  OfficialScorecard,
  createFightResult,
  updateFightResult,
  getFightResult,
} from '../api/client';
import './FightResultModal.css';

interface FightResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  fight: Fight | null;
  onSuccess: () => void;
}

export function FightResultModal({ isOpen, onClose, fight, onSuccess }: FightResultModalProps) {
  const [loading, setLoading] = useState(false);
  const [existingResult, setExistingResult] = useState<FightResult | null>(null);
  const [activeRound, setActiveRound] = useState(1);
  const [formData, setFormData] = useState<FightResultCreate>({
    winner: 'fighter1',
    method: 'decision',
    finish_round: null,
    finish_time: null,
    official_scorecards: [],
  });

  useEffect(() => {
    if (isOpen && fight) {
      loadExistingResult();
      setActiveRound(1); // Reset to round 1 when opening
    }
  }, [isOpen, fight]);

  const loadExistingResult = async () => {
    if (!fight) return;
    
    try {
      const result = await getFightResult(fight.id);
      setExistingResult(result);
      setFormData({
        winner: result.winner,
        method: result.method,
        finish_round: result.finish_round,
        finish_time: result.finish_time,
        official_scorecards: result.official_scorecards.map(sc => ({
          judge_name: sc.judge_name,
          round_scores: sc.round_scores.map(rs => ({
            round_number: rs.round_number,
            fighter1_score: rs.fighter1_score,
            fighter2_score: rs.fighter2_score,
          })),
        })),
      });
    } catch (error) {
      // No existing result, that's fine
      setExistingResult(null);
      initializeEmptyScorecards();
    }
  };

  const initializeEmptyScorecards = () => {
    if (!fight) return;
    
    const rounds = fight.rounds || 3;
    const scorecards: OfficialScorecard[] = [
      { judge_name: 'Judge 1', round_scores: [] },
      { judge_name: 'Judge 2', round_scores: [] },
      { judge_name: 'Judge 3', round_scores: [] },
    ];

    scorecards.forEach(scorecard => {
      for (let i = 1; i <= rounds; i++) {
        scorecard.round_scores.push({
          round_number: i,
          fighter1_score: 10,
          fighter2_score: 9,
        });
      }
    });

    setFormData(prev => ({ ...prev, official_scorecards: scorecards }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fight) return;

    try {
      setLoading(true);
      
      if (existingResult) {
        await updateFightResult(fight.id, formData);
      } else {
        await createFightResult(fight.id, formData);
      }
      
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to save fight result:', error);
      alert('Ошибка сохранения результата боя');
    } finally {
      setLoading(false);
    }
  };

  const updateJudgeName = (judgeIndex: number, name: string) => {
    const newScorecards = [...formData.official_scorecards];
    newScorecards[judgeIndex].judge_name = name;
    setFormData({ ...formData, official_scorecards: newScorecards });
  };

  const updateRoundScore = (
    judgeIndex: number,
    roundNumber: number,
    fighter: 'fighter1' | 'fighter2',
    score: number
  ) => {
    const newScorecards = [...formData.official_scorecards];
    const roundScore = newScorecards[judgeIndex].round_scores.find(
      rs => rs.round_number === roundNumber
    );
    
    if (roundScore) {
      if (fighter === 'fighter1') {
        roundScore.fighter1_score = score;
      } else {
        roundScore.fighter2_score = score;
      }
    }
    
    setFormData({ ...formData, official_scorecards: newScorecards });
  };

  const calculateTotal = (scorecard: OfficialScorecard, fighter: 'fighter1' | 'fighter2') => {
    return scorecard.round_scores.reduce((sum, rs) => {
      return sum + (fighter === 'fighter1' ? rs.fighter1_score : rs.fighter2_score);
    }, 0);
  };

  const isDecision = formData.method === 'decision';
  const needsScorecards = isDecision && formData.official_scorecards.length > 0;

  if (!fight) return null;

  return (
    <AdminModal
      isOpen={isOpen}
      onClose={onClose}
      title={`Результат боя: ${fight.fighter1?.name || 'TBA'} vs ${fight.fighter2?.name || 'TBA'}`}
    >
      <form onSubmit={handleSubmit} className="fight-result-form">
        <div className="admin-form-group">
          <label>Победитель *</label>
          <select
            required
            value={formData.winner}
            onChange={(e) => setFormData({ ...formData, winner: e.target.value as any })}
          >
            <option value="fighter1">{fight.fighter1?.name || 'Fighter 1'}</option>
            <option value="fighter2">{fight.fighter2?.name || 'Fighter 2'}</option>
            <option value="draw">Ничья</option>
            <option value="no_contest">No Contest</option>
          </select>
        </div>

        <div className="admin-form-group">
          <label>Метод победы *</label>
          <select
            required
            value={formData.method}
            onChange={(e) => {
              const method = e.target.value as any;
              setFormData({ ...formData, method });
              if (method === 'decision' && formData.official_scorecards.length === 0) {
                initializeEmptyScorecards();
              }
            }}
          >
            <option value="ko_tko">KO/TKO</option>
            <option value="submission">Submission</option>
            <option value="decision">Decision</option>
            <option value="dq">DQ</option>
          </select>
        </div>

        {!isDecision && (
          <>
            <div className="admin-form-row">
              <div className="admin-form-group">
                <label>Раунд окончания</label>
                <input
                  type="number"
                  min="1"
                  max={fight.rounds || 5}
                  value={formData.finish_round || ''}
                  onChange={(e) => setFormData({ ...formData, finish_round: e.target.value ? parseInt(e.target.value) : null })}
                />
              </div>
              <div className="admin-form-group">
                <label>Время окончания</label>
                <input
                  type="text"
                  placeholder="напр. 2:34"
                  value={formData.finish_time || ''}
                  onChange={(e) => setFormData({ ...formData, finish_time: e.target.value || null })}
                />
              </div>
            </div>
          </>
        )}

        {needsScorecards && (
          <div className="official-scorecards-section">
            <h3>Судейские записи</h3>
            
            {/* Round Tabs */}
            <div className="round-tabs">
              {formData.official_scorecards[0]?.round_scores.map((rs) => (
                <button
                  key={rs.round_number}
                  type="button"
                  className={`round-tab ${activeRound === rs.round_number ? 'active' : ''}`}
                  onClick={() => setActiveRound(rs.round_number)}
                >
                  Раунд {rs.round_number}
                </button>
              ))}
            </div>

            {/* Current Round Scores */}
            <div className="round-content">
              {formData.official_scorecards.map((scorecard, judgeIndex) => {
                const roundScore = scorecard.round_scores.find(rs => rs.round_number === activeRound);
                if (!roundScore) return null;

                return (
                  <div key={judgeIndex} className="judge-round-card">
                    <div className="judge-info">
                      <input
                        type="text"
                        className="judge-name-input"
                        value={scorecard.judge_name}
                        onChange={(e) => updateJudgeName(judgeIndex, e.target.value)}
                        placeholder={`Судья ${judgeIndex + 1}`}
                      />
                      <div className="judge-totals">
                        <span className="total-label">Итого:</span>
                        <span className="total-score fighter1">
                          {fight.fighter1?.name || 'F1'}: {calculateTotal(scorecard, 'fighter1')}
                        </span>
                        <span className="total-score fighter2">
                          {fight.fighter2?.name || 'F2'}: {calculateTotal(scorecard, 'fighter2')}
                        </span>
                      </div>
                    </div>

                    <div className="score-inputs-row">
                      <div className="score-input-group">
                        <label>{fight.fighter1?.name || 'Fighter 1'}</label>
                        <input
                          type="number"
                          min="7"
                          max="10"
                          value={roundScore.fighter1_score}
                          onChange={(e) => updateRoundScore(
                            judgeIndex,
                            activeRound,
                            'fighter1',
                            parseInt(e.target.value) || 10
                          )}
                          className="score-input"
                        />
                      </div>
                      <div className="score-input-group">
                        <label>{fight.fighter2?.name || 'Fighter 2'}</label>
                        <input
                          type="number"
                          min="7"
                          max="10"
                          value={roundScore.fighter2_score}
                          onChange={(e) => updateRoundScore(
                            judgeIndex,
                            activeRound,
                            'fighter2',
                            parseInt(e.target.value) || 10
                          )}
                          className="score-input"
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="admin-form-actions">
          <button type="button" className="admin-btn" onClick={onClose} disabled={loading}>
            Отмена
          </button>
          <button type="submit" className="admin-btn admin-btn-primary" disabled={loading}>
            {loading ? 'Сохранение...' : 'Сохранить и разрешить'}
          </button>
        </div>
      </form>
    </AdminModal>
  );
}

