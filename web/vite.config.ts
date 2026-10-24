import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';
import { writeFileSync } from 'node:fs';

/**
 * Writes a service worker next to each app (dist/p/sw.js, dist/crew/sw.js) that lists
 * every built file, so both apps open and keep working with the Wi-Fi gone. The
 * Japanese font slices are only needed on the crew tablet, so the passenger worker
 * skips them.
 */
function serviceWorker(): Plugin {
  return {
    name: 'hashi-sw',
    apply: 'build',
    writeBundle(options, bundle) {
      const outDir = options.dir ?? 'dist';
      const all = Object.keys(bundle);
      const assets = all.filter((f) => !f.endsWith('.html') && !f.endsWith('.map') && !f.endsWith('.woff'));
      for (const app of ['p', 'crew'] as const) {
        const files = assets
          .filter((f) => app === 'crew' || !/noto-sans-jp/.test(f))
          .map((f) => `/${f}`);
        const pages = [`/${app}/`, `/${app}/index.html`, `/${app}/manifest.webmanifest`];
        const body = `// Generated at build time.
const VERSION = ${JSON.stringify(Date.now().toString(36))};
const CACHE = 'hashi-${app}-' + VERSION;
const MEDIA = 'hashi-media';
const PRECACHE = ${JSON.stringify([...pages, ...files])};

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await Promise.allSettled(PRECACHE.map((u) => cache.add(u)));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keep = [CACHE, MEDIA];
    for (const k of await caches.keys()) {
      if (k.startsWith('hashi-${app}-') && !keep.includes(k)) await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname === '/api/catalog') {
    e.respondWith(networkFirst(req, MEDIA));
  } else if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
    return;
  } else if (url.pathname.startsWith('/audio/')) {
    e.respondWith(cacheFirst(req, MEDIA));
  } else if (req.mode === 'navigate') {
    e.respondWith(networkFirst(req, CACHE, '/${app}/'));
  } else {
    e.respondWith(cacheFirst(req, CACHE));
  }
});

async function cacheFirst(req, name) {
  const cache = await caches.open(name);
  const hit = await cache.match(req);
  if (hit) return hit;
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (err) {
    return new Response('', { status: 504 });
  }
}

async function networkFirst(req, name, fallbackUrl) {
  const cache = await caches.open(name);
  try {
    const res = await fetch(req, { cache: 'no-store' });
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (err) {
    return (await cache.match(req, { ignoreSearch: true })) ||
      (fallbackUrl && (await cache.match(fallbackUrl))) ||
      new Response('Offline', { status: 503 });
  }
}
`;
        writeFileSync(resolve(outDir, app, 'sw.js'), body);
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), serviceWorker()],
  build: {
    rollupOptions: {
      input: {
        p: resolve(__dirname, 'p/index.html'),
        crew: resolve(__dirname, 'crew/index.html'),
        live: resolve(__dirname, 'live/index.html'),
      },
    },
    chunkSizeWarningLimit: 900,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/audio': 'http://127.0.0.1:8000',
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true },
    },
  },
});
