import { describe, it, expect } from 'vitest';
import { formatDate, formatDateShort, getCountryFlag, getFightWord } from './formatters';

describe('formatters', () => {
  describe('formatDate', () => {
    it('should format date string to Russian locale', () => {
      const result = formatDate('2025-12-15');
      expect(result).toContain('декабря');
      expect(result).toContain('2025');
    });

    it('should return TBD for null date', () => {
      expect(formatDate(null)).toBe('TBD');
    });
  });

  describe('formatDateShort', () => {
    it('should format date without year', () => {
      const result = formatDateShort('2025-12-15');
      expect(result).toContain('декабря');
      expect(result).not.toContain('2025');
    });

    it('should return TBD for null date', () => {
      expect(formatDateShort(null)).toBe('TBD');
    });
  });

  describe('getCountryFlag', () => {
    it('should return US flag for USA', () => {
      expect(getCountryFlag('USA')).toBe('🇺🇸');
      expect(getCountryFlag('United States')).toBe('🇺🇸');
    });

    it('should return Russian flag for Russia', () => {
      expect(getCountryFlag('Russia')).toBe('🇷🇺');
      expect(getCountryFlag('Россия')).toBe('🇷🇺');
    });

    it('should return Brazilian flag for Brazil', () => {
      expect(getCountryFlag('Brazil')).toBe('🇧🇷');
      expect(getCountryFlag('Бразилия')).toBe('🇧🇷');
    });

    it('should return globe emoji for unknown country', () => {
      expect(getCountryFlag('Unknown Country')).toBe('🌍');
    });

    it('should return globe emoji for null/undefined', () => {
      expect(getCountryFlag(null)).toBe('🌍');
      expect(getCountryFlag(undefined)).toBe('🌍');
    });
  });

  describe('getFightWord', () => {
    it('should return "бой" for 1', () => {
      expect(getFightWord(1)).toBe('бой');
      expect(getFightWord(21)).toBe('бой');
      expect(getFightWord(101)).toBe('бой');
    });

    it('should return "боя" for 2-4', () => {
      expect(getFightWord(2)).toBe('боя');
      expect(getFightWord(3)).toBe('боя');
      expect(getFightWord(4)).toBe('боя');
      expect(getFightWord(22)).toBe('боя');
    });

    it('should return "боёв" for 5-20 and 0', () => {
      expect(getFightWord(0)).toBe('боёв');
      expect(getFightWord(5)).toBe('боёв');
      expect(getFightWord(10)).toBe('боёв');
      expect(getFightWord(11)).toBe('боёв');
      expect(getFightWord(15)).toBe('боёв');
      expect(getFightWord(20)).toBe('боёв');
    });

    it('should handle teens correctly', () => {
      expect(getFightWord(11)).toBe('боёв');
      expect(getFightWord(12)).toBe('боёв');
      expect(getFightWord(13)).toBe('боёв');
      expect(getFightWord(14)).toBe('боёв');
    });
  });
});

