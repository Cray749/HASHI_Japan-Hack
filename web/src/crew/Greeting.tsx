import { useState } from 'react';
import type { Catalog, GreetingSet } from '../shared/types';
import { Icon, SPEECH_LANG, playAudio } from '../shared/ui';

/** Katakana greeting coach: the crew learn a few words in the passenger's language. */
export function GreetingList({ set, compact = false }: { set: GreetingSet; compact?: boolean }) {
  return (
    <div className={`greetings ${compact ? 'compact' : ''}`}>
      {set.items.map((g) => (
        <div key={g.id} className="greet">
          <div className="greet-main">
            <p className="katakana" lang="ja">{g.katakana}</p>
            <p className="script" lang={set.lang}>{g.script}</p>
            <p className="romaji">{g.romaji}</p>
            <p className="meaning"><span lang="ja">{g.ja}</span> · {g.meaning}</p>
          </div>
          <button className="btn" aria-label={`Listen: ${g.meaning}`}
            onClick={() => playAudio(`/audio/greet_${set.lang}_${g.id}.mp3`, g.script, SPEECH_LANG[set.lang])}>
            <Icon name="Volume2" /> 聞く
          </button>
        </div>
      ))}
    </div>
  );
}

export default function GreetingPanel({ cat }: { cat: Catalog }) {
  const [lang, setLang] = useState<'pa' | 'hi'>('pa');
  const set = cat.greetings.find((g) => g.lang === lang);
  return (
    <div className="panel">
      <h2>挨拶コーチ <small>Greeting coach</small></h2>
      <p className="hint">カタカナを読むだけで、お客様の言葉で挨拶できます。 Read the katakana aloud to greet in the passenger&apos;s language.</p>
      <div className="seg">
        {(['pa', 'hi'] as const).map((l) => (
          <button key={l} className={lang === l ? 'on' : ''} onClick={() => setLang(l)}>
            {l === 'pa' ? 'パンジャブ語 Punjabi' : 'ヒンディー語 Hindi'}
          </button>
        ))}
      </div>
      {set && <GreetingList set={set} />}
    </div>
  );
}
