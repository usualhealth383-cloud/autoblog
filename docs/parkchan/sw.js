/* 오늘 분량을 미리 받아 둔다 — 지하 강의실이나 지하철에서도 열리도록.
   앱을 새로 배포하면 CACHE 이름을 바꿔 옛 캐시를 버린다.

   원칙
   1. 우리 주소(같은 출처)의 GET 만 다룬다. 학원 서버(Supabase) 호출과 폰트는 손대지 않는다.
      — 예전에는 모든 GET 을 가로채 API 응답까지 캐시에 넣었다. 진도·출석·커뮤니티 글 같은
        개인 정보가 브라우저 캐시에 남고, 로그아웃해도 지워지지 않았다.
   2. 화면 이동(navigate)은 네트워크를 먼저 보고 실패하면 캐시로 연다(새 개념 반영).
   3. 그 밖의 자원(아이콘·매니페스트)은 캐시를 먼저 보고 없으면 받아 온다.
   4. 정상 응답(200, 같은 출처)만 캐시에 넣는다. API 실패 자리에 index.html 을 돌려주지 않는다. */
const CACHE = 'pcs-2026-09-09d';
const ASSETS = [
  './', './index.html', './manifest.webmanifest',
  './icon-192.png', './icon-512.png', './icon-180.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const keepable = (res) => res && res.ok && res.type === 'basic';

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch { return; }
  if (url.origin !== self.location.origin) return;   // 학원 서버·폰트는 그대로 통과시킨다

  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then((res) => {
          if (keepable(res)) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); }
          return res;
        })
        .catch(() => caches.match(req).then((hit) => hit || caches.match('./index.html')))
    );
    return;
  }

  e.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      if (keepable(res)) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); }
      return res;
    }))
  );
});
