/* 약지도 — 오프라인에서도 약 정보가 열리도록 앱 셸을 캐시한다.
   빌드(tools/build.py)마다 CACHE 이름이 바뀌어 옛 캐시를 버린다. */
const CACHE = 'yakjido-2026-09-08-8802';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-180.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  // 폰트·외부 자원은 그대로 통과, 앱 셸은 네트워크 우선 → 실패 시 캐시
  if (url.origin !== location.origin) return;
  e.respondWith(fetch(e.request).then((res) => {
    const copy = res.clone();
    caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
    return res;
  }).catch(() => caches.match(e.request).then((hit) => hit || caches.match('./index.html'))));
});
