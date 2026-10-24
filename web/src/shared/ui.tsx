import { useEffect, useState } from 'react';
import { ICONS } from './iconMap';

/** Icon by lucide name (names come from the data files). */
export function Icon({ name, size = 24, strokeWidth = 2, className }: {
  name: string;
  size?: number;
  strokeWidth?: number;
  className?: string;
}) {
  const Cmp = ICONS[name] ?? ICONS.Circle;
  return <Cmp size={size} strokeWidth={strokeWidth} className={className} aria-hidden="true" />;
}

/** The bridge motif: an arc with vertical hangers. Used on splash and empty states. */
export function Bridge({ size = 120, color = 'currentColor' }: { size?: number; color?: string }) {
  const hangers = [24, 40, 56, 72, 88, 104, 120, 136, 152, 168, 184];
  const arcY = (x: number) => 78 - 56 * Math.sin(((x - 16) / 168) * Math.PI);
  return (
    <svg width={size} height={size * 0.62} viewBox="0 0 200 124" role="img" aria-label="HASHI bridge">
      <path d="M16 78 Q100 -34 184 78" fill="none" stroke={color} strokeWidth="5" strokeLinecap="round" />
      {hangers.map((x) => (
        <line key={x} x1={x} x2={x} y1={arcY(x)} y2={88} stroke={color} strokeWidth="3" strokeLinecap="round" />
      ))}
      <rect x="6" y="88" width="188" height="9" rx="4.5" fill={color} />
      <rect x="28" y="97" width="9" height="22" rx="3" fill={color} />
      <rect x="163" y="97" width="9" height="22" rx="3" fill={color} />
    </svg>
  );
}

/** Seconds since a timestamp, refreshed every few seconds. */
export function useNow(ms = 5000): number {
  const [now, setNow] = useState(() => Date.now() / 1000);
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now() / 1000), ms);
    return () => window.clearInterval(id);
  }, [ms]);
  return now;
}

export function ago(seconds: number): string {
  if (seconds < 10) return 'now';
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m}m`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

export function store<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function save(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* private mode or blocked storage: the app still works, it just forgets */
  }
}

/** Play a pre-generated audio file; fall back to the phone's own voice if it is missing. */
let current: HTMLAudioElement | null = null;
export function playAudio(url: string, fallbackText?: string, speechLang?: string): void {
  try {
    current?.pause();
    const a = new Audio(url);
    current = a;
    a.onerror = () => speak(fallbackText, speechLang);
    void a.play().catch(() => speak(fallbackText, speechLang));
  } catch {
    speak(fallbackText, speechLang);
  }
}

export function speak(text?: string, lang?: string): void {
  if (!text || !('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    if (lang) u.lang = lang;
    window.speechSynthesis.speak(u);
  } catch {
    /* no voice available: the large text is still on screen */
  }
}

export const SPEECH_LANG: Record<string, string> = {
  hi: 'hi-IN', pa: 'pa-IN', en: 'en-US', ja: 'ja-JP', ta: 'ta-IN', te: 'te-IN', bn: 'bn-IN', gu: 'gu-IN',
  mr: 'mr-IN', kn: 'kn-IN', ml: 'ml-IN', th: 'th-TH', vi: 'vi-VN', id: 'id-ID', fil: 'fil-PH', ms: 'ms-MY',
  km: 'km-KH', my: 'my-MM',
};
