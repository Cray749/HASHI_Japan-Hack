import { useEffect, useRef, useState } from 'react';
import { Recorder, micAvailable } from '../passenger/recorder';
import type { Msg } from '../passenger/Talk';
import type { Passenger } from '../shared/types';
import { Icon, SPEECH_LANG, speak } from '../shared/ui';
import { LANG_LABEL } from './labels';

/** Conversations with passengers. Crew type or speak Japanese; the passenger gets their own language. */
export default function TalkPanel({ pax, threads, selected, onSelect, send, notice }: {
  pax: Record<string, Passenger>; threads: Record<string, Msg[]>; selected: string;
  onSelect: (seat: string) => void; send: (m: object) => void; notice: string;
}) {
  const seats = Object.keys(pax).sort((a, b) => parseInt(a, 10) - parseInt(b, 10) || a.localeCompare(b));
  const withThread = seats.filter((s) => (threads[s] ?? []).some((m) => m.status === 'sent'));
  const seat = selected && pax[selected] ? selected : withThread[0] ?? seats[0] ?? '';
  const thread = (threads[seat] ?? []).filter((m) => m.status === 'sent');
  const [text, setText] = useState('');
  const [rec, setRec] = useState<'idle' | 'rec' | 'busy'>('idle');
  const recorder = useRef<Recorder | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const spoken = useRef<string>('');

  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }); }, [thread.length, seat]);

  // read the newest passenger message aloud in Japanese so a crew member with full hands can hear it
  useEffect(() => {
    const last = thread[thread.length - 1];
    if (last && last.from === 'passenger' && last.id !== spoken.current) {
      spoken.current = last.id;
      speak(last.ja, SPEECH_LANG.ja);
    }
  }, [thread.length]); // eslint-disable-line react-hooks/exhaustive-deps

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
        form.append('lang', 'ja');
        const j = await (await fetch('/api/stt', { method: 'POST', body: form })).json();
        if (j.ok && j.text?.trim()) setText(j.text.trim());
      }
    } catch {
      /* typing still works */
    }
    setRec('idle');
  };

  const sendNow = () => {
    if (!text.trim() || !seat) return;
    send({ t: 'crew_say', seat, text: text.trim(), src: 'ja' });
    setText('');
  };

  return (
    <div className="panel talkpanel">
      <h2>会話 <small>Conversation</small></h2>
      <div className="seat-pick">
        {seats.map((s) => (
          <button key={s} className={`chip ${s === seat ? 'saffron' : ''} ${withThread.includes(s) ? 'dotted' : ''}`} onClick={() => onSelect(s)}>
            {s} · {LANG_LABEL[pax[s].lang].ja}
          </button>
        ))}
      </div>
      {seat && (
        <p className="hint">
          {seat}: {LANG_LABEL[pax[seat].lang].ja} {LANG_LABEL[pax[seat].lang].en}。 日本語で入力または音声で話すと、乗客の言語になります。
          Type or speak Japanese; the passenger gets their own language.
        </p>
      )}
      <div className="cthread">
        {thread.length === 0 && <p className="hint">まだ会話はありません。 No messages yet.</p>}
        {thread.map((m) => (
          <div key={m.id} className={`cbubble ${m.from}`}>
            {m.from === 'passenger' ? (
              <>
                <p className="ja" lang="ja">{m.ja}</p>
                <small lang={m.lang}>{m.original}</small>
              </>
            ) : (
              <>
                <p className="ja" lang="ja">{m.original}</p>
                <small lang={m.lang}>→ {m.translated}</small>
                {m.back && <small className="back">back-translation: {m.back}</small>}
              </>
            )}
            <span className={`chip ${m.lane === 'vetted' ? 'green' : 'saffron'}`}>
              {m.lane === 'vetted' ? '承認済み Pre-approved' : '機械翻訳 Machine translation'}
              {m.from === 'passenger' && m.score != null ? ` · check ${m.score}%` : ''}
            </span>
          </div>
        ))}
        {notice && <p className="hint warn">{notice}</p>}
        <div ref={end} />
      </div>
      <div className="composer">
        {micAvailable() && (
          <button
            className={`mic small ${rec}`}
            disabled={rec === 'busy'}
            onPointerDown={(e) => { e.preventDefault(); void start(); }}
            onPointerUp={() => void stop()}
            onPointerCancel={() => void stop()}
            aria-label="Hold to speak Japanese"
          >
            <Icon name={rec === 'busy' ? 'Loader' : 'Mic'} size={28} />
          </button>
        )}
        <input value={text} lang="ja" onChange={(e) => setText(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') sendNow(); }}
          placeholder="日本語で入力 · Type in Japanese" aria-label="Message" />
        <button className="btn primary" onClick={sendNow} disabled={!text.trim() || !seat}><Icon name="Send" /></button>
      </div>
    </div>
  );
}
