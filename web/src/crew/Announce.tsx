import { useState } from 'react';
import type { Announcement, Catalog } from '../shared/types';
import { Icon } from '../shared/ui';

export default function AnnouncePanel({ cat, anns, send }: {
  cat: Catalog; anns: Announcement[]; send: (m: object) => void;
}) {
  const [phrase, setPhrase] = useState(cat.announcements[0]?.id ?? '');
  const [scope, setScope] = useState<'all' | 'rows'>('all');
  const [from, setFrom] = useState('20');
  const [to, setTo] = useState('30');

  const rows = () => {
    const a = parseInt(from, 10), b = parseInt(to, 10);
    if (!a || !b) return [];
    return Array.from({ length: Math.abs(b - a) + 1 }, (_, i) => Math.min(a, b) + i);
  };

  const sendIt = () =>
    send({ t: 'announce', phrase_id: phrase, target: scope === 'all' ? { all: true } : { rows: rows() } });

  return (
    <div className="panel">
      <h2>アナウンス <small>Announcements</small></h2>
      <div className="phrases" role="radiogroup" aria-label="Announcement">
        {cat.announcements.map((a) => (
          <button key={a.id} role="radio" aria-checked={phrase === a.id}
            className={`phrase ${phrase === a.id ? 'on' : ''}`} onClick={() => setPhrase(a.id)}>
            <Icon name={a.icon} size={22} />
            <span><span lang="ja">{a.text.ja}</span><small>{a.text.en}</small></span>
            {a.kind === 'safety' && <span className="chip vermilion">安全 Safety</span>}
          </button>
        ))}
      </div>
      <div className="target">
        <div className="seg">
          <button className={scope === 'all' ? 'on' : ''} onClick={() => setScope('all')}>全席 All seats</button>
          <button className={scope === 'rows' ? 'on' : ''} onClick={() => setScope('rows')}>列 Rows</button>
        </div>
        {scope === 'rows' && (
          <span className="rows-input">
            <input value={from} onChange={(e) => setFrom(e.target.value)} inputMode="numeric" aria-label="From row" />
            –
            <input value={to} onChange={(e) => setTo(e.target.value)} inputMode="numeric" aria-label="To row" />
          </span>
        )}
        <button className="btn primary" onClick={sendIt}><Icon name="Send" /> 送信 · Send</button>
      </div>

      <h3>確認ボード <small>Understood board</small></h3>
      {anns.length === 0 && <p className="hint">まだありません。 Nothing sent yet.</p>}
      {[...anns].reverse().map((a) => {
        const p = cat.announcements.find((x) => x.id === a.phrase);
        const seats = Object.entries(a.acks);
        const ok = seats.filter(([, v]) => v.state === 'understood').length;
        const waiting = seats.filter(([, v]) => v.state === 'sent').map(([s]) => s);
        return (
          <section key={a.id} className="ack">
            <header>
              <Icon name={a.icon} size={20} />
              <strong lang="ja">{p ? p.text.ja : a.custom}</strong>
            </header>
            <div className="bar" role="progressbar" aria-valuenow={ok} aria-valuemax={seats.length}>
              <span style={{ width: seats.length ? `${(ok / seats.length) * 100}%` : '0%' }} />
            </div>
            <p>
              <Icon name="BadgeCheck" size={16} /> {ok} / {seats.length} 理解 understood
              {waiting.length === 0 && seats.length > 0 && <span className="chip green">全員確認 All confirmed</span>}
            </p>
            {waiting.length > 0 && (
              <p className="waiting">
                {waiting.map((s) => (
                  <span key={s} className="chip saffron"><Icon name="Clock" size={14} /> {s} 未確認 waiting</span>
                ))}
              </p>
            )}
          </section>
        );
      })}
    </div>
  );
}
