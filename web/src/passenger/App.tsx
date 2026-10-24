import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Announcement, Catalog, Checkin, ExitCheck, Intent, MatchResult, Request } from '../shared/types';
import { LiveSocket, loadCatalog, type SocketStatus } from '../shared/net';
import { Bridge, Icon, SPEECH_LANG, playAudio } from '../shared/ui';
import Onboarding from './Onboarding';
import { MoreScreen, RequestCard, Tile, VoiceButton } from './Home';
import { AnnouncementOverlay, CheckinOverlay, ConfirmOverlay, ExitOverlay, HelpSentOverlay, LandedScreen } from './Overlays';
import { setLanguages, setPackUi, t } from './i18n';
import { loadProfile, saveProfile, wipeProfile, type Profile } from './profile';

export default function App() {
  const [cat, setCat] = useState<Catalog | null>(null);
  const [loadErr, setLoadErr] = useState(false);
  const [p, setP] = useState<Profile>(loadProfile);
  const [conn, setConn] = useState<SocketStatus>('connecting');
  const [reqs, setReqs] = useState<Record<string, Request>>({});
  const [anns, setAnns] = useState<Announcement[]>([]);
  const [exit, setExit] = useState<ExitCheck | null>(null);
  const [checkin, setCheckin] = useState<Checkin | null>(null);
  const [screen, setScreen] = useState<'home' | 'more'>('home');
  const [voiceResult, setVoiceResult] = useState<MatchResult | null>(null);
  const [notice, setNotice] = useState('');
  const [helpReq, setHelpReq] = useState<string | null>(null);
  const [landed, setLanded] = useState(false);
  const sock = useRef<LiveSocket | null>(null);
  const profileRef = useRef(p);
  profileRef.current = p;
  const lastAudioReq = useRef<string>('');

  useEffect(() => {
    let alive = true;
    const attempt = () =>
      loadCatalog().then((c) => { if (!alive) return; setPackUi(c.ui); setLanguages(c.languages ?? []); setCat(c); }).catch(() => {
        if (!alive) return;
        setLoadErr(true);
        window.setTimeout(attempt, 2000);
      });
    void attempt();
    return () => { alive = false; };
  }, []);

  const lang = p.lang;
  const ready = p.onboarded && cat;

  // One socket for the whole session once the passenger has finished onboarding.
  useEffect(() => {
    if (!p.onboarded) return;
    const hello = () => {
      const q = profileRef.current;
      sock.current?.send({ t: 'hello', lang: q.lang, senior: q.senior, first_time: q.firstTime,
        pictures_first: q.picturesFirst, needs: q.needs });
    };
    const s = new LiveSocket(
      `/ws/passenger?seat=${encodeURIComponent(p.seat)}`,
      (m) => {
        switch (m.t) {
          case 'welcome':
            setReqs(Object.fromEntries((m.requests as Request[]).map((r) => [r.id, r])));
            setAnns(m.announcements);
            setExit(m.exit_check);
            setCheckin(m.checkin ?? null);
            break;
          case 'checkin':
            setCheckin(m.checkin);
            break;
          case 'checkin_done':
            setCheckin(null);
            break;
          case 'request':
            setReqs((old) => ({ ...old, [m.request.id]: m.request }));
            break;
          case 'announce':
            setAnns((old) => (old.some((a) => a.id === m.announcement.id) ? old : [...old, m.announcement]));
            break;
          case 'exit_check':
            setExit(m.check);
            break;
          case 'exit_done':
            window.setTimeout(() => setExit(null), 2500);
            break;
          case 'landed':
            wipeProfile();
            setLanded(true);
            s.close();
            break;
        }
      },
      setConn,
      hello,
    );
    sock.current = s;
    return () => { s.close(); sock.current = null; };
  }, [p.onboarded, p.seat]); // eslint-disable-line react-hooks/exhaustive-deps

  // Keep the server's copy of the profile current when it changes.
  useEffect(() => {
    if (!p.onboarded) return;
    saveProfile(p);
    sock.current?.send({ t: 'profile', lang: p.lang, senior: p.senior, first_time: p.firstTime,
      pictures_first: p.picturesFirst, needs: p.needs });
  }, [p.lang, p.senior, p.firstTime, p.picturesFirst, p.needs, p.onboarded]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    document.documentElement.style.setProperty('--fs', p.senior ? '20px' : '16px');
    document.documentElement.lang = p.lang;
  }, [p.senior, p.lang]);

  // Play the reply audio once when a new reply arrives.
  useEffect(() => {
    if (!cat) return;
    for (const r of Object.values(reqs)) {
      const last = r.replies[r.replies.length - 1];
      if (!last) continue;
      const key = `${r.id}:${last.at}`;
      if (key === lastAudioReq.current) continue;
      lastAudioReq.current = key;
      const reply = cat.replies.find((x) => x.id === last.reply);
      if (reply) playAudio(`/audio/reply_${reply.id}_${lang}.mp3`, reply.text[lang] ?? reply.text.en, SPEECH_LANG[lang]);
    }
  }, [reqs, cat, lang]);

  const sendIntent = useCallback((i: Intent, via: 'tap' | 'voice' = 'tap', confidence?: number) => {
    sock.current?.send({ t: 'request', intent: i.id, via, confidence });
    setScreen('home');
    setVoiceResult(null);
    if (i.urgency === 3) setHelpReq(i.id);
    if ('vibrate' in navigator) navigator.vibrate?.(40);
  }, []);

  const onVoice = useCallback((r: MatchResult) => {
    if (!cat) return;
    const top = r.candidates?.[0];
    const intent = top && cat.intents.find((x) => x.id === top.intent);
    if (r.mode === 'send' && intent) sendIntent(intent, 'voice', top.score);
    else if (r.mode === 'confirm' && r.candidates.length) setVoiceResult(r);
    else setNotice(t(lang, 'tapPicture'));
  }, [cat, lang, sendIntent]);

  const open = useMemo(
    () => Object.values(reqs).filter((r) => r.status === 'new' || r.status === 'seen' || r.status === 'replied')
      .filter((r) => !(r.understood_at && Date.now() / 1000 - r.understood_at > 25))
      .sort((a, b) => b.urgency - a.urgency || b.created - a.created),
    [reqs],
  );

  if (landed) return <LandedScreen lang={lang} />;
  if (!cat) {
    return (
      <main className="onb splash">
        <Bridge size={150} color="var(--navy)" />
        <p className="tag">{loadErr ? 'Connecting to the cabin network…' : 'HASHI'}</p>
      </main>
    );
  }
  if (!ready) {
    return <Onboarding initial={p} languages={cat.languages} onDone={(np) => setP({ ...np, onboarded: true })} />;
  }

  const tiles = cat.intents.filter((i) => i.tile && i.id !== 'help');
  const help = cat.intents.find((i) => i.id === 'help')!;
  const firstAnn = anns[0];
  const voiceAllowed = cat.languages?.find((l) => l.code === lang)?.voice ?? false;
  const voiceBtn = <VoiceButton p={p} disabled={conn !== 'online'} voiceAllowed={voiceAllowed} onResult={onVoice} onProblem={setNotice} />;

  return (
    <div className={`app ${p.senior ? 'senior' : ''}`}>
      <header className="top">
        <span className="logo"><Bridge size={34} color="#fff" /> HASHI</span>
        <span className="seat-chip">{p.seat}</span>
        <label className="lang-btn">
          <Icon name="Languages" size={20} />
          <select aria-label="Language" value={lang} onChange={(e) => setP({ ...p, lang: e.target.value })}>
            {cat.languages.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
          </select>
        </label>
      </header>

      {conn !== 'online' && (
        <div className="banner warn" role="status" lang={lang}>
          <Icon name="WifiOff" /> <span>{t(lang, 'offline')} {t(lang, 'offlineHelp')}</span>
        </div>
      )}
      {notice && (
        <div className="banner warn" role="status" lang={lang} onClick={() => setNotice('')}>
          <Icon name="Info" /> <span>{notice}</span>
        </div>
      )}

      {screen === 'more' ? (
        <MoreScreen cat={cat} p={p} onPick={(i) => sendIntent(i)} onBack={() => setScreen('home')} />
      ) : (
        <main className="home" lang={lang}>
          {open.length > 0 && (
            <div className="reqs">
              {open.map((r) => (
                <RequestCard key={r.id} req={r} cat={cat} p={p}
                  onUnderstood={(id) => sock.current?.send({ t: 'understood', req_id: id })}
                  onCancel={(id) => sock.current?.send({ t: 'cancel', req_id: id })} />
              ))}
            </div>
          )}
          <h1 className="ask">{t(lang, 'askWhat')}</h1>
          {!p.picturesFirst && voiceBtn}
          <div className="grid">
            {tiles.map((i) => <Tile key={i.id} intent={i} lang={lang} senior={p.senior} onPick={(x) => sendIntent(x)} />)}
            <button className={`tile tint-grey ${p.senior ? 'senior' : ''}`} onClick={() => setScreen('more')}>
              <Icon name="Plus" size={p.senior ? 60 : 44} />
              <span className="tile-native">{t(lang, 'more')}</span>
              {lang !== 'en' && <span className="tile-en">More</span>}
            </button>
          </div>
          {p.picturesFirst && voiceBtn}
        </main>
      )}

      <button className="help-bar" onClick={() => sendIntent(help)} lang={lang}>
        <Icon name="TriangleAlert" size={34} />
        <span>{t(lang, 'helpBig')}</span>
      </button>

      {voiceResult && (
        <ConfirmOverlay result={voiceResult} cat={cat} lang={lang} senior={p.senior}
          onPick={(i, c) => sendIntent(i, 'voice', c)} onClose={() => { setVoiceResult(null); setNotice(t(lang, 'tapPicture')); }} />
      )}
      {helpReq && (
        <HelpSentOverlay lang={lang} onClose={() => setHelpReq(null)}
          onCancel={() => {
            const r = Object.values(reqs).find((x) => x.intent === helpReq && x.status !== 'done');
            if (r) sock.current?.send({ t: 'cancel', req_id: r.id });
            setHelpReq(null);
          }} />
      )}
      {exit && !firstAnn && (
        <ExitOverlay check={exit} p={p} onAnswer={(id, willing, answer) =>
          sock.current?.send({ t: 'exit_answer', check_id: id, willing, answer })} />
      )}
      {checkin && !checkin.answer && !firstAnn && (
        <CheckinOverlay p={p} onAnswer={(a) => {
          sock.current?.send({ t: 'checkin_answer', answer: a });
          setCheckin(null);
        }} />
      )}
      {firstAnn && (
        <AnnouncementOverlay key={firstAnn.id} ann={firstAnn} cat={cat} p={p}
          onAck={(id) => {
            sock.current?.send({ t: 'ack', ann_id: id });
            setAnns((old) => old.filter((a) => a.id !== id));
          }} />
      )}
    </div>
  );
}
