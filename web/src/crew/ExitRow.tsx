import { useState } from 'react';
import type { ExitCheck, Passenger } from '../shared/types';
import { Icon } from '../shared/ui';
import { EXIT_LABEL } from './labels';

const ANSWER: Record<string, string> = {
  when_told: '「乗務員の指示があってから」 Only when crew say so',
  right_away: '「止まったらすぐ」 As soon as it stops',
  unknown: '「わからない」 Does not know',
};

export default function ExitRowPanel({ pax, checks, send }: {
  pax: Record<string, Passenger>; checks: ExitCheck[]; send: (m: object) => void;
}) {
  const rowsWithPax = [...new Set(Object.keys(pax).map((s) => parseInt(s, 10)))].sort((a, b) => a - b);
  const [picked, setRow] = useState<number>(24);
  // default to row 24 (the demo's exit row) when it has passengers, else the first row
  const row = rowsWithPax.includes(picked) ? picked : rowsWithPax[0] ?? picked;
  const latest = (r: number) => [...checks].reverse().find((c) => c.row === r && c.open);
  const active = checks.filter((c) => c.open).sort((a, b) => b.created - a.created);

  return (
    <div className="panel">
      <h2>非常口座席チェック <small>Exit-row check (teach-back)</small></h2>
      <p className="hint">
        座席のお客様に「いつ非常口を開けますか」と確認します。 Passengers answer on their phone: willing and able, and when they would open the door.
      </p>
      <div className="target">
        <label>
          列 Row{' '}
          <select value={row} onChange={(e) => setRow(parseInt(e.target.value, 10))}>
            {(rowsWithPax.length ? rowsWithPax : [24]).map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        <button className="btn primary" disabled={!rowsWithPax.includes(row)}
          onClick={() => send({ t: 'exit_start', row })}>
          <Icon name="DoorOpen" /> 確認を開始 · Start check
        </button>
      </div>
      {!latest(row) && active.length === 0 && <p className="hint">まだ確認は始まっていません。 No check running.</p>}
      {active.map((c) => {
        const states = Object.values(c.seats);
        const passed = states.filter((s) => s.state === 'passed').length;
        return (
          <section key={c.id} className="exit-check">
            <h3>列 Row {c.row} <small>{passed} / {states.length} OK</small></h3>
            <div className="exit-seats">
              {Object.entries(c.seats).sort().map(([seat, s]) => {
                const L = EXIT_LABEL[s.state];
                const needsHuman = s.state === 'retry' || s.state === 'unwilling';
                return (
                  <div key={seat} className={`exit-seat ${L.cls}`}>
                    <strong>{seat}</strong>
                    <span className={`chip ${L.cls}`}><Icon name={L.icon} size={14} /> {L.ja} {L.en}</span>
                    {s.answer && <small>{ANSWER[s.answer] ?? s.answer}</small>}
                    {needsHuman && (
                      <span className="row-actions">
                        <button className="btn good" onClick={() => send({ t: 'exit_resolve', check_id: c.id, seat, ok: true })}>
                          <Icon name="Check" size={16} /> 対面で確認 In person OK
                        </button>
                        <button className="btn" onClick={() => send({ t: 'exit_resolve', check_id: c.id, seat, ok: false })}>
                          <Icon name="ArrowLeftRight" size={16} /> 席替え Reseat
                        </button>
                      </span>
                    )}
                    {s.state === 'waiting' && <small>「未確認の席には直接お声がけください」 crew will check in person</small>}
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
