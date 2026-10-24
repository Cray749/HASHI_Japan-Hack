import type { PaxLang } from '../shared/types';
import { save, store } from '../shared/ui';

export interface Profile {
  lang: PaxLang;
  seat: string;
  senior: boolean;
  firstTime: boolean;
  picturesFirst: boolean;
  needs: string[];
  voiceOk: boolean;
  onboarded: boolean;
  preset?: boolean; // filled in from the phone app, so the language step is skipped
}

const KEY = 'hashi.pax.v1';

export function loadProfile(): Profile {
  const base: Profile = {
    lang: 'pa', seat: '', senior: false, firstTime: false, picturesFirst: false,
    needs: [], voiceOk: false, onboarded: false,
  };
  const saved = store<Partial<Profile>>(KEY, {});
  const fromUrl = new URLSearchParams(location.search).get('seat');
  const p = { ...base, ...saved };
  if (fromUrl && /^\d{1,2}[A-Ka-k]$/.test(fromUrl)) {
    if (p.seat !== fromUrl.toUpperCase()) p.onboarded = false;
    p.seat = fromUrl.toUpperCase();
  }
  // The phone app passes the profile in the URL fragment (it never reaches a server log).
  const frag = new URLSearchParams(location.hash.replace(/^#/, ''));
  if (frag.get('lang')) {
    p.lang = frag.get('lang') as Profile['lang'];
    p.senior = frag.get('senior') === '1';
    p.needs = (frag.get('needs') ?? '').split(',').filter(Boolean);
    p.onboarded = false;
    p.preset = true;
  }
  return p;
}

export function saveProfile(p: Profile): void {
  save(KEY, p);
}

export function wipeProfile(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* nothing to wipe */
  }
}
