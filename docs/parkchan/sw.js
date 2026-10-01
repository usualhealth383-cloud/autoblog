/* 오늘 분량을 미리 받아 둔다 — 지하 강의실이나 지하철에서도 열리도록.
   앱을 새로 배포하면 CACHE 이름을 바꿔 옛 캐시를 버린다.

   원칙
   1. 우리 주소(같은 출처)의 GET 과 웹 글꼴만 다룬다. 학원 서버(Supabase) 호출은 손대지 않는다.
      — 예전에는 모든 GET 을 가로채 API 응답까지 캐시에 넣었다. 진도·출석·커뮤니티 글 같은
        개인 정보가 브라우저 캐시에 남고, 로그아웃해도 지워지지 않았다.
   2. 앱 화면(navigate)은 한 벌(./index.html)로만 둔다. 주소 뒤 ?… 가 달라도 같은 앱이다
      — 예전엔 주소마다 3MB 사본이 쌓였고, 보호자 동의 링크(consent.html?t=…)의 토큰까지 캐시에 남았다(2026-10-01 점검).
   3. 네트워크를 먼저 보되 3.5초 안에 안 오면 저장본으로 연다(약한 망에서 한참 기다리지 않게). 받아 오면 저장본을 새로 바꾼다.
   4. 보호자 동의 페이지는 저장하지 않는다(늘 새로, 토큰을 남기지 않게).
   5. 문제 은행·탐구·그림 파일(more-지문.json)은 설치할 때 미리 받는다. 이름에 지문이 있어 판이 바뀌면 새 이름이 된다.
   6. 웹 글꼴(Google Fonts)은 따로 오래 두는 캐시에 — 오프라인에서도 제 글꼴로 보이게. 판이 바뀌어도 지우지 않는다. */
// CACHE·DATA 두 줄은 app/build.py 가 빌드할 때마다 고쳐 쓴다(앱 내용 지문) — 손으로 올리지 않아도 새 판이 옛 캐시에 가리지 않는다.
const CACHE = 'pcs-2b8d8e9f84';
const DATA = './more-dc3ea5093d.json';   // 문제 은행·자료 탐구·그림 — 앱이 첫 화면 뒤에 받는 파일. 미리 받아 두어 오프라인에서도 열리게
const FONTS = 'pcs-fonts-v1';
const ASSETS = ['./index.html', DATA, './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-180.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE && k !== FONTS).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const keepable = (res) => res && res.ok && (res.type === 'basic' || res.type === 'cors');
const within = (p, ms) => new Promise((ok, no) => { const t = setTimeout(() => no(new Error('slow')), ms); p.then((v) => { clearTimeout(t); ok(v); }, (e) => { clearTimeout(t); no(e); }); });

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch { return; }

  // 웹 글꼴: 캐시 먼저, 없으면 받아서 넣는다
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(caches.open(FONTS).then((c) => c.match(req).then((hit) => hit || fetch(req).then((res) => { if (keepable(res)) c.put(req, res.clone()).catch(() => {}); return res; }))));
    return;
  }
  if (url.origin !== self.location.origin) return;   // 학원 서버는 그대로 통과

  if (req.mode === 'navigate') {
    if (/consent\.html$/.test(url.pathname)) return;   // 동의 페이지: 저장하지 않는다
    const isApp = /\/(index\.html)?$/.test(url.pathname);
    if (!isApp) {   // 약관·처리방침 같은 정적 페이지
      e.respondWith(fetch(req).then((res) => { if (keepable(res)) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(url.pathname, copy)).catch(() => {}); } return res; })
        .catch(() => caches.match(url.pathname).then((hit) => hit || caches.match('./index.html'))));
      return;
    }
    const net = fetch(req).then((res) => { if (keepable(res)) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put('./index.html', copy)).catch(() => {}); } return res; });
    e.respondWith(within(net, 3500).catch(() => caches.match('./index.html').then((hit) => hit || net)));
    return;
  }

  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then((hit) => hit || fetch(req).then((res) => {
      if (keepable(res)) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); }
      return res;
    }))
  );
});
