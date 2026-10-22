import { useState } from 'react';
import type { PaxLang } from '../shared/types';
import { Bridge, Icon } from '../shared/ui';
import { LANG_NAMES, t } from './i18n';
import type { Profile } from './profile';

const LANGS: PaxLang[] = ['pa', 'hi', 'en'];

export default function Onboarding({ initial, onDone }: { initial: Profile; onDone: (p: Profile) => void }) {
  const [step, setStep] = useState(0);
  const hasSeat = /^\d{1,2}[A-Ka-k]$/.test(initial.seat);
  const [p, setP] = useState<Profile>(initial);
  const lang = p.lang;
  const upd = (patch: Partial<Profile>) => setP((old) => ({ ...old, ...patch }));
  const seatOk = /^\d{1,2}[A-Ka-k]$/.test(p.seat.trim());

  const toggleNeed = (n: string) =>
    upd({ needs: p.needs.includes(n) ? p.needs.filter((x) => x !== n) : [...p.needs, n] });

  if (step === 0) {
    return (
      <main className="onb splash">
        <div className="bridge-hero"><Bridge size={190} color="var(--navy)" /></div>
        <h1 className="brand">HASHI <span className="three">橋 पुल ਪੁਲ</span></h1>
        <p className="tag">Don&apos;t translate. Understand.</p>
        <h2 className="pick">ਆਪਣੀ ਬੋਲੀ ਚੁਣੋ · अपनी भाषा चुनिए · Choose your language</h2>
        <div className="langs">
          {LANGS.map((l) => (
            <button key={l} className="btn big" onClick={() => { upd({ lang: l }); setStep(hasSeat ? 2 : 1); }} lang={l}>
              {LANG_NAMES[l]}
            </button>
          ))}
        </div>
      </main>
    );
  }

  if (step === 1) {
    return (
      <main className="onb">
        <h2 lang={lang}>{t(lang, 'seatAsk')}</h2>
        <input
          className="seat-input"
          value={p.seat}
          onChange={(e) => upd({ seat: e.target.value.toUpperCase().slice(0, 3) })}
          placeholder={t(lang, 'seatHint')}
          inputMode="text"
          autoCapitalize="characters"
          aria-label={t(lang, 'seatAsk')}
          autoFocus
        />
        <div className="row">
          <button className="btn" onClick={() => setStep(0)}>{t(lang, 'back')}</button>
          <button className="btn primary" disabled={!seatOk} onClick={() => setStep(2)}>{t(lang, 'next')}</button>
        </div>
      </main>
    );
  }

  if (step === 2) {
    return (
      <main className="onb" lang={lang}>
        <h2>{t(lang, 'consentTitle')}</h2>
        <ul className="consent">
          <li><Icon name="Eye" /> {t(lang, 'consent1')}</li>
          <li><Icon name="Clock" /> {t(lang, 'consent2')}</li>
          <li><Icon name="Mic" /> {t(lang, 'consent3')}</li>
        </ul>
        <button className="btn primary wide" onClick={() => { upd({ voiceOk: true }); setStep(3); }}>
          <Icon name="Mic" /> {t(lang, 'agreeVoice')}
        </button>
        <button className="btn wide" onClick={() => { upd({ voiceOk: false }); setStep(3); }}>
          {t(lang, 'agreeTap')}
        </button>
      </main>
    );
  }

  return (
    <main className="onb" lang={lang}>
      <h2>{t(lang, 'profileTitle')}</h2>
      <div className="checks">
        {([
          ['senior', p.senior, () => upd({ senior: !p.senior })],
          ['firstTime', p.firstTime, () => upd({ firstTime: !p.firstTime })],
          ['pictures', p.picturesFirst, () => upd({ picturesFirst: !p.picturesFirst })],
        ] as const).map(([key, on, toggle]) => (
          <button key={key} className={`check ${on ? 'on' : ''}`} onClick={toggle} aria-pressed={on}>
            <Icon name={on ? 'Check' : 'Circle'} /> {t(lang, key)}
          </button>
        ))}
        {(['veg', 'hearing', 'mobility'] as const).map((n) => (
          <button key={n} className={`check ${p.needs.includes(n) ? 'on' : ''}`} onClick={() => toggleNeed(n)}
            aria-pressed={p.needs.includes(n)}>
            <Icon name={p.needs.includes(n) ? 'Check' : 'Circle'} /> {t(lang, n)}
          </button>
        ))}
      </div>
      <button className="btn primary wide" onClick={() => onDone({ ...p, seat: p.seat.trim().toUpperCase() })}>
        {t(lang, 'start')}
      </button>
    </main>
  );
}
