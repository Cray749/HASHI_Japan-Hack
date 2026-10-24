import type { Announcement, Catalog, Checkin, Passenger, Request } from '../shared/types';
import { Icon, ago, useNow } from '../shared/ui';
import { LANG_LABEL } from './labels';

interface Reason { ja: string; en: string; points: number }

/**
 * Quiet-seat radar. A transparent score of who may need a gentle hello, built only from what the
 * passenger chose to share plus timing. No age and no guessing. Crew can see every reason.
 */
export function scoreSeat(p: Passenger, reqs: Request[], anns: Announcement[], checks: Checkin[], now: number) {
  const reasons: Reason[] = [];
  if (p.senior) reasons.push({ ja: 'シニアモード', en: 'Senior mode', points: 3 });
  if (p.first_time) reasons.push({ ja: '初搭乗', en: 'First flight', points: 2 });
  if (p.needs.includes('hearing')) reasons.push({ ja: '耳が不自由', en: 'Hard of hearing', points: 2 });
  if (p.needs.includes('mobility')) reasons.push({ ja: '歩行支援', en: 'Needs walking help', points: 2 });
  if (p.pictures_first) reasons.push({ ja: '絵を優先', en: 'Prefers pictures', points: 1 });
  const mine = reqs.filter((r) => r.seat === p.seat);
  const stamps = [p.joined, ...mine.map((r) => r.created), ...checks.filter((c) => c.seat === p.seat).map((c) => c.at)];
  for (const a of anns) {
    const ack = a.acks[p.seat];
    if (ack?.at) stamps.push(ack.at);
  }
  const quietMin = (now - Math.max(...stamps)) / 60;
  if (quietMin >= 2) {
    reasons.push({ ja: `${Math.floor(quietMin)}分間 操作なし`, en: `No activity for ${Math.floor(quietMin)} min`, points: Math.min(3, quietMin / 20) });
  }
  const unconfirmed = anns.filter((a) => a.kind === 'safety' && a.acks[p.seat]?.state === 'sent').length;
  if (unconfirmed) reasons.push({ ja: '未確認の安全アナウンス', en: 'Safety announcement not confirmed', points: 3 });
  const hasOpen = mine.some((r) => ['new', 'seen', 'replied'].includes(r.status));
  const score = hasOpen ? 0 : reasons.reduce((n, r) => n + r.points, 0); // open requests are already handled by the cards
  return { score, reasons, quietMin };
}

export default function RadarPanel({ pax, reqs, anns, checks, cat, send }: {
  pax: Record<string, Passenger>; reqs: Request[]; anns: Announcement[]; checks: Checkin[]; cat: Catalog;
  send: (m: object) => void;
}) {
  const now = useNow(5000);
  void cat;
  const rows = Object.values(pax)
    .map((p) => ({ p, ...scoreSeat(p, reqs, anns, checks, now), check: checks.find((c) => c.seat === p.seat) }))
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 8);
  return (
    <div className="panel">
      <h2>静かな席 <small>Quiet seats</small></h2>
      <p className="hint">
        自分から呼べない方に、乗務員から声をかけます。理由はすべて表示されます。 Crew reach out first to people who
        will not press the call button. Every reason is shown; nothing is inferred from age.
      </p>
      {rows.length === 0 && <p className="hint">いまは該当なし。 No seats to greet right now.</p>}
      {rows.map(({ p, score, reasons, check }) => (
        <section key={p.seat} className="radar-row">
          <header>
            <strong className="seat-big">{p.seat}</strong>
            <span className="chip sky"><Icon name="Languages" size={14} /> {LANG_LABEL[p.lang].ja} {LANG_LABEL[p.lang].en}</span>
            <span className="chip">{score.toFixed(1)} pt</span>
          </header>
          <p className="chips">
            {reasons.map((r) => (
              <span key={r.ja} className="chip saffron">{r.ja} <small>{r.en}</small></span>
            ))}
          </p>
          <div className="actions">
            <button className="btn primary" onClick={() => send({ t: 'checkin', seat: p.seat })}>
              <Icon name="Smile" /> 声かけ · Check in
            </button>
            {check && (
              <span className={`chip ${check.answer === 'fine' ? 'green' : check.answer === 'call' ? 'vermilion' : 'saffron'}`}>
                {check.answer === 'fine' ? '大丈夫 Fine' : check.answer === 'call' ? '呼んでいます Wants crew' : '返事待ち Waiting'}
                {' · '}{ago(now - (check.answered_at ?? check.at))}
              </span>
            )}
          </div>
        </section>
      ))}
    </div>
  );
}
