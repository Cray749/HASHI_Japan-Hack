import type { Catalog } from './types';

const CATALOG_KEY = 'hashi.catalog.v1';

/** Catalogue of requests, replies and announcements. Cached so the app opens offline. */
export async function loadCatalog(): Promise<Catalog> {
  try {
    const res = await fetch('/api/catalog', { cache: 'no-cache' });
    if (!res.ok) throw new Error(String(res.status));
    const data = (await res.json()) as Catalog;
    try {
      localStorage.setItem(CATALOG_KEY, JSON.stringify(data));
    } catch {
      /* storage can be blocked; the network copy still works */
    }
    return data;
  } catch (err) {
    try {
      const cached = localStorage.getItem(CATALOG_KEY);
      if (cached) return JSON.parse(cached) as Catalog;
    } catch {
      /* fall through */
    }
    throw err;
  }
}

export type SocketStatus = 'connecting' | 'online' | 'offline';

/**
 * WebSocket that reconnects by itself (cabin Wi-Fi blips). Messages sent while offline
 * wait in a small queue and go out when the link returns. A ping every 10 s detects
 * half-open links that the browser does not report.
 */
export class LiveSocket {
  private ws: WebSocket | null = null;
  private queue: string[] = [];
  private closed = false;
  private retry = 0;
  private lastSeen = 0;
  private timer: number | undefined;
  private beat: number | undefined;
  status: SocketStatus = 'connecting';

  constructor(
    private path: string,
    private onMessage: (msg: any) => void,
    private onStatus: (s: SocketStatus) => void,
    private onOpen?: () => void,
  ) {
    this.connect();
    this.beat = window.setInterval(() => this.heartbeat(), 10000);
    window.addEventListener('online', this.nudge);
    document.addEventListener('visibilitychange', this.nudge);
  }

  private nudge = () => {
    if (!this.closed && this.status !== 'online') {
      window.clearTimeout(this.timer);
      this.connect();
    }
  };

  private setStatus(s: SocketStatus) {
    if (this.status !== s) {
      this.status = s;
      this.onStatus(s);
    }
  }

  private connect() {
    if (this.closed) return;
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    let ws: WebSocket;
    try {
      ws = new WebSocket(`${proto}://${location.host}${this.path}`);
    } catch {
      this.scheduleRetry();
      return;
    }
    this.ws = ws;
    this.setStatus(this.retry === 0 ? 'connecting' : 'offline');
    ws.onopen = () => {
      this.retry = 0;
      this.lastSeen = Date.now();
      this.setStatus('online');
      this.onOpen?.();
      const pending = this.queue;
      this.queue = [];
      pending.forEach((m) => ws.send(m));
    };
    ws.onmessage = (ev) => {
      this.lastSeen = Date.now();
      try {
        this.onMessage(JSON.parse(ev.data));
      } catch {
        /* ignore malformed frames */
      }
    };
    ws.onclose = () => {
      if (this.ws === ws) this.scheduleRetry();
    };
    ws.onerror = () => ws.close();
  }

  private scheduleRetry() {
    if (this.closed) return;
    this.setStatus('offline');
    this.retry += 1;
    const wait = Math.min(3000, 400 * this.retry);
    window.clearTimeout(this.timer);
    this.timer = window.setTimeout(() => this.connect(), wait);
  }

  private heartbeat() {
    if (this.status !== 'online' || !this.ws) return;
    if (Date.now() - this.lastSeen > 25000) {
      this.ws.close();
      return;
    }
    this.ws.send(JSON.stringify({ t: 'ping' }));
  }

  send(msg: object) {
    const text = JSON.stringify(msg);
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(text);
    } else {
      this.queue.push(text);
      if (this.queue.length > 50) this.queue.shift();
    }
  }

  close() {
    this.closed = true;
    window.clearInterval(this.beat);
    window.clearTimeout(this.timer);
    window.removeEventListener('online', this.nudge);
    document.removeEventListener('visibilitychange', this.nudge);
    this.ws?.close();
  }
}
