import { useMemo } from 'react';

/** Falling cherry-blossom petals. Decorative only: hidden from screen readers, off when motion is reduced. */
export function Sakura({ count = 10 }: { count?: number }) {
  const petals = useMemo(
    () => Array.from({ length: count }, (_, i) => ({
      left: `${(i * 97 + 13) % 100}%`,
      delay: `${-((i * 1.7) % 12)}s`,
      dur: `${10 + ((i * 3) % 8)}s`,
      size: 8 + ((i * 5) % 8),
      sway: `${14 + ((i * 7) % 26)}px`,
    })),
    [count],
  );
  return (
    <div className="sakura" aria-hidden="true">
      {petals.map((p, i) => (
        <i key={i} style={{ left: p.left, animationDelay: p.delay, animationDuration: p.dur, width: p.size, height: p.size * 1.15, ['--sway' as string]: p.sway }} />
      ))}
    </div>
  );
}

/** Mount Fuji, the rising sun, drifting clouds and a plane with a contrail. */
export function FujiScene() {
  return (
    <svg className="fuji" viewBox="0 0 400 210" role="img" aria-label="Mount Fuji and a plane">
      <rect width="400" height="210" fill="#E3EBFD" />
      <circle className="sun" cx="300" cy="64" r="30" fill="#D9333F" />
      <g className="cloud c1" fill="#fff" opacity="0.95"><ellipse cx="70" cy="50" rx="34" ry="10" /><ellipse cx="92" cy="43" rx="22" ry="9" /></g>
      <g className="cloud c2" fill="#fff" opacity="0.9"><ellipse cx="250" cy="110" rx="30" ry="8" /><ellipse cx="270" cy="104" rx="18" ry="7" /></g>
      <path d="M10 200 L150 70 Q200 26 250 70 L392 200 Z" fill="#1B2B5B" />
      <path d="M118 102 L152 70 Q200 30 248 70 L284 104 L258 92 L238 112 L206 88 L178 114 L148 94 Z" fill="#fff" />
      <path d="M0 200 H400 V210 H0 Z" fill="#0E1A3A" />
      <g className="plane">
        <line x1="-70" y1="20" x2="-6" y2="20" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeDasharray="2 7" />
        <path d="M0 20 L22 17 L30 10 L34 10 L30 17 L40 17 L44 13 L46 13 L44 20 L46 27 L44 27 L40 23 L30 23 L34 30 L30 30 L22 23 Z" fill="#D9333F" />
      </g>
    </svg>
  );
}

/** A band of seigaiha (blue ocean waves), the traditional Japanese pattern. */
export function Waves({ className = '' }: { className?: string }) {
  return (
    <svg className={`waves ${className}`} viewBox="0 0 400 40" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <pattern id="seigaiha" width="40" height="20" patternUnits="userSpaceOnUse">
          <g fill="none" stroke="#3B6FE0" strokeWidth="1.4">
            <path d="M0 20a20 20 0 0 1 40 0M6 20a14 14 0 0 1 28 0M12 20a8 8 0 0 1 16 0" />
            <path d="M-20 10a20 20 0 0 1 40 0M-14 10a14 14 0 0 1 28 0M-8 10a8 8 0 0 1 16 0M20 10a20 20 0 0 1 40 0M26 10a14 14 0 0 1 28 0M32 10a8 8 0 0 1 16 0" />
          </g>
        </pattern>
      </defs>
      <rect width="400" height="40" fill="url(#seigaiha)" />
    </svg>
  );
}
