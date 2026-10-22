import type { ExitState, PaxLang } from '../shared/types';

/** Crew-facing words: Japanese first, English subtitle. */
export const URGENCY = {
  3: { ja: '緊急', en: 'URGENT', icon: 'TriangleAlert', cls: 'vermilion' },
  2: { ja: '要対応', en: 'Needs attention', icon: 'Bell', cls: 'saffron' },
  1: { ja: '通常', en: 'Routine', icon: 'Clock', cls: 'sky' },
} as const;

export const LANG_LABEL: Record<PaxLang, { ja: string; en: string }> = {
  pa: { ja: 'パンジャブ語', en: 'Punjabi' },
  hi: { ja: 'ヒンディー語', en: 'Hindi' },
  en: { ja: '英語', en: 'English' },
};

export const NEED_LABEL: Record<string, { ja: string; en: string; icon: string }> = {
  veg: { ja: 'ベジタリアン', en: 'Vegetarian', icon: 'Salad' },
  hearing: { ja: '耳が不自由', en: 'Hard of hearing', icon: 'EarOff' },
  mobility: { ja: '歩行支援', en: 'Needs walking help', icon: 'Accessibility' },
};

export const STATUS_LABEL = {
  new: { ja: '新着', en: 'New' },
  seen: { ja: '対応中', en: 'On the way' },
  replied: { ja: '返信済み', en: 'Replied' },
  done: { ja: '完了', en: 'Done' },
  cancelled: { ja: '取消', en: 'Cancelled' },
} as const;

export const EXIT_LABEL: Record<ExitState, { ja: string; en: string; icon: string; cls: string }> = {
  waiting: { ja: '回答待ち', en: 'Waiting', icon: 'Clock', cls: 'saffron' },
  passed: { ja: '確認済み', en: 'Understood', icon: 'BadgeCheck', cls: 'green' },
  retry: { ja: '要再確認', en: 'Check in person', icon: 'TriangleAlert', cls: 'vermilion' },
  unwilling: { ja: '協力不可', en: 'Not willing', icon: 'X', cls: 'vermilion' },
  reseat: { ja: '席替え', en: 'Reseat', icon: 'ArrowLeftRight', cls: 'sky' },
};
