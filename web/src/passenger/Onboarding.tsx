import { useState } from 'react';
import type { LanguageInfo } from '../shared/types';
import { FujiScene, Sakura, Waves } from '../shared/japan';
import { Icon } from '../shared/ui';
import { PROFILE_HELP, t } from './i18n';
import type { Profile } from './profile';

export default function Onboarding({ initial, languages, onDone }: {
  initial: Profile; languages: LanguageInfo[]; onDone: (p: Profile) => void;
}) {
  const hasSeat = /^\d{1,2}[A-Ka-k]$/.test(initial.seat);
  const [step, setStep] = useState(initial.preset ? (hasSeat ? 2 : 1) : 0);
  const [p, setP] = useState<Profile>(initial);
  const lang = p.lang;
  const voiceLang = languages.find((l) => l.code === lang)?.voice ?? false;
  const upd = (patch: Partial<Profile>) => setP((old) => ({ ...old, ...patch }));
  const seatOk = /^\d{1,2}[A-Ka-k]$/.test(p.seat.trim());

  const toggleNeed = (n: string) =>
    upd({ needs: p.needs.includes(n) ? p.needs.filter((x) => x !== n) : [...p.needs, n] });

  if (step === 0) {
    return (
      <main className="onb splash">
        <Sakura count={14} />
        <FujiScene />
        <h1 className="brand">HASHI <span className="three">橋 पुल ਪੁਲ</span></h1>
        <p className="tag">Don&apos;t translate. Understand.</p>
        <h2 className="pick">ਆਪਣੀ ਬੋਲੀ ਚੁਣੋ · अपनी भाषा चुनिए · Choose your language</h2>
        <div className="langs">
          {languages.map((l) => (
            <button key={l.code} className="btn big" onClick={() => { upd({ lang: l.code }); setStep(hasSeat ? 2 : 1); }} lang={l.code}>
              {l.name}
            </button>
          ))}
        </div>
        <a className="link" href="/live/">Live translator (speak and see the translation)</a>
        <Waves />
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
          {voiceLang && <li><Icon name="Mic" /> {t(lang, 'consent3')}</li>}
        </ul>
        {voiceLang ? (
          <>
            <button className="btn primary wide" onClick={() => { upd({ voiceOk: true }); setStep(3); }}>
              <Icon name="Mic" /> {t(lang, 'agreeVoice')}
            </button>
            <button className="btn wide" onClick={() => { upd({ voiceOk: false }); setStep(3); }}>
              {t(lang, 'agreeTap')}
            </button>
          </>
        ) : (
          <button className="btn primary wide" onClick={() => { upd({ voiceOk: false }); setStep(3); }}>
            {t(lang, 'start')}
          </button>
        )}
        <button className="btn wide" onClick={() => setStep(hasSeat ? 0 : 1)}><Icon name="ChevronLeft" /> {t(lang, 'back')}</button>
      </main>
    );
  }

  return (
    <main className="onb" lang={lang}>
      <h2>{t(lang, 'profileTitle')}</h2>
      <p className="help-line">{PROFILE_HELP[lang] ?? PROFILE_HELP.en}</p>
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
      <div className="row">
        <button className="btn" onClick={() => setStep(2)}><Icon name="ChevronLeft" /> {t(lang, 'back')}</button>
        <button className="btn primary" onClick={() => onDone({ ...p, seat: p.seat.trim().toUpperCase() })}>
          {t(lang, 'start')}
        </button>
      </div>
    </main>
  );
}
