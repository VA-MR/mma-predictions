import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  setAuthToken,
  getAuthToken,
  getEvents,
  getFight,
  createPrediction,
  getMyPredictions,
} from './client';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setAuthToken(null);
  });

  describe('Token Management', () => {
    it('should set and get auth token', () => {
      setAuthToken('test-token-123');
      expect(getAuthToken()).toBe('test-token-123');
    });

    it('should clear auth token when set to null', () => {
      setAuthToken('test-token');
      setAuthToken(null);
      expect(getAuthToken()).toBeNull();
    });

    it('should persist token to localStorage', () => {
      setAuthToken('persistent-token');
      expect(localStorage.setItem).toHaveBeenCalledWith('auth_token', 'persistent-token');
    });

    it('should remove token from localStorage when cleared', () => {
      setAuthToken(null);
      expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('getEvents', () => {
    it('should fetch upcoming events by default', async () => {
      const mockEvents = [
        { id: 1, name: 'UFC 300', slug: 'ufc-300' },
        { id: 2, name: 'UFC 301', slug: 'ufc-301' },
      ];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockEvents),
      });

      const events = await getEvents();

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events?upcoming_only=true',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(events).toEqual(mockEvents);
    });

    it('should fetch all events when upcomingOnly is false', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      await getEvents(false);

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events?upcoming_only=false',
        expect.any(Object)
      );
    });

    it('should throw error on failed request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Server error' }),
      });

      await expect(getEvents()).rejects.toThrow('Server error');
    });
  });

  describe('getFight', () => {
    it('should fetch fight by ID', async () => {
      const mockFight = {
        id: 1,
        fighter1: { name: 'Fighter 1' },
        fighter2: { name: 'Fighter 2' },
      };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockFight),
      });

      const fight = await getFight(1);

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/fights/1',
        expect.any(Object)
      );
      expect(fight).toEqual(mockFight);
    });

    it('should throw error for non-existent fight', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Fight not found' }),
      });

      await expect(getFight(999)).rejects.toThrow('Fight not found');
    });
  });

  describe('createPrediction', () => {
    it('should create prediction with auth token', async () => {
      setAuthToken('user-token');
      const mockPrediction = {
        id: 1,
        fight_id: 1,
        predicted_winner: 'fighter1',
        win_method: 'ko_tko',
      };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPrediction),
      });

      const prediction = await createPrediction({
        fight_id: 1,
        predicted_winner: 'fighter1',
        win_method: 'ko_tko',
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/predictions',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer user-token',
          }),
          body: expect.any(String),
        })
      );
      expect(prediction).toEqual(mockPrediction);
    });

    it('should throw error for duplicate prediction', async () => {
      setAuthToken('user-token');
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: () => Promise.resolve({ detail: 'Prediction already exists' }),
      });

      await expect(
        createPrediction({
          fight_id: 1,
          predicted_winner: 'fighter1',
          win_method: 'ko_tko',
        })
      ).rejects.toThrow('Prediction already exists');
    });
  });

  describe('getMyPredictions', () => {
    it('should fetch user predictions with auth', async () => {
      setAuthToken('user-token');
      const mockPredictions = [
        { id: 1, fight_id: 1, predicted_winner: 'fighter1' },
        { id: 2, fight_id: 2, predicted_winner: 'fighter2' },
      ];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPredictions),
      });

      const predictions = await getMyPredictions();

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/predictions/mine',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer user-token',
          }),
        })
      );
      expect(predictions).toEqual(mockPredictions);
    });
  });
});

