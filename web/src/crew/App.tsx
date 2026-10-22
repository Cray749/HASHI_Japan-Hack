import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Announcement, Catalog, ExitCheck, Passenger, PaxLang, Request } from '../shared/types';
import { LiveSocket, loadCatalog, type SocketStatus } from '../shared/net';
import { Bridge, Icon, save, store } from '../shared/ui';
import AnnouncePanel from './Announce';
import ExitRowPanel from './ExitRow';
import GreetingPanel from './Greeting';
import RequestCard from './RequestCard';
import SeatMap from './SeatMap';
import { LANG_LABEL, URGENCY } from './labels';

type Tab = 'requests' | 'seats' | 'announce' | 'exit' | 'greet';

function useWide(): boolean {
  const q = '(min-width: 1000px)';
  const [wide, setWide] = useState(() => window.matchMedia(q).matches);
  useEffect(() => {
    const m = window.matchMedia(q);
    const f = () => setWide(m.matches);
    m.addEventListener('change', f);
    return () => m.removeEventListener('change', f);
  }, []);
  return wide;
}

/** Short two-tone beep for urgent requests (needs one tap on "sound" first). */
function beep(ctx: AudioContext | null) {
  if (!ctx) return;
  [880, 660, 880].forEach((f, i) => {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.frequency.value = f;
    o.connect(g);
    g.connect(ctx.destination);
    const t0 = ctx.currentTime + i * 0.22;
    g.gain.setValueAtTime(0.25, t0);
    g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.2);
    o.start(t0);
    o.stop(t0 + 0.21);
  });
}

