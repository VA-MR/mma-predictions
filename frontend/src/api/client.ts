/**
 * API Client for MMA Scoring Backend
 */

const API_BASE = '/api';

// Types
export interface Fighter {
  id: number;
  name: string;
  name_english: string | null;
  country: string | null;
  wins: number;
  losses: number;
  draws: number;
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  reach_cm: number | null;
  style: string | null;
  weight_class: string | null;
  ranking: string | null;
  wins_ko_tko: number | null;
  wins_submission: number | null;
  wins_decision: number | null;
  losses_ko_tko: number | null;
  losses_submission: number | null;
  losses_decision: number | null;
  profile_url: string | null;
  profile_scraped: boolean;
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
  result?: FightResult | null;
  // Event metadata
  event_name: string | null;
  event_date: string | null;
  organization: string | null;
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
  is_correct: boolean | null;
  resolved_at: string | null;
  user?: User;
  fight?: Fight;
}

export interface RoundScore {
  id: number;
  round_number: number;
  fighter1_score: number;
  fighter2_score: number;
  is_correct?: boolean | null;
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
  correct_rounds: number;
  total_rounds: number;
  resolved_at: string | null;
  user?: User;
  fight?: Fight;
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

// Fighters API
export async function getFighter(id: number): Promise<Fighter> {
  return apiFetch<Fighter>(`/fighters/${id}`);
}

export async function getFighterFights(id: number, limit = 10): Promise<Fight[]> {
  return apiFetch<Fight[]>(`/fighters/${id}/fights?limit=${limit}`);
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

// Admin API Types
export interface Organization {
  name: string;
  event_count: number;
}

export type FighterDetail = Fighter;

export interface FighterCreateUpdate {
  name: string;
  name_english?: string | null;
  country?: string | null;
  wins?: number;
  losses?: number;
  draws?: number;
  age?: number | null;
  height_cm?: number | null;
  weight_kg?: number | null;
  reach_cm?: number | null;
  style?: string | null;
  weight_class?: string | null;
  ranking?: string | null;
  wins_ko_tko?: number | null;
  wins_submission?: number | null;
  wins_decision?: number | null;
  losses_ko_tko?: number | null;
  losses_submission?: number | null;
  losses_decision?: number | null;
  profile_url?: string | null;
  profile_scraped?: boolean;
}

export interface EventCreateUpdate {
  name: string;
  organization: string;
  event_date?: string | null;
  time_msk?: string | null;
  location?: string | null;
  url: string;
  slug: string;
  is_upcoming?: boolean;
}

export interface FightCreateUpdate {
  event_id: number;
  fighter1_id?: number | null;
  fighter2_id?: number | null;
  card_type?: string;
  weight_class?: string | null;
  rounds?: number | null;
  scheduled_time?: string | null;
  fight_order?: number | null;
}

// Fight Result Types
export interface OfficialRoundScore {
  id?: number;
  round_number: number;
  fighter1_score: number;
  fighter2_score: number;
}

export interface OfficialScorecard {
  id?: number;
  judge_name: string;
  round_scores: OfficialRoundScore[];
  total_fighter1?: number;
  total_fighter2?: number;
}

export interface FightResultCreate {
  winner: 'fighter1' | 'fighter2' | 'draw' | 'no_contest';
  method: 'ko_tko' | 'submission' | 'decision' | 'dq';
  finish_round?: number | null;
  finish_time?: string | null;
  official_scorecards: OfficialScorecard[];
}

export interface FightResult {
  id: number;
  fight_id: number;
  winner: 'fighter1' | 'fighter2' | 'draw' | 'no_contest';
  method: 'ko_tko' | 'submission' | 'decision' | 'dq';
  finish_round: number | null;
  finish_time: string | null;
  is_resolved: boolean;
  official_scorecards: OfficialScorecard[];
  created_at: string;
  updated_at: string;
}

// Admin API - Organizations
export async function getAdminOrganizations(skip = 0, limit = 100): Promise<Organization[]> {
  return apiFetch<Organization[]>(`/admin/organizations?skip=${skip}&limit=${limit}`);
}

// Admin API - Fighters
export async function getAdminFighters(skip = 0, limit = 100, search?: string): Promise<FighterDetail[]> {
  let url = `/admin/fighters?skip=${skip}&limit=${limit}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  return apiFetch<FighterDetail[]>(url);
}

export async function getAdminFighter(id: number): Promise<FighterDetail> {
  return apiFetch<FighterDetail>(`/admin/fighters/${id}`);
}

export async function createAdminFighter(data: FighterCreateUpdate): Promise<FighterDetail> {
  return apiFetch<FighterDetail>('/admin/fighters', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAdminFighter(id: number, data: FighterCreateUpdate): Promise<FighterDetail> {
  return apiFetch<FighterDetail>(`/admin/fighters/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteAdminFighter(id: number): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/admin/fighters/${id}`, {
    method: 'DELETE',
  });
}

// Admin API - Events
export async function getAdminEvents(skip = 0, limit = 100, organization?: string): Promise<Event[]> {
  let url = `/admin/events?skip=${skip}&limit=${limit}`;
  if (organization) url += `&organization=${encodeURIComponent(organization)}`;
  return apiFetch<Event[]>(url);
}

export async function getAdminEvent(id: number): Promise<Event> {
  return apiFetch<Event>(`/admin/events/${id}`);
}

export async function createAdminEvent(data: EventCreateUpdate): Promise<Event> {
  return apiFetch<Event>('/admin/events', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAdminEvent(id: number, data: EventCreateUpdate): Promise<Event> {
  return apiFetch<Event>(`/admin/events/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteAdminEvent(id: number): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/admin/events/${id}`, {
    method: 'DELETE',
  });
}

// Admin API - Fights
export async function getAdminFights(skip = 0, limit = 100, eventId?: number): Promise<Fight[]> {
  let url = `/admin/fights?skip=${skip}&limit=${limit}`;
  if (eventId) url += `&event_id=${eventId}`;
  return apiFetch<Fight[]>(url);
}

export async function getAdminFight(id: number): Promise<Fight> {
  return apiFetch<Fight>(`/admin/fights/${id}`);
}

export async function createAdminFight(data: FightCreateUpdate): Promise<Fight> {
  return apiFetch<Fight>('/admin/fights', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAdminFight(id: number, data: FightCreateUpdate): Promise<Fight> {
  return apiFetch<Fight>(`/admin/fights/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteAdminFight(id: number): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/admin/fights/${id}`, {
    method: 'DELETE',
  });
}

// Admin API - Fight Results
export async function getFightResult(fightId: number): Promise<FightResult> {
  return apiFetch<FightResult>(`/admin/fights/${fightId}/result`);
}

export async function createFightResult(fightId: number, data: FightResultCreate): Promise<FightResult> {
  return apiFetch<FightResult>(`/admin/fights/${fightId}/result`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateFightResult(fightId: number, data: FightResultCreate): Promise<FightResult> {
  return apiFetch<FightResult>(`/admin/fights/${fightId}/result`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteFightResult(fightId: number): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/admin/fights/${fightId}/result`, {
    method: 'DELETE',
  });
}

// Get fights for a specific event (for admin event management)
export async function getEventFights(eventId: number): Promise<Fight[]> {
  return apiFetch<Fight[]>(`/admin/fights?event_id=${eventId}`);
}

