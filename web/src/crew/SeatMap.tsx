import { useMemo } from 'react';
import type { Announcement, Catalog, Passenger, Request } from '../shared/types';
import { Icon } from '../shared/ui';
import { GreetingList } from './Greeting';
import { PassengerChips } from './RequestCard';

const LEFT = ['A', 'B', 'C'];
const RIGHT = ['D', 'E', 'F'];

export default function SeatMap({ pax, reqs, anns, cat, selected, onSelect }: {
  pax: Record<string, Passenger>; reqs: Request[]; anns: Announcement[]; cat: Catalog;
  selected: string; onSelect: (seat: string) => void;
}) {
  const rows = useMemo(() => {
    const nums = Object.keys(pax).map((s) => parseInt(s, 10));
    // show from just above the first occupied row; an empty cabin shows a default block
    const lo = nums.length ? Math.max(1, Math.min(...nums) - 1) : 10;
    const hi = Math.max(lo + 12, ...nums.map((n) => n + 1));
    return Array.from({ length: hi - lo + 1 }, (_, i) => lo + i);
  }, [pax]);

  const state = (seat: string) => {
    const open = reqs.filter((r) => r.seat === seat && ['new', 'seen', 'replied'].includes(r.status));
    if (open.some((r) => r.urgency === 3)) return 'urgent';
    if (open.length) return 'open';
    const waiting = anns.some((a) => a.acks[seat]?.state === 'sent' && a.kind === 'safety');
    if (waiting) return 'unconfirmed';
    return pax[seat] ? 'seated' : 'empty';
  };

  const icon = { urgent: 'TriangleAlert', open: 'Clock', unconfirmed: 'Megaphone', seated: '', empty: '' } as const;
  const word = { urgent: '緊急', open: '依頼', unconfirmed: '未確認', seated: '', empty: '' } as const;

  const cell = (row: number, col: string) => {
    const seat = `${row}${col}`;
    const st = state(seat);
    return (
      <button key={seat} className={`seat-cell ${st} ${selected === seat ? 'sel' : ''}`} onClick={() => onSelect(seat)}
        aria-label={`${seat} ${st}`} disabled={st === 'empty'}>
        <span className="sc-name">{col}</span>
        {icon[st] && <Icon name={icon[st]} size={14} />}
        {word[st] && <span className="sc-word">{word[st]}</span>}
      </button>
    );
  };

  const sel = pax[selected];
  const selReqs = reqs.filter((r) => r.seat === selected && ['new', 'seen', 'replied'].includes(r.status));
  const greet = sel ? cat.greetings.find((g) => g.lang === sel.lang) : undefined;

  return (
    <div className="seatmap">
      <div className="legend">
        <span className="chip vermilion"><Icon name="TriangleAlert" size={14} /> 緊急 Urgent</span>
        <span className="chip saffron"><Icon name="Clock" size={14} /> 依頼 Request</span>
        <span className="chip sky"><Icon name="Megaphone" size={14} /> 未確認 Not confirmed</span>
        <span className="chip green">搭乗者 Seated</span>
      </div>
      <div className="plane" role="grid">
        {rows.map((row) => (
          <div key={row} className="seat-row" role="row">
            <span className="row-no">{row}</span>
            {LEFT.map((c) => cell(row, c))}
            <span className="aisle" />
            {RIGHT.map((c) => cell(row, c))}
          </div>
        ))}
      </div>
      {sel && (
        <aside className="seat-detail">
          <h3>{selected} <small>{sel.online ? 'オンライン online' : 'オフライン offline'}</small></h3>
          <PassengerChips p={sel} />
          {selReqs.map((r) => {
            const i = cat.intents.find((x) => x.id === r.intent);
            return <p key={r.id} className="ja" lang="ja">{i?.labels.ja} <small>{i?.labels.en}</small></p>;
          })}
          {greet && <GreetingList set={greet} compact />}
        </aside>
      )}
    </div>
  );
}