export default function App() {
  const [cat, setCat] = useState<Catalog | null>(null);
  const [conn, setConn] = useState<SocketStatus>('connecting');
  const [pax, setPax] = useState<Record<string, Passenger>>({});
  const [reqs, setReqs] = useState<Record<string, Request>>({});
  const [anns, setAnns] = useState<Record<string, Announcement>>({});
  const [exits, setExits] = useState<Record<string, ExitCheck>>({});
  const [tab, setTab] = useState<Tab>('seats');
  const [selected, setSelected] = useState('');
  const [sound, setSound] = useState(false);
  const [showQr, setShowQr] = useState(false);
  const [filter, setFilter] = useState<'open' | 'all'>('open');
  // languages this crew member can speak; matching requests are flagged so they take them
  const [speaks, setSpeaks] = useState<PaxLang[]>(() => store<PaxLang[]>('hashi.crew.speaks', []));
  const toggleSpeak = (l: PaxLang) => {
    const next = speaks.includes(l) ? speaks.filter((x) => x !== l) : [...speaks, l];
    setSpeaks(next);
    save('hashi.crew.speaks', next);
  };
  const wide = useWide();
  const sock = useRef<LiveSocket | null>(null);
  const audio = useRef<AudioContext | null>(null);
  const soundRef = useRef(false);
  soundRef.current = sound;

  useEffect(() => {
    let alive = true;
    const go = () => loadCatalog().then((c) => alive && setCat(c)).catch(() => window.setTimeout(go, 2000));
    void go();
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    const s = new LiveSocket('/ws/crew', (m) => {
      switch (m.t) {
        case 'snapshot':
          setPax(Object.fromEntries((m.passengers as Passenger[]).map((p) => [p.seat, p])));
          setReqs(Object.fromEntries((m.requests as Request[]).map((r) => [r.id, r])));
          setAnns(Object.fromEntries((m.announcements as Announcement[]).map((a) => [a.id, a])));
          setExits(Object.fromEntries((m.exit_checks as ExitCheck[]).map((c) => [c.id, c])));
          break;
        case 'passenger':
          setPax((o) => ({ ...o, [m.passenger.seat]: m.passenger }));
          break;
        case 'request':
          setReqs((o) => ({ ...o, [m.request.id]: m.request }));
          if (m.new && m.request.urgency === 3 && soundRef.current) beep(audio.current);
          break;
        case 'announcement':
          setAnns((o) => ({ ...o, [m.announcement.id]: m.announcement }));
          break;
        case 'exit':
          setExits((o) => ({ ...o, [m.exit.id]: m.exit }));
          break;
      }
    }, setConn);
    sock.current = s;
    return () => s.close();
  }, []);

  const send = useCallback((m: object) => sock.current?.send(m), []);

  const all = useMemo(() => Object.values(reqs), [reqs]);
  const open = useMemo(
    () => all.filter((r) => ['new', 'seen', 'replied'].includes(r.status))
      .sort((a, b) => b.urgency - a.urgency || a.created - b.created),
    [all],
  );
  const urgent = open.filter((r) => r.urgency === 3 && r.status !== 'replied');
  const shown = filter === 'open' ? open : [...all].sort((a, b) => b.created - a.created);
  const unconfirmed = Object.values(anns).reduce(
    (n, a) => n + Object.values(a.acks).filter((x) => x.state === 'sent').length, 0);
  const waitingUnderstood = open.filter((r) => r.replies.length && !r.understood_at).length;

  if (!cat) {
    return <main className="boot"><Bridge size={140} color="#fff" /><p>HASHI Crew · 読み込み中 Loading…</p></main>;
  }

  const requestsPane = (
    <section className="requests-pane" aria-label="Requests">
      {urgent.length > 0 && (
        <div className="urgent-banner" role="alert">
          {urgent.map((r) => {
            const i = cat.intents.find((x) => x.id === r.intent);
            return (
              <div key={r.id} className="urgent-row">
                <Icon name="Siren" size={30} />
                <strong className="useat">{r.seat}</strong>
                <span lang="ja" className="ja">{URGENCY[3].ja}: {i?.labels.ja}</span>
                {speaks.includes(r.lang) && <span className="chip green"><Icon name="Languages" size={14} /> あなたの言語 Your language</span>}
                <span className="en">{i?.labels.en}</span>
                {r.status === 'new' && (
                  <button className="btn" onClick={() => send({ t: 'seen', req_id: r.id })}>向かいます · On my way</button>
                )}
              </div>
            );
          })}
        </div>
      )}
      <div className="pane-head">
        <h2>依頼 <small>Requests</small></h2>
        <div className="seg">
          <button className={filter === 'open' ? 'on' : ''} onClick={() => setFilter('open')}>対応中 Open ({open.length})</button>
          <button className={filter === 'all' ? 'on' : ''} onClick={() => setFilter('all')}>すべて All</button>
        </div>
      </div>
      {shown.length === 0 ? (
        <div className="empty">
          <Bridge size={150} color="var(--muted)" />
          <p>依頼はありません。 No requests right now.</p>
          <small>橋 · पुल · ਪੁਲ</small>
        </div>
      ) : (
        shown.map((r) => <RequestCard key={r.id} req={r} cat={cat} pax={pax[r.seat]} send={send} speaks={speaks.includes(r.lang)} />)
      )}
    </section>
  );

  const sidePane = (
    <section className="side-pane">
      {tab === 'seats' && <SeatMap pax={pax} reqs={all} anns={Object.values(anns)} cat={cat} selected={selected} onSelect={setSelected} />}
      {tab === 'announce' && <AnnouncePanel cat={cat} anns={Object.values(anns).sort((a, b) => a.created - b.created)} send={send} />}
      {tab === 'exit' && <ExitRowPanel pax={pax} checks={Object.values(exits).sort((a, b) => a.created - b.created)} send={send} />}
      {tab === 'greet' && <GreetingPanel cat={cat} />}
    </section>
  );

  const tabs: [Tab, string, string, string][] = [
    ['requests', 'ListChecks', '依頼', 'Requests'],
    ['seats', 'UsersRound', '座席', 'Seats'],
    ['announce', 'Megaphone', 'アナウンス', 'Announce'],
    ['exit', 'DoorOpen', '非常口', 'Exit row'],
    ['greet', 'Languages', '挨拶', 'Greet'],
  ];

  return (
    <div className="crew">
      <header className="bar">
        <span className="logo"><Bridge size={40} color="#fff" /> HASHI</span>
        <span className="zone">乗務員画面 Crew view · Zone B <span className={`live ${conn}`}>
          <Icon name={conn === 'online' ? 'Wifi' : 'WifiOff'} size={14} /> {conn === 'online' ? 'Live' : '再接続中 Reconnecting'}</span></span>
        <span className="stats">
          <span className="stat"><Icon name="Clock" size={16} /> {open.length} <small>依頼 open</small></span>
          <span className={`stat ${urgent.length ? 'alert' : ''}`}><Icon name="TriangleAlert" size={16} /> {urgent.length} <small>緊急 urgent</small></span>
          <span className="stat"><Icon name="BadgeCheck" size={16} /> {waitingUnderstood} <small>理解待ち</small></span>
          <span className="stat"><Icon name="Megaphone" size={16} /> {unconfirmed} <small>未確認</small></span>
        </span>
        <span className="speaks" role="group" aria-label="Languages I speak">
          <small>話せる言語 I speak</small>
          {(['pa', 'hi'] as const).map((l) => (
            <button key={l} className="hbtn sm" aria-pressed={speaks.includes(l)} onClick={() => toggleSpeak(l)}>
              {LANG_LABEL[l].ja}
            </button>
          ))}
        </span>
        <button className="hbtn" aria-pressed={sound} onClick={() => {
          if (!audio.current) audio.current = new AudioContext();
          setSound(!sound);
          if (!sound) beep(audio.current);
        }}><Icon name={sound ? 'Bell' : 'BellOff'} size={18} /> {sound ? '音 On' : '音 Off'}</button>
        <button className="hbtn" onClick={() => setShowQr(true)}><Icon name="QrCode" size={18} /> QR</button>
        <button className="hbtn" onClick={() => {
          if (window.confirm('着陸しました。全データを削除します。\nLanded: delete all flight data?')) {
            fetch('/api/landing', { method: 'POST' }).catch(() => undefined);
          }
        }}><Icon name="PlaneLanding" size={18} /> 着陸 Landed</button>
      </header>

      <nav className="tabs" aria-label="Sections">
        {tabs.filter(([id]) => !(wide && id === 'requests')).map(([id, icon, ja, en]) => (
          <button key={id} className={tab === id ? 'on' : ''} onClick={() => setTab(id)} aria-pressed={tab === id}>
            <Icon name={icon} size={20} /> <span lang="ja">{ja}</span> <small>{en}</small>
            {id === 'requests' && urgent.length > 0 && <span className="dot" aria-label="urgent" />}
          </button>
        ))}
      </nav>

      <div className={`cols ${wide ? 'wide' : ''}`}>
        {(wide || tab === 'requests') && requestsPane}
        {(wide ? true : tab !== 'requests') && sidePane}
      </div>

      {showQr && <QrModal onClose={() => setShowQr(false)} />}
    </div>
  );
}

function QrModal({ onClose }: { onClose: () => void }) {
  const [info, setInfo] = useState<{ url: string; crew_url: string; others?: string[] } | null>(null);
  useEffect(() => { fetch('/api/join').then((r) => r.json()).then(setInfo).catch(() => undefined); }, []);
  return (
    <div className="modal" role="dialog" aria-label="Passenger QR" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <h2>乗客用QR <small>Passenger QR</small></h2>
        <img src="/api/qr.svg" alt="QR code to open HASHI on a phone" width={260} height={260} />
        <p className="url">{info?.url ?? '…'}</p>
        {info?.others && info.others.length > 0 && (
          <p className="hint">他のアドレス Other addresses: {info.others.join('  ')}</p>
        )}
        <p className="hint">スマホのカメラで読み取る · Scan with the phone camera. Same Wi-Fi as this tablet.</p>
        <button className="btn primary" onClick={onClose}>閉じる · Close</button>
      </div>
    </div>
  );
}
