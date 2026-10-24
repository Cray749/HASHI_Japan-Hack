import { useRef, useState } from 'react';
import type { Catalog, Intent, MatchResult, PaxLang, Request } from '../shared/types';
import { Icon, SPEECH_LANG, playAudio } from '../shared/ui';
import { CATEGORIES, t } from './i18n';
import type { Profile } from './profile';
import { Recorder, micAvailable } from './recorder';

const TINT: Record<string, string> = {
  drink: 'sky', food: 'saffron', comfort: 'grey', seat: 'grey', assist: 'green', info: 'grey', urgent: 'vermilion',
};

export function Tile({ intent, lang, senior, onPick }: {
  intent: Intent; lang: PaxLang; senior: boolean; onPick: (i: Intent) => void;
}) {
  return (
    <button className={`tile tint-${TINT[intent.cat] ?? 'grey'} ${senior ? 'senior' : ''}`} onClick={() => onPick(intent)}>
      <Icon name={intent.icon} size={senior ? 60 : 44} />
      <span className="tile-native" lang={lang}>{intent.labels[lang] ?? intent.labels.en}</span>
      {lang !== 'en' && <span className="tile-en">{intent.labels.en}</span>}
    </button>
  );
}

/** One open request: sent -> crew coming -> reply (picture, text, audio) -> understood. */
export function RequestCard({ req, cat, p, onUnderstood, onCancel }: {
  req: Request; cat: Catalog; p: Profile;
  onUnderstood: (id: string) => void; onCancel: (id: string) => void;
}) {
  const intent = cat.intents.find((i) => i.id === req.intent);
  const last = req.replies[req.replies.length - 1];
  const reply = last ? cat.replies.find((r) => r.id === last.reply) : undefined;
  const step = req.status === 'new' ? 1 : req.status === 'seen' ? 2 : 3;
  if (!intent) return null;
  return (
    <section className={`req step-${step} ${req.urgency === 3 ? 'urgent' : ''}`} aria-live="polite">
      <header>
        <Icon name={intent.icon} size={28} />
        <strong lang={p.lang}>{intent.labels[p.lang] ?? intent.labels.en}</strong>
        {req.status === 'new' || req.status === 'seen' ? (
          <button className="link" onClick={() => onCancel(req.id)}>{t(p.lang, 'cancel')}</button>
        ) : null}
      </header>
      <ol className="steps" lang={p.lang}>
        <li className="on"><Icon name="Check" size={18} /> {t(p.lang, 'sent')}</li>
        <li className={step >= 2 ? 'on' : ''}><Icon name={step >= 2 ? 'Check' : 'Clock'} size={18} /> {t(p.lang, 'seen')}</li>
        <li className={step >= 3 ? 'on' : ''}><Icon name={step >= 3 ? 'Check' : 'Clock'} size={18} /> {t(p.lang, 'replied')}</li>
      </ol>
      {reply && (
        <div className="reply" lang={p.lang}>
          <Icon name={reply.icon} size={p.senior ? 72 : 56} />
          <p className="reply-text">{reply.text[p.lang] ?? reply.text.en}</p>
          <button className="btn" onClick={() => playAudio(`/audio/reply_${reply.id}_${p.lang}.mp3`, reply.text[p.lang] ?? reply.text.en, SPEECH_LANG[p.lang])}>
            <Icon name="Volume2" /> {t(p.lang, 'play')}
          </button>
          {req.understood_at ? (
            <p className="done-line"><Icon name="BadgeCheck" /> {t(p.lang, 'understoodDone')}</p>
          ) : (
            <button className="btn good wide" onClick={() => onUnderstood(req.id)}>
              <Icon name="BadgeCheck" /> {t(p.lang, 'understood')}
            </button>
          )}
        </div>
      )}
    </section>
  );
}

/** Hold to speak (or tap once to start and once to finish, for people who find holding hard). */
export function VoiceButton({ p, disabled, voiceAllowed, onResult, onProblem }: {
  p: Profile; disabled: boolean; voiceAllowed: boolean;
  onResult: (r: MatchResult) => void; onProblem: (msg: string) => void;
}) {
  const rec = useRef<Recorder | null>(null);
  const downAt = useRef(0);
  const timer = useRef<number | undefined>(undefined);
  const [state, setState] = useState<'idle' | 'rec' | 'sticky' | 'busy'>('idle');
  const usable = p.voiceOk && voiceAllowed && micAvailable();

  const stop = async () => {
    window.clearTimeout(timer.current);
    const r = rec.current;
    rec.current = null;
    if (!r) return;
    setState('busy');
    try {
      const blob = await r.stop();
      if (!blob) { setState('idle'); onProblem(t(p.lang, 'tooShort')); return; }
      const form = new FormData();
      form.append('audio', blob, 'voice.wav');
      form.append('lang', p.lang);
      const res = await fetch('/api/voice', { method: 'POST', body: form });
      onResult((await res.json()) as MatchResult);
    } catch {
      onProblem(t(p.lang, 'tapPicture'));
    }
    setState('idle');
  };

  const begin = async () => {
    if (state !== 'idle') return;
    try {
      const r = new Recorder();
      await r.start();
      rec.current = r;
      downAt.current = Date.now();
      setState('rec');
      timer.current = window.setTimeout(() => void stop(), 9000);
    } catch {
      setState('idle');
      onProblem(t(p.lang, 'micBlocked'));
    }
  };

  const release = () => {
    if (state === 'rec') {
      if (Date.now() - downAt.current < 500) setState('sticky');
      else void stop();
    }
  };

  if (!usable) {
    return <p className="mic-off" lang={p.lang}><Icon name="MicOff" /> {p.voiceOk && voiceAllowed ? t(p.lang, 'micBlocked') : t(p.lang, 'tapPicture')}</p>;
  }
  return (
    <button
      className={`mic ${state}`}
      disabled={disabled || state === 'busy'}
      onPointerDown={(e) => { e.preventDefault(); if (state === 'sticky') void stop(); else void begin(); }}
      onPointerUp={release}
      onPointerCancel={release}
      onContextMenu={(e) => e.preventDefault()}
      lang={p.lang}
      aria-label={t(p.lang, 'holdSpeak')}
    >
      <Icon name={state === 'busy' ? 'Loader' : 'Mic'} size={36} />
      <span>{state === 'rec' || state === 'sticky' ? t(p.lang, 'listening') : state === 'busy' ? t(p.lang, 'thinking') : t(p.lang, 'holdSpeak')}</span>
    </button>
  );
}

export function MoreScreen({ cat, p, onPick, onBack }: {
  cat: Catalog; p: Profile; onPick: (i: Intent) => void; onBack: () => void;
}) {
  return (
    <div className="more">
      <button className="btn" onClick={onBack}><Icon name="ChevronLeft" /> {t(p.lang, 'back')}</button>
      {CATEGORIES.map((c) => {
        const items = cat.intents.filter((i) => i.cat === c.id);
        if (!items.length) return null;
        return (
          <section key={c.id}>
            <h3 lang={p.lang}><Icon name={c.icon} size={22} /> {c.label[p.lang] ?? c.label.en}</h3>
            <div className="grid">
              {items.map((i) => <Tile key={i.id} intent={i} lang={p.lang} senior={p.senior} onPick={onPick} />)}
            </div>
          </section>
        );
      })}
    </div>
  );
}
