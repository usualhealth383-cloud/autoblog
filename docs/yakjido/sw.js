/* 약지도 — 오프라인에서도 약 정보가 열리도록.

   캐시를 두 개로 나눈다.
   · 껍데기(CACHE)   — index.html·아이콘. 빌드마다 이름이 바뀌어 옛것을 버린다.
   · 자료(DATA)      — data/*.json (낱알 5,660개·성분 4,766개 등 17 MB).
                       내용이 거의 안 바뀌는데 빌드마다 버리면 어르신 폰이 매번 다시 받는다.
                       그래서 이름을 고정하고, 빌드가 바뀌어도 그대로 둔다.
   자료는 «캐시 먼저» — 한 번 받은 것은 즉시 열리고, 뒤에서 조용히 새로 받아 둔다. */
const CACHE = 'yakjido-2026-09-22-896';
const DATA = 'yakjido-data-v1';
const ASSETS = ['./', './index.html', './data/core.json', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-180.png', './icon-maskable-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    /* 자료 캐시는 남긴다 — 이것까지 지우면 17 MB 를 다시 받게 된다 */
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE && k !== DATA).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;     // 폰트·날씨 같은 바깥 것은 건드리지 않는다

  if (url.pathname.includes('/data/')) {          // 자료 — 캐시 먼저, 뒤에서 갱신
    e.respondWith(caches.open(DATA).then((c) => c.match(e.request).then((hit) => {
      const net = fetch(e.request).then((res) => { if (res && res.ok) c.put(e.request, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })));
    return;
  }
  /* 앱 셸 — 네트워크 우선이되 «2.5초까지만» 기다린다.
     껍데기가 420 KB 라, 신호가 나쁜 곳에서는 캐시에 있는데도 매번 기다리셔야 했다.
     2.5초 안에 안 오면 캐시에 있는 것을 먼저 열어 드리고, 받아 온 새것은 캐시에 넣어
     다음에 여실 때 반영한다. 신호가 좋으면 예전과 똑같이 늘 최신을 받는다. */
  e.respondWith((async () => {
    const net = fetch(e.request).then((res) => {
      if (res && res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone())).catch(() => {});
      return res;
    });
    const hit = await caches.match(e.request);
    if (!hit) return net.catch(() => caches.match('./index.html'));
    const slow = new Promise((r) => setTimeout(() => r(null), 2500));
    const first = await Promise.race([net.catch(() => null), slow]);
    return first || hit;
  })());
});
