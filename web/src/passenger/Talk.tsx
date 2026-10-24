import { useEffect, useRef, useState } from 'react';
import { Icon, SPEECH_LANG, speak } from '../shared/ui';
import type { Profile } from './profile';
import { Recorder, micAvailable } from './recorder';
import { TALK } from './talkUi';

export interface Msg {
  id: string;
  from: 'passenger' | 'crew';
  original: string;
  lang: string;
  ja?: string;
  back?: string;
  translated?: string;
  lane: 'machine' | 'vetted';
  status: string;
  score?: number;
  warn?: boolean;
}

/** Live conversation with the crew. The passenger's words are checked by translating them back before they are sent. */
export default function Talk({ p, thread, pending, busy, error, onSay, onConfirm, onCancel, onBack }: {
  p: Profile; thread: Msg[]; pending: Msg | null; busy: boolean; error: string;
  onSay: (text: string) => void; onConfirm: (id: string) => void; onCancel: (id: string) => void; onBack: () => void;
}) {
  const [title, question, yes, again, caution] = TALK[p.lang] ?? TALK.en;
  const [typed, setTyped] = useState('');
  const [rec, setRec] = useState<'idle' | 'rec' | 'busy'>('idle');
  const recorder = useRef<Recorder | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }); }, [thread.length, pending?.id]);

  const start = async () => {
    if (rec !== 'idle') return;
    try {
      const r = new Recorder();
      await r.start();
      recorder.current = r;
      setRec('rec');
    } catch {
      setRec('idle');
    }
  };

  const stop = async () => {
    const r = recorder.current;
    recorder.current = null;
    if (!r) return;
    setRec('busy');
    try {
      const blob = await r.stop();
      if (blob) {
        const form = new FormData();
        form.append('audio', blob, 'v.wav');
        form.append('lang', p.lang);
        const j = await (await fetch('/api/stt', { method: 'POST', body: form })).json();
        if (j.ok && j.text?.trim()) onSay(j.text.trim());
      }
    } catch {
      /* the typed box is still there */
    }
    setRec('idle');
  };

  return (
    <div className="talk">
      <button className="btn" onClick={onBack}><Icon name="ChevronLeft" /> {title}</button>
      <div className="thread" lang={p.lang}>
        {thread.filter((m) => m.status !== 'cancelled' && m.status !== 'pending').map((m) => (
          <div key={m.id} className={`bubble ${m.from}`}>
            <p lang={m.from === 'crew' ? p.lang : m.lang}>{m.from === 'crew' ? m.translated : m.original}</p>
            <small>
              {m.from === 'crew' ? <><Icon name="Volume2" size={14} /> </> : null}
              {m.lane === 'vetted' ? '✔ pre-approved wording' : 'machine translation'}
            </small>
            {m.from === 'crew' && (
              <button className="link" onClick={() => speak(m.translated, SPEECH_LANG[p.lang])}><Icon name="Volume2" size={16} /></button>
            )}
          </div>
        ))}
        {pending && (
          <div className="check" role="alertdialog">
            <p className="q">{question}</p>
            <p className="big" lang={p.lang}>{pending.back}</p>
            <p className="ja-line" lang="ja">日本語: {pending.ja}</p>
            {pending.warn && <p className="caution"><Icon name="TriangleAlert" size={18} /> {caution}</p>}
            <div className="row">
              <button className="btn good" onClick={() => onConfirm(pending.id)}><Icon name="Check" /> {yes}</button>
              <button className="btn" onClick={() => onCancel(pending.id)}><Icon name="Mic" /> {again}</button>
            </div>
          </div>
        )}
        {error && <p className="caution">{error}</p>}
        <div ref={end} />
      </div>

      <div className="composer">
        {micAvailable() && (
          <button
            className={`mic small ${rec}`}
            disabled={busy || rec === 'busy'}
            onPointerDown={(e) => { e.preventDefault(); void start(); }}
            onPointerUp={() => void stop()}
            onPointerCancel={() => void stop()}
            aria-label="Hold to speak"
          >
            <Icon name={rec === 'busy' || busy ? 'Loader' : 'Mic'} size={30} />
          </button>
        )}
        <input value={typed} onChange={(e) => setTyped(e.target.value)} lang={p.lang} aria-label="Type" />
        <button className="btn primary" disabled={busy || !typed.trim()} onClick={() => { onSay(typed); setTyped(''); }}>
          <Icon name="Send" />
        </button>
      </div>
    </div>
  );
}
