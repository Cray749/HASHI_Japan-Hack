import { useEffect, useRef, useState } from 'react';
import { Recorder, micAvailable } from '../passenger/recorder';
import type { LanguageInfo } from '../shared/types';
import { Bridge, Icon } from '../shared/ui';

interface LiveResult {
  ok: boolean;
  error?: string;
  heard?: string;
  translation?: string | null;
  match?: { intent: string; ja: string; en: string; confidence: number; mode: string } | null;
}

const JA: LanguageInfo = { code: 'ja', name: '日本語', voice: true, status: 'draft' };

/** Speak or type, see what was heard and the translation. Open-ended, so it is labelled as unverified. */
export default function App() {
  const [langs, setLangs] = useState<LanguageInfo[]>([]);
  const [src, setSrc] = useState('hi');
  const [tgt, setTgt] = useState('ja');
  const [canTranslate, setCanTranslate] = useState(false);
  const [state, setState] = useState<'idle' | 'rec' | 'busy'>('idle');
  const [res, setRes] = useState<LiveResult | null>(null);
  const [typed, setTyped] = useState('');
  const rec = useRef<Recorder | null>(null);

  useEffect(() => {
    fetch('/api/catalog').then((r) => r.json()).then((c) => setLangs([...c.languages, JA])).catch(() => undefined);
    fetch('/api/live/info').then((r) => r.json()).then((i) => setCanTranslate(!!i.translate)).catch(() => undefined);
  }, []);

  const start = async () => {
    if (state !== 'idle') return;
    try {
      const r = new Recorder();
      await r.start();
      rec.current = r;
      setState('rec');
    } catch {
      setRes({ ok: false, error: 'mic' });
    }
  };

  const stop = async () => {
    const r = rec.current;
    rec.current = null;
    if (!r) return;
    setState('busy');
    try {
      const blob = await r.stop();
      if (!blob) throw new Error('short');
      const form = new FormData();
      form.append('audio', blob, 'v.wav');
      form.append('src', src);
      form.append('tgt', tgt);
      setRes((await (await fetch('/api/live', { method: 'POST', body: form })).json()) as LiveResult);
    } catch {
      setRes({ ok: false, error: 'failed' });
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
      setRes({ ok: r.ok, heard: typed, translation: r.ok ? j.text : null, error: r.ok ? undefined : 'no_model' });
    } catch {
      setRes({ ok: false, error: 'failed' });
    }
    setState('idle');
  };

  const name = (c: string) => langs.find((l) => l.code === c)?.name ?? c;
  const swap = () => { setSrc(tgt); setTgt(src); setRes(null); };

  return (
    <main className="live">
      <header>
        <Bridge size={64} color="#fff" />
        <div>
          <h1>HASHI Live</h1>
          <p>話して翻訳 · Speak and see the translation</p>
        </div>
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
          <span>{state === 'rec' ? '離すと翻訳 · Release to translate' : state === 'busy' ? '処理中… Working…' : '押して話す · Hold and speak'}</span>
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

      {res && (
        <section className="result" aria-live="polite">
          {!res.ok && <p className="note">うまくいきませんでした。もう一度どうぞ。 Could not do that ({res.error}). Try again.</p>}
          {res.heard !== undefined && res.ok !== false && (
            <>
              <p className="label">聞こえた内容 · Heard ({name(src)})</p>
              <p className="heard" lang={src}>{res.heard || '…'}</p>
            </>
          )}
          {res.translation && (
            <>
              <p className="label">翻訳 · Translation ({name(tgt)}) <span className="chip saffron">機械翻訳・未確認 Machine translation, unverified</span></p>
              <p className="trans" lang={tgt}>{res.translation}</p>
            </>
          )}
          {res.ok && !res.translation && !canTranslate && (
            <p className="note">Free translation model not installed here (python scripts/get_nllb.py). The cabin request match below still works.</p>
          )}
          {res.match && (
            <div className="match">
              <p className="label">キャビン依頼として認識 · Recognised cabin request <span className="chip green">{Math.round(res.match.confidence * 100)}%{res.match.mode === 'confirm' ? ' · ask to confirm' : ''}</span></p>
              <p className="trans" lang="ja">{res.match.ja}</p>
              <p className="heard">{res.match.en}</p>
              <p className="note">This one is the vetted Japanese written in advance, not machine translation.</p>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
