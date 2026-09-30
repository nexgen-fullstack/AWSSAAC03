// Офлайн-режим: сторінка — спершу з мережі (щоб бачити оновлення), без мережі — з кешу.
const PREFIX = 'saa2-';
const CACHE = PREFIX + 'baa9381f38';
const CORE = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png'];
self.addEventListener('install', e => {
  // кожен файл окремо: якщо одного бракує, офлайн-режим однаково встановиться
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u => c.add(u).catch(() => null))))
    .then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith(PREFIX) && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  // «Глибоке навчання» (deep/) — окремий сайт зі своїм service worker: не кешуємо його тут
  const rel = url.pathname.slice(new URL(self.registration.scope).pathname.length);
  if (rel.startsWith('deep/')) return;
  if (req.mode === 'navigate') {
    if (rel !== '' && rel !== 'index.html') return;
    e.respondWith(fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put('./index.html', copy));
      return res;
    }).catch(() => caches.match('./index.html')));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  })));
});
