/* 약지도 — 오프라인에서도 약 정보가 열리도록.

   캐시를 두 개로 나눈다.
   · 껍데기(CACHE)   — index.html·srv.js·아이콘 + 본문(core.json·detail.json). 빌드마다 이름이 바뀌어 옛것을 버린다.
                       본문은 앱이 「?v=판」 주소로 받으므로 같은 판끼리만 맞물린다 — 새 화면 + 옛 본문이 섞이지 않게(5-02).
   · 자료(DATA)      — 나머지 data/*.json (낱알 5,660개·성분 4,766개 등 17 MB).
                       내용이 거의 안 바뀌는데 빌드마다 버리면 어르신 폰이 매번 다시 받는다.
                       그래서 이름을 고정하고, 빌드가 바뀌어도 그대로 둔다. 앱은 이것도 「?v=판」으로 받아(5-02)
                       판이 같으면 캐시 그대로, 판이 바뀌면 새로 받아 넣고 옛 판은 지운다(prune).
   판 없는 옛 주소는 «캐시 먼저» — 한 번 받은 것은 즉시 열리고, 뒤에서 조용히 새로 받아 둔다.
   인터넷이 안 되면 어느 캐시에든 있는 사본을 준다(5-01 — 첫 방문 뒤 비행기 모드에서 본문이 안 뜨던 것). */
const CACHE = 'yakjido-2026-10-23T00:07-58baeb79';
const DATA = 'yakjido-data-v1';
/* 본문(core·detail)은 여기서 받지 않는다 — 첫 방문에 페이지가 이미 받은 것을 한 번 더 받던 것(5-03). 페이지가 워커에 연결되면 같은 주소로 다시 불러 캐시에 넣는다. */
/* terms.html·privacy.html — 첫 동의 화면과 설정의 「약관·개인정보」가 앱 안에서 읽는다(비행기 모드에서도 열리게, 10-14) */
const ASSETS = ['./', './index.html', './manifest.webmanifest', './srv.js', './find.js', './terms.html', './privacy.html', './icon-192.png', './icon-512.png', './icon-180.png', './icon-maskable-512.png'];

