import type { Catalog, Passenger, Request } from '../shared/types';
import { Icon, ago, useNow } from '../shared/ui';
import { LANG_LABEL, NEED_LABEL, STATUS_LABEL, URGENCY } from './labels';

export function PassengerChips({ p }: { p?: Passenger }) {
  if (!p) return null;
  return (
    <span className="chips">
      <span className="chip sky"><Icon name="Languages" size={14} /> {LANG_LABEL[p.lang].ja} {LANG_LABEL[p.lang].en}</span>
      {p.senior && <span className="chip saffron"><Icon name="Type" size={14} /> シニア Senior</span>}
      {p.first_time && <span className="chip"><Icon name="Plane" size={14} /> 初搭乗 First flight</span>}
      {p.pictures_first && <span className="chip"><Icon name="Image" size={14} /> 絵優先 Pictures</span>}
      {p.needs.map((n) => NEED_LABEL[n] && (
        <span key={n} className="chip green"><Icon name={NEED_LABEL[n].icon} size={14} /> {NEED_LABEL[n].ja} {NEED_LABEL[n].en}</span>
      ))}
    </span>
  );
}

export default function RequestCard({ req, cat, pax, send }: {
  req: Request; cat: Catalog; pax?: Passenger; send: (m: object) => void;
}) {
  const now = useNow(5000);
  const intent = cat.intents.find((i) => i.id === req.intent);
  if (!intent) return null;
  const u = URGENCY[req.urgency];
  const lastReply = req.replies[req.replies.length - 1];
  return (
    <article className={`card u${req.urgency} s-${req.status}`} aria-label={`${req.seat} ${intent.labels.en}`}>
      <div className="seat-col">
        <span className="seat">{req.seat}</span>
        <span className={`chip ${u.cls}`}><Icon name={u.icon} size={14} /> {u.ja} {u.en}</span>
        <span className="age">{ago(now - req.created)}</span>
      </div>
      <div className="body">
        <div className="what">
          <Icon name={intent.icon} size={34} />
          <div>
            <p className="ja" lang="ja">{intent.labels.ja}</p>
            <p className="en">{intent.labels.en}</p>
          </div>
        </div>
        <PassengerChips p={pax} />
        <p className="meta">
          {req.via === 'voice' && <span className="chip"><Icon name="Mic" size={14} /> 音声 Voice {req.confidence ? `${Math.round(req.confidence * 100)}%` : ''}</span>}
          <span className="chip">{STATUS_LABEL[req.status].ja} {STATUS_LABEL[req.status].en}</span>
          {lastReply && (req.understood_at
            ? <span className="chip green"><Icon name="BadgeCheck" size={14} /> 理解確認 Understood</span>
            : <span className="chip saffron"><Icon name="Clock" size={14} /> 理解待ち Waiting for &quot;understood&quot;</span>)}
        </p>
        <div className="actions">
          {req.status === 'new' && (
            <button className="btn primary" onClick={() => send({ t: 'seen', req_id: req.id })}>
              <Icon name="Footprints" /> 向かいます · On my way
            </button>
          )}
          {intent.replies.map((rid) => {
            const r = cat.replies.find((x) => x.id === rid);
            if (!r) return null;
            return (
              <button key={rid} className="btn" onClick={() => send({ t: 'reply', req_id: req.id, reply_id: rid })}>
                <Icon name={r.icon} size={18} />
                <span><span lang="ja">{r.text.ja.replace(/。$/, '')}</span><small>{r.text.en}</small></span>
              </button>
            );
          })}
          <button className="btn dark" onClick={() => send({ t: 'done', req_id: req.id })}>
            <Icon name="Check" /> 完了 · Done
          </button>
        </div>
      </div>
    </article>
  );
}
