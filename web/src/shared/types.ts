export type Lang = 'en' | 'ja' | 'hi' | 'pa';
export type PaxLang = 'hi' | 'pa' | 'en';
export type Texts = Record<Lang, string>;

export interface Intent {
  id: string;
  cat: string;
  urgency: 1 | 2 | 3;
  icon: string;
  tile: boolean;
  labels: Texts;
  replies: string[];
}

export interface Reply {
  id: string;
  icon: string;
  text: Texts;
}

export interface AnnouncementPhrase {
  id: string;
  icon: string;
  kind: 'safety' | 'info';
  text: Texts;
}

export interface GreetingItem {
  id: string;
  script: string;
  katakana: string;
  romaji: string;
  meaning: string;
  ja: string;
}

export interface GreetingSet {
  lang: 'hi' | 'pa';
  name: string;
  items: GreetingItem[];
}

export interface Catalog {
  langs: Lang[];
  intents: Intent[];
  replies: Reply[];
  announcements: AnnouncementPhrase[];
  greetings: GreetingSet[];
}

export interface Passenger {
  seat: string;
  lang: PaxLang;
  senior: boolean;
  first_time: boolean;
  pictures_first: boolean;
  needs: string[];
  online: boolean;
}

export type RequestStatus = 'new' | 'seen' | 'replied' | 'done' | 'cancelled';

export interface Request {
  id: string;
  seat: string;
  intent: string;
  urgency: 1 | 2 | 3;
  via: 'tap' | 'voice';
  confidence: number | null;
  status: RequestStatus;
  created: number;
  seen_at: number | null;
  replies: { reply: string; at: number }[];
  understood_at: number | null;
  done_at: number | null;
  lang: PaxLang;
}

export interface Announcement {
  id: string;
  phrase: string | null;
  custom: string | null;
  kind: 'safety' | 'info';
  icon: string;
  target: { all: boolean; rows: number[]; seats: string[] };
  created: number;
  acks: Record<string, { state: 'sent' | 'understood'; at: number | null }>;
}

export type ExitState = 'waiting' | 'passed' | 'retry' | 'unwilling' | 'reseat';

export interface ExitCheck {
  id: string;
  row: number;
  created: number;
  open: boolean;
  seats: Record<string, { state: ExitState; answer: string | null; at: number | null }>;
}

export interface MatchResult {
  ok?: boolean;
  error?: string;
  heard?: string;
  mode: 'send' | 'confirm' | 'tiles';
  confidence?: number;
  candidates: { intent: string; score: number; phrase: string }[];
  ms?: number;
}