self.addEventListener('install', (e) => {
  /* HTTP 캐시를 건너뛰고 서버에서 새로 — 몇 시간 묵은 srv.js 가 새 캐시 이름에 갇히지 않게(5-03) */
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS.map((u) => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    /* 자료 캐시는 남긴다 — 이것까지 지우면 17 MB 를 다시 받게 된다.
       같은 주소(github.io)를 쓰는 다른 앱의 캐시는 건드리지 않는다 — 「yakjido-」로 시작하는 약지도 것만 지운다(2026-10-14 외부 검수 2차 #23) */
    .then((keys) => Promise.all(keys.filter((k) => k.startsWith('yakjido-') && k !== CACHE && k !== DATA).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

/* 자료 캐시는 이름이 고정이라, 새 판을 넣으면 같은 파일의 다른 판(옛 ?v=·꼬리 없는 옛 주소)을 지운다 — 17 MB 가 판마다 쌓이지 않게.
   인터넷이 없을 때 쓸 사본은 방금 넣은 새 판이 맡는다 */
const prune = (c, url) => c.keys().then((ks) => Promise.all(ks.filter((r) => { const u = new URL(r.url); return u.pathname === url.pathname && u.search !== url.search; }).map((r) => c.delete(r)))).catch(() => {});
/* 어느 캐시에든 있으면 — 주소 꼬리(?v=)가 달라도 같은 파일이면 준다(인터넷이 없을 때만) */
const anyCache = (req) => caches.match(req, { ignoreSearch: true });
/* 네트워크를 기다리되, 8초 안에 응답이 시작되지 않으면 캐시에 있는 사본을 먼저 준다(신호는 잡히는데 데이터가 안 흐르는 곳). 캐시에도 없으면 계속 기다린다. */
function netOrCache(req, net) {
  return new Promise((resolve) => {
    let done = false; const fin = (r) => { if (!done && r) { done = true; resolve(r); } };
    net.then(fin, () => anyCache(req).then((x) => { if (!done) { done = true; resolve(x || Response.error()); } }));
    setTimeout(() => { anyCache(req).then(fin); }, 8000);
  });
}

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;     // 폰트·날씨 같은 바깥 것은 건드리지 않는다

  if (url.pathname.includes('/data/')) {
    const core = /\/data\/(core|detail)\.json$/.test(url.pathname);
    /* 앱은 모든 자료를 「?v=판」 주소로 받는다(5-02). 판이 박힌 주소는 내용이 바뀌지 않으니 캐시에 있으면 그것이 곧 정답 */
    const ver = url.searchParams.has('v');
    e.respondWith(caches.open(core ? CACHE : DATA).then((c) => c.match(e.request).then((hit) => {
      if (hit && (core || ver)) return hit;
      const net = fetch(e.request).then((res) => {
        if (res && res.ok) { c.put(e.request, res.clone()).then(() => { if (!core) prune(c, url); }).catch(() => {}); }
        return res;
      });
      /* 판 없는 옛 주소 — 캐시 먼저, 뒤에서 갱신 */
      if (hit) { net.catch(() => {}); return hit; }
      return netOrCache(e.request, net);
    })));
    return;
  }
  /* 앱 셸 — 네트워크 우선이되 «2.5초까지만» 기다린다.
     껍데기가 420 KB 라, 신호가 나쁜 곳에서는 캐시에 있는데도 매번 기다리셔야 했다.
     2.5초 안에 안 오면 캐시에 있는 것을 먼저 열어 드리고, 받아 온 새것은 캐시에 넣어
     다음에 여실 때 반영한다. 신호가 좋으면 예전과 똑같이 늘 최신을 받는다.
     화면 이동이 아닌 파일(srv.js·아이콘)은 HTTP 캐시에서 묵은 것을 받지 않게 서버에 한 번 확인한다(no-cache = 바뀌지 않았으면 304). */
  e.respondWith((async () => {
    const req = e.request.mode === 'navigate' ? e.request : new Request(e.request.url, { cache: 'no-cache', credentials: 'same-origin' });
    const net = fetch(req).then((res) => {
      if (res && res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone())).catch(() => {});
      return res;
    });
    const hit = await caches.match(e.request) || await anyCache(e.request);
    if (!hit) return net.catch(() => caches.match('./index.html'));
    const slow = new Promise((r) => setTimeout(() => r(null), 2500));
    const first = await Promise.race([net.catch(() => null), slow]);
    return first || hit;
  })());
});

/* 약 알림 — 안드로이드 크롬은 페이지의 new Notification() 을 막는다(서비스워커로만 띄울 수 있다).
   그래서 알림은 여기서 띄우고, 「먹었어요」를 누르면 앱을 열어 그 복용을 체크한다(2026-09-23).
   체크는 그 알림의 날짜로 적는다(5-16 — 밤 알림을 다음 날 아침에 눌러도 어제 것으로). */
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const d = e.notification.data || {};
  const took = e.action === 'took' && d.key;
  // Z6 — 「10분 뒤 다시」: 서비스워커는 10분을 기다려 주지 않아(브라우저가 몇 분 안에 멈춤) 열린 창에 타이머를 맡긴다. 창이 없으면 그 창을 열어 맡긴다
  const later = e.action === 'later' && d.key;
  const q = () => encodeURIComponent(d.key) + (d.day ? '&day=' + encodeURIComponent(d.day) : '');
  const hash = took ? '#/schedule?tick=' + q() : later ? '#/schedule?later=' + q() : (d.go === '#/visits' ? '#/visits' : '#/schedule');   // 진료 예약 알림은 예약 화면으로(2026-10-13)
  e.waitUntil((async () => {
    /* 같은 주소의 다른 앱 창이 먼저 잡히던 것 — 이 워커가 맡은 범위(약지도 주소) 안의 창만 고른다. 없으면 약지도를 새로 연다(2026-10-14 외부 검수 2차 #24) */
    const all = (await self.clients.matchAll({ type: 'window', includeUncontrolled: true })).filter((c) => String(c.url || '').startsWith(self.registration.scope));
    for (const c of all) {
      if (later) { try { c.postMessage({ type: 'yakjido-later', key: d.key, day: d.day || '', title: e.notification.title || '', body: e.notification.body || '' }); } catch (x) {} return; }
      if ('focus' in c) { try { c.postMessage({ type: 'yakjido-tick', key: took ? d.key : '', day: d.day || '', go: d.go === '#/visits' ? '/visits' : '' }); } catch (x) {} return c.focus(); }
    }
    return self.clients.openWindow('./' + hash);
  })());
});
