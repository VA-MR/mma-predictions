/**
 * API Client for MMA Scoring Backend
 */

const API_BASE = '/api';

// Types
export interface Fighter {
  id: number;
  name: string;
  country: string | null;
  wins: number;
  losses: number;
  draws: number;
  profile_url: string | null;
  record: string;
}

export interface Fight {
  id: number;
  event_id: number;
  card_type: string;
  weight_class: string | null;
  rounds: number | null;
  scheduled_time: string | null;
  fight_order: number | null;
  fighter1: Fighter | null;
  fighter2: Fighter | null;
}

export interface MainEventInfo {
  fighter1_name: string | null;
  fighter2_name: string | null;
  weight_class: string | null;
}

export interface Event {
  id: number;
  name: string;
  organization: string;
  event_date: string | null;
  time_msk: string | null;
  location: string | null;
  is_upcoming: boolean;
  slug: string;
  url: string;
  fight_count: number;
  main_event: MainEventInfo | null;
}

export interface EventDetail extends Event {
  fights: Fight[];
}

export interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  photo_url: string | null;
  display_name: string;
  created_at: string;
}

export interface Prediction {
  id: number;
  user_id: number;
  fight_id: number;
  predicted_winner: 'fighter1' | 'fighter2';
  win_method: 'ko_tko' | 'submission' | 'decision' | 'dq';
  confidence: number | null;
  created_at: string;
  user?: User;
}

export interface RoundScore {
  id: number;
  round_number: number;
  fighter1_score: number;
  fighter2_score: number;
}

export interface Scorecard {
  id: number;
  user_id: number;
  fight_id: number;
  created_at: string;
  round_scores: RoundScore[];
  total_fighter1: number;
  total_fighter2: number;
  winner: string | null;
  user?: User;
}

export interface PredictionStats {
  total_predictions: number;
  fighter1_picks: number;
  fighter2_picks: number;
  fighter1_percentage: number;
  fighter2_percentage: number;
  methods: Record<string, { fighter1: number; fighter2: number }>;
}

export interface ScorecardStats {
  total_scorecards: number;
  rounds: Record<number, {
    average_fighter1: number;
    average_fighter2: number;
    fighter1_round_wins: number;
    fighter2_round_wins: number;
  }>;
  average_total_fighter1: number;
  average_total_fighter2: number;
  fighter1_wins: number;
  fighter2_wins: number;
  draws: number;
  fighter1_win_percentage: number;
  fighter2_win_percentage: number;
}

export interface UserStats {
  total_predictions: number;
  total_scorecards: number;
  predictions_by_method: Record<string, number>;
}

// Token management
let authToken: string | null = localStorage.getItem('auth_token');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
}

export function getAuthToken(): string | null {
  return authToken;
}

// API helpers
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// Auth API
export async function telegramLogin(authData: {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}): Promise<{ access_token: string; user: User }> {
  const response = await apiFetch<{ access_token: string; user: User }>(
    '/auth/telegram',
    {
      method: 'POST',
      body: JSON.stringify(authData),
    }
  );
  setAuthToken(response.access_token);
  return response;
}

export async function logout() {
  setAuthToken(null);
}

// Events API
export async function getEvents(upcomingOnly = true): Promise<Event[]> {
  return apiFetch<Event[]>(`/events?upcoming_only=${upcomingOnly}`);
}

export async function getEvent(slug: string): Promise<EventDetail> {
  return apiFetch<EventDetail>(`/events/${slug}`);
}

// Fights API
export async function getFight(id: number): Promise<Fight> {
  return apiFetch<Fight>(`/fights/${id}`);
}

export async function getFightStats(id: number): Promise<{
  fight: Fight;
  prediction_stats: PredictionStats;
  scorecard_stats: ScorecardStats;
}> {
  return apiFetch(`/fights/${id}/stats`);
}

// Predictions API
export async function createPrediction(data: {
  fight_id: number;
  predicted_winner: 'fighter1' | 'fighter2';
  win_method: 'ko_tko' | 'submission' | 'decision' | 'dq';
  confidence?: number;
}): Promise<Prediction> {
  return apiFetch<Prediction>('/predictions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getFightPredictions(fightId: number): Promise<Prediction[]> {
  return apiFetch<Prediction[]>(`/predictions/fight/${fightId}`);
}

export async function getFightPredictionStats(fightId: number): Promise<PredictionStats> {
  return apiFetch<PredictionStats>(`/predictions/fight/${fightId}/stats`);
}

export async function getMyPredictions(): Promise<Prediction[]> {
  return apiFetch<Prediction[]>('/predictions/mine');
}

export async function getMyFightPrediction(fightId: number): Promise<Prediction | null> {
  try {
    return await apiFetch<Prediction>(`/predictions/mine/fight/${fightId}`);
  } catch {
    return null;
  }
}

// Scorecards API
export async function createScorecard(data: {
  fight_id: number;
  round_scores: Array<{
    round_number: number;
    fighter1_score: number;
    fighter2_score: number;
  }>;
}): Promise<Scorecard> {
  return apiFetch<Scorecard>('/scorecards', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getFightScorecards(fightId: number): Promise<Scorecard[]> {
  return apiFetch<Scorecard[]>(`/scorecards/fight/${fightId}`);
}

export async function getFightScorecardStats(fightId: number): Promise<ScorecardStats> {
  return apiFetch<ScorecardStats>(`/scorecards/fight/${fightId}/stats`);
}

export async function getMyScorecards(): Promise<Scorecard[]> {
  return apiFetch<Scorecard[]>('/scorecards/mine');
}

export async function getMyFightScorecard(fightId: number): Promise<Scorecard | null> {
  try {
    return await apiFetch<Scorecard>(`/scorecards/mine/fight/${fightId}`);
  } catch {
    return null;
  }
}

// Users API
export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>('/users/me');
}

export async function getCurrentUserStats(): Promise<UserStats> {
  return apiFetch<UserStats>('/users/me/stats');
}

export async function getUser(id: number): Promise<User> {
  return apiFetch<User>(`/users/${id}`);
}

export async function getUserStats(id: number): Promise<UserStats> {
  return apiFetch<UserStats>(`/users/${id}/stats`);
}

