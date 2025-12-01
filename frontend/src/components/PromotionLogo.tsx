import { CSSProperties } from 'react';
import './PromotionLogo.css';

interface PromotionLogoProps {
  organization: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  style?: CSSProperties;
  showText?: boolean;
}

// Map of organization names to their logo files
const LOGO_MAP: Record<string, string> = {
  'ufc': '/logos/ufc.svg',
  'bellator': '/logos/bellator.svg',
  'one': '/logos/one.svg',
  'one championship': '/logos/one.svg',
  'pfl': '/logos/pfl.svg',
  'ksw': '/logos/ksw.svg',
  'aca': '/logos/aca.svg',
  'oktagon': '/logos/oktagon.svg',
  'oktagon mma': '/logos/oktagon.svg',
  'cage warriors': '/logos/cage-warriors.svg',
  'lfa': '/logos/lfa.svg',
  'brave cf': '/logos/brave-cf.svg',
  'brave': '/logos/brave-cf.svg',
  'uae warriors': '/logos/uae-warriors.svg',
  'ares fc': '/logos/ares-fc.svg',
  'ares': '/logos/ares-fc.svg',
  'mma series': '/logos/mma-series.svg',
  'open fc': '/logos/open-fc.svg',
};

// Fallback colors for promotions without logos
const ORG_COLORS: Record<string, string> = {
  'ufc': '#D20A0A',
  'bellator': '#1E3A8A',
  'one': '#C41E3A',
  'pfl': '#0066CC',
  'ksw': '#FF6B00',
  'aca': '#8B0000',
  'oktagon': '#FFD700',
  'cage warriors': '#00AA00',
  'lfa': '#4B0082',
  'brave cf': '#C0C0C0',
  'uae warriors': '#006400',
  'ares fc': '#800080',
  'mma series': '#333333',
  'open fc': '#2F4F4F',
};

const SIZE_MAP = {
  sm: { width: 32, height: 16 },
  md: { width: 48, height: 24 },
  lg: { width: 80, height: 40 },
  xl: { width: 120, height: 60 },
};

function getOrgKey(org: string): string {
  return org.toLowerCase().trim();
}

export default function PromotionLogo({ 
  organization, 
  size = 'md', 
  className = '',
  style = {},
  showText = false
}: PromotionLogoProps) {
  const orgKey = getOrgKey(organization);
  const logoPath = LOGO_MAP[orgKey];
  const dimensions = SIZE_MAP[size];
  const color = ORG_COLORS[orgKey] || '#666666';

  if (logoPath) {
    return (
      <div className={`promotion-logo-wrapper ${className}`} style={style}>
        <img
          src={logoPath}
          alt={`${organization} logo`}
          className={`promotion-logo promotion-logo--${size}`}
          style={{
            width: dimensions.width,
            height: dimensions.height,
            objectFit: 'contain',
          }}
          onError={(e) => {
            // If logo fails to load, replace with fallback
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const parent = target.parentElement;
            if (parent) {
              const fallback = document.createElement('div');
              fallback.className = 'promotion-logo-fallback';
              fallback.style.cssText = `
                width: ${dimensions.width}px;
                height: ${dimensions.height}px;
                background-color: ${color};
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-weight: 700;
                font-size: ${dimensions.height * 0.5}px;
              `;
              fallback.textContent = organization.slice(0, 3).toUpperCase();
              parent.appendChild(fallback);
            }
          }}
        />
        {showText && <span className="promotion-logo-text">{organization}</span>}
      </div>
    );
  }

  // Fallback: colored badge with abbreviation
  const abbreviation = organization
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 3);

  return (
    <div className={`promotion-logo-wrapper ${className}`} style={style}>
      <div
        className={`promotion-logo-fallback promotion-logo--${size}`}
        style={{
          width: dimensions.width,
          height: dimensions.height,
          backgroundColor: color,
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 700,
          fontSize: dimensions.height * 0.5,
          fontFamily: 'system-ui, -apple-system, sans-serif',
          textTransform: 'uppercase',
          letterSpacing: '-0.02em',
        }}
        title={organization}
      >
        {abbreviation}
      </div>
      {showText && <span className="promotion-logo-text">{organization}</span>}
    </div>
  );
}

// Export helper to get all available promotions
export function getAllPromotions(): string[] {
  return [
    'UFC',
    'Bellator',
    'ONE Championship',
    'PFL',
    'ACA',
    'KSW',
    'OKTAGON',
    'Cage Warriors',
    'LFA',
    'BRAVE CF',
    'UAE Warriors',
    'Ares FC',
    'MMA Series',
    'Open FC',
  ];
}

// Export the logo map for external use
export { LOGO_MAP, ORG_COLORS };
