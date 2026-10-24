import { useEffect, useState } from 'react';
import type { Announcement, Catalog, ExitCheck, Intent, MatchResult, PaxLang } from '../shared/types';
import { Bridge, Icon, SPEECH_LANG, playAudio } from '../shared/ui';
import { CHECKIN, t } from './i18n';
import type { Profile } from './profile';

export function AnnouncementOverlay({ ann, cat, p, onAck }: {
  ann: Announcement; cat: Catalog; p: Profile; onAck: (id: string) => void;
}) {
  const phrase = cat.announcements.find((a) => a.id === ann.phrase);
  const text = phrase ? phrase.text[p.lang] ?? phrase.text.en : ann.custom ?? '';
  const audio = phrase ? `/audio/ann_${phrase.id}_${p.lang}.mp3` : '';
  useEffect(() => {
    if (audio) playAudio(audio, text, SPEECH_LANG[p.lang]);
    if ('vibrate' in navigator) navigator.vibrate?.([200, 100, 200]);
  }, [ann.id]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className="overlay ann" role="alertdialog" aria-live="assertive" lang={p.lang}>
      <p className="overlay-label"><Icon name="Megaphone" /> {t(p.lang, 'announcement')}</p>
      <Icon name={ann.icon} size={p.senior ? 110 : 84} />
      <p className="ann-text">{text}</p>
      {audio && (
        <button className="btn" onClick={() => playAudio(audio, text, SPEECH_LANG[p.lang])}>
          <Icon name="Volume2" /> {t(p.lang, 'play')}
        </button>
      )}
      <button className="btn good wide" onClick={() => onAck(ann.id)}>
        <Icon name="BadgeCheck" /> {t(p.lang, 'understood')}
      </button>
    </div>
  );
}

/** Teach-back for the exit row: willing and able, and when do you open the door. */
export function ExitOverlay({ check, p, onAnswer }: {
  check: ExitCheck; p: Profile; onAnswer: (check: string, willing: boolean, answer: string) => void;
}) {
  const [willing, setWilling] = useState<boolean | null>(null);
  const [done, setDone] = useState(false);
  const lang = p.lang;
  if (done) {
    return (
      <div className="overlay" lang={lang}>
        <Icon name="BadgeCheck" size={80} />
        <p className="ann-text">{t(lang, 'exitThanks')}</p>
      </div>
    );
  }
  return (
    <div className="overlay" role="dialog" lang={lang}>
      <p className="overlay-label"><Icon name="DoorOpen" /> {t(lang, 'exitTitle')}</p>
      {willing === null ? (
        <>
          <p className="ann-small">{t(lang, 'exitIntro')}</p>
          <p className="ann-text">{t(lang, 'exitQ1')}</p>
          <button className="btn good wide" onClick={() => setWilling(true)}><Icon name="Check" /> {t(lang, 'yes')}</button>
          <button className="btn wide" onClick={() => { setDone(true); onAnswer(check.id, false, ''); }}>
            <Icon name="X" /> {t(lang, 'no')}
          </button>
        </>
      ) : (
        <>
          <p className="ann-text">{t(lang, 'exitQ2')}</p>
          {(['when_told', 'right_away', 'unknown'] as const).map((a, i) => (
            <button key={a} className="btn wide" onClick={() => { setDone(true); onAnswer(check.id, true, a); }}>
              {t(lang, (['exitA1', 'exitA2', 'exitA3'] as const)[i])}
            </button>
          ))}
        </>
      )}
    </div>
  );
}

/** "Did you mean ...?" after a voice request the matcher is not sure about. */
export function ConfirmOverlay({ result, cat, lang, senior, onPick, onClose }: {
  result: MatchResult; cat: Catalog; lang: PaxLang; senior: boolean;
  onPick: (i: Intent, conf: number) => void; onClose: () => void;
}) {
  const items = result.candidates
    .map((c) => ({ c, i: cat.intents.find((x) => x.id === c.intent) }))
    .filter((x): x is { c: MatchResult['candidates'][number]; i: Intent } => !!x.i);
  return (
    <div className="overlay" role="dialog" lang={lang}>
      <p className="overlay-label">{t(lang, 'didYouMean')}</p>
      <div className="confirm-list">
        {items.map(({ c, i }, n) => (
          <button key={i.id} className={`tile big ${n === 0 ? 'first' : ''} ${senior ? 'senior' : ''}`} onClick={() => onPick(i, c.score)}>
            <Icon name={i.icon} size={senior ? 64 : 48} />
            <span className="tile-native">{i.labels[lang] ?? i.labels.en}</span>
            {lang !== 'en' && <span className="tile-en">{i.labels.en}</span>}
          </button>
        ))}
      </div>
      <button className="btn wide" onClick={onClose}><Icon name="X" /> {t(lang, 'no')}</button>
    </div>
  );
}

export function HelpSentOverlay({ lang, onCancel, onClose }: { lang: PaxLang; onCancel: () => void; onClose: () => void }) {
  return (
    <div className="overlay urgent" role="alertdialog" lang={lang}>
      <Icon name="Siren" size={96} />
      <p className="ann-text">{t(lang, 'sent')}</p>
      <p className="ann-small">{t(lang, 'seen')}</p>
      <button className="btn wide" onClick={onClose}><Icon name="Check" /> OK</button>
      <button className="link light" onClick={onCancel}>{t(lang, 'cancel')}</button>
    </div>
  );
}

export function LandedScreen({ lang }: { lang: PaxLang }) {
  return (
    <main className="onb splash" lang={lang}>
      <Bridge size={160} color="var(--navy)" />
      <p className="ann-text">{t(lang, 'landed')}</p>
      <p className="tag">橋 · पुल · ਪੁਲ</p>
    </main>
  );
}

/** Crew reached out first: a calm "Is everything OK?" card for people who never press a button. */
export function CheckinOverlay({ p, onAnswer }: { p: Profile; onAnswer: (a: 'fine' | 'call') => void }) {
  const [q, fine, call] = CHECKIN[p.lang] ?? CHECKIN.en;
  useEffect(() => {
    if ('vibrate' in navigator) navigator.vibrate?.(120);
  }, []);
  return (
    <div className="overlay" role="alertdialog" lang={p.lang}>
      <Icon name="Smile" size={p.senior ? 110 : 84} />
      <p className="ann-text">{q}</p>
      <button className="btn good wide" onClick={() => onAnswer('fine')}><Icon name="Check" /> {fine}</button>
      <button className="btn primary wide" onClick={() => onAnswer('call')}><Icon name="Hand" /> {call}</button>
    </div>
  );
}
