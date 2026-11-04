/* ═══ 메디나눔 공용 푸시 부품(11-03 · 약지도 세션 설계) — 다섯 앱 「앱을 닫아도 제시간에」 ═══
   옮길 곳: yozm-health _도구/푸시_부품.js (Main 이 옮김) · 서버: mn-push-check(앱별 판정 모듈) · 표: 메디나눔_공용푸시_1103.sql
   하는 일: 알림 허락 → 웹 푸시 구독 → 서버에 저장(mn_push_save: 앱·기기 말·시간대) · 끄기(mn_push_drop) · 상태 · 시험 알림(이 기기에서 바로)
   하지 않는 일: 무엇을 언제 보낼지(서버 모듈 몫) · 화면(앱마다 알림 부품 안에 「앱을 닫아도 제시간에」 한 줄로 넣는다)
   쓰는 법(앱 끝, 계정·알림 부품 뒤):
     푸시.설치({ app: 'kids', vapid: '<공개 열쇠 — 약지도 srv.js FAM_VAPID 와 같은 값>', 준비: function () { return 서버.준비(); },
                 말: function () { return LANG || 'ko'; } });
     푸시.켜기().then(function (r) { r.ok ? … : 알림(r.why) })   // r.why: 'login' | 'nopush' | 'denied' | 'ios' | 'error'
     푸시.끄기() · 푸시.상태() → { 지원, 허락, 구독 } · 푸시.시험('제목', '본문')
   서비스워커: 앱 sw.js 에 아래 「SW 조각」을 넣는다(약지도 sw.js 의 push 처리와 같은 꼴) — data.go 는 '#/…' 만 받는다.
   ⚠ 아이폰은 사파리 → 공유 → 홈 화면에 추가한 아이콘으로 연 앱에서만(iOS 16.4+) — 'ios' 를 돌려주면 그 안내를 보여 주세요. */
(function () {
  if (window.푸시) return;
  var 설정 = { app: '', vapid: '', 준비: null, 말: null };
  function b64u(s) { var p = '='.repeat((4 - s.length % 4) % 4), b = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); var u = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
  function 지원() { return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window; }
  function 아이폰웹() { return /iPhone|iPad|iPod/.test(navigator.userAgent || '') && !(window.navigator.standalone || matchMedia('(display-mode: standalone)').matches); }
  function 시간대() { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Seoul'; } catch (e) { return 'Asia/Seoul'; } }
  function 말() { try { var l = typeof 설정.말 === 'function' ? 설정.말() : 'ko'; return /^(ko|en|es|ja|zh)$/.test(l) ? l : 'ko'; } catch (e) { return 'ko'; } }
  function rpc(fn, args) { return Promise.resolve(설정.준비 && 설정.준비()).then(function (sb) { if (!sb) throw new Error('login'); return sb.rpc(fn, args); }).then(function (r) { if (r && r.error) throw r.error; return r && r.data; }); }
  function 켜기() {
    if (!지원()) return Promise.resolve({ ok: false, why: 아이폰웹() ? 'ios' : 'nopush' });
    return Notification.requestPermission().then(function (p) {
      if (p !== 'granted') return { ok: false, why: 'denied' };
      return navigator.serviceWorker.ready.then(function (reg) { return reg.pushManager.getSubscription().then(function (s) { return s || reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64u(설정.vapid) }); }); })
        .then(function (sub) { var j = sub.toJSON(); return rpc('mn_push_save', { p_app: 설정.app, p_endpoint: j.endpoint, p_p256dh: j.keys.p256dh, p_auth: j.keys.auth, p_lang: 말(), p_tz: 시간대() }); })
        .then(function () { return { ok: true }; });
    }).catch(function (e) { return { ok: false, why: /login/.test(String(e && e.message)) ? 'login' : 'error' }; });
  }
  function 끄기() {
    if (!지원()) return Promise.resolve({ ok: true });
    return navigator.serviceWorker.ready.then(function (reg) { return reg.pushManager.getSubscription(); }).then(function (sub) {
      if (!sub) return { ok: true };
      return rpc('mn_push_drop', { p_endpoint: sub.endpoint }).catch(function () {}).then(function () { return sub.unsubscribe(); }).then(function () { return { ok: true }; });
    }).catch(function () { return { ok: false, why: 'error' }; });
  }
  function 상태() {
    if (!지원()) return Promise.resolve({ 지원: false, 허락: 'unsupported', 구독: false });
    return navigator.serviceWorker.ready.then(function (reg) { return reg.pushManager.getSubscription(); })
      .then(function (s) { return { 지원: true, 허락: Notification.permission, 구독: !!s }; }, function () { return { 지원: true, 허락: Notification.permission, 구독: false }; });
  }
  /* 시험 알림 — 서버를 거치지 않고 이 기기에서 바로(허락·소리·잠금화면 확인용) */
  function 시험(t, b) {
    if (!지원() || Notification.permission !== 'granted') return Promise.resolve(false);
    return navigator.serviceWorker.ready.then(function (reg) { return reg.showNotification(t || '시험 알림', { body: b || '알림이 이렇게 와요.', tag: 'mn-push-test', icon: 'icon-192.png' }); }).then(function () { return true; }, function () { return false; });
  }
  window.푸시 = { 설치: function (o) { for (var k in o) 설정[k] = o[k]; }, 켜기: 켜기, 끄기: 끄기, 상태: 상태, 시험: 시험, 아이폰웹: 아이폰웹 };
})();

/* ── SW 조각(앱 sw.js 에 그대로 붙이기) ──────────────────────────────
self.addEventListener('push', (e) => {
  let m = {}; try { m = e.data ? e.data.json() : {}; } catch (x) {}
  const go = /^#\/[a-z0-9\/?=&_-]*$/i.test(m.go || '') ? m.go : '#/';
  e.waitUntil(self.registration.showNotification(String(m.title || '').slice(0, 60) || '알림', {
    body: String(m.body || '').slice(0, 200), tag: String(m.tag || 'mn-push').slice(0, 80), icon: 'icon-192.png', badge: 'icon-192.png', data: { go } }));
});
// notificationclick: data.go 로 열기(이미 있는 앱 notificationclick 이 있으면 go 만 받아 쓰기)
───────────────────────────────────────────────────────────────────── */
