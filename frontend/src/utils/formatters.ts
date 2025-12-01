/**
 * Shared formatting utilities for the frontend.
 */

/**
 * Format a date string to Russian locale with full format.
 * @param dateStr - ISO date string or null
 * @returns Formatted date string (e.g., "15 декабря 2025")
 */
export function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'TBD';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

/**
 * Format a date string to Russian locale with short format (no year).
 * @param dateStr - ISO date string or null
 * @returns Formatted date string (e.g., "15 декабря")
 */
export function formatDateShort(dateStr: string | null): string {
  if (!dateStr) return 'TBD';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
  });
}

/**
 * Country to flag emoji mapping.
 */
const COUNTRY_FLAGS: Record<string, string> = {
  // English names
  'USA': '🇺🇸',
  'United States': '🇺🇸',
  'Russia': '🇷🇺',
  'Brazil': '🇧🇷',
  'Mexico': '🇲🇽',
  'UK': '🇬🇧',
  'United Kingdom': '🇬🇧',
  'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'Ireland': '🇮🇪',
  'Japan': '🇯🇵',
  'Poland': '🇵🇱',
  'Australia': '🇦🇺',
  'Canada': '🇨🇦',
  'China': '🇨🇳',
  'South Korea': '🇰🇷',
  'Germany': '🇩🇪',
  'France': '🇫🇷',
  'Netherlands': '🇳🇱',
  'Sweden': '🇸🇪',
  'Kazakhstan': '🇰🇿',
  'Ukraine': '🇺🇦',
  'Georgia': '🇬🇪',
  'Armenia': '🇦🇲',
  'Azerbaijan': '🇦🇿',
  'Uzbekistan': '🇺🇿',
  'Tajikistan': '🇹🇯',
  'Kyrgyzstan': '🇰🇬',
  'Belarus': '🇧🇾',
  // Russian names
  'США': '🇺🇸',
  'Россия': '🇷🇺',
  'Бразилия': '🇧🇷',
  'Мексика': '🇲🇽',
  'Великобритания': '🇬🇧',
  'Англия': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'Ирландия': '🇮🇪',
  'Япония': '🇯🇵',
  'Польша': '🇵🇱',
  'Австралия': '🇦🇺',
  'Канада': '🇨🇦',
  'Китай': '🇨🇳',
  'Южная Корея': '🇰🇷',
  'Германия': '🇩🇪',
  'Франция': '🇫🇷',
  'Нидерланды': '🇳🇱',
  'Швеция': '🇸🇪',
  'Казахстан': '🇰🇿',
  'Украина': '🇺🇦',
  'Грузия': '🇬🇪',
  'Армения': '🇦🇲',
  'Азербайджан': '🇦🇿',
  'Узбекистан': '🇺🇿',
  'Таджикистан': '🇹🇯',
  'Киргизия': '🇰🇬',
  'Беларусь': '🇧🇾',
};

/**
 * Get flag emoji for a country.
 * @param country - Country name (English or Russian)
 * @returns Flag emoji or globe emoji if not found
 */
export function getCountryFlag(country: string | null): string {
  if (!country) return '🌍';
  return COUNTRY_FLAGS[country] || '🌍';
}

/**
 * Get the correct Russian word form for "fight" based on count.
 * @param count - Number of fights
 * @returns Correct word form ("бой", "боя", or "боёв")
 */
export function getFightWord(count: number): string {
  const lastTwo = count % 100;
  const lastOne = count % 10;

  if (lastTwo >= 11 && lastTwo <= 19) {
    return 'боёв';
  }
  if (lastOne === 1) {
    return 'бой';
  }
  if (lastOne >= 2 && lastOne <= 4) {
    return 'боя';
  }
  return 'боёв';
}

