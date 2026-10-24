import { useEffect, useRef, useState } from 'react';
import { Recorder, micAvailable } from '../passenger/recorder';
import type { LanguageInfo } from '../shared/types';
import { Bridge, Icon } from '../shared/ui';

interface Candidate { intent: string; score: number; ja: string; en: string }
interface LiveResult {
  ok: boolean;
  error?: string;
  heard?: string;
  translation?: string | null;
  translator?: string | null;
  match?: { intent: string; ja: string; en: string; confidence: number; mode: string } | null;
  steps?: {
    received?: { seconds: number };
    noise?: { applied: boolean; ms: number };
    asr?: { engine: string; ms: number };
    fold?: { sound_form: string };
    match?: { ms: number; mode: string; suspect: boolean; candidates: Candidate[] };
    translate?: { ms: number; model: string | null };
    discarded?: boolean;
    total_ms?: number;
  };
}

const JA: LanguageInfo = { code: 'ja', name: '日本語', voice: true, status: 'draft' };

/** Speak or type, then watch every step the system takes. Works with the Wi-Fi off. */
export default function App() {
  const [langs, setLangs] = useState<LanguageInfo[]>([]);
  const [src, setSrc] = useState('ta');
  const [tgt, setTgt] = useState('ja');
  const [canTranslate, setCanTranslate] = useState(false);
  const [state, setState] = useState<'idle' | 'rec' | 'busy'>('idle');
  const [res, setRes] = useState<LiveResult | null>(null);
  const [typed, setTyped] = useState('');
  const [seat, setSeat] = useState('24C');
  const [sent, setSent] = useState('');
  const [online, setOnline] = useState(navigator.onLine);
  const rec = useRef<Recorder | null>(null);

  useEffect(() => {
    fetch('/api/catalog').then((r) => r.json()).then((c) => setLangs([...c.languages, JA])).catch(() => undefined);
    fetch('/api/live/info').then((r) => r.json()).then((i) => setCanTranslate(!!i.translate)).catch(() => undefined);
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener('online', up);
    window.addEventListener('offline', down);
    return () => { window.removeEventListener('online', up); window.removeEventListener('offline', down); };
  }, []);

  const start = async () => {
    if (state !== 'idle') return;
    try {
      const r = new Recorder();
      await r.start();
      rec.current = r;
      setState('rec');
    } catch {
      setRes({ ok: false, error: 'microphone' });
    }
  };

  const stop = async () => {
    const r = rec.current;
    rec.current = null;
    if (!r) return;
    setState('busy');
    setSent('');
    try {
      const blob = await r.stop();
      if (!blob) throw new Error('short');
      const form = new FormData();
      form.append('audio', blob, 'v.wav');
      form.append('src', src);
      form.append('tgt', tgt);
      setRes((await (await fetch('/api/live', { method: 'POST', body: form })).json()) as LiveResult);
    } catch {
      setRes({ ok: false, error: 'too short or failed' });
    }
    setState('idle');
  };

  const translateTyped = async () => {
    if (!typed.trim()) return;
    setState('busy');
    try {
      const r = await fetch('/api/translate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: typed, src, tgt }),
      });
      const j = await r.json();
      setRes({ ok: r.ok, heard: typed, translation: r.ok ? j.text : null, translator: 'NLLB-200 600M', error: r.ok ? undefined : 'translation model not installed' });
    } catch {
      setRes({ ok: false, error: 'failed' });
    }
    setState('idle');
  };

  const sendToCrew = async () => {
    if (!res?.match) return;
    const r = await fetch('/api/live/send', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seat, intent: res.match.intent }),
    });
    setSent(r.ok ? `${seat}` : 'error');
  };

  const name = (c: string) => langs.find((l) => l.code === c)?.name ?? c;
  const swap = () => { setSrc(tgt); setTgt(src); setRes(null); };
  const st = res?.steps;

  return (
    <main className="live">
      <header>
        <Bridge size={64} color="#fff" />
        <div>
          <h1>HASHI Live</h1>
          <p>話して理解 · Speak and watch it understand</p>
        </div>
        <span className={`chip ${online ? 'saffron' : 'green'} net`}>
          <Icon name={online ? 'Wifi' : 'WifiOff'} size={14} /> {online ? 'ネット接続あり Online' : 'オフライン動作中 Offline, all local'}
        </span>
      </header>

      <section className="pick">
        <label>
          話す言語 · I speak
          <select value={src} onChange={(e) => { setSrc(e.target.value); setRes(null); }}>
            {langs.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
          </select>
        </label>
        <button className="btn" onClick={swap} aria-label="Swap languages"><Icon name="ArrowLeftRight" /></button>
        <label>
          翻訳先 · Translate to
          <select value={tgt} onChange={(e) => { setTgt(e.target.value); setRes(null); }}>
            {langs.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
          </select>
        </label>
      </section>

      {micAvailable() ? (
        <button
          className={`bigmic ${state}`}
          disabled={state === 'busy'}
          onPointerDown={(e) => { e.preventDefault(); void start(); }}
          onPointerUp={() => void stop()}
          onPointerCancel={() => void stop()}
        >
          <Icon name={state === 'busy' ? 'Loader' : 'Mic'} size={40} />
          <span>{state === 'rec' ? '離すと処理 · Release when done' : state === 'busy' ? '処理中… Working…' : '押して話す · Hold and speak'}</span>
          {state === 'rec' && <span className="wave" aria-hidden="true"><i /><i /><i /><i /><i /></span>}
        </button>
      ) : (
        <p className="note">The microphone needs https or localhost. Type below instead.</p>
      )}

      <section className="type">
        <input value={typed} onChange={(e) => setTyped(e.target.value)} placeholder="… or type here" aria-label="Type text" />
        <button className="btn primary" onClick={() => void translateTyped()} disabled={state === 'busy'}>
          <Icon name="Send" /> 翻訳 · Translate
        </button>
      </section>

      {res && !res.ok && <p className="note">うまくいきませんでした。もう一度どうぞ。 Could not do that ({res.error}). Try again.</p>}

      {res?.ok && st && (
        <ol className="pipeline" aria-label="Pipeline">
          <li className="done">
            <b>1 · 録音 Capture</b>
            <span>{st.received?.seconds} s of audio reached the local server</span>
          </li>
          <li className="done">
            <b>2 · ノイズ除去 Noise cleanup</b>
            <span>{st.noise?.applied ? `applied (${st.noise.ms} ms)` : 'off by default: it lowered accuracy in heavy noise'}</span>
          </li>
          <li className="done">
            <b>3 · 音声認識 Speech to text</b>
            <span>{st.asr?.engine}, on this laptop's CPU, {st.asr?.ms} ms, no internet</span>
            <em lang={src}>{res.heard || '…'}</em>
          </li>
          {st.fold && (
            <li className="done">
              <b>4 · 音の形に統一 Fold to a sound form</b>
              <span>every script becomes one rough sound spelling, so scripts cannot collide</span>
              <em className="mono">{st.fold.sound_form}</em>
            </li>
          )}
          {st.match && (
            <li className="done">
              <b>5 · 照合 Match to the 42 requests</b>
              <span>character n-grams plus fuzzy word overlap, {st.match.ms} ms{st.match.suspect ? ' · looping output, will not auto-send' : ''}</span>
              <div className="bars">
                {st.match.candidates.map((c) => (
                  <div key={c.intent} className="bar-row">
                    <span>{c.en}</span>
                    <div className="bar"><div style={{ width: `${Math.round(c.score * 100)}%` }} /></div>
                    <span>{Math.round(c.score * 100)}%</span>
                  </div>
                ))}
              </div>
            </li>
          )}
          <li className="done">
            <b>6 · 録音を破棄 Recording discarded</b>
            <span>kept in memory only, never written to disk</span>
          </li>
          {res.translation && (
            <li className="done">
              <b>＋ 翻訳 Translation</b>
              <span>{res.translator}, {st.translate?.ms} ms · machine translation, unverified ({name(tgt)})</span>
              <em lang={tgt}>{res.translation}</em>
            </li>
          )}
          <li className={res.match ? 'done' : 'wait'}>
            <b>7 · 乗務員カード Crew card</b>
            {res.match ? (
              <>
                <span>pre-written Japanese, confidence {Math.round(res.match.confidence * 100)}%{res.match.mode === 'confirm' ? ' · passenger confirms first' : ''}</span>
                <div className="jacard">
                  <p className="ja" lang="ja">{res.match.ja}</p>
                  <p className="en">{res.match.en}</p>
                </div>
                <div className="sendrow">
                  <label>席 Seat <input className="seat-in" value={seat} onChange={(e) => setSeat(e.target.value.toUpperCase())} /></label>
                  <button className="btn primary" onClick={() => void sendToCrew()}>
                    <Icon name="Send" /> 乗務員に送る · Send to crew
                  </button>
                  {sent && <span className="chip green">{sent === 'error' ? 'error' : `sent for seat ${sent}`}</span>}
                </div>
              </>
            ) : (
              <span>not sure enough: the passenger would see the picture tiles instead of a guess</span>
            )}
          </li>
          <li className="total">合計 Total {st.total_ms} ms</li>
        </ol>
      )}

      {res?.ok && !res.translation && !canTranslate && tgt !== 'en' && (
        <p className="note">Free translation to {name(tgt)} needs the NLLB model (python scripts/get_nllb.py). To English, Whisper translates without it.</p>
      )}
    </main>
  );
}
