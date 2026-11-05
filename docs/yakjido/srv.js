/* 약지도 — 계정·기록 이어 두기(메디나눔 공용 서버) + 첫 동의·로그인 문·약관 읽기 화면(2026-10-14). app-shell.html 뒤에 따로 받는 파일(2026-10-13). */
/* ▼▼ 서버 부품 시작 ▼▼ */
/* 약지도 메디나눔 합류 1013 — 길동무.html(yozm-health, 10-13 정본)의 서버 부품 사본. 바꾼 것: 계정 지우기에 p_app · 결과 문구 · 동의 안내 글 · 버튼 색(약지도 색) · 복구 표시 이름 · 라이브러리 SRI(supabase.js) · 가입 때 user_metadata {app, age14_at} · 서버.복구처리 내보내기 */
/* ═══ 계정·기록 동기화·문의 — 네 앱 공용 부품 (Supabase, 2026-09-15) ═══════════════
   원칙: ‘없어도 앱은 그대로’. 인터넷이 없거나 스크립트를 못 받으면 조용히 꺼진다.
   기록은 localStorage 가 정본이고, 서버는 ‘복사본’이다. 열쇠(앱마다 접두사)로 골라 올린다.
   열쇠는 publishable(공개용) — 표마다 RLS 가 본인 것만 열어 준다. service_role 은 앱에 넣지 않는다.
   쓰는 법: 각 앱 끝에서  서버.설치({app:'gyeote', 열쇠:/^gyeote_/, 다시그리기:function(){…}});
   화면: 계정화면HTML() 을 아무 화면에나 넣고, 단추는 계정동작('login'|'signup'|'logout'|'sync'|'ask') 를 부른다. */
(function () {
  /* 길동무 정본에서 쓰던 글 거르기 — 약지도에는 같은 이름의 도우미가 없어 여기 둔다 */
  var 글자안전 = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  /* 2026-10-13 메디나눔 공용 서버(gildongmu 프로젝트 · 서울) — 다섯 앱(소아·길동무·CS·곁에·약지도)이 함께 쓴다. 기록은 app 칸으로 앱마다 나뉜다.
     publishable 키는 앱에 실어도 되는 키다(행 단위 보안이 지킨다). ⛔ service_role 키 · secret 키는 넣지 않는다. 비우면 준비()가 라이브러리를 받지 않는다. */
  var URL = 'https://uszalzczpmyifzbamjno.supabase.co';
  var KEY = 'sb_publishable_YQSz-D-RCXzHGUhso06rMg_GOIIRDuV';
  /* 2026-10-13 상용화 점검 1-23 — 판을 못 박고 무결성(SRI) 값을 단다. CDN 이 바뀐 파일을 주면 브라우저가 실행하지 않는다(로그인 칸만 「잠시 문제」).
     .min.js 는 jsDelivr 가 그때그때 만드는 파일이라 SRI 를 쓰면 안 된다 — npm 묶음에 든 그대로의 supabase.js(110 KB)를 쓴다.
     판을 올릴 때: curl 로 받아 `openssl dgst -sha384 -binary | openssl base64 -A` 값으로 LIB_SRI 를 함께 바꾼다. */
  var LIB = 'vendor/supabase.js';   /* 바깥 파일 0(10-27) — 배포 묶음 안의 supabase-js 2.45.4 */
  var LIB_SRI = 'sha384-0w2KAL2YHP6wKOkUDzkCDGgVvfmHnj02DHeQ6XcHOgTfFsGyonKOpShMH1x6nk9o';
  var 설정 = { app: 'app', 열쇠: /^$/, 다시그리기: null, 준비됨: true };
  var sb = null, 준비중 = null, 세션 = null, 동기화중 = false;
  /* 2026-09-23 검수 #8 — 서버에 표(스키마)가 아직 없으면 앱이 서버.설치({ 준비됨:false }) 로 알린다.
     그동안 계정 칸은 「준비 중」 한 줄뿐 — 가입·로그인·문의 칸과 단추를 보이지 않고, 라이브러리도 받지 않는다(되는 척 금지). */
  function 준비됨() { var r = 설정.준비됨; try { if (typeof r === 'function') r = r(); } catch (e) { r = false; } return r !== false; }
  var 준비중말 = '계정·이어 보기는 준비 중이에요. 지금은 이 휴대폰에서 그대로 쓰실 수 있어요.';
  var 복구모드 = false, 복구중 = false;   /* 2026-09-23 큰문제 #10 — 메일의 복구 링크로 들어와 새 비밀번호를 정하는 중 */
  /* 메일 링크가 돌아올 주소 — 지금 앱 주소. file:// 등 웹 주소가 아니면 넘기지 않는다(Supabase Site URL 로 간다). */
  /* 2026-10-13 상용화 점검 — 설치 앱(https://localhost)·옛 주소(github.io)는 Supabase 돌아올 주소 허용 목록에 없어 메일 링크가 다른 앱 첫 화면으로 갔다.
     허용 목록에 있는 약지도 웹 주소(meta.webUrl = yakjido.medinanum.com)로 돌려보낸다 — 거기서 비밀번호 다시 정하기까지 끝난다. */
  function 앱주소() { try {
    var 웹 = (typeof D !== 'undefined' && D.meta && D.meta.webUrl) || '';
    var 지금 = /^https?:$/.test(location.protocol) ? location.origin + location.pathname : null;
    if (웹 && (!지금 || /localhost|github\.io/.test(location.hostname))) return 웹;
    return 지금; } catch (e) { return null; } }
  function 복구대기() { try { return sessionStorage.getItem('yj_recovery'); } catch (e) { return null; } }
  function 복구처리() {
    if (!준비됨()) return;
    var h = 복구대기(); if (!h || 복구중) return;
    var p = {}; h.split('&').forEach(function (kv) { var i = kv.indexOf('='); if (i > 0) { try { p[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' ')); } catch (e) {} } });
    if (p.error || p.error_code) {
      try { sessionStorage.removeItem('yj_recovery'); } catch (e) {}
      알림('메일의 링크가 만료됐거나 이미 쓰였어요. 비밀번호를 바꾸시려면 「비밀번호를 잊으셨나요?」로 새 링크를 받아 주세요.');
      return;
    }
    if (!p.access_token || !p.refresh_token) { try { sessionStorage.removeItem('yj_recovery'); } catch (e) {} return; }
    if (!서버허용()) { 알림('「서버에 저장하기」에 동의하신 뒤 새 비밀번호를 정할 수 있어요. 로그인 화면이나 내 정보 → 설정 → 계정에서 동의해 주세요.'); return; }
    복구중 = true;
    준비().then(function () { return sb.auth.setSession({ access_token: p.access_token, refresh_token: p.refresh_token }); }).then(function (r) {
      복구중 = false;
      if (r && r.error) throw r.error;
      try { sessionStorage.removeItem('yj_recovery'); } catch (e) {}
      세션 = (r && r.data && r.data.session) || 세션; 복구모드 = true;
      화면갱신();
      try { if (typeof go === 'function') go('/me?t=set'); } catch (e) {}
      알림('새 비밀번호를 정해 주세요.');
    }).catch(function (e) {
      복구중 = false;
      var m = (e && e.message) || '';
      if (/offline|lib|Failed to fetch|NetworkError/i.test(m)) { 알림(말(e)); return; }   /* 연결되면 다시 — 링크는 들고 있는다 */
      try { sessionStorage.removeItem('yj_recovery'); } catch (e2) {}
      알림('메일의 링크가 만료됐거나 이미 쓰였어요. 비밀번호를 바꾸시려면 「비밀번호를 잊으셨나요?」로 새 링크를 받아 주세요.');
    });
  }

  function 상태읽기() { try { return JSON.parse(localStorage.getItem('_srv_' + 설정.app) || '{}') || {}; } catch (e) { return {}; } }
  function 상태쓰기(o) { try { localStorage.setItem('_srv_' + 설정.app, JSON.stringify(o)); } catch (e) {} }
  function 해시(s) { var h = 5381; for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0; return String(h); }
  function 내열쇠() { var out = []; try { for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (설정.열쇠.test(k)) out.push(k); } } catch (e) {} return out; }
  function 온라인() { return typeof navigator === 'undefined' || navigator.onLine !== false; }

  /* 라이브러리는 필요할 때 한 번만 받는다 — 첫 화면을 늦추지 않는다 */
  function 준비() {
    if (sb) return Promise.resolve(sb);
    if (!준비됨() || !URL || !KEY) return Promise.reject(new Error('off'));   /* 길동무 서버 준비 1008 — 꺼짐·주소 빈칸이면 아무것도 받지 않는다 */
    if (준비중) return 준비중;
    준비중 = new Promise(function (res, rej) {
      if (window.supabase && window.supabase.createClient) return res();
      if (!온라인()) return rej(new Error('offline'));
      var s = document.createElement('script'); s.src = LIB; s.async = true; s.integrity = LIB_SRI; s.crossOrigin = 'anonymous'; s.referrerPolicy = 'no-referrer';
      s.onload = function () { res(); }; s.onerror = function () { rej(new Error('lib')); };
      document.head.appendChild(s);
    }).then(function () {
      sb = window.supabase.createClient(URL, KEY, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false } });
      sb.auth.onAuthStateChange(function (ev, s) { 세션 = s; if (ev === 'PASSWORD_RECOVERY') { 복구모드 = true; 화면갱신(); } if (s && (ev === 'SIGNED_IN' || ev === 'INITIAL_SESSION')) { 계정확인(s); 지운것올리기().then(끌어오기).then(function () { 밀어올리기(); }); 구독조회(); if (typeof 설정.로그인됨 === 'function') { try { 설정.로그인됨(sb, s); } catch (e) {} } } });
      return sb.auth.getSession().then(function (r) { 세션 = r && r.data ? r.data.session : null; return sb; });
    }).catch(function (e) { 준비중 = null; throw e; });
    return 준비중;
  }

  /* 서버 → 이 기기. 서버 쪽이 더 새것이면 덮는다(마지막으로 쓴 쪽이 이긴다). */
  /* 2026-09-22 — 두 기기가 같은 열쇠를 각각 고쳤을 때 합친다. 못 합칠 꼴이면 null. */
  function 병합(내것, 서버것) {
    var a, b; try { a = JSON.parse(내것); b = JSON.parse(서버것); } catch (e) { return null; }
    var 때 = function (x) { if (!x || typeof x !== 'object') return 0; return Number(x.t || x.ts || x.at || x.updated || 0) || 0; };
    if (Array.isArray(a) && Array.isArray(b)) {
      var 열쇠 = function (x) { if (x && typeof x === 'object') { if (x.id != null) return 'i' + x.id; if (x.t != null || x.ts != null) return 't' + (x.t != null ? x.t : x.ts); } return 'j' + JSON.stringify(x); };
      var 본 = {}, 합 = [];
      b.concat(a).forEach(function (x) { var k = 열쇠(x); if (본[k]) return; 본[k] = 1; 합.push(x); });
      if (합.length && 합.every(function (x) { return 때(x) > 0; })) 합.sort(function (x, y) { return 때(x) - 때(y); });
      return JSON.stringify(합);
    }
    if (a && b && typeof a === 'object' && typeof b === 'object' && !Array.isArray(a) && !Array.isArray(b)) {
      var 합2 = {}; Object.keys(b).forEach(function (k) { 합2[k] = b[k]; });
      Object.keys(a).forEach(function (k) { if (!(k in 합2)) { 합2[k] = a[k]; return; } var ta = 때(a[k]), tb = 때(합2[k]); 합2[k] = (ta >= tb) ? a[k] : 합2[k]; });
      return JSON.stringify(합2);
    }
    return null;
  }
  /* 2026-09-22 — 같은 폰에 「다른 계정」이 들어오면 앞사람 기록·지울 목록을 새 계정에 올리지 않는다.
     이 앱의 기기 기록과 동기화 상태를 비우고 새 계정 것을 끌어온다. 처음 로그인하는 기기(user 없음)는 그대로 둔다. */
  function 계정확인(s) {
    var 새 = s && s.user && s.user.id; if (!새) return;
    var st = 상태읽기();
    if (st.user && st.user !== 새) {
      try { 내열쇠().forEach(function (k) { localStorage.removeItem(k); }); } catch (e) {}
      상태쓰기({ user: 새 });
      try { 알림('다른 계정으로 들어오셔서, 이 휴대폰에 있던 이전 계정의 기록은 비웠어요.'); } catch (e) {}
      if (typeof 설정.다시그리기 === 'function') { try { 설정.다시그리기(); } catch (e) {} }
      return;
    }
    if (!st.user) { st.user = 새; 상태쓰기(st); }
  }
  function 끌어오기() {
    if (!sb || !세션 || !동기화됨()) return Promise.resolve(0);
    var st = 상태읽기(), 바뀜 = 0;
    return sb.from('records').select('key,value,updated_at').eq('app', 설정.app).then(function (r) {
      if (r.error || !r.data) return 0;
      var 해시들 = st.hashes || {}, 묘비 = st.gone || {}, 싹지운때 = st.wipe || 0;
      r.data.forEach(function (row) {
        var v = row.value && typeof row.value.v === 'string' ? row.value.v : null; if (v === null) return;
        var 지금 = null; try { 지금 = localStorage.getItem(row.key); } catch (e) {}
        var 서버시각 = Date.parse(row.updated_at) || 0, 내시각 = (st.times || {})[row.key] || 0;
        /* 2026-09-22 — 이 기기에서 「지운」 기록을 서버가 되살리고 있었다. 지운 때가 서버 것보다
           새로우면 되살리지 않는다(서버 쪽은 밀어올리기가 곧 지운다). */
        if ((묘비[row.key] || 0) >= 서버시각 || 싹지운때 >= 서버시각) return;
        if (지금 === v) { 해시들[row.key] = 해시(v); return; }
        /* 2026-09-22 — 누가 바뀌었는지는 「마지막으로 맞춘 값의 해시」로 본다.
           서버만 바뀜 → 서버 것. 나만 바뀜 → 내 것(곧 올린다). 둘 다 바뀜 → 합친다(못 합치면 서버 것). */
        var 맞춘 = 해시들[row.key], 내바뀜 = (지금 !== null && 맞춘 != null && 해시(지금) !== 맞춘), 서버바뀜 = (맞춘 == null || 해시(v) !== 맞춘);
        /* 2026-10-13 상용화 점검 — 이 기기에 기록이 있는데 한 번도 맞춘 적이 없으면(처음 로그인) 덮지 않고 합친다. 예전엔 서버 것으로 말없이 덮었다. */
        if (지금 !== null && 맞춘 == null && 지금 !== v) { var 첫합 = (typeof 설정.병합 === 'function' ? 설정.병합(row.key, 지금, v) : 병합(지금, v)); if (첫합 !== null) { try { localStorage.setItem(row.key, 첫합); 해시들[row.key] = 해시(v); 바뀜++; } catch (e) {} return; } }
        if (지금 === null || !내바뀜) { try { localStorage.setItem(row.key, v); 해시들[row.key] = 해시(v); 바뀜++; } catch (e) {} return; }
        if (!서버바뀜) return;   /* 내 것만 바뀜 — 밀어올리기가 올린다 */
        var 합친 = (typeof 설정.병합 === 'function' ? 설정.병합(row.key, 지금, v) : 병합(지금, v));   /* 앱이 자기 기록 모양을 알면 앱이 합친다(약지도 2026-10-13) */
        if (합친 === null) { if (서버시각 > 내시각) { try { localStorage.setItem(row.key, v); 해시들[row.key] = 해시(v); 바뀜++; } catch (e) {} } return; }
        try { localStorage.setItem(row.key, 합친); 해시들[row.key] = 해시(v); 바뀜++; } catch (e) {}   /* 해시는 서버 것 — 합친 값은 곧 올라간다 */
      });
      st.hashes = 해시들; st.last_pull = Date.now(); 상태쓰기(st);
      if (바뀜 && typeof 설정.다시그리기 === 'function') { try { 설정.다시그리기(); } catch (e) {} }
      return 바뀜;
    });
  }
  /* 2026-09-22 — 지운 것을 서버에도 지운다. 「바뀐 열쇠만 올린다」는 열쇠가 「없어진」 것을
     못 본다. 그래서 지울 때 묘비(gone)를 적어 두고, 여기서 서버에서 지운 뒤 묘비를 치운다.
     「모두 지우기」는 wipe 때를 적어 두고 이 앱의 서버 기록을 전부 지운다. */
  /* ⚠️ 묘비(gone)와 싹 지운 때(wipe)는 서버에 반영한 뒤에도 「남긴다」. 지우자마자 치우면,
     오프라인이던 다른 기기가 나중에 옛 복사본을 올렸을 때 이 기기가 그걸 도로 끌어온다.
     「보낼 것」(pending·wipe_pending)만 따로 두고 치운다. 묘비는 90일 지나면 걷는다. */
  function 지운것올리기() {
    if (!sb || !세션 || !온라인()) return Promise.resolve(0);
    var st = 상태읽기(), 보낼 = (st.pending || []).slice(), 일 = Promise.resolve(), 셈 = 0;
    if (st.wipe_pending) {
      일 = 일.then(function () {
        return sb.from('records').delete().eq('user_id', 세션.user.id).eq('app', 설정.app).then(function (r) {
          if (r.error) return;
          var s2 = 상태읽기(); delete s2.wipe_pending; s2.pending = []; s2.hashes = {}; s2.times = {}; 상태쓰기(s2); 셈++;
        });
      });
    }
    if (보낼.length) {
      일 = 일.then(function () {
        var s3 = 상태읽기(), 남은 = (s3.pending || []).slice(); if (!남은.length) return;
        return sb.from('records').delete().eq('user_id', 세션.user.id).eq('app', 설정.app).in('key', 남은).then(function (r) {
          if (r.error) return;
          var s4 = 상태읽기(), h = s4.hashes || {}, t = s4.times || {};
          남은.forEach(function (k) { delete h[k]; delete t[k]; });
          s4.pending = (s4.pending || []).filter(function (k) { return 남은.indexOf(k) < 0; });
          s4.hashes = h; s4.times = t; 상태쓰기(s4); 셈 += 남은.length;
        });
      });
    }
    return 일.then(function () { return 셈; }).catch(function () { return 0; });
  }
  function 묘비걷기(g) {
    var 한계 = Date.now() - 90 * 864e5, out = {};
    Object.keys(g || {}).forEach(function (k) { if (g[k] >= 한계) out[k] = g[k]; });
    return out;
  }
  function 지움표시(열쇠들) {
    var st = 상태읽기(), g = 묘비걷기(st.gone), p = st.pending || [], now = Date.now();
    (열쇠들 || []).forEach(function (k) { if (!설정.열쇠.test(k)) return; g[k] = now; if (p.indexOf(k) < 0) p.push(k); });
    st.gone = g; st.pending = p; 상태쓰기(st);
  }
  function 전부지움표시() {
    var st = 상태읽기(); st.wipe = Date.now(); st.wipe_pending = 1; st.gone = {}; st.pending = []; st.hashes = {}; st.times = {}; 상태쓰기(st);
  }

  /* 이 기기 → 서버. 바뀐 열쇠만 올린다. */
  function 밀어올리기() {
    if (!sb || !세션 || 동기화중 || !온라인()) return Promise.resolve(0);
    /* 2026-09-22 — 올리기 전에 먼저 끌어와 합친다. 안 그러면 다시 연결된 폰이 다른 폰이 그사이 올린 것을 덮어쓴다.
       올릴 것이 하나도 없으면(바뀐 열쇠도, 지울 것도) 서버를 부르지 않는다 — 30초마다 헛읽기를 막는다. */
    var st0 = 상태읽기(), 해0 = st0.hashes || {}, 바뀜있음 = !!(st0.wipe_pending || (st0.pending || []).length);
    if (!바뀜있음) 내열쇠().some(function (k) { var v = null; try { v = localStorage.getItem(k); } catch (e) {} if (v === null) return false; if (해0[k] !== 해시(v)) { 바뀜있음 = true; return true; } return false; });
    if (!바뀜있음) return Promise.resolve(0);
    return 지운것올리기().then(끌어오기).then(밀어올리기본);
  }
  function 밀어올리기본() {
    if (!sb || !세션 || 동기화중 || !온라인() || !동기화됨()) return Promise.resolve(0);
    var st = 상태읽기(), 해시들 = st.hashes || {}, 시각들 = st.times || {}, rows = [];
    내열쇠().forEach(function (k) {
      var v = null; try { v = localStorage.getItem(k); } catch (e) {} if (v === null) return;
      var h = 해시(v); if (해시들[k] === h) return;
      rows.push({ user_id: 세션.user.id, app: 설정.app, key: k, value: { v: v }, updated_at: new Date().toISOString() });
    });
    if (!rows.length) return Promise.resolve(0);
    동기화중 = true;
    return sb.from('records').upsert(rows, { onConflict: 'user_id,app,key' }).then(function (r) {
      동기화중 = false;
      if (r.error) return 0;
      rows.forEach(function (x) { 해시들[x.key] = 해시(x.value.v); 시각들[x.key] = Date.now(); });
      st.hashes = 해시들; st.times = 시각들; st.last_push = Date.now(); 상태쓰기(st);
      return rows.length;
    }).catch(function () { 동기화중 = false; return 0; });
  }

  /* ── 구독 상태 ── 서버 표 subscriptions 를 RPC 로 읽는다(처음이면 체험 14일이 생긴다). 표가 아직 없거나 오프라인이면 조용히 지난 값을 쓴다. */
  function 구독키() { return '_srv_sub_' + 설정.app; }
  function 구독조회() {
    if (!sb || !세션) return Promise.resolve(null);
    return sb.rpc('subscription_status', { p_app: 설정앱() }).then(function (r) {
      if (r.error) return null;
      var row = Array.isArray(r.data) ? r.data[0] : r.data; if (!row) return null;
      var o = { status: row.status, plan: row.plan || null, source: row.source || null, until: row.until ? Date.parse(row.until) : null, user: 세션.user.id, at: Date.now() };
      try { localStorage.setItem(구독키(), JSON.stringify(o)); } catch (e) {}
      화면갱신();
      if (typeof 설정.구독바뀜 === 'function') { try { 설정.구독바뀜(o); } catch (e) {} }
      return o;
    }).catch(function () { return null; });
  }
  function 설정앱() { return 설정.app; }
  window.구독상태 = function () {
    var o = null; try { o = JSON.parse(localStorage.getItem(구독키()) || 'null'); } catch (e) {}
    if (!o || !o.status) return null;
    var 남 = o.until ? Math.max(0, Math.ceil((o.until - Date.now()) / 864e5)) : null;
    var 열림 = (o.status === 'trial' || o.status === 'active') && (!o.until || o.until > Date.now());
    return { status: o.status, plan: o.plan, source: o.source, until: o.until, days: 남, 열림: 열림, at: o.at, user: o.user };
  };
  /* 2026-10-14 — 로그인 문(#/login)을 보고 있으면 알림을 단추 바로 위 글 칸에(사라지는 토스트 대신) */
  var 알림 = function (t) { try { if (document.getElementById('doorMsg')) { 문말(t); return; } if (typeof 잠깐말 === 'function') 잠깐말(t); else if (typeof tell === 'function') tell(t, ''); else if (typeof toast === 'function') toast(t); else console.log(t); } catch (e) { console.log(t); } };
  function 말(e) { var m = (e && e.message) || String(e || '');
    if (m === 'off') return 준비중말;
    if (/offline|lib|Failed to fetch|NetworkError/i.test(m)) return '인터넷이 닿지 않아요. 연결된 뒤 다시 해 주세요.';
    if (/Invalid login/i.test(m)) return '이메일이나 비밀번호가 맞지 않아요.';
    if (/already registered|already exists/i.test(m)) return '이미 가입된 이메일이에요. 로그인해 주세요.';
    if (/Password should be|weak/i.test(m)) return '비밀번호는 6자 이상, 남이 짐작하기 어렵게 정해 주세요.';
    if (/Email not confirmed/i.test(m)) return '메일함의 확인 링크를 먼저 눌러 주세요.';
    if (/rate limit|too many|security purposes/i.test(m)) return '잠깐 사이에 여러 번 하셔서 잠시 막혔어요. 조금 뒤에 다시 해 주세요.';
    if (/different from the old/i.test(m)) return '이전과 다른 비밀번호를 써 주세요.';
    if (/invalid.*email|validate email|email.*invalid/i.test(m)) return '이메일 주소를 다시 확인해 주세요.';
    if (/signups? not allowed|disabled/i.test(m)) return '지금은 새 계정을 만들 수 없어요. 잠시 뒤에 다시 해 주세요.';
    try { console.warn('계정', m); } catch (e2) {}
    return '잠시 문제가 생겼어요. 조금 뒤에 다시 해 주세요.'; }

  function 이용권줄() {
    if (!window.구독 || !구독.켜짐()) return '';   /* 2026-09-23 구독 틀 — 유료화 스위치가 꺼져 있으면 체험·요금 글을 보이지 않는다(되는 척 금지) */
    var sv = window.구독상태(); if (!sv) return '';
    var 날 = sv.until ? new Date(sv.until).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' }) : '';
    var t = sv.status === 'active' ? '구독 중' + (sv.plan === 'year' ? ' · 연 결제' : sv.plan === 'month' ? ' · 월 결제' : '') + (날 ? ' · ' + 날 + '까지' : '')
      : (sv.status === 'trial' && sv.열림) ? '체험 중 · ' + sv.days + '일 남음' + (날 ? ' (' + 날 + '까지)' : '')
      : '체험이 끝났어요 · 결제는 아직 붙기 전이라 요금이 나가지 않아요';
    return '<div class="srvrow"><b>이용권</b><span>' + t + '</span></div>';
  }
  window.이용권줄HTML = function () { try { return 이용권줄(); } catch (e) { return ''; } };
  function 화면갱신() { var el = document.getElementById('srvbox'); if (el) el.outerHTML = (el.getAttribute('data-door') && window.계정문HTML) ? window.계정문HTML() : window.계정화면HTML(); }   /* 10-14 로그인 문은 그 모양 그대로 */

  window.계정화면HTML = function () {
    var st = 상태읽기(), 이메일 = 세션 && 세션.user ? 세션.user.email : '';
    var 시각 = st.last_push || st.last_pull; var 언제 = 시각 ? new Date(시각).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '아직';
    var h = '<div id="srvbox" class="srvbox">';
    if (!준비됨()) return h + '<div class="srvrow"><b>계정·이어 보기는 준비 중이에요</b><span>지금은 이 휴대폰에서 그대로 쓰실 수 있어요.</span></div></div>';   /* 검수 #8 */
    if (!이메일) h += '<button type="button" class="srvdoor" onclick="go(\'/login\')">로그인 · 회원가입 화면 열기</button>';   /* 2026-10-14 로그인 문 */
    if (!서버허용()) {   /* 2026-09-22 — 동의 전·철회 상태: 되는 척 로그인 칸을 보이지 않고, 계정을 만드는 그 자리에서 동의를 받는다 */
      return h + '<p class="srvtiny">계정을 만들거나 로그인하려면 「서버에 저장하기」 동의가 필요해요 — ' + (window.계정항목 ? 계정항목.ko : '') + ' — 이 기록이 계정에 묶여 메디나눔 서버(서울)에 저장돼요.' + (window.계정항목 && 계정항목.뒤 != null ? 계정항목.뒤 : '') + '</p>'
        + '<div class="srvbtns"><button type="button" onclick="if(window.서버동의켜기)서버동의켜기()">동의하고 계속</button></div>'
        + (window.방침주소 ? '<a class="srvlink" href="' + 글자안전(방침주소()) + '#acct"' + (window.Capacitor && Capacitor.isNativePlatform && Capacitor.isNativePlatform() ? ' target="_blank" rel="noopener"' : '') + '>무엇이 올라가는지 자세히</a>' : '') + '</div>';
    }
    if (!이메일 && 복구대기() && !복구중) setTimeout(복구처리, 0);   /* 동의를 막 켠 뒤라면 여기서 이어 간다 */
    if (이메일 && 복구모드) {   /* 2026-09-23 큰문제 #10 — 메일의 복구 링크로 들어왔다 */
      h += '<div class="srvrow"><b>새 비밀번호 정하기</b><span>' + 글자안전(이메일) + ' · 메일의 링크로 들어오셨어요</span></div>'
        + '<input id="srvNewPw" type="password" autocomplete="new-password" enterkeyhint="next" aria-label="새 비밀번호 (6자 이상)" placeholder="새 비밀번호 (6자 이상)">'
        + '<input id="srvNewPw2" type="password" autocomplete="new-password" enterkeyhint="done" aria-label="새 비밀번호 한 번 더" placeholder="새 비밀번호 한 번 더">'
        + '<div class="srvbtns"><button type="button" onclick="계정동작(\'newpw\')">새 비밀번호 저장</button></div>'
        + '<p class="srvtiny">저장하면 이 휴대폰에서 로그인된 채로 이어져요.</p>';
    }
    if (이메일) {
      h += '<div class="srvrow"><b>' + 이메일 + '</b><span>로그인됨 · 마지막 동기화 ' + 언제 + '</span></div>' + 이용권줄()
        + '<div class="srvbtns"><button type="button" onclick="계정동작(\'sync\')">지금 동기화</button><button type="button" onclick="계정동작(\'logout\')">로그아웃</button></div>'
        + '<p class="srvtiny">기록은 이 휴대폰과 메디나눔 서버(서울)에 함께 있어요. 폰을 바꿔도 같은 이메일로 로그인하시면 이어져요. 메디나눔의 다른 앱과 계정은 하나지만 기록은 앱마다 따로예요.</p>'
        + '<button type="button" class="srvlink" onclick="계정동작(\'delete\')">계정 지우기 — 약지도의 서버 기록을 지웁니다</button>';
    } else {
      /* 2026-09-21 — 바로 위 화면 설명이 같은 말을 이미 하고 있었다(한 화면에 두 번). */
      h += '<input id="srvEmail" type="email" inputmode="email" autocomplete="email" enterkeyhint="next" aria-label="이메일" placeholder="이메일" value="' + (st.email || '') + '">'
        + '<input id="srvPw" type="password" autocomplete="current-password" enterkeyhint="go" aria-label="비밀번호 (6자 이상)" placeholder="비밀번호 (6자 이상)">'
        /* 2026-09-23 결정 0923 나 — 가입확인 갈고리: 앱이 넘기면 계정 만들기 앞에 필수 체크를 둔다(체크 전에는 계정 만들기 단추가 막힘). 로그인은 그대로. */
        + (설정.가입확인 ? '<label class="srvage"><input id="srvAge" type="checkbox" onchange="this.dataset.at=this.checked?new Date().toISOString():\'\';var b=document.getElementById(\'srvSignup\');if(b)b.disabled=!this.checked"><span>' + 글자안전(설정.가입확인.글) + '</span></label>'
            + (설정.가입확인.설명 ? '<p class="srvtiny">' + 글자안전(설정.가입확인.설명) + '</p>' : '') : '')
        + (window.구독 ? 구독.가입동의HTML() : '')   /* 2026-09-23 구독 틀 — 유료화 켜짐일 때만: 체험 뒤 결제 안내 필수 체크 */
        + '<div class="srvbtns"><button type="button" onclick="계정동작(\'login\')">로그인</button><button type="button" id="srvSignup" onclick="계정동작(\'signup\')"' + (설정.가입확인 ? ' disabled' : '') + '>계정 만들기</button></div>'
        + '<p class="srvtiny">계정을 만들면 메일함에 확인 링크가 가요. 한 번 누르면 끝이에요. 비밀번호를 잊으시면 아래 「비밀번호를 잊으셨나요?」를 눌러 주세요.</p>'
        + '<button type="button" class="srvlink" onclick="계정동작(\'reset\')">비밀번호를 잊으셨나요?</button>';
    }
    /* 2026-10-13 — 문의는 로그인해야 보내진다(답할 곳). 로그인 전엔 칸을 숨긴다 — 바로 아래 「이 앱에 대해」의 메일 주소가 그 자리. */
    if (이메일) h += '<div class="srvask"><b>문의 · 잘못된 내용 알리기</b><textarea id="srvAsk" rows="3" aria-label="문의 · 잘못된 내용 알리기" placeholder="어느 화면의 무엇이 이상한지 적어 주세요. 답은 이메일로 드립니다."></textarea>'
      + '<div class="srvbtns"><button type="button" onclick="계정동작(\'ask\')">보내기</button></div></div>';
    h += '</div>';
    return h;
  };

  /* ── 2026-10-14 약지도 — 로그인 문(#/login · 현욱님 「회원가입/로그인 화면」) ────────────────────
     같은 칸 id(srvEmail·srvPw·srvAge)와 같은 계정동작을 쓰고 모양만 다르다 — 서버 쪽 동작은 그대로.
     화면갱신은 #srvbox 의 data-door 를 보고 이 모양으로 다시 그린다.
     「서버에 저장하기」(건강 민감정보 · 개인정보 보호법 23조)는 계정을 쓰는 «그 자리»에서 따로 체크로 받는다 — 기본은 꺼짐.
     소셜 단추는 켠 것(window.소셜켜짐() → ['google'])만 그린다 — 눌러도 안 되는 단추 금지.
     10-30 현욱님 「일단 켜놓자」 — 구글만 켠다(카카오는 Supabase 키 고친 뒤, 네이버는 검수 뒤). 네 앱 계정 부품과 같은 꼴:
     「메일로 계속하기」 아래 「또는」 + 「Google로 계속하기」, 누르면 메일과 같은 체크(만 14세·서버 저장)를 먼저 본다.
     설치 앱(웹뷰)에서는 구글이 웹뷰 로그인을 막으므로, 바깥 브라우저로 여는 껍데기.열기가 있을 때만 보인다. */
  var 소셜글 = { kakao: '카카오로 계속하기', google: 'Google로 계속하기' }, 소셜이름 = { kakao: '카카오', google: 'Google' };
  var 소셜그림 = { kakao: '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="#000" d="M12 3C6.48 3 2 6.58 2 11c0 2.85 1.86 5.35 4.66 6.77l-.95 3.5c-.08.3.26.54.52.37l4.14-2.75c.53.07 1.08.11 1.63.11 5.52 0 10-3.58 10-8S17.52 3 12 3z"/></svg>', google: '<svg viewBox="0 0 48 48" width="20" height="20" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>' };
  function 네이티브() { try { return !!(window.Capacitor && Capacitor.isNativePlatform && Capacitor.isNativePlatform()); } catch (e) { return false; } }
  window.소셜켜짐 = function () { if (!준비됨()) return []; if (네이티브() && !(window.껍데기 && typeof window.껍데기.열기 === 'function')) return []; return ['kakao', 'google']; };   /* 11-02 카카오 켬(Main · 네 앱과 같은 순서: 카카오 위, Google 아래) */
  window.계정문소셜 = function (p) {
    if (window.소셜켜짐().indexOf(p) < 0) return;
    var g = document.getElementById('srvAgree'), a = document.getElementById('srvAge');
    if (!서버허용()) {
      if (!g || !g.checked) { 문필수('srvAgree', '「서버에 저장하기」에 체크해 주세요. 동의하지 않으셔도 약지도는 그대로 쓰실 수 있어요.'); return; }
    }
    /* 처음인지 미리 알 수 없어 늘 묻는다 — 메일의 「처음 만들 때 필수」와 같은 체크 */
    if (설정.가입확인 && (!a || !a.checked)) { 문필수('srvAge', 소셜이름[p] + '로 계속하려면 「' + 설정.가입확인.글 + '」에 체크해 주세요.'); return; }
    /* 동의 기록은 모든 확인이 끝난 뒤 — 먼저 적으면 화면이 다시 그려져 방금 띄운 안내가 사라졌다(11-03) */
    if (!서버허용() && typeof 설정.동의기록 === 'function') { try { 설정.동의기록(); } catch (e) {} }
    var 앱id = 네이티브() && window.껍데기 && window.껍데기.appId ? window.껍데기.appId : '';
    var 돌아올 = 앱id ? 앱id + '://login' : 앱주소();
    문말(소셜이름[p] + '로 넘어가는 중이에요…');
    return 준비().then(function () {
      try { sessionStorage.setItem('yj_oauth', JSON.stringify({ p: p, age14_at: (a && a.dataset && a.dataset.at) || new Date().toISOString() })); } catch (e) {}
      return sb.auth.signInWithOAuth({ provider: p, options: { redirectTo: 돌아올 || undefined, skipBrowserRedirect: true } });
    }).then(function (r) {
      if (r && r.error) throw r.error;
      var u = r && r.data && r.data.url; if (!u) throw new Error('no url');
      if (앱id) return window.껍데기.열기(u);
      location.assign(u);
    }).catch(function (e) { 문말(''); 알림(말(e)); });
  };
  /* 구글에서 돌아옴 — 웹은 주소 꼬리(#access_token…), 설치 앱은 appUrlOpen 이 넘겨준 주소 */
  function 소셜돌아옴(url) {
    var i = String(url || '').search(/[#?]/); if (i < 0) return Promise.resolve(false);
    var q = {}; String(url).slice(i + 1).split('&').forEach(function (kv) { var j = kv.indexOf('='); if (j > 0) { try { q[decodeURIComponent(kv.slice(0, j))] = decodeURIComponent(kv.slice(j + 1).replace(/\+/g, ' ')); } catch (e) {} } });
    if (!(q.access_token && q.refresh_token) && !q.error) return Promise.resolve(false);
    var 표 = {}; try { 표 = JSON.parse(sessionStorage.getItem('yj_oauth') || '{}') || {}; sessionStorage.removeItem('yj_oauth'); } catch (e) {}
    if (q.error) { 알림(q.error === 'access_denied' ? '로그인을 그만두셨어요. 바뀐 것은 없어요.' : '로그인이 되지 않았어요. 잠시 뒤 다시 해 주세요.'); return Promise.resolve(false); }
    return 준비().then(function () { return sb.auth.setSession({ access_token: q.access_token, refresh_token: q.refresh_token }); }).then(function (r) {
      if (r && r.error) throw r.error;
      if (r && r.data && r.data.session) 세션 = r.data.session;
      var u = 세션 && 세션.user, st = 상태읽기(); if (u && u.email) st.email = u.email; st.social = (u && u.app_metadata && u.app_metadata.provider) || 'social'; 상태쓰기(st);
      /* 처리방침 1항 — 가입 앱·만 14세 확인 시각을 계정 기록에 남긴다(메일 가입과 같은 칸) */
      var m = (u && u.user_metadata) || {};
      if (u && !m.age14_at) sb.auth.updateUser({ data: { app: m.app || 설정.app, age14_at: 표.age14_at || new Date().toISOString() } }).catch(function () {});
      알림('로그인했어요. 기록을 맞추는 중이에요…'); 화면갱신(); try { if (typeof go === 'function') go('/me?t=set'); } catch (e) {} return true;
    }).catch(function (e) { 알림(말(e)); return false; });
  }
  var 문탭 = 'login', 문말글 = '';
  function 문말(t) { 문말글 = t || ''; var el = document.getElementById('doorMsg'); if (el) { el.textContent = 문말글; el.hidden = !문말글; } }
  window.계정문말 = 문말;
  function 비번칸(id, 이름, ac, 다음) {
    return '<label class="door-f" for="' + id + '">' + 이름 + '</label><div class="door-pw"><input id="' + id + '" type="password" autocomplete="' + ac + '" enterkeyhint="' + 다음 + '" minlength="6" autocapitalize="off" spellcheck="false">'
      + '<button type="button" class="door-eye" aria-pressed="false" aria-controls="' + id + '" aria-label="비밀번호 보이기" onclick="계정문눈(this,\'' + id + '\')">보이기</button></div>';
  }
  window.계정문눈 = function (b, id) { var p = document.getElementById(id); if (!p) return; var 보임 = p.type === 'password'; p.type = 보임 ? 'text' : 'password'; b.setAttribute('aria-pressed', 보임 ? 'true' : 'false'); b.setAttribute('aria-label', 보임 ? '비밀번호 숨기기' : '비밀번호 보이기'); b.textContent = 보임 ? '숨기기' : '보이기'; };
  window.계정문탭 = function (t) {
    var e = document.getElementById('srvEmail'), v = e ? e.value : null;
    문탭 = t === 'signup' ? 'signup' : 'login'; 문말글 = ''; 화면갱신();
    var e2 = document.getElementById('srvEmail'); if (e2 && v != null) e2.value = v;
    var b = document.querySelector('.door-seg [aria-selected="true"]'); if (b) b.focus();
  };
  window.계정문확인 = function () {
    var b = document.getElementById('srvDoorGo'), w = document.getElementById('doorWhy'); if (!b) return;
    var g = document.getElementById('srvAgree'), 막 = !!(g && !g.checked);
    if (w) w.hidden = !막; document.querySelectorAll('.door-why').forEach(function (x) { x.hidden = !막; });
  };
  /* 11-03 현욱님 폰 — 필수 체크 없이 카카오·Google 을 누르면 잠긴 단추라 아무 일도 없었다(「눌러도 진행이 안 돼요」).
     단추는 늘 눌리고, 빠진 체크 칸 바로 아래에 빨간 글 · 칸 테두리 · 그 칸으로 스크롤(시트 뒤 띠에 가리지 않게) */
  function 문필수(id, 글) {
    var c = document.getElementById(id), lb = c && c.closest('label'); if (!lb) { 문말(글); return; }
    document.querySelectorAll('.door-need-msg').forEach(function (x) { x.remove(); });
    lb.classList.add('door-need');
    var m = document.createElement('p'); m.className = 'door-need-msg'; m.setAttribute('role', 'alert'); m.textContent = window.I18N && I18N.t ? I18N.t(글) : 글; lb.insertAdjacentElement('afterend', m);
    try { lb.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) { lb.scrollIntoView(); }
    try { c.focus({ preventScroll: true }); } catch (e) {}
  }
  document.addEventListener('change', function (e) { var t = e.target; if (!t || !/^(srvAgree|srvAge)$/.test(t.id) || !t.checked) return; var lb = t.closest('label'); if (lb) { lb.classList.remove('door-need'); var n = lb.nextElementSibling; if (n && n.classList.contains('door-need-msg')) n.remove(); } });
  window.계정문동작 = function (what) {
    what = what || (문탭 === 'signup' ? 'signup' : 'login');
    var g = document.getElementById('srvAgree'), a = document.getElementById('srvAge'), em = document.getElementById('srvEmail'), pw = document.getElementById('srvPw');
    if (!서버허용()) {
      if (!g || !g.checked) { 문필수('srvAgree', '「서버에 저장하기」에 체크해 주세요. 동의하지 않으셔도 약지도는 그대로 쓰실 수 있어요.'); return; }
    }
    if (what === 'signup' && 설정.가입확인 && (!a || !a.checked)) { 문필수('srvAge', '계정을 만들려면 「' + 설정.가입확인.글 + '」에 체크해 주세요.'); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(((em || {}).value || '').trim())) { 문말('이메일 주소를 다시 확인해 주세요.'); if (em) em.focus(); return; }
    if (what !== 'reset' && ((pw || {}).value || '').length < 6) { 문말('비밀번호는 6자 이상이에요.'); if (pw) pw.focus(); return; }
    if (!서버허용() && typeof 설정.동의기록 === 'function') { try { 설정.동의기록(); } catch (e) {} }   /* 확인이 다 끝난 뒤에 적는다 */
    문말(what === 'reset' ? '메일을 보내는 중이에요…' : '잠시만요…');
    return window.계정동작(what);
  };
  window.계정문HTML = function () {
    var st = 상태읽기(), 이메일 = 세션 && 세션.user ? 세션.user.email : '', h = '<div id="srvbox" class="srvbox door-box" data-door="1">';
    var 말칸 = '<p id="doorMsg" class="door-msg" role="status" aria-live="polite"' + (문말글 ? '' : ' hidden') + '>' + 글자안전(문말글) + '</p>';
    if (!준비됨()) return h + '<p class="door-note">' + 준비중말 + '</p></div>';
    if (!이메일 && 복구대기() && !복구중 && 서버허용()) setTimeout(복구처리, 0);
    /* 전에 로그인한 폰 — 세션을 되살리는 동안 로그인 칸이 잠깐 보이고, 되살아나면 계정 모양으로 바꾼다 */
    if (!이메일 && st.email && !sb && 서버허용() && 온라인()) 준비().then(function () { if (세션) 화면갱신(); }).catch(function () {});
    if (이메일 && 복구모드) return h + '<h2 class="door-h2">새 비밀번호 정하기</h2><p class="door-note">' + 글자안전(이메일) + ' · 메일의 링크로 들어오셨어요.</p>'
      + 비번칸('srvNewPw', '새 비밀번호 <small>6자 이상</small>', 'new-password', 'next') + 비번칸('srvNewPw2', '새 비밀번호 한 번 더', 'new-password', 'done')
      + 말칸 + '<button type="button" class="door-go" onclick="계정동작(\'newpw\')">새 비밀번호 저장</button></div>';
    if (이메일) {
      var 시각 = st.last_push || st.last_pull, 언제 = 시각 ? new Date(시각).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '아직 없어요';
      return h + '<div class="door-me"><span class="door-av" aria-hidden="true">' + 글자안전(이메일.charAt(0).toUpperCase()) + '</span><span><b>' + 글자안전(이메일) + '</b><small>로그인돼 있어요 · 마지막으로 맞춘 때 ' + 글자안전(언제) + '</small></span></div>'
        + '<p class="door-note">기록은 이 휴대폰과 메디나눔 서버(서울)에 함께 있어요. 새 휴대폰에서 같은 이메일로 로그인하시면 그대로 이어져요.</p>' + 말칸
        + '<div class="srvbtns"><button type="button" onclick="계정동작(\'sync\')">지금 맞추기</button><button type="button" onclick="계정동작(\'logout\')">로그아웃</button></div>'
        + '<button type="button" class="srvlink" onclick="go(\'/me?t=set\')">계정 지우기·동의 거두기는 내 정보 → 설정에서</button></div>';
    }
    var 가입 = 문탭 === 'signup', 동의됨 = 서버허용(), 소셜 = [], 항목 = window.계정항목 || {};
    try { 소셜 = (typeof window.소셜켜짐 === 'function' && window.소셜켜짐()) || []; } catch (e) { 소셜 = []; }
    /* 2026-10-29 현욱님 — 로그인/회원가입 갈림 없이 「메일로 계속하기」 하나: 계정이 있으면 로그인, 처음이면 그 자리에서 만든다 */
    가입 = false;
    if (설정.가입확인) h += '<label class="door-ck"><input id="srvAge" type="checkbox" onchange="this.dataset.at=this.checked?new Date().toISOString():\'\'"><span><b>' + 글자안전(설정.가입확인.글) + ' <em class="door-tag">처음 만들 때 필수</em></b>' + (설정.가입확인.설명 ? '<small>' + 글자안전(설정.가입확인.설명) + '</small>' : '') + '</span></label>';
    if (가입 && 설정.가입확인) h += '<label class="door-ck"><input id="srvAge" type="checkbox" onchange="this.dataset.at=this.checked?new Date().toISOString():\'\';계정문확인()"><span><b>' + 글자안전(설정.가입확인.글) + ' <em class="door-tag">필수</em></b>' + (설정.가입확인.설명 ? '<small>' + 글자안전(설정.가입확인.설명) + '</small>' : '') + '</span></label>';
    if (!동의됨) h += '<label class="door-ck"><input id="srvAgree" type="checkbox" onchange="계정문확인()"><span><b>「서버에 저장하기」에 동의해요 <em class="door-tag">필수</em></b><small>건강에 관한 민감정보라 따로 여쭤요. 로그인하시면 이 휴대폰의 기록이 계정으로 이어져요.</small></span></label>'
      + '<details class="door-more"><summary>무엇이 올라가나요<svg class="i chev" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></summary><dl>'
      + '<dt>올라가는 것</dt><dd>' + 글자안전(항목.ko || '약지도 기록') + '</dd><dt>어디에</dt><dd>메디나눔 서버(Supabase, 서울)</dd><dt>왜</dt><dd>폰을 바꿔도 이어 보려고</dd>'
      + '<dt>언제까지</dt><dd>계정을 지우실 때까지 — 동의를 거두시면 서버 기록을 바로 지워요</dd></dl><p>동의하지 않으셔도 되고, 동의하지 않아도 약지도는 이 휴대폰에서 그대로 쓰실 수 있어요. 보기 설정과 날씨는 올라가지 않아요.</p></details>';
    var 막힘 = !동의됨;
    /* 11-01 네 앱 계정 시트와 같은 순서(Main 606f55c8 · 「어르신은 Google 이 위가 쉽다」): 동의 체크 → Google → 「또는 메일로」 → 이메일·비밀번호 → 메일로 계속하기 */
    h += (소셜.length ? '<div class="door-social">' + 소셜.filter(function (p) { return 소셜글[p]; }).map(function (p) { return '<button type="button" class="door-soc door-' + p + '" onclick="계정문소셜(\'' + p + '\')">' + 소셜그림[p] + '<span>' + 소셜글[p] + '</span></button>'; }).join('') + '</div>' + (막힘 ? '<p class="door-why">먼저 위의 필수 칸에 체크해 주세요</p>' : '') + '<p class="door-or"><span>또는 메일로</span></p>' : '');
    h += '<label class="door-f" for="srvEmail">이메일</label><input id="srvEmail" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" enterkeyhint="next" value="' + 글자안전(st.email || '') + '">'
      + 비번칸('srvPw', '비밀번호 <small>처음이면 새로 정할 비밀번호 · 6자 이상</small>', 'current-password', 'go');
    h += 말칸 + '<button type="button" id="srvDoorGo" class="door-go" onclick="계정문동작(\'continue\')"' + (막힘 ? ' aria-describedby="doorWhy"' : '') + '>메일로 계속하기</button>'
      + (막힘 ? '<p id="doorWhy" class="door-why">먼저 위의 필수 칸에 체크해 주세요</p>' : '')
      + '<p class="door-note">계정이 있으면 로그인하고, 처음이면 계정을 만들어요. 새로 만들면 메일함에 확인 링크가 가요 — 한 번 누르면 끝이에요.</p>'
      + '<button type="button" class="srvlink door-forgot" onclick="계정문동작(\'reset\')">비밀번호를 잊으셨나요?</button>';
    return h + '</div>';
  };
  /* 다른 화면에서 왔으면 지난 글 칸을 비운다 */
  window.계정문처음 = function (탭) { 문말글 = ''; if (탭) 문탭 = 탭 === 'signup' ? 'signup' : 'login'; };

  var 지우기예약 = 0;   /* 2026-09-22 — 계정 지우기 두 번 누르기 */
  /* 2026-09-22 — 엔터로 로그인. 칸이 <form> 안에 있지 않아 엔터가 아무 데도 닿지 않았다. */
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' || e.isComposing) return;
    var id = e.target && e.target.id;
    if (id === 'srvEmail') { e.preventDefault(); var pw = document.getElementById('srvPw'); if (pw) pw.focus(); }
    else if (id === 'srvPw') { e.preventDefault(); if (document.querySelector('#srvbox[data-door]')) window.계정문동작(); else window.계정동작('login'); }
    else if (id === 'srvNewPw') { e.preventDefault(); var p2 = document.getElementById('srvNewPw2'); if (p2) p2.focus(); }
    else if (id === 'srvNewPw2') { e.preventDefault(); window.계정동작('newpw'); }
  });
  function 서버허용() { try { return !설정.허용 || 설정.허용() !== false; } catch (e) { return true; } }
  window.서버허용 = 서버허용;
  /* 2026-09-23 구독 틀 — 앱이 '동기화는 구독 기능'이라고 알려 준다(스위치 꺼짐이면 늘 true). 지운 것 올리기는 멈추지 않는다. */
  function 동기화됨() { try { return !설정.동기화허용 || 설정.동기화허용() !== false; } catch (e) { return true; } }
  window.계정동작 = function (what) {
    if (!준비됨()) { 알림(준비중말); return; }   /* 검수 #8 — 서버 표가 올라가기 전 */
    /* 2026-09-22 — 「서버에 저장하기」 동의를 철회한 동안은 로그아웃만 된다 */
    if (!서버허용() && what !== 'logout') { 알림('「서버에 저장하기」에 동의하셔야 계정을 쓸 수 있어요. 로그인 화면이나 내 정보 → 설정 → 계정에서 동의해 주세요.'); return; }
    var email = (document.getElementById('srvEmail') || {}).value || '', pw = (document.getElementById('srvPw') || {}).value || '';
    email = email.trim();
    if (what === 'ask') {
      var t = ((document.getElementById('srvAsk') || {}).value || '').trim(); if (!t) { 알림('내용을 적어 주세요.'); return; }
      return 준비().then(function () {
        if (!세션) { 알림('문의는 로그인한 뒤에 보내실 수 있어요(답을 드릴 곳이 필요해요).'); return; }
        return sb.from('inquiries').insert({ user_id: 세션.user.id, app: 설정.app, kind: 'ask', text: t, screen: location.hash || '' }).then(function (r) {
          if (r.error) throw r.error; 알림('보냈어요. 이메일로 답해 드릴게요.'); var ta = document.getElementById('srvAsk'); if (ta) ta.value = '';
        });
      }).catch(function (e) { 알림(말(e)); });
    }
    if (what === 'delete') {
      /* 2026-09-22 — 계정 지우기(탈퇴). 서버 함수 delete_own_account 가 본인 행과 계정을 지운다(_시안/계정_지우기.sql). */
      if (!세션) { 알림('먼저 로그인해 주세요.'); return; }
      if (Date.now() - 지우기예약 > 10000) {
        지우기예약 = Date.now();
        알림('약지도의 서버 기록을 지우고, 다른 메디나눔 앱 기록이 없으면 계정까지 지워요. 되돌릴 수 없어요. 10초 안에 「계정 지우기」를 한 번 더 누르시면 지워요.');
        return;
      }
      지우기예약 = 0;
      return 준비().then(function () { return typeof 설정.지우기전 === 'function' ? Promise.resolve(설정.지우기전(sb, 세션)).catch(function () {}) : null; }).then(function () { return sb.rpc('yak_family_end_all').then(function () {}, function () {}); }).then(function () { return sb.rpc('delete_own_account', { p_app: 설정.app }); }).then(function (r) {
        if (r && r.error) throw r.error;
        try { 내열쇠().forEach(function (k) { localStorage.removeItem(k); }); } catch (e) {}
        try { localStorage.removeItem('_srv_' + 설정.app); localStorage.removeItem(구독키()); ['yakjido.ask', 'mn.addr', 'mn.chat.on.yakjido'].forEach(function (k) { localStorage.removeItem(k); }); } catch (e) {}   /* 11-04 묻고 싶은 것·응급 카드 주소도 */
        세션 = null; try { sb.auth.signOut(); } catch (e) {}
        알림(r && r.data && r.data.account_deleted === false ? '약지도의 서버 기록과 이 휴대폰의 기록을 지웠어요. 다른 메디나눔 앱 기록이 남아 있어 계정은 그대로예요.' : '계정과 약지도 서버 기록을 지웠어요. 이 휴대폰에 있던 약지도 기록도 비웠어요.');
        화면갱신();
        if (typeof 설정.다시그리기 === 'function') { try { 설정.다시그리기(); } catch (e) {} }
      }).catch(function (e) { var m = 말(e); 알림(/인터넷/.test(m) ? '인터넷이 닿지 않아 지우지 못했어요. 연결되면 「계정 지우기」를 다시 눌러 주세요.' : m); });   /* 2026-10-13 — 「자동으로 이어집니다」는 지우기에는 거짓이었다 */
    }
    if (what === 'newpw') {   /* 2026-09-23 큰문제 #10 — 복구 링크로 들어온 세션에서 새 비밀번호를 저장한다 */
      var n1 = (document.getElementById('srvNewPw') || {}).value || '', n2 = (document.getElementById('srvNewPw2') || {}).value || '';
      if (n1.length < 6) { 알림('비밀번호는 6자 이상이어야 해요.'); return; }
      if (n1 !== n2) { 알림('두 칸의 비밀번호가 달라요.'); return; }
      return 준비().then(function () { if (!세션) throw new Error('login'); return sb.auth.updateUser({ password: n1 }); }).then(function (r) {
        if (r && r.error) throw r.error;
        복구모드 = false; 알림('새 비밀번호를 저장했어요.'); 화면갱신();
      }).catch(function (e) { 알림(/^login$/.test((e && e.message) || '') ? '복구 링크가 만료됐어요. 「비밀번호를 잊으셨나요?」로 새 링크를 받아 주세요.' : 말(e)); });
    }
    if (what === 'logout') { return 준비().then(function () { return sb.auth.signOut(); }).then(function () { 세션 = null; try { localStorage.removeItem(구독키()); } catch (e) {} 알림('로그아웃했어요. 이 휴대폰의 기록은 그대로 있어요.'); 화면갱신(); }).catch(function (e) { 알림(말(e)); }); }
    if (what === 'sync') { return 준비().then(function () { if (!세션) { 알림('먼저 로그인해 주세요.'); return; } return 끌어오기().then(function () { return 밀어올리기(); }).then(function (n) { 알림('맞췄어요' + (n ? ' (' + n + '건 올림)' : '') + '.'); 화면갱신(); }); }).catch(function (e) { 알림(말(e)); }); }
    if (what === 'signup' && 설정.가입확인 && !(document.getElementById('srvAge') || {}).checked) { 알림('계정을 만들려면 「' + 설정.가입확인.글 + '」에 체크해 주세요.'); return; }   /* 2026-09-23 나 */
    if (!email || email.indexOf('@') < 0) { 알림('이메일을 적어 주세요.'); return; }
    var st = 상태읽기(); st.email = email; 상태쓰기(st);
    if (what === 'reset') { return 준비().then(function () { var u = 앱주소(); return u ? sb.auth.resetPasswordForEmail(email, { redirectTo: u }) : sb.auth.resetPasswordForEmail(email); }).then(function (r) { if (r && r.error) throw r.error; }).then(function () { 알림('메일함을 확인해 주세요. 링크를 누르면 새 비밀번호를 정하실 수 있어요.'); }).catch(function (e) { 알림(말(e)); }); }
    if (pw.length < 6) { 알림('비밀번호는 6자 이상이어야 해요.'); return; }
    return 준비().then(function () {
      if (what === 'signup' && 설정.가입확인 && typeof 설정.가입확인.기록 === 'function') { try { 설정.가입확인.기록(); } catch (e) {} }   /* 2026-09-23 나 — 확인한 때를 앱이 적는다 */
      /* 2026-10-13 상용화 점검 2-08/2-19 — 만 14세 확인을 «언제» 했는지 계정 기록(user_metadata)에 남긴다(처리방침 1항: 가입 앱·만 14세 확인 시각).
         가입확인을 쓰지 않는 앱이면 app 만 넣는다. 비밀 값은 없다. */
      var 가입표 = { app: 설정.app }; if (설정.가입확인) { var ag = document.getElementById('srvAge'); 가입표.age14_at = (ag && ag.dataset && ag.dataset.at) || new Date().toISOString(); }
      /* 2026-10-29 「메일로 계속하기」 — 먼저 로그인해 보고, 맞는 계정이 없으면 그 자리에서 만든다.
         Supabase 는 「없는 메일」과 「틀린 비밀번호」를 같은 말로 돌려주므로, 만들기를 시도해 이미 있는 메일이면(identities 가 빈 배열) 비밀번호 문제로 알린다. */
      if (what === 'continue') return sb.auth.signInWithPassword({ email: email, password: pw }).then(function (r) {
        if (!r.error) { 세션 = r.data.session; 알림('로그인했어요. 기록을 맞추는 중이에요…'); 화면갱신(); return; }
        if (!/invalid login credentials/i.test(String(r.error.message || ''))) throw r.error;
        var ag = document.getElementById('srvAge');
        if (설정.가입확인 && !(ag && ag.checked)) { 알림('비밀번호가 맞지 않거나 처음 쓰시는 메일이에요. 처음이시면 「' + 설정.가입확인.글 + '」에 체크하고 다시 눌러 주세요. 계정이 있으시면 「비밀번호를 잊으셨나요?」를 눌러 주세요.'); return; }
        if (설정.가입확인 && typeof 설정.가입확인.기록 === 'function') { try { 설정.가입확인.기록(); } catch (e) {} }
        return sb.auth.signUp(앱주소() ? { email: email, password: pw, options: { emailRedirectTo: 앱주소(), data: 가입표 } } : { email: email, password: pw, options: { data: 가입표 } }).then(function (r2) {
          if (r2.error) throw r2.error;
          var u = r2.data && r2.data.user;
          if (u && Array.isArray(u.identities) && u.identities.length === 0) { 알림('이미 있는 계정이에요. 비밀번호를 다시 확인하시거나 「비밀번호를 잊으셨나요?」를 눌러 주세요.'); return; }
          if (r2.data && r2.data.session) { 세션 = r2.data.session; 알림('처음 쓰시는 메일이라 계정을 만들었어요. 기록을 올리는 중이에요…'); 화면갱신(); }
          else 알림('처음 쓰시는 메일이라 계정을 만들었어요. 메일함의 확인 링크를 누르신 뒤 다시 「메일로 계속하기」를 눌러 주세요.');
        });
      });
      if (what === 'signup') return sb.auth.signUp(앱주소() ? { email: email, password: pw, options: { emailRedirectTo: 앱주소(), data: 가입표 } } : { email: email, password: pw, options: { data: 가입표 } }).then(function (r) {
        if (r.error) throw r.error;
        if (r.data && r.data.session) { 세션 = r.data.session; 알림('계정을 만들었어요. 기록을 올리는 중이에요…'); 화면갱신(); }
        else 알림('메일함에 확인 링크를 보냈어요. 누르신 뒤 로그인해 주세요.');
      });
      return sb.auth.signInWithPassword({ email: email, password: pw }).then(function (r) {
        if (r.error) throw r.error; 세션 = r.data.session; 알림('로그인했어요. 기록을 맞추는 중이에요…'); 화면갱신();
      });
    }).catch(function (e) { 알림(말(e)); });
  };

  window.서버 = {
    설치: function (o) {
      설정.app = o.app || 설정.app; 설정.열쇠 = o.열쇠 || 설정.열쇠; 설정.다시그리기 = o.다시그리기 || null; 설정.구독바뀜 = o.구독바뀜 || null;
      설정.허용 = typeof o.허용 === 'function' ? o.허용 : null;   /* 2026-09-22 — 앱이 「서버에 저장하기」 동의를 철회했는지 알려 준다 */
      설정.동기화허용 = typeof o.동기화허용 === 'function' ? o.동기화허용 : null;   /* 2026-09-23 구독 틀 */
      설정.가입확인 = (o.가입확인 && o.가입확인.글) ? o.가입확인 : null;
      설정.지우기전 = typeof o.지우기전 === 'function' ? o.지우기전 : null; 설정.로그인됨 = typeof o.로그인됨 === 'function' ? o.로그인됨 : null;   /* 길동무 서버 준비 1008 */
      설정.동의기록 = typeof o.동의기록 === 'function' ? o.동의기록 : null;   /* 2026-10-14 로그인 문 — 「서버에 저장하기」 체크를 앱의 동의 기록에 적는 갈고리 */
      설정.준비됨 = typeof o.준비됨 === 'function' ? o.준비됨 : o.준비됨 !== false;   /* 2026-10-13 — 함수로 넘기면 함수 그대로(약지도 meta.account 스위치) */
      설정.병합 = typeof o.병합 === 'function' ? o.병합 : null;   /* 2026-10-13 — 앱이 자기 기록 모양대로 합치는 갈고리(두 폰 동기화) */   /* 검수 #8 — 서버 표가 올라가면 앱의 설치 줄에서 true 로(또는 줄을 지운다) */   /* 2026-09-23 나 — { 글, 설명, 기록 } : 계정 만들기 앞 필수 체크 */
      /* 10-30 구글에서 돌아옴 — 복구 링크보다 먼저 본다(취소하면 error= 로 온다) */
      /* 설치 때는 자료(D.meta)가 아직일 수 있어 준비됨을 묻지 않는다 — yj_oauth 표시가 있으면 우리가 보낸 길이다. 처리는 자료가 온 뒤(최대 15초) */
      try { var 소 = location.hash; if (sessionStorage.getItem('yj_oauth') && /(^#|&)(access_token|error)=/.test(소) && !/type=recovery/.test(소)) { history.replaceState(history.state, '', location.pathname + location.search); var 소n = 0; (function 기다림() { if (준비됨()) 소셜돌아옴('#' + 소.replace(/^#/, '')); else if (++소n < 60) setTimeout(기다림, 250); })(); } } catch (e) {}
      if (준비됨()) { try { if (/(^#|&)(type=recovery|error_code=)/.test(location.hash)) { sessionStorage.setItem('yj_recovery', location.hash.slice(1)); history.replaceState(history.state, '', location.pathname + location.search); } } catch (e) {} }   /* 길동무 서버 준비 1008 */
      var st = 상태읽기();
      /* 전에 로그인한 적이 있을 때만 라이브러리를 받아 세션을 되살린다 — 처음 온 분의 첫 화면은 건드리지 않는다 */
      if (준비됨() && st.email && 온라인() && 서버허용()) { setTimeout(function () { 준비().catch(function () {}); }, 1500); }
      /* 화면을 떠날 때·30초마다 바뀐 것만 올린다 — 동의를 철회한 동안은 올리지 않는다 */
      setInterval(function () { if (세션 && 서버허용()) 밀어올리기(); }, 30000);
      document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden' && 세션 && 서버허용()) 밀어올리기(); });
      window.addEventListener('online', function () { if (세션 && 서버허용()) 밀어올리기(); if (복구대기()) 복구처리(); });
      if (복구대기()) setTimeout(복구처리, 0);   /* 2026-09-23 큰문제 #10 — 복구 링크로 막 들어왔다 */
      var css = document.createElement('style');
      css.textContent = '.srvbox{display:flex;flex-direction:column;gap:8px}.srvbox input,.srvbox textarea{width:100%;box-sizing:border-box;min-height:46px;padding:10px 12px;border:1.5px solid var(--ui-line);border-radius:var(--r-input);font:inherit;font-size:1rem;background:var(--card);color:var(--text)}'
        + '.srvbtns{display:flex;gap:8px;flex-wrap:wrap}.srvbtns button{flex:1;min-height:46px;padding:0 14px;border:1.5px solid var(--ui-line);border-radius:999px;background:var(--card);color:var(--text);font:600 1rem/1 inherit;font-family:inherit;cursor:pointer;touch-action:manipulation}.srvbtns button:first-child{background:var(--primary);color:var(--on-primary);border-color:var(--primary)}'
        + '.srvrow{display:flex;flex-direction:column;gap:2px}.srvrow span{color:var(--muted);font-size:.92em}.srvtiny{margin:0;color:var(--muted);font-size:.9em;line-height:1.6}.srvlink{background:none;border:0;min-height:46px;padding:8px 0;color:var(--primary-deep);font:inherit;font-weight:600;text-align:left;cursor:pointer}a.srvlink{display:inline-flex;align-items:center;text-decoration:underline;text-underline-offset:3px}'
        + '.srvask{margin-top:10px;padding-top:10px;border-top:1px dashed var(--hairline);display:flex;flex-direction:column;gap:8px}.srvask b{font-size:.95em}'
        + '.srvage{display:flex;align-items:center;gap:10px;min-height:46px;cursor:pointer}.srvbox .srvage input{width:20px;height:20px;min-height:20px;margin:0;padding:0;flex:none;accent-color:var(--accent,currentColor)}.srvbtns button:disabled{opacity:.45;cursor:not-allowed}';
      document.head.appendChild(css);
    },
    소셜돌아옴: 소셜돌아옴,
    세션: function () { return 세션; }, 올리기: function () { return sb && 세션 && 서버허용() && 동기화됨() ? 밀어올리기() : Promise.resolve(0); },   /* 11-03 체크 즉시 올리기 */
    동기화: function () { return 준비().then(지운것올리기).then(끌어오기).then(밀어올리기); },
    /* 2026-09-22 — 지운 것을 서버에도 지운다. 로그인 전이거나 오프라인이면 묘비만 남기고,
       연결되면 그때 지운다. 앱은 열쇠를 지울 때 이걸 부르면 된다. */
    지움: function (열쇠들) { 지움표시(열쇠들); if (sb && 세션 && 온라인()) return 지운것올리기(); return Promise.resolve(0); },
    전부지움: function () { 전부지움표시(); if (sb && 세션 && 온라인()) return 지운것올리기(); return Promise.resolve(0); },
    /* 2026-10-13 — 「서버에 저장하기」 동의를 거둘 때: 이 앱의 서버 기록을 지우고(다른 앱 기록이 없으면 계정도) 로그아웃. 이 기기 기록은 그대로. */
    서버만지움: function () {
      return 준비().then(function () {
        if (!세션) return { skipped: true };
        return sb.rpc('yak_family_end_all').then(function () {}, function () {}).then(function () { return sb.rpc('delete_own_account', { p_app: 설정.app }); }).then(function (r) {   /* 11-02 — 동의를 거두면 가족 알림 연결도 끊는다 */
          if (r && r.error) throw r.error;
          try { localStorage.removeItem('_srv_' + 설정.app); } catch (e) {}
          세션 = null; try { sb.auth.signOut(); } catch (e) {}
          화면갱신(); return (r && r.data) || {};
        });
      });
    },
    문의: function (kind, text, screen) { return 준비().then(function () { if (!세션) throw new Error('login'); return sb.from('inquiries').insert({ user_id: 세션.user.id, app: 설정.app, kind: kind || 'ask', text: text, screen: screen || '' }); }); },
    준비: 준비, 상태: 상태읽기, 구독: function () { return 준비().then(구독조회); },
    /* 2026-10-13 상용화 점검 1-15 — 설치 앱이 메일 복구 링크(appUrlOpen)로 돌아오면 app-shell 이 sessionStorage 에 넣고 바로 부른다 */
    복구처리: 복구처리,
    준비됨: 준비됨   /* 검수 #8 — false 면 계정·동기화 준비 중 */
  };
})();
/* ▲▲ 서버 부품 끝 ▲▲ */
/* ▼▼ 구독 부품 시작 ▼▼ */
/* ═══ 구독(체험·잠금·해지) — 네 앱 공용 부품 (2026-09-23) ═══════════════════════════
   설계: _시안/구독_틀_설계.md · 서버: _서버/구독_추가.sql (start_trial · subscription_status · cancel_subscription)
   원칙
   · 한 줄로 판단한다 — 구독.열림(id): 스위치 꺼짐 → 늘 열림 · 응급 id → 늘 열림 · 면제 → 열림 ·
     서버 구독 상태가 trial/active 이고 until 전 → 열림 · 그 밖 → 막힘.
   · 스위치(유료화)가 꺼져 있는 동안 이 부품은 화면에 아무것도 내놓지 않는다(요금·체험·결제 글 0, 되는 척 금지).
     검토할 때만 주소에 ?paywall=1 을 붙이면 '이번 창에서만' 켜진다(어디에도 저장하지 않는다).
   · 응급·위기(109·1577-0199·119·응급실 찾기 등)는 잠금 목록에 넣어도 부품이 거부한다.
   · 부품 글에는 앱 전용 말을 넣지 않는다 — 앱마다 다른 말(「안전 계획」·「환자 확인」 등)은 설치 옵션 문구 로 끼운다.
   · 서버는 서버 부품이 내놓는 공개 손잡이(서버.준비 · 서버.세션)로만 만진다. 서버 부품이 없으면 조용히 비활성.
     서버 부품의 window.구독상태 · 구독조회 와는 따로 논다(저장 열쇠도 다르다: _sub_<app>).
   쓰는 법(앱 끝, 서버.설치 뒤):
     구독.설치({ app:'gyeote', 유료화:false,
                 가격:{ 월:5900, 연:49000, 학생월:4900, 학생연:39000,     // 월만 꼭. 연·학생월·학생연은 있으면 막힘 시트·관리 화면에 함께 보인다
                        출시:{ 월:4900, 연:39900 } },                   // 출시 기념가(출시 3개월 안 가입 · 첫 1년) — 있으면 한 줄 더
                 회원권:{ 월:12900, 연:99000, 출시월:9900, 출시연:79000, 판매:false },   // 다섯 앱 공용. 판매:false 면 「곧 열려요」
                 잠금:{ sync:'서버 동기화·여러 기기', lab:{ ko:'검사 추이', en:'Lab trends' }, … },   // id → 화면에 보일 이름(글 또는 {ko,en})
                 응급:['crisis', …],                                // 늘 열림(기본 목록에 더해진다)
                 면제:function(){ return false; },                  // 길동무: 확인된 환자
                 계정:true,                                         // 계정(로그인) 화면이 없는 앱은 false — 로그인·체험 시작 글/단추를 감추고
                                                                    //   「계정이 열리면 체험을 시작할 수 있어요」로 사실대로
                 말:function(){ return 'ko'; },                     // 'ko' | 'en' — 부품 글 두 벌 중 고른다(CS: 앱의 ko())
                 문구:{ 응급안내:'…', 막힘앞:'…', 막힘뒤:'…', 관리뒤:'…',   // ⬅ 앱별 말 끼울 자리(HTML · {ko,en} · function(id, 말){…})
                        학생:{ko:'학생·수련의', en:'students and trainees'}, 학생조건:{ko:'학교·병원 이메일 인증 뒤', en:'…'} },
                 학생인증:null,                                     // ⬅ 학생 인증 화면이 생기면 여는 함수. 없으면 「인증은 준비 중」으로 사실대로
                 결제사:null,                                        // 결제사가 정해지면 이름(예: 'toss')
                 결제:{ 등록:function(){ … } },                      // ⬅ 결제사 붙일 자리 — 결제수단 등록 창을 여는 함수.
                                                                     //    결제사:null(또는 결제.등록 없음)이면 이 자리는 쓰지 않고 「결제 준비 중」 한 줄만 보인다.
                                                                     //    그때는 막힘 시트·관리·동의 체크·2일 전 카드 어디에서도 「○월 ○일부터 결제됩니다」를 말하지 않고
                                                                     //    「결제가 시작되기 전에 요금·결제일을 보여 드리고 다시 동의를 받아요」로 말한다(2026-09-23 검수 #7).
                 인증:{ 휴대폰:false, 공동:false },                  // ⬅ 문자 발송사·인증 대행 계약 뒤 함수(또는 true)로. false 면 단추가 안 보인다.
                 시트열기:function(html, 제목){…}, 시트닫기:function(){…},   // 앱의 기존 시트 부품
                 알림:function(말){…}, 로그인열기:function(){…}, 바뀜:function(상태){…},
                 모양:{ 카드:'blk', 줄:'rcta', 주:'p', 보조:'s', 작은글:'bandnote' } });   // 앱의 기존 클래스(새 색·크기 없음)
     진입점:  if (!구독.열림('sync')) return 구독.막힘('sync');
     화면:    구독.전환카드HTML() (홈 맨 위) · 구독.관리HTML() (설정) · 구독.가입동의HTML() (가입 화면)
   ⚠️ 서버 동기화 잠금은 서버 부품이 `동기화허용` 갈고리를 받을 때만 자동 동기화까지 멈춘다(곁에 서버 부품에 있음).
      이 부품은 「지금 동기화」 단추(계정동작('sync'))와 가입 동의 체크만 감싼다.
   ⚠️ 영어 글도 우리말과 같은 금지 낱말 규칙을 따른다(요금이 없다는 뜻의 낱말을 쓰지 않는다).
   판 2026-09-23b(검수 #7) — 결제사 없을 때 「결제됩니다」 대신 「다시 동의를 받아요」 · 잠금 이름 뒤 조사(은/는)를 받침으로 고른다.
     검증은 구독.판 으로 새 부품인지 본다(다시 심기 전 앱은 구독.판 이 없다).
   판 2026-10-08(결제 다리) — 스토어 껍데기(_껍데기/src/껍데기.js)가 window.껍데기.결제 를 내놓으면 결제 자리를 그것으로 쓴다(앱 설치 줄은 그대로 결제사:null).
     · 스위치(유료화)가 꺼져 있으면 껍데기가 있어도 아무것도 바뀌지 않는다(껍데기결제() 가 null).
     · 「14일 체험 시작」·「다시 구독하기」 → 껍데기.결제.구매('<app>_month') → 웹훅이 서버 표를 고치면 subscription_status 를 다시 읽는다(몇 번 되읽음).
       start_trial RPC 는 스토어 길에서는 부르지 않는다(체험은 스토어 상품의 14일 체험이다).
     · 설정 → 구독에 「구매 복원」(껍데기.결제.복원 → 되읽음) · 해지는 스토어의 구독 관리 화면으로(「스토어에서 구독 관리」 — 앱이 해지한 척하지 않는다).
     · 사용자가 결제를 그만두면 「결제를 취소했어요」, 그 밖의 오류는 「결제가 되지 않았어요」 한 줄(차분하게 · 기술 글 없음).
   판 2026-10-13(로그인 없이 구매) — 스토어 길(껍데기.결제)에서는 계정이 없어도 체험 시작·구독·구매 복원이 된다.
     · 열림 판단은 스토어 영수증(RevenueCat 고객 정보 — 껍데기.결제.상태())을 먼저 본다. 기기에 _sub_store_<app> 으로 요약만 둔다
       (활성·체험·갱신·만료·상품 — 이름·메일 없음). 로그인했으면 서버 표(subscription_status)도 함께 본다 — 둘 중 열린 쪽이 이긴다.
     · 로그인하면 껍데기가 RevenueCat 에 그 계정 id 로 logIn 한다(로그인 전 구매가 계정에 붙는다 · 다른 기기에서 복원 가능).
     · 웹(브라우저) 길은 그대로 — 계정·서버 체험(start_trial).
     · 해지는 여전히 스토어의 구독 관리 화면에서만(앱이 해지한 척하지 않는다).
     · 1년 이용권 — 스토어 길이고 가격.연 이 있으면 「1년으로 시작」 단추가 함께 보인다(상품 <app>_year). 동의 글은 두 요금을 함께 적는다.
       카드·관리 화면의 요금은 산 상품(plan)대로(연이면 연 요금).
   판 2026-10-21(출시 기념가 · 메디나눔 회원권) — 현욱님 10-21 결정(docs/shared/원칙_결정.md · docs/requests/20261021_메디나눔_전앱_회원권.md)
     · 가격.출시:{월,연} — 출시 기념가(출시 3개월 안 가입 · 첫 1년). 요금줄에 정가와 함께 한 줄. 실제 할인은 스토어의 첫해 할인 offer 가 한다
       (앱은 값을 말할 뿐 깎아 주는 척하지 않는다).
     · 회원권:{월,연,출시월,출시연,판매} — 다섯 앱 공용 이용권. 스토어 상품 medinanum_pass_month · _year, RevenueCat 권한 medinanum_pass.
       판매:false(기본)이면 요금줄에 값과 「곧 열려요」만 — 단추 없음(되는 척 금지). 판매:true 이고 스토어 길이면 「회원권으로 시작」 단추.
     · 열림 — 스토어 영수증에 medinanum_pass 권한이 살아 있으면 이 앱도 연다(껍데기 요약의 권한 목록 · 회원권 상품의 만료일).
       다섯 앱이 공용 서버의 같은 계정 id 로 RevenueCat 에 들어가므로 다른 앱에서 산 회원권도 보인다. 서버 표는 pass_subscriptions(plan 'pass_month' · 'pass_year').
     · 초대 코드(가입 부품 _도구/가입_부품.js) — 서버가 plan 'invite' 로 돌려주면 「초대 코드로 체험 중 · ○월 ○일까지」(결제 글 없음). */
(function () {
  var 판 = '2026-10-21';
  var 응급기본 = ['crisis', 'sos', 'emergency', 'danger', 'call109', 'call119', 'call15770199', 'safety_plan', 'er', 'er_find', 'where'];
  var 설정 = { app: 'app', 유료화: false, 가격: { 월: 0 }, 회원권: null, 잠금: {}, 면제: null, 응급: [], 결제사: null, 결제: null, 계정: true, 말: null, 문구: {}, 학생인증: null,
               인증: { 휴대폰: false, 공동: false }, 시트열기: null, 시트닫기: null, 알림: null, 로그인열기: null, 바뀜: null,
               모양: { 카드: 'srvbox', 줄: 'srvbtns', 주: '', 보조: '', 작은글: 'srvtiny' } };
  var 검토 = false; try { 검토 = /[?&]paywall=1(?:&|#|$)/.test(String(location.search || '')); } catch (e) {}
  var 설치됨 = false, 조회중 = null;

  /* ── 말 두 벌 — 부품 글은 여기 한 곳에. {날}·{값} 같은 자리는 채움() 이 채운다 ── */
  var 글표 = {
    ko: {
      구독: '구독', 이기능: '이 기능',
      잠김: '<b>{이름}</b>{은는} 구독으로 열리는 기능이에요.',
      응급기본: '위급할 때 쓰는 연결은 언제나 열려 있어요.',
      계정으로: '체험은 계정으로 시작해요. 로그인하고 메일 확인을 마치면 14일 동안 모두 쓸 수 있어요.',
      계정없음: '체험과 구독은 준비 중이에요. 지금은 이 기능을 열 수 없어요.',
      전환날: '14일 체험 뒤 {날}부터 {값}이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      전환: '14일 체험이 끝나면 {값}이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      동의: '(필수) 14일 체험이 끝나는 {날}에 {값}이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      체험끝: '14일 체험이 끝났어요.', 기간끝: '구독 기간이 끝났어요.', 기록그대로: '그동안 남긴 기록은 그대로 있어요.', 기록그대로2: '남긴 기록은 그대로 있어요.',
      로그인하러: '로그인하러 가기', 닫기: '닫기', 체험시작: '14일 체험 시작', 결제수단: '결제수단 등록',
      결제준비: '결제 준비 중이에요. 지금은 결제되지 않아요.', 결제준비짧게: '결제 준비 중이에요.',
      /* 2026-10-20 — 결제 단추 바로 위 고지(전자상거래법 13조 · Play 구독 정책). 요청 20261020_ClinicScore_메디나눔_구독부품글표 */
      고지첫결제: '첫 결제 — 14일 체험이 끝나는 {날}에 {값}이 결제됩니다.',
      고지첫결제날없음: '첫 결제 — 14일 체험이 끝나는 날에 {값}이 결제됩니다.',
      고지갱신: '갱신 — 이후 {주기}마다 자동으로 갱신됩니다. 해지하지 않으면 계속 결제됩니다.',
      고지주기월: '한 달', 고지주기연: '1년',
      고지해지스토어: '해지 — 구독을 산 스토어에서 언제든 해지할 수 있습니다. Google Play 는 「결제 및 정기 결제 → 정기 결제」, App Store 는 「계정 → 구독」. 앱을 지워도 해지되지 않습니다.',
      고지해지앱: '해지 — 이 앱의 「구독과 결제」 화면에서 언제든 해지할 수 있습니다. 앱을 지워도 해지되지 않습니다.',
      고지검토: '<b>검토용 미리 보기</b> — 결제가 열린 뒤 결제 단추 위에 보일 안내입니다. 지금은 결제되지 않습니다.',
      고지복원: '복원 — 폰을 바꾸거나 앱을 다시 설치하면 「구매 복원」으로 이용권을 되살릴 수 있습니다.',
      약관: '이용약관', 처리방침: '개인정보 처리방침', 환불안내: '환불·해지 안내',
      다시동의: '결제가 시작되기 전에 요금·결제일을 보여 드리고 다시 동의를 받아요.',
      동의준비: '(필수) 14일 체험은 {날}에 끝나요. 결제가 시작되기 전에 요금·결제일을 보여 드리고 다시 동의를 받아요.',
      요금: '요금', 학생기본: '학생', 학생인증준비: '인증은 준비 중이에요', 학생인증단추: '학생 인증하기',
      출시가: '출시 기념가', 출시조건: '출시 3개월 안에 가입하면 첫 1년', 회원권: '메디나눔 회원권', 회원권설명: '다섯 앱을 함께 쓰는 이용권', 회원권자격: 'ClinicScore 의료인 기능은 의료인 확인 뒤 열려요',
      곧: '곧 열려요', 출시값: '{값}(출시 기념가 · 첫 1년, 둘째 해부터 {정가})', 출시값둘: '출시 기념가 {값} — 첫 1년, 둘째 해부터 {정가}', 초대중: '<b>초대 코드로 체험 중</b> · {날}까지', 초대뒤: '이 기간에는 결제되지 않아요. 기간이 끝나면 일반 상태로 돌아가요.', 회원권시작: '회원권으로 시작', 회원권연시작: '회원권 1년으로 시작 · {값}', 회원권중: '메디나눔 회원권으로 열려 있어요.',
      이유: { login: '먼저 로그인해 주세요.', verify: '메일함의 확인 링크를 먼저 눌러 주세요. 확인한 계정에서 체험이 시작돼요.',
              used_account: '이 계정은 14일 체험을 이미 쓰셨어요.', used_device: '이 기기에서는 14일 체험을 이미 쓰셨어요.',
              device: '이 브라우저에서는 체험을 시작할 수 없어요. 다른 브라우저로 해 주세요.', app: '잠시 문제가 있었어요. 다시 해 주세요.',
              noacct: '계정이 열리면 체험을 시작할 수 있어요.' },
      체크: '결제 안내를 확인하고 체크해 주세요.', 인터넷: '인터넷이 닿지 않아요. 연결되면 다시 해 주세요.',
      체험됨: '14일 체험을 시작했어요. {날}까지 모두 쓸 수 있어요.',
      해지취소됨: '해지를 취소했어요. 그대로 이어져요.', 해지됨: '해지했어요. ', 까지그대로: '{날}까지는 그대로 쓸 수 있어요.',
      카드결제: '{날}에 {값}이 결제됩니다. 원하지 않으시면 그 전에 해지할 수 있어요.',
      카드준비: '{날}에 14일 체험이 끝나요. 결제가 시작되기 전에 요금·결제일을 보여 드리고 다시 동의를 받아요.',
      해지자세히: '해지·자세히', 카드닫기이름: '결제 안내 닫기',
      관리로그인: '로그인하면 구독 상태를 볼 수 있어요.',
      관리계정없음: '계정이 열리면 여기서 체험을 시작하고 구독 상태를 볼 수 있어요.',
      아직: '아직 체험을 시작하지 않았어요.', 관리전환: '14일 체험 뒤 {값}이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      구독중: '구독 중이에요', 체험중: '체험 중이에요', 남음: ' · {n}일 남았어요', 까지괄호: ' ({날}까지)',
      해지예약: '해지를 예약했어요. ', 해지예약뒤: '{날}까지는 그대로 쓸 수 있고, 그 뒤로 결제되지 않아요.',
      해지취소: '해지 취소', 다음결제: '다음 결제일 {날} · {값}', 해지하기: '해지하기', 해지해도: '해지해도 {날}까지는 그대로 쓸 수 있어요.', 기간끝말: '기간 끝',
      휴대폰: '휴대폰으로 인증', 공동: '공동인증서로 인증', 미연결: '아직 연결되지 않았어요.', 문제: '잠시 문제가 있었어요.',
      /* 2026-10-08 스토어 결제(껍데기) */
      복원: '구매 복원', 다시구독: '다시 구독하기', 스토어관리: '스토어에서 구독 관리',
      스토어해지: '해지는 스토어의 구독 관리 화면에서 해요. 해지해도 {날}까지는 그대로 쓸 수 있어요.',
      결제취소: '결제를 취소했어요. 바뀐 것은 없어요.', 결제안됨: '결제가 되지 않았어요. 잠시 뒤 다시 해 주세요.',
      결제반영중: '결제는 끝났어요. 구독 상태가 곧 반영돼요. 잠시 뒤 다시 열어 주세요.', 구독됨: '구독을 시작했어요. 바로 모두 쓸 수 있어요.',
      관리전환둘: '14일 체험 뒤 고르신 요금({값})이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      연시작: '1년으로 시작 · {값}', 연구독: '1년으로 구독 · {값}',
      동의둘: '(필수) 14일 체험이 끝나는 {날}에 고르신 요금({값})이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      전환둘날: '14일 체험 뒤 {날}부터 고르신 요금({값})이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      복원됨: '구매를 복원했어요.', 복원없음: '복원할 구매가 없어요. 구매한 Google 계정이 이 폰에 로그인되어 있는지 확인해 주세요.'
    },
    en: {
      구독: 'Subscription', 이기능: 'This feature',
      잠김: '<b>{이름}</b> is part of the subscription.',
      응급기본: 'Emergency help is always open.',
      계정으로: 'The trial starts from an account. Sign in and confirm your email to use everything for 14 days.',
      계정없음: 'The trial and subscription are still being prepared. This feature cannot be opened yet.',
      전환날: 'After the 14-day trial, {값} will be charged from {날}. You can cancel any time before then.',
      전환: 'When the 14-day trial ends, {값} will be charged. You can cancel any time before then.',
      동의: '(Required) When the 14-day trial ends on {날}, {값} will be charged. You can cancel any time before then.',
      체험끝: 'Your 14-day trial has ended.', 기간끝: 'Your subscription period has ended.', 기록그대로: 'Everything you recorded is still here.', 기록그대로2: 'Everything you recorded is still here.',
      로그인하러: 'Sign in', 닫기: 'Close', 체험시작: 'Start 14-day trial', 결제수단: 'Add payment method',
      결제준비: 'Payments are not set up yet. Nothing is charged now.', 결제준비짧게: 'Payments are not set up yet.',
      고지첫결제: 'First charge — {값} on {날}, when the 14-day trial ends.',
      고지첫결제날없음: 'First charge — {값} on the day the 14-day trial ends.',
      고지갱신: 'Renewal — renews automatically every {주기}. You are charged until you cancel.',
      고지주기월: 'month', 고지주기연: 'year',
      고지해지스토어: 'Cancel — any time in the store you bought it from: Google Play ‘Payments and subscriptions → Subscriptions’, App Store ‘Account → Subscriptions’. Deleting the app does not cancel it.',
      고지해지앱: 'Cancel — any time on the ‘Subscription and billing’ screen in this app. Deleting the app does not cancel it.',
      고지검토: '<b>Review preview</b> — this is what appears above the payment button once billing opens. Nothing is charged now.',
      고지복원: 'Restore — if you change phones or reinstall, ‘Restore purchase’ brings your subscription back.',
      약관: 'Terms of Service', 처리방침: 'Privacy Policy', 환불안내: 'Refunds and cancellation',
      다시동의: 'Before any payment starts, we will show you the price and billing date and ask for your consent again.',
      동의준비: '(Required) The 14-day trial ends on {날}. Before any payment starts, we will show you the price and billing date and ask for your consent again.',
      요금: 'Price', 학생기본: 'students', 학생인증준비: 'verification is coming soon', 학생인증단추: 'Verify student status',
      출시가: 'Launch price', 출시조건: 'first year, if you join within 3 months of launch', 회원권: 'MediNanum pass', 회원권설명: 'one plan for all five apps', 회원권자격: 'ClinicScore professional tools open after the professional check',
      곧: 'coming soon', 출시값: '{값} (launch price for the first year; {정가} from the second year)', 출시값둘: 'launch price {값} for the first year; {정가} from the second year', 초대중: '<b>Invite access</b> · until {날}', 초대뒤: 'Nothing is charged during this period. Afterwards it returns to normal.', 회원권시작: 'Start with the pass', 회원권연시작: 'Start a 1-year pass · {값}', 회원권중: 'Open through your MediNanum pass.',
      이유: { login: 'Please sign in first.', verify: 'Please open the confirmation link in your email first. The trial starts on a confirmed account.',
              used_account: 'This account has already used the 14-day trial.', used_device: 'This device has already used the 14-day trial.',
              device: 'The trial cannot be started in this browser. Please try another browser.', app: 'Something went wrong. Please try again.',
              noacct: 'You can start the trial once accounts open.' },
      체크: 'Please read the billing notice and tick the box.', 인터넷: 'Cannot reach the internet. Please try again once you are connected.',
      체험됨: 'Your 14-day trial has started. Everything is open until {날}.',
      해지취소됨: 'Cancellation withdrawn. Your plan continues.', 해지됨: 'Cancelled. ', 까지그대로: 'You can keep using it until {날}.',
      카드결제: '{값} will be charged on {날}. If you do not want this, you can cancel before then.',
      카드준비: 'Your 14-day trial ends on {날}. Before any payment starts, we will show you the price and billing date and ask for your consent again.',
      해지자세히: 'Cancel · details', 카드닫기이름: 'Close billing notice',
      관리로그인: 'Sign in to see your subscription.',
      관리계정없음: 'Once accounts open, you can start the trial and see your subscription here.',
      아직: 'You have not started the trial yet.', 관리전환: 'After the 14-day trial, {값} will be charged. You can cancel any time before then.',
      구독중: 'Subscribed', 체험중: 'On trial', 남음: ' · {n} days left', 까지괄호: ' (until {날})',
      해지예약: 'Cancellation scheduled. ', 해지예약뒤: 'You can keep using it until {날}, and nothing will be charged after that.',
      해지취소: 'Undo cancellation', 다음결제: 'Next payment {날} · {값}', 해지하기: 'Cancel', 해지해도: 'Even if you cancel, you can keep using it until {날}.', 기간끝말: 'the end of the period',
      휴대폰: 'Verify by phone', 공동: 'Verify with certificate', 미연결: 'Not connected yet.', 문제: 'Something went wrong.',
      /* 2026-10-08 store billing (shell) */
      복원: 'Restore purchases', 다시구독: 'Subscribe again', 스토어관리: 'Manage in the store',
      스토어해지: 'Cancel from the store’s subscription settings. Even if you cancel, you can keep using it until {날}.',
      결제취소: 'Payment cancelled. Nothing has changed.', 결제안됨: 'The payment did not go through. Please try again in a moment.',
      결제반영중: 'Payment complete. Your subscription will show up shortly. Please reopen in a moment.', 구독됨: 'Your subscription has started. Everything is open now.',
      관리전환둘: 'After the 14-day trial, the plan you choose ({값}) will be charged. You can cancel any time before then.',
      연시작: 'Start with 1 year · {값}', 연구독: 'Subscribe for 1 year · {값}',
      동의둘: '(Required) When the 14-day trial ends on {날}, the plan you choose ({값}) will be charged. You can cancel any time before then.',
      전환둘날: 'After the 14-day trial, the plan you choose ({값}) will be charged from {날}. You can cancel any time before then.',
      복원됨: 'Purchases restored.', 복원없음: 'No purchases to restore. Please check that the Google account you bought with is signed in on this phone.'
    }
  };
  var 달이름 = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function 말() { try { if (typeof 설정.말 === 'function' && 설정.말() === 'en') return 'en'; } catch (e) {} return 'ko'; }
  function 채움(t, o) { return String(t).replace(/\{(\w+|[가-힣]+)\}/g, function (m, k) { return o && k in o ? o[k] : m; }); }
  function 말글(k, o) { var 표 = 글표[말()], t = 표[k]; if (t == null) t = 글표.ko[k]; return 채움(t, o); }
  function 두벌(v, id) {   /* 앱이 준 글 — 글 · {ko,en} · function(id, 말) */
    if (v == null) return '';
    if (typeof v === 'function') { try { return String(v(id, 말()) || ''); } catch (e) { return ''; } }
    if (typeof v === 'object') return String(v[말()] != null ? v[말()] : (v.ko != null ? v.ko : ''));
    return String(v);
  }
  function 문(k, id) { return 두벌((설정.문구 || {})[k], id); }

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function 켜짐() { return !!(설정.유료화 || 검토); }
  function 응급(id) { return 응급기본.indexOf(id) >= 0 || (설정.응급 || []).indexOf(id) >= 0; }
  function 원(n) { n = Number(n || 0); return 말() === 'en' ? '₩' + n.toLocaleString('en-US') : n.toLocaleString('ko-KR') + '원'; }
  function 월값(n) { n = n == null ? (설정.가격 || {}).월 : n; return 말() === 'en' ? 원(n) + '/month' : '월 ' + 원(n); }
  function 연값(n) { return 말() === 'en' ? 원(n) + '/year' : '연 ' + 원(n); }
  function 날(t) { var d = new Date(t); return 말() === 'en' ? 달이름[d.getMonth()] + ' ' + d.getDate() : (d.getMonth() + 1) + '월 ' + d.getDate() + '일'; }
  function 계정있나() { return 설정.계정 !== false; }
  function 이름(id) { return 두벌(설정.잠금 && 설정.잠금[id]) || 말글('이기능'); }
  /* 결제사가 실제로 붙었나 — 이름(결제사)과 등록 함수(결제.등록)가 둘 다 있을 때만. 아니면 「결제됩니다」를 말하지 않는다.
     2026-10-08 — 스토어 껍데기(window.껍데기.결제)가 있으면 그것도 「붙은 것」이다. 스위치가 꺼져 있으면 껍데기도 없는 셈(화면 0). */
  function 껍데기결제() {
    if (!켜짐()) return null;
    try { var k = window.껍데기; return (k && k.있음 && k.결제 && typeof k.결제.구매 === 'function') ? k.결제 : null; } catch (e) { return null; }
  }
  function 상품(plan) { return 설정.app + (plan === 'year' ? '_year' : '_month'); }
  var 회원권권한 = 'medinanum_pass';
  function 회원권상품(plan) { return 회원권권한 + (plan === 'year' ? '_year' : '_month'); }
  function 회원권판매() { var g = 설정.회원권; return !!(g && g.판매 === true && g.월 && 껍데기결제()); }   /* 스토어 상품을 등록한 뒤에만 판다 */   /* 스토어 상품 id — store-webhook 이 앞머리(<app>_)로 앱을 가른다 */
  function 연있나() { return !!(껍데기결제() && 설정.가격 && 설정.가격.연); }   /* 2026-10-13 — 스토어 길에서 1년 이용권도 판다 */
  /* 2026-10-21 곁에·길동무 요청 — 첫 결제를 말하는 자리(고지·동의·전환·시작 단추)는 출시 기념가가 있으면 그 값과 둘째 해 값을 함께.
     가격.출시.까지('YYYY-MM-DD', 그날까지 가입)가 지나면 정가만. 요금줄(정가·출시 기념가 나란히)은 그대로. */
  function 출시중() { var o = (설정.가격 || {}).출시; if (!o) return null; if (o.까지) { var d = Date.parse(o.까지 + 'T23:59:59+09:00'); if (!isNaN(d) && Date.now() > d) return null; } return o; }
  function 첫월값() { var o = 출시중(); return o && o.월 ? 말글('출시값', { 값: 월값(o.월), 정가: 월값() }) : 월값(); }
  function 첫연값() { var o = 출시중(), g = 설정.가격 || {}; return o && o.연 && g.연 ? 말글('출시값', { 값: 연값(o.연), 정가: 연값(g.연) }) : 연값(g.연); }
  function 두요금() {   /* 괄호 안에 또 괄호가 들지 않게 — 출시 기념가면 한 줄로 묶는다 */
    var o = 출시중(), g = 설정.가격 || {};
    if (o && o.월 && o.연 && g.연) return 말글('출시값둘', { 값: 월값(o.월) + ' · ' + 연값(o.연), 정가: 월값() + ' · ' + 연값(g.연) });
    return 첫월값() + ' · ' + 첫연값();
  }
  function 첫값(s) { if (s && s.회원권) return 값(s); return s && s.plan === 'year' && 설정.가격 && 설정.가격.연 ? 첫연값() : 첫월값(); }   /* 체험 뒤 첫 결제 */
  function 값(s) {   /* 산 상품대로 */
    var 회 = 설정.회원권; if (s && s.회원권 && 회 && 회.월) return s.plan === 'year' && 회.연 ? 연값(회.연) : 월값(회.월);
    return s && s.plan === 'year' && 설정.가격 && 설정.가격.연 ? 연값(설정.가격.연) : 월값();
  }
  function 결제있나() { return !!((설정.결제사 && 설정.결제 && typeof 설정.결제.등록 === 'function') || 껍데기결제()); }
  function 전환말(끝) {   /* 체험 뒤 이야기 — 결제사가 없으면 날짜·금액 대신 「다시 동의를 받아요」 */
    if (!결제있나()) return 말글('다시동의');
    if (끝 && 연있나()) return 말글('전환둘날', { 날: 날(끝), 값: 두요금() });
    return 끝 ? 말글('전환날', { 날: 날(끝), 값: 첫월값() }) : 말글('전환', { 값: 첫월값() });
  }
  /* 조사 — 낱말 끝 받침으로 고른다(「추이는」「사례집은」「6개째부터는」). 끝의 괄호 덧말「(Lab)」은 보지 않는다.
     짝은 '은/는' · '이/가' · '을/를' 처럼 받침 있는 쪽을 앞에. 우리말·숫자로 끝나지 않으면 「은(는)」 꼴로 둔다. */
  function 받침(w) {
    w = String(w || '').replace(/\s*\([^()]*\)\s*$/, '').replace(/[\s.,·'"’”」』]+$/, '');
    if (!w) return -1;
    var c = w.charCodeAt(w.length - 1);
    if (c >= 0xAC00 && c <= 0xD7A3) return (c - 0xAC00) % 28 ? 1 : 0;
    if (/[0-9]$/.test(w)) return '013678'.indexOf(w.slice(-1)) >= 0 ? 1 : 0;   /* 영·일·삼·육·칠·팔 */
    if (/(^|[^A-Za-z])[A-Z]{2,}$/.test(w)) return 'LMNR'.indexOf(w.slice(-1)) >= 0 ? 1 : 0;   /* 대문자 줄임말은 글자 이름으로(PDF→에프·HTML→엘) */
    return -1;
  }
  function 조사(w, 짝) { var p = String(짝).split('/'), b = 받침(w); return b < 0 ? p[0] + '(' + p[1] + ')' : p[b ? 0 : 1]; }
  function 알림(t) {
    try { if (typeof 설정.알림 === 'function') return 설정.알림(t); } catch (e) {}
    try { if (typeof 잠깐말 === 'function') 잠깐말(t); else if (typeof toast === 'function') toast(t); else console.log(t); } catch (e) { console.log(t); }
  }
  function 모(k) { return (설정.모양 && 설정.모양[k]) || ''; }
  function 단추(글, 부름, 주, 이름) {
    return '<button type="button"' + ((주 ? 모('주') : 모('보조')) ? ' class="' + (주 ? 모('주') : 모('보조')) + '"' : '') +
      (이름 ? ' aria-label="' + esc(이름) + '"' : '') + ' onclick="' + 부름 + '">' + esc(글) + '</button>';
  }
  function 줄(안) { return 안 ? '<div class="' + 모('줄') + '">' + 안 + '</div>' : ''; }
  function 작은(글) { return '<p class="' + 모('작은글') + '">' + 글 + '</p>'; }
  /* 가격 여럿 — 연·학생월·학생연이 있을 때만 한 줄로 더 보인다(월 하나뿐이면 결제 안내 글로 충분하다) */
  function 요금줄() {
    var g = 설정.가격 || {}, 칸 = [];
    if (g.연) 칸.push(월값(g.월) + ' · ' + 연값(g.연));
    if (g.학생월 || g.학생연) {
      var 학 = 문('학생') || 말글('학생기본'), 값 = [];
      if (g.학생월) 값.push(월값(g.학생월)); if (g.학생연) 값.push(연값(g.학생연));
      var 조건 = 문('학생조건');
      var 인증 = typeof 설정.학생인증 === 'function' ? '' : 말글('학생인증준비');   /* 인증 화면이 없으면 사실대로 「준비 중」 */
      칸.push(esc(학) + ' ' + 값.join(' · ') + ((조건 || 인증) ? ' (' + [esc(조건), 인증].filter(Boolean).join(' — ') + ')' : ''));
    }
    if (g.출시 && (g.출시.월 || g.출시.연)) {
      var 출 = []; if (g.출시.월) 출.push(월값(g.출시.월)); if (g.출시.연) 출.push(연값(g.출시.연));
      칸.push(말글('출시가') + ' ' + 출.join(' · ') + ' (' + 말글('출시조건') + ')');
    }
    var 회 = 설정.회원권;
    if (회 && 회.월) {
      var 회값 = [월값(회.월)]; if (회.연) 회값.push(연값(회.연));
      var 회출 = []; if (회.출시월) 회출.push(월값(회.출시월)); if (회.출시연) 회출.push(연값(회.출시연));
      칸.push('<b>' + 말글('회원권') + '</b>(' + 말글('회원권설명') + ') ' + 회값.join(' · ') +
        (회출.length ? ' — ' + 말글('출시가') + ' ' + 회출.join(' · ') : '') + (회원권판매() ? '' : ' — ' + 말글('곧')) + ' (' + 말글('회원권자격') + ')');   /* 2026-10-22 회원권 = 결제 권한, 들어갈 자격은 따로 */
    }
    if (!칸.length) return '';
    return 작은('<span class="subprice">' + 말글('요금') + ' ' + 칸.join(' · ') + '</span>') +
      (회원권판매() ? 줄(단추(말글('회원권시작'), "구독.회원권구매()", false) + (설정.회원권.연 ? 단추(말글('회원권연시작', { 값: 연값(설정.회원권.연) }), "구독.회원권구매('year')", false) : '')) : '') +
      (typeof 설정.학생인증 === 'function' && (g.학생월 || g.학생연) ? 줄(단추(말글('학생인증단추'), '구독.학생인증()', false)) : '');
  }

  /* ── 결제 고지 — 결제 단추 바로 위 네 줄(2026-10-20) ──
     전자상거래법 13조·Play 구독 정책: 첫 청구일 · 요금과 갱신 주기 · 해지 경로 · 약관·처리방침·환불 링크.
     ⚠️ 결제 길이 아직 없으면(결제사·스토어 모두 없음) ①②③ 을 말하지 않는다 — 되는 척이 된다. 링크 셋만 보인다.
     문서 주소는 설정.문서 로 덮어쓸 수 있다(기본은 medinanum.com 의 공개 문서). */
  function 문서주소(k) {
    var d = 설정.문서 || {};
    if (d[k]) return String(d[k]);
    var app = String(설정.app || '').replace(/[^a-z0-9_-]/g, '');
    if (k === '약관') return 'https://medinanum.com/terms' + (app === 'yakjido' ? '-yakjido' : '') + '.html';
    if (k === '환불') return 'https://medinanum.com/refund.html';
    return 'https://medinanum.com/privacy-' + app + '.html';
  }
  function 문서링크() {
    var a = [['약관', '약관'], ['처리방침', '처리방침'], ['환불안내', '환불']];
    var h = [];
    for (var i = 0; i < a.length; i++) {
      h.push('<a href="' + esc(문서주소(a[i][1])) + '" target="_blank" rel="noopener">' + esc(말글(a[i][0])) + '</a>');
    }
    return h.join(' · ');
  }
  function 결제고지(끝, plan) {
    if (!결제있나() && !검토) return 작은(문서링크());
    var 주기 = 말글(plan === 'year' ? '고지주기연' : '고지주기월');
    var 값 = plan === 'year' && 설정.가격 && 설정.가격.연 ? 첫연값() : 첫월값();
    var 줄들 = [
      끝 ? 말글('고지첫결제', { 날: 날(끝), 값: 값 }) : 말글('고지첫결제날없음', { 값: 값 }),
      말글('고지갱신', { 주기: 주기 }),
      말글(껍데기결제() || !결제있나() ? '고지해지스토어' : '고지해지앱'),   /* 출시 경로가 스토어다 — 검토 미리 보기도 그 말로 */
      말글('고지복원')
    ];
    if (!결제있나()) 줄들.unshift(말글('고지검토'));   /* 검토 주소에서만 — 사실(지금은 결제되지 않음)을 먼저 */
    var h = '<ul class="subnotice">';
    for (var i = 0; i < 줄들.length; i++) h += '<li>' + 줄들[i] + '</li>';
    return h + '</ul>' + 작은(문서링크());
  }

  /* ── 서버 — 서버 부품의 공개 손잡이만 ── */
  function 서버있나() { return 계정있나() && !!(window.서버 && typeof window.서버.준비 === 'function' && typeof window.서버.세션 === 'function'); }
  function 세션() { try { return 서버있나() ? window.서버.세션() : null; } catch (e) { return null; } }
  function 사용자() { var s = 세션(); return s && s.user ? s.user.id : null; }
  function 저장키() { return '_sub_' + 설정.app; }
  function 읽기() {
    var o = null; try { o = JSON.parse(localStorage.getItem(저장키()) || 'null'); } catch (e) {}
    if (!o || typeof o !== 'object') return null;
    var u = 사용자(); if (u && o.user && o.user !== u) return null;   /* 다른 계정의 것은 쓰지 않는다 */
    return o;
  }
  function 쓰기(o) { try { if (o) localStorage.setItem(저장키(), JSON.stringify(o)); else localStorage.removeItem(저장키()); } catch (e) {} }
  function 때(v) { if (v == null || v === '') return null; var n = typeof v === 'number' ? v : Date.parse(v); return isNaN(n) ? null : n; }
  function 바뀜알림() {
    if (typeof 설정.바뀜 === 'function') { try { 설정.바뀜(상태()); } catch (e) {} }
    try { var el = document.getElementById('subman'); if (el) el.outerHTML = 관리HTML(); } catch (e) {}
  }
  function 조회() {
    if (!켜짐() || !서버있나()) return Promise.resolve(null);
    if (조회중) return 조회중;
    조회중 = window.서버.준비().then(function (sb) {
      var s = 세션(); if (!sb || !s) return null;
      return sb.rpc('subscription_status', { p_app: 설정.app }).then(function (r) {
        if (r && r.error) return null;
        var row = r ? (Array.isArray(r.data) ? r.data[0] : r.data) : null;
        var 회 = !!(row && /^pass_/.test(String(row.plan || '')));   /* 2026-10-21 서버가 회원권 줄을 돌려주면 plan 이 pass_month · pass_year */
        var o = row ? { status: row.status || null, plan: 회 ? String(row.plan).slice(5) : (row.plan || null), 회원권: 회, 초대: !!(row && row.plan === 'invite'), source: row.source || null, until: 때(row.until),
                        started_at: 때(row.started_at), converts_at: 때(row.converts_at), cancel: !!row.cancel_at_period_end,
                        pay_ready: !!row.pay_ready } : { status: null };
        o.user = s.user ? s.user.id : null; o.at = Date.now();
        쓰기(o); 바뀜알림(); return o;
      });
    }).catch(function () { return null; }).then(function (o) { 조회중 = null; return o; });
    return 조회중;
  }
  /* ── 스토어 영수증 요약(2026-10-13) — 껍데기.결제.상태() 의 요약만 기기에 둔다 ── */
  function 스토어키() { return '_sub_store_' + 설정.app; }
  function 스토어읽기() {
    if (!껍데기결제()) return null;
    var o = null; try { o = JSON.parse(localStorage.getItem(스토어키()) || 'null'); } catch (e) {}
    return o && typeof o === 'object' ? o : null;
  }
  function 스토어쓰기(r) {
    if (!r) return null;
    var o = { 활성: !!r.활성, 체험: !!r.체험, 갱신: r.갱신 !== false, 만료: 때(r.만료), 상품: String(r.상품id || (r.상품 && r.상품[0]) || ''), at: Date.now() };
    if (Array.isArray(r.권한) && r.권한.indexOf(회원권권한) >= 0) { o.활성 = true; o.회원권 = true; if (r.회원권만료) o.만료 = 때(r.회원권만료); if (r.회원권상품) o.상품 = String(r.회원권상품); }   /* 2026-10-21 회원권이 살아 있으면 이 앱도 열림 */
    if (!o.활성 && !o.만료) { try { localStorage.removeItem(스토어키()); } catch (e) {} return null; }   /* 산 적 없음 */
    try { localStorage.setItem(스토어키(), JSON.stringify(o)); } catch (e) {}
    return o;
  }
  var 스토어조회중 = null;
  function 스토어조회() {
    var 결 = 껍데기결제(); if (!결 || typeof 결.상태 !== 'function') return Promise.resolve(null);
    if (스토어조회중) return 스토어조회중;
    스토어조회중 = Promise.resolve().then(function () { return 결.상태(); })
      .then(function (r) { var o = 스토어쓰기(r); 바뀜알림(); return o; }, function () { return null; })
      .then(function (o) { 스토어조회중 = null; return o; });
    return 스토어조회중;
  }
  function 스토어상태(now) {
    var 스 = 스토어읽기(); if (!스) return null;
    var 열 = 스.활성 && (!스.만료 || 스.만료 > now);
    return { 로그인: !!세션(), status: 스.체험 ? 'trial' : 'active', plan: /_year/.test(스.상품) ? 'year' : 'month', source: 'google', 회원권: !!스.회원권,
             until: 스.만료, converts_at: 스.체험 ? 스.만료 : null, cancel: !스.갱신, pay_ready: true,
             days: 스.만료 ? Math.max(0, Math.ceil((스.만료 - now) / 864e5)) : null, 열림: 열, at: 스.at, 스토어: true };
  }
  function 상태() {
    var now = Date.now(), 스 = 스토어상태(now);
    if (스 && 스.열림) return 스;   /* 스토어 영수증이 열려 있으면 그것으로 */
    var o = 계정있나() ? 읽기() : null;   /* 계정이 없는 앱은 남은 저장값도 보지 않는다 */
    if (!o || (!o.status && 스)) return 스 || { 로그인: !!세션(), status: null, 열림: false };
    var 기한 = o.until ? o.until > now : o.status === 'active';
    return { 로그인: !!세션(), status: o.status, plan: o.plan, 회원권: !!o.회원권, 초대: !!o.초대, source: o.source || null, until: o.until, converts_at: o.converts_at, cancel: !!o.cancel,
             pay_ready: !!o.pay_ready, days: o.until ? Math.max(0, Math.ceil((o.until - now) / 864e5)) : null,
             열림: (o.status === 'trial' || o.status === 'active') && 기한, at: o.at };
  }

  /* ── 기기 표식 — 임의값 32바이트를 한 번 만들어 두고, 그 SHA-256 만 보낸다(개인정보 아님) ── */
  function hex(a) { var s = ''; for (var i = 0; i < a.length; i++) s += (a[i] < 16 ? '0' : '') + a[i].toString(16); return s; }
  function 기기표식() {
    return new Promise(function (res) {
      try {
        var raw = null; try { raw = localStorage.getItem('_sub_dev'); } catch (e) {}
        if (!raw || !/^[0-9a-f]{64}$/.test(raw)) {
          var b = new Uint8Array(32); crypto.getRandomValues(b); raw = hex(b);
          try { localStorage.setItem('_sub_dev', raw); } catch (e) {}
        }
        if (!(window.crypto && crypto.subtle && window.TextEncoder)) return res(null);
        crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw)).then(function (d) { res(hex(new Uint8Array(d))); }, function () { res(null); });
      } catch (e) { res(null); }
    });
  }

  /* ── 판단 ── */
  function 열림(id) {
    if (!켜짐()) return true;
    if (응급(id)) return true;
    if (!설정.잠금 || !Object.prototype.hasOwnProperty.call(설정.잠금, id)) return true;   /* 잠금 목록에 없는 것은 연다 */
    try { if (typeof 설정.면제 === 'function' && 설정.면제()) return true; } catch (e) {}
    return 상태().열림;
  }

  /* ── 시트 ── */
  var 내시트 = null;
  function 시트열기(html, 제목) {
    if (typeof 설정.시트열기 === 'function') { try { return 설정.시트열기(html, 제목); } catch (e) {} }
    시트닫기();   /* 앱이 시트를 주지 않았을 때만 — 색·크기는 앱 것을 물려받는다 */
    var v = document.createElement('div'); v.id = 'subsheet'; v.setAttribute('role', 'dialog'); v.setAttribute('aria-modal', 'true'); v.setAttribute('aria-label', 제목 || 말글('구독'));
    v.style.cssText = 'position:fixed;left:0;right:0;bottom:0;max-height:85vh;overflow:auto;z-index:2147482000;padding:16px;background:inherit;border-top:1px solid rgba(0,0,0,.15)';
    v.innerHTML = '<div class="srvbox"><b>' + esc(제목 || '') + '</b>' + html + '</div>';
    document.body.appendChild(v); 내시트 = v;
  }
  function 시트닫기() {
    if (내시트) { try { 내시트.remove(); } catch (e) {} 내시트 = null; return; }
    if (typeof 설정.시트닫기 === 'function') { try { 설정.시트닫기(); } catch (e) {} }
  }
  function 동의줄(id) {
    var 끝 = Date.now() + 7 * 864e5;
    return '<label class="subagree"><input type="checkbox" id="' + id + '"> <span>' + (연있나() ? 말글('동의둘', { 날: 날(끝), 값: 두요금() }) : 말글(결제있나() ? '동의' : '동의준비', { 날: 날(끝), 값: 첫월값() })) + '</span></label>';
  }
  function 결제줄(s) {
    if (껍데기결제()) {
      /* 2026-10-08 스토어 결제 — 체험 전에는 「14일 체험 시작」이 곧 스토어 구매라 단추를 겹치지 않는다. 끝난 뒤(체험 끝·기간 끝)에만 「다시 구독하기」 */
      return (s && s.status && !s.열림) ? 줄(단추(말글('다시구독'), '구독.결제등록()', true) + (연있나() ? 단추(말글('연구독', { 값: 첫연값() }), "구독.결제등록('year')", false) : '')) : '';
    }
    if (결제있나()) {
      /* 결제사가 붙은 뒤: 설정.결제.등록() 이 결제수단 등록 창을 연다 */
      return 줄(단추(말글('결제수단'), '구독.결제등록()', false));
    }
    return 작은(말글('결제준비'));
  }
  function 막힘HTML(id) {
    var s = 상태(), 끝 = Date.now() + 7 * 864e5, 몸 = '', 단 = '', 동 = '';
    var 응 = 문('응급안내', id) || 말글('응급기본');
    var 스토어길 = !!껍데기결제();   /* 2026-10-13 — 스토어 길은 계정 없이도 체험·구독을 시작한다 */
    if (!계정있나() && !스토어길) {
      /* 계정 화면이 없는 앱 — 로그인·체험 시작 글/단추를 보이지 않는다(되는 척 금지) */
      몸 = '<p>' + 말글('계정없음') + '</p><p>' + 전환말(null) + '</p>';
      단 = 단추(말글('닫기'), '구독.닫기()', false);
    } else if (!스토어길 && (!서버있나() || !s.로그인)) {
      몸 = '<p>' + 말글('계정으로') + '</p><p>' + 전환말(끝) + '</p>';
      단 = (typeof 설정.로그인열기 === 'function' ? 단추(말글('로그인하러'), '구독.로그인()', true) : '') + 단추(말글('닫기'), '구독.닫기()', false);
    } else if (!s.status) {
      몸 = '<p>' + 전환말(끝) + '</p>';
      동 = 동의줄('subAgreeT');
      단 = 단추(말글('체험시작'), '구독.체험시작()', true) + (연있나() ? 단추(말글('연시작', { 값: 첫연값() }), "구독.체험시작('year')", false) : '') + 단추(말글('닫기'), '구독.닫기()', false);
    } else {
      몸 = '<p>' + (s.status === 'trial' ? 말글('체험끝') : 말글('기간끝')) + ' ' + 말글('기록그대로') + '</p>';
      단 = 단추(말글('닫기'), '구독.닫기()', false);
    }
    return '<div class="subsheet">' + 문('막힘앞', id) +
      '<p>' + 말글('잠김', { 이름: esc(이름(id)), 은는: 조사(이름(id), '은/는') }) + ' ' + 응 + '</p>' + 몸 + 요금줄() + 동 + 결제고지(끝) + 줄(단) + 결제줄(s) + 문('막힘뒤', id) + '</div>';
  }
  function 막힘(id) {
    if (열림(id)) return true;   /* 꺼짐·응급·열림이면 아무것도 띄우지 않는다 */
    시트열기(막힘HTML(id), 이름(id) || 말글('구독'));
    return false;
  }

  /* ── 체험 · 해지 ── */
  function 이유(k) { var 표 = 글표[말()].이유; return 표[k] || 표.app; }
  var 체험중 = false;
  function 체험시작(plan) {
    if (!켜짐()) return Promise.resolve(false);
    var 칸 = document.getElementById('subAgreeT');
    if (칸 && !칸.checked) { 알림(말글('체크')); try { 칸.focus(); } catch (e) {} return Promise.resolve(false); }
    if (껍데기결제()) return 구매흐름(plan);   /* 스토어 길: 체험은 스토어 상품의 14일 체험. start_trial 은 부르지 않는다 · 2026-10-13 로그인 없이도 */
    if (!계정있나()) { 알림(이유('noacct')); return Promise.resolve(false); }
    if (!서버있나() || !세션()) { 알림(이유('login')); return Promise.resolve(false); }
    if (체험중) return Promise.resolve(false);
    체험중 = true;
    return 기기표식().then(function (dev) {
      if (!dev) { 알림(이유('device')); return false; }
      return window.서버.준비().then(function (sb) { return sb.rpc('start_trial', { p_app: 설정.app, p_device: dev }); }).then(function (r) {
        var d = r && r.data; if (Array.isArray(d)) d = d[0];
        if (r && r.error) { 알림(이유('app')); return false; }
        if (!d || !d.ok) { 알림(이유((d && d.why) || 'app')); return false; }
        return 조회().then(function () { 시트닫기(); 알림(말글('체험됨', { 날: 날(때(d.until) || Date.now() + 7 * 864e5) })); return true; });
      });
    }).catch(function () { 알림(말글('인터넷')); return false; })
      .then(function (x) { 체험중 = false; return x; });
  }
  /* ── 스토어 결제(껍데기) — 구매 · 복원 · 스토어 관리 (2026-10-08) ── */
  var 구매중 = false;
  function 다시조회(n) {   /* 웹훅이 서버 표를 고치는 데 몇 초 걸린다 — 열릴 때까지 몇 번 되읽는다 */
    return 조회().then(function () {
      var s = 상태(); if (s.열림 || n <= 0) return s;
      return new Promise(function (res) { setTimeout(res, 1500); }).then(function () { return 다시조회(n - 1); });
    });
  }
  function 결제오류말(e) {
    var c = e && (e.code || e.why);
    if (c === 'login') return 이유('login');
    if (c === 'network' || c === 'offline') return 말글('인터넷');
    return 말글('결제안됨');
  }
  function 구매흐름(plan, 회원권) {
    var 결 = 껍데기결제(); if (!결) return Promise.resolve(false);
    if (구매중) return Promise.resolve(false);
    구매중 = true;
    return Promise.resolve().then(function () { return 결.구매(회원권 ? 회원권상품(plan) : 상품(plan)); }).then(function (r) {
      if (r && r.취소) { 알림(말글('결제취소')); return false; }
      스토어쓰기(r && r.상태);   /* 2026-10-13 — 스토어 영수증이 곧 열쇠(웹훅을 기다리지 않는다) */
      var 뒤 = 상태().열림 ? Promise.resolve(상태()) : (세션() ? (쓰기(null), 다시조회(4)) : 스토어조회().then(function () { return 상태(); }));
      return 뒤.then(function (s) { 바뀜알림();
        시트닫기();
        알림(s.열림 ? (s.status === 'trial' ? 말글('체험됨', { 날: 날(s.until || Date.now() + 7 * 864e5) }) : 말글('구독됨')) : 말글('결제반영중'));
        return true;
      });
    }).catch(function (e) { 알림(결제오류말(e)); return false; })
      .then(function (x) { 구매중 = false; return x; });
  }
  function 복원() {
    if (!켜짐()) return Promise.resolve(false);
    var 결 = 껍데기결제();
    if (!결 || typeof 결.복원 !== 'function') { 알림(말글('미연결')); return Promise.resolve(false); }
    if (구매중) return Promise.resolve(false);   /* 2026-10-13 — 로그인 없이도(스토어 계정으로 복원) */
    구매중 = true;
    return Promise.resolve().then(function () { return 결.복원(); }).then(function (r) {
      스토어쓰기(r && r.상태);
      if (상태().열림 || !세션()) { 바뀜알림(); return 상태(); }
      쓰기(null); return 다시조회(2);
    })
      .then(function (s) { 알림(s.열림 ? 말글('복원됨') : 말글('복원없음')); return !!s.열림; })
      .catch(function (e) { 알림(결제오류말(e)); return false; })
      .then(function (x) { 구매중 = false; return x; });
  }
  function 스토어관리() {
    var 결 = 껍데기결제();
    if (!결 || typeof 결.관리 !== 'function') { 알림(말글('미연결')); return false; }
    try { 결.관리(상품()); return true; } catch (e) { 알림(말글('문제')); return false; }
  }
  function 해지(취소) {
    if (!켜짐()) return Promise.resolve(false);
    if (껍데기결제()) return Promise.resolve(스토어관리());   /* 스토어 구독은 스토어에서만 끊긴다 — 앱이 해지한 척하지 않는다(로그인과 무관) */
    if (!계정있나()) { 알림(이유('noacct')); return Promise.resolve(false); }
    if (!서버있나() || !세션()) { 알림(이유('login')); return Promise.resolve(false); }
    return window.서버.준비().then(function (sb) { return sb.rpc('cancel_subscription', { p_app: 설정.app, p_cancel: !취소 }); }).then(function (r) {
      if (r && r.error) { 알림(이유('app')); return false; }
      return 조회().then(function () {
        var s = 상태();
        알림(취소 ? 말글('해지취소됨') : 말글('해지됨') + (s.until ? 말글('까지그대로', { 날: 날(s.until) }) : ''));
        return true;
      });
    }).catch(function () { 알림(말글('인터넷')); return false; });
  }

  /* ── 화면 조각 ── */
  function 카드키() { return '_sub_card_' + 설정.app; }
  function 전환카드HTML() {
    if (!켜짐()) return '';
    var s = 상태(); if (s.status !== 'trial' || s.cancel || !s.열림) return '';
    var t = s.converts_at || s.until, now = Date.now(); if (!t || t <= now || t - now > 2 * 864e5) return '';
    var 닫음 = null; try { 닫음 = localStorage.getItem(카드키()); } catch (e) {}
    if (닫음 === String(t)) return '';   /* 이 주기에는 이미 닫았다 */
    var 스토어 = /^(google|apple)$/.test(String(s.source || ''));   /* 2026-10-08 — 스토어에서 산 체험은 스토어가 결제수단을 쥐고 있다 */
    var 글 = ((s.pay_ready || 스토어) && 결제있나()) ? 말글('카드결제', { 날: 날(t), 값: 첫값(s) }) : 말글('카드준비', { 날: 날(t) });   /* 결제사가 없으면 서버가 pay_ready 라 해도 「결제됩니다」를 말하지 않는다 */
    return '<div class="' + 모('카드') + ' subcard" id="subcard" role="status"><p>' + 글 + '</p>' +
      줄(단추(말글('해지자세히'), '구독.관리열기()', false) + 단추(말글('닫기'), '구독.카드닫기()', false, 말글('카드닫기이름'))) + '</div>';
  }
  function 카드닫기() {
    var s = 상태(), t = s.converts_at || s.until;
    try { if (t) localStorage.setItem(카드키(), String(t)); } catch (e) {}
    var el = document.getElementById('subcard'); if (el) el.remove();
  }
  function 관리HTML() {
    if (!켜짐()) return '';
    var s = 상태(), h = '', 스토어길 = !!껍데기결제();
    /* 2026-10-20 — 사는 자리에서만 고지한다(아직 시작 안 함 · 끝남). 구독 중이면 「다음 결제일」이 이미 말한다. */
    var 고지 = (!s.status || !s.열림) ? 결제고지(!s.status ? Date.now() + 7 * 864e5 : null) : '';
    if (!계정있나() && !스토어길) {
      h = '<p>' + 말글('관리계정없음') + '</p><p>' + (결제있나() ? 말글('관리전환', { 값: 첫월값() }) : 말글('다시동의')) + '</p>' + 요금줄();
    } else if (!스토어길 && (!서버있나() || !s.로그인)) {
      h = '<p>' + 말글('관리로그인') + '</p>' + 요금줄() + (typeof 설정.로그인열기 === 'function' ? 줄(단추(말글('로그인하러'), '구독.로그인()', true)) : '');
    } else if (!s.status) {
      h = '<p><b>' + 말글('아직') + '</b></p><p>' + (결제있나() ? (연있나() ? 말글('관리전환둘', { 값: 두요금() }) : 말글('관리전환', { 값: 첫월값() })) : 말글('다시동의')) + '</p>' + 요금줄() + 동의줄('subAgreeT') +
        고지 +
        줄(단추(말글('체험시작'), '구독.체험시작()', true) + (연있나() ? 단추(말글('연시작', { 값: 첫연값() }), "구독.체험시작('year')", false) : ''));
      고지 = '';   /* 단추 위에 이미 넣었다 */
    } else if (s.열림 && s.초대) {   /* 2026-10-21 초대 코드(가입 부품) — 결제가 없다. 날짜만 */
      h = '<p>' + 말글('초대중', { 날: s.until ? 날(s.until) : '—' }) + '</p>' + 작은(말글('초대뒤'));
    } else if (s.열림) {
      var 다음 = s.converts_at || s.until;
      h = '<p><b>' + (s.status === 'active' ? 말글('구독중') : 말글('체험중')) + '</b>' + (s.days != null ? 말글('남음', { n: s.days }) : '') + (s.until ? 말글('까지괄호', { 날: 날(s.until) }) : '') + '</p>' +
        (s.cancel ? '<p>' + 말글('해지예약') + (s.until ? 말글('해지예약뒤', { 날: 날(s.until) }) : '') + '</p>' +
                    줄(단추(말글('해지취소'), '구독.해지취소()', false))
                  : '<p>' + (결제있나() ? 말글('다음결제', { 날: 다음 ? 날(다음) : '—', 값: s.status === 'trial' ? 첫값(s) : 값(s) }) : 말글('다시동의')) + '</p>' + 요금줄() +
                    (껍데기결제()   /* 2026-10-08 — 스토어 구독은 스토어의 구독 관리에서 해지한다(앱의 「해지하기」는 되는 척이 된다) */
                      ? 줄(단추(말글('스토어관리'), '구독.스토어관리()', false)) + 작은(말글('스토어해지', { 날: s.until ? 날(s.until) : 말글('기간끝말') }))
                      : 줄(단추(말글('해지하기'), '구독.해지()', false)) + 작은(말글('해지해도', { 날: s.until ? 날(s.until) : 말글('기간끝말') }))));
    } else {
      h = '<p><b>' + (s.status === 'trial' ? 말글('체험끝') : 말글('기간끝')) + '</b> ' + 말글('기록그대로2') + '</p>' + 요금줄();
    }
    var 복 = 껍데기결제() ? 줄(단추(말글('복원'), '구독.복원()', false)) : '';   /* 폰을 바꿨거나 다시 설치했을 때 — 2026-10-13 로그인 없이도 */
    return '<div id="subman" class="subman">' + h + 고지 + 결제줄(s) + 복 + 문('관리뒤') + '</div>';
  }
  function 가입동의HTML() {
    if (!켜짐() || !계정있나()) return '';
    var 인 = 설정.인증 || {}, 칸 = '';
    /* 휴대폰 인증·공동인증 — 계약 뒤 함수(또는 true)를 주면 단추가 보인다. 지금은 false 라 안 보인다(되는 척 금지). */
    if (인.휴대폰) 칸 += 단추(말글('휴대폰'), "구독.인증('휴대폰')", false);
    if (인.공동) 칸 += 단추(말글('공동'), "구독.인증('공동')", false);
    return '<div class="subjoin">' + 동의줄('subAgree') + 줄(칸) + '</div>';
  }

  /* ── 설치 ── */
  function 설치(o) {
    o = o || {};
    ['app', '유료화', '가격', '회원권', '면제', '결제사', '결제', '인증', '시트열기', '시트닫기', '알림', '로그인열기', '바뀜', '계정', '말', '학생인증'].forEach(function (k) { if (k in o) 설정[k] = o[k]; });
    if (o.모양) 설정.모양 = o.모양;
    설정.문구 = o.문구 && typeof o.문구 === 'object' ? o.문구 : {};
    설정.응급 = (o.응급 || []).slice();
    설정.잠금 = {};
    Object.keys(o.잠금 || {}).forEach(function (id) {
      if (응급(id)) { try { console.warn('구독 부품: 응급 기능은 잠글 수 없어요 —', id); } catch (e) {} return; }
      var v = o.잠금[id];
      설정.잠금[id] = v && typeof v === 'object' ? v : String(v);   /* 이름 — 글 또는 {ko,en} */
    });
    if (설치됨) return;
    설치됨 = true;
    try {
      var css = document.createElement('style');
      css.textContent = '.subagree{display:flex;gap:10px;align-items:flex-start;min-height:44px;padding:8px 0;cursor:pointer;line-height:1.6}' +
        '.subagree input{flex:none;width:22px;height:22px;margin:2px 0 0}.subsheet p,.subman p,.subcard p{margin:0 0 8px}' +
        /* 2026-10-20 결제 고지 — 점 없이 줄마다 「첫 결제 —」 같은 이름이 붙어 있어 목록 점을 쓰지 않는다 */
        '.subnotice{margin:8px 0 10px;padding:0;list-style:none;font-size:14px;line-height:1.65}' +
        '.subnotice li{margin:0 0 6px}.subnotice li:last-child{margin:0}';
      document.head.appendChild(css);
    } catch (e) {}
    /* 계정 단추를 감싼다 — 가입 동의 체크(켜짐일 때만) · 「지금 동기화」 잠금 · 로그인하면 상태 읽기 · 로그아웃하면 지우기 */
    if (typeof window.계정동작 === 'function' && !window.계정동작.__구독) {
      var 원 = window.계정동작;
      var 싼 = function (what) {
        if (켜짐() && 계정있나() && what === 'signup') {
          var 칸 = document.getElementById('subAgree');
          if (칸 && !칸.checked) { 알림(말글('체크')); try { 칸.focus(); } catch (e) {} return; }
        }
        if (what === 'sync' && 설정.잠금.sync && !열림('sync')) return 막힘('sync');
        var r = 원.apply(this, arguments);
        if (what === 'logout' || what === 'delete') Promise.resolve(r).then(function () { if (!세션()) 쓰기(null); });
        if (켜짐() && (what === 'login' || what === 'signup')) Promise.resolve(r).then(function () { setTimeout(function () { 조회(); 스토어조회(); }, 300); });   /* 스토어조회 → 껍데기가 그 계정으로 logIn(로그인 전 구매가 계정에 붙는다) */
        return r;
      };
      싼.__구독 = 1; window.계정동작 = 싼;
    }
    /* 켜진 창에서만, 전에 로그인한 적이 있으면 상태를 읽어 둔다(첫 화면은 늦추지 않는다) */
    if (켜짐() && 서버있나()) {
      setTimeout(function () {
        var st = {}; try { st = window.서버.상태() || {}; } catch (e) {}
        if (st.email || 세션()) 조회();
      }, 1800);
    }
    /* 2026-10-08 — 껍데기(스토어 결제)는 맨 마지막 스크립트라 이 부품보다 늦게 온다. 오면 열린 관리 화면만 다시 그린다(꺼짐이면 아무것도 안 한다). */
    try { document.addEventListener('껍데기준비', function () { if (켜짐()) { 바뀜알림(); 스토어조회(); } }); } catch (e) {}   /* 2026-10-13 — 영수증도 읽는다 */
  }

  window.구독 = {
    판: 판, 설치: 설치, 켜짐: 켜짐, 열림: 열림, 막힘: 막힘, 상태: 상태, 조회: 조회,
    체험시작: 체험시작, 해지: function () { return 해지(false); }, 해지취소: function () { return 해지(true); },
    전환카드HTML: 전환카드HTML, 카드닫기: 카드닫기, 관리HTML: 관리HTML, 가입동의HTML: 가입동의HTML,
    관리열기: function () { 시트열기(관리HTML(), 말글('구독')); 스토어조회(); },
    닫기: 시트닫기,
    로그인: function () { 시트닫기(); try { if (계정있나() && typeof 설정.로그인열기 === 'function') 설정.로그인열기(); } catch (e) {} },
    결제등록: function (plan) {   /* ⬅ 결제사 붙일 자리 — 2026-10-08: 스토어 껍데기가 있으면 스토어 구매 · 10-13 plan 'year' 면 1년 */
      if (껍데기결제()) return 구매흐름(plan);
      if (!설정.결제사 || !설정.결제 || typeof 설정.결제.등록 !== 'function') { 알림(말글('결제준비짧게')); return; }
      try { 설정.결제.등록(); } catch (e) { 알림(말글('문제')); }
    },
    회원권구매: function (plan) { if (!회원권판매()) { 알림(말글('곧')); return Promise.resolve(false); } return 구매흐름(plan, true); },
    회원권판매: 회원권판매,
    복원: 복원, 스토어관리: 스토어관리, 결제종류: function () { return 껍데기결제() ? 'store' : (결제있나() ? 'pg' : null); }, 상품: 상품,
    학생인증: function () {   /* ⬅ 학생 인증 화면 붙일 자리 */
      if (typeof 설정.학생인증 !== 'function') { 알림(말글('미연결')); return; }
      try { 설정.학생인증(); } catch (e) { 알림(말글('문제')); }
    },
    인증: function (종류) {
      var f = (설정.인증 || {})[종류];
      if (typeof f === 'function') { try { return f(); } catch (e) {} }
      알림(말글('미연결'));
    },
    말: 말, 응급인가: 응급, 잠금목록: function () { return Object.keys(설정.잠금); }, 조사: 조사, 결제있나: 결제있나
  };
})();
/* ▲▲ 구독 부품 끝 ▲▲ */

/* 약지도 — 두 폰 합치기(app-shell 의 sanitizeMe 를 씀). 2026-10-13 상용화 점검 */
window.mergeMe = function (localRaw, serverRaw) {
  let a, b; try { a = sanitizeMe(JSON.parse(localRaw)); b = sanitizeMe(JSON.parse(serverRaw)); } catch (e) { return null; }
  const ma = a._mt || {}, mb = b._mt || {}, out = {}, mt = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]); keys.delete('_mt');
  const dayUnion = (x, y, f) => { const r = { ...(y || {}) }; for (const [d, v] of Object.entries(x || {})) r[d] = r[d] ? f(v, r[d]) : v; return r; };
  for (const k of keys) {
    if (k === 'taken') out.taken = dayUnion(a.taken, b.taken, (x, y) => [...new Set([...y, ...x])]);
    else if (k === 'skipped') out.skipped = dayUnion(a.skipped, b.skipped, (x, y) => [...new Set([...y, ...x])]);   /* 건너뜀도 날마다 합침 — 다른 폰에서 먹었어요면 아래에서 뺀다 */
    else if (k === 'prnLog') out.prnLog = dayUnion(a.prnLog, b.prnLog, (x, y) => { const s = new Set(y.map(e => e.id + '@' + e.t)); return [...y, ...x.filter(e => !s.has(e.id + '@' + e.t))]; });
    else if (k === 'days') out.days = dayUnion(a.days, b.days, (x, y) => (x.n >= y.n ? x : y));
    else out[k] = (ma[k] || 0) >= (mb[k] || 0) ? (k in a ? a[k] : b[k]) : (k in b ? b[k] : a[k]);
    mt[k] = Math.max(ma[k] || 0, mb[k] || 0);
  }
  /* 한 폰은 「먹었어요」, 다른 폰은 「건너뜀」이면 먹었어요가 이긴다 */
  if (out.skipped && out.taken) for (const d of Object.keys(out.skipped)) { const t = new Set(out.taken[d] || []); out.skipped[d] = out.skipped[d].filter(x => !t.has(x)); if (!out.skipped[d].length) delete out.skipped[d]; }
  out._mt = mt;
  return JSON.stringify(sanitizeMe(out));
};
try {
  /* 준비됨 = meta.json 의 account 스위치 — 공용 서버에 약지도 칸(메디나눔_약지도_추가_1013.sql)이 열린 뒤에 true 로 켠다. 그 전엔 「준비 중」 한 줄(되는 척 금지). */
  서버.설치({ app: 'yakjido', 열쇠: /^yakjido\.(me|fam|hx)\.v1$/, 병합: function (k, mine, theirs) { return k === 'yakjido.me.v1' && typeof mergeMe === 'function' ? mergeMe(mine, theirs) : null; },   /* 11-03 fam.v1 = 알림 설정(시간대·기다리는 시간·쉬는 시간·정시 알림) — 서버 알림 함수가 읽는다 */ 준비됨: function () { return !!(typeof D !== 'undefined' && D.meta && D.meta.account === true); }, 허용: srvAgreed, 다시그리기: srvReload,
    가입확인: { 글: '만 14세 이상이에요', 설명: '메디나눔 계정은 만 14세 이상만 만들 수 있어요. 아이 약은 보호자 계정에 담아 주세요.' },
    /* 2026-10-14 로그인 문의 「서버에 저장하기」 체크 — 설정의 서버동의켜기와 같은 꼴로 적는다 */
    동의기록: function () { try { localStorage.setItem(AGREE_KEY, JSON.stringify({ server: true, at: new Date().toISOString() })); } catch (e) {} } });
} catch (e) {}

/* 2026-10-22 공용 구독 부품(다섯 앱 같은 것) — 유료화 스위치는 끈 채로. 꺼져 있는 동안 요금·체험 글은 어디에도 나오지 않는다(되는 척 금지). 검토는 주소에 ?paywall=1.
   요금 = 10-21 결정(앱 하나 월 5,900 · 연 49,000 / 출시 기념가 4,900 · 39,900 / 회원권). 무료로 남는 것 = 10-22 현욱님 답 9번(약 찾기·약봉투 읽기·복약 알림·안전 신호·겹침 확인).
   잠금 목록 = 현욱님 10-22 답 A(기록을 쌓아 보는 것만). */
try {
  구독.설치({ app: 'yakjido', 유료화: false,
    가격: { 월: 5900, 연: 49000, 출시: { 월: 4900, 연: 39900 } },
    회원권: { 월: 12900, 연: 99000, 출시월: 9900, 출시연: 79000, 판매: false },
    잠금: { sync: '여러 기기에서 이어 보기', trend: '혈압·혈당 2주 흐름 그림', visitdoc: '진료실 한 장 종이로 뽑기', rx: '처방약 길잡이' },   /* 10-22 현욱님 잠금 A — 약 개수로는 막지 않는다 */
    응급: ['emergency', 'redflag', 'call119', 'find', 'bag', 'schedule', 'together'],
    문구: { 응급안내: '약 찾기·약봉투 읽기·복약 알림·응급 신호와 겹침 확인은 언제나 열려 있어요.' },
    결제사: null, 인증: { 휴대폰: false, 공동: false },
    시트열기: function (html, 제목) { var v = document.getElementById('view'); if (!v) return; v.innerHTML = topBar({ back: '뒤로' }) + '<h1>' + esc(제목 || '구독') + '</h1>' + html; scrollTo(0, 0); },
    시트닫기: function () { route(); },
    알림: function (t) { try { toast(t); } catch (e) {} },
    로그인열기: function () { go('/login'); },
    바뀜: function () { try { if (/^#\/me/.test(location.hash)) route(); } catch (e) {} } });
} catch (e) {}
/* 다섯 언어(10-27) — 설정의 언어·나라 칸. 언어를 바꾸면 다시 연다. 나라는 응급·위기 번호를 고른다(요청서 표) */
window.언어칸 = function () {
  var LN = [['ko', '한국어'], ['en', 'English'], ['es', 'Español'], ['ja', '日本語'], ['zh', '简体中文']];
  var CN = [['KR', '한국 · 119'], ['US', 'USA · 911'], ['ES', 'España · 112'], ['JP', '日本 · 119'], ['CN', '中国 · 120']];
  var b = function (on, js, t) { return '<button type="button" class="' + (on ? 'on' : '') + '" aria-pressed="' + on + '" onclick="' + js + '">' + t + '</button>'; };
  return '<section class="sec card" style="margin-top:16px"><h2>언어 · Language</h2><div class="fs-seg lang-seg" role="group" aria-label="언어" style="flex-wrap:wrap">' + LN.map(function (x) { return b(window.LANG === x[0], "setLang('" + x[0] + "')", x[1]); }).join('') + '</div>' +
    '<p class="small muted" style="margin-top:10px">사는 나라 · Country — 응급 번호</p><div class="fs-seg lang-seg" role="group" aria-label="나라" style="flex-wrap:wrap">' + CN.map(function (x) { return b(window.CC === x[0], "setLang(window.LANG,'" + x[0] + "')", x[1]); }).join('') + '</div>' +
    (window.설정판 && 설정판.말과나라열기 ? '<button type="button" class="link" style="margin-top:10px;min-height:44px" onclick="설정판.말과나라열기()">말과 나라 · 그 나라 말을 얼마나 하는지</button>' : '') + '</section>';
};
/* ▼▼ 대화 부품 시작 ▼▼ */
/* ═══ 메디나눔 대화 부품 — AI 없이 «대화하는 느낌» (2026-10-27 Main · 요청서 docs/requests/20261027_메디나눔_전앱_대화형.md) ═══
   하는 일 두 가지(모두 기기 안 — 서버·AI 없음, 기내에서도 됨):
   ① 이해: 사람이 친 한 문장에서 «값»(체온·나이·몸무게·시간·횟수·약 이름)을 뽑고, 앱이 준 «뜻» 목록 가운데 가장 가까운 것을 고른다.
      위험 판정은 앱의 기존 함수(설정.위험)를 «맨 먼저» 부른다 — 위험이면 뜻 고르기를 하지 않는다.
   ② 화면: 말풍선 · 입력 중 점 셋 · 답 칩(2~4개) · 직접 쓰기 · 같은 대화 기억 · 다시 열면 「이어서 할까요?」.
   쓰는 법:
     var 봇 = 대화.만들기({
       앱:'kids', 언어:'ko',
       뜻:[{ id:'fever', 예문:['애가 열이 나요','열이 39도','몸이 뜨거워요'], 태그:['열','발열','고열'] }, …],
       약:['타이레놀','아세트아미노펜','이부프로펜','부루펜'],              // 이름 뽑기용(앱이 준다)
       위험: function(글, 값){ return null 또는 {말:'지금 119 …', 전화:'119'} },   // 앱의 기존 위험 판정
       처리: function(입력, 상태){ return { 말:['…'], 칩:['예','아니요'], 끝:false } }   // 한 번에 한 질문
     });
     봇.붙이기(document.getElementById('chat'));   // 화면 그리기
     봇.이해('애가 39.2도인데 해열제 먹였어')      // → {값:{체온:39.2, 약:[]}, 뜻:[{id,점수}], 위험:null}
*/
(function () {
  if (window.대화) return;
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function 고름(s) { return String(s || '').toLowerCase().replace(/\s+/g, ''); }
  var 한수 = { '한': 1, '하나': 1, '두': 2, '둘': 2, '세': 3, '셋': 3, '네': 4, '넷': 4, '다섯': 5, '여섯': 6, '일곱': 7, '여덟': 8, '아홉': 9, '열': 10 };
  var 날수 = { '하루': 1, '이틀': 2, '사흘': 3, '나흘': 4, '닷새': 5, '엿새': 6, '이레': 7, '열흘': 10 };

  /* ── 값 뽑기 ── 숫자 표기·단위·띄어쓰기 흔들림을 받아 준다. 못 뽑으면 넣지 않는다(짐작 금지). */
  function 값뽑기(글, 약목록) {
    var t = String(글 || '').replace(/[，]/g, ',').replace(/℃/g, '도').replace(/°\s*c/gi, '도');
    var v = {}, m;
    m = t.match(/(3[4-9]|4[0-3])(?:[.,]([0-9]))?\s*(?:도|度|grados?|degrees?)/i) || t.match(/(?:체온|열|temp|fiebre|熱|体温|发烧|發燒)\D{0,6}(3[4-9]|4[0-3])(?:[.,]([0-9]))?/i);
    if (m) v.체온 = parseFloat(m[1] + (m[2] ? '.' + m[2] : ''));
    if ((m = t.match(/(1?[0-9]{2}|[0-9])(?:[.,]([0-9]))?\s*(?:kg|킬로|키로|kilo)/i))) v.몸무게 = parseFloat(m[1] + (m[2] ? '.' + m[2] : ''));
    if ((m = t.match(/(?:생후\s*)?([0-9]{1,2})\s*(?:개월|달|months?|meses|か月|ヶ月|个月|個月)/i))) v.나이개월 = +m[1];
    else if ((m = t.match(/(?:만\s*)?([0-9]{1,3})\s*(?:살|세|years?\s*old|años|歳|岁|歲)/i))) v.나이개월 = +m[1] * 12;
    else if ((m = t.match(/([1-9]0)\s*대/))) v.나이개월 = +m[1] * 12;
    else if ((m = t.match(/(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\s*살/))) v.나이개월 = 한수[m[1]] * 12;
    if ((m = t.match(/([0-9]{1,2})\s*(?:시간|hours?|horas?|時間|小时|小時)/i))) v.시간 = +m[1];
    else if ((m = t.match(/([0-9]{1,2})\s*(?:일|days?|días?|日|天)\s*(?:째|전|동안|정도|넘게)?/i)) && !/[0-9]\s*일\s*(?:에|날)/.test(t)) v.시간 = +m[1] * 24;
    else if ((m = t.match(/(?:^|[\s,])(하루|이틀|사흘|나흘|닷새|엿새|이레|열흘)\s*(?=째|동안|전|넘게|정도|이상|가\s*지|됐|지났|간)/))) v.시간 = 날수[m[1]] * 24;   /* 「하루 세 번」·「타이레놀」 같은 것은 기간이 아니다 */
    else if (/어제|yesterday|ayer|昨日|昨天/.test(t)) v.시간 = 24;
    if ((m = t.match(/([0-9]{1,2}|한|두|세|네|다섯)\s*(?:번|회|times|veces|回|次)/i))) v.횟수 = 한수[m[1]] || +m[1];
    if (약목록 && 약목록.length) {
      var g = 고름(t), 찾음 = [];
      약목록.forEach(function (n) { if (n && g.indexOf(고름(n)) >= 0 && 찾음.indexOf(n) < 0) 찾음.push(n); });
      if (찾음.length) v.약 = 찾음;
    }
    return v;
  }

  /* ── 뜻 고르기 ── 찾기 부품이 있으면 그것으로(띄어쓰기·조사·초성), 없으면 낱말 겹침 */
  function 뜻색인(뜻) {
    if (window.찾기 && typeof window.찾기.만들기 === 'function') {
      try { return window.찾기.만들기({ 항목: 뜻.map(function (d) { return { id: d.id, 제목: (d.예문 || [])[0] || d.id, 별칭: (d.예문 || []).slice(1), 태그: d.태그 || [] }; }) }); } catch (e) {}
    }
    return null;
  }
  function 뜻고르기(봇, 글) {
    if (봇.색인) { try { return 봇.색인.찾기(글, { 최대: 3 }).map(function (r) { return { id: r.id, 점수: r.점수 }; }); } catch (e) {} }
    var g = 고름(글), 결과 = [];
    봇.설정.뜻.forEach(function (d) {
      var s = 0; (d.태그 || []).concat(d.예문 || []).forEach(function (w) { if (w && g.indexOf(고름(w)) >= 0) s += 고름(w).length; });
      if (s) 결과.push({ id: d.id, 점수: s });
    });
    return 결과.sort(function (a, b) { return b.점수 - a.점수; }).slice(0, 3);
  }

  var 기본말 = {
    ko: { 입력: '편하게 적어 주세요', 보내기: '보내기', 직접: '직접 쓰기', 모름: '제가 아직 그 말을 잘 몰라요. 이렇게 물어보시겠어요?', 이어: '지난번 이야기를 이어서 할까요?', 예: '이어서 할게요', 새: '새로 시작', 생각: '생각하는 중' },
    en: { 입력: 'Type in your own words', 보내기: 'Send', 직접: 'Type instead', 모름: "I don't know that phrase yet. Could you ask it like one of these?", 이어: 'Pick up where we left off?', 예: 'Continue', 새: 'Start over', 생각: 'Thinking' },
    es: { 입력: 'Escríbalo con sus palabras', 보내기: 'Enviar', 직접: 'Escribir', 모름: 'Todavía no conozco esa expresión. ¿Puede preguntarlo de una de estas formas?', 이어: '¿Seguimos donde lo dejamos?', 예: 'Seguir', 새: 'Empezar de nuevo', 생각: 'Pensando' },
    ja: { 입력: 'ご自由に入力してください', 보내기: '送信', 직접: '自分で入力', 모름: 'その言い方はまだよく分かりません。次のように聞いてみてください。', 이어: '前回の続きから話しますか？', 예: '続ける', 새: '最初から', 생각: '考えています' },
    zh: { 입력: '请用自己的话写下来', 보내기: '发送', 직접: '自己输入', 모름: '我还不太懂这个说法。可以换成下面这样问吗？', 이어: '要接着上次的话题吗？', 예: '继续', 새: '重新开始', 생각: '正在思考' }
  };
  var CSS = '.mnc{display:flex;flex-direction:column;gap:8px}.mnc-log{display:flex;flex-direction:column;gap:8px}' +
    '.mnc-b{max-width:86%;padding:11px 14px;border-radius:18px;line-height:1.55;font-size:calc(15px * var(--fs,1));word-break:keep-all;overflow-wrap:anywhere;white-space:pre-line}' +
    '.mnc-b.bot{align-self:flex-start;background:var(--card,#F3F4F2);border:1px solid var(--line,rgba(0,0,0,.08));border-bottom-left-radius:6px}' +
    '.mnc-b.me{align-self:flex-end;background:var(--teal,#1F6F6B);color:#fff;border-bottom-right-radius:6px}' +
    '.mnc-b.sos{border:2px solid #C0392B;background:#FDECEA;color:#5A1209}.mnc-b.sos a{display:inline-flex;margin-top:8px;min-height:44px;align-items:center;padding:0 16px;border-radius:12px;background:#C0392B;color:#fff;font-weight:800;text-decoration:none}' +
    '.mnc-dots{align-self:flex-start;display:flex;gap:4px;padding:12px 14px}.mnc-dots i{width:7px;height:7px;border-radius:50%;background:currentColor;opacity:.35;animation:mncd 1s infinite}.mnc-dots i:nth-child(2){animation-delay:.15s}.mnc-dots i:nth-child(3){animation-delay:.3s}' +
    '@keyframes mncd{50%{opacity:.9;transform:translateY(-3px)}}@media (prefers-reduced-motion:reduce){.mnc-dots i{animation:none}}' +
    '.mnc-chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end}.mnc-chips button{min-height:44px;padding:0 16px;border-radius:22px;border:1px solid var(--teal,#1F6F6B);background:transparent;color:inherit;font:inherit;font-size:calc(15px * var(--fs,1))}' +
    '.mnc-in{display:flex;gap:8px;position:sticky;bottom:0;padding:8px 0;background:var(--surface,#fff)}.mnc-in input{flex:1;min-width:0;font:inherit;font-size:16px;padding:12px 14px;border-radius:22px;border:1px solid var(--line,rgba(0,0,0,.18));background:transparent;color:inherit}' +
    '.mnc-in button{min-width:48px;min-height:48px;border-radius:24px;border:0;background:var(--teal,#1F6F6B);color:#fff;font:inherit;font-weight:700;padding:0 14px}';

  function 만들기(o) {
    var 봇 = { 설정: { 앱: '', 언어: 'ko', 뜻: [], 약: [], 위험: null, 처리: null, 말: {}, 기억: true } };
    for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) 봇.설정[k] = o[k];
    봇.색인 = 뜻색인(봇.설정.뜻 || []);
    var 열쇠 = '_mnchat_' + (봇.설정.앱 || 'x');
    function 말(k) { var L = 기본말[봇.설정.언어] || 기본말.ko; return (봇.설정.말 && 봇.설정.말[k]) || L[k] || 기본말.ko[k]; }
    function 상태읽기() { try { return JSON.parse(localStorage.getItem(열쇠) || 'null'); } catch (e) { return null; } }
    function 사람말있나(s) { return !!(s && s.기록 && s.기록.some(function (r) { return r[0] === 'me'; })); }
    function 상태쓰기(s) { if (!봇.설정.기억 || !사람말있나(s)) return; try { localStorage.setItem(열쇠, JSON.stringify(s)); } catch (e) {} }   /* 사람이 한 마디라도 한 뒤부터 기억(첫 인사만으론 저장 안 함 — 약지도 10-27) */

    봇.이해 = function (글) {
      var 값 = 값뽑기(글, 봇.설정.약), 위 = null;
      try { if (typeof 봇.설정.위험 === 'function') 위 = 봇.설정.위험(String(글 || ''), 값); } catch (e) { 위 = null; }
      return { 글: 글, 값: 값, 위험: 위 || null, 뜻: 위 ? [] : 뜻고르기(봇, 글) };
    };

    봇.붙이기 = function (곳, 첫말) {
      if (!곳) return;
      if (!document.getElementById('mnc-css')) { var st = document.createElement('style'); st.id = 'mnc-css'; st.textContent = CSS; document.head.appendChild(st); }
      곳.innerHTML = '<div class="mnc" role="log" aria-live="polite"><div class="mnc-log"></div><div class="mnc-chips"></div>' +
        '<form class="mnc-in"><input type="text" enterkeyhint="send" aria-label="' + esc(말('입력')) + '" placeholder="' + esc(말('입력')) + '"><button type="submit" aria-label="' + esc(말('보내기')) + '">' + esc(말('보내기')) + '</button></form></div>';
      var 로그 = 곳.querySelector('.mnc-log'), 칩칸 = 곳.querySelector('.mnc-chips'), 폼 = 곳.querySelector('form'), 칸 = 곳.querySelector('input');
      var 상태 = { 값: {}, 단계: 0, 기록: [] };
      function 풍선(글, 누구, 위험) {
        var d = document.createElement('div'); d.className = 'mnc-b ' + (누구 === 'me' ? 'me' : 'bot') + (위험 ? ' sos' : '');
        if (위험) d.innerHTML = esc(위험.말) + (위험.전화 && /^[\d+]/.test(위험.전화) ? '<br><a href="tel:' + esc(위험.전화) + '">' + esc(위험.전화) + '</a>' : '');
        else d.textContent = 글;
        로그.appendChild(d); 상태.기록.push([누구, 위험 ? 위험.말 : 글]); if (상태.기록.length > 60) 상태.기록.shift();
        try { d.scrollIntoView({ block: 'end', behavior: 'smooth' }); } catch (e) {}
      }
      function 칩(목록) {
        칩칸.innerHTML = '';
        (목록 || []).slice(0, 4).forEach(function (c) {
          var b = document.createElement('button'); b.type = 'button'; b.textContent = c;
          b.addEventListener('click', function () { 보냄(c); }); 칩칸.appendChild(b);
        });
      }
      function 봇말(답) {
        var 줄 = [].concat(답 && 답.말 || []), i = 0;
        var 점 = document.createElement('div'); 점.className = 'mnc-dots'; 점.setAttribute('aria-label', 말('생각')); 점.innerHTML = '<i></i><i></i><i></i>';
        function 다음() {
          if (i >= 줄.length) { 칩(답 && 답.칩); 상태쓰기(상태); return; }
          로그.appendChild(점);
          setTimeout(function () { try { 점.remove(); } catch (e) {} 풍선(줄[i++], 'bot'); 다음(); }, Math.min(900, 250 + String(줄[i]).length * 12));
        }
        다음();
      }
      function 보냄(글) {
        글 = String(글 || '').trim(); if (!글) return;
        칩칸.innerHTML = ''; 풍선(글, 'me');
        var 앎 = 봇.이해(글);
        for (var k in 앎.값) if (Object.prototype.hasOwnProperty.call(앎.값, k)) 상태.값[k] = 앎.값[k];
        if (앎.위험) { 풍선('', 'bot', 앎.위험); 상태쓰기(상태); return; }   /* 위험이면 다른 말 없이 안전 안내 먼저 */
        var 답 = null;
        try { 답 = typeof 봇.설정.처리 === 'function' ? 봇.설정.처리(앎, 상태) : null; } catch (e) { 답 = null; }
        if (!답 || !답.말 || !답.말.length) {
          var 가까운 = (봇.설정.뜻 || []).slice(0, 3).map(function (d) { return (d.예문 || [])[0]; }).filter(Boolean);
          답 = { 말: [말('모름')], 칩: 가까운 };
        }
        봇말(답);
      }
      폼.addEventListener('submit', function (ev) { ev.preventDefault(); var v = 칸.value; 칸.value = ''; 보냄(v); });
      var 지난 = 상태읽기();
      if (사람말있나(지난)) {
        봇말({ 말: [말('이어')], 칩: [말('예'), 말('새')] });
        var 원 = 보냄;
        보냄 = function (글) {
          보냄 = 원;
          if (글 === 말('예')) { 상태 = 지난; 칩칸.innerHTML = ''; 지난.기록.slice(-6).forEach(function (r) { 풍선(r[1], r[0]); }); return; }
          try { localStorage.removeItem(열쇠); } catch (e) {}
          칩칸.innerHTML = ''; if (첫말) 봇말(첫말); else return;
          if (글 !== 말('새')) 원(글);
        };
      } else if (첫말) 봇말(첫말);
      봇.보냄 = function (글) { 보냄(글); };
      봇.지우기 = function () { try { localStorage.removeItem(열쇠); } catch (e) {} };
    };
    return 봇;
  }
  window.대화 = { 판: '2026-10-27-1', 만들기: 만들기, 값뽑기: 값뽑기 };
})();
/* ▲▲ 대화 부품 끝 ▲▲ */

/* ═══ 약지도 대화(10-27 · 요청서 20261027_메디나눔_전앱_대화형) — AI 없이 «대화하는 느낌». 모두 기기 안(기내에서도 됨).
   이해·말풍선은 메디나눔 공용 «대화 부품»(위), 뜻·약 이름·위험 판정·답은 여기. 겹침은 «같이 먹어도 되나요» 엔진(ixRun) 그대로 ═══ */
(function () {
  var 짧은이름 = function (n) { return String(n || '').replace(/\(.*?\)/g, '').split(/\s|\d/)[0].replace(/(정|캡슐|연질캡슐|시럽|현탁액|액|산|과립|츄어블정|서방정|이알서방정|필름코팅정|겔|크림|연고|패취|패치)$/, ''); };
  var 이름표 = null;
  function 이름들() {
    if (이름표) return 이름표; 이름표 = {};
    var 넣기 = function (n, id) { n = String(n || '').trim(); if (n.length >= 2 && !이름표[n]) 이름표[n] = id; };
    /* 손으로 단 이름이 먼저 — 「판콜에이」는 페닐레프린이 아니라 복합 감기약(아세트아미노펜이 든) 화면으로 가야 겹침이 보인다 */
    [['타이레놀', 'acetaminophen'], ['부루펜', 'ibuprofen'], ['애드빌', 'ibuprofen'], ['이지엔', 'ibuprofen'], ['탁센', 'naproxen'], ['아스피린', 'aspirin'], ['맥시부펜', 'dexibuprofen'], ['챔프', 'acetaminophen'], ['판콜', 'pancol-a'], ['판피린', 'panpyrin-t'], ['테라플루', 'theraflu'], ['콜대원', 'coldaewon'], ['게보린', 'geworin'], ['펜잘', 'penzal'], ['그날엔', 'gnalen'], ['타이레놀콜드', 'tylenol-cold']].forEach(function (x) { 넣기(x[0], x[1]); });
    /* 성분 화면 이름은 괄호를 뗀 통째로만(괄호 안은 「마른기침」「두드러기」 같은 쓰임새라 약 이름이 아니다). 제품 하나짜리 화면(「판콜에이 내복액」)은 앞 낱말도. 제품 이름은 그다음 — 복합제 화면 이름이 성분 화면의 제품 목록보다 먼저 */
    (D.drugs || []).forEach(function (d) { 넣기(String(d.name).replace(/\s*\(.*?\)/g, ''), d.id); if ((d.products || []).some(function (p) { return p.name === d.name; })) 넣기(짧은이름(d.name), d.id); if (d.en) 넣기(String(d.en).toLowerCase(), d.id); });
    (D.drugs || []).forEach(function (d) { (d.products || []).forEach(function (p) { 넣기(짧은이름(p.name), d.id); }); });
    return 이름표;
  }
  /* 갈래 낱말 — 제품을 모를 때. 처방약 갈래는 처방약 길잡이로 */
  var 갈래 = { 감기약: { 묻기: '어떤 감기약인지 아세요?', 칩: ['판콜에이', '테라플루', '콜대원'] }, 진통제: { 묻기: '어떤 진통제인지 아세요?', 칩: ['타이레놀', '이부프로펜', '게보린'] }, 해열제: { 묻기: '어떤 해열제인지 아세요?', 칩: ['타이레놀', '이부프로펜'] }, 소화제: { 묻기: '어떤 소화제인지 아세요?', 칩: ['베아제', '훼스탈'] } };
  var 처방갈래 = [['bp', /혈압약|고혈압/], ['dm', /당뇨약|혈당약|메트포르민/], ['chol', /콜레스테롤약|고지혈|스타틴/], ['blood', /와파린|항응고|피\s*묽게|아스피린\s*프로텍트|엘리퀴스|자렐토|릭시아나/], ['thyroid', /갑상선/], ['sleep', /수면제|우울증약|항우울|안정제/]];
  /* 위험 — 앱이 이미 쓰는 판정을 글로 옮긴 것(홈 응급 줄 · 증상 응급 줄 · 아이 3개월 38℃ · 41℃ · 항암 38℃ · 과다복용). 새 기준을 짓지 않는다 */
  var 마음 = /죽고\s*싶|자살|자해|끝내고\s*싶|없어지고\s*싶|사라지고\s*싶|살\s*이유|손목.*그|그었|모아서.*먹|약.*모아/;
  var 응급 = [/가슴.*(쥐어|조이|짓누|아프|답답).*(땀|숨)|가슴.*(쥐어짜|조이듯|짓누르)/, /한쪽.*(힘|마비|저리|처)|말이\s*어눌|얼굴.*(처졌|비뚤)|발음이\s*이상/, /숨.*(차서|막|못\s*쉬|안\s*쉬|가빠|쌕쌕|힘들)/, /(입술|혀|목구멍|얼굴).*(부었|붓고|부어)/, /경련|발작|까무러/, /의식|깨워도|안\s*일어나|축\s*처지/, /피를\s*토|토혈|변이\s*(새)?까|짜장\s*같|짜장처럼/, /머리.*(부딪|다친).*(토|구토)/, /(제일|가장|살면서).*심한\s*두통|벼락\s*두통/, /배가\s*(딱딱|너무\s*아파서\s*못)/];
  /* 이미 많이 먹었다·삼켰다(10-28 곁에 교훈) — 증상을 묻기 전에 119 상담 먼저. 문구는 약 화면 「너무 많이 드셨을 때」(NHS)와 같게 */
  var 과다 = /(한\s*통|통째|[0-9]{2,}\s*(알|정|개|봉)|많이|잔뜩|한꺼번에|두\s*배|두\s*번|실수로|모르고\s*또).*(먹었|먹였|삼켰|먹여|먹어\s*버렸)|(아이|애기|아기|애)가.*(약|알약|약통|시럽).*(삼켰|주워\s*먹|꺼내\s*먹|먹어\s*버렸|다\s*먹)|took (a lot|too many|the whole|all|double|twice)|swallowed|overdos|tom[ée] (muchas|demasiad|el doble|dos veces)|sobredosis|se (lo )?tragó|(薬|錠).*(たくさん|大量|全部|二回分|2回分).*飲|飲み込んだ|過量|吃了(很多|一整瓶|大量|一整盒|两次|双倍)|吞了|过量/i;
  /* 다섯 언어 위험 낱말(10-27 Main — 한국어만 알아듣던 곳이 있었다). 언어와 상관없이 다 본다(영어 폰을 쓰는 한국 사람도 있다) */
  var 마음다국 = /suicid|kill(ing)? myself|want to die|end (my|it all)|self[- ]?harm|cut(ting)? myself|no reason to live|quiero morir|matarme|quitarme la vida|no quiero vivir|hacerme daño|autolesi|死にたい|自殺|消えたい|自傷|リストカット|想死|自杀|不想活|轻生|自残|割腕/i;
  var 응급다국 = [/chest (pain|hurts|tight|pressure)|can'?t breathe|cannot breathe|short(ness)? of breath|trouble breathing|struggling to breathe|wheez|face (is )?droop|slurred|one side.*(weak|numb)|(lips?|tongue|throat).*(swell|swollen|clos)|(swell|swollen).*(lips?|tongue|throat)|seizure|convuls|fit(ting)?\b.*child|unconscious|passed out|won'?t wake|unresponsive|floppy|(vomit|throw)(ing|ed)? (up )?blood|black (stool|poop)|worst headache|took (a lot|too many|the whole|all)|overdos|not breathing/i,
    /dolor (de|en el) pecho|no puedo respirar|me falta (mucho )?el aire|ahog|cara caída|habla arrastrada|un lado.*(débil|dormid)|(labios?|lengua|garganta).*(hinch|cierra)|hinch\w*.*(labios?|lengua|garganta)|convuls|inconsciente|no despierta|no responde|(vómito|vomit\w*) (con )?sangre|heces negras|peor dolor de cabeza|tom[ée] (muchas|demasiad)|sobredosis|no respira/i,
    /胸が?(痛|苦し|締め付け|しめつけ)|息が(苦し|できな)|呼吸が(苦し|でき)|顔.*(ゆが|垂れ)|ろれつ|片側.*(力|しびれ)|(唇|舌|喉).*(腫れ|詰ま)|けいれん|痙攣|意識が(ない|な)|起きない|ぐったり|血を吐|吐血|黒い便|最悪の頭痛|(薬|錠).*(たくさん|大量|全部).*飲|過量|息をしていない/,
    /胸(痛|口痛|闷|口闷|口发紧)|喘不过气|呼吸困难|不能呼吸|没法呼吸|脸.*(歪|下垂)|口齿不清|说话含糊|一侧.*(无力|麻)|(嘴唇|舌头|喉咙).*(肿|紧)|抽搐|惊厥|昏迷|失去意识|叫不醒|吐血|黑便|最严重的头痛|吃了(很多|一整瓶|大量|一整盒)|过量|没有呼吸/];
  var 중독상담 = {
    US: { 번호: '1-800-222-1222', 이름: { ko: '미국 중독 상담(Poison Control, 1-800-222-1222)', en: 'Poison Control at 1-800-222-1222', es: 'a Poison Control (1-800-222-1222)', ja: '米国の中毒相談（Poison Control、1-800-222-1222）', zh: '美国中毒咨询热线（Poison Control，1-800-222-1222）' } },
    ES: { 번호: '915620420', 이름: { ko: '스페인 독성정보서비스(91 562 04 20)', en: "Spain's Toxicology Information Service (91 562 04 20)", es: 'al Servicio de Información Toxicológica (91 562 04 20)', ja: 'スペインの中毒情報サービス（91 562 04 20）', zh: '西班牙毒物信息服务（91 562 04 20）' } },
    JP: { 번호: '072-727-2499', 이름: { ko: '일본 중독110번(오사카 072-727-2499 / 쓰쿠바 029-852-9999, 두 곳 모두 365일 24시간)', en: 'the Japan Poison Information Center (Osaka 072-727-2499 / Tsukuba 029-852-9999, both open 24 hours, every day)', es: 'al Centro de Información Toxicológica de Japón (Osaka 072-727-2499 / Tsukuba 029-852-9999, ambos 24 horas, todos los días)', ja: '中毒110番（大阪 072-727-2499／つくば 029-852-9999、どちらも365日24時間対応）', zh: '日本中毒110（大阪 072-727-2499／筑波 029-852-9999，均为全年24小时）' } }
  };
  var 위험말 = {
    ko: { hr: ['(24시간)', '(상담 시간은 지역마다 달라요)'], s: function (e) { return '스스로 해치려고 약을 먹었거나, 깨우기 어렵거나, 숨쉬기 어렵거나, 경련하면 지금 ' + e + '에 전화하세요. 혼자 있지 말고 직접 운전하지 마세요. 약 상자와 남은 약을 챙기세요.'; }, p: function (P, e) { return '실수로 많이 먹었고 깨어 있고 숨을 평소처럼 쉬면, 증상이 없어도 지금 ' + P + '에 연락하세요. 스스로 해치려고 먹었거나 숨쉬기 어렵거나 경련·쓰러짐·깨우기 어려움이 있으면 ' + e + '. 억지로 토하게 하지 마시고, 약 상자와 남은 약을 챙기세요. 아세트아미노펜은 처음엔 멀쩡해도 몇 시간~며칠 뒤 간이 상할 수 있어요.'; }, o: function (e) { return '약을 너무 많이 먹었거나 아이가 약을 주워 먹었다면 증상이 없어도 지금 ' + e + '에 연락하세요. 억지로 토하게 하지 마시고, 약 상자와 남은 약을 챙기세요. 직접 운전해서 가지 마세요. 아세트아미노펜은 처음엔 멀쩡해도 몇 시간~며칠 뒤 간이 상할 수 있어요.'; }, n: function (e) { return '지금 위험하면 ' + (/^\d/.test(e) ? '응급 번호 ' + e : e) + '에 전화하세요. 곁에 있는 사람에게도 지금 알려 주세요.'; }, m: function (p, e) { return '많이 힘드시군요. 혼자 견디지 마세요 — 지금 ' + p + '에 전화하면 바로 이야기를 들어 줘요(24시간). 위험이 급하면 ' + e + '.'; }, b: function (e) { return '3개월이 안 된 아기가 38℃ 이상이면 해열제보다 진료가 먼저예요. 지금 응급실로 가거나 ' + e + '에 전화하세요.'; }, h: function (e) { return '41℃ 이상이면 지금 응급실로 가거나 ' + e + '에 전화하세요.'; }, c: function (e) { return '항암 치료 중 38℃ 이상은 바로 병원에 알려야 하는 열이에요. 치료받는 병원 응급 연락처나 ' + e + '로.'; }, r: function (e) { return '약보다 진료가 먼저예요. 지금 ' + e + '에 전화하거나 응급실로 가세요. 직접 운전하지 마세요.'; } },
    en: { hr: [' (24 hours)', ' (hours vary by region)'], s: function (e) { return 'If the medicine was taken to self-harm, or the person is hard to wake, has trouble breathing or is having a seizure, call ' + e + ' now. Do not stay alone and do not drive yourself. Bring the medicine box and any pills left.'; }, p: function (P, e) { return 'If this was accidental and the person is awake and breathing normally, call ' + P + ' now, even if there are no symptoms. For intentional self-harm, trouble breathing, seizures, collapse or difficulty waking, call ' + e + '. Do not make yourself vomit. Bring the medicine box and any pills left. With acetaminophen you can feel fine at first, but liver damage can show up hours to days later.'; }, o: function (e) { return 'If you took too much, call ' + e + ' now for advice even if you feel fine. Do not make yourself vomit. Bring the medicine box and any pills left. Do not drive yourself. With acetaminophen you can feel fine at first, but liver damage can show up hours to days later.'; }, n: function (e) { return 'If you are in danger now, call ' + (/^\d/.test(e) ? 'the emergency number ' + e : e) + '. Tell someone near you right now, too.'; }, m: function (p, e) { return "It sounds like things are really hard right now. You don't have to face this alone — call " + p + ' now to talk to someone (24 hours). If you are in immediate danger, call ' + e + '.'; }, b: function (e) { return 'A baby under 3 months with a temperature of 38°C or higher needs a doctor before any fever medicine. Go to the emergency room now or call ' + e + '.'; }, h: function (e) { return 'A temperature of 41°C or higher needs the emergency room now — or call ' + e + '.'; }, c: function (e) { return 'A temperature of 38°C or higher during cancer treatment must be reported right away. Call your treatment hospital’s emergency line or ' + e + '.'; }, r: function (e) { return 'See a doctor before taking any medicine. Call ' + e + ' or go to the emergency room now. Do not drive yourself.'; } },
    es: { hr: [' (24 horas)', ' (el horario varía según la región)'], s: function (e) { return 'Si tomó el medicamento para hacerse daño, o si cuesta despertarle, respira con dificultad o tiene convulsiones, llame ahora al ' + e + '. No se quede solo y no conduzca usted mismo. Lleve la caja del medicamento y las pastillas que queden.'; }, p: function (P, e) { return 'Si la ingestión fue accidental y la persona está consciente y respira con normalidad, llame ahora ' + P + ', aunque no tenga síntomas. Si fue para hacerse daño o hay dificultad para respirar, convulsiones, desmayo o cuesta despertarla, llame al ' + e + '. No se provoque el vómito. Lleve la caja del medicamento y las pastillas que queden. Con el paracetamol puede sentirse bien al principio, pero el daño en el hígado puede aparecer horas o días después.'; }, o: function (e) { return 'Si ha tomado demasiado, llame ahora al ' + e + ' para que le orienten, aunque se encuentre bien. No se provoque el vómito. Lleve la caja del medicamento y las pastillas que queden. No conduzca usted mismo. Con el paracetamol puede sentirse bien al principio, pero el daño en el hígado puede aparecer horas o días después.'; }, n: function (e) { return 'Si corre peligro ahora, llame ' + (/^\d/.test(e) ? 'al número de emergencias ' + e : 'a ' + e) + '. Avise también ahora a alguien que esté cerca.'; }, m: function (p, e) { return 'Parece que está pasando por un momento muy difícil. No tiene que afrontarlo solo: llame ahora al ' + p + ' para hablar con alguien (24 horas). Si corre peligro inmediato, llame al ' + e + '.'; }, b: function (e) { return 'Un bebé de menos de 3 meses con 38 °C o más necesita atención médica antes que cualquier antitérmico. Vaya a urgencias ahora o llame al ' + e + '.'; }, h: function (e) { return 'Con 41 °C o más, vaya a urgencias ahora o llame al ' + e + '.'; }, c: function (e) { return 'Durante un tratamiento contra el cáncer, 38 °C o más debe comunicarse enseguida. Llame al teléfono de urgencias de su hospital o al ' + e + '.'; }, r: function (e) { return 'Antes que cualquier medicamento, necesita atención médica. Llame ahora al ' + e + ' o vaya a urgencias. No conduzca usted mismo.'; } },
    ja: { hr: ['（24時間）', '（受付時間は地域によって異なります）'], s: function (e) { return '自分を傷つける目的で薬を飲んだ場合や、起こしても起きにくい・呼吸が苦しい・けいれんしている場合は、今すぐ ' + e + ' に電話してください。ひとりにならず、ご自分で運転しないでください。薬の箱と残りの薬を手元に置いてください。'; }, p: function (P, e) { return '誤って飲みすぎ、意識がはっきりしていて呼吸も普段どおりなら、症状がなくても' + P + 'へすぐ相談してください。自分を傷つける目的で飲んだ場合や、意識・呼吸の異常、けいれんがある場合は ' + e + ' へ。無理に吐かせず、薬の箱と残りの薬を手元に置いてください。アセトアミノフェンは最初は何ともなくても、数時間〜数日後に肝臓が傷むことがあります。'; }, o: function (e) { return '飲みすぎた場合は、平気そうでも今すぐ ' + e + ' に電話して相談してください。無理に吐かせないでください。薬の箱と残りの薬を持って行き、ご自分で運転しないでください。アセトアミノフェンは最初は何ともなくても、数時間〜数日後に肝臓が傷むことがあります。'; }, n: function (e) { return '今危険なときは' + (/^\d/.test(e) ? '緊急番号 ' + e + ' ' : e) + 'に電話してください。そばにいる人にも今すぐ知らせてください。'; }, m: function (p, e) { return 'とてもつらい状態なのですね。ひとりで抱え込まないでください。今すぐ ' + p + ' に電話すれば話を聞いてもらえます（24時間）。命の危険が迫っているときは ' + e + ' へ。'; }, b: function (e) { return '生後3か月未満の赤ちゃんが38℃以上なら、解熱剤より先に受診が必要です。今すぐ救急外来へ行くか ' + e + ' に電話してください。'; }, h: function (e) { return '41℃以上なら今すぐ救急外来へ行くか ' + e + ' に電話してください。'; }, c: function (e) { return 'がん治療中の38℃以上の熱はすぐに病院へ連絡が必要です。治療中の病院の緊急連絡先か ' + e + ' へ。'; }, r: function (e) { return '薬より先に受診が必要です。今すぐ ' + e + ' に電話するか救急外来へ行ってください。ご自分で運転しないでください。'; } },
    zh: { hr: ['（24小时）', '（服务时间因地区而异）'], s: function (e) { return '如果是为了伤害自己而服药，或者叫不醒、呼吸困难、抽搐，请立即拨打 ' + e + '。不要独处，不要自己开车。请带上药盒和剩下的药。'; }, p: function (P, e) { return '如果是误服过量，且人清醒、呼吸正常，即使没有症状也请现在联系' + P + '。如果是为了伤害自己而服药，或出现呼吸困难、抽搐、昏倒、叫不醒，请拨打 ' + e + '。不要催吐，请带上药盒和剩下的药。对乙酰氨基酚刚开始可能没有不适，但数小时到数天后可能出现肝损伤。'; }, o: function (e) { return '如果服用过量，即使感觉没事，也请现在拨打 ' + e + ' 咨询。不要催吐。请带上药盒和剩下的药，不要自己开车。对乙酰氨基酚刚开始可能没有不适，但数小时到数天后可能出现肝损伤。'; }, n: function (e) { return '如果现在有危险，请拨打' + (/^\d/.test(e) ? '急救电话 ' + e : e) + '。也请马上告诉身边的人。'; }, m: function (p, e) { return '听起来您现在非常难受。请不要一个人扛着——现在拨打 ' + p + '，会有人倾听您（24小时）。如果情况紧急，请拨打 ' + e + '。'; }, b: function (e) { return '不满3个月的婴儿体温达到38°C或以上，应先就医，而不是先用退烧药。请立即去急诊或拨打 ' + e + '。'; }, h: function (e) { return '体温达到41°C或以上，请立即去急诊或拨打 ' + e + '。'; }, c: function (e) { return '抗癌治疗期间体温达到38°C或以上，需要立即告知医院。请联系治疗医院的急诊电话或拨打 ' + e + '。'; }, r: function (e) { return '比起用药，您需要先就医。请立即拨打 ' + e + ' 或去急诊。请不要自己开车。'; } }
  };
  function 위험(글, 값) {
    var t = String(글 || ''), N = (window.I18N && window.I18N.emg) || { e: '119', m: ['109', '1577-0199'] }, M = 위험말[window.LANG] || 위험말.ko;
    if (!N.e) N = { e: ({ ko: '그 나라 응급 번호', en: 'the local emergency number', es: 'el número de emergencias del país', ja: '現地の緊急番号', zh: '当地急救电话' })[window.LANG] || 'the local emergency number', m: [] };   /* 11-04 번호 모르는 나라 — 글만, 전화 단추 없음 */
    var p = N.m[0] || N.e;
    var 의도 = 마음.test(t) || 마음다국.test(t), L = 위험말[window.LANG] ? window.LANG : 'ko';
    /* 이미 삼킨 것이 먼저(10-28 곁에 교훈). 바깥 검수 9차(10-28): 스스로 해치려고 먹었거나 의식·숨·경련 이상이면 응급 번호,
       증상 없는 실수 복용은 그 나라 중독 상담(있는 나라만 — 미국·스페인·일본). 한국·중국·모르는 나라는 응급 번호 */
    if (과다.test(t)) {
      var t2 = t.replace(new RegExp(과다.source, 'gi'), ' ');   /* 「많이 먹었다」 낱말 자체는 중증 신호로 세지 않는다 */
      var 중증 = 의도 || 응급.concat(응급다국).some(function (r) { return r.test(t2); }) || /의식|깨워도|안\s*깨|숨.*(못|안|힘들|차)|경련|쓰러|unconscious|won'?t wake|not breathing|seizure|inconsciente|no despierta|convuls|意識|けいれん|息をしていない|昏迷|叫不醒|抽搐|没有呼吸/i.test(t2);
      if (중증) return { 말: M.s(N.e), 전화: N.e };
      var P = 중독상담[window.CC];
      if (P) return { 말: M.p(P.이름[L] || P.이름.en, N.e), 전화: P.번호 };
      return { 말: M.o(N.e), 전화: N.e };
    }
    /* 마음 위기 번호의 「24시간」은 확인된 나라(한국 109·미국 988·스페인 024)만 — 일본·중국은 지역마다 운영 시간이 다르다(바깥 검수 9차) */
    if (의도 && (!N.m[0] || N.m[0] === N.e)) return { 말: M.n(N.e), 전화: N.e };   /* 11-04 Main — 위기 상담 번호가 없는 나라는 상담 문장 대신 응급 번호 */
    if (의도) { var 말 = M.m(p, N.e); if (!/^(KR|US|ES)$/.test(window.CC || 'KR')) 말 = 말.replace(M.hr[0], M.hr[1]); return { 말: 말, 전화: p }; }
    var 열 = 값 && 값.체온, 달 = 값 && 값.나이개월;
    if ((열 >= 38 && 달 != null && 달 < 3) || (열 >= 38 && /3\s*개월\s*(미만|안|전)|신생아|백일\s*전|newborn|recién nacido|新生児|新生儿/i.test(t))) return { 말: M.b(N.e), 전화: N.e };
    if (열 >= 41) return { 말: M.h(N.e), 전화: N.e };
    if (열 >= 38 && /항암|암\s*치료|항암제|chemo|cancer treatment|quimio|抗がん剤|がん治療|化疗|抗癌/i.test(t)) return { 말: M.c(N.e), 전화: N.e };
    for (var i = 0; i < 응급.length; i++) if (응급[i].test(t)) return { 말: M.r(N.e), 전화: N.e };
    for (var j = 0; j < 응급다국.length; j++) if (응급다국[j].test(t)) return { 말: M.r(N.e), 전화: N.e };
    return null;
  }
  function 뜻목록() {
    var L = (D.symptoms || []).map(function (s) { return { id: 'sym:' + s.id, 예문: [s.name, s.short].filter(Boolean), 태그: (s.tags || []).concat(String(s.name || '').split(/[·,\s]/)).filter(function (w) { return w && w.length >= 2; }) }; });
    L.push({ id: 'kids', 예문: ['아이 해열제 몇 mL', '아기 해열제 양'], 태그: ['아이', '아기', '애기', '우리애', '애가', '개월', '키로', '미리', 'mL'] });
    L.push({ id: 'pill', 예문: ['이 알약 뭐예요', '알약 모양으로 찾기'], 태그: ['알약', '모양', '써있', '적혀', '각인', '동그란', '길쭉'] });
    L.push({ id: 'bag', 예문: ['먹는 약 정리', '내 약통'], 태그: ['약통', '정리', '먹는약'] });
    L.push({ id: 'together', 예문: ['같이 먹어도 되나요'], 태그: ['같이', '함께', '병용', '이랑', '하고'] });
    return L;
  }
  function 약찾기(글) {
    var g = String(글 || '').toLowerCase().replace(/\s+/g, ''), T = 이름들(), 찾음 = [], ids = [];
    Object.keys(T).sort(function (a, b) { return b.length - a.length; }).forEach(function (n) {
      var k = n.toLowerCase().replace(/\s+/g, ''); if (g.indexOf(k) < 0) return;
      if (찾음.some(function (x) { return x.indexOf(k) >= 0; })) return;   /* 「타이레놀콜드」 안의 「타이레놀」은 따로 세지 않는다 */
      찾음.push(k); if (ids.indexOf(T[n]) < 0) ids.push(T[n]);
    });
    return ids;
  }
  var 갈곳 = {};
  function 칩길(이름, 길) { 갈곳[이름] = 길; return 이름; }
    function 겹침(ids) {
    var ds = ids.map(function (i) { return drug(i); }).filter(Boolean), T = ME.taking, 결;
    ME.taking = []; try { 결 = ixCards(ixRun(ds)); } finally { ME.taking = T; }
    var 센 = 결.filter(function (c) { return c.lv === 'stop' || c.lv === 'warn'; });
    var 말 = [ds.map(function (d) { return d.name; }).join(' · ') + ' — 같이 드시는지 볼게요.'];
    if (센.length) 말.push((센.some(function (c) { return c.lv === 'stop'; }) ? '같이 드시면 안 되는 것이 있어요: ' : '조심할 것이 있어요: ') + 센.slice(0, 2).map(function (c) { return c.t; }).join(' / ') + '. 자세한 이유와 대신할 방법은 「내 약통에 담고 자세히」에서 보세요.');
    else 말.push('이 둘 사이에 겹치는 성분이나 조심할 조합은 안 보여요. 다른 약을 더 드시면 그 약까지 함께 봐야 해요.');
    return { 말: 말, 칩: [칩길('내 약통에 담고 자세히', function () { ME.taking = ME.taking || []; ids.forEach(function (i) { if (ME.taking.indexOf(i) < 0) ME.taking.push(i); }); saveMe(); go('/together'); }), 칩길(짧은이름(ds[0].name) + ' 자세히', '/drug/' + ds[0].id), '다른 질문'] };
  }
  /* 증상은 앱의 찾기(search — 구어 사전·말끝 떼기)로 고른다. 그 앞에 대화에서 흔한 입말을 찾기 낱말로 고른다 */
  var 입말 = [[/술\s*(먹|마시)|숙취|해장/, '숙취'], [/머리.*(깨질|터질|지끈|띵)/, '두통'], [/담\s*(이\s*)?걸|목이?\s*안\s*돌|뻐근/, '담 결림'], [/코\s*(가\s*)?막혀|코막힘/, '코막힘'],
    [/체한|체했|얹힌|명치/, '체함'], [/배탈|토하고\s*설사|토하면서\s*설사|장염/, '장염'], [/베였|베인|긁혔|까졌|상처/, '상처'], [/데었|데인|화상/, '데었을 때'], [/눈곱|눈이\s*빨개|결막염/, '눈병'], [/목.*(아프|따끔|칼칼|부었)|침\s*삼킬/, '목 아픔'],
    [/눈.*가렵|가려운\s*눈|꽃가루|두드러기/, '알레르기'], [/기침/, '기침'], [/쪼매|억수로|겁나게|엄청/g, ' '], [/(나는데예|하는데예|예$|요$)/, '']];
  function 증상찾기(t) {
    var q = t, 낱 = [];
    입말.forEach(function (x) { if (x[1] === ' ' || x[1] === '') q = q.replace(x[0], x[1]); else if (x[0].test(t)) 낱.push(x[1]); });
    var 해 = function (w) { try { var r = search(w); r = Array.isArray(r) ? r : []; for (var i = 0; i < Math.min(3, r.length); i++) if (r[i].k === '증상') return r[i].h.replace('/symptom/', ''); } catch (e) {} return null; };
    return (낱.length ? 해(낱[0]) : null) || 해(q);
  }
  function 처리(앎, 상태) {
    var t = String(앎.글 || '').trim();
    if (갈곳[t]) { var 길 = 갈곳[t]; setTimeout(function () { typeof 길 === 'function' ? 길() : go(길); }, 350); return { 말: ['열어 드릴게요.'] }; }
    if (t === '다른 질문' || t === '모르겠어요') { 상태.약 = []; return { 말: ['네, 무엇이든 편하게 적어 주세요.'], 칩: ['같이 먹어도 되나', '아이 해열제', '이 알약 뭐지'] }; }
    var ids = 약찾기(t), 이전 = 상태.약 || [], 같이 = /같이|함께|이랑|랑\s|하고|병용|먹어도|먹은\s*뒤|먹었는데|또\s*먹/.test(t);
    var 갈 = Object.keys(갈래).filter(function (k) { return t.indexOf(k) >= 0; })[0];
    var rx = 처방갈래.filter(function (x) { return x[1].test(t); })[0];
    if (rx && (ids.length || 같이 || 갈)) return { 말: [RX_NAME[rx[0]] + '을 드시는군요. 처방약과 약국 약을 함께 드실 때 조심할 것을 길잡이에 모아 두었어요.'], 칩: [칩길(RX_NAME[rx[0]] + ' 길잡이', '/rx/' + rx[0]), '다른 질문'] };
    if (ids.length >= 2) { 상태.약 = ids; return 겹침(ids); }
    if (ids.length === 1 && 이전.length && 이전.indexOf(ids[0]) < 0) { 상태.약 = 이전.concat(ids); return 겹침(상태.약); }
    if (/아이|아기|애기|우리\s*애|애가|[0-9]+\s*개월/.test(t) && /얼마|몇|양|미리|mL|ml|먹여/i.test(t)) 앎.뜻 = [{ id: 'kids' }].concat(앎.뜻 || []);
    else if (ids.length === 1 && 갈) { 상태.약 = ids; 상태.기다림 = 갈; return { 말: [짧은이름(drug(ids[0]).name) + '와 ' + 갈 + '을 같이 — 맞으세요?', 갈래[갈].묻기], 칩: 갈래[갈].칩.concat(['모르겠어요']) }; }
    if (ids.length === 1 && !(앎.뜻[0] && 앎.뜻[0].id === 'kids')) { var d = drug(ids[0]); 상태.약 = ids;
      return { 말: [d.name + (d.tagline ? ' — ' + String(d.tagline).replace(/\*\*/g, '') : '') + '.', (앎.값.시간 ? '' : '함께 드시는 다른 약이 있으면 이름을 적어 주세요. 겹치는지 바로 볼게요.')].filter(Boolean), 칩: [칩길('먹는 법 보기', '/drug/' + d.id), '다른 질문'] }; }
    var 뜻 = (앎.뜻 || [])[0], v = 앎.값;
    if (뜻 && 뜻.id === 'kids' || /아이|아기|애기|우리\s*애|애가/.test(t) && /(해열|열|감기|시럽|미리|mL|ml)/i.test(t)) {
      var 되 = [v.체온 ? v.체온 + '℃' : '', v.몸무게 ? v.몸무게 + ' kg' : '', v.나이개월 != null ? (v.나이개월 < 24 ? v.나이개월 + '개월' : Math.floor(v.나이개월 / 12) + '살') : ''].filter(Boolean).join(', ');
      return { 말: [(되 ? 되 + ' — 확인했어요. ' : '') + '아이 해열제는 몸무게로 양을 정해요.', v.몸무게 ? '계산 화면에서 시럽 mL·간격·하루 한도를 바로 볼 수 있어요.' : '몸무게를 아시면 더 정확해요 — 계산 화면에서 넣어 주세요.'], 칩: [칩길('해열제 양 계산', '/kids'), '다른 질문'] }; }
    if (뜻 && 뜻.id === 'pill') return { 말: ['색·모양·앞뒤 글자로 찾을 수 있어요. 사진으로 약봉투를 읽을 수도 있어요.'], 칩: [칩길('알약 찾기', '/pill'), 칩길('사진으로 읽기', '/photo'), '다른 질문'] };
    if (뜻 && 뜻.id === 'bag') return { 말: ['드시는 약을 내 약통에 담아 두면 겹침·먹는 시간을 함께 봐 드려요.'], 칩: [칩길('내 약통 열기', '/bag'), '다른 질문'] };
    var sid = 증상찾기(t); if (sid) 뜻 = { id: 'sym:' + sid };
    if (뜻 && 뜻.id.indexOf('sym:') === 0) { var s = (D.symptoms || []).filter(function (x) { return 'sym:' + x.id === 뜻.id; })[0];
      if (s) return { 말: [s.name + ' — 이렇게 들렸어요.', '먼저 위험 신호가 없는지 함께 보고, 약국에서 살 약과 먹는 법을 알려 드릴게요.'], 칩: [칩길('이렇게 하세요', '/symptom/' + s.id), '다른 질문'] }; }
    if (뜻 && 뜻.id === 'together') return { 말: ['드시는 약 이름을 둘 이상 적어 주세요. 예) 타이레놀이랑 판콜'] };
    return null;
  }
  window.vTalkS = function () {
    setTimeout(function () {
      var 곳 = document.getElementById('talk'); if (!곳 || !window.대화) return;
      /* 화면을 다시 그려도(자료가 늦게 와 route() 가 다시 돌 때) 하던 대화를 그대로 — 같은 대화 칸을 다시 끼운다 */
      if (window._talkNode && window._talkNode !== 곳) { 곳.replaceWith(window._talkNode); return; }
      window._talkNode = 곳;
      var 봇 = 대화.만들기({ 앱: 'yakjido', 언어: window.LANG || 'ko', 뜻: 뜻목록(), 약: Object.keys(이름들()), 위험: 위험, 처리: 처리 });
      봇.붙이기(곳, { 말: ['어떤 약이 궁금하세요? 어디가 아프세요?', '편하게 적어 주세요. 예) 타이레놀이랑 감기약 같이 먹어도 돼?'], 칩: ['같이 먹어도 되나', '아이 해열제', '이 알약 뭐지'] });
      var q = (location.hash.match(/[?&]q=([^&]+)/) || [])[1]; if (q) setTimeout(function () { 봇.보냄(decodeURIComponent(q)); }, 900);
      window.약지도대화 = { 위험: 위험, 처리: 처리, 약찾기: 약찾기, 봇: 봇 };
    }, 0);
    return topBar({ back: '홈' }) + '<h1>물어보기</h1><p class="small muted" style="margin:4px 0 12px">사람 상담이 아니라 앱 안의 안내예요. 이 폰 안에서만 읽고 어디로도 보내지 않아요.</p><div id="talk" class="talk"></div>' + disclaimer();
  };
  /* 대화의 뜻 고르기·답은 아직 한국어만(다섯 언어 말뭉치는 다음 회차) — 한국어가 아닌 화면에는 홈 입구를 내지 않는다. 위험 낱말은 다섯 언어 다 본다 */
  window.대화줄 = function () { if (window.LANG && window.LANG !== 'ko') return ''; return '<a class="talk-door" href="#/talk"><span class="b">어떤 약이 궁금하세요? 어디가 아프세요?</span><span class="small muted">「타이레놀이랑 감기약 같이 먹어도 돼?」처럼 편하게 물어보세요 ›</span></a>'; };
  var cs = document.createElement('style');
  cs.textContent = '.talk-door{display:flex;flex-direction:column;gap:4px;margin:12px 0 4px;padding:14px 16px;border-radius:18px 18px 18px 6px;background:var(--tint);color:var(--ink);text-decoration:none;min-height:48px}.talk-door .b{font-weight:700}.talk{min-height:50vh}';
  document.head.appendChild(cs);
})();

/* 기내 모드(10-27 · 요청서 20261027_메디나눔_전앱_기내모드) — 인터넷 없이 쓰도록 자료·고른 언어·글꼴을 미리 받아 둔다.
   받는 것은 서비스 워커 캐시에 들어간다(같은 주소라 앱이 그대로 꺼내 씀). 서버 응답(로그인·동기화)은 담지 않는다. 글꼴·supabase-js 도 묶음 안(바깥 파일 0). */
(function () {
  var K = 'yakjido.offline', MB = function (b) { return (b / 1048576).toFixed(b < 10485760 ? 1 : 0) + ' MB'; };
  var 갈래 = [['core', '약 자료', '약 찾기·겹침·증상·처방약 길잡이', /^(core|detail|brands|lexicon|meta|mixes|nutrients|names-rx|kpic)\.json$/],
              ['easy', '쉬운 설명', '제품마다 쉬운 말 설명서', /^easy-/],
              ['pill', '낱알 식별', '모양·색·글자로 알약 찾기', /^pills/]];
  var 상태 = function () { try { return JSON.parse(localStorage.getItem(K) || 'null'); } catch (e) { return null; } };
  var 판 = function () { try { return DATAV; } catch (e) { return ''; } };
  var 목록 = null, 고름 = { core: 1, easy: 1, pill: 1, lang: 1, font: 1 }, 받는중 = false;
  function 읽기() { return 목록 ? Promise.resolve(목록) : fetch('data/offline.json?v=' + 판(), { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (j) { 목록 = j; return j; }); }
  function 할일(j) {
    var out = [];
    갈래.forEach(function (g) { if (고름[g[0]]) j.data.forEach(function (f) { if (g[3].test(f.n)) out.push({ u: 'data/' + f.n + '?v=' + 판(), b: f.b }); }); });
    if (고름.lang && window.LANG && window.LANG !== 'ko') (j.i18n || []).forEach(function (f) { if (f.n === window.LANG + '.json') out.push({ u: 'data/i18n/' + f.n, b: f.b }); });
    if (고름.font) (j.ext || []).forEach(function (f) { out.push({ u: f.n, b: f.b }); });
    return out;
  }
  function 크기(j, k) {
    if (k === 'font') return (j.ext || []).reduce(function (s, f) { return s + f.b; }, 0);
    if (k === 'lang') return (j.i18n || []).filter(function (f) { return f.n === window.LANG + '.json'; }).reduce(function (s, f) { return s + f.b; }, 0);
    var g = 갈래.filter(function (x) { return x[0] === k; })[0]; return g ? j.data.filter(function (f) { return g[3].test(f.n); }).reduce(function (s, f) { return s + f.b; }, 0) : 0;
  }
  function 줄(id, t, s, b) { return '<label class="gn-row"><input type="checkbox" ' + (고름[id] ? 'checked' : '') + ' onchange="기내고름(\'' + id + '\',this.checked)"><span><b>' + t + '</b><span class="small muted">' + s + '</span></span><em>' + b + '</em></label>'; }
  function 그리기() {
    var box = document.getElementById('gn-box'); if (!box) return;
    읽기().then(function (j) {
      var st = 상태(), 새판 = st && st.v !== 판(), tot = 할일(j).reduce(function (s, x) { return s + x.b; }, 0);
      var h = st ? '<p class="gn-st ' + (새판 ? 'old' : 'ok') + '">' + (새판 ? '받아 둔 뒤에 약 자료가 새로 나왔어요 — 다시 받으면 새것으로 바뀌어요.' : '인터넷 없이 쓸 준비가 됐어요 · ' + esc(st.at) + ' 받음 · ' + MB(st.b)) + '</p>' : '';
      h += 갈래.map(function (g) { return 줄(g[0], g[1], g[2], MB(크기(j, g[0]))); }).join('');
      if (window.LANG && window.LANG !== 'ko') h += 줄('lang', '고른 언어', '번역 사전', MB(크기(j, 'lang')));
      h += 줄('font', '글꼴·로그인 프로그램', '글씨 모양과 연결되면 쓰는 로그인', MB(크기(j, 'font')));
      h += '<p class="small muted gn-tot">받을 크기 약 <b>' + MB(tot) + '</b>' + (tot > 31457280 ? ' — 30 MB 가 넘어요. 필요한 갈래만 고르셔도 돼요.' : '') + ' 와이파이에서 받기를 권해요.</p>';
      h += '<div class="gn-bar" hidden><progress max="100" value="0"></progress><span class="small muted"></span></div>';
      h += '<button type="button" class="btn" onclick="기내받기()">' + (st ? '다시 받기' : '받아 두기') + '</button>';
      if (st) h += '<button type="button" class="btn ghost" style="margin-top:8px" onclick="기내지우기()">받아 둔 것 지우기</button>';
      box.innerHTML = h; if (window.I18N && I18N.tr) I18N.tr(box);
    }).catch(function () { box.innerHTML = '<p class="small muted">목록을 못 읽었어요 — 인터넷이 될 때 다시 열어 주세요.</p>'; if (window.I18N && I18N.tr) I18N.tr(box); });
  }
  window.기내고름 = function (k, on) { 고름[k] = on ? 1 : 0; 그리기(); };
  window.기내받기 = function () {
    if (받는중) return; if (navigator.onLine === false) { try { toast('인터넷이 될 때 받을 수 있어요'); } catch (e) {} return; }
    받는중 = true;
    읽기().then(function (j) {
      var q = 할일(j), all = q.reduce(function (s, x) { return s + x.b; }, 0) || 1, got = 0, n = 0, bad = 0;
      var bar = document.querySelector('#gn-box .gn-bar'), pg = bar && bar.querySelector('progress'), tx = bar && bar.querySelector('span');
      if (bar) bar.hidden = false;
      var 표시 = function () { if (pg) pg.value = Math.min(100, Math.round(got / all * 100)); if (tx) tx.textContent = MB(got) + ' / ' + MB(all) + (bad ? ' · 못 받은 것 ' + bad : ''); };
      var 하나 = function (x) { return fetch(x.u).then(function (r) { if (!r.ok) throw 0; return r.blob(); }).then(function () { got += x.b; }).catch(function () { bad++; }).then(표시); };
      var 일꾼 = function () { var x = q[n++]; return x ? 하나(x).then(일꾼) : Promise.resolve(); };
      return Promise.all([일꾼(), 일꾼(), 일꾼(), 일꾼()]).then(function () {
        받는중 = false;
        if (bad) { try { toast('못 받은 파일이 ' + bad + '개 있어요 — 다시 받기를 눌러 주세요'); } catch (e) {} 표시(); return; }
        var d = new Date(), at = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
        try { localStorage.setItem(K, JSON.stringify({ v: 판(), at: at, b: got, lang: window.LANG || 'ko' })); } catch (e) {}
        try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist(); } catch (e) {}
        try { toast('다 받았어요 — 인터넷 없이도 열려요'); } catch (e) {}
        그리기();
      });
    }).catch(function () { 받는중 = false; try { toast('목록을 못 읽었어요'); } catch (e) {} });
  };
  window.기내지우기 = function () {
    var 끝 = function () { try { localStorage.removeItem(K); } catch (e) {} 그리기(); try { toast('받아 둔 것을 지웠어요'); } catch (e) {} };
    if (!window.caches) return 끝();
    caches.keys().then(function (ks) { return Promise.all(ks.filter(function (k) { return k === 'yakjido-data-v1' || k === 'yakjido-ext-v1'; }).map(function (k) { return caches.delete(k); })); }).then(끝, 끝);
  };
  window.기내칸 = function () { setTimeout(그리기, 0); return '<section class="sec card" id="offline" style="margin-top:16px"><h2>기내에서 쓰기</h2><p class="small muted">비행기·지하·해외처럼 인터넷이 없거나 막힌 곳에 가시기 전에 미리 받아 두세요. 로그인·동기화·바깥 링크는 연결되면 돼요.</p><div id="gn-box"><p class="small muted">목록을 읽는 중…</p></div></section>'; };
  window.기내줄 = function () { var st = 상태(); if (st && st.v === 판()) return ''; return '<p class="gn-home"><a href="#/me?t=set&to=offline" onclick="setTimeout(function(){var e=document.getElementById(\'offline\');e&&e.scrollIntoView({block:\'start\'})},300)">' + (st ? '받아 둔 약 자료가 새로 나왔어요 — 기내용 다시 받기 ›' : '인터넷 없는 곳에 가세요? 기내에서 쓰게 받아 두기 ›') + '</a></p>'; };
  var cs = document.createElement('style');
  cs.textContent = '.gn-row{display:flex;gap:12px;align-items:center;padding:12px 0;border-top:1px solid var(--line);min-height:48px}.gn-row input{width:22px;height:22px;flex:none}.gn-row>span{flex:1;display:flex;flex-direction:column;gap:2px}.gn-row em{font-style:normal;color:var(--muted);font-size:.875rem;white-space:nowrap}' +
    '.gn-tot{margin:10px 0}.gn-bar{display:flex;flex-direction:column;gap:4px;margin:8px 0 12px}.gn-bar progress{width:100%;height:10px;accent-color:var(--primary)}.gn-st{padding:10px 12px;border-radius:12px;font-size:.875rem;font-weight:600;margin:8px 0}.gn-st.ok{background:var(--tint);color:var(--primary-deep)}.gn-st.old{background:var(--caution-tint);color:var(--caution)}' +
    '.gn-home{text-align:center;margin:18px 0 4px;font-size:.875rem}.gn-home a{color:var(--muted);display:inline-flex;align-items:center;min-height:44px}';
  document.head.appendChild(cs);
})();
/* 설정 화면의 구독 칸 — 스위치가 꺼져 있으면 빈 글(아무것도 안 보임) */
window.구독관리 = function () { try { var h = 구독.관리HTML(); return h ? '<section class="sec card" style="margin-top:16px"><h2>구독</h2>' + h + '</section>' : ''; } catch (e) { return ''; } };

/* ═══ 2026-10-14 약지도 — 첫 동의 · 로그인 문 · 약관 읽기 (현욱님 「이용약관을 체크하지 못하게 돼있잖아」 「회원가입/로그인 화면」) ═══
   첫 화면 예산(index.html 압축 228 KB) 때문에 화면 코드는 여기(따로 받는 파일)에 둔다. index 에는 문지기(consentGate)와 길(#/consent·#/login·#/doc)만.
   본보기: ClinicScore renderConsent(로고·이름·한 줄 → 세 줄 카드 → 모두 동의 → 필수 줄 → 큰 단추 → 발문).
   ⚖️ 들어올 때 받는 동의는 필수 둘(이용약관·개인정보 처리방침)뿐 — 계약 이행에 필요한 처리는 동의가 필요 없고(개인정보 보호법 15조 1항 4호, 2023 개정),
      건강 민감정보는 «모으는 그 순간» 따로 받는다(23조) → 「서버에 저장하기」·만 14세 확인은 계정을 만들 때(로그인 문). 선택 항목·광고 동의는 없다. */
/* 다른 폰의 기록을 받아 오면 다시 그린다(서버.설치의 다시그리기) — 10-14 app-shell 에서 옮김(첫 화면 예산). 함수 선언이라 위 설치 줄보다 먼저 있다 */
function srvReload(){ try { ME = loadMe(localStorage.getItem(ME_KEY)); snapMe(); } catch (e) {} try { armNotifications(); } catch (e) {} try { route(); } catch (e) {} }
/* ── 「서버에 저장하기」 동의 켜기·거두기(설정의 계정 칸) — 10-14 app-shell 에서 옮김(첫 화면 예산). 내용은 그대로 ── */
/* Z4 #22 — 올라가는 것에 아이 정보(부르는 말·생년월일·몸무게)·약 알레르기가 빠져 있었다. 처리방침 1절 표와 같게 */
window.계정항목 = { ko: '드시는 약·복용 시간과 기록·몸 상태(임신·수유·지병 등)·약 알레르기·불편했던 일·혈압 수첩·진료 예약·아이 정보(부르는 말·생년월일·몸무게)', 뒤: ' 목적은 폰을 바꿔도 이어 보기, 보관은 계정을 지우시거나 동의를 거두실 때까지(거두시면 바로 지워요). 건강에 관한 민감정보라 따로 동의를 받고, 동의하지 않으셔도 약지도는 이 폰에서 그대로 쓰실 수 있어요. 보기 설정과 날씨는 올라가지 않아요.' };
window.서버동의켜기 = async function(){
  if (!(await appConfirm('「서버에 저장하기」에 동의하시겠어요?\n\n올라가는 것: ' + 계정항목.ko + '\n어디에: 메디나눔 서버(Supabase, 서울)\n왜: 폰을 바꿔도 이어 보려고\n언제까지: 계정을 지우실 때까지 — 동의를 거두시면 서버 기록을 바로 지워요\n\n건강에 관한 민감정보예요. 동의하지 않으셔도 되고, 동의하지 않아도 약지도는 이 폰에서 그대로 쓰실 수 있어요.', { ok:'동의해요', cancel:'동의하지 않아요' }))) return;
  try { localStorage.setItem(AGREE_KEY, JSON.stringify({ server:true, at:new Date().toISOString() })); } catch (e) {}
  route();
};
window.서버동의끄기 = async function(){
  const off = (msg) => { try { localStorage.setItem(AGREE_KEY, JSON.stringify({ server:false, at:new Date().toISOString() })); } catch (e) {} toast(msg); route(); };
  if (!srvHasAccount()) return off('서버에 저장하기 동의를 거두었어요. 이 폰의 기록은 그대로 있어요.');
  /* 동의를 거두면 서버에 둔 것도 지운다(처리방침 9항) — 이 폰의 기록은 남긴다 */
  if (!(await appConfirm('동의를 거두면 메디나눔 서버에 있는 약지도 기록을 지우고 로그아웃해요. 이 폰의 기록은 그대로 있어요.\n(다른 메디나눔 앱 기록이 없으면 계정도 함께 지워져요.)', { ok:'동의 거두기', cancel:'그만둘게요', danger:true }))) return;
  서버.서버만지움().then(r => { if (r && r.skipped) { toast('로그인이 풀려 있어 서버 기록을 지우지 못했어요 — 다시 로그인한 뒤 거두어 주세요'); return; } off('동의를 거두고 서버의 약지도 기록을 지웠어요. 이 폰의 기록은 그대로 있어요.'); })
    .catch(() => toast('서버에 닿지 못해 아직 거두지 못했어요. 인터넷이 연결되면 다시 눌러 주세요.'));
};

const 동의칸 = { terms: 0, privacy: 0 };
function 동의그리기(){
  const C = 동의칸, both = !!(C.terms && C.privacy);
  document.querySelectorAll('.cs-row[data-k]').forEach(b => b.setAttribute('aria-checked', String(!!C[b.dataset.k])));
  const all = document.querySelector('.cs-all'); if (all) all.setAttribute('aria-checked', both ? 'true' : (C.terms || C.privacy) ? 'mixed' : 'false');
  const g = document.getElementById('csGo'); if (g) g.disabled = !both;
  const w = document.getElementById('csWhy'); if (w) w.hidden = both;
}
window.동의누름 = k => { const C = 동의칸; if (k === 'all') { const v = C.terms && C.privacy ? 0 : 1; C.terms = C.privacy = v; } else C[k] = C[k] ? 0 : 1; 동의그리기(); };
/* 10-29 「첫 진입 동의 벽 금지」 — 체크박스 대신 단추 한 번으로 두 필수 동의 */
window.동의한번 = () => { 동의칸.terms = 동의칸.privacy = 1; window.동의하기(); };
window.동의하기 = () => {
  if (!(동의칸.terms && 동의칸.privacy)) return;
  try { localStorage.setItem(CONSENT_KEY, JSON.stringify({ v: CONSENT_VER, at: dayKey(new Date()), terms: 1, privacy: 1 })); } catch (e) {}
  window.__동의됨 = CONSENT_VER;   /* 저장이 막힌 브라우저에서도 이번에는 들어가게 */
  let n = ''; try { n = sessionStorage.getItem(CONSENT_NEXT) || ''; sessionStorage.removeItem(CONSENT_NEXT); } catch (e) {}
  if (/^(consent|doc|login)(\/|\?|$)/.test(n)) n = '';
  HIST.length = 0;   /* 뒤로 가기가 동의 화면으로 돌아가지 않게 */
  const to = n || (helloDone() ? 'home' : 'hello/1');
  try { location.replace(location.href.split('#')[0] + '#/' + to); } catch (e) { go('/' + to); }
};
const 동의줄 = (k, t, s, L, 링크) => `<div class="cs-item"><button type="button" class="cs-row" role="checkbox" aria-checked="${!!동의칸[k]}" data-k="${k}" onclick="동의누름('${k}')"><span class="cs-bx">${I.check}</span><span class="cs-tx"><b><span class="cs-tag">필수</span>${t}</b><span>${s}</span></span></button>
  <details class="cs-more"><summary>자세히${I.chev}</summary><ul>${L.map(x => `<li>${x}</li>`).join('')}</ul><button type="button" class="cs-doc" onclick="go('/doc/${k}')">${링크}${I.chev}</button></details></div>`;
window.문_consent = () => {
  let 전 = null; try { 전 = JSON.parse(localStorage.getItem(CONSENT_KEY) || 'null'); } catch (e) {}
  const 다시 = helloDone() || !!전, both = !!(동의칸.terms && 동의칸.privacy);
  /* 10-30 현욱님 「글 배열·디자인 이상」 — 예전 동의자의 다시 동의: 머리 하나 + 바뀐 것 세 줄 + 「확인하고 계속」 + 작은 자세히(판 번호·전문은 그 안) */
  if (다시) return `<div class="door cs cs-again">
  <img class="door-mark" src="${esc(BRANDMARK)}" alt="" width="64" height="64">
  <h1>약지도 약속이 조금 바뀌었어요</h1>
  <ul class="cs-list">
    <li>${I.book}<span><b>이용약관·개인정보 처리방침이 생겼어요</b><small>약 정보의 기준과 기록을 다루는 방법을 적어 두었어요</small></span></li>
    <li>${I.user}<span><b>계정은 고르는 거예요</b><small>로그인하지 않아도 대부분의 기능을 쓰실 수 있어요</small></span></li>
    <li>${I.lock}<span><b>기록은 먼저 이 휴대폰에</b><small>서버에 저장하는 것은 계정을 만들 때 따로 여쭤요</small></span></li>
  </ul>
  <button type="button" class="door-go" id="csGo" onclick="동의한번()">확인하고 계속</button>
  <details class="cs-more cs-detail"><summary>자세히${I.chev}</summary>
    <p>이용약관 판 ${esc(CONSENT_VER)} · 동의하시면 두 문서에 함께 동의한 것으로 적어 둬요. 예전에 동의하신 날 ${esc((전 && 전.at) || '없음')}.</p>
    <button type="button" class="cs-doc" onclick="go('/doc/terms')">이용약관 전문${I.chev}</button> <button type="button" class="cs-doc" onclick="go('/doc/privacy')">개인정보 처리방침 전문${I.chev}</button>
    <p class="cs-note">동의 내용은 설정 → 약관·개인정보에서 언제든 다시 보실 수 있어요.</p>
  </details>
</div>`;
  return `<div class="door cs">
  <img class="door-mark" src="${esc(BRANDMARK)}" alt="" width="64" height="64">
  <h1>약지도</h1>
  <p class="door-s">어디가 불편한지 고르면, 집에서 할 일 · 약국에서 찾을 약 · 진료가 필요한 신호를 차례로 알려 드려요</p>
  ${다시 ? `<p class="cs-new">${I.info}<span>약지도에 이용약관과 개인정보 처리방침이 새로 생겼어요. 한 번만 확인해 주세요.</span></p>` : ''}
  <ul class="cs-list">
    <li>${I.pill}<span>증상에 맞는 약국 약과 먹는 법을 <b>식약처 허가 설명서</b> 기준으로 알려 드려요.</span></li>
    <li>${I.shield}<span>드시는 약끼리 성분이 겹치거나 함께 드시면 안 되는 조합을 살펴 드려요.</span></li>
    <li>${I.heart}<span>진단·처방을 대신하지 않아요. 급하면 119, 그리고 의사·약사와 상의하세요.</span></li>
  </ul>
  <p class="cs-sum">의료기기가 아니에요 · 기록은 먼저 이 휴대폰에 저장돼요 · 광고·분석에 쓰지 않아요</p>
  <button type="button" class="door-go" id="csGo" onclick="동의한번()">${다시 ? '약관·처리방침에 동의하고 계속' : '약관·처리방침에 동의하고 시작'}</button>
  <details class="cs-more cs-detail"><summary>자세히 — 무엇에 동의하나요${I.chev}</summary>
    <h3>이용약관</h3><p>의료기기가 아니에요. 약 정보를 드리고 기록을 도와요. 약을 고르고 드시는 결정은 의사·약사와 함께 하세요.</p><ul>${['약 설명은 <b>식약처 허가 설명서</b>가 기본이에요. 해외 지침이나 진료실 관행이 다르면 둘 다 보여 드려요.',
    '위험 신호가 있으면 약보다 진료가 먼저예요. 급하면 119예요.',
    '약을 팔거나 건네지 않아요. 약은 약국에서 약사와 상의해 사세요.',
    '계정은 고르실 수 있고, 만 14세 이상만 만들 수 있어요.',
    '지금은 돈을 내는 기능이 없어요. 생기면 요금과 해지·환불 조건을 미리 알리고 따로 동의를 받아요.'].map(x => `<li>${x}</li>`).join('')}</ul><button type="button" class="cs-doc" onclick="go('/doc/terms')">약관 전문 보기${I.chev}</button>
    <h3>개인정보 처리방침</h3><p>드시는 약·기록·몸 상태는 먼저 쓰시는 휴대폰에 저장되고, 광고·분석에 쓰지 않아요. 계정을 만들고 따로 동의하실 때만 메디나눔 서버(서울)에 복사돼요.</p><ul>${['로그인하지 않고도 대부분의 기능을 쓰실 수 있어요.',
    '광고나 이용자 분석 도구를 넣게 되면 먼저 알려요.',
    '서버 저장은 계정을 만들 때 「서버에 저장하기」에 따로 동의하셔야 해요. 거두시면 서버 기록을 바로 지워요.',
    '「부모님께 보내기」를 링크로 보내실 때만 고른 약 목록·호칭·메모가 7일 동안 서버에 머문 뒤 지워져요.',
    '약 사진은 휴대폰 안에서 글자를 읽는 데만 쓰고 보내지 않아요.',
    '기록은 내 정보 → 설정에서 언제든 지우실 수 있어요.'].map(x => `<li>${x}</li>`).join('')}</ul><button type="button" class="cs-doc" onclick="go('/doc/privacy')">전문 보기${I.chev}</button>
    <p class="cs-note">건강에 관한 기록을 서버에 저장하는 것은 계정을 만들 때 따로 여쭤요.</p>
  </details>
  <p class="cs-foot">동의 내용은 설정 → 약관·개인정보에서 언제든 다시 보실 수 있어요 · 약지도 v${esc(D.meta?.version || '')}</p>
</div>`;
};

/* 설정의 「약관·개인정보」 칸 · 내 정보 맨 위 계정 줄 · 처음 안내 끝의 계정 칸 — index 는 ext('이름') 으로 부른다(첫 화면 예산) */
window.약관칸 = () => { const c = consentRec(); return `<section class="sec card" id="legal"><h2>약관·개인정보</h2><div class="rows-l" style="margin-top:10px">${lrow(I.book, '이용약관', '약지도를 쓰실 때의 약속', "go('/doc/terms')")}${lrow(I.lock, '개인정보 처리방침', '무엇을 어디에 두는지', "go('/doc/privacy')")}</div>
  <p class="small muted" style="margin-top:8px">${c && c.at ? `동의한 날 ${esc(c.at)} · 판 ${esc(c.v || '')}` : '동의 기록이 이 휴대폰에 없어요'}</p></section>`; };
/* 설정의 계정 칸(meta.account 가 켜졌을 때만) — 10-14 app-shell 에서 옮김(첫 화면 예산). 내용은 그대로 */
window.계정칸 = () => D.meta?.account !== true ? '' : `<section class="sec card" id="acct"><h2>계정 <small>폰을 바꿔도 이어 보기 · 선택</small></h2>
    <p class="small muted" style="margin:4px 0 12px">로그인하지 않아도 약지도는 쓰실 수 있어요. 로그인하시면 기록을 메디나눔 서버(서울)에 복사해 두어 다른 폰에서 이어 받아요.</p>
    ${계정화면HTML()}
    ${srvAgreed() ? `<button type="button" class="srvlink" onclick="서버동의끄기()">「서버에 저장하기」 동의 거두기</button>` : ''}
  </section>`;
/* 2026-10-29 현욱님 — 설정 맨 위 첫 칸 = 계정 카드. 로그인 전엔 큰 단추 하나, 뒤엔 메일 · 이용권 · 동기화 · 로그아웃 · 계정 지우기(작게). 상세 칸(#acct)은 아래 그대로 */
/* 계정 카드·메디나눔 서명 모양 — 첫 화면 예산 때문에 여기서 붙인다 */
try { const st = document.createElement('style'); st.textContent = ".acct-card .acct-hd{display:flex;align-items:center;gap:12px}.acct-card .acct-hd>span:last-child{display:flex;flex-direction:column;min-width:0}.acct-card .acct-hd b{font-size:1.0625rem;overflow-wrap:anywhere}.acct-card .acct-hd small{color:var(--muted);font-size:.875rem;margin-top:2px}.acct-ic,.acct-av{flex:none;width:44px;height:44px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:var(--tint);color:var(--primary-deep)}.acct-av{background:var(--primary);color:var(--on-primary,#fff);font-weight:700;font-size:1.125rem}.acct-card .acct-go{width:100%;margin-top:14px;min-height:52px;font-size:1.0625rem}.acct-card .acct-act{display:flex;gap:10px;margin-top:14px}.acct-card .acct-act .btn{flex:1;margin:0;min-height:48px}.acct-card .srvrow{margin-top:12px}.acct-card .acct-del{margin-top:6px;font-size:.8125rem}.mn-logo{width:1.35em;height:1.35em;vertical-align:-.3em;margin-right:5px;color:#1A2B4A}.mn-logo path{fill:none;stroke:currentColor;stroke-width:236;stroke-linecap:round;stroke-linejoin:round}.mn-logo .mn-tile{fill:#FFFFFF;stroke:#CBD2DC;stroke-width:24}:root[data-theme=\"dark\"] .mn-logo .mn-tile{display:none}:root[data-theme=\"dark\"] .mn-logo{color:#FFFFFF}@media (prefers-color-scheme:dark){ :root:not([data-theme=\"light\"]) .mn-logo{color:#FFFFFF} :root:not([data-theme=\"light\"]) .mn-logo .mn-tile{display:none} }"; document.head.appendChild(st); } catch (e) {}
/* 10-30 현욱님 「알림 설정은?」 — 알림 한 화면: 무엇을 · 언제 · 켜기/끄기(다섯 앱 같은 꼴: 머리 + 권한 줄 + 종류별 스위치 행) */
window.문_notify = (_, q) => {
  const n = takingItems().length, timed = takingItems().filter(d => !schedUnset(d)).length;
  const perm = NATIVE ? NATIVE_PERM : ('Notification' in window ? Notification.permission : 'unsupported');
  const sw = (k, on, fn) => `<button class="sw ${on ? 'on' : ''}" role="switch" aria-checked="${on}" aria-label="${k}" onclick="${fn}"></button>`;
  const row = (ic, t, s2, on, fn) => `<div class="nt-row"><span class="nt-ic">${ic}</span><span class="nt-t"><b>${t}</b><small>${s2}</small></span>${sw(t, on, fn)}</div>`;
  const vn = (typeof visits === 'function' ? visits() : []).length;
  return `${topBar({ back:'내 정보' })}<h1>알림 설정</h1>
  <p class="nt-perm ${perm === 'granted' ? 'ok' : ''}">${perm === 'granted' ? `${I.check}<span>휴대폰 알림이 켜져 있어요</span>` : perm === 'denied' ? `${I.alert}<span>${typeof NATIVE !== 'undefined' && NATIVE ? '휴대폰 설정에서 약지도 알림이 꺼져 있어요 — 설정 → 앱 → 약지도 → 알림을 켜 주세요' : '이 브라우저에서 약지도 알림이 막혀 있어요 — 주소창 왼쪽 자물쇠 → 알림 → 허용으로 바꿔 주세요'}</span>` : `${I.info}<span>알림을 받으려면 한 번 허락이 필요해요</span><button type="button" class="btn line" onclick="${NATIVE ? 'askNativeNoti()' : 'askNoti()'}">허락하기</button>`}</p>
  <section class="sec card nt-list">
    ${row(I.clock, '약 드실 시간', n ? `시간을 정한 약 ${timed}가지 · 정한 시각에` : '약통에 약을 담고 시간을 고르면 울려요', noteOn('dose'), `setNoteOn('dose',${!noteOn('dose')})`)}
    ${row(I.alert, '아직 안 드셨을 때 한 번 더', '체크가 없으면 30분 뒤 한 번만', noteOn('dose') && noteOn('again'), `setNoteOn('again',${!noteOn('again')})`)}
    ${row(I.pill, '약이 떨어지기 전에', '남은 알 수를 넣은 약 · 5일분 남는 날 아침 9시', noteOn('stock'), `setNoteOn('stock',${!noteOn('stock')})`)}
    ${row(I.cal, '진료 예약', vn ? `예약 ${vn}건 · 전날 저녁 7시와 2시간 전` : '진료 예약을 적어 두면 전날과 2시간 전에', noteOn('visit'), `setNoteOn('visit',${!noteOn('visit')})`)}
    ${row(I.check, '저녁 9시 하루 정리', '그날 체크 안 한 약이 있을 때만 · 기본 꺼짐', eveningOn(), `setEvening(${!eveningOn()})`)}
  </section>
  <div class="actions two"><button class="btn line" onclick="go('/schedule?t=sc1')">${I.clock} 약마다 시간 고르기</button><button class="btn line" onclick="go('/schedule?t=sc2')">${I.pill} 남은 알 수 넣기</button></div>
  <p class="small muted" style="margin-top:12px">알림이 늦거나 안 오면 <button type="button" class="link" onclick="go('/schedule?t=sc4')">알림이 늦어요 도움말</button>을 봐 주세요.</p>
  ${doseSrvHTML()}${famCard(q || {})}`;
};
/* ── 11-02 가족 알림(현욱님 「지금 만든다 · 가족 최대 3명 · 약 이름 뺌」 · 설계 yakjido/가족알림_설계.md) ──
   본인: 초대 코드 6자리(24시간) → 가족이 「받은 코드 넣기」 → 정한 시각 2시간 뒤에도 체크가 없으면 가족 휴대폰에 「아직 체크가 없어요」.
   서버: 함수 yak_family_* · yak_push_* (메디나눔_약지도_가족알림_1102.sql) + 예약 함수 yak-family-check. meta.family 가 true 일 때만 보인다(되는 척 금지). */
const FAMQ = { list: null, busy: false, open: '', msg: '', code: null };
const famOn = () => D.meta?.family === true && D.meta?.account === true;
/* 11-03 「개인 맞춤」(현욱님) — 알림 설정은 yakjido.fam.v1(계정과 함께 서버로 → 서버 알림 함수가 읽음).
   tz = 기기 시간대(기기 설정 값) · wait = 가족에게 알리기까지 1·2·3시간 · qs/qe = 쉬는 시간 · dose = 앱을 닫아도 정시 알림 · nm = 알림에 약 이름(「알림에 약 이름 보이기」를 켰을 때만) */
const FAM_KEY = 'yakjido.fam.v1', FAM_DEF = { wait: 2, qs: '22:00', qe: '07:00', dose: false };
const famPrefs = () => { let o = {}; try { o = JSON.parse(localStorage.getItem(FAM_KEY) || '{}') || {}; } catch (e) {} return { ...FAM_DEF, ...o }; };
function famSave(ch){ const p = { ...famPrefs(), ...(ch || {}) }; try { p.tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Seoul'; } catch (e) { p.tz = 'Asia/Seoul'; } p.lang = typeof LANG !== 'undefined' ? LANG : 'ko';   /* 11-03 알림 글은 받는 사람 말로 */
  if (p.dose && noteName()) { p.nm = {}; for (const d of takingItems()) p.nm[d.id] = String(d.simple && !d.name ? d.simple : d.name || '').slice(0, 30); } else delete p.nm;
  const v = JSON.stringify(p); try { if (localStorage.getItem(FAM_KEY) !== v) localStorage.setItem(FAM_KEY, v); } catch (e) {} }
/* 체크하면 그 자리에서 서버로(오프라인이면 다음 기회에) — 가족 알림 오알림을 줄인다 */
let famUp = 0;
try { const set0 = Storage.prototype.setItem; Storage.prototype.setItem = function (k, v) { set0.call(this, k, v);
  if (this === window.localStorage && k === 'yakjido.me.v1') { clearTimeout(famUp); famUp = setTimeout(() => { try { if (srvLoggedIn()) { famSave(); 서버.올리기().catch(() => {}); } } catch (e) {} }, 1500); } }; } catch (e) {}
try { if (srvLoggedIn()) famSave(); } catch (e) {}
/* 웹 푸시 공개 열쇠(공개 값 · 개인 열쇠는 서버 Vault) — 첫 화면 예산 때문에 meta 가 아니라 여기 */
const FAM_VAPID = 'BLPdgoz3Tcdtm5wQNBSpBKelzaoP_TJ-_iA98wIAlUFmxfL0kKO3MePDvALZMryA8pUMy4r7Mcp5D1JgZPfptSo';
const famRpc = (fn, args) => 서버.준비().then(sb => sb.rpc(fn, args || {})).then(r => { if (r.error) throw r.error; return r.data; });
function famLoad(){ if (FAMQ.busy) return; FAMQ.busy = true; famRpc('yak_family_list').then(d => { FAMQ.list = d || []; }).catch(() => { FAMQ.list = []; FAMQ.msg = '가족 연결을 불러오지 못했어요. 잠시 뒤 다시 열어 주세요.'; }).finally(() => { FAMQ.busy = false; if (/^#\/notify/.test(location.hash)) route(); }); }
const famWhen = t => { try { return new Date(t).toLocaleString('ko-KR', { month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit' }); } catch (e) { return ''; } };
function famCard(q){
  if (!famOn()) return '';
  if (q.code && /^\d{6}$/.test(q.code) && !FAMQ.open) { FAMQ.open = 'join'; FAMQ.code = q.code; }
  const head = `<h2 class="fam-h" id="fam">가족에게 알리기</h2>`;
  /* 11-03 GPT 개인정보 검수 — 「체크 기록 없음 ≠ 안 드심」, 언제·얼마나·멈추는 조건을 동의 전에 보이게 */
  const lead = `<p>약을 드셨는지 체크한 기록이 없으면 연결한 가족에게 알려요. <b>약을 안 드셨다고 확인된 것은 아니에요.</b></p>
    <ul class="fam-rule"><li>정한 복용 시각에서 ${famPrefs().wait}시간이 지난 뒤, 15분마다 하는 확인 때 보내요</li><li>가족 한 분당 하루 최대 2번 · 쉬는 시간(${esc(famPrefs().qs)}~${esc(famPrefs().qe)}, 내 휴대폰 시각)에는 새 알림을 보내지 않아요</li><li>약 이름은 보내지 않아요</li><li>내 기록이 서버에 3일 넘게 올라오지 않으면 알림도 멈춰요. 알림이 없다고 약 체크가 잘되고 있다는 뜻은 아니에요</li></ul>`;
  if (!srvLoggedIn()) return `<section class="sec card fam">${head}${lead}<p>가족이 보낸 코드를 넣어 알림을 받을 수도 있어요. 두 분 모두 로그인이 필요해요.</p>
    <button type="button" class="btn line" onclick="go('/login')">${I.user} 로그인하고 켜기</button></section>`;
  if (FAMQ.list == null) { famLoad(); return `<section class="sec card fam">${head}<p class="small muted">불러오는 중이에요…</p></section>`; }
  const mine = FAMQ.list.filter(x => x.role === 'owner'), watch = FAMQ.list.filter(x => x.role === 'member');
  const ownRow = x => x.status === 'waiting'
    ? `<li><span><b>코드 ${esc(x.code)}</b><small>${esc(famWhen(x.code_expires))}까지 · 받은 분이 넣으면 연결 요청이 와요</small></span><span class="fam-b"><button type="button" class="btn line" onclick="famShare('${esc(x.code)}')">보내기</button><button type="button" class="link" onclick="famEnd('${x.id}')">취소</button></span></li>`
    : x.status === 'asking'
    ? `<li class="fam-hot"><span><b>코드를 받은 분이 연결을 요청했어요</b><small>계정 이메일: <span>${esc(x.other_email || '')}</span><br>이 분께 내 약 체크 알림을 보내도 될까요?</small></span><span class="fam-b"><button type="button" class="btn primary" onclick="famApprove('${x.id}',true)">연결 허락</button><button type="button" class="link" onclick="famApprove('${x.id}',false)">거절</button></span></li>`
    : `<li><span><b>${esc(x.other_email || '가족')}</b><small>연결됨 · 체크 기록이 없으면 이 분께 알려요</small></span><span class="fam-b">${대화단추(x.id)}<button type="button" class="link" onclick="famEnd('${x.id}')">끊기</button></span></li>`;
  const watchRow = x => x.status === 'asking'
    ? `<li><span><b>${esc(x.label)}</b><small>상대가 허락하면 알림이 시작돼요</small></span><span class="fam-b"><button type="button" class="link" onclick="famEnd('${x.id}')">취소</button></span></li>`
    : `<li${q.fam ? ' class="fam-hot"' : ''}><span><b>${esc(x.label)}</b><small>${x.muted_today ? '오늘은 이 분의 새 알림을 보내지 않아요. 연결은 유지돼요.' : '약 체크 기록이 없으면 이 휴대폰으로 알려 드려요'}</small></span><span class="fam-b">${대화단추(x.id)}${x.muted_today ? '' : `<button type="button" class="btn line" onclick="famMute('${x.id}')">이 분 알림 오늘만 끄기</button>`}<button type="button" class="link" onclick="famEnd('${x.id}')">끊기</button></span></li>`;
  const tag = '<em class="door-tag">선택</em>';
  const invite = FAMQ.open === 'invite' ? `<div class="fam-form">
      <label class="fam-l" for="famLabel">가족 화면에 보일 내 이름</label><input id="famLabel" maxlength="20" placeholder="예) 엄마" autocomplete="off">
      <p class="small muted">연결한 가족과 아직 쓰지 않은 초대 코드를 합쳐 최대 3개까지 만들 수 있어요. 코드는 24시간 안에 한 번만 쓸 수 있고, 받은 분이 로그인해 연결을 요청하면 내가 허락해야 알림이 시작돼요.</p>
      <details class="fam-det" open><summary>제공 내용 자세히</summary><dl>
        <dt>받는 분</dt><dd>내가 허락해 연결한 가족(최대 3명)</dd>
        <dt>보내는 정보</dt><dd>내가 정한 이름(호칭), 내 계정 이메일, 복용 예정 시각, 그 시각의 체크 기록이 없다는 것. 약 이름·병·복용 기록 전체는 보내지 않아요</dd>
        <dt>사용 목적</dt><dd>약을 놓쳤을 수 있을 때 가족이 안부를 확인하려고</dd>
        <dt>받는 분의 보유·이용</dt><dd>안부 확인에만 쓰고, 연결을 끊거나 필요 없어지면 지우도록 안내해요. 끊으면 새 알림은 바로 멈춰요. 이미 도착한 알림은 가족 휴대폰에서 직접 지워야 해요</dd>
        <dt>해외 전달</dt><dd>알림은 가족이 쓰는 브라우저·기기 회사(구글·애플·모질라 — 미국 등)의 알림 서버를 거쳐 가요. 전달을 기다리는 동안 최대 1시간 머물 수 있어요</dd>
        <dt>잠금화면</dt><dd>호칭과 복용 시각이 가족 휴대폰 잠금화면에 보일 수 있어요</dd>
        <dt>동의하지 않으면</dt><dd>가족 알림만 쓸 수 없어요. 다른 기능은 그대로 쓸 수 있어요</dd></dl></details>
      <label class="door-ck"><input id="famOk" type="checkbox"><span><b>복용 예정 시각과 약 체크 기록 같은 건강정보를 가족 알림에 쓰고, 연결한 가족에게 제공하는 데 동의해요 ${tag}</b></span></label>
      <label class="door-ck"><input id="famOk2" type="checkbox"><span><b>가족 알림을 전달하려고 알림 내용이 해외 알림 서버를 거치는 데 동의해요 ${tag}</b></span></label>
      <button type="button" class="btn primary" onclick="famInvite()">동의하고 코드 만들기</button></div>` : '';
  const join = FAMQ.open === 'join' ? `<div class="fam-form">
      <label class="fam-l" for="famCode">가족에게 받은 6자리 코드</label><input id="famCode" inputmode="numeric" maxlength="6" autocomplete="one-time-code" value="${esc(FAMQ.code || '')}">
      <details class="fam-det" open><summary>연결하기 전에 확인해 주세요</summary><dl>
        <dt>상대에게 보이는 것</dt><dd>내 계정 이메일 — 서로 연결한 사람이 맞는지 확인하려고요</dd>
        <dt>받는 정보</dt><dd>상대가 정한 이름(호칭), 복용 예정 시각, 그 시각의 체크 기록이 없다는 것. 약을 안 드셨다는 뜻은 아니에요</dd>
        <dt>받은 정보는</dt><dd>안부 확인에만 써 주세요. 연결을 끊거나 필요 없어지면 휴대폰에서 지워 주세요. 이미 도착한 알림은 자동으로 지워지지 않아요</dd>
        <dt>잠금화면</dt><dd>호칭과 복용 시각이 이 휴대폰 잠금화면에 보일 수 있어요. 원하지 않으면 휴대폰 설정에서 알림 미리보기를 꺼 주세요</dd>
        <dt>해외 전달</dt><dd>알림은 이 휴대폰의 브라우저·기기 회사 알림 서버(미국 등)를 거쳐 와요</dd>
        <dt>동의하지 않으면</dt><dd>연결하지 않아도 돼요. 다른 기능은 그대로 쓸 수 있어요</dd></dl></details>${pushNote()}
      <label class="door-ck"><input id="famJoinOk" type="checkbox"><span><b>내 계정 이메일을 상대에게 보여 주고, 위 내용으로 알림을 받는 데 동의해요 ${tag}</b></span></label>
      <p class="small muted">상대가 허락하면 알림이 시작돼요. 알림 허락을 한 번 여쭤요.</p>
      <button type="button" class="btn primary" onclick="famJoin()">동의하고 연결 요청하기</button></div>` : '';
  return `<section class="sec card fam">${head}${lead}
    ${FAMQ.msg ? `<p class="fam-msg" role="status">${esc(FAMQ.msg)}</p>` : ''}
    ${mine.length ? `<h3 class="fam-s">내 약 체크를 받는 가족</h3><ul class="fam-ul">${mine.map(ownRow).join('')}</ul>` : ''}
    ${watch.length ? `<h3 class="fam-s">내가 챙기는 분</h3><ul class="fam-ul">${watch.map(watchRow).join('')}</ul><button type="button" class="link fam-off" onclick="famPushOff()">이 휴대폰에서 가족 알림 받기 끄기</button>` : ''}
    ${mine.length ? famSetHTML() : ''}
    <div class="actions two">${mine.length < 3 ? `<button type="button" class="btn line" aria-expanded="${FAMQ.open === 'invite'}" onclick="FAMQ.open=FAMQ.open==='invite'?'':'invite';FAMQ.msg='';route()">가족 초대하기</button>` : ''}<button type="button" class="btn line" aria-expanded="${FAMQ.open === 'join'}" onclick="FAMQ.open=FAMQ.open==='join'?'':'join';FAMQ.msg='';route()">받은 코드 넣기</button></div>
    ${invite}${join}</section>`;   /* 아이폰 안내는 위 「앱을 닫아도 제시간에」 칸에 한 번 */
}
const famIos = () => `<p class="small muted fam-ios">아이폰은 사파리에서 공유 → 홈 화면에 추가한 뒤, 그 아이콘으로 연 약지도에서만 알림을 받을 수 있어요(iOS 16.4 이상).</p>`;   /* 6 — 아이폰 안내는 늘 보이게 */
/* 본인: 가족에게 알리기까지 기다리는 시간 · 쉬는 시간(야간 근무면 낮으로) */
function famSetHTML(){ const p = famPrefs();
  return `<details class="fam-det"><summary>내 가족 알림 설정</summary>
    <p class="fam-l">가족에게 알리기까지</p><div class="seg fam-seg" role="group">${[1, 2, 3].map(h => `<button type="button" class="${p.wait === h ? 'on' : ''}" aria-pressed="${p.wait === h}" onclick="famSet({wait:${h}})">${h}시간</button>`).join('')}</div>
    <p class="fam-l">쉬는 시간 <small class="muted">이 시간에는 가족에게 새 알림을 보내지 않아요 · 내 휴대폰 시각</small></p>
    <div class="fam-q"><input type="time" id="famQs" value="${esc(p.qs)}" aria-label="쉬는 시간 시작"><span>~</span><input type="time" id="famQe" value="${esc(p.qe)}" aria-label="쉬는 시간 끝"><button type="button" class="btn line" onclick="famSet({qs:document.getElementById('famQs').value,qe:document.getElementById('famQe').value})">저장</button></div></details>`; }
function famSet(ch){ if (ch.qs != null && !/^([01]\d|2[0-3]):[0-5]\d$/.test(ch.qs + '') || ch.qe != null && !/^([01]\d|2[0-3]):[0-5]\d$/.test(ch.qe + '')) { FAMQ.msg = '시각을 다시 골라 주세요.'; route(); return; }
  famSave(ch); 서버.올리기().catch(() => {}); FAMQ.msg = '저장했어요. 다음 확인부터 이대로 보내요.'; route(); }
/* 본인: 앱을 닫아도 제시간에(웹 — 설치 앱은 휴대폰 자체 알람이라 필요 없다) */
/* 11-03 공용 푸시 부품 동의HTML 과 같은 뜻 — 켜는 칸 아래 한 줄 + 약지도 처리방침(국외 이전 7절) */
const pushNote = () => '<p class="small muted">켜면 이 기기의 알림 받을 주소·언어·시간대를 서버에 둡니다. 끄면 바로 지워요. <a href="privacy.html#s7" target="_blank" rel="noopener">처리방침</a></p>';
function doseSrvHTML(){
  if (!famOn() || (typeof NATIVE !== 'undefined' && NATIVE)) return '';
  const on = famPrefs().dose && srvLoggedIn();
  return `<section class="sec card fam">${'<h2 class="fam-h">앱을 닫아도 제시간에</h2>'}
    <p>앱을 닫아 두어도 약 드실 시간에 알려 드려요. 서버가 5분마다 확인해서 복용 시각 앞뒤 3분 안에 한 번 보내요. 알림에서 바로 「먹었어요」·「10분 뒤 다시」를 누를 수 있어요.</p>
    <p class="small muted">약 이름은 「알림에 약 이름 보이기」를 켰을 때만 넣어요 — 잠금화면에 보일 수 있어요.</p>
    ${!srvLoggedIn() ? `<button type="button" class="btn line" onclick="go('/login')">${I.user} 로그인하고 켜기</button>`
      : on ? `<p class="fam-msg">켜져 있어요</p><button type="button" class="link" onclick="doseSrv(false)">끄기</button>`
      : `<label class="door-ck"><input id="doseOk" type="checkbox"><span><b>정시 알림을 전달하려고 알림 내용(복용 시각, 켠 경우 약 이름)이 이 휴대폰 브라우저 회사의 해외 알림 서버를 거치는 데 동의해요 <em class="door-tag">선택</em></b><small>동의하지 않아도 앱이 열려 있을 때의 알림은 그대로예요.</small></span></label>
         <button type="button" class="btn primary" onclick="doseSrv(true)">동의하고 켜기</button>`}
    ${pushNote()}${famIos()}</section>`; }
function doseSrv(on){
  if (on && !document.getElementById('doseOk')?.checked) { FAMQ.msg = '켜려면 동의에 체크해 주세요.'; route(); return; }
  (on ? famPush() : Promise.resolve()).then(() => { famSave({ dose: !!on, doseAt: on ? new Date().toISOString() : null }); return 서버.올리기(); })
    .then(() => { FAMQ.msg = on ? '켰어요. 앱을 닫아도 제시간에 알려 드려요.' : '껐어요. 앱이 열려 있을 때의 알림은 그대로예요.'; }).catch(e => { FAMQ.msg = famErr(e); }).finally(() => route()); }
const famErr = e => { const m = String((e && (e.message || e.code)) || e); return /family limit/.test(m) ? '가족은 3명까지 연결할 수 있어요.' : /too many/.test(m) ? '코드를 너무 여러 번 넣었어요. 한 시간 뒤에 다시 해 주세요.' : /self/.test(m) ? '내가 만든 코드예요. 가족 휴대폰에서 넣어 주세요.' : /already/.test(m) ? '이미 연결된 분이에요.' : /nopush/.test(m) ? '이 브라우저는 알림을 받을 수 없어요. 아이폰은 사파리 공유 → 홈 화면에 추가한 뒤 그 아이콘으로 열어 주세요.' : /denied/.test(m) ? '알림이 막혀 있어요. 위의 안내대로 알림을 허용한 뒤 다시 눌러 주세요.' : '잠시 뒤 다시 해 주세요.'; };
function famShare(code){ const url = (D.meta?.webUrl || 'https://yakjido.medinanum.com/') + '#/notify?code=' + code;
  shareOut({ title: '약지도 가족 알림', text: `[약지도] 제 약 체크를 놓치면 알려 주는 가족 알림 코드예요: ${code} (24시간)\n약지도 → 내 정보 → 알림 설정 → 받은 코드 넣기\n${url}` }).catch(() => {}); }
function famInvite(){ const ok = document.getElementById('famOk'), ok2 = document.getElementById('famOk2'); if (!ok || !ok.checked || !ok2 || !ok2.checked) { FAMQ.msg = '가족 알림을 쓰려면 두 가지 동의에 모두 체크해 주세요. 동의하지 않아도 다른 기능은 그대로 쓸 수 있어요.'; route(); return; }
  const label = (document.getElementById('famLabel')?.value || '').trim() || '가족';
  famRpc('yak_family_invite', { p_label: label, p_consent: true }).then(d => { const c = d && d[0] && d[0].code; FAMQ.open = ''; FAMQ.msg = c ? `코드 ${c} 를 만들었어요. 가족에게 보내 주세요.` : ''; FAMQ.list = null; if (c) famShare(c); })
    .catch(e => { FAMQ.msg = famErr(e); }).finally(() => route()); }
const b64u = s => { const p = '='.repeat((4 - s.length % 4) % 4), b = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from(b, c => c.charCodeAt(0)); };
async function famPush(){
  if (!('serviceWorker' in navigator) || !('PushManager' in window) || !FAM_VAPID) throw new Error('nopush');
  const p = await Notification.requestPermission(); if (p !== 'granted') throw new Error('denied');
  const reg = await navigator.serviceWorker.ready; let sub = await reg.pushManager.getSubscription();
  if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64u(FAM_VAPID) });
  const j = sub.toJSON();
  /* 11-03 서버가 공용 푸시(mn-push-check)로 바뀜 — 공용 표가 정본. 옛 yak_push_subs 는 남겨 두되 실패해도 넘어감 */
  await famRpc('mn_push_save', { p_app: 'yakjido', p_endpoint: j.endpoint, p_p256dh: j.keys.p256dh, p_auth: j.keys.auth, p_lang: typeof LANG !== 'undefined' ? LANG : 'ko', p_tz: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Seoul' });
  try { await famRpc('yak_push_save', { p_endpoint: j.endpoint, p_p256dh: j.keys.p256dh, p_auth: j.keys.auth }); } catch (e) {}
}
function famJoin(){ const c = (document.getElementById('famCode')?.value || '').replace(/\D/g, ''); FAMQ.code = c;
  if (c.length !== 6) { FAMQ.msg = '6자리 숫자를 넣어 주세요.'; route(); return; }
  if (!document.getElementById('famJoinOk')?.checked) { FAMQ.msg = '연결하려면 동의에 체크해 주세요. 연결하지 않아도 다른 기능은 그대로 쓸 수 있어요.'; route(); return; }
  famPush().then(() => famRpc('yak_family_accept', { p_code: c })).then(d => { if (!d || !d.length) { FAMQ.msg = '코드가 맞지 않거나 24시간이 지났어요. 가족에게 새 코드를 받아 주세요.'; return; }
      FAMQ.open = ''; FAMQ.code = null; FAMQ.list = null; FAMQ.msg = `${d[0].owner_label} 님께 연결을 요청했어요. 상대가 허락하면 알림이 시작돼요.`; })
    .catch(e => { FAMQ.msg = famErr(e); }).finally(() => route()); }
function famEnd(id){ if (!confirm('연결을 끊을까요? 새 알림은 바로 멈추고 연결 기록은 지워요.')) return; famRpc('yak_family_end', { p_id: id }).then(() => { FAMQ.list = null; FAMQ.msg = '끊었어요.'; }).catch(e => { FAMQ.msg = famErr(e); }).finally(() => route()); }
function famMute(id){ const u = new Date(); u.setHours(24, 0, 0, 0); famRpc('yak_family_mute', { p_id: id, p_until: u.toISOString() }).then(() => { FAMQ.list = null; FAMQ.msg = '오늘은 알림을 보내지 않을게요.'; }).catch(e => { FAMQ.msg = famErr(e); }).finally(() => route()); }
function famApprove(id, ok){ famRpc('yak_family_approve', { p_id: id, p_ok: !!ok }).then(() => { FAMQ.list = null; FAMQ.msg = ok ? '연결했어요. 이제 약 체크 기록이 없으면 이 분께 알려요.' : '거절했어요. 연결 요청을 지웠어요.'; }).catch(e => { FAMQ.msg = famErr(e); }).finally(() => route()); }
async function famPushOff(){ try { const reg = await navigator.serviceWorker.ready, sub = await reg.pushManager.getSubscription(); if (sub) { await famRpc('yak_push_drop', { p_endpoint: sub.endpoint }).catch(() => {}); await famRpc('mn_push_drop', { p_endpoint: sub.endpoint }).catch(() => {}); await sub.unsubscribe(); } FAMQ.msg = '이 휴대폰에서 가족 알림 받기를 껐어요. 등록된 알림 주소도 지웠어요.'; } catch (e) { FAMQ.msg = famErr(e); } route(); }
Object.assign(window, { FAMQ, famShare, famInvite, famJoin, famEnd, famMute, famApprove, famPushOff, famSet, doseSrv });
/* ── 11-03 현욱님 「내 병력」 — 약만 보고는 왜 드시는지 알 수 없다(클로피도그렐: 스텐트? 뇌경색?). 환자·보호자가 병력·시술·병원을 적어 두고,
   처음 가는 병원·응급실에서 한 장으로 보여 준다. 약 → 「보통 이런 때 써요」는 식약처 허가 효능·효과를 줄인 «후보»일 뿐 — 앱이 정하지 않고 사람이 고른다(진단 아님).
   저장: yakjido.hx.v1(계정과 함께 서버로 — 서버.설치 열쇠). 응급 정보라 보기는 늘 열림 */
const HX_KEY = 'yakjido.hx.v1';
/* 약 갈래 → 성분 낱말(약봉투로 담은 처방약 이름·성분에서 찾기) · 보통 쓰는 경우(식약처 허가 효능·효과 요약) */
/* 11-03 GPT 약사 검수 반영: 끝 글자(프라졸·스타틴·티딘·프릴…)로 찾으면 아리피프라졸·니스타틴·아자시티딘·프릴로카인이 걸리고 프로프라놀롤·설트랄린을 놓친다
   → 성분 이름 전체로 찾는다. 셋째 칸 = 성분·함량에 따라 갈리는 쓰임([찾을 글, 쓰임] — 먼저 맞는 것). 쓰임은 «후보» — 해당 성분·제품 허가에 있는 것만 표시 */
const HX_MG = n => new RegExp('(^|[^\\d.])' + n.replace('.', '\\.') + '\\s*(mg|밀리그램)', 'i');
const HX_USE = {
  'bp.arb': [['사르탄'], ['고혈압', '심부전(일부 성분)', '당뇨병으로 생긴 콩팥병(일부 성분)']],
  'bp.acei': [['캅토프릴', '에날라프릴', '라미프릴', '페린도프릴', '리시노프릴', '이미다프릴', '포시노프릴', '실라자프릴', '베나제프릴', '퀴나프릴', '조페노프릴'],
    ['고혈압', '심부전(일부 성분)', '심근경색 뒤 심장 기능 저하(일부 성분)', '당뇨병으로 생긴 콩팥병·단백뇨(일부 성분)'],
    [[/라미프릴/, ['고혈압', '심부전', '심근경색 뒤 심장 기능 저하', '당뇨병으로 생긴 콩팥병·단백뇨', '심근경색·뇌졸중 위험 줄이기(위험이 높은 분)']]]],
  'bp.ccb': [['디핀'], ['고혈압', '협심증(일부 성분·제품)'], [[/레르카니디핀/, ['고혈압']]]],
  'bp.beta': [['프로프라놀롤', '아테놀롤', '비소프롤롤', '메토프롤롤', '네비보롤', '카르베딜롤', '베탁솔롤', '셀리프롤롤', '라베탈롤', '에스몰롤'],
    ['고혈압', '협심증(일부 성분)', '심부전(일부 성분)', '빠른 맥박·부정맥(일부 성분)'],
    [[/프로프라놀롤/, ['고혈압', '협심증', '빠른 맥박·부정맥', '갑상선 기능 항진 증상 조절', '비후성 심근병증(심장 근육이 두꺼워짐)']]]],
  'bp.diur': [['티아지드', '클로르탈리돈', '푸로세미드', '스피로노락톤', '인다파미드', '토라세미드', '토르세미드', '에플레레논'],
    ['고혈압(해당 제품)', '몸이 붓는 병(심부전·콩팥·간)'],
    [[/스피로노락톤/, ['고혈압', '몸이 붓는 병(심부전·콩팥·간)', '알도스테론 호르몬 과다', '혈액 속 칼륨 부족']]]],
  'bp.dig': [['디곡신'], ['심부전', '심방세동·심방조동(빠른 맥박 조절)', '발작성 심방빈맥']],
  'bp.nitrate': [['니트로글리세린', '니코란딜', /이소소르비드\S*질산|질산\S*이소소르비드/], ['협심증']],
  'dm.met': [['메트포르민'], ['제2형 당뇨병']], 'dm.glip': [['글립틴'], ['제2형 당뇨병']], 'dm.su': [['글리메피리드', '글리클라지드', '글리피지드'], ['제2형 당뇨병']],
  'dm.sglt': [['글리플로진'], ['제2형 당뇨병', '심부전(일부 성분)', '만성 콩팥병(일부 성분)']],
  'chol.statin': [['아토르바스타틴', '로수바스타틴', '피타바스타틴', '심바스타틴', '프라바스타틴', '플루바스타틴', '로바스타틴'],
    ['콜레스테롤이 높음(이상지질혈증)', '심근경색·뇌졸중 위험 줄이기(해당 성분·허가 조건에 맞는 분)']],
  'blood.aspirin': [[], ['심근경색·뇌경색·불안정협심증 뒤 혈전 예방', '심장 혈관 시술(스텐트)·우회수술 뒤 혈전 예방', '심혈관질환 위험이 높아 예방으로 드심(병이 없어도 처방될 수 있어요)']],
  'blood.clopi': [['클로피도그렐'], ['급성 관상동맥증후군·관상동맥 스텐트(심장 혈관 시술)', '심근경색 뒤', '뇌경색 뒤', '말초동맥질환(다리 혈관이 좁아짐)', '심방세동 혈전 예방(아스피린과 함께·허가 조건에 맞는 분)']],
  'blood.warf': [['와파린'], ['심방세동(뇌졸중 예방)', '다리 혈전·폐색전', '인공 심장판막']],
  'blood.doac': [['리바록사반', '아픽사반', '에독사반', '다비가트란'], ['심방세동(뇌졸중 예방)', '다리 깊은 정맥 혈전·폐색전 치료와 재발 예방', '무릎·고관절 수술 뒤 혈전 예방(해당 제품)'],
    [[t => /리바록사반/.test(t) && HX_MG('2.5').test(t), ['관상동맥질환·말초동맥질환 혈전 예방(아스피린 등과 함께)', '급성 관상동맥증후군 뒤 혈전 예방']]]],
  'blood.other': [['실로스타졸', '사르포그렐레이트'], ['말초동맥질환(다리 혈관이 좁아짐)', '뇌경색 뒤 재발 예방(실로스타졸)']],
  'gi.ppi': [['오메프라졸', '에스오메프라졸', '란소프라졸', '덱스란소프라졸', '판토프라졸', '라베프라졸', '일라프라졸', '테고프라잔', '펙수프라잔', '보노프라잔'],
    ['위식도 역류', '위·십이지장 궤양(해당 제품)', '헬리코박터 제균(해당 제품·항생제와 함께)', '소염진통제·아스피린 드시는 동안 궤양 예방(해당 제품)']],
  'gi.h2': [['파모티딘', '시메티딘', '니자티딘', '라푸티딘', '록사티딘', '라니티딘'], ['위·십이지장 궤양', '위식도 역류', '위염(해당 제품)']],
  'mind.ssri': [['설트랄린', '세르트랄린', '에스시탈로프람', '플루옥세틴', '파록세틴', '플루복사민'],
    ['우울증', '불안장애·공황장애(일부 성분)', '강박장애(일부 성분)', '외상후스트레스장애(일부 성분)', '월경 전 불쾌장애(일부 성분)'],
    [[/플루옥세틴/, ['우울증', '강박장애', '신경성 폭식증', '월경 전 불쾌장애(해당 제품)']]]],
  'mind.tca': [['아미트리프틸린', '노르트립틸린', '이미프라민', '클로미프라민'], ['우울증', '야뇨증(일부 성분·제품)']],
  'mind.zdrug': [['졸피뎀'], ['불면증']],
  'mind.bzd': [['디아제팜', '로라제팜', '클로나제팜', '알프라졸람', '트리아졸람', '에티졸람', '브로마제팜', '클로르디아제폭시드', '클로티아제팜', '플루라제팜', '플루니트라제팜'],
    ['불안장애(일부 성분)', '공황장애(일부 성분)', '불면증(일부 성분)', '근육 경련·긴장(일부 성분)', '뇌전증·발작(일부 성분)'],
    [[/클로나제팜/, ['뇌전증·발작', '공황장애']], [/알프라졸람/, ['불안장애', '공황장애']], [/디아제팜/, ['불안', '근육 경련·긴장', '발작 조절']], [/트리아졸람|플루라제팜|플루니트라제팜/, ['불면증']]]],
  'mind.li': [['탄산리튬', '리튬'], ['양극성 장애(조울병)']],
  'mind.aed': [['카르바마제핀', '발프로', '레비티라세탐', '라모트리진', '토피라메이트', '옥스카르바제핀', '라코사미드'],
    ['뇌전증(경련)', '양극성 장애(일부 성분·제품)', '삼차신경통(카르바마제핀)', '편두통 예방(토피라메이트)'],
    [[/토피라메이트/, ['뇌전증(경련)', '편두통 예방']], [/카르바마제핀/, ['뇌전증(경련)', '삼차신경통', '양극성 장애(해당 제품)']]]],
  'pros.alpha': [['탐스로신', '실로도신', '알푸조신', '독사조신', '테라조신', '나프토피딜'], ['전립선비대증(소변 보기 불편)'],
    [[/독사조신|테라조신/, ['전립선비대증(소변 보기 불편)', '고혈압(해당 제품)']]]],
  'pros.5ari': [['피나스테리드', '두타스테리드'], ['전립선비대증(해당 제품)', '남성형 탈모(해당 제품)'],
    [[t => /피나스테리드/.test(t) && HX_MG('1').test(t), ['남성형 탈모']], [t => /피나스테리드/.test(t) && HX_MG('5').test(t), ['전립선비대증(소변 보기 불편)']]]],
  'blad.oab': [['솔리페나신', '다리페나신', '톨테로딘', '페소테로딘', '옥시부티닌', '프로피베린', '트로스피움'], ['과민성 방광(소변이 잦고 급함)']], 'blad.b3': [['미라베그론', '비베그론'], ['과민성 방광(소변이 잦고 급함)']],
  'thy.levo': [['레보티록신', '레보치록신', '리오티로닌'], ['갑상선 호르몬 부족(갑상선 기능 저하증·수술 뒤 포함)']],
  'gout.allo': [['알로푸리놀', '알로퓨리놀', '페북소스타트'], ['통풍(요산 낮추기)'], [[/알로[푸퓨]리놀/, ['통풍(요산 낮추기)', '요산이 높음(고요산혈증)', '요산으로 생긴 콩팥병']]]],
  'gout.colch': [['콜히친'], ['통풍 발작 치료·예방']],
  'dem.ache': [['도네페질', '리바스티그민', '갈란타민'], ['알츠하이머 치매', '파킨슨병 치매(리바스티그민)']], 'dem.mem': [['메만틴'], ['알츠하이머 치매']],
  'park.maob': [['라사길린', '셀레길린', '사피나미드'], ['파킨슨병']], 'park.dopa': [['로피니롤', '프라미펙솔', '레보도파'], ['파킨슨병', '하지불안증후군(로피니롤·프라미펙솔)']],
  'bone.bis': [['알렌드론산', '리세드론산', '이반드론산', '졸레드론산', '파미드론산'], ['골다공증(해당 제품)'],
    [[t => /파미드론산/.test(t) || (/졸레드론산/.test(t) && HX_MG('4').test(t)), ['암으로 혈액 속 칼슘이 높아짐', '암의 뼈 전이·다발골수종 뼈 합병증 관리']]]],
  'resp.luka': [['몬테루카스트', '프란루카스트', '자피르루카스트'], ['천식', '알레르기 비염']], 'resp.theo': [['테오필린', '아미노필린', '독소필린'], ['천식', '만성 폐쇄성 폐질환']],
  'pain.gaba': [['가바펜틴', '프레가발린', '미로가발린'], ['신경병증 통증(대상포진 뒤·당뇨병)', '뇌전증·부분 발작(해당 제품)', '섬유근육통(프레가발린 해당 제품)']],
  'eye.glau': [['라타노프로스트', '타플루프로스트', '트라보프로스트', '비마토프로스트', '도르졸라미드', '브린졸라미드', '브리모니딘'], ['녹내장·높은 안압']], 'eye.beta': [['티몰롤'], ['녹내장·높은 안압']],
  'ster.pred': [['프레드니솔론', '메틸프레드니솔론', '덱사메타손'], ['여러 염증·면역 질환(류마티스·천식 악화·피부병·콩팥병 등) — 왜 드시는지 꼭 적어 두세요']],
};
const hxHit = (w, t) => typeof w === 'string' ? t.includes(w) : typeof w === 'function' ? w(t) : w.test(t);
const HX_COMMON = ['관상동맥 스텐트(심장 혈관 시술)', '심근경색', '협심증', '심부전', '심방세동', '뇌경색', '뇌출혈', '고혈압', '당뇨병', '만성 콩팥병', '투석', '간경변', '천식', '만성 폐쇄성 폐질환', '갑상선 수술', '암', '장기 이식', '인공 관절 수술', '심장 판막 수술', '뇌전증'];
const hxRead = () => { try { const o = JSON.parse(localStorage.getItem(HX_KEY) || '{}'); return Array.isArray(o.list) ? o.list : []; } catch (e) { return []; } };
const hxWrite = L => { try { localStorage.setItem(HX_KEY, JSON.stringify({ list: L.slice(0, 40), t: Date.now() })); } catch (e) {} };
/* 드시는 약 → 보통 쓰는 경우 후보 */
function hxSuggest(){
  const out = [];
  for (const d of takingItems()) {
    let k = d.id.startsWith('cls:') ? d.id.slice(4) : '';
    if (!HX_USE[k]) { k = ''; const txt = ((d.pub && (d.pub.ingr || '')) + ' ' + d.name); if (d.pub && d.pub.rx) for (const [kk, [kw]] of Object.entries(HX_USE)) if (kw.some(w => hxHit(w, txt))) { k = kk; break; }
      if (!k && /아스피린/.test(txt) && /(^|[^\d])100\s*(mg|밀리그램)/i.test(txt)) k = 'blood.aspirin'; }   /* 심장 때문에 드시는 저용량 아스피린(일반약) */
    if (k && HX_USE[k]) { const t = ((d.pub && (d.pub.ingr || '')) + ' ' + d.name), o = (HX_USE[k][2] || []).find(([w]) => hxHit(w, t)); out.push({ d, k, uses: o ? o[1] : HX_USE[k][1] }); }
  }
  return out;
}
const HXQ = { open: '', pre: '', src: '', edit: -1 };
window.병력칸 = () => {
  const L = hxRead(), S = hxSuggest(), now = new Date().getFullYear();
  const row = (x, i) => `<li><span><b>${esc(x.t)}</b><small>${esc([x.y ? x.y + '년' + (x.m ? ' ' + x.m + '월' : '') : '', x.where, x.note].filter(Boolean).join(' · ') || '언제·어디서는 비워 두셨어요')}${x.src ? ' · ' + esc(x.src) + ' 때문에 적음' : ''}</small></span><span class="fam-b"><button type="button" class="link" onclick="hxEdit(${i})">고치기</button><button type="button" class="link" onclick="hxDel(${i})">지우기</button></span></li>`;
  const sel = (id, n0, n1, v, unit) => `<select id="${id}" class="hx-sel"><option value="">${unit === '년' ? '연도' : '월'}</option>${Array.from({ length: n1 - n0 + 1 }, (_, i) => unit === '년' ? n1 - i : n0 + i).map(n => `<option value="${n}"${String(v) === String(n) ? ' selected' : ''}>${n}${unit}</option>`).join('')}</select>`;
  const e = HXQ.edit >= 0 ? L[HXQ.edit] || {} : {};
  const form = HXQ.open ? `<div class="fam-form">
      <label class="fam-l" for="hxT">무엇을 — 병·시술·수술</label><input id="hxT" list="hxCommon" maxlength="60" value="${esc(e.t || HXQ.pre || '')}" placeholder="예) 관상동맥 스텐트"><datalist id="hxCommon">${HX_COMMON.map(t => `<option value="${esc(t)}">`).join('')}</datalist>
      <span class="fam-l">언제 <small class="muted">대략이라도 괜찮아요</small></span><div class="fam-q">${sel('hxY', now - 80, now, e.y, '년')}${sel('hxM', 1, 12, e.m, '월')}</div>
      <label class="fam-l" for="hxW">어느 병원</label><input id="hxW" maxlength="40" value="${esc(e.where || '')}" placeholder="예) 경북대병원 순환기내과">
      <label class="fam-l" for="hxN">메모 <small class="muted">선택</small></label><input id="hxN" maxlength="80" value="${esc(e.note || '')}" placeholder="예) 스텐트 2개 · 1년간 두 가지 피 묽게 하는 약">
      <div class="actions two"><button type="button" class="btn primary" onclick="hxSave()">저장</button><button type="button" class="btn line" onclick="HXQ.open='';HXQ.edit=-1;route()">닫기</button></div></div>` : '';
  return `<section class="sec card hx" id="hx"><h2 class="fam-h">내 병력 · 시술</h2>
    <p class="small">어디서 진료받든 설명하기 쉽게 적어 두세요. 처음 가는 병원·응급실에서 <b>한 장으로 보여 줄 수 있어요.</b></p>
    ${L.length ? `<ul class="fam-ul">${L.map(row).join('')}</ul>` : '<p class="small muted">아직 적은 것이 없어요.</p>'}
    ${S.length ? `<div class="hx-sug"><p class="fam-l">드시는 약은 보통 이런 때 써요 <small class="muted">약만으로는 이유를 알 수 없어요. 해당하는 것만 눌러 적어 두세요 — 진단이 아니에요</small></p>${S.map(s => `<div class="hx-s"><b>${esc(s.d.name)}</b><div class="chips">${s.uses.map(u => L.some(x => x.t === u) ? `<span class="chip on" aria-disabled="true">${I.check} <span>${esc(u)}</span><span> · 적어 둠</span></span>` : `<button type="button" class="chip" onclick="hxAdd(${esc(JSON.stringify(u))},${esc(JSON.stringify(s.d.name))})">${I.plus || '+'} <span>${esc(u)}</span></button>`).join('')}</div></div>`).join('')}<p class="small muted">출처: 식약처 의약품 허가사항(효능·효과)을 줄인 것</p></div>` : ''}
    <div class="actions two"><button type="button" class="btn line" onclick="hxAdd('','')">직접 적기</button><button type="button" class="btn${L.length ? ' primary' : ' line'}" onclick="hxShow()">병원에서 보여 주기</button></div>
    ${form}</section>`;
};
function hxAdd(t, src){ HXQ.open = 'add'; HXQ.pre = t || ''; HXQ.src = src || ''; HXQ.edit = -1; route(); setTimeout(() => document.getElementById('hxY')?.focus(), 50); }
function hxEdit(i){ HXQ.open = 'edit'; HXQ.edit = i; HXQ.pre = ''; HXQ.src = ''; route(); }
function hxDel(i){ if (!confirm('이 줄을 지울까요?')) return; const L = hxRead(); L.splice(i, 1); hxWrite(L); toast('지웠어요'); route(); }
function hxSave(){ const v = id => (document.getElementById(id)?.value || '').trim(); const t = v('hxT').replace(/[<>]/g, '');
  if (!t) { toast('무엇인지 적어 주세요'); document.getElementById('hxT')?.focus(); return; }
  const L = hxRead(), x = { t: t.slice(0, 60), y: v('hxY') || '', m: v('hxM') || '', where: v('hxW').replace(/[<>]/g, '').slice(0, 40), note: v('hxN').replace(/[<>]/g, '').slice(0, 80) };
  if (HXQ.edit >= 0 && L[HXQ.edit]) { x.src = L[HXQ.edit].src || ''; L[HXQ.edit] = x; } else { x.src = HXQ.src || ''; L.push(x); }
  hxWrite(L); HXQ.open = ''; HXQ.edit = -1; toast('적어 두었어요'); route(); }
/* 병원에서 보여 주기 — 화면 가득 큰 글씨 한 장(응급 정보라 늘 열림) */
function hxShow(){
  const L = hxRead(), meds = takingItems(), al = (ME.ae || []).map(x => x.n || x.id).filter(Boolean), cs = (typeof condOn === 'function' ? condOn() : []).map(c => Array.isArray(c) ? c[1] : ((typeof FLAG_LABEL !== 'undefined' && FLAG_LABEL[c]) || c));
  const why = n => L.filter(x => x.src === n).map(x => x.t);
  document.querySelectorAll('.hx-show').forEach(x => x.remove());
  const el = document.createElement('div'); el.className = 'hx-show'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('aria-label', '병원에서 보여 주기');
  el.innerHTML = `<div class="hx-in"><button type="button" class="btn line hx-x" onclick="this.closest('.hx-show').remove()">${I.x} 닫기</button>
    <h1>진료 보실 때 보여 주세요</h1><p class="small muted">${esc(new Date().toLocaleDateString('ko-KR'))} · 약지도에 본인·보호자가 적은 내용이에요</p>
    <h2>병력 · 시술</h2>${L.length ? `<ul>${L.map(x => `<li><b>${esc(x.t)}</b>${x.y ? ` — ${esc(x.y)}년${x.m ? ' ' + esc(x.m) + '월' : ''}` : ''}${x.where ? ` · ${esc(x.where)}` : ''}${x.note ? `<br><span>${esc(x.note)}</span>` : ''}</li>`).join('')}</ul>` : '<p>적은 것이 없어요</p>'}
    ${cs.length ? `<h2>건강 상태</h2><p>${cs.map(esc).join(' · ')}</p>` : ''}
    <h2>드시는 약</h2>${meds.length ? `<ul>${meds.map(d => `<li><b>${esc(d.name)}</b>${why(d.name).length ? ` — ${esc(why(d.name).join(', '))} 때문에` : ''}</li>`).join('')}</ul>` : '<p>담은 약이 없어요</p>'}
    <h2>약 알레르기 · 부작용</h2><p>${al.length ? al.map(esc).join(' · ') : '적은 것이 없어요'}</p></div>`;
  document.body.appendChild(el); el.querySelector('.hx-x').focus();
  /* 화면이 바뀌거나(뒤로 가기 포함) Esc 면 닫는다 — 덮인 채 남지 않게 */
  const close = () => { el.remove(); removeEventListener('hashchange', close); removeEventListener('keydown', onKey); };
  const onKey = e => { if (e.key === 'Escape') close(); };
  addEventListener('hashchange', close); addEventListener('keydown', onKey);
}
Object.assign(window, { HXQ, hxAdd, hxEdit, hxDel, hxSave, hxShow });
/* 11-03 검수 D — 내보내기·가져오기·모두 지우기에 「내 병력」(hx)·알림 설정(fam)도 함께. 첫 화면 예산 때문에 app-shell 함수를 여기서 감싼다 */
try {
  const ex0 = exportMe, wipe0 = wipeMe, im0 = importMe;
  const getJ = k => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
  exportMe = async function () {
    const payload = { app: 'yakjido', v: 2, at: new Date().toISOString(), me: ME, hx: getJ(HX_KEY), fam: getJ(FAM_KEY) };
    if (await saveFile(`약지도-내기록-${todayKey()}.json`, JSON.stringify(payload, null, 1), 'application/json'))
      toast('파일로 받았어요 — 새 휴대폰에서 「가져오기」로 넣으시면 돼요');
  };
  wipeMe = async function () { await wipe0(); try { if (!localStorage.getItem(ME_KEY)) { localStorage.removeItem(HX_KEY); localStorage.removeItem(FAM_KEY); ['yakjido.ask', 'mn.addr', 'mn.chat.on.yakjido'].forEach(k => localStorage.removeItem(k)); } } catch (e) {} };   /* 11-04 묻고 싶은 것·응급 카드 주소도 */
  importMe = async function (file) {
    let j = null; try { j = file && file.size <= 3e6 ? JSON.parse(await file.text()) : null; } catch (e) {}
    const before = JSON.stringify(ME); await im0(file);
    if (JSON.stringify(ME) !== before && j && j.app === 'yakjido') {
      if (j.hx && Array.isArray(j.hx.list)) hxWrite(j.hx.list.filter(x => x && typeof x.t === 'string').map(x => ({ t: String(x.t).slice(0, 60), y: String(x.y || '').slice(0, 4), m: String(x.m || '').slice(0, 2), where: String(x.where || '').slice(0, 40), note: String(x.note || '').slice(0, 80), src: String(x.src || '').slice(0, 80) })));
      if (j.fam && typeof j.fam === 'object') famSave({ wait: [1, 2, 3].includes(j.fam.wait) ? j.fam.wait : 2, qs: /^\d\d:\d\d$/.test(j.fam.qs) ? j.fam.qs : '22:00', qe: /^\d\d:\d\d$/.test(j.fam.qe) ? j.fam.qe : '07:00', dose: false });   /* 정시 알림은 새 기기에서 다시 켜야(구독은 기기마다) */
      route();
    }
  };
} catch (e) {}
try { const st3 = document.createElement('style'); st3.textContent = '@media (max-width:440px){.hx .actions.two{flex-direction:column}.hx .actions.two .btn{width:100%;flex:none}}.hx-sug{margin-top:12px;padding-top:10px;border-top:1px dashed var(--hairline)}.hx-s{margin:8px 0}.hx-s b{display:block;margin-bottom:4px}.hx-s .chips{display:flex;flex-wrap:wrap;gap:6px}.hx-s .chip{min-height:44px;white-space:normal;text-align:left;display:inline-flex;align-items:center;gap:4px}.hx-sel{min-height:44px;padding:6px 10px;border:1.5px solid var(--ui-line);border-radius:12px;font:inherit;background:var(--card);color:var(--text)}'
  + '.hx-show{position:fixed;inset:0;z-index:9999;background:var(--bg,#fff);overflow:auto;-webkit-overflow-scrolling:touch}.hx-in{max-width:720px;margin:0 auto;padding:16px 16px 48px;font-size:1.1875rem;line-height:1.6}.hx-in h1{font-size:1.625rem;margin:12px 0 4px}.hx-in h2{font-size:1.25rem;margin:20px 0 6px;padding-top:12px;border-top:2px solid var(--hairline)}.hx-in ul{margin:0;padding-left:1.1em}.hx-in li{margin:6px 0}.hx-in li span{color:var(--body)}.hx-x{width:auto;margin:0;float:right}@media print{.hx-x{display:none}}';
  document.head.appendChild(st3); } catch (e) {}

try { const st2 = document.createElement('style'); st2.textContent = '.fam-h{display:flex;align-items:center;justify-content:flex-start;gap:8px;margin:0 0 6px;font-size:1.125rem}.fam-h .i{width:22px;height:22px}.fam-s{margin:14px 0 4px;font-size:1rem;color:var(--muted)}.fam-ul{list-style:none;margin:0;padding:0}.fam-ul li{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:10px 0;border-top:1px solid var(--hairline)}.fam-ul li>span:first-child{min-width:0}.fam-ul b{display:block;overflow-wrap:anywhere}.fam-ul small{display:block;color:var(--muted);font-size:.875rem}.fam-b{display:flex;align-items:center;gap:6px}.fam-b .btn{width:auto;min-height:44px;padding:0 14px;margin:0}.fam-b .link{min-height:44px;padding:0 8px}.fam-hot{background:var(--caution-tint);border-radius:12px;padding:10px!important}.fam-form{display:flex;flex-direction:column;gap:8px;margin-top:12px;padding-top:12px;border-top:1px dashed var(--hairline)}.fam-l{font-weight:700}.fam-form input:not([type=checkbox]){min-height:48px;padding:10px 12px;border:1.5px solid var(--ui-line);border-radius:12px;font:inherit;background:var(--card);color:var(--text)}.fam-rule{margin:6px 0 4px;padding-left:1.1em;color:var(--body);font-size:.9375rem;line-height:1.6}.fam-det{margin:4px 0;border:1px solid var(--hairline);border-radius:12px;padding:8px 12px}.fam-det summary{font-weight:700;cursor:pointer;min-height:40px;display:flex;align-items:center}.fam-det dl{margin:6px 0 0}.fam-det dt{font-weight:700;margin-top:8px}.fam-det dd{margin:2px 0 0;color:var(--body);font-size:.9375rem;line-height:1.6}.fam-off{display:block;min-height:44px;margin-top:6px}.fam-seg{display:flex;gap:6px}.fam-seg button{flex:1;min-height:44px;border:1.5px solid var(--ui-line);border-radius:12px;background:var(--card);color:var(--text);font:inherit;font-weight:700}.fam-seg button.on{background:var(--primary);color:var(--on-primary);border-color:var(--primary)}.fam-q{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.fam-q input{min-height:44px;padding:6px 10px;border:1.5px solid var(--ui-line);border-radius:12px;font:inherit;background:var(--card);color:var(--text)}.fam-q .btn{width:auto;margin:0;min-height:44px}.fam-ios{margin-top:10px}.fam-msg{padding:10px 12px;border-radius:12px;background:var(--accent-tint);color:var(--accent-text)}.nt-perm{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:10px 0 4px;padding:12px 14px;border-radius:14px;background:var(--accent-tint);color:var(--accent-text);font-size:1rem}.nt-perm.ok{background:var(--normal-tint);color:var(--normal)}.nt-perm .btn{width:auto;margin:0 0 0 auto;min-height:44px}.nt-list{padding:4px 16px}.nt-row{display:flex;align-items:center;gap:12px;padding:14px 0;border-top:1px solid var(--hairline)}.nt-row:first-child{border-top:0}.nt-ic{flex:none;width:40px;height:40px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:var(--tint);color:var(--primary-deep)}.nt-t{flex:1;min-width:0;display:flex;flex-direction:column}.nt-t b{font-size:1.0625rem}.nt-t small{color:var(--muted);font-size:.9375rem;margin-top:2px}.nt-row .sw{flex:none}'; document.head.appendChild(st2); } catch (e) {}
window.계정카드 = () => { if (D.meta?.account !== true) return ''; const 나 = srvLoggedIn(), m = 나 ? (서버.세션()?.user?.email || '') : '';
  if (!나) return `<section class="sec card acct-card"><div class="acct-hd"><span class="acct-ic" aria-hidden="true">${I.user}</span><span><b>메디나눔 계정</b><small>폰을 바꿔도 약통·복용 기록을 이어 봐요 · 선택</small></span></div>
    <button type="button" class="btn primary acct-go" onclick="go('/login')">로그인 · 계정 만들기</button></section>`;
  return `<section class="sec card acct-card"><div class="acct-hd"><span class="acct-av" aria-hidden="true">${esc(m.charAt(0).toUpperCase())}</span><span><b>${esc(m)}</b><small>로그인돼 있어요 · 이어 보기 켜짐</small></span></div>
    ${window.이용권줄HTML ? 이용권줄HTML() : ''}
    <div class="acct-act"><button type="button" class="btn line" onclick="계정동작('sync')">지금 맞추기</button><button type="button" class="btn line" onclick="계정동작('logout');setTimeout(route,600)">로그아웃</button></div>
    <button type="button" class="srvlink acct-del" onclick="go('/me?t=set');setTimeout(()=>document.getElementById('acct')?.scrollIntoView({block:'start'}),300)">계정 지우기·동의 거두기는 아래 「계정」 칸에서</button></section>`; };
window.계정줄 = () => D.meta?.account !== true ? '' : `<div class="rows-l acct-row">${srvLoggedIn() ? lrow(I.user, '메디나눔 계정', esc((서버.세션()?.user?.email || '') + ' · 이어 보기 켜짐'), "go('/login')") : lrow(I.user, '계정 만들기 · 로그인 <em class="door-tag">선택</em>', '폰을 바꿔도 이어 봐요', "go('/login')")}</div>`;
window.처음계정 = () => D.meta?.account !== true || srvLoggedIn() ? '' : `<div class="hello-acct"><b>계정 만들기 · 로그인 <em class="door-tag">선택</em></b><span>폰을 바꿔도 이어 봐요</span>
  <div class="actions two"><button class="btn line" onclick="helloFinish();go('/login')">${I.user} 로그인 · 계정 만들기</button><button class="btn line" onclick="helloFinish()">둘러보기</button></div></div>`;
/* 넓은 화면 왼쪽 메뉴의 앱 표시(아티팩트는 BRANDMARK 가 다르다) · 계정이 꺼져 있으면 메뉴의 계정 칸을 뺀다 */
try { const nv = document.querySelector('nav.tabbar');
  if (nv && !nv.querySelector('.nav-mark')) nv.insertAdjacentHTML('afterbegin', `<a class="nav-mark pc" href="#/home"><img src="${esc(BRANDMARK)}" alt="" width="36" height="36"><span><b>약지도</b><small>집에서 할 일 · 약국 약 · 진료 신호를 차례로</small></span></a>`);
  if (nv && D.meta?.account === true && !nv.querySelector('.nav-acct')) nv.insertAdjacentHTML('beforeend', `<button data-tab="login" class="pc nav-acct" aria-label="계정 · 로그인" onclick="go('/login')"><svg class="i" viewBox="0 0 24 24"><path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4M10 16l4-4-4-4M14 12H4"/></svg>계정 · 로그인</button>`);
  if (/^#\/login/.test(location.hash)) nv.querySelector('.nav-acct')?.classList.add('on'); } catch (e) {}

/* 로그인 문 — 따로 한 장(현욱님 「회원가입/로그인 화면」). 로그인은 언제나 고르는 것(애플 심사 5.1.1(v) · 메디나눔 약관 7조): 「로그인 없이 계속 쓰기」가 늘 있다 */
window.문나가기 = () => { const p = HIST.length >= 2 ? HIST[HIST.length - 2] : ''; if (p && !/^(login|consent|hello|doc)/.test(p)) goBack(); else go('/home'); };
window.문_login = (_, q) => {
  if (ROUTE_PREV !== 'login' && window.계정문처음) 계정문처음(q && q.t);
  const 켜짐 = D.meta?.account === true, 나 = srvLoggedIn();
  return `<div class="door lg">
  <button type="button" class="back door-back" onclick="문나가기()">${I.prev}뒤로</button>
  <img class="door-mark" src="${esc(BRANDMARK)}" alt="" width="64" height="64">
  <h1>${나 ? '메디나눔 계정' : '로그인하면 폰을 바꿔도<br>그대로 이어 봐요'}</h1>
  ${나 ? '' : `<ul class="lg-list">
    <li>${I.check}<span>새 휴대폰에서 같은 이메일로 로그인하면 약통·복용 기록이 그대로 와요</span></li>
    <li>${I.check}<span>메디나눔 앱들과 계정 하나 — 기록은 앱마다 따로예요</span></li>
    <li>${I.check}<span>로그인하지 않아도 약지도의 대부분의 기능을 쓰실 수 있어요</span></li></ul>`}
  ${켜짐 && window.계정문HTML ? 계정문HTML() : '<p class="door-note" style="margin-top:20px">계정은 준비 중이에요. 지금은 이 휴대폰에서 그대로 쓰실 수 있어요.</p>'}
  <button type="button" class="door-skip" onclick="문나가기()">${나 ? '돌아가기' : '로그인 없이 계속 쓰기'}</button>
  <p class="cs-foot"><button type="button" class="cs-doc" onclick="go('/doc/terms')">이용약관</button> · <button type="button" class="cs-doc" onclick="go('/doc/privacy')">개인정보 처리방침</button></p>
</div>`;
};

/* 약관·방침 전문 — 앱 안에서 읽는다(설치 앱에서 바깥 주소로 나가면 앱 화면이 끊긴다). 같은 주소의 html 을 받아 본문(main)만 보여 준다 */
const 문서 = {};
function 문서풀기(t){
  const d = new DOMParser().parseFromString(t, 'text/html'), m = d.querySelector('main') || d.body;
  m.querySelectorAll('script,style,link,.mark').forEach(e => e.remove());
  m.querySelectorAll('*').forEach(e => { for (const a of [...e.attributes]) if (/^on/i.test(a.name)) e.removeAttribute(a.name); if (e.id) e.id = 'doc-' + e.id; });
  m.querySelectorAll('a[href]').forEach(a => { const h = a.getAttribute('href') || ''; a.classList.add('link');   /* 문장 속 링크(누름 크기 예외 — WCAG 2.5.8) */
    if (h.startsWith('#')) { a.setAttribute('href', '#'); a.setAttribute('onclick', `document.getElementById(${JSON.stringify('doc-' + h.slice(1))})?.scrollIntoView();return false`); }
    else if (/^privacy(-yakjido)?\.html/.test(h)) a.setAttribute('href', '#/doc/privacy');
    else if (/^terms(-yakjido)?\.html/.test(h)) a.setAttribute('href', '#/doc/terms');
    else if (!h.startsWith('mailto:')) { if (NATIVE && !/^https?:/.test(h)) a.setAttribute('href', (D.meta?.webUrl || '') + h); a.setAttribute('target', '_blank'); a.setAttribute('rel', 'noopener'); } });
  return m.innerHTML;
}
window.문_doc = k => {
  k = k === 'privacy' ? 'privacy' : 'terms';
  const 이름 = k === 'terms' ? '이용약관' : '개인정보 처리방침', 웹 = (D.meta?.webUrl || 'https://yakjido.medinanum.com/') + k + '.html', v = 문서[k];
  if (v === undefined) { 문서[k] = null; fetch(k + '.html', { cache: 'no-cache' }).then(r => r.ok ? r.text() : Promise.reject(r.status)).then(t => { 문서[k] = 문서풀기(t); }).catch(() => { 문서[k] = false; }).then(() => { if (location.hash.startsWith('#/doc/' + k)) route(); }); }
  const 몸 = v ? v : v === false ? `<h1>${이름}</h1><div class="empty card" style="margin-top:16px"><b>전문을 불러오지 못했어요</b>인터넷 연결을 확인하고 다시 열어 주세요.</div>` : `<h1>${이름}</h1><p class="loading">불러오는 중이에요…</p>`;
  if (v === false) 문서[k] = undefined;   /* 다음에 열 때 다시 받아 본다 */
  return `<div class="top"><button class="back" onclick="goBack()">${I.prev}뒤로</button></div><article class="docv">${몸}</article>
  <p class="small muted docv-web">웹에서도 보실 수 있어요 — <a class="link" href="${esc(웹)}" target="_blank" rel="noopener">${esc(웹.replace(/^https:\/\//, ''))}</a></p>`;
};

try { const css = document.createElement('style'); css.textContent = `
.door{max-width:560px;margin:0 auto;padding:4px 0 32px}
.door-mark{display:block;width:64px;height:64px;border-radius:18px;margin:12px auto 14px;box-shadow:0 6px 18px rgba(var(--primary-rgb),.18)}
.door h1{text-align:center;font-size:1.625rem;line-height:1.35}
.door-s{text-align:center;color:var(--muted);margin-top:6px;font-size:1rem}
.cs-new{display:flex;gap:10px;align-items:flex-start;margin-top:18px;padding:12px 14px;border-radius:12px;background:var(--accent-tint);color:var(--accent-text);font-size:.9375rem;font-weight:600;line-height:1.55}
.cs-new svg.i{margin-top:2px}
.cs-list{list-style:none;margin:20px 0 0;padding:2px 16px;background:var(--card);border:1px solid var(--hairline);border-radius:var(--r-card);box-shadow:var(--shadow-card)}
.cs-list li{display:flex;gap:12px;align-items:flex-start;padding:13px 0;line-height:1.6;color:var(--body);font-size:1rem}
.cs-list li+li{border-top:1px solid var(--hairline)}
.cs-list svg.i{margin-top:2px;color:var(--primary)}
.cs-h{font-size:1.0625rem;font-weight:800;margin:28px 2px 10px}
.cs-row{display:flex;gap:12px;align-items:flex-start;width:100%;text-align:left;padding:14px 16px;min-height:56px;border-radius:14px;color:var(--text)}
.cs-all{background:var(--tint)}
.cs-all .cs-tx b{font-size:1.0625rem}
.cs-item{margin-top:10px;border:1.5px solid var(--hairline);border-radius:14px;background:var(--card)}
.cs-bx{flex:none;width:24px;height:24px;margin-top:1px;border-radius:7px;border:2px solid var(--ui-line);background:var(--card);display:grid;place-items:center;color:transparent}
.cs-bx svg.i{width:16px;height:16px;stroke-width:3}
[aria-checked=true]>.cs-bx{background:var(--primary);border-color:var(--primary);color:var(--on-primary)}
[aria-checked=mixed]>.cs-bx{border-color:var(--primary);background:linear-gradient(var(--primary),var(--primary)) center/10px 2.5px no-repeat var(--card)}
.cs-tx{flex:1;min-width:0}.cs-tx b{display:block;font-size:1rem;line-height:1.45}
.cs-tx>span{display:block;margin-top:4px;font-size:.875rem;line-height:1.6;color:var(--body)}
.cs-tag,.door-tag{display:inline-block;margin-right:6px;padding:1px 7px;border-radius:6px;background:var(--tint);color:var(--primary-deep);font-size:.875rem;font-weight:800;font-style:normal;vertical-align:2px}
.door-tag{margin:0 0 0 4px}
.cs-more{padding:0 16px 6px 52px}
.cs-more>summary,.door-more>summary{display:inline-flex;align-items:center;gap:4px;min-height:48px;font-size:.875rem;font-weight:700;color:var(--primary-deep);cursor:pointer;list-style:none}
.cs-more>summary::-webkit-details-marker,.door-more>summary::-webkit-details-marker{display:none}
.cs-more>summary svg.chev,.door-more>summary svg.chev{width:16px;height:16px;transition:transform .2s}
.cs-more[open]>summary svg.chev,.door-more[open]>summary svg.chev{transform:rotate(90deg)}
.cs-more ul{margin:0 0 4px;padding-left:1.1em;font-size:.875rem;line-height:1.65;color:var(--body)}
.cs-more li{margin:5px 0;color:var(--body)}
.cs-doc{display:inline-flex;align-items:center;gap:2px;min-height:48px;font-size:.875rem;font-weight:700;color:var(--primary-deep)}
.cs-doc svg.i{width:16px;height:16px}
.door-go{display:flex;align-items:center;justify-content:center;width:100%;min-height:56px;margin-top:22px;border-radius:14px;background:var(--primary);color:var(--on-primary);font-size:1.0625rem;font-weight:800;box-shadow:var(--shadow-raised)}
.door-go:disabled{background:var(--tint2);color:var(--muted);box-shadow:none;border:1.5px dashed var(--ui-line);cursor:not-allowed}
.door-why{margin-top:8px;text-align:center;font-size:.875rem;color:var(--muted)}
.door-why[hidden],.door-msg[hidden]{display:none}
.cs-again .cs-list li>span{display:flex;flex-direction:column}.cs-again .cs-list b{font-size:1.0625rem}.cs-again .cs-list small{color:var(--muted);font-size:.9375rem;margin-top:2px}.cs-again h1{margin-top:6px}
.cs-sum{margin-top:18px;text-align:center;font-size:1rem;line-height:1.6;color:var(--body)}.cs-detail{margin-top:10px;padding:0}.cs-detail>summary{min-height:48px;justify-content:center;width:100%;font-size:1rem}.cs-detail h3{font-size:1.0625rem;margin:16px 0 4px}.cs-detail p,.cs-detail li{font-size:1rem;line-height:1.65}.cs-detail ul{padding-left:1.1em;margin:6px 0}.cs-note{margin-top:14px;color:var(--muted)}
.cs-foot{margin-top:18px;text-align:center;font-size:.875rem;color:var(--muted);line-height:1.6}
.cs-foot .cs-doc{font-size:.875rem}
.lg h1{font-size:1.5rem}
.door-back{display:flex}
.lg-list{list-style:none;margin:16px auto 0;padding:0;max-width:420px}
.lg-list li{display:flex;gap:10px;align-items:flex-start;padding:5px 0;font-size:.9375rem;line-height:1.55;color:var(--body)}
.lg-list svg.i{width:18px;height:18px;margin-top:3px;color:var(--normal);stroke-width:2.4}
.srvbox.door-box{margin-top:20px;padding:18px 16px 14px;background:var(--card);border:1px solid var(--hairline);border-radius:var(--r-card);box-shadow:var(--shadow-card);gap:8px}
.door-seg{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:4px;border-radius:12px;background:var(--tint2);margin-bottom:6px}
.door-seg button{min-height:46px;border-radius:9px;font-weight:700;color:var(--muted)}
.door-seg button.on{background:var(--card);color:var(--text);box-shadow:0 1px 4px rgba(0,0,0,.14)}
.door-f{display:block;margin-top:6px;font-size:.875rem;font-weight:700;color:var(--text)}
.door-f small{font-weight:500;color:var(--muted);margin-left:4px}
.door-pw{position:relative}
.srvbox .door-pw input{padding-right:84px}
.door-eye{position:absolute;right:3px;top:50%;transform:translateY(-50%);min-height:44px;min-width:64px;padding:0 10px;border-radius:9px;font-size:.875rem;font-weight:700;color:var(--primary-deep)}
.door-ck{display:flex;gap:12px;align-items:flex-start;padding:12px 2px 2px;cursor:pointer}
.srvbox .door-ck input{-webkit-appearance:none;appearance:none;flex:none;width:24px;height:24px;min-height:0;margin:1px 0 0;padding:0;border:2px solid var(--ui-line);border-radius:7px;background:var(--card);cursor:pointer}
.srvbox .door-ck input:checked{border-color:var(--primary);background:var(--primary) url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'><path d='M5 12.5l4.5 4.5L19 7.5'/></svg>") center/16px no-repeat}
.door-ck b{display:block;font-size:.9375rem;line-height:1.45}
.door-ck small{display:block;margin-top:3px;font-size:.875rem;line-height:1.55;color:var(--muted)}
.door-more{padding-left:36px}
.door-more dl{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;margin:0 0 8px;font-size:.875rem;line-height:1.55}
.door-more dt{color:var(--muted);font-weight:700}.door-more dd{margin:0;color:var(--body)}
.door-more p{font-size:.875rem;line-height:1.55;color:var(--muted)}
.door-msg{margin-top:4px;padding:10px 12px;border-radius:10px;background:var(--tint2);color:var(--text);font-size:.875rem;line-height:1.55}
.srvbox .door-go{margin-top:6px}
.door-forgot{align-self:center;text-align:center}
.door-note{font-size:.875rem;color:var(--muted);line-height:1.6;text-align:center}
.door-h2{font-size:1.0625rem}
.door-me{display:flex;gap:12px;align-items:center}
.door-av{flex:none;width:44px;height:44px;border-radius:50%;background:var(--tint);color:var(--primary-deep);display:grid;place-items:center;font-weight:800;font-size:1.125rem}
.door-me b{display:block;overflow-wrap:anywhere}.door-me small{display:block;color:var(--muted);font-size:.875rem}
.door-social{display:flex;flex-direction:column;gap:8px}.door-soc{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:48px;border-radius:12px;font:600 1rem/1.2 inherit;font-family:inherit;cursor:pointer;touch-action:manipulation}
.door-need{outline:2px solid var(--danger,#c0392b);outline-offset:4px;border-radius:10px}.door-need-msg{margin:-2px 0 6px;color:var(--danger,#c0392b);font-weight:700;font-size:.9375rem}.door-google{background:#fff;color:#1f1f1f;border:1px solid #747775}.door-kakao{background:#FEE500;color:rgba(0,0,0,.85);border:0}.door-soc:disabled{opacity:.45;cursor:not-allowed}.door-google svg{flex:none}
.door-or{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:.875rem}.door-or::before,.door-or::after{content:"";flex:1;border-top:1px solid var(--hairline)}
@media (min-width:1024px){.nav-mark{align-items:center;gap:10px;padding:4px 8px 20px;text-decoration:none;color:var(--text)}.nav-mark img{border-radius:10px;flex:none}
.nav-mark b{display:block;font-size:1.125rem;font-weight:800}.nav-mark small{display:block;font-size:.875rem;line-height:1.35;color:var(--muted)}
.hello-hi p,.hello-close{margin-left:auto;margin-right:auto}}
@media (hover:hover){nav.tabbar button:hover{background:var(--tint2);color:var(--text)}nav.tabbar button.on:hover{background:var(--tint)}.srow:hover,.util-row:hover,.hello-big:hover,.card .row:hover{background:var(--tint2)}}
.srvdoor{min-height:48px;margin-bottom:6px;border-radius:12px;border:1.5px solid var(--ui-line);background:var(--card);color:var(--text);font-weight:700}
.acct-row{margin-top:12px}.hello-acct{margin-top:var(--s5);padding:16px;border-radius:14px;border:1px solid var(--hairline);background:var(--card)}.hello-acct>b{display:block}.hello-acct>span{display:block;font-size:.875rem;color:var(--muted)}.hello-acct .actions{margin-top:12px}
.door-skip{display:block;width:100%;min-height:52px;margin-top:14px;border-radius:12px;border:1.5px solid var(--hairline);background:var(--card);color:var(--body);font-weight:700}
.docv{max-width:42em}
.docv h1{font-size:1.5rem;margin:4px 0 6px}
.docv .meta{font-size:.875rem;color:var(--muted);margin-bottom:16px;line-height:1.6}
.docv .lead{background:var(--tint);border-radius:14px;padding:14px 16px;margin:0 0 12px}
.docv .lead p{margin:0 0 6px;color:var(--text)}
.docv section{border-top:1px solid var(--hairline);padding:14px 0}
.docv>p{margin-bottom:12px}
.docv h2{font-size:1.125rem;margin:0 0 6px}
.docv h3{font-size:1rem;margin:14px 0 4px}
.docv p,.docv li{font-size:.9375rem;line-height:1.75;color:var(--body)}
.docv li{margin:0 0 6px}
.docv ul,.docv ol{padding-left:1.25em;margin:0 0 8px}
.docv .wrap{overflow-x:auto}
.docv table{width:100%;border-collapse:collapse;font-size:.875rem;margin-top:6px}
.docv th,.docv td{text-align:left;vertical-align:top;padding:8px 6px;border-bottom:1px solid var(--hairline);overflow-wrap:anywhere;color:var(--body)}
.docv th{color:var(--muted);font-weight:700}
.docv a{color:var(--primary-deep);font-weight:600;display:inline;padding:0;text-decoration:underline;text-underline-offset:3px;overflow-wrap:anywhere}
.docv b{color:var(--text)}
.docv footer{border-top:1px solid var(--hairline);padding-top:14px}
.docv footer p{font-size:.875rem;margin:0 0 4px;color:var(--muted)}
.docv-web{margin-top:16px}.docv-web a{display:inline;overflow-wrap:anywhere}
@media (hover:hover){.cs-row:hover{background:var(--tint2)}.cs-all:hover{background:var(--tint)}.door-skip:hover,.door-seg button:not(.on):hover{color:var(--text)}.door-go:not(:disabled):hover{filter:brightness(1.06)}}
@media (min-width:600px){
  body.is-door .app{max-width:none;background:var(--ground)}
  body.is-door main{padding-top:40px}
  .door{padding:28px 40px 32px;border-radius:24px;background:var(--surface);border:1px solid var(--hairline);box-shadow:0 12px 40px rgba(0,0,0,.08)}
}`; document.head.appendChild(css); } catch (e) {}

/* ───────── 영양제 두 입구(10-20, 다음방향 리서치 4장) ─────────
   「무엇이 불편해서요?」(목적별 suppGoals) · 「누구세요?」(시기별 suppStages). 둘 다 성분 단위이고 성분 설명은 supplements·성분 사전을 가리키기만 한다.
   결론 한 줄 → 먼저 진료 신호(두 보기 모두 펼침) → 챙겨 볼 것(언제만 · 근거 세기) → 값을 못 해요. 식약처 문구·연구 한 줄·출처는 「왜 그런가요 ›」 안. */
const 영양이름 = x => String(x.supp).startsWith('nut:') ? (x.label || x.supp.slice(4)) : (supp(x.supp)?.name || x.supp);
const 영양길 = x => String(x.supp).startsWith('nut:') ? `go('/nut/${x.supp.slice(4)}')` : `go('/supp/${x.supp}')`;
const 근거세기 = { '강함':'otc', '중간':'cvs', '약함':'warn', '차이없음':'warn' };
const 근거말 = g => g === '차이없음' ? '사람 연구에서 차이 없음' : '근거 ' + g;
const 영양칸 = (x, sub) => `<div class="sg-pick"><button type="button" class="sg-h" onclick="${영양길(x)}"><b>${esc(영양이름(x))}</b>${x.grade ? `<span class="badge ${근거세기[x.grade] || 'warn'}">${esc(근거말(x.grade))}</span>` : ''}${I.chev}</button>
  ${sub ? `<p class="sg-when">${fmt(sub)}</p>` : ''}${x.mfds || x.human || x.why || (x.src || []).length ? fold('왜 그런가요', `${x.why ? `<p>${fmt(x.why)}</p>` : ''}${x.mfds ? `<p><b>식약처 기능성</b> — ${fmt(x.mfds)}</p>` : ''}${x.human ? `<p style="margin-top:6px"><b>사람 연구</b> — ${fmt(x.human)}</p>` : ''}${srcChips(x.src, true)}`) : ''}</div>`;
const 값못함 = L => (L || []).length ? `<section class="sec"><div class="sech"><h2 class="sec-h">따로 드실 이유가 적은 것</h2></div><div class="card rows">${L.map(x => `<div class="sg-skip"><button type="button" class="sg-h" onclick="${영양길(x)}"><b>${esc(영양이름(x))}</b>${I.chev}</button><p>${fmt(x.why)}</p>${(x.src || []).length ? srcChips(x.src) : ''}</div>`).join('')}</div></section>` : '';
window.영양입구 = () => { const G = D.suppGoals || [], S = D.suppStages || []; if (!G.length) return '';
  return `<section class="sec"><div class="sech"><h2 class="sec-h">무엇이 불편해서요?</h2></div><div class="rg">${G.map(g => `<button class="rg-t ${g.tone || ''}" onclick="go('/sgoal/${g.id}')"><span class="ic">${icon(g.icon)}</span><b>${esc(g.name)}</b></button>`).join('')}</div></section>
  <section class="sec"><div class="sech"><h2 class="sec-h">누구세요?</h2><span class="secn">나이·시기별로 챙길 것</span></div><div class="rows-l">${S.map(x => lrow(icon(x.icon), esc(x.name), esc(x.line), `go('/sstage/${x.id}')`)).join('')}${lrow(I.family, '아이·10대예요', '아이 영양은 우리 집 소아과와 같은 기준으로 봐요', "go('/kids')")}</div></section>`; };
window.문_sgoal = id => { const g = byId(D.suppGoals, id); if (!g) return `${topBar({ back:'영양제' })}<p class="loading">찾는 항목이 없어요.</p>`;
  return `${topBar({ back:'영양제' })}<div class="${g.tone || ''}"><div class="eyebrow" style="color:var(--gfg,var(--primary))">무엇이 불편해서요?</div><h1>${esc(g.name)}</h1></div>
  <div class="note" role="note" style="margin-top:12px">${I.info}<span><b>${fmt(g.first.line)}</b></span></div>
  <section class="sec card"><h2>이럴 땐 영양제보다 진료가 먼저예요</h2>${list(g.first.flags, 'plain x')}${g.first.test ? `<p class="small" style="margin-top:8px"><b>먼저 할 검사</b> — ${esc(g.first.test)}</p>` : ''}${g.symptom ? `<div class="rows-l" style="margin-top:8px">${lrow(I.alert, '증상 화면에서 진료 신호 모두 보기', '', `go('/symptom/${g.symptom}')`)}</div>` : ''}</section>
  ${(g.picks || []).length ? `<section class="sec"><div class="sech"><h2 class="sec-h">챙겨 볼 만한 것</h2></div><div class="card rows">${g.picks.map(x => 영양칸(x, x.when)).join('')}</div></section>` : ''}
  ${값못함(g.skip)}
  ${disclaimer(D.meta?.suppDisclaimer)}`; };
window.문_sstage = id => { const g = byId(D.suppStages, id); if (!g) return `${topBar({ back:'영양제' })}<p class="loading">찾는 항목이 없어요.</p>`;
  return `${topBar({ back:'영양제' })}<div class="eyebrow">누구세요?</div><h1>${esc(g.name)}</h1>
  <div class="note" role="note" style="margin-top:12px">${I.info}<span><b>${fmt(g.line)}</b></span></div>
  ${(g.picks || []).length ? `<section class="sec"><div class="sech"><h2 class="sec-h">챙길 것</h2></div><div class="card rows">${g.picks.map(x => 영양칸(x, x.dose)).join('')}</div></section>` : ''}
  ${값못함(g.skip)}
  ${(g.check || []).length ? `<section class="sec card"><h2>먼저 확인할 것</h2>${list(g.check)}</section>` : ''}
  ${disclaimer(D.meta?.suppDisclaimer)}`; };
try { const css = document.createElement('style'); css.textContent = `.sg-pick,.sg-skip{padding:12px 0;border-bottom:1px solid var(--hairline)}.sg-pick:last-child,.sg-skip:last-child{border-bottom:0}
.sg-h{display:flex;align-items:center;gap:8px;width:100%;min-height:48px;text-align:left}.sg-h b{flex:1;min-width:0;font-size:1.0625rem;font-weight:800}.sg-h .badge{flex:none}
.sg-when{font-size:.9375rem;color:var(--body);line-height:1.6}.sg-skip p{font-size:.9375rem;color:var(--body);line-height:1.6}`; document.head.appendChild(css); } catch (e) {}

/* ───────── 처방약 길잡이 화면(app-shell 에서 옮김 · 첫 화면 예산) — 혈압·당뇨·콜레스테롤·피 묽게 하는 약·갑상선·잠과 마음 ───────── */
let RXG = null;
function rxLoad(){ if (!RXG && window.__RXG__) RXG = window.__RXG__; if (!RXG) { RXG = { wait:true }; loadJSON('rxguide.json').then(j => { RXG = j; redraw(); }).catch(() => { RXG = { err:true }; redraw(); }); } return RXG; }
const rxRows = L => `<div class="rows-l">${L.map(g => lrow(I.pill, esc(RX_NAME[g]) + ' 드시는 분께', RXG?.guides?.[g]?.short ? esc(RXG.guides[g].short) : '먹는 법 · 깜빡했을 때 · 조심할 약', `go('/rx/${g}')`)).join('')}</div>`;
window.vRxS = function(id){
  const R = rxLoad();
  if (window.구독 && !구독.열림('rx')) { setTimeout(() => 구독.막힘('rx'), 0); return `${topBar({ back:'이전' })}<h1>처방약 길잡이</h1>`; }
  if (R.wait) return `${topBar({ back:'이전', unreviewed:!RXG?.reviewed })}<h1>처방약 길잡이</h1><p class="muted" style="margin-top:8px">불러오는 중이에요…</p>`;
  if (R.err) return `${topBar({ back:'이전', unreviewed:!RXG?.reviewed })}<h1>처방약 길잡이</h1><div class="note" style="margin-top:12px">${I.alert}<span>자료를 불러오지 못했어요. 인터넷에 연결된 뒤 다시 열어 주세요.</span></div>`;
  const g = R.guides?.[id];
  if (!g) return `${topBar({ back:'이전', unreviewed:!RXG?.reviewed })}<div class="eyebrow">오래 드시는 약</div><h1>처방약 길잡이</h1>
    <p style="margin-top:6px">병원에서 받아 오래 드시는 약마다 <b>먹는 법 · 깜빡했을 때 · 약국에서 조심할 약 · 바로 병원 갈 신호</b>를 모았어요.</p>
    ${rxRows(R.order || RX_IDS)}${disclaimer()}`;
  const mine = new Set((ME.taking || []).filter(x => x.startsWith('cls:' + id + '.')).map(x => x.slice(4)));
  const all = [...new Set([...(g.src || []), ...[g.do, g.otc, g.kinds, g.er, g.myths].flat().filter(Boolean).flatMap(x => x.src || []), ...(g.miss?.src || []), ...(g.clinic?.src || [])])];
  const kind = k => `<li${mine.has(k.k) ? ' class="me"' : ''}><b>${esc(k.n)}</b>${mine.has(k.k) ? ' <span class="badge soft">내 약</span>' : ''}<br>${fmt(k.t)}</li>`;
  const clin = [g.clinic?.t, ...(g.kinds || []).filter(k => k.clinic).map(k => `**${k.n}** — ${k.clinic}`)].filter(Boolean);
  return `${topBar({ back:'이전', unreviewed:!(g.reviewed ?? RXG?.reviewed) })}
  <div class="eyebrow">처방약 길잡이</div><h1>${esc(g.title)}</h1>
  <p class="lead-p" style="margin-top:6px">${fmt(g.lead)}</p>
  <section class="sec card"><h2>이렇게 드세요</h2><ol class="steps">${g.do.map(x => `<li>${fmt(x.t)}${x.go ? ` <a class="link" href="#${esc(x.go[0])}">${esc(x.go[1])}</a>` : ''}</li>`).join('')}</ol></section>
  <div class="note alert" style="margin-top:12px">${I.alert}<span><b>이럴 땐 바로</b><br>${g.er.map(x => fmt(x.t)).join('<br>')}</span></div>
  ${fold('깜빡했을 때', `<p>${fmt(g.miss.t)}</p>`, { open:true })}
  ${(g.otc || []).length ? fold('약국 약·음식 — 같이 조심할 것', `<ul class="plain">${g.otc.map(x => `<li><b>${esc(x.n)}</b><br>${fmt(x.t)}${x.do ? `<br><span class="muted">${fmt(x.do)}</span>` : ''}</li>`).join('')}</ul>`) : ''}
  ${(g.kinds || []).length ? fold(id === 'chol' ? '알아 둘 것 — 근육통·간 수치·혈당' : '종류별로 알아 둘 것', `<ul class="plain">${g.kinds.map(kind).join('')}</ul>`, { open: mine.size > 0 }) : ''}
  ${clin.length ? fold('진료실 이야기 — 약을 바꾸는 이유', `<ul class="plain">${clin.map(t => `<li>${fmt(t)}</li>`).join('')}</ul>`) : ''}
  ${(g.myths || []).length ? fold('흔한 오해', `<ul class="plain">${g.myths.map(m => `<li><b>${esc(m.q)}</b><br>${fmt(m.a)}</li>`).join('')}</ul>`) : ''}
  ${(() => { const o = (R.order || RX_IDS).filter(x => x !== id); return o.length ? fold('다른 약 길잡이', rxRows(o)) : ''; })()}
  ${srcChips(all)}
  ${disclaimer('약을 줄이거나 바꾸는 것은 처방한 의사와 정하세요.')}`;
}

/* 받는 화면(app-shell 에서 옮김 — 첫 화면 예산 10-27) */
window.vParentShareS = function(code){
  const S = SHARE(); const st = PSHARE[code];
  if (!S.fn) return `${topBar({ back:'처음으로', nosearch:true })}<section class="sec"><div class="empty card"><b>이 링크를 열 수 없어요</b>앱의 보내기 서버가 아직 준비되지 않았어요.</div></section>`;
  if (!st) { PSHARE[code] = { loading: true };
    fetch(S.fn, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ action:'get', code }) })
      .then(r => r.json().then(j => ({ ok: r.ok, status: r.status, j }))).then(({ ok, status, j }) => { PSHARE[code] = ok ? { data: j } : { err: status }; route(); })
      .catch(() => { PSHARE[code] = { err: 0 }; route(); });
    return `${topBar({ back:'처음으로', nosearch:true })}<section class="sec"><p class="loading">받은 약을 불러오는 중이에요…</p></section>`; }
  if (st.loading) return `${topBar({ back:'처음으로', nosearch:true })}<section class="sec"><p class="loading">받은 약을 불러오는 중이에요…</p></section>`;
  if (st.err) return `${topBar({ back:'처음으로', nosearch:true })}<section class="sec"><div class="empty card"><b>${st.err === 410 ? '기간이 지난 링크예요' : '받은 약을 불러오지 못했어요'}</b>${st.err === 410 ? '보낸 지 7일이 지나 지워졌어요. 다시 보내 달라고 해 주세요.' : '인터넷 연결을 확인하고 다시 열어 주세요.'}</div></section>`;
  const x = st.data;
  const sy = (() => { const t = (x.items || []).find(it => /^sym:/.test(it.id || '')); return t ? byId(D.symptoms, t.id.slice(4)) : null; })();
  const meds = (x.items || []).filter(it => !/^sym:/.test(it.id || ''));
  /* 외부 검수 6차 #5 — 보내는 화면·복사 글과 같은 설명서 단서(근이완 복합제 + 다른 해열진통제)를 받는 화면에도 — 같은 판정(basket 의 mix 1) */
  const nsK = k => (ingIndex().byKey[k]?.cls || []).includes('nsaid'), dk = it => drug(it.id) ? drugKeys(drug(it.id)) : [];
  const mixIt = it => dk(it).includes('ethenzamide') && meds.some(o => o !== it && dk(o).some(k => k === 'acetaminophen' || nsK(k)));
  return `<div class="pshare">${topBar({ back:'처음으로', nosearch:true })}
  <div class="eyebrow">${x.label ? esc(x.label) + '께 온 부탁' : '받은 약'}</div>
  <h1 style="font-size:1.625rem">이 화면을 약사님께 보여 주세요</h1>
  ${x.note ? `<p class="ps-note">“${esc(x.note)}”</p>` : ''}
  <section class="sec"><div class="ps-list">${meds.map(it => { const d = drug(it.id); const nm = it.product || (d ? d.name : it.name);
    return `<div class="ps-item">${prodArt(pimg(it.product || ''), nm)}<div><b>${esc(nm)}</b><span>${esc(it.product ? (d ? ingrName(d) : it.name) : '')}</span>${mixIt(it) ? `<small class="cau">${I.alert}${esc(mixTxt({ mix: 1 }))}</small>` : ''}</div></div>`; }).join('')}</div>
    <p class="ps-ask">성분·함량·제형이 같으면 다른 제품도 괜찮아요.</p></section>
  ${sy && sy.care?.er?.length ? `<div class="flag" role="note" style="margin-top:12px">${I.alert}<div><b>이럴 땐 약 대신 바로 119</b><p>${esc(sy.name)} 때문에 보내 드린 약이에요. 아래 가운데 하나라도 있으면 약국에 가지 마시고 119에 전화하거나 응급실로 가세요.</p>${list(sy.care.er)}<a class="call" href="tel:119">${I.alert} 119 전화</a></div></div>${sy.care.clinic?.length ? fold('이럴 땐 오늘 병원으로', list(sy.care.clinic)) : ''}` : ''}
  <div class="note" style="margin-top:12px">${I.alert}<span><b>약사님께 앓고 계신 병과 드시는 약을 꼭 말씀하세요.</b> 혈압약·당뇨약·피 묽게 하는 약을 드시면 특히요.</span></div>
  <div class="actions"><a class="btn" href="${GO_LINK.open[0]}" target="_blank" rel="noopener">${I.pin || I.search} 가까운 문 연 약국 찾기</a>${x.bought_at ? `<span class="badge otc">샀어요 표시함</span>` : `<button class="btn line" onclick="psBought('${esc(code)}')">${I.check} 샀어요</button>`}</div>
  ${disclaimer()}</div>`;
};
/* 의사에게 물어보기(app-shell 에서 옮김 — 첫 화면 예산 10-26) */
window.vAskDocS = function(_, q){
  const A = D.askdoc || []; if (!A.length) return vHome();
  const item = x => `<details class="xc" id="ad-${x.id}" ${q.open === x.id ? 'open' : ''}><summary>
    <div class="ic">${icon(x.icon)}</div><b>${esc(x.q)}</b><span class="cnt">답 보기${I.chev}</span></summary>
    <div class="bd"><div class="chat"><div class="bubble me"><span class="who">물은 말</span>${esc(x.q)}</div>
      <div class="bubble"><span class="who">응급실 의사</span>${fmt(x.a)}</div></div>
      <div class="actions" style="margin-top:10px">${speakBtn(`(D.askdoc.find(y=>y.id==='${x.id}')||{}).a`, '답 읽어 주기')}${x.go ? `<a class="btn ghost" href="#${x.go}">${I.chev} ${esc(x.goText || '자세히')}</a>` : ''}</div>
    </div></details>`;
  return `${topBar({ back:'홈' })}<div class="eyebrow">진료실 답</div><h1>의사에게 물었어요</h1>
  <p style="margin-top:6px">약국·진료실에서 자주 듣는 질문에, <b>진료실에서 의사가 실제로 하는 대답</b>을 그대로 옮겼어요. 모두 ${A.length}가지.</p>
  <section class="sec"><div class="explore">${A.map(item).join('')}</div></section>
  <section class="sec"><div class="note">${I.info}<span>일반적인 설명이에요. <b>드시는 약이나 몸 상태에 따라 답이 달라질 수 있어</b> 약사·의사와 상의하세요.</span></div></section>`;
};
/* 오해 풀이(app-shell 에서 옮김 — 첫 화면 예산 10-26) */
window.vMythsS = function(_, q){
  const M = D.myths || [];
  if (!M.length) return vHome();
  const MG = ['약국에서 사는 것', '영양제', '약 고르기', '같이 먹어도 되나', '그 밖에'];
  const card = m => `<details class="xc myth" id="my-${m.id}" ${q.open === m.id ? 'open' : ''}><summary>
    <div class="ic">${icon(m.icon)}</div>
    <b class="heard">“${esc(m.heard)}”</b>
    <span class="verdict">${esc(m.verdict)}</span>
    <span class="cnt">근거 보기${I.chev}</span></summary>
    <div class="bd">
      <div class="myth-n">${I.scale}${esc(m.n)}</div>
      <p class="myth-lead">${fmt(m.body)}</p>
      <div class="actions" style="margin-top:6px">${speakBtn(`(D.myths.find(x=>x.id==='${m.id}')||{}).body`, m.heard + ' 근거 읽어 주기')}</div>
      ${srcChips(m.src, true)}
      ${m.go ? `<div class="actions"><a class="btn ghost" href="#${m.go}">${I.chev} ${esc(m.goText || '자세히 보기')}</a></div>` : ''}
    </div></details>`;
  const groups = MG.map(g => [g, M.filter(m => m.group === g)]).filter(([, xs]) => xs.length);
  const rest = M.filter(m => !MG.includes(m.group));
  return `${topBar({ back:'홈' })}<div class="eyebrow">근거로 다시 보기</div><h1>그런 줄 알았는데</h1>
  <p style="margin-top:6px">약에 대해 흔히 듣는 말 가운데, <b>자료를 찾아보면 달랐던 것</b>들이에요.
  「하지 마세요」가 아니라 <b>숫자가 어디까지 말하는지</b>를 그대로 적었어요. 모두 ${M.length}가지.</p>
  ${(() => { const today = M[new Date().getDate() % M.length]; return `<div class="rows-l" style="margin-top:14px">${lrow(icon(today.icon), `오늘의 한 가지 — “${esc(today.heard)}”`, esc(today.verdict), `go('/myths?open=${today.id}')`)}</div>`; })()}
  ${(() => {
    /* 2026-09-30 — 갈래를 모두 펼치면 폰 4장이었다(오늘의 한 가지 카드는 옛 모양이 깨져 있었다). ClinicScore 처럼 탭, 고른 갈래만 */
    const G = [...groups, ...(rest.length ? [['그 밖에', rest]] : [])];
    const oi = q.open ? G.findIndex(([, xs]) => xs.some(m => m.id === q.open)) : -1;
    const k = oi >= 0 ? oi : Math.max(0, Math.min(G.length - 1, +(q.g || 0) || 0)), [g, xs] = G[k];
    return `<nav class="tabs" role="tablist" aria-label="갈래" style="margin-top:20px">${G.map(([gn, L], i) => `<button class="tab ${i === k ? 'on' : ''}" role="tab" aria-selected="${i === k}" onclick="go('/myths?g=${i}')">${esc(gn)}<span class="n">${L.length}</span></button>`).join('')}</nav>
    <div class="sech"><h2 class="sec-h">${esc(g)}</h2><span class="secn">${xs.length}가지</span></div>
    <div class="explore">${xs.map(card).join('')}</div>`; })()}
  <section class="sec"><div class="note">${I.info}<span><b>이 화면은 「약을 먹지 마세요」가 아니에요.</b> 근거가 없다고 밝힌 것은 「효과가 없다고 증명됐다」와 다르고, 근거가 약한 것도 의사가 이유가 있어 내실 수 있어요. <b>드시던 약을 이 화면을 보고 스스로 끊지 마세요.</b></span></div></section>
  ${disclaimer()}`;
};
/* 근거와 검수 기준(app-shell 에서 옮김 — 첫 화면 예산) */
window.vAboutS = function(){
  const S = D.sources || {};
  return `${topBar({ back:'내 정보' })}<h1>근거와 검수 기준</h1>
  <section class="sec card"><h2>이렇게 만들었어요</h2>${list(D.meta?.method || [])}</section>
  ${(() => {
    /* 출처 242건을 한 줄로 늘어놓으면 화면이 25,000픽셀(폰 30장)이 된다 —
       종류별로 묶고 접어 둔다. 코크란·메타분석처럼 「근거가 센 것」을 맨 위로. */
    const ORDER = ['코크란 리뷰', '메타분석', '우산 리뷰', '체계적 고찰', '무작위 비교 시험', '진료 지침', '종설', '후향 연구', '관찰 연구', '허가사항', '기타'];
    const g = new Map();
    for (const [k, v] of Object.entries(S)) {
      let t = String(v.type || '기타').trim();
      if (/허가|식약처|e약은요/.test(t)) t = '허가사항';
      if (!ORDER.includes(t)) t = ORDER.includes(t) ? t : (/지침|가이드/.test(t) ? '진료 지침' : /코크란/.test(t) ? '코크란 리뷰' : t);
      if (!g.has(t)) g.set(t, []);
      g.get(t).push([k, v]);
    }
    const keys = [...g.keys()].sort((a, b) => {
      const ia = ORDER.indexOf(a), ib = ORDER.indexOf(b);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
    /* 4-01 — 출처 메모(원문 인용·확인 날짜)는 줄 안에 늘어놓지 않고 작은 접이로. PMID 는 줄에 그대로 */
    const row = ([k, v]) => { const note = String(v.note || '').trim(), extra = note.replace(/PMID\s*\d+/g, '').replace(/[\s·—\-.,]/g, '').length > 0;
      return `<a class="row" href="${esc(v.url)}" target="_blank" rel="noopener" style="text-decoration:none"><div class="body"><b>${fmt(v.label)}</b><span>${esc(v.type || '')}${(m => m ? ' · ' + esc(m[0]) : '')(note.match(/PMID\s*\d+/))}</span></div>${I.link}</a>${extra ? `<details class="src-note"><summary>원문 메모 보기</summary><p>${esc(note)}</p></details>` : ''}`; };
    return `<section class="sec"><h2>참고 문헌·지침 <small>${Object.keys(S).length}건</small></h2>
      <p class="small muted" style="margin-bottom:8px">근거가 센 것부터 묶어 두었어요. 갈래를 누르면 펼쳐져요.</p>
      ${keys.map(t => `<details class="acc"><summary>${esc(t)}<small>${g.get(t).length}건</small>${I.chev}</summary><div class="bd"><div class="rows">${g.get(t).map(row).join('')}</div></div></details>`).join('')}
    </section>`;
  })()}
  ${fold(`${I.book}오픈소스 고지`, ossList(), { cls:'oss-fold' })}
  ${disclaimer()}`;
}

;/* ▼▼ 통합찾기 부품 시작 ▼▼ */
/* ═══ 메디나눔 통합 찾기 — 다섯 앱 공용 (2026-10-26 Main · 요청서 docs/requests/20261023_메디나눔_전앱_통합찾기.md) ═══
   하는 일: 이 앱에서 친 말로 «다른 네 앱»의 글·계산기를 찾아, 앱별로 묶어 보여 준다. 누르면 그 앱의 그 화면이 열린다.
   목록: 앱마다 자기 웹 주소에 `medinanum-search.json` 을 둔다(그 앱 세션이 만든다 — 아래 «목록 꼴»).
         https://kids.medinanum.com/ · gildongmu · cs · gyeote · yakjido  →  /medinanum-search.json
         (배포 머리말 `_headers` 가 이 파일에 Access-Control-Allow-Origin: * 를 붙인다 — deploy_web.py)
   목록 꼴: { "앱":"kids", "판":"2026-10-26", "항목":[ { "id":"fever", "t":"아이 열 판단", "s":"한 줄 요약",
             "k":["열","해열제","발열"], "u":"#doc/fever", "e":1 (응급·위험 신호 — 누구에게나), "c":1 (의료인 전용) }, … ] }
             — 본문은 넣지 않는다(작게: 앱 하나 100 KB 안쪽). u 는 그 앱 주소 뒤에 붙는 길(# 로 시작).
   혜택(10-22·10-23 원칙): 회원권은 결제 권한, 자격은 따로.
     · 회원(또는 유료화 스위치가 꺼져 있을 때): 다른 앱 결과 전부 보기·열기.
     · 회원 아님: 다른 앱은 「N개 있어요」 개수만 + 응급(e) 항목은 늘 보이고 열린다.
     · 의료인 전용(c) 항목은 의료인확인() 이 참일 때만 센다·보인다(회원권과 무관).
   지키는 것: 검색어를 어디에도 보내지 않는다(목록만 받아 기기에서 찾는다) · 목록은 메모리 + localStorage(하루) ·
              실패하면 조용히 빈 칸(이 앱 검색은 그대로) · ES5 · 화면 글은 해요체.
   쓰는 법:
     통합찾기.설치({ 앱:'kids', 의료인확인: function(){ return false; }, 열기: function(url){ location.href = url; } });
     통합찾기.붙이기(document.getElementById('xsearch'), '열');   // 앱 찾기 결과 아래 빈 칸에 그린다
     통합찾기.찾기('열').then(function(묶음){ … })                 // [{앱, 이름, 주소, 보임:[항목], 숨김수, 응급:[항목]}]
*/
(function () {
  if (window.통합찾기) return;
  var 앱들 = [
    { 키: 'kids', 이름: '우리 집 소아과', 주소: 'https://kids.medinanum.com/' },
    { 키: 'gildongmu', 이름: '길동무', 주소: 'https://gildongmu.medinanum.com/' },
    { 키: 'yakjido', 이름: '약지도', 주소: 'https://yakjido.medinanum.com/' },
    { 키: 'gyeote', 이름: '곁에', 주소: 'https://gyeote.medinanum.com/' },
    { 키: 'cs', 이름: 'ClinicScore', 주소: 'https://cs.medinanum.com/' }
  ];
  var 설정 = { 앱: '', 의료인확인: null, 열기: null, 하루: 864e5 };
  var 목록들 = {};   /* 키 → {항목, 색인} */
  var 받는중 = null;

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function 고름(s) { return String(s || '').toLowerCase().replace(/[\s ·.,!?()\[\]{}'"~\-_/]/g, ''); }

  function 회원() {
    try {
      var 구 = window.구독;
      if (!구 || typeof 구.켜짐 !== 'function' || !구.켜짐()) return true;   /* 유료화 꺼짐 = 모두 열림 */
      var st = 구.상태(); return !!(st && st.열림 && st.회원권);
    } catch (e) { return false; }
  }
  function 의료인() { try { return typeof 설정.의료인확인 === 'function' && !!설정.의료인확인(); } catch (e) { return false; } }

  function 저장읽기(키) {
    try { var o = JSON.parse(localStorage.getItem('_mnx_' + 키) || 'null'); if (o && o.at && Date.now() - o.at < 설정.하루 && o.항목) return o.항목; } catch (e) {}
    return null;
  }
  function 저장쓰기(키, 항목) { try { localStorage.setItem('_mnx_' + 키, JSON.stringify({ at: Date.now(), 항목: 항목 })); } catch (e) {} }

  function 하나받기(a) {
    var 남은 = 저장읽기(a.키);
    if (남은) return Promise.resolve(남은);
    if (!window.fetch) return Promise.resolve([]);
    return fetch(a.주소 + 'medinanum-search.json', { credentials: 'omit', cache: 'no-cache' }).then(function (r) {
      if (!r.ok) return [];
      return r.json().then(function (j) { var 항 = (j && j.항목 && j.항목.length) ? j.항목 : []; 저장쓰기(a.키, 항); return 항; });
    }).catch(function () { return []; });
  }

  function 색인만들기(항목) {
    if (window.찾기 && typeof window.찾기.만들기 === 'function') {
      try {
        return window.찾기.만들기({ 항목: 항목.map(function (h) { return { id: h.id, 제목: h.t, 태그: h.k || [], 요약: h.s || '' }; }) });
      } catch (e) {}
    }
    return null;
  }

  function 모두받기() {
    if (받는중) return 받는중;
    var 남 = 앱들.filter(function (a) { return a.키 !== 설정.앱; });
    받는중 = Promise.all(남.map(function (a) {
      return 하나받기(a).then(function (항) { 목록들[a.키] = { 항목: 항, 색인: 색인만들기(항) }; });
    })).then(function () { 받는중 = null; return 목록들; }, function () { 받는중 = null; return 목록들; });
    return 받는중;
  }

  function 맞추기(목, 말) {
    if (!목 || !목.항목.length) return [];
    if (목.색인) {
      try {
        var r = 목.색인.찾기(말, { 최대: 40 }); var 표 = {};
        목.항목.forEach(function (h) { 표[h.id] = h; });
        return r.map(function (x) { return 표[x.id]; }).filter(Boolean);
      } catch (e) {}
    }
    var q = 고름(말); if (!q) return [];
    return 목.항목.filter(function (h) {
      return 고름(h.t).indexOf(q) >= 0 || (h.k || []).some(function (k) { return 고름(k).indexOf(q) >= 0; }) || 고름(h.s).indexOf(q) >= 0;
    });
  }

  function 찾기(말) {
    말 = String(말 || '').trim();
    if (!말) return Promise.resolve([]);
    return 모두받기().then(function () {
      var 회 = 회원(), 의 = 의료인();
      return 앱들.filter(function (a) { return a.키 !== 설정.앱; }).map(function (a) {
        var 맞음 = 맞추기(목록들[a.키], 말).filter(function (h) { return !h.c || 의; });
        var 응급 = 맞음.filter(function (h) { return h.e; });
        var 보임 = 회 ? 맞음 : 응급;
        return { 앱: a.키, 이름: a.이름, 주소: a.주소, 보임: 보임.slice(0, 6), 더: Math.max(0, 보임.length - 6), 숨김수: 회 ? 0 : 맞음.length - 응급.length, 전체: 맞음.length };
      }).filter(function (g) { return g.전체 > 0; });
    });
  }

  function HTML(묶음) {
    if (!묶음 || !묶음.length) return '';
    var 회 = 회원(), h = '<section class="mnx" aria-label="메디나눔 다른 앱에서"><h3 class="mnx-h">메디나눔 다른 앱에서</h3>';
    묶음.forEach(function (g) {
      h += '<div class="mnx-app"><div class="mnx-name">' + esc(g.이름) + ' <span>' + g.전체 + '개</span></div>';
      g.보임.forEach(function (it) {
        h += '<a class="mnx-row" href="' + esc(g.주소 + (it.u || '')) + '" data-mnx="1" rel="noopener">' +
             (it.e ? '<i class="mnx-e">급할 때</i>' : '') + '<b>' + esc(it.t) + '</b>' + (it.s ? '<small>' + esc(it.s) + '</small>' : '') + '</a>';
      });
      if (g.더) h += '<a class="mnx-more" href="' + esc(g.주소) + '" data-mnx="1" rel="noopener">' + esc(g.이름) + '에서 ' + g.더 + '개 더 보기 ›</a>';
      if (g.숨김수 > 0) h += '<div class="mnx-lock">' + g.숨김수 + '개가 더 있어요 · 메디나눔 회원권으로 다섯 앱을 한 번에 찾아요</div>';
      h += '</div>';
    });
    if (!회) h += '<p class="mnx-note">급할 때 볼 안내는 회원권 없이도 늘 열려요.</p>';
    return h + '</section>';
  }

  var CSS = '.mnx{margin:18px 0 8px}.mnx-h{font-size:calc(15px * var(--fs,1));margin:0 0 8px;font-weight:800}' +
    '.mnx-app{border:1px solid var(--line,rgba(0,0,0,.12));border-radius:14px;padding:10px 12px;margin:0 0 10px;background:var(--card,transparent)}' +
    '.mnx-name{font-weight:700;font-size:calc(14px * var(--fs,1));margin:0 0 6px}.mnx-name span{font-weight:500;opacity:.7}' +
    '.mnx-row{display:block;padding:9px 0;min-height:44px;border-top:1px solid var(--line,rgba(0,0,0,.08));color:inherit;text-decoration:none;word-break:keep-all}' +
    '.mnx-row b{display:block;font-size:calc(15px * var(--fs,1))}.mnx-row small{display:block;opacity:.75;font-size:calc(13px * var(--fs,1));margin-top:2px}' +
    '.mnx-e{font-style:normal;font-size:calc(11px * var(--fs,1));font-weight:700;padding:2px 7px;border-radius:99px;background:#FDE7E4;color:#8A1F11;margin-right:6px}' +
    '.mnx-more{display:block;padding:8px 0 2px;font-size:calc(13px * var(--fs,1));color:inherit;opacity:.85}' +
    '.mnx-lock,.mnx-note{font-size:calc(13px * var(--fs,1));opacity:.8;padding-top:6px;word-break:keep-all}' +
    'html[data-theme="dark"] .mnx-e{background:#4A1F1A;color:#FFD9D2}';

  function 붙이기(곳, 말) {
    if (!곳) return Promise.resolve();
    if (!document.getElementById('mnx-css')) { var s = document.createElement('style'); s.id = 'mnx-css'; s.textContent = CSS; document.head.appendChild(s); }
    var 이번 = (곳._mnx = (곳._mnx || 0) + 1);
    return 찾기(말).then(function (묶음) {
      if (곳._mnx !== 이번) return;   /* 그새 다른 말을 쳤으면 버린다 */
      곳.innerHTML = HTML(묶음);
      if (typeof 설정.열기 === 'function') {
        Array.prototype.forEach.call(곳.querySelectorAll('a[data-mnx]'), function (a) {
          a.addEventListener('click', function (ev) { ev.preventDefault(); try { 설정.열기(a.getAttribute('href')); } catch (e) { location.href = a.getAttribute('href'); } });
        });
      }
    });
  }

  window.통합찾기 = {
    판: '2026-10-26-1',
    설치: function (o) { o = o || {}; for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) 설정[k] = o[k]; },
    찾기: 찾기, HTML: HTML, 붙이기: 붙이기, 앱들: 앱들,
    비우기: function () { 목록들 = {}; 앱들.forEach(function (a) { try { localStorage.removeItem('_mnx_' + a.키); } catch (e) {} }); }
  };
})();
/* ▲▲ 통합찾기 부품 끝 ▲▲ */
try { 통합찾기.설치({ 앱: 'yakjido', 열기: function (url) { location.href = url; } }); } catch (e) {}
;/* ▼▼ 이용량 부품 시작 ▼▼ */
/* ═══ 메디나눔 익명 이용 통계 — 다섯 앱 공용 (2026-10-26 Main · 현욱님 「월 정액 시범 → 이용량 보고 결정」) ═══
   하는 일: 「검사 시작·끝냄·다시 하기·결과 칸 열기」 같은 기능 이름의 «횟수»만 기기에 모았다가 하루 한 번 서버 합계에 더한다.
   보내는 것: 앱 이름 + {기능이름: 횟수}. 계정·기기 식별값·답·결과·검색어는 보내지 않는다. 서버는 날짜별 합계만 둔다(RPC bump_usage).
   스위치: 켜짐 — 기본 false. 처리방침에 「익명 이용 통계」 줄이 시행된 뒤(출시 판)에만 켠다. 이용자가 설정에서 끄면 즉시 멈추고 모은 것도 버린다.
   쓰는 법:
     이용량.설치({ 앱:'gyeote', 켜짐:false, 주소:'https://<프로젝트>.supabase.co', 공개키:'<publishable 키>' });
     이용량.센다('test_start_hsp');      // 이름은 영문 소문자·숫자·밑줄 40자 안. 검사 키는 이름 끝에 붙여도 된다(답·결과는 안 됨)
     이용량.끄기(true|false) · 이용량.꺼짐()  // 설정 칸 「앱 개선을 위한 익명 이용 통계」
*/
(function () {
  if (window.이용량) return;
  var 설정 = { 앱: '', 켜짐: false, 주소: '', 공개키: '' };
  var 열쇠 = '_mn_usage', 끔열쇠 = '_mn_usage_off';
  function 읽기() { try { return JSON.parse(localStorage.getItem(열쇠) || 'null') || { d: '', e: {} }; } catch (e) { return { d: '', e: {} }; } }
  function 쓰기(o) { try { localStorage.setItem(열쇠, JSON.stringify(o)); } catch (e) {} }
  function 오늘() { var t = new Date(); return t.getFullYear() + '-' + (t.getMonth() + 1) + '-' + t.getDate(); }
  function 꺼짐() { try { return localStorage.getItem(끔열쇠) === '1'; } catch (e) { return false; } }
  function 돌아감() { return !!설정.켜짐 && !꺼짐() && !!설정.앱; }

  function 보내기(o) {
    if (!설정.주소 || !설정.공개키 || !window.fetch) return;
    var 묶음 = o.e, 있음 = false; for (var k in 묶음) { 있음 = true; break; }
    if (!있음) return;
    try {
      fetch(설정.주소.replace(/\/$/, '') + '/rest/v1/rpc/bump_usage', {
        method: 'POST', credentials: 'omit', keepalive: true,
        headers: { 'Content-Type': 'application/json', apikey: 설정.공개키, Authorization: 'Bearer ' + 설정.공개키 },
        body: JSON.stringify({ p_app: 설정.앱, p_events: 묶음 })
      }).catch(function () {});
    } catch (e) {}
  }
  function 넘기기() {   /* 날이 바뀌었으면 어제 모은 것을 보내고 비운다 */
    var o = 읽기(), d = 오늘();
    if (o.d && o.d !== d) { 보내기(o); o = { d: d, e: {} }; 쓰기(o); }
    if (!o.d) { o.d = d; 쓰기(o); }
    return o;
  }
  function 센다(이름) {
    if (!돌아감()) return;
    이름 = String(이름 || '').toLowerCase();
    if (!/^[a-z0-9_]{1,40}$/.test(이름)) return;
    var o = 넘기기(), 개수 = 0; for (var k in o.e) 개수++;
    if (!o.e[이름] && 개수 >= 30) return;
    o.e[이름] = Math.min(200, (o.e[이름] || 0) + 1); 쓰기(o);
  }
  window.이용량 = {
    판: '2026-10-26-1',
    설치: function (o) { o = o || {}; for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) 설정[k] = o[k]; if (돌아감()) 넘기기(); },
    센다: 센다, 꺼짐: 꺼짐, 돌아감: 돌아감,
    끄기: function (끔) { try { if (끔) { localStorage.setItem(끔열쇠, '1'); localStorage.removeItem(열쇠); } else localStorage.removeItem(끔열쇠); } catch (e) {} },
    지금보내기: function () { if (!돌아감()) return; var o = 읽기(); 보내기(o); 쓰기({ d: 오늘(), e: {} }); }   /* 시험용 */
  };
})();
/* ▲▲ 이용량 부품 끝 ▲▲ */
/* 10-26 현욱님 「월 정액 시범 → 이용량 보고 결정」 — 꺼진 채(처리방침 「익명 이용 통계」 줄 시행 뒤에 켬) */
try { 이용량.설치({ 앱: 'yakjido', 켜짐: false, 주소: 'https://uszalzczpmyifzbamjno.supabase.co', 공개키: 'sb_publishable_YQSz-D-RCXzHGUhso06rMg_GOIIRDuV' }); 이용량.센다('open'); } catch (e) {}

/* ▼▼ 위기번호 표 시작 ▼▼ */
/* ═══ 메디나눔 위기·응급 번호 표 — 나라 기준(말 기준 아님) · 2026-11-04 곁에에서 꺼냄(다섯 앱 공용 · 길동무 「말과 나라」가 재사용)
   나라: ISO 2자. 위기[0] = 한국 109(자살예방) 자리, 위기[1] = 한국 1577-0199(정신건강) 자리. 위기가 비면 응급 번호로.
   확인된 번호만 넣는다(멕시코는 응급 911 만 · 위기 전용 번호 확인 전). 표에 없는 나라는 XX — 번호 null: 누르는 단추 없이 「그 나라 응급 번호로 전화하세요」 글만.
   11-04b: XX 112 기본값 없앰 · 응급 번호 12나라(VN TH PH ID NP UZ KH MN LK BD IN GB) — 출처는 줄 옆.
   나라 고르는 순서: ① localStorage mn.place.country(사용자가 「말과 나라」에서 고른 값) ② 앱이 가진 값 ③ 시간대·기기 지역 짐작.
   ── 공용 부품 셋(위기번호 표 · 설정 부품 · 응급카드 부품) 공통 약속 · 주인: 길동무 세션 ──
   판: 이 파일 안 «판» 한 곳(코드의 판 값). 고치면 판을 올리고 다섯 앱에 다시 심는다. 지금 판 2026-11-05a.
   심는 순서(앱마다 같다): ① 위기번호 표 → ② 설정 부품 → ③ 응급카드 부품 — 표가 앞에 있어야 말과 나라 고르개·응급 번호가 표를 쓴다.
   심기·비교: python3 _도구/공용부품_심기.py 비교 · python3 _도구/공용부품_심기.py <소아|곁에|길동무|CS> · 다른 저장소(약지도): python3 _도구/공용부품_심기.py 파일 <경로>
   ⛔ 앱 사본을 직접 고치지 않는다 — 이 파일을 고치고 다시 심는다(심기 스크립트는 정본과 다른 사본을 보면 멈춘다).
*/
(function () {
  if (window.메디나눔위기번호) return;
  var 판 = '2026-11-05b';   /* 11-05b 유럽연합 26나라(스페인 빼고) 112 · 11-04d 라오스 LA 구급 1195 · TH 1669·VN 115·KH 119 gov.uk 다시 확인 · 11-04c 머리 주석 정리 */
  var 표 = {
    KR: { 이름: { ko: '한국', en: 'Korea', es: 'Corea', ja: '韓国', zh: '韩国' }, 응급: '119', 경찰: '112', 위기: ['109', '1577-0199'] },
    US: { 이름: { ko: '미국', en: 'United States', es: 'Estados Unidos', ja: 'アメリカ', zh: '美国' }, 응급: '911', 경찰: '911', 위기: ['988'] },
    ES: { 이름: { ko: '스페인', en: 'Spain', es: 'España', ja: 'スペイン', zh: '西班牙' }, 응급: '112', 경찰: '112', 위기: ['024'] },
    JP: { 이름: { ko: '일본', en: 'Japan', es: 'Japón', ja: '日本', zh: '日本' }, 응급: '119', 경찰: '110', 위기: ['0570-783-556', '0570-064-556'] }   /* 109(자살예방) 자리 → いのちの電話, 1577-0199(정신건강) 자리 → こころの健康相談統一ダイヤル */,
    CN: { 이름: { ko: '중국', en: 'China', es: 'China', ja: '中国', zh: '中国' }, 응급: '120', 경찰: '110', 위기: ['12356'] },
    MX: { 이름: { ko: '멕시코', en: 'Mexico', es: 'México', ja: 'メキシコ', zh: '墨西哥' }, 응급: '911', 경찰: '911', 위기: ['800 911 2000'] },   /* 11-05 위기 Línea de la Vida 800 911 2000 24시간 — paho.org(25주년) · tabasco.gob.mx(주 보건부) · 11-03 Main — 확인된 응급 911 만(위기 전용 번호는 확인 전이라 넣지 않음 → 위기 자리도 911) */
    HK: { 이름: { ko: '홍콩', en: 'Hong Kong', es: 'Hong Kong', ja: '香港', zh: '香港' }, 응급: '999', 경찰: '999', 위기: ['2896 0000'] },   /* 10-27 Main 표 — The Samaritans(英文) */
    /* 11-04 Main — 한국에 많이 사는 나라부터 «응급(구급) 번호만». 공식 출처 두 곳이 맞는 것만. 위기 상담 번호는 아직 넣지 않음(위기 자리도 응급 번호).
       경찰은 한 번호로 모두 받는 나라만 같은 번호, 나머지는 null(→ 글로 「그 나라 경찰 번호」, 누르는 단추 없음).
       뺀 나라: 미얀마(영국 정부 192 · 미국 대사관은 192 를 고속도로 번호로·다른 번호와 엇갈림) → 그 밖. */
    VN: { 이름: { ko: '베트남', en: 'Vietnam', es: 'Vietnam', ja: 'ベトナム', zh: '越南' }, 응급: '115', 경찰: null, 위기: [] },   /* gov.uk/foreign-travel-advice/vietnam/getting-help · vietnam.travel(베트남 관광청) — 115 구급, 112 아님 */
    TH: { 이름: { ko: '태국', en: 'Thailand', es: 'Tailandia', ja: 'タイ', zh: '泰国' }, 응급: '1669', 경찰: null, 위기: ['1323'] },   /* 11-05 위기 정신건강국 1323 24시간 — thailand.go.th · nationthailand.com · gov.uk Thailand health(1669 보건부) · th.usembassy.gov */
    PH: { 이름: { ko: '필리핀', en: 'Philippines', es: 'Filipinas', ja: 'フィリピン', zh: '菲律宾' }, 응급: '911', 경찰: '911', 위기: ['1553'] },   /* 11-05 위기 NCMH Crisis Hotline 1553(보건부) 24시간 — lusog-isip.deped.gov.ph · DOH 발표(mb.com.ph 2026-01) · gov.uk Philippines getting-help(911 구급·소방·경찰) · ph.usembassy.gov */
    ID: { 이름: { ko: '인도네시아', en: 'Indonesia', es: 'Indonesia', ja: 'インドネシア', zh: '印度尼西亚' }, 응급: '118', 경찰: null, 위기: [] },   /* gov.uk Indonesia getting-help(118) · indonesia.travel(118·119) */
    NP: { 이름: { ko: '네팔', en: 'Nepal', es: 'Nepal', ja: 'ネパール', zh: '尼泊尔' }, 응급: '102', 경찰: null, 위기: [] },   /* gov.uk Nepal getting-help · np.usembassy.gov · heoc.mohp.gov.np */
    UZ: { 이름: { ko: '우즈베키스탄', en: 'Uzbekistan', es: 'Uzbekistán', ja: 'ウズベキスタン', zh: '乌兹别克斯坦' }, 응급: '103', 경찰: null, 위기: [] },   /* gov.uk Uzbekistan getting-help · uzbekistan.travel */
    KH: { 이름: { ko: '캄보디아', en: 'Cambodia', es: 'Camboya', ja: 'カンボジア', zh: '柬埔寨' }, 응급: '119', 경찰: null, 위기: [] },   /* gov.uk Cambodia getting-help · travel.state.gov Cambodia */
    LA: { 이름: { ko: '라오스', en: 'Laos', es: 'Laos', ja: 'ラオス', zh: '老挝' }, 응급: '1195', 경찰: null, 위기: [] },   /* 11-04d 구급 1195(경찰 1191·화재 1190 따로) — gov.uk/foreign-travel-advice/laos/getting-help · travel.gc.ca Laos 둘 다 1195. 일부 생활 안내의 195 는 공식 아님 */
    MN: { 이름: { ko: '몽골', en: 'Mongolia', es: 'Mongolia', ja: 'モンゴル', zh: '蒙古' }, 응급: '103', 경찰: null, 위기: [] },   /* gov.uk Mongolia getting-help · mn.usembassy.gov */
    LK: { 이름: { ko: '스리랑카', en: 'Sri Lanka', es: 'Sri Lanka', ja: 'スリランカ', zh: '斯里兰卡' }, 응급: '1990', 경찰: null, 위기: ['1926'] },   /* 11-05 위기 국립정신건강연구소 1926 24시간(보건부 소속) — NIMH 연차보고 2022 · sundaytimes.lk · gov.uk Sri Lanka health · lk.usembassy.gov(1990 Suwa Seriya) */
    BD: { 이름: { ko: '방글라데시', en: 'Bangladesh', es: 'Bangladés', ja: 'バングラデシュ', zh: '孟加拉国' }, 응급: '999', 경찰: '999', 위기: [] },   /* gov.uk Bangladesh getting-help · 999.gov.bd */
    IN: { 이름: { ko: '인도', en: 'India', es: 'India', ja: 'インド', zh: '印度' }, 응급: '112', 경찰: '112', 위기: ['14416'] },   /* 11-05 위기 Tele-MANAS 14416(보건가족복지부) — pib.gov.in PRID 2022057 · PRID 1919200 · gov.uk India health(112) · India ERSS(112 · 내무부) */
    GB: { 이름: { ko: '영국', en: 'United Kingdom', es: 'Reino Unido', ja: 'イギリス', zh: '英国' }, 응급: '999', 경찰: '999', 위기: ['116 123'] },   /* gov.uk · NHS 999 · 11-05 위기 Samaritans 116 123 24시간 — phw.nhs.wales · 111.wales.nhs.uk · cntw.nhs.uk */
    /* 11-05 현욱님 결정(소아 경유) — 유럽연합 27개국 공통 응급 번호 112(유럽 지침 2002/22/EC 제26조 · (EU) 2018/1972 제109조). 위기 상담은 나라마다 달라 빈칸(→ 응급 번호), 경찰도 빈칸. 스페인은 위에 024 와 함께 있다 */
    AT: { 이름: { ko: '오스트리아', en: 'Austria', es: 'Austria', ja: 'オーストリア', zh: '奥地利' }, 응급: '112', 경찰: null, 위기: [] },
    BE: { 이름: { ko: '벨기에', en: 'Belgium', es: 'Bélgica', ja: 'ベルギー', zh: '比利时' }, 응급: '112', 경찰: null, 위기: [] },
    BG: { 이름: { ko: '불가리아', en: 'Bulgaria', es: 'Bulgaria', ja: 'ブルガリア', zh: '保加利亚' }, 응급: '112', 경찰: null, 위기: [] },
    HR: { 이름: { ko: '크로아티아', en: 'Croatia', es: 'Croacia', ja: 'クロアチア', zh: '克罗地亚' }, 응급: '112', 경찰: null, 위기: [] },
    CY: { 이름: { ko: '키프로스', en: 'Cyprus', es: 'Chipre', ja: 'キプロス', zh: '塞浦路斯' }, 응급: '112', 경찰: null, 위기: [] },
    CZ: { 이름: { ko: '체코', en: 'Czechia', es: 'Chequia', ja: 'チェコ', zh: '捷克' }, 응급: '112', 경찰: null, 위기: [] },
    DK: { 이름: { ko: '덴마크', en: 'Denmark', es: 'Dinamarca', ja: 'デンマーク', zh: '丹麦' }, 응급: '112', 경찰: null, 위기: [] },
    EE: { 이름: { ko: '에스토니아', en: 'Estonia', es: 'Estonia', ja: 'エストニア', zh: '爱沙尼亚' }, 응급: '112', 경찰: null, 위기: [] },
    FI: { 이름: { ko: '핀란드', en: 'Finland', es: 'Finlandia', ja: 'フィンランド', zh: '芬兰' }, 응급: '112', 경찰: null, 위기: [] },
    FR: { 이름: { ko: '프랑스', en: 'France', es: 'Francia', ja: 'フランス', zh: '法国' }, 응급: '112', 경찰: null, 위기: [] },
    DE: { 이름: { ko: '독일', en: 'Germany', es: 'Alemania', ja: 'ドイツ', zh: '德国' }, 응급: '112', 경찰: null, 위기: [] },
    GR: { 이름: { ko: '그리스', en: 'Greece', es: 'Grecia', ja: 'ギリシャ', zh: '希腊' }, 응급: '112', 경찰: null, 위기: [] },
    HU: { 이름: { ko: '헝가리', en: 'Hungary', es: 'Hungría', ja: 'ハンガリー', zh: '匈牙利' }, 응급: '112', 경찰: null, 위기: [] },
    IE: { 이름: { ko: '아일랜드', en: 'Ireland', es: 'Irlanda', ja: 'アイルランド', zh: '爱尔兰' }, 응급: '112', 경찰: null, 위기: [] },
    IT: { 이름: { ko: '이탈리아', en: 'Italy', es: 'Italia', ja: 'イタリア', zh: '意大利' }, 응급: '112', 경찰: null, 위기: [] },
    LV: { 이름: { ko: '라트비아', en: 'Latvia', es: 'Letonia', ja: 'ラトビア', zh: '拉脱维亚' }, 응급: '112', 경찰: null, 위기: [] },
    LT: { 이름: { ko: '리투아니아', en: 'Lithuania', es: 'Lituania', ja: 'リトアニア', zh: '立陶宛' }, 응급: '112', 경찰: null, 위기: [] },
    LU: { 이름: { ko: '룩셈부르크', en: 'Luxembourg', es: 'Luxemburgo', ja: 'ルクセンブルク', zh: '卢森堡' }, 응급: '112', 경찰: null, 위기: [] },
    MT: { 이름: { ko: '몰타', en: 'Malta', es: 'Malta', ja: 'マルタ', zh: '马耳他' }, 응급: '112', 경찰: null, 위기: [] },
    NL: { 이름: { ko: '네덜란드', en: 'Netherlands', es: 'Países Bajos', ja: 'オランダ', zh: '荷兰' }, 응급: '112', 경찰: null, 위기: [] },
    PL: { 이름: { ko: '폴란드', en: 'Poland', es: 'Polonia', ja: 'ポーランド', zh: '波兰' }, 응급: '112', 경찰: null, 위기: [] },
    PT: { 이름: { ko: '포르투갈', en: 'Portugal', es: 'Portugal', ja: 'ポルトガル', zh: '葡萄牙' }, 응급: '112', 경찰: null, 위기: [] },
    RO: { 이름: { ko: '루마니아', en: 'Romania', es: 'Rumanía', ja: 'ルーマニア', zh: '罗马尼亚' }, 응급: '112', 경찰: null, 위기: [] },
    SK: { 이름: { ko: '슬로바키아', en: 'Slovakia', es: 'Eslovaquia', ja: 'スロバキア', zh: '斯洛伐克' }, 응급: '112', 경찰: null, 위기: [] },
    SI: { 이름: { ko: '슬로베니아', en: 'Slovenia', es: 'Eslovenia', ja: 'スロベニア', zh: '斯洛文尼亚' }, 응급: '112', 경찰: null, 위기: [] },
    SE: { 이름: { ko: '스웨덴', en: 'Sweden', es: 'Suecia', ja: 'スウェーデン', zh: '瑞典' }, 응급: '112', 경찰: null, 위기: [] },
    XX: { 이름: { ko: '그 밖', en: 'Other', es: 'Otro', ja: 'その他', zh: '其他' }, 응급: null, 경찰: null, 위기: [] }   /* 11-04 Main — 모르는 나라는 누르는 번호 없음(112 기본값 없앰) */
  };
  function 고른곳() { try { var v = JSON.parse(localStorage.getItem('mn.place') || 'null'); if (v && v.country) return 표[v.country] ? v.country : 'XX'; } catch (e) {} return null; }
  window.메디나눔위기번호 = { 판: 판, 표: 표, 고른곳: 고른곳 };   /* 표를 쓰는 앱은 읽기만 */
})();
/* ▲▲ 위기번호 표 끝 ▲▲ */
/* ▼▼ 설정 부품 시작 ▼▼ */
/* ═══ 설정 뼈대 — 메디나눔 다섯 앱 같은 순서·같은 꼴 (2026-11-03 현욱님 「100점 검수 라운드 2」 · 주인: 길동무 세션)
   요청서 docs/requests/20261103_100점_검수_라운드2.md A·D
   순서(고정): ① 계정 카드 ② 회원권 줄 ③ 나에게 맞추기(앱 고유) ④ 알림 ⑤ 화면과 언어(언어 · 글자 크기 3단 · 화면 밝기 3단 — 글자·밝기는 이 자리에서 바로 고름)
               ⑥ 내 기록(동의 · 내 기록 파일로 받기(JSON) · 옮기기·되살리기 · 모두 지우기 · 앱 고유) ⑦ 이 앱(처리방침 · 앱 정보 · 문의)
   꼴: 줄은 앱의 줄 그리기 함수(줄:)로 그린다 — 앱 고유의 줄 모양·아이콘을 그대로. 묶음 제목·표준 줄 이름은 부품이 다섯 말로 들고 다닌다.
   쓰는 법(앱 끝, 계정·회원권 부품 뒤):
     설정판.설치({ app:'gildongmu', 언어: function(){ return 'ko' },
       줄: function(아이콘, 제목, 설명, 값, 부름){ return '<button …>' },   // 앱의 줄 모양
       아이콘: function(이름){ return '<svg…>' },                          // 이름: user · card · hands · bell · globe · text · sun · shield · download · copy · trash · doc · info · chat · plane · heart
       계정: function(){ return 계정.카드HTML() }, 회원권: true,
       나에게: [{ 아이콘:'hands', 제목:'…', 설명:'…', 값:'…', 부름:"openSettings('role')" }, …],
       알림: { 설명:'…', 값:'켜짐', 부름:"openSettings('noti')" },
       언어: { 값:'한국어', 부름:"openSettings('lang')" },
       글자: { 값: function(){ return 0|1|2 }, 바꿈: function(n){…} },
       밝기: { 값: function(){ return 'light'|'dark'|'auto' }, 바꿈: function(v){…}, 준비: true },   // 준비:false 면 「어둡게」를 「준비 중」으로(되는 척 금지)
       동의: { 값:'…', 부름:"openSettings('consent')" },
       파일: { 부름:'saveBackupFile()' }, 옮기기: { 부름:'openBackup()' }, 지우기: { 부름:"openSettings('data')" },
       기록더: [{…}],                                                       // 앱 고유(기내에서 쓰기 · 사연 보내기 등)
       처리방침: 'https://medinanum.com/privacy-gildongmu.html', 정보: { 부름:'openAbout()' }, 문의: { 부름:"openSettings('help')" },
       아래말: '…', 다시그리기: function(){ openSettings('menu') } });
     화면: 설정판.HTML()  — 시트 맨 위 제목 아래에 통째로.
   ⛔ 지우기·계정 지우기는 앱의 확인 화면으로만 간다(이 부품이 직접 지우지 않는다).
   ── 공용 부품 셋(위기번호 표 · 설정 부품 · 응급카드 부품) 공통 약속 · 주인: 길동무 세션 ──
   판: 이 파일 안 «판» 한 곳(코드의 판 값). 고치면 판을 올리고 다섯 앱에 다시 심는다. 지금 판 2026-11-05a.
   심는 순서(앱마다 같다): ① 위기번호 표 → ② 설정 부품 → ③ 응급카드 부품 — 표가 앞에 있어야 말과 나라 고르개·응급 번호가 표를 쓴다.
   심기·비교: python3 _도구/공용부품_심기.py 비교 · python3 _도구/공용부품_심기.py <소아|곁에|길동무|CS> · 다른 저장소(약지도): python3 _도구/공용부품_심기.py 파일 <경로>
   ⛔ 앱 사본을 직접 고치지 않는다 — 이 파일을 고치고 다시 심는다(심기 스크립트는 정본과 다른 사본을 보면 멈춘다).
*/
(function () {
  if (window.설정판 && window.설정판.__v) return;
  var 판 = '2026-11-05a';   /* 11-05a 유럽연합 시간대 */   /* 11-04i 묶음 제목 h3→h2(화면 읽기 머리글 건너뜀 없게 · 곁에가 찾음) */   /* 11-04h 기기 언어로 나라 짐작 안 함(모르면 빈칸·번호 없음) · 11-04g 응급번호()·번호HTML() · 11-04f 제목·설명 이스케이프 · 11-04e 기본 줄 값 이스케이프 · 11-04d 머리 주석 정리 */
  var 설정 = { app: 'app', 언어: null, 줄: null, 아이콘: null, 다시그리기: null };
  var 글표 = {
    ko: { 맞추기: '나에게 맞추기', 알림: '알림', 화면: '화면과 언어', 기록: '내 기록', 앱: '이 앱',
      알림제목: '알림', 언어: '언어 · Language', 글자: '글자 크기', 글자들: ['기본', '조금 크게', '가장 크게'], 밝기: '화면 밝기', 밝기들: ['밝게', '어둡게', '기기 설정 따라'], 준비중: '준비 중',
      동의: '내 동의 내용', 동의설명: '동의를 바꾸거나 철회', 파일: '내 기록 파일로 받기', 파일설명: '모든 기록을 파일 하나(JSON)로 이 기기에 저장', 옮기기: '옮기기 · 되살리기', 옮기기설명: '복사해 두었다가 다른 기기에서 되살리기',
      지우기: '모두 지우기', 지우기설명: '이 기기의 기록과 설정 — 확인 뒤 지워요', 처리방침: '개인정보 처리방침', 처리방침설명: '무엇을 · 왜 · 언제까지', 정보: '이 앱에 대하여', 정보설명: '의료기기 아님 · 근거 자료 · 약관', 문의: '문의하고 잘못된 내용 알리기', 문의설명: '고쳐야 할 것을 알려 주세요' },
    en: { 맞추기: 'Personalize', 알림: 'Notifications', 화면: 'Display and language', 기록: 'My records', 앱: 'This app',
      알림제목: 'Notifications', 언어: 'Language · 언어', 글자: 'Text size', 글자들: ['Default', 'Larger', 'Largest'], 밝기: 'Screen brightness', 밝기들: ['Light', 'Dark', 'Follow device'], 준비중: 'Coming soon',
      동의: 'My consents', 동의설명: 'Change or withdraw consent', 파일: 'Download my records', 파일설명: 'Save all records to this device as one file (JSON)', 옮기기: 'Move · restore', 옮기기설명: 'Copy and restore on another device',
      지우기: 'Delete everything', 지우기설명: 'Records and settings on this device — deleted after you confirm', 처리방침: 'Privacy policy', 처리방침설명: 'What, why and for how long', 정보: 'About this app', 정보설명: 'Not a medical device · sources · terms', 문의: 'Contact us and report errors', 문의설명: 'Tell us what needs fixing' },
    es: { 맞추기: 'Ajustado a mí', 알림: 'Avisos', 화면: 'Pantalla e idioma', 기록: 'Mis registros', 앱: 'Esta app',
      알림제목: 'Avisos', 언어: 'Idioma · 언어', 글자: 'Tamaño del texto', 글자들: ['Normal', 'Más grande', 'Lo más grande'], 밝기: 'Pantalla', 밝기들: ['Clara', 'Oscura', 'Según el dispositivo'], 준비중: 'Muy pronto',
      동의: 'Mis consentimientos', 동의설명: 'Cambiar o retirar el consentimiento', 파일: 'Descargar mis registros', 파일설명: 'Guardar todos los registros en este dispositivo en un archivo (JSON)', 옮기기: 'Mover · restaurar', 옮기기설명: 'Copiar y restaurar en otro dispositivo',
      지우기: 'Borrar todo', 지우기설명: 'Registros y ajustes de este dispositivo: se borran tras confirmar', 처리방침: 'Política de privacidad', 처리방침설명: 'Qué, por qué y hasta cuándo', 정보: 'Sobre esta app', 정보설명: 'No es un producto sanitario · fuentes · condiciones', 문의: 'Contacto y notificación de errores', 문의설명: 'Díganos qué hay que corregir' },
    ja: { 맞추기: '自分に合わせる', 알림: '通知', 화면: '画面と言語', 기록: '自分の記録', 앱: 'このアプリ',
      알림제목: '通知', 언어: '言語 · 언어', 글자: '文字の大きさ', 글자들: ['標準', '少し大きく', 'いちばん大きく'], 밝기: '画面の明るさ', 밝기들: ['明るく', '暗く', '端末の設定に合わせる'], 준비중: '準備中',
      동의: '同意の内容', 동의설명: '同意の変更・撤回', 파일: '記録をファイルで受け取る', 파일설명: 'すべての記録を1つのファイル（JSON）でこの端末に保存', 옮기기: '移す · 戻す', 옮기기설명: 'コピーして別の端末で戻す',
      지우기: 'すべて消す', 지우기설명: 'この端末の記録と設定 — 確認してから消します', 처리방침: '個人情報の取り扱い', 처리방침설명: '何を・なぜ・いつまで', 정보: 'このアプリについて', 정보설명: '医療機器ではありません · 根拠 · 規約', 문의: 'お問い合わせ・誤りの報告', 문의설명: '直すべきところを教えてください' },
    zh: { 맞추기: '为我调整', 알림: '提醒', 화면: '显示和语言', 기록: '我的记录', 앱: '本应用',
      알림제목: '提醒', 언어: '语言 · 언어', 글자: '字体大小', 글자들: ['标准', '大一些', '最大'], 밝기: '屏幕亮度', 밝기들: ['浅色', '深色', '跟随设备'], 준비중: '即将推出',
      동의: '我的同意', 동의설명: '更改或撤回同意', 파일: '把记录下载为文件', 파일설명: '把全部记录以一个文件（JSON）保存到本设备', 옮기기: '转移 · 恢复', 옮기기설명: '复制后在其他设备恢复',
      지우기: '全部删除', 지우기설명: '本设备上的记录和设置——确认后删除', 처리방침: '隐私政策', 처리방침설명: '收集什么、为什么、保存多久', 정보: '关于本应用', 정보설명: '不是医疗器械 · 依据 · 条款', 문의: '联系我们、报告错误', 문의설명: '告诉我们需要改正的地方' }
  };
  function 말() { var l = null; try { if (typeof 설정.언어 === 'function') l = 설정.언어(); } catch (e) {} if (!l) l = (document.documentElement && document.documentElement.lang) || 'ko'; l = String(l).toLowerCase().slice(0, 2); return 글표[l] ? l : 'ko'; }
  function 글(k) { var t = 글표[말()][k]; return t == null ? 글표.ko[k] : t; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function 값(v) { try { return typeof v === 'function' ? v() : v; } catch (e) { return null; } }
  function 아이콘(n) { try { if (typeof 설정.아이콘 === 'function') return 설정.아이콘(n) || ''; } catch (e) {} return ''; }
  function 줄(a, 제목, 설명, 값글, 부름) {
    if (!부름) return '';
    /* 11-04f 보안(곁에가 찾음) — 제목·설명은 «글자»로만 받아 부품이 한 번 이스케이프한다(앱의 줄 그리기는 제목·설명을 그대로 넣는다). 값은 앱의 줄 그리기가 이스케이프한다(소아·곁에·길동무 · CS 는 설치에서) */
    제목 = esc(제목); 설명 = 설명 ? esc(설명) : '';
    try { if (typeof 설정.줄 === 'function') return 설정.줄(아이콘(a), 제목, 설명 || '', 값글 || '', 부름); } catch (e) {}
    /* 11-04e 보안 — 기본 줄은 값도 글자로만(제목·설명은 위에서 이미) */
    return '<button type="button" class="ms-row" onclick="' + esc(부름) + '"><span class="ms-rt"><b>' + 제목 + '</b>' + (설명 ? '<span>' + 설명 + '</span>' : '') + '</span>' + (값글 ? '<span class="ms-rv">' + esc(값글) + '</span>' : '') + '</button>';
  }
  function 묶음(제목, 안) { return 안 ? '<div class="ms-group"><h2 class="ms-h">' + 제목 + '</h2><div class="menu">' + 안 + '</div></div>' : ''; }
  function 고름(이름, 목록, 지금, 부름, 막힘) {
    return '<div class="ms-seg" role="group" aria-label="' + esc(이름) + '"><span class="ms-sl">' + 이름 + '</span><div class="ms-sb">' + 목록.map(function (x, i) {
      var 끔 = 막힘 && 막힘(i), on = !끔 && 지금 === i;
      return '<button type="button" class="' + (on ? 'on' : '') + '" aria-pressed="' + on + '"' + (끔 ? ' disabled aria-disabled="true"' : ' onclick="' + 부름 + '(' + i + ')"') + '>' + x + (끔 ? ' <span class="ms-soon">' + 글('준비중') + '</span>' : '') + '</button>';
    }).join('') + '</div></div>';
  }
  var 밝기값 = ['light', 'dark', 'auto'];
  function HTML() {
    스타일();
    var o = 설정, h = '';
    h += 값(o.계정) || '';
    if (o.회원권 && window.회원권) { var q = 회원권.줄(); h += '<div class="menu">' + 줄('card', q.제목, q.설명, q.값, '회원권.열기()') + '</div>'; }
    h += 묶음(글('맞추기'), (값(o.나에게) || []).map(function (x) { return 줄(x.아이콘, 값(x.제목), 값(x.설명), 값(x.값), x.부름); }).join(''));
    if (o.알림) h += 묶음(글('알림'), 줄('bell', 글('알림제목'), 값(o.알림.설명), 값(o.알림.값), o.알림.부름));
    var 화 = '';
    if (o.언어) 화 += 줄('globe', 글('언어'), 값(o.언어.설명), 값(o.언어.값), o.언어.부름);
    화 += 곳줄();
    var 고름칸 = '';
    if (o.글자) 고름칸 += 고름(글('글자'), 글('글자들'), Number(값(o.글자.값)) || 0, '설정판.글자');
    if (o.밝기) { var 준비 = o.밝기.준비 !== false; 고름칸 += 고름(글('밝기'), 글('밝기들'), 밝기값.indexOf(값(o.밝기.값) || 'light'), '설정판.밝기', function (i) { return !준비 && i > 0; }); }
    if (화 || 고름칸) h += '<div class="ms-group"><h2 class="ms-h">' + 글('화면') + '</h2>' + (화 ? '<div class="menu">' + 화 + '</div>' : '') + (고름칸 ? '<div class="ms-segs">' + 고름칸 + '</div>' : '') + '</div>';
    var 기 = '';
    if (o.동의) 기 += 줄('shield', 글('동의'), 값(o.동의.설명) || 글('동의설명'), 값(o.동의.값), o.동의.부름);
    if (o.파일) 기 += 줄('download', 글('파일'), 글('파일설명'), 값(o.파일.값), o.파일.부름);
    if (o.옮기기) 기 += 줄('copy', 글('옮기기'), 글('옮기기설명'), 값(o.옮기기.값), o.옮기기.부름);
    (값(o.기록더) || []).forEach(function (x) { 기 += 줄(x.아이콘, 값(x.제목), 값(x.설명), 값(x.값), x.부름); });
    if (o.지우기) 기 += 줄('trash', 글('지우기'), 글('지우기설명'), 값(o.지우기.값), o.지우기.부름);
    h += 묶음(글('기록'), 기);
    var 앱 = '';
    if (o.처리방침) 앱 += 줄('doc', 글('처리방침'), 글('처리방침설명'), '', "window.open('" + String(o.처리방침).replace(/'/g, '') + "','_blank','noopener')");
    if (o.정보) 앱 += 줄('info', 글('정보'), 값(o.정보.설명) || 글('정보설명'), '', o.정보.부름);
    if (o.문의) 앱 += 줄('chat', 글('문의'), 글('문의설명'), '', o.문의.부름);
    h += 묶음(글('앱'), 앱);
    if (o.아래말) h += '<p class="tiny ms-foot">' + 값(o.아래말) + '</p>';
    return '<div class="ms" id="msSettings">' + h + '</div>';
  }
  /* ── 말과 나라(2026-11-04 현욱님 「진행」 · docs/requests/20261104_언어나라_묻기.md) ──
     앱 말 · 사는 나라 · 그 나라 말 수준을 한 화면 세 줄로(미리 채움 · 「맞아요」 한 번 · 건너뛰기 없음).
     값: localStorage mn.place = {lang, country, level('ok'|'some'|'none'), at} — 다섯 앱 같은 열쇠. 읽기 설정판.말과나라() · 바뀌면 window 에 'mn:place' 이벤트.
     앱이 주는 것(설치의 말과나라: {…}): 기본() → {lang, country} 미리 채울 값 · 바꿈(값, 말바뀜, 나라바뀜) → 앱 말·나라에 반영 · 나라들: ['KR', …] 고를 목록.
     첫 실행: 앱이 동의를 마친 뒤 설정판.말과나라확인() — 값이 없을 때만 연다. 자동 시험(navigator.webdriver)에서는 스스로 열지 않는다(설정판.말과나라열기() 로 연다). */
  var 말이름 = { ko: '한국어', en: 'English', es: 'Español', ja: '日本語', zh: '中文' }, 말순 = ['ko', 'en', 'es', 'ja', 'zh'];
  var 나라이름 = {
    KR: ['한국', 'South Korea', 'Corea del Sur', '韓国', '韩国'], US: ['미국', 'United States', 'Estados Unidos', 'アメリカ', '美国'], ES: ['스페인', 'Spain', 'España', 'スペイン', '西班牙'],
    JP: ['일본', 'Japan', 'Japón', '日本', '日本'], CN: ['중국', 'China', 'China', '中国', '中国'], MX: ['멕시코', 'Mexico', 'México', 'メキシコ', '墨西哥'], HK: ['홍콩', 'Hong Kong', 'Hong Kong', '香港', '香港'],
    GB: ['영국', 'United Kingdom', 'Reino Unido', 'イギリス', '英国'], CA: ['캐나다', 'Canada', 'Canadá', 'カナダ', '加拿大'], AU: ['호주', 'Australia', 'Australia', 'オーストラリア', '澳大利亚'],
    NZ: ['뉴질랜드', 'New Zealand', 'Nueva Zelanda', 'ニュージーランド', '新西兰'], IE: ['아일랜드', 'Ireland', 'Irlanda', 'アイルランド', '爱尔兰'], IN: ['인도', 'India', 'India', 'インド', '印度'],
    SG: ['싱가포르', 'Singapore', 'Singapur', 'シンガポール', '新加坡'], PH: ['필리핀', 'Philippines', 'Filipinas', 'フィリピン', '菲律宾'], EU: ['유럽(EU)', 'Europe (EU)', 'Europa (UE)', 'ヨーロッパ（EU）', '欧洲（欧盟）'],
    XX: ['그 밖의 나라', 'Another country', 'Otro país', 'その他の国', '其他国家'] };
  var 곁에나라들 = ['KR', 'US', 'ES', 'JP', 'CN', 'MX', 'HK', 'XX'];   /* 곁에 나라 표(11-03) 그대로 — 앱이 나라들로 더 줄 수 있다 */
  var 나라말 = { KR: 'ko', US: 'en', GB: 'en', CA: 'en', AU: 'en', NZ: 'en', IE: 'en', SG: 'en', PH: 'en', IN: 'en', ES: 'es', MX: 'es', JP: 'ja', CN: 'zh', HK: 'zh' };
  var 말이름들 = { ko: ['한국어', 'Korean', 'coreano', '韓国語', '韩语'], en: ['영어', 'English', 'inglés', '英語', '英语'], es: ['스페인어', 'Spanish', 'español', 'スペイン語', '西班牙语'],
    ja: ['일본어', 'Japanese', 'japonés', '日本語', '日语'], zh: ['중국어', 'Chinese', 'chino', '中国語', '中文'] };
  var 곳글 = {
    ko: { 제목: '쓰는 말과 사는 나라', 설명: '맞는 응급 번호와 안내를 드리려고 여쭤요. 맞으면 한 번만 눌러 주세요.', 앱말: '앱을 볼 말', 나라: '지금 사는 나라', 수준: '{말}를 얼마나 하세요?', 수준일반: '그 나라 말을 얼마나 하세요?',
      수준들: ['편해요', '조금 해요', '거의 못해요'], 맞아요: '맞아요', 나라고름: '나라를 골라 주세요', 줄: '말과 나라', 줄설명: '응급 번호와 안내를 이 값으로 맞춰요', 안정함: '아직 안 정함' },
    en: { 제목: 'Your language and country', 설명: 'We ask so we can show the right emergency numbers and guidance. If this looks right, tap once.', 앱말: 'App language', 나라: 'Country you live in now', 수준: 'How well do you speak {말}?', 수준일반: 'How well do you speak the local language?',
      수준들: ['Comfortably', 'A little', 'Hardly at all'], 맞아요: 'Looks right', 나라고름: 'Choose your country', 줄: 'Language and country', 줄설명: 'Emergency numbers and guidance follow these', 안정함: 'Not set yet' },
    es: { 제목: 'Su idioma y su país', 설명: 'Se lo preguntamos para mostrarle los números de emergencia y la información correctos. Si es correcto, pulse una vez.', 앱말: 'Idioma de la app', 나라: 'País donde vive ahora', 수준: '¿Qué tal habla {말}?', 수준일반: '¿Qué tal habla el idioma del país?',
      수준들: ['Con soltura', 'Un poco', 'Casi nada'], 맞아요: 'Es correcto', 나라고름: 'Elija su país', 줄: 'Idioma y país', 줄설명: 'Los números de emergencia y la información siguen estos datos', 안정함: 'Sin elegir' },
    ja: { 제목: '使う言葉と住んでいる国', 설명: '正しい緊急番号と案内をお伝えするためにお聞きしています。合っていれば一度押してください。', 앱말: 'アプリの言葉', 나라: '今住んでいる国', 수준: '{말}はどのくらい話せますか？', 수준일반: 'その国の言葉はどのくらい話せますか？',
      수준들: ['問題なく話せる', '少し話せる', 'ほとんど話せない'], 맞아요: 'これで合っています', 나라고름: '国を選んでください', 줄: '言葉と国', 줄설명: '緊急番号と案内をこの内容に合わせます', 안정함: 'まだ選んでいません' },
    zh: { 제목: '您的语言和所在国家', 설명: '为了向您显示正确的急救电话和信息，我们需要了解这些。如果没问题，请点一下。', 앱말: '应用语言', 나라: '目前居住的国家', 수준: '您的{말}水平如何？', 수준일반: '您的当地语言水平如何？',
      수준들: ['很流利', '会一点', '几乎不会'], 맞아요: '没问题', 나라고름: '请选择国家', 줄: '语言和国家', 줄설명: '急救电话和信息会按此设置', 안정함: '尚未选择' } };
  function 곳(k, l) { l = l || 말(); return (곳글[l] || 곳글.ko)[k]; }
  function 칸(l) { var i = 말순.indexOf(l); return i < 0 ? 0 : i; }
  var 곳열쇠 = 'mn.place';
  function 곳읽기() { try { var v = JSON.parse(localStorage.getItem(곳열쇠) || 'null'); return v && v.lang && v.country && v.level ? v : null; } catch (e) { return null; } }
  function 나라짐작() {
    try { var tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
      var 표 = { 'Asia/Seoul': 'KR', 'Asia/Tokyo': 'JP', 'Asia/Shanghai': 'CN', 'Asia/Chongqing': 'CN', 'Asia/Urumqi': 'CN', 'Asia/Hong_Kong': 'HK', 'Europe/Madrid': 'ES', 'Atlantic/Canary': 'ES', 'Africa/Ceuta': 'ES',
        'America/Mexico_City': 'MX', 'America/Monterrey': 'MX', 'America/Merida': 'MX', 'America/Cancun': 'MX', 'America/Chihuahua': 'MX', 'America/Mazatlan': 'MX', 'America/Hermosillo': 'MX', 'America/Tijuana': 'MX',
        'Europe/London': 'GB', 'Europe/Dublin': 'IE', 'Asia/Singapore': 'SG', 'Asia/Manila': 'PH', 'Asia/Kolkata': 'IN', 'Asia/Calcutta': 'IN', 'Pacific/Auckland': 'NZ',
        'Asia/Ho_Chi_Minh': 'VN', 'Asia/Saigon': 'VN', 'Asia/Bangkok': 'TH', 'Asia/Jakarta': 'ID', 'Asia/Makassar': 'ID', 'Asia/Jayapura': 'ID', 'Asia/Kathmandu': 'NP', 'Asia/Katmandu': 'NP', 'Asia/Tashkent': 'UZ', 'Asia/Samarkand': 'UZ',
        'Asia/Phnom_Penh': 'KH', 'Asia/Ulaanbaatar': 'MN', 'Asia/Ulan_Bator': 'MN', 'Asia/Colombo': 'LK', 'Asia/Dhaka': 'BD',
        'Europe/Berlin': 'DE', 'Europe/Busingen': 'DE', 'Europe/Paris': 'FR', 'Europe/Rome': 'IT', 'Europe/Amsterdam': 'NL', 'Europe/Brussels': 'BE', 'Europe/Vienna': 'AT', 'Europe/Warsaw': 'PL', 'Europe/Prague': 'CZ', 'Europe/Stockholm': 'SE', 'Europe/Copenhagen': 'DK', 'Europe/Helsinki': 'FI', 'Europe/Lisbon': 'PT', 'Atlantic/Madeira': 'PT', 'Atlantic/Azores': 'PT', 'Europe/Athens': 'GR', 'Europe/Budapest': 'HU', 'Europe/Bucharest': 'RO', 'Europe/Sofia': 'BG', 'Europe/Zagreb': 'HR', 'Europe/Ljubljana': 'SI', 'Europe/Bratislava': 'SK', 'Europe/Vilnius': 'LT', 'Europe/Riga': 'LV', 'Europe/Tallinn': 'EE', 'Europe/Luxembourg': 'LU', 'Europe/Malta': 'MT', 'Asia/Nicosia': 'CY', 'Asia/Famagusta': 'CY', 'Europe/Nicosia': 'CY', 'Europe/Mariehamn': 'FI' };   /* 11-05 유럽연합(소아 경유 현욱님 결정) */   /* 11-04c 공용 표의 나라 */
      if (표[tz]) return 표[tz];
      if (/^America\/(New_York|Chicago|Denver|Los_Angeles|Phoenix|Anchorage|Detroit|Indiana|Kentucky|Boise|Juneau|Sitka|Nome|Adak|Menominee|North_Dakota)|^Pacific\/Honolulu$/.test(tz)) return 'US';
      if (/^America\/(Toronto|Vancouver|Edmonton|Winnipeg|Halifax|St_Johns|Regina|Montreal)/.test(tz)) return 'CA';
      if (/^Australia\//.test(tz)) return 'AU';
    } catch (e) {}
    /* 11-04h Main 결정 — 기기 언어의 지역(ko-KR·en-US)으로 짐작하지 않는다: 크롬 기본 en-US 인 기기가 많아 미국 밖 사람에게 911, 해외의 ko-KR 기기에 119 가 나갈 수 있다.
       시간대 표에 없으면 모름(XX) → 번호 없이 「현지 응급 번호」, 말과 나라 화면은 「나라를 골라 주세요」 빈칸 */
    return 'XX';
  }
  function 곳기본() {
    표합치기();
    var o = 설정.말과나라 || {}, d = 값(o.기본) || {}, l = d.lang || 말();
    if (말순.indexOf(l) < 0) l = 'en';
    var c = (d.country && 나라이름[d.country] && d.country !== 'XX') ? d.country : 나라짐작();
    return { lang: l, country: c === 'XX' ? '' : c };   /* 모르면 빈칸 — 사용자가 고른다(그 밖의 나라도 고를 수 있다) */
  }
  /* 11-04c — 공용 위기번호 표(window.메디나눔위기번호 · _도구/위기번호_표.js)의 나라도 고르개에 — 베트남·태국 등이 「그 밖」으로 묶이지 않게 */
  function 공용표() { try { return (window.메디나눔위기번호 && 메디나눔위기번호.표) || null; } catch (e) { return null; } }
  function 표합치기() { var t = 공용표(); if (!t) return; Object.keys(t).forEach(function (k) { if (나라이름[k] || !t[k] || !t[k].이름) return; 나라이름[k] = 말순.map(function (l) { return t[k].이름[l] || t[k].이름.en || k; }); }); }
  function 나라목록() { 표합치기(); var o = 설정.말과나라 || {}, a = (값(o.나라들) || 곁에나라들).filter(function (k) { return 나라이름[k]; }), t = 공용표();
    if (t) Object.keys(t).forEach(function (k) { if (k !== 'XX' && a.indexOf(k) < 0 && 나라이름[k]) a.push(k); });
    a = a.filter(function (k) { return k !== 'XX'; }); a.push('XX'); return a; }
  var 고르는중 = null;
  function 수준묻나(p) { return 나라말[p.country] !== p.lang; }
  function 곳그림() {
    var p = 고르는중, l = p.lang, el = document.getElementById('mnPlace'); if (!el) return;
    var 나말 = 나라말[p.country], 질문 = 나말 ? 곳('수준', l).replace('{말}', 말이름들[나말][칸(l)]) : 곳('수준일반', l);
    if (p.country && !나라이름[p.country]) p.country = 'XX';   /* 11-04b 목록 밖 나라(BR·VN 등)는 그 밖(국제 안내)으로 · 11-04h 빈칸('')은 아직 안 고름 */
    var 목 = 나라목록(); if (p.country && 목.indexOf(p.country) < 0) 목.unshift(p.country);
    el.innerHTML = '<div class="mnp-box" role="dialog" aria-modal="true" aria-labelledby="mnpT" lang="' + l + '">' +
      '<h2 id="mnpT">' + 곳('제목', l) + '</h2><p class="mnp-sub">' + 곳('설명', l) + '</p>' +
      '<label class="mnp-l" for="mnpLang">' + 곳('앱말', l) + '</label><select id="mnpLang" class="mnp-sel" onchange="설정판.말과나라고름(\'lang\',this.value)">' +
        말순.map(function (k) { return '<option value="' + k + '"' + (k === l ? ' selected' : '') + '>' + 말이름[k] + '</option>'; }).join('') + '</select>' +
      '<label class="mnp-l" for="mnpCountry">' + 곳('나라', l) + '</label><select id="mnpCountry" class="mnp-sel" onchange="설정판.말과나라고름(\'country\',this.value)">' + (p.country ? '' : '<option value="" selected disabled>' + 곳('나라고름', l) + '</option>') +
        목.map(function (k) { return '<option value="' + k + '"' + (k === p.country ? ' selected' : '') + '>' + 나라이름[k][칸(l)] + '</option>'; }).join('') + '</select>' +
      (p.country && 수준묻나(p) ? '<div class="ms-seg mnp-lv" role="group" aria-label="' + esc(질문) + '"><span class="ms-sl">' + 질문 + '</span><div class="ms-sb">' +
        곳('수준들', l).map(function (x, i) { var v = ['ok', 'some', 'none'][i], on = p.level === v; return '<button type="button" class="' + (on ? 'on' : '') + '" aria-pressed="' + on + '" onclick="설정판.말과나라고름(\'level\',\'' + v + '\')">' + x + '</button>'; }).join('') + '</div></div>' : '') +
      '<button type="button" class="mnp-ok" onclick="설정판.말과나라맞아요()"' + (!p.country || (수준묻나(p) && !p.level) ? ' disabled aria-disabled="true"' : '') + '>' + 곳('맞아요', l) + '</button></div>';
  }
  function 곳열기() {
    스타일(); 표합치기(); var 지금 = 곳읽기(), d = 곳기본();
    고르는중 = 지금 ? { lang: d.lang, country: 나라이름[지금.country] ? 지금.country : 'XX', level: 지금.level } : { lang: d.lang, country: d.country, level: '' };
    if (!수준묻나(고르는중)) 고르는중.level = 'ok'; else if (고르는중.level === 'ok' && !지금) 고르는중.level = '';
    var el = document.getElementById('mnPlace'); if (!el) { el = document.createElement('div'); el.id = 'mnPlace'; el.className = 'mnp'; document.body.appendChild(el); }
    곳그림(); try { el.querySelector('select').focus(); } catch (e) {}
  }
  function 곳맞아요() {
    var p = 고르는중; if (!p || !p.country) return; if (!수준묻나(p)) p.level = 'ok'; if (!p.level) return;
    var 옛 = 곳읽기(), 새 = { lang: p.lang, country: p.country, level: p.level, at: new Date().toISOString().slice(0, 10) };
    try { localStorage.setItem(곳열쇠, JSON.stringify(새)); } catch (e) {}
    var el = document.getElementById('mnPlace'); if (el) el.remove(); 고르는중 = null;
    try { window.dispatchEvent(new CustomEvent('mn:place', { detail: 새 })); } catch (e) {}
    var o = 설정.말과나라 || {}, 기 = 곳기본();
    try { if (typeof o.바꿈 === 'function') o.바꿈(새, 새.lang !== 말(), !옛 || 옛.country !== 새.country); } catch (e) {}
    다시();
  }
  /* 11-04g — 동의 전 첫 화면에서도 쓰는 «사는 나라 응급 번호» 한 곳(Main · CS·소아·약지도가 부른다)
     나라: ① mn.place.country(말과 나라에서 고른 값) ② 시간대·기기 지역 짐작 — 자동 시험(navigator.webdriver)이고 고른 값이 없으면 한국(곁에 약속)
     번호: 공용 위기번호 표(window.메디나눔위기번호 — 표가 앞에 심겨 있어야 한다). 표 밖·번호 null 이면 번호 없음 → 누르는 단추 없이 「현지 응급 번호」 글.
     설정판.응급번호() → { 나라, 이름, 응급, 경찰, 위기1, 위기2, 고름 }   (번호는 '119' 같은 글 또는 null · 고름: 사용자가 고른 나라인지)
     설정판.번호HTML('응급'|'경찰'|'위기1'|'위기2', 꾸밈) → 번호가 있으면 <a href="tel:…">번호</a>, 없으면 그 말의 「현지 응급 번호」 글(링크 없음) */
  var 현지 = { ko: '현지 응급 번호', en: 'the local emergency number', es: 'el número de emergencias local', ja: '現地の救急番号', zh: '当地急救电话' };
  function 응급번호() {
    var 곳 = 곳읽기(), c = 곳 && 곳.country, 고름 = !!c;
    if (!c) c = navigator.webdriver ? 'KR' : 나라짐작();
    var 표 = 공용표() || {}, N = 표[c] || 표.XX || {};
    if (!표[c]) c = 'XX';
    var 위 = (N.위기 || []).filter(Boolean), 응 = N.응급 || null;
    return { 나라: c, 이름: (N.이름 && (N.이름[말()] || N.이름.en)) || '', 응급: 응, 경찰: N.경찰 || 응, 위기1: 위[0] || 응, 위기2: 위[1] || 위[0] || 응, 고름: 고름 };
  }
  function 번호HTML(k, 꾸밈) {
    var n = 응급번호()[k || '응급'];
    if (!n) return '<span class="ms-local">' + 현지[말()] + '</span>';
    return '<a href="tel:' + esc(String(n).replace(/[^\d+]/g, '')) + '"' + (꾸밈 ? ' class="' + esc(꾸밈) + '"' : '') + '>' + esc(n) + '</a>';
  }
  function 곳줄() {
    var o = 설정.말과나라; if (!o) return ''; 표합치기(); var v = 곳읽기();
    var 값글 = v ? (나라이름[v.country] || 나라이름.XX)[칸(말())] + (v.level === 'ok' ? '' : ' · ' + 곳('수준들')[v.level === 'some' ? 1 : 2]) : 곳('안정함');
    return 줄('globe', 곳('줄'), 곳('줄설명'), 값글, '설정판.말과나라열기()');
  }
  function 다시() { try { if (typeof 설정.다시그리기 === 'function') 설정.다시그리기(); } catch (e) {} }
  var 스타일됨 = false;
  function 스타일() {
    if (스타일됨 || !document.head) return; 스타일됨 = true;
    var A = 'var(--ms-accent,var(--accent,currentColor))', L = 'var(--ms-line,var(--line,rgba(127,127,127,.28)))', D = 'var(--ms-dim,var(--ink2,inherit))', C = 'var(--ms-card,var(--card,transparent))';
    var st = document.createElement('style'); st.id = 'ms-style';
    st.textContent = '.ms{word-break:keep-all;overflow-wrap:anywhere}.ms-group{margin-top:18px}.ms-h,#msSettings h2.ms-h{font-size:.84em;font-weight:800;letter-spacing:.02em;line-height:1.4;font-family:inherit;text-transform:none;color:' + D + ';margin:0 4px 8px;padding:0;border:0;background:none}' +
      '.ms-segs{display:flex;flex-direction:column;gap:12px;margin-top:10px;padding:14px;border-radius:16px;background:' + C + ';border:1px solid ' + L + '}' +
      '.ms-sl{display:block;font-weight:700;margin-bottom:8px}.ms-sb{display:flex;flex-wrap:wrap;gap:6px}' +
      '.ms-sb button{flex:1 1 90px;min-height:48px;padding:6px 10px;border-radius:12px;border:1px solid ' + L + ';background:transparent;color:inherit;font:inherit;font-weight:600;cursor:pointer;line-height:1.25}' +
      '.ms-sb button.on{border:2px solid ' + A + ';color:' + A + ';font-weight:800}.ms-sb button[disabled]{opacity:.6;cursor:default}.ms-soon{display:inline-block;font-size:.78em;font-weight:700}' +
      '.ms-row{display:flex;gap:10px;align-items:center;width:100%;min-height:56px;padding:12px;border:0;border-bottom:1px solid ' + L + ';background:transparent;color:inherit;font:inherit;text-align:left;cursor:pointer}' +
      '.ms-rt{flex:1;min-width:0;display:flex;flex-direction:column}.ms-rt>span{font-size:.88em;color:' + D + '}.ms-rv{flex:none;font-size:.86em;color:' + A + ';font-weight:700}.ms-foot{margin-top:16px}' +
      '.mnp{position:fixed;inset:0;z-index:2147483000;background:var(--bg,#fff);color:var(--ink,inherit);overflow:auto;display:flex;justify-content:center;padding:max(24px,env(safe-area-inset-top)) 16px 32px;word-break:keep-all;overflow-wrap:anywhere}' +
      '.mnp-box{width:100%;max-width:480px;margin:auto 0}.mnp-box h2{margin:0 0 8px;font-size:1.35em;line-height:1.3}.mnp-sub{margin:0 0 18px;color:' + D + ';line-height:1.55}' +
      '.mnp-l{display:block;font-weight:700;margin:14px 0 6px}.mnp-sel{width:100%;min-height:52px;padding:10px 12px;border-radius:12px;border:1px solid ' + L + ';background:' + C + ';color:inherit;font:inherit;font-size:16px;max-width:100%}' +
      '.mnp-lv{margin-top:16px}.mnp-ok{display:block;width:100%;min-height:56px;margin-top:22px;border:0;border-radius:14px;background:' + A + ';color:var(--ms-on-accent,#fff);font:inherit;font-size:1.05em;font-weight:800;cursor:pointer}.mnp-ok[disabled]{opacity:.45;cursor:default}';
    document.head.appendChild(st);
  }
  window.설정판 = {
    __v: 판, 판: 판, HTML: HTML,
    설치: function (o) { o = o || {}; Object.keys(o).forEach(function (k) { 설정[k] = o[k]; }); return window.설정판; },
    글자: function (n) { try { 설정.글자.바꿈(n); } catch (e) {} 다시(); },
    밝기: function (i) { try { 설정.밝기.바꿈(밝기값[i] || 'light'); } catch (e) {} 다시(); },
    글: 글,
    말과나라: function () { return 곳읽기(); },
    말과나라열기: 곳열기, 말과나라맞아요: 곳맞아요,
    말과나라고름: function (k, v) { if (!고르는중) return; 고르는중[k] = v; if (k !== 'level') { if (!수준묻나(고르는중)) 고르는중.level = 'ok'; else if (고르는중.level === 'ok') 고르는중.level = ''; } 곳그림(); },
    말과나라확인: function () { if (곳읽기() || navigator.webdriver || document.getElementById('mnPlace')) return false; 곳열기(); return true; },
    나라이름: function (k, l) { 표합치기(); var n = 나라이름[k]; return n ? n[칸(l || 말())] : ''; },
    말이름: function (k, l) { var n = 말이름들[k]; return n ? n[칸(l || 말())] : ''; },
    응급번호: 응급번호, 번호HTML: 번호HTML, 나라짐작: 나라짐작
  };
})();
/* ▲▲ 설정 부품 끝 ▲▲ */
/* ▼▼ 응급카드 부품 시작 ▼▼ */
/* ═══ 응급 카드 — 그 나라 말이 서툰 분께 「119 에 이렇게 말하세요」 (2026-11-04 현욱님 「진행」 · 주인: 길동무 세션)
   요청서 docs/requests/20261104_언어나라_묻기.md 「차별점 — 응급 카드」
   보이는 때: 설정판.말과나라() 가 country 'KR' · level 'some'|'none' · lang 이 한국어가 아닐 때만. 그 밖에는 빈 글('').
   모양: 큰 한국어 문장(상대에게 보여 줘도 되게) + 그 아래 본인 말. 적어 둔 주소가 있으면 한 줄 더(주소는 이 기기 localStorage mn.addr 에만 — 서버로 보내지 않는다).
   통역 줄(11-04 Main 확인 · 설계안): 「119 에 통역을 부탁하세요」 · 1345 외국인종합안내센터(법무부 — 생활·행정 도움, 평일 09:00~22:00 · 20개 말 · 18시 뒤 한·영·중 · immigration.go.kr/immigration/1530/subview.do)
     · 11-05 확정: 1345 영·중 「평일 9~22시」 · 스·일 「평일 9~18시」(18시 뒤는 한·영·중만) · 1330 관광 통역(시간은 적지 않음 — 출처가 갈림 · 통역 도움으로만, 119 연결을 약속하지 않는다). 1577-0071 은 넣지 않는다. 앱이 통역줄로 바꿀 수 있다.
   내 말 카드: 기기 말이 다섯 말 밖(vi·th·tl·id·ne·uz·km·mn·ru·my)이면 #mn-ecard 맨 위에 그 말로(응급카드.내말카드HTML() 로 따로도).
   쓰는 법: 화면에 <div id="mn-ecard"></div> 자리만 두면 부품이 채운다(응급카드.채우기() · mn:place 이벤트 · 자리가 새로 그려지면 스스로).
            문자열이 필요하면 응급카드.HTML(). 「주소 적어 두기」는 카드 안에서 바로.
   ⛔ 이모지 0 · « » 0 · 단추 44px 이상 · 320 넘침 0.
   ── 공용 부품 셋(위기번호 표 · 설정 부품 · 응급카드 부품) 공통 약속 · 주인: 길동무 세션 ──
   판: 이 파일 안 «판» 한 곳(코드의 판 값). 고치면 판을 올리고 다섯 앱에 다시 심는다. 지금 판 2026-11-05b.
   심는 순서(앱마다 같다): ① 위기번호 표 → ② 설정 부품 → ③ 응급카드 부품 — 표가 앞에 있어야 말과 나라 고르개·응급 번호가 표를 쓴다.
   심기·비교: python3 _도구/공용부품_심기.py 비교 · python3 _도구/공용부품_심기.py <소아|곁에|길동무|CS> · 다른 저장소(약지도): python3 _도구/공용부품_심기.py 파일 <경로>
   ⛔ 앱 사본을 직접 고치지 않는다 — 이 파일을 고치고 다시 심는다(심기 스크립트는 정본과 다른 사본을 보면 멈춘다).
*/
(function () {
  if (window.응급카드 && window.응급카드.__v) return;
  var 판 = '2026-11-05b', 주소열쇠 = 'mn.addr';   /* 11-05b 1345 시간 말별·1330 시간 뺌 · 11-05a 내 말 응급 카드(10개 말) 합침 · 11-04b 머리 주석 정리 · 11-04 첫 판은 통역 줄 없음 */
  var 기본통역줄 = [
    { 번호: '119', 말: { en: 'Ask 119 for an interpreter.', es: 'Pida un intérprete al 119.', ja: '119に通訳をお願いしてください。', zh: '请向119要求翻译服务。' } },
    { 번호: '1345', 말: { en: 'Immigration Contact Center (Ministry of Justice) — help with daily life and paperwork, not emergencies. In English on weekdays 09:00–22:00. From abroad +82-2-1345.',
      es: 'Centro de Atención a Extranjeros (Ministerio de Justicia): ayuda con la vida diaria y los trámites, no con emergencias. En español, de lunes a viernes de 09:00 a 18:00. Desde el extranjero +82-2-1345.',
      ja: '外国人総合案内センター（法務部）— 生活や手続きの相談（緊急ではないとき）。日本語は平日09:00〜18:00。海外から+82-2-1345。',
      zh: '外国人综合咨询中心（法务部）——生活和行政事务咨询（非紧急情况）。中文服务工作日09:00～22:00。从海外拨打+82-2-1345。' } },
    { 번호: '1330', 말: { en: 'Korea Travel Hotline — interpretation help in English, Japanese and Chinese.', es: 'Línea de turismo de Corea: ayuda con la interpretación en inglés, japonés y chino.',
      ja: '観光通訳案内 — 英語・日本語・中国語で通訳の手助けをします。', zh: '旅游咨询热线——提供英语、日语、中文口译帮助。' } } ];
  var 설정 = { 통역줄: 기본통역줄 };
  var 말이름ko = { en: '영어', es: '스페인어', ja: '일본어', zh: '중국어' };
  var 글표 = {
    en: { 머리: 'Say this to 119, or show them this screen', 나: 'I am a foreigner. I do not speak Korean well. I need an English interpreter.', 주소: 'Address', 적기: 'Save your address', 고치기: 'Change address', 저장: 'Save', 칸: 'Address in Korea (e.g. street, building, unit)' },
    es: { 머리: 'Diga esto al 119 o muestre esta pantalla', 나: 'Soy extranjero o extranjera. No hablo bien coreano. Necesito un intérprete de español.', 주소: 'Dirección', 적기: 'Guardar mi dirección', 고치기: 'Cambiar la dirección', 저장: 'Guardar', 칸: 'Dirección en Corea (calle, edificio, piso)' },
    ja: { 머리: '119にはこう伝えてください（この画面を見せても大丈夫です）', 나: '外国人です。韓国語があまり話せません。日本語の通訳が必要です。', 주소: '住所', 적기: '住所を書いておく', 고치기: '住所を直す', 저장: '保存', 칸: '韓国の住所（通り・建物・部屋番号）' },
    zh: { 머리: '请这样告诉119，或把这个画面给对方看', 나: '我是外国人。我韩语说得不好。我需要中文翻译。', 주소: '地址', 적기: '记下我的地址', 고치기: '修改地址', 저장: '保存', 칸: '在韩国的地址（街道、楼名、房间号）' }
  };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function 곳() { try { return window.설정판 && 설정판.말과나라 ? 설정판.말과나라() : null; } catch (e) { return null; } }
  function 주소() { try { return String(localStorage.getItem(주소열쇠) || '').trim(); } catch (e) { return ''; } }
  function 보일까() { var p = 곳(); return !!(p && p.country === 'KR' && (p.level === 'some' || p.level === 'none') && 글표[p.lang]); }
  var 스타일됨 = false;
  function 스타일() {
    if (스타일됨 || !document.head) return; 스타일됨 = true;
    var st = document.createElement('style'); st.id = 'ec-style';
    st.textContent = '.ec:first-child{margin-top:34px}.ec{margin:0 0 16px;padding:16px;border-radius:16px;border:2px solid var(--ec-line,var(--warn,#b3261e));background:var(--ec-bg,var(--card,transparent));word-break:keep-all;overflow-wrap:anywhere}' +
      '.ec-h{margin:0 0 10px;font-size:.92em;font-weight:800;color:var(--ec-line,var(--warn,#b3261e))}.ec-ko{margin:0;font-size:1.32em;font-weight:800;line-height:1.5}' +
      '.ec-me{margin:8px 0 0;line-height:1.55;color:var(--ink2,inherit)}.ec-addr{margin:12px 0 0;padding-top:10px;border-top:1px solid var(--line,rgba(127,127,127,.28))}' +
      '.ec-addr .ec-ko{font-size:1.18em}.ec-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.ec-btn{min-height:48px;padding:8px 14px;border-radius:12px;border:1px solid var(--line,rgba(127,127,127,.4));background:transparent;color:inherit;font:inherit;font-weight:700;cursor:pointer}' +
      '.ec-in{flex:1 1 200px;min-width:0;min-height:48px;padding:8px 12px;border-radius:12px;border:1px solid var(--line,rgba(127,127,127,.4));background:transparent;color:inherit;font:inherit;font-size:16px}' +
      '.ec-tl{margin:10px 0 0;font-size:.95em}.ec-tl a{font-weight:800}' +
      '.mnl-card{margin:0 0 14px;padding:14px 16px;border-radius:16px;border:1px solid var(--ec-line,var(--warn,#b3261e));background:var(--ec-bg,var(--card,transparent));line-height:1.55;word-break:keep-all;overflow-wrap:anywhere}.mnl-card p{margin:0 0 8px}.mnl-t{font-weight:800}' +
      '.mnl-r{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px}.mnl-card a.mnl-b{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:999px;background:var(--ec-line,var(--warn,#b3261e));color:#fff;font-weight:700;text-decoration:none}';
    document.head.appendChild(st);
  }
  function HTML() {
    if (!보일까()) return '';
    스타일();
    var p = 곳(), l = p.lang, t = 글표[l], a = 주소();
    var h = '<section class="ec" id="ecCard" aria-label="' + esc(t.머리) + '"><p class="ec-h">' + esc(t.머리) + '</p>' +
      '<p class="ec-ko" lang="ko" translate="no">외국인입니다. 한국어를 잘 못해요. ' + 말이름ko[l] + ' 통역이 필요해요.</p>' +
      '<p class="ec-me" lang="' + l + '">' + esc(t.나) + '</p>';
    if (a) h += '<div class="ec-addr"><p class="ec-ko" lang="ko" translate="no">주소: ' + esc(a) + '</p><p class="ec-me" lang="' + l + '">' + esc(t.주소) + ': ' + esc(a) + '</p></div>';
    (설정.통역줄 || []).forEach(function (x) {   /* Main 이 공식 확인한 번호만 */
      if (!x || !x.번호) return;
      h += '<p class="ec-tl"><a href="tel:' + esc(String(x.번호).replace(/[^\d+]/g, '')) + '">' + esc(x.번호) + '</a> ' + esc((x.말 && x.말[l]) || '') + '</p>';
    });
    h += '<div class="ec-row" id="ecAddrRow"><button type="button" class="ec-btn" onclick="응급카드.주소열기()">' + esc(a ? t.고치기 : t.적기) + '</button></div></section>';
    return h;
  }

  /* ── 내 말 응급 카드(11-05 현욱님 「베트남인이 한국에 살면 베트남어로 한국 응급번호」 · 곁에에서 가져와 합침) ──
     화면 말(다섯 말) 밖의 말을 쓰는 분 — 기기 언어(navigator.languages)로 판정 — 께 그 말로 짧은 카드. 번호는 사는 나라(설정판.응급번호()) 기준.
     한국: 119 구급·112 경찰 · 109 자살예방 24시간(한국어 — 외국어 통역은 확인 못 함, 그렇게 적음) · 1345 외국인종합안내(이 말이 목록에 있을 때만) · 1330 관광통역안내.
     1345 시간(11-05 확정 · 법무부 immigration.go.kr/immigration/1530): 평일 09:00~22:00, 단 18시 뒤는 한·영·중만 → 이 10개 말은 「평일 9~18시」(w).
     1330: 출처가 갈려(질병관리청 07~24시 · 지자체 08~19시) 시간은 적지 않고 번호만 — h 는 「1330 이 이 말을 하는지」 표시로만 쓴다. 글은 언어층이 건드리지 않게 data-raw. */
  var 내말표 = {
    vi: { n: 'Tiếng Việt', t: 'Trợ giúp khẩn cấp bằng tiếng Việt', d: 'Nếu đang gặp nguy hiểm, hãy gọi ngay', a: 'cấp cứu', p: 'cảnh sát', s: 'Muốn nói chuyện khi lòng nặng nề', k: '24 giờ, tiếng Hàn', m: 'Hỗ trợ bằng tiếng Việt', w: 'ngày thường 9–18 giờ', h: '7–24 giờ', l: 'Hãy gọi số khẩn cấp của nơi bạn đang sống.', c: 'Gọi' },
    th: { n: 'ภาษาไทย', t: 'ความช่วยเหลือฉุกเฉินเป็นภาษาไทย', d: 'ถ้ากำลังอยู่ในอันตราย โทรทันที', a: 'รถพยาบาล', p: 'ตำรวจ', s: 'อยากคุยกับใครสักคนเมื่อใจหนักอึ้ง', k: '24 ชั่วโมง ภาษาเกาหลี', m: 'ความช่วยเหลือเป็นภาษาไทย', w: 'วันธรรมดา 9–18 น.', h: '7–24 น.', l: 'โทรหมายเลขฉุกเฉินของประเทศที่คุณอาศัยอยู่', c: 'โทร' },
    tl: { n: 'Filipino', t: 'Tulong pang-emergency sa Filipino', d: 'Kung nasa panganib ka ngayon, tumawag agad', a: 'ambulansya', p: 'pulis', s: 'Kung gusto mong may makausap kapag mabigat ang loob mo', k: '24 oras, sa wikang Korean', m: 'Tulong sa wikang Filipino', w: 'Lunes–Biyernes 9–18', h: '7–24', l: 'Tumawag sa emergency number ng bansang tinitirhan mo.', c: 'Tawagan' },
    id: { n: 'Bahasa Indonesia', t: 'Bantuan darurat dalam bahasa Indonesia', d: 'Jika sedang dalam bahaya, segera telepon', a: 'ambulans', p: 'polisi', s: 'Ingin bicara saat hati terasa berat', k: '24 jam, bahasa Korea', m: 'Bantuan dalam bahasa Indonesia', w: 'hari kerja 09.00–18.00', h: '07.00–24.00', l: 'Telepon nomor darurat di negara tempat Anda tinggal.', c: 'Telepon' },
    ne: { n: 'नेपाली', t: 'नेपालीमा आपतकालीन सहायता', d: 'अहिले खतरामा हुनुहुन्छ भने तुरुन्तै फोन गर्नुहोस्', a: 'एम्बुलेन्स', p: 'प्रहरी', s: 'मन भारी हुँदा कसैसँग कुरा गर्न', k: '24 घण्टा, कोरियाली भाषामा', m: 'नेपाली भाषामा सहायता', w: 'सोमबार–शुक्रबार 9–18 बजे', h: '', l: 'तपाईं बस्ने देशको आपतकालीन नम्बरमा फोन गर्नुहोस्।', c: 'फोन' },
    uz: { n: 'Oʻzbekcha', t: 'Oʻzbek tilida favqulodda yordam', d: 'Hozir xavf ostida boʻlsangiz, darhol qoʻngʻiroq qiling', a: 'tez yordam', p: 'politsiya', s: 'Koʻnglingiz ogʻir boʻlsa, gaplashish uchun', k: '24 soat, koreys tilida', m: '', w: '', h: '', l: 'Yashayotgan mamlakatingizdagi favqulodda raqamga qoʻngʻiroq qiling.', c: 'Qoʻngʻiroq' },
    km: { n: 'ខ្មែរ', t: 'ជំនួយបន្ទាន់ជាភាសាខ្មែរ', d: 'បើកំពុងមានគ្រោះថ្នាក់ សូមទូរសព្ទភ្លាម', a: 'រថយន្តសង្គ្រោះ', p: 'ប៉ូលិស', s: 'ចង់និយាយជាមួយនរណាម្នាក់ពេលចិត្តធ្ងន់', k: '24 ម៉ោង ភាសាកូរ៉េ', m: 'ជំនួយជាភាសាខ្មែរ', w: 'ថ្ងៃធ្វើការ 9–18 ម៉ោង', h: '', l: 'សូមទូរសព្ទទៅលេខបន្ទាន់នៃប្រទេសដែលអ្នករស់នៅ។', c: 'ទូរសព្ទ' },
    mn: { n: 'Монгол', t: 'Монгол хэлээр яаралтай тусламж', d: 'Одоо аюулд байгаа бол шууд залгаарай', a: 'түргэн тусламж', p: 'цагдаа', s: 'Сэтгэл хүнд үед хэн нэгэнтэй ярилцмаар байвал', k: '24 цаг, солонгос хэлээр', m: 'Монгол хэлээр тусламж', w: 'ажлын өдөр 9–18 цаг', h: '', l: 'Амьдарч буй улсынхаа яаралтай дугаарт залгаарай.', c: 'Залгах' },
    ru: { n: 'Русский', t: 'Экстренная помощь на русском', d: 'Если вы в опасности, звоните сразу', a: 'скорая', p: 'полиция', s: 'Если тяжело на душе и хочется поговорить', k: 'круглосуточно, на корейском', m: 'Помощь на русском', w: 'будни 9–18', h: '7–24', l: 'Позвоните по экстренному номеру страны, где вы живёте.', c: 'Позвонить' },
    my: { n: 'မြန်မာ', t: 'မြန်မာဘာသာဖြင့် အရေးပေါ်အကူအညီ', d: 'အခု အန္တရာယ်ရှိနေရင် ချက်ချင်း ဖုန်းဆက်ပါ', a: 'လူနာတင်ယာဉ်', p: 'ရဲ', s: 'စိတ်လေးလံနေချိန် တစ်ယောက်ယောက်နဲ့ စကားပြောချင်ရင်', k: '24 နာရီ၊ ကိုရီးယားဘာသာ', m: 'မြန်မာဘာသာဖြင့် အကူအညီ', w: 'ရုံးဖွင့်ရက် 9–18 နာရီ', h: '', l: 'သင်နေထိုင်ရာ နိုင်ငံ၏ အရေးပေါ်နံပါတ်ကို ဖုန်းဆက်ပါ။', c: 'ဖုန်းဆက်' }
  };
  function 내말() {
    try {
      var 화면 = (곳() || {}).lang || String(document.documentElement.lang || 'ko').slice(0, 2);
      var L = 설정.기기말 || (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || '']);
      for (var i = 0; i < L.length; i++) { var c = String(L[i] || '').toLowerCase().split('-')[0]; if (c === 'fil') c = 'tl'; if (c === 'ms') c = 'id';
        if (['ko', 'en', 'es', 'ja', 'zh'].indexOf(c) >= 0) return null; if (내말표[c] && c !== 화면) return c; }
    } catch (e) {}
    return null;
  }
  function 내말단추(n, 이름, c) { var d = String(n).replace(/[^\d]/g, ''); return '<a class="mnl-b" href="tel:' + d + '">' + esc(c + ' ' + n + (이름 ? ' · ' + 이름 : '')) + '</a>'; }
  function 내말카드HTML() {
    var c = 내말(); if (!c) return '';
    스타일();
    var M = 내말표[c], 번 = {}; try { 번 = window.설정판 && 설정판.응급번호 ? 설정판.응급번호() : {}; } catch (e) {}
    var 나라 = 번.나라 || 'KR', 안 = '<p class="mnl-t">' + esc(M.t) + '</p>';
    if (나라 === 'KR') {
      안 += '<p>' + esc(M.d) + '</p><div class="mnl-r">' + 내말단추('119', M.a, M.c) + 내말단추('112', M.p, M.c) + '</div>' +
        '<p>' + esc(M.s) + ' — 109 (' + esc(M.k) + ')</p><div class="mnl-r">' + 내말단추('109', '', M.c) + '</div>';
      if (M.m) 안 += '<p>' + esc(M.m) + ': 1345 (' + esc(M.w) + ')' + (M.h ? ' · 1330' : '') + '</p><div class="mnl-r">' + 내말단추('1345', '', M.c) + (M.h ? 내말단추('1330', '', M.c) : '') + '</div>';
    } else if (번.응급) {
      안 += '<p>' + esc(M.d) + '</p><div class="mnl-r">' + 내말단추(번.응급, M.a, M.c) + (번.위기1 && 번.위기1 !== 번.응급 ? 내말단추(번.위기1, '', M.c) : '') + '</div>';
    } else { 안 += '<p>' + esc(M.l) + '</p>'; }
    return '<div class="mnl-card" data-raw="1" translate="no" lang="' + c + '" role="region" aria-label="' + esc(M.t) + '">' + 안 + '</div>';
  }
  function 주소열기() {
    var p = 곳(), t = p && 글표[p.lang], r = document.getElementById('ecAddrRow'); if (!t || !r) return;
    r.innerHTML = '<input id="ecAddrIn" class="ec-in" type="text" autocomplete="street-address" aria-label="' + esc(t.칸) + '" placeholder="' + esc(t.칸) + '" value="' + esc(주소()) + '">' +
      '<button type="button" class="ec-btn" onclick="응급카드.주소저장()">' + esc(t.저장) + '</button>';
    try { document.getElementById('ecAddrIn').focus(); } catch (e) {}
  }
  function 주소저장() {
    var i = document.getElementById('ecAddrIn'), v = i ? String(i.value || '').trim().slice(0, 200) : '';
    try { if (v) localStorage.setItem(주소열쇠, v); else localStorage.removeItem(주소열쇠); } catch (e) {}
    var 자 = document.getElementById('mn-ecard'); if (자 && 자.contains(document.getElementById('ecCard'))) { 자.removeAttribute('data-ec'); 채우기(); return; }
    var c = document.getElementById('ecCard'); if (c) { var d = document.createElement('div'); d.innerHTML = HTML(); if (d.firstChild) c.parentNode.replaceChild(d.firstChild, c); else c.remove(); }
  }
  function 채우기() {
    var el = document.getElementById('mn-ecard'); if (!el) return false;
    var h = 내말카드HTML() + HTML(); if (el.getAttribute('data-ec') === h) return true;   /* 11-05 내 말 카드가 맨 위 */
    el.innerHTML = h; el.setAttribute('data-ec', h); return true;
  }
  try { window.addEventListener('mn:place', 채우기); } catch (e) {}
  try { var 예약 = 0; new MutationObserver(function () { var el = document.getElementById('mn-ecard'); if (el && !el.hasAttribute('data-ec')) { clearTimeout(예약); 예약 = setTimeout(채우기, 0); } })
    .observe(document.documentElement, { childList: true, subtree: true }); } catch (e) {}
  window.응급카드 = { __v: 판, 판: 판, HTML: HTML, 채우기: 채우기, 내말카드HTML: 내말카드HTML, 내말: 내말, 내말표: 내말표, 보일까: 보일까, 주소열기: 주소열기, 주소저장: 주소저장, 주소: 주소,
    설치: function (o) { o = o || {}; Object.keys(o).forEach(function (k) { 설정[k] = o[k]; }); return window.응급카드; } };
})();
/* ▲▲ 응급카드 부품 끝 ▲▲ */

/* 11-04 현욱님 「쓰는 말 · 사는 나라 · 그 나라 말」(요청서 yozm-health docs/requests/20261104_언어나라_묻기.md) — 공용 부품(길동무 정본 _도구/설정_부품.js·응급카드_부품.js)을 그대로 심음.
   약지도는 출처가 따로라 같은 열쇠(mn.place)·같은 모양으로 이 안에 저장한다. 나라는 app-shell CC 가 mn.place.country 를 먼저 본다(응급 번호·약 이름 나라 한 곳).
   고르개: 약지도 표(KR·US·ES·JP·CN) + 공용 위기번호 표 나라. 표에 없는 나라는 번호 없음(누르는 단추 없이 「그 나라 응급 번호」). */
try {
  설정판.설치({ app: 'yakjido', 언어: () => window.LANG || 'ko', 말과나라: {
    기본: () => ({ lang: window.LANG || 'ko', country: window.CC || 'KR' }),
    나라들: ['KR', 'US', 'ES', 'JP', 'CN', 'MX', 'HK', 'VN', 'TH', 'PH', 'ID', 'NP', 'UZ', 'KH', 'MN', 'LK', 'BD', 'IN', 'GB', 'XX'],
    바꿈: (v) => { if (v && (v.lang !== window.LANG || v.country !== window.CC)) { try { localStorage.setItem('yakjido.lang', v.lang); localStorage.setItem('yakjido.cc', v.country); } catch (e) {} location.reload(); } else route(); } } });
  응급카드.설치({ 통역줄: [
    { 번호: '119', 말: { en: 'Ask 119 for an interpreter.', es: 'Pida al 119 un intérprete.', ja: '119に通訳を頼んでください。', zh: '请向119要求翻译。' } },
    { 번호: '1345', 말: { en: 'Immigration Contact Center (Ministry of Justice) — weekdays 09:00~22:00, 20 languages (after 18:00 only Korean, English and Chinese). For daily-life and admin help, not emergencies.',
      es: 'Centro de Atención a Extranjeros (Ministerio de Justicia): días laborables 09:00~22:00, 20 idiomas (después de las 18:00 solo coreano, inglés y chino). Ayuda para la vida diaria y trámites, no para urgencias.',
      ja: '外国人総合案内センター（法務部）— 平日 09:00~22:00・20の言葉（18時以降は韓国語・英語・中国語のみ）。救急ではなく生活・行政の手助けです。',
      zh: '外国人综合咨询中心（法务部）——工作日 09:00~22:00，20种语言（18点以后只有韩语·英语·中文）。用于生活·行政帮助，不用于急救。' } } ] });
} catch (e) {}
window.응급칸 = () => (window.응급카드 ? 응급카드.HTML() : '');
try { const st = document.createElement('style'); st.textContent = 'html .ec .ec-ko{word-break:keep-all!important;overflow-wrap:break-word!important}'; document.head.appendChild(st); } catch (e) {}   /* 일본어·중국어 화면의 글자 단위 줄바꿈이 한국어 문장까지 자르지 않게 */
/* 옛 설정의 언어·나라 단추(setLang)도 같은 값(mn.place)을 고치게 */
(() => { const 원 = window.setLang; if (typeof 원 !== 'function') return;
  window.setLang = (l, cc) => { try { const p = JSON.parse(localStorage.getItem('mn.place') || 'null'); if (p) localStorage.setItem('mn.place', JSON.stringify(Object.assign(p, { lang: l, country: cc || p.country, at: new Date().toISOString() }))); } catch (e) {} 원(l, cc); }; })();
window.addEventListener('mn:place', () => { try { route(); } catch (e) {} });
/* 첫 실행 — 동의를 마친 뒤 홈에 오면 한 번(값이 있으면 열지 않음 · 자동 시험에서는 열지 않음) */
const 곳확인 = () => { try { if (consentRec() && /^#\/(home)?$|^$/.test(location.hash || '')) 설정판.말과나라확인(); } catch (e) {} };
window.addEventListener('hashchange', () => setTimeout(곳확인, 300)); setTimeout(곳확인, 900);

/* 11-04 현욱님 「압도적 매력」 ② 약국 앞 한 장 — 묻고 싶은 것 한 줄(이 기기에만). 카드 안은 약사에게 보이는 말(한국에 사는 외국어 사용자는 카드가 한국어로 남고 사용자 말 풀이를 아래에) */
const ASK_KEY = 'yakjido.ask';
window.물을말 = () => { let v = ''; try { v = localStorage.getItem(ASK_KEY) || ''; } catch (e) {}
  const ko = (window.LANG || 'ko') !== 'ko' && window.CC === 'KR';
  const 풀이 = { en: 'This card stays in Korean so the pharmacist can read it.', es: 'Esta tarjeta se queda en coreano para que la lea el farmacéutico.', ja: 'このカードは薬剤師が読めるよう韓国語のままです。', zh: '这张卡片保留韩语，方便药剂师阅读。' }[window.LANG];
  return `<div class="show-q"><p class="show-ask"><b>물어보고 싶은 것</b>${v ? '<br>' + esc(v) : ''}</p>
    <div data-noko>${ko && 풀이 ? `<p class="small muted" lang="${window.LANG}">${esc(풀이)}</p>` : ''}<label class="small" for="askIn" style="display:block;margin-top:8px">약사님께 묻고 싶은 것 한 줄 <small class="muted">선택 · 이 휴대폰에만</small></label>
    <input id="askIn" maxlength="120" value="${esc(v)}" placeholder="예) 졸리지 않은 약으로 주세요" style="width:100%;min-height:48px;margin-top:4px" onchange="물을말저장(this.value)"></div></div>`; };
window.물을말저장 = v => { try { v = String(v || '').replace(/[<>]/g, '').trim().slice(0, 120); if (v) localStorage.setItem(ASK_KEY, v); else localStorage.removeItem(ASK_KEY); } catch (e) {} route(); };

/* 11-04 「압도적 매력」 ① 약 이름 몰라도 등록 — 알약 찾기(각인·모양·색 → 식약처 사진)로 담은 뒤, 약이 둘 이상이면 바로 「겹치는지 보기」 */
['togglePub', 'addPubIx'].forEach(fn => { const 원 = window[fn]; if (typeof 원 !== 'function') return;
  window[fn] = async (...a) => { const 전 = (ME.taking || []).length; const r = await 원(...a); const 후 = (ME.taking || []).length;
    if (후 > 전 && 후 >= 2) setTimeout(() => { if (!/^#\/(pill|pub|photo|drugs|search)/.test(location.hash) || document.getElementById('mixNudge')) return;
      const v = document.getElementById('view'); if (!v) return; const d = document.createElement('div'); d.id = 'mixNudge'; d.className = 'note'; d.style.margin = '12px 0';
      d.innerHTML = `${I.shield}<span>내 약통에 담았어요. 지금 드시는 약 ${후}가지가 서로 겹치거나 부딪히지 않는지 바로 볼 수 있어요. <button type="button" class="link" style="min-height:44px" onclick="go('/together')">겹치는지 보기</button><br><small class="muted">사진과 각인이 확실하지 않으면 약 봉투나 약국에서 확인하세요.</small></span>`;
      v.prepend(d); try { if (window.I18N && I18N.tr) I18N.tr(d); } catch (e) {} }, 400);
    return r; }; });

/* 11-04 현욱님 「매일 돌아올 이유」 — 이번 주 지킴 막대(진짜 기록 dayStat · 코드로 그림) + 7일·14일·30일 이어질 때 조용한 한 줄.
   막대: 다 챙긴 날 가득 · 일부 반 · 빠진 날 빈 칸 · 정해 둔 약이 없던 날 점선. 숫자는 「7일 중 N일」(자연빈도). */
window.주간칸 = () => { try {
  const W = '일월화수목금토', days = [];
  for (let i = 6; i >= 0; i--) { const k = dayBefore(i), st = dayStat(k), d = new Date(k + 'T12:00:00'); days.push({ k, s: st.s, w: W[d.getDay()], today: i === 0 }); }
  const plan = days.filter(x => x.s !== 'none'); if (plan.length < 2) return '';   /* 기록이 쌓이기 전엔 보이지 않게 */
  const full = days.filter(x => x.s === 'full' || x.s === 'skip').length, stk = streakDays();
  const h = s => s === 'full' || s === 'skip' ? 100 : s === 'part' ? 50 : s === 'miss' ? 8 : 0;
  const bar = x => `<span class="wk-d${x.today ? ' now' : ''}" role="img" aria-label="${x.w}요일 ${x.s === 'full' || x.s === 'skip' ? '다 챙김' : x.s === 'part' ? '일부' : x.s === 'miss' ? '못 챙김' : '정해 둔 약 없음'}"><i class="wk-b ${x.s}" style="height:${Math.max(h(x.s), 8)}%"></i><small>${x.w}</small></span>`;
  const 축 = stk >= 7 && [7, 14, 21, 30, 60, 90, 180, 365].includes(stk) ? `<p class="wk-cele">${stk === 7 ? '일주일' : stk + '일'}을 채우셨어요 · 꾸준함이 약효를 지켜요</p>` : '';
  return `<div class="wk"><div class="wk-t"><b>이번 주</b><small>7일 중 ${full}일 다 챙김</small></div><div class="wk-bars">${days.map(bar).join('')}</div>${축}</div>`;
} catch (e) { return ''; } };
try { const st = document.createElement('style'); st.textContent = '.wk{padding:12px 16px 14px;border-top:1px solid var(--hairline)}.wk-t{display:flex;justify-content:space-between;align-items:baseline;gap:8px}.wk-t small{color:var(--muted)}.wk-bars{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-top:8px;height:64px}.wk-d{display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:4px;min-width:0}.wk-d small{font-size:.75rem;color:var(--muted)}.wk-d.now small{color:var(--primary);font-weight:700}.wk-b{display:block;width:100%;max-width:28px;border-radius:6px 6px 3px 3px;background:var(--primary)}.wk-b.part{background:var(--caution)}.wk-b.miss{background:var(--hairline)}.wk-b.none{background:transparent;border:1px dashed var(--hairline);height:8px!important}.wk-cele{margin-top:8px;font-size:.875rem;color:var(--primary-deep)}'; document.head.appendChild(st); } catch (e) {}

/* ▼▼ 가족대화 부품 시작 ▼▼ */
/* ═══ 가족 대화 — 이미 이어진 가족(약지도 yak_family_links · 소아 care_links)끼리 짧은 글 (2026-11-04 현욱님 「완벽하게 다듬어」 · 주인: 길동무 세션)
   설계 docs/requests/20261104_가족대화.md — 90일 지난 글은 서버가 지움 · 소아는 보호자끼리 먼저(학생은 2단계).
   서버 함수(Main): mn_chat_enable(p_app) · mn_chat_disable(p_app) · mn_chat_send(p_app, p_link, p_body, p_kind 'text'|'quick'|'card') → id
                    mn_chat_list(p_app, p_link, p_before(지금 보이는 가장 작은 id · 처음은 null), p_limit) → [{id, mine, kind, body, created_at}] 최신부터 · mn_chat_rooms(p_app) → [{link_id, other_on, last_at, unread}]
   서버 오류 글: 'login required' → 로그인 안내 · 'chat off' → 동의 한 장 · 'not allowed' → 「연결이 끝난 대화예요」 · 'too many'(시간당 60개) → 「잠시 뒤에 보내 주세요」
   쓰는 법(앱 끝, 서버 부품 뒤):
     가족대화.설치({ app:'yakjido'|'kids', 준비: function(){ return 서버.준비() },          // supabase 손잡이(로그인 세션이 붙은 것)를 주는 Promise
       로그인됨: function(){ return !!서버.세션() }, 말: function(){ return 'ko' },          // ko·en·es·ja·zh
       이름: function(link_id){ return '아빠' },                                            // 방 이름(상대) — 앱이 안다
       칩: null })                                                                          // 없으면 앱별 기본 빠른 말(다섯 말). 앱이 주면 [{ko,en,es,ja,zh}] 또는 ['…'] · {시각} 은 지금 HH:MM
     가족대화.열기()             — 첫 화면(처음이면 동의 한 장 → 방 목록) · 가족대화.방열기(link_id) — 바로 그 방
     가족대화.카드보내기(link_id, 글) — 앱이 자동으로 붙이는 한 줄(「08:02 아침 약 먹었어요」) · 켜 둔 분만 보낸다(꺼져 있으면 아무것도 안 함)
     가족대화.안읽음() → Promise<수>  — 입구 단추의 숫자 · 가족대화.켜짐() → true|false
   ⛔ 글·이름은 textContent 로만 넣는다(innerHTML 금지 — 남이 쓴 글이다) · 이모지 0 · « » 0 · 단추 44px 이상 · 320 넘침 0 · 열려 있을 때만 15초마다 새로 받는다.
   ── 공용 부품 공통 약속 ── 판: 코드의 판 한 곳 · 심기·비교: python3 _도구/공용부품_심기.py · 앱 사본을 직접 고치지 않는다. */
(function () {
  if (window.가족대화 && window.가족대화.__v) return;
  var 판 = '2026-11-04b', 설정 = { app: 'app', 준비: null, 로그인됨: null, 말: null, 이름: null, 칩: null }, 최대 = 500, 주기 = 15000;
  var 말순 = ['ko', 'en', 'es', 'ja', 'zh'];
  var 글표 = {
    ko: { 제목: '가족 대화', 닫기: '닫기', 뒤로: '방 목록', 동의제목: '가족 대화를 켤까요?',
      동의: ['보낸 글은 이어진 가족에게 전하려고 서버에 저장돼요.', '90일이 지난 글은 자동으로 지워져요.', '대화를 끄면 내가 보낸 글은 바로 지워져요.', '건강 이야기가 섞일 수 있어요. 꼭 필요한 것만 적어 주세요.'],
      켜기: '동의하고 켜기', 나중: '나중에', 방들: '대화할 가족', 방없음: '아직 이어진 가족이 없어요. 가족 연결에서 먼저 이어 주세요.', 새글: '새 글 {n}', 상대꺼짐: '상대가 아직 대화를 켜지 않았어요',
      빈방: '아직 주고받은 글이 없어요. 아래 빠른 말로 시작해 보세요.', 쓰기: '글 쓰기', 보내기: '보내기', 실패: '보내지 못했어요', 다시: '다시', 더보기: '이전 글 더 보기',
      끄기: '대화 끄기', 끄기확인: '끄면 내가 보낸 글이 지워져요. 다시 누르면 꺼요.', 로그인: '로그인한 뒤에 쓸 수 있어요.', 안됨: '지금은 대화를 불러오지 못했어요. 잠시 뒤 다시 해 주세요.', 나: '나', 빠른말: '빠른 말', 연결끝: '연결이 끝난 대화예요. 새 글은 보낼 수 없어요.', 많음: '잠시 뒤에 보내 주세요' },
    en: { 제목: 'Family chat', 닫기: 'Close', 뒤로: 'Chats', 동의제목: 'Turn on family chat?',
      동의: ['Messages you send are stored on our server so they can reach your linked family.', 'Messages older than 90 days are deleted automatically.', 'If you turn chat off, the messages you sent are deleted right away.', 'Health details may come up — please share only what is needed.'],
      켜기: 'Agree and turn on', 나중: 'Not now', 방들: 'Family to chat with', 방없음: 'No family is linked yet. Link family first in Family connections.', 새글: '{n} new', 상대꺼짐: 'They have not turned on chat yet',
      빈방: 'No messages yet. Start with a quick message below.', 쓰기: 'Write a message', 보내기: 'Send', 실패: 'Could not send', 다시: 'Retry', 더보기: 'Show earlier messages',
      끄기: 'Turn off chat', 끄기확인: 'Turning it off deletes the messages you sent. Tap again to turn off.', 로그인: 'Sign in to use this.', 안됨: 'Could not load the chat right now. Please try again in a moment.', 나: 'Me', 빠른말: 'Quick messages', 연결끝: 'This connection has ended. You can no longer send messages here.', 많음: 'Please wait a moment before sending more' },
    es: { 제목: 'Chat familiar', 닫기: 'Cerrar', 뒤로: 'Chats', 동의제목: '¿Activar el chat familiar?',
      동의: ['Los mensajes que envíe se guardan en nuestro servidor para que lleguen a su familia vinculada.', 'Los mensajes de más de 90 días se borran automáticamente.', 'Si desactiva el chat, los mensajes que envió se borran enseguida.', 'Pueden salir temas de salud: comparta solo lo necesario.'],
      켜기: 'Aceptar y activar', 나중: 'Ahora no', 방들: 'Familia con quien hablar', 방없음: 'Aún no hay familia vinculada. Vincúlela primero en Conexiones familiares.', 새글: '{n} nuevos', 상대꺼짐: 'Todavía no ha activado el chat',
      빈방: 'Aún no hay mensajes. Empiece con un mensaje rápido de abajo.', 쓰기: 'Escribir un mensaje', 보내기: 'Enviar', 실패: 'No se pudo enviar', 다시: 'Reintentar', 더보기: 'Ver mensajes anteriores',
      끄기: 'Desactivar el chat', 끄기확인: 'Al desactivarlo se borran los mensajes que envió. Pulse otra vez para desactivar.', 로그인: 'Inicie sesión para usarlo.', 안됨: 'No se pudo cargar el chat ahora. Inténtelo de nuevo en un momento.', 나: 'Yo', 빠른말: 'Mensajes rápidos', 연결끝: 'Esta conexión ha terminado. Ya no puede enviar mensajes aquí.', 많음: 'Espere un momento antes de enviar más' },
    ja: { 제목: '家族のトーク', 닫기: '閉じる', 뒤로: 'トーク一覧', 동의제목: '家族のトークをオンにしますか？',
      동의: ['送ったメッセージは、つながっている家族に届けるためにサーバーに保存されます。', '90日を過ぎたメッセージは自動で消えます。', 'トークをオフにすると、自分が送ったメッセージはすぐ消えます。', '健康の話が含まれることがあります。必要なことだけ書いてください。'],
      켜기: '同意してオンにする', 나중: 'あとで', 방들: 'トークする家族', 방없음: 'まだつながっている家族がいません。先に家族の連携でつないでください。', 새글: '新着 {n}', 상대꺼짐: '相手はまだトークをオンにしていません',
      빈방: 'まだメッセージはありません。下のクイックメッセージから始めてみてください。', 쓰기: 'メッセージを書く', 보내기: '送る', 실패: '送れませんでした', 다시: 'もう一度', 더보기: '前のメッセージを見る',
      끄기: 'トークをオフにする', 끄기확인: 'オフにすると自分が送ったメッセージが消えます。もう一度押すとオフになります。', 로그인: 'ログインすると使えます。', 안됨: '今はトークを読み込めませんでした。少ししてからもう一度お試しください。', 나: '自分', 빠른말: 'クイックメッセージ', 연결끝: 'この連携は終わっています。新しいメッセージは送れません。', 많음: '少し時間をおいてから送ってください' },
    zh: { 제목: '家人聊天', 닫기: '关闭', 뒤로: '聊天列表', 동의제목: '要开启家人聊天吗？',
      동의: ['您发送的消息会保存在服务器上，以便送达已关联的家人。', '超过90天的消息会自动删除。', '关闭聊天后，您发送的消息会立即删除。', '内容可能涉及健康信息，请只写必要的内容。'],
      켜기: '同意并开启', 나중: '以后再说', 방들: '可以聊天的家人', 방없음: '还没有关联的家人。请先在家人关联中建立关联。', 새글: '{n} 条新消息', 상대꺼짐: '对方还没有开启聊天',
      빈방: '还没有消息。可以先用下面的快捷消息开始。', 쓰기: '写消息', 보내기: '发送', 실패: '发送失败', 다시: '重试', 더보기: '查看更早的消息',
      끄기: '关闭聊天', 끄기확인: '关闭后您发送的消息会被删除。再按一次即关闭。', 로그인: '登录后才能使用。', 안됨: '暂时无法加载聊天，请稍后再试。', 나: '我', 빠른말: '快捷消息', 연결끝: '这个关联已经结束，无法再发送新消息。', 많음: '请稍后再发送' }
  };
  var 기본칩 = {
    yakjido: [{ ko: '약 드셨어요?', en: 'Did you take your medicine?', es: '¿Se tomó la medicina?', ja: '薬は飲みましたか？', zh: '吃药了吗？' },
      { ko: '먹었어요', en: 'I took it', es: 'Ya me la tomé', ja: '飲みました', zh: '吃过了' },
      { ko: '약 드세요', en: 'Time to take your medicine', es: 'Es hora de tomar la medicina', ja: '薬を飲んでくださいね', zh: '该吃药了' },
      { ko: '병원 같이 갈까요?', en: 'Shall we go to the hospital together?', es: '¿Vamos juntos al hospital?', ja: '一緒に病院に行きましょうか？', zh: '要一起去医院吗？' }],
    kids: [{ ko: '해열제 먹였어요({시각})', en: 'Gave fever medicine ({시각})', es: 'Le di el antitérmico ({시각})', ja: '解熱剤を飲ませました（{시각}）', zh: '已经喂了退烧药（{시각}）' },
      { ko: '열 몇 도예요?', en: 'What is the temperature?', es: '¿Cuánta fiebre tiene?', ja: '熱は何度ですか？', zh: '现在体温多少度？' },
      { ko: '병원 다녀올게요', en: 'I am taking them to the clinic', es: 'Voy con él al médico', ja: '病院に行ってきます', zh: '我带孩子去医院' }]
  };
  function 말() { var l = null; try { if (typeof 설정.말 === 'function') l = 설정.말(); } catch (e) {} return 말순.indexOf(l) >= 0 ? l : 'ko'; }
  function 글(k) { var t = (글표[말()] || 글표.ko)[k]; return t == null ? 글표.ko[k] : t; }
  function 켬열쇠() { return 'mn.chat.on.' + 설정.app; }
  function 켜짐() { try { return localStorage.getItem(켬열쇠()) === '1'; } catch (e) { return false; } }
  function 로그인됨() { try { return typeof 설정.로그인됨 === 'function' ? !!설정.로그인됨() : true; } catch (e) { return false; } }
  function 지금() { var d = new Date(); return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }
  function rpc(fn, args) {
    if (typeof 설정.준비 !== 'function') return Promise.reject(new Error('준비 없음'));
    return Promise.resolve(설정.준비()).then(function (sb) { if (!sb || !sb.rpc) throw new Error('서버 없음'); return sb.rpc(fn, args); })
      .then(function (r) { if (r && r.error) throw r.error; return r ? r.data : null; });
  }
  function 오류(e) { var t = String((e && (e.message || e.details || e.hint)) || e || '').toLowerCase();
    return /chat off/.test(t) ? 'off' : /not allowed/.test(t) ? 'gone' : /too many/.test(t) ? 'many' : /login required/.test(t) ? 'login' : 'etc'; }
  function 꺼짐처리() { try { localStorage.removeItem(켬열쇠()); } catch (e) {} 멈춤(); 지금방 = null; 동의(); }
  function 로그인안내() { 멈춤(); 지금방 = null; 틀열기(); 머리(글('제목'), false); 비움(); 몸.appendChild(칸('p', 'fc-p', 글('로그인'))); }
  function 연결끝() { 멈춤(); if (!몸 || 몸.querySelector('.fc-gone')) return; var p = 칸('p', 'fc-p fc-gone', 글('연결끝')); p.setAttribute('role', 'status'); 몸.appendChild(p); if (발) 발.style.display = 'none'; }
  function 이름(id) { try { var n = typeof 설정.이름 === 'function' ? 설정.이름(id) : ''; return n ? String(n) : '—'; } catch (e) { return '—'; } }
  function 칩들() {
    var a = 설정.칩 || 기본칩[설정.app] || [], l = 말();
    return a.map(function (x) { var t = typeof x === 'string' ? x : (x[l] || x.ko || ''); return String(t).replace(/\{시각\}/g, 지금()); }).filter(Boolean);
  }
  /* ── 그리기 도구: 글은 textContent 로만 ── */
  function 칸(tag, cls, 글자) { var e = document.createElement(tag); if (cls) e.className = cls; if (글자 != null) e.textContent = 글자; return e; }
  function 단추(글자, cls, 누름) { var b = 칸('button', cls, 글자); b.type = 'button'; b.addEventListener('click', 누름); return b; }
  var 스타일됨 = false;
  function 스타일() {
    if (스타일됨 || !document.head) return; 스타일됨 = true;
    var A = 'var(--fc-accent,var(--accent,#2f6b5a))', L = 'var(--fc-line,var(--line,rgba(127,127,127,.3)))', C = 'var(--fc-card,var(--card,#fff))', D = 'var(--fc-dim,var(--ink2,#666))';
    var st = document.createElement('style'); st.id = 'fc-style';
    st.textContent = '.fc{position:fixed;inset:0;z-index:2147482000;background:var(--bg,#fff);color:var(--ink,inherit);display:flex;flex-direction:column;word-break:keep-all;overflow-wrap:anywhere}' +
      '.fc-hd{display:flex;align-items:center;gap:8px;padding:max(10px,env(safe-area-inset-top)) 12px 10px;border-bottom:1px solid ' + L + '}.fc-hd h2{flex:1;min-width:0;margin:0;font-size:1.15em;line-height:1.3}' +
      '.fc-x,.fc-bk{min-height:44px;min-width:44px;padding:6px 12px;border-radius:12px;border:1px solid ' + L + ';background:transparent;color:inherit;font:inherit;font-weight:700;cursor:pointer}' +
      '.fc-bd{flex:1;overflow:auto;padding:14px 16px}.fc-p{margin:0 0 10px;line-height:1.55}.fc-dim{color:' + D + '}.fc-ul{margin:0 0 16px;padding:0;list-style:none}.fc-ul li{display:flex;gap:8px;padding:6px 0;line-height:1.55}.fc-ul li:before{content:"";flex:none;width:6px;height:6px;margin-top:.62em;border-radius:50%;background:' + A + '}' +
      '.fc-main{display:block;width:100%;min-height:52px;margin-top:10px;border:0;border-radius:14px;background:' + A + ';color:#fff;font:inherit;font-weight:800;cursor:pointer}.fc-sub{display:block;width:100%;min-height:48px;margin-top:8px;border:1px solid ' + L + ';border-radius:14px;background:transparent;color:inherit;font:inherit;font-weight:700;cursor:pointer}' +
      '.fc-room{display:flex;align-items:center;gap:10px;width:100%;min-height:60px;padding:12px;margin-bottom:8px;border:1px solid ' + L + ';border-radius:14px;background:' + C + ';color:inherit;font:inherit;text-align:left;cursor:pointer}.fc-room b{flex:1;min-width:0}.fc-room small{display:block;font-weight:500;color:' + D + '}' +
      '.fc-new{flex:none;min-width:24px;padding:2px 8px;border-radius:999px;background:' + A + ';color:#fff;font-size:.82em;font-weight:800;text-align:center}' +
      '.fc-msgs{display:flex;flex-direction:column;gap:8px}.fc-day{align-self:center;margin:6px 0;font-size:.8em;color:' + D + '}.fc-m{max-width:82%;align-self:flex-start}.fc-m.me{align-self:flex-end}' +
      '.fc-b{padding:9px 12px;border-radius:16px 16px 16px 4px;background:' + C + ';border:1px solid ' + L + ';line-height:1.5;white-space:pre-wrap}.fc-m.me .fc-b{border-radius:16px 16px 4px 16px;background:' + A + ';color:#fff;border-color:transparent}' +
      '.fc-m.card .fc-b{border-style:dashed}.fc-t{display:block;margin-top:2px;font-size:.76em;color:' + D + '}.fc-m.me .fc-t{text-align:right}.fc-fail{display:flex;gap:6px;align-items:center;justify-content:flex-end;margin-top:4px;font-size:.84em;color:var(--alarm,#b3261e)}' +
      '.fc-fail button{min-height:44px;padding:4px 12px;border-radius:10px;border:1px solid currentColor;background:transparent;color:inherit;font:inherit;font-weight:700;cursor:pointer}' +
      '.fc-ft{border-top:1px solid ' + L + ';padding:10px 12px max(10px,env(safe-area-inset-bottom))}.fc-chips{display:flex;gap:6px;overflow-x:auto;padding-bottom:8px}.fc-chip{flex:none;min-height:44px;padding:6px 12px;border-radius:999px;border:1px solid ' + A + ';background:transparent;color:' + A + ';font:inherit;font-weight:700;cursor:pointer;white-space:nowrap}' +
      '.fc-row{display:flex;gap:8px;align-items:flex-end}.fc-in{flex:1;min-width:0;min-height:48px;max-height:30vh;padding:10px 12px;border-radius:14px;border:1px solid ' + L + ';background:' + C + ';color:inherit;font:inherit;font-size:16px;resize:none}' +
      '.fc-send{flex:none;min-height:48px;min-width:64px;padding:6px 14px;border:0;border-radius:14px;background:' + A + ';color:#fff;font:inherit;font-weight:800;cursor:pointer}.fc-send[disabled]{opacity:.45}.fc-n{display:block;margin-top:4px;font-size:.76em;color:' + D + ';text-align:right}' +
      '.fc-more{display:block;margin:0 auto 10px;min-height:44px;padding:4px 14px;border-radius:12px;border:1px solid ' + L + ';background:transparent;color:inherit;font:inherit;cursor:pointer}.fc-off{display:block;margin:18px auto 0;min-height:44px;padding:4px 14px;border:0;background:transparent;color:' + D + ';font:inherit;text-decoration:underline;cursor:pointer}';
    document.head.appendChild(st);
  }
  /* ── 틀 ── */
  var 틀 = null, 몸 = null, 발 = null, 머리글 = null, 지금방 = null, 타이머 = 0, 메시지 = [], 끝 = false, 끄기누름 = 0;
  function 틀열기() {
    스타일();
    if (!틀) {
      틀 = 칸('div', 'fc'); 틀.id = 'mnFamChat'; 틀.setAttribute('role', 'dialog'); 틀.setAttribute('aria-modal', 'true');
      var hd = 칸('div', 'fc-hd'); 머리글 = 칸('h2'); 머리글.id = 'fcT'; 틀.setAttribute('aria-labelledby', 'fcT');
      hd.appendChild(머리글); 틀.appendChild(hd); 몸 = 칸('div', 'fc-bd'); 틀.appendChild(몸); 발 = 칸('div', 'fc-ft'); 틀.appendChild(발);
      document.body.appendChild(틀);
    }
    틀.setAttribute('lang', 말()); return 틀;
  }
  function 머리(제목, 뒤로) {
    var hd = 틀.querySelector('.fc-hd'); hd.textContent = '';
    if (뒤로) hd.appendChild(단추(글('뒤로'), 'fc-bk', function () { 방목록(); }));
    머리글.textContent = 제목; hd.appendChild(머리글); hd.appendChild(단추(글('닫기'), 'fc-x', 닫기));
  }
  function 닫기() { 멈춤(); 지금방 = null; if (틀) { 틀.remove(); 틀 = null; } }
  function 멈춤() { clearInterval(타이머); 타이머 = 0; }
  function 비움() { 몸.textContent = ''; 발.textContent = ''; 발.style.display = 'none'; }
  /* ── 동의 한 장 ── */
  function 동의() {
    틀열기(); 머리(글('동의제목'), false); 비움();
    var ul = 칸('ul', 'fc-ul'); 글('동의').forEach(function (t) { ul.appendChild(칸('li', '', t)); }); 몸.appendChild(ul);
    var 말칸 = 칸('p', 'fc-p fc-dim'); 말칸.setAttribute('role', 'status'); 몸.appendChild(말칸);
    var 켜 = 단추(글('켜기'), 'fc-main', function () {
      켜.disabled = true; 말칸.textContent = '';
      rpc('mn_chat_enable', { p_app: 설정.app }).then(function () { try { localStorage.setItem(켬열쇠(), '1'); } catch (e) {} 방목록(); })
        .catch(function (e) { 켜.disabled = false; 말칸.textContent = 오류(e) === 'login' ? 글('로그인') : 글('안됨'); });
    });
    몸.appendChild(켜); 몸.appendChild(단추(글('나중'), 'fc-sub', 닫기));
  }
  /* ── 방 목록 ── */
  function 방목록() {
    멈춤(); 지금방 = null; 틀열기(); 머리(글('제목'), false); 비움();
    몸.appendChild(칸('p', 'fc-p fc-dim', '…'));
    return rpc('mn_chat_rooms', { p_app: 설정.app }).then(function (rows) {
      if (!틀 || 지금방) return; 몸.textContent = '';
      rows = rows || [];
      if (!rows.length) { 몸.appendChild(칸('p', 'fc-p', 글('방없음'))); }
      else {
        몸.appendChild(칸('p', 'fc-p fc-dim', 글('방들')));
        rows.forEach(function (r) {
          var b = 단추('', 'fc-room', function () { 방열기(r.link_id); });
          var t = 칸('b', '', 이름(r.link_id)); if (!r.other_on) t.appendChild(칸('small', '', 글('상대꺼짐')));
          b.appendChild(t); if (r.unread > 0) b.appendChild(칸('span', 'fc-new', 글('새글').replace('{n}', String(r.unread))));
          몸.appendChild(b);
        });
      }
      몸.appendChild(단추(글('끄기'), 'fc-off', 끄기));
    }).catch(function (e) { if (!틀) return; var k = 오류(e); if (k === 'off') return 꺼짐처리(); if (k === 'login') return 로그인안내(); 몸.textContent = ''; 몸.appendChild(칸('p', 'fc-p', 글('안됨'))); });
  }
  function 끄기(e) {
    var 단 = e && e.currentTarget;
    if (Date.now() - 끄기누름 > 8000) { 끄기누름 = Date.now(); if (단) 단.textContent = 글('끄기확인'); return; }
    끄기누름 = 0;
    rpc('mn_chat_disable', { p_app: 설정.app }).then(function () { try { localStorage.removeItem(켬열쇠()); } catch (e) {} 닫기(); })
      .catch(function () { if (단) 단.textContent = 글('안됨'); });
  }
  /* ── 방 ── */
  function 날글(d) { try { return d.toLocaleDateString({ ko: 'ko-KR', en: 'en-US', es: 'es-ES', ja: 'ja-JP', zh: 'zh-CN' }[말()], { month: 'long', day: 'numeric', weekday: 'short' }); } catch (e) { return d.toISOString().slice(0, 10); } }
  function 시글(d) { return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }
  function 그리기() {
    var 칸들 = 몸.querySelector('.fc-msgs'); if (!칸들) return;
    var 아래 = 몸.scrollHeight - 몸.scrollTop - 몸.clientHeight < 60;
    칸들.textContent = ''; var 앞날 = '';
    if (!메시지.length) 칸들.appendChild(칸('p', 'fc-p fc-dim', 글('빈방')));
    메시지.forEach(function (m) {
      var d = new Date(m.created_at || Date.now()), 날 = 날글(d);
      if (날 !== 앞날) { 칸들.appendChild(칸('div', 'fc-day', 날)); 앞날 = 날; }
      var w = 칸('div', 'fc-m' + (m.mine ? ' me' : '') + (m.kind === 'card' ? ' card' : ''));
      w.appendChild(칸('div', 'fc-b', m.body)); w.appendChild(칸('span', 'fc-t', 시글(d)));
      if (m.실패) { var f = 칸('div', 'fc-fail', m.이유 || 글('실패')); f.appendChild(단추(글('다시'), '', function () { 보내기(m.body, m.kind, m); })); w.appendChild(f); }
      칸들.appendChild(w);
    });
    if (아래) 몸.scrollTop = 몸.scrollHeight;
  }
  function 합치기(rows) {   /* 서버가 준 것(최신부터)을 오래된 것부터로 · 같은 id 는 하나 · 보내는 중·실패한 내 글은 끝에 둔다 */
    var 있음 = {}; 메시지.forEach(function (m) { if (m.id) 있음[m.id] = m; });
    (rows || []).forEach(function (r) { if (!있음[r.id]) 있음[r.id] = { id: r.id, mine: !!r.mine, kind: r.kind || 'text', body: String(r.body == null ? '' : r.body), created_at: r.created_at }; });
    var 서버것 = Object.keys(있음).map(function (k) { return 있음[k]; }).sort(function (a, b) { var x = Number(a.id), y = Number(b.id); return (isFinite(x) && isFinite(y)) ? x - y : String(a.created_at).localeCompare(String(b.created_at)); });
    메시지 = 서버것.concat(메시지.filter(function (m) { return !m.id; }));
  }
  function 받기() {
    if (!지금방 || document.visibilityState === 'hidden') return Promise.resolve();
    var 방 = 지금방;
    return rpc('mn_chat_list', { p_app: 설정.app, p_link: 방, p_before: null, p_limit: 50 }).then(function (rows) { if (방 !== 지금방) return; 합치기(rows); 그리기(); }).catch(function (e) { if (방 !== 지금방) return; var k = 오류(e); if (k === 'off') 꺼짐처리(); else if (k === 'gone') 연결끝(); else if (k === 'login') 로그인안내(); });
  }
  function 더받기(btn) {
    var ids = 메시지.filter(function (m) { return m.id != null; }).map(function (m) { return Number(m.id); }).filter(function (n) { return isFinite(n); }); if (!ids.length) return;
    btn.disabled = true;   /* 11-04b Main — p_before 는 지금 보이는 가장 작은 메시지 id(bigint) */
    rpc('mn_chat_list', { p_app: 설정.app, p_link: 지금방, p_before: Math.min.apply(null, ids), p_limit: 50 }).then(function (rows) {
      var h = 몸.scrollHeight; 합치기(rows); 그리기(); 몸.scrollTop += 몸.scrollHeight - h; btn.disabled = false; if (!rows || rows.length < 50) btn.remove();
    }).catch(function (e) { btn.disabled = false; var k = 오류(e); if (k === 'off') 꺼짐처리(); else if (k === 'gone') 연결끝(); });
  }
  function 방열기(id) {
    if (!켜짐()) return 동의();
    틀열기(); 지금방 = id; 메시지 = []; 머리(이름(id), true); 비움();
    var 더 = 단추(글('더보기'), 'fc-more', function () { 더받기(더); }); 몸.appendChild(더);
    var 칸들 = 칸('div', 'fc-msgs'); 칸들.setAttribute('aria-live', 'polite'); 몸.appendChild(칸들);
    발.style.display = '';
    var 칩칸 = 칸('div', 'fc-chips'); 칩칸.setAttribute('role', 'group'); 칩칸.setAttribute('aria-label', 글('빠른말'));
    칩들().forEach(function (t, i) { 칩칸.appendChild(단추(t, 'fc-chip', function () { 보내기(칩들()[i] || t, 'quick'); })); });   /* {시각}은 누른 때로 다시 */
    발.appendChild(칩칸);
    var 줄 = 칸('div', 'fc-row'), 입 = 칸('textarea', 'fc-in'); 입.rows = 1; 입.maxLength = 최대; 입.setAttribute('aria-label', 글('쓰기')); 입.placeholder = 글('쓰기');
    var 수 = 칸('span', 'fc-n', '0/' + 최대), 보 = 단추(글('보내기'), 'fc-send', function () { var t = 입.value.trim(); if (!t) return; 입.value = ''; 수.textContent = '0/' + 최대; 보.disabled = true; 보내기(t, 'text'); });
    보.disabled = true;
    입.addEventListener('input', function () { if (입.value.length > 최대) 입.value = 입.value.slice(0, 최대); 수.textContent = 입.value.length + '/' + 최대; 보.disabled = !입.value.trim(); });
    줄.appendChild(입); 줄.appendChild(보); 발.appendChild(줄); 발.appendChild(수);
    그리기(); 받기().then(function () { if (메시지.filter(function (m) { return m.id; }).length < 50) 더.remove(); 몸.scrollTop = 몸.scrollHeight; });   /* 50개보다 적으면 더 볼 것이 없다 */
    멈춤(); 타이머 = setInterval(받기, 주기);
  }
  function 보내기(글자, kind, 다시칸) {
    var t = String(글자 || '').trim().slice(0, 최대); if (!t || !지금방) return Promise.resolve(null);
    var m = 다시칸 || { mine: true, kind: kind || 'text', body: t, created_at: new Date().toISOString() };
    m.실패 = false; if (!다시칸) 메시지.push(m); 그리기(); 몸.scrollTop = 몸.scrollHeight;
    var 방 = 지금방;
    return rpc('mn_chat_send', { p_app: 설정.app, p_link: 방, p_body: t, p_kind: m.kind }).then(function (id) {
      m.id = (id && typeof id === 'object' && id.id) ? id.id : id; if (방 === 지금방) { 메시지 = 메시지.filter(function (x) { return x !== m; }); 합치기([m]); 그리기(); } return m.id;
    }).catch(function (e) { var k = 오류(e); if (k === 'off') { 꺼짐처리(); return null; } if (k === 'login') { 로그인안내(); return null; }
      if (k === 'gone') { 메시지 = 메시지.filter(function (x) { return x !== m; }); 그리기(); 연결끝(); return null; }
      m.실패 = true; m.이유 = k === 'many' ? 글('많음') : ''; 그리기(); return null; });
  }
  function 열기() {
    if (!로그인됨()) { 틀열기(); 머리(글('제목'), false); 비움(); 몸.appendChild(칸('p', 'fc-p', 글('로그인'))); return; }
    return 켜짐() ? 방목록() : 동의();
  }
  function 카드보내기(link, 글자) {
    if (!켜짐() || !로그인됨() || !link) return Promise.resolve(null);
    var t = String(글자 || '').trim().slice(0, 최대); if (!t) return Promise.resolve(null);
    return rpc('mn_chat_send', { p_app: 설정.app, p_link: link, p_body: t, p_kind: 'card' }).catch(function () { return null; });
  }
  function 안읽음() {
    if (!켜짐() || !로그인됨()) return Promise.resolve(0);
    return rpc('mn_chat_rooms', { p_app: 설정.app }).then(function (rows) { return (rows || []).reduce(function (s, r) { return s + (r.unread > 0 ? +r.unread : 0); }, 0); }).catch(function () { return 0; });
  }
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible' && 지금방) 받기(); });
  window.가족대화 = { __v: 판, 판: 판, 열기: 열기, 방열기: 방열기, 닫기: 닫기, 카드보내기: 카드보내기, 안읽음: 안읽음, 켜짐: 켜짐,
    설치: function (o) { o = o || {}; Object.keys(o).forEach(function (k) { 설정[k] = o[k]; }); return window.가족대화; } };
})();
/* ▲▲ 가족대화 부품 끝 ▲▲ */

/* 11-04 Main 「가족 대화」 — 공용 부품(yozm-health _도구/가족대화_부품.js · 주인 길동무)을 그대로 심고 아래에서만 잇는다.
   방 = 허락까지 끝난 가족 연결(yak_family_links) 하나 · 이름 = 연결의 이름표(챙기는 분 → 그 분 호칭, 내 체크를 받는 가족 → 계정 이메일).
   입구: 알림 설정의 연결마다 「대화」 · 홈은 안 읽은 글이 있을 때만 맨 위 한 줄 · 「먹었어요」는 대화를 켠 분만 「아침 약 먹었어요 · 08:02」 카드(약 이름·양 없음, 하루 한 회차 한 번). */
const 대화된연결 = x => x && x.status !== 'waiting' && x.status !== 'asking';
const 대화방이름 = id => { const x = (FAMQ.list || []).find(r => String(r.id) === String(id)); return !x ? '가족' : x.role === 'member' ? (x.label || '가족') : (x.other_email || '가족'); };
const 대화단추 = id => window.가족대화 ? `<button type="button" class="btn line" onclick="가족대화.방열기('${esc(String(id))}')">대화</button>` : '';
try { if (window.가족대화) 가족대화.설치({ app: 'yakjido', 준비: () => 서버.준비(), 로그인됨: () => { try { return srvLoggedIn(); } catch (e) { return false; } }, 말: () => window.LANG || 'ko', 이름: 대화방이름 }); } catch (e) {}
const 대화점 = { n: 0, at: 0 };
window.가족대화줄 = () => { try {
  if (!famOn() || !window.가족대화 || !가족대화.켜짐() || !srvLoggedIn()) return '';
  if (FAMQ.list == null) famLoad();
  if (Date.now() - 대화점.at > 60000) { 대화점.at = Date.now();
    가족대화.안읽음().then(n => { n = n > 0 ? n : 0; if (n !== 대화점.n) { 대화점.n = n; if (/^#\/(home)?$|^$/.test(location.hash || '')) route(); } }).catch(() => {}); }
  return 대화점.n > 0 ? `<button type="button" class="famdot" onclick="가족대화.열기()" aria-label="가족 대화 새 글 ${대화점.n}"><b>${대화점.n}</b><span>가족 대화 새 글</span></button>` : '';
} catch (e) { return ''; } };
const 대화카드 = keys => { try {
  if (!famOn() || !window.가족대화 || !가족대화.켜짐() || !srvLoggedIn() || !keys || !keys.length) return;
  const day = todayKey(), CK = 'yakjido.chatcard'; let 보냄 = {}; try { 보냄 = JSON.parse(localStorage.getItem(CK) || '{}') || {}; } catch (e) {}
  const 오늘 = (보냄.d === day ? 보냄.k : []) || [], 새 = keys.map(k => String(k).split('@')[1]).filter(t => t && !오늘.includes(t));
  if (!새.length) return;
  const t = [...new Set(새)].sort()[0], h = +t.slice(0, 2), L = window.LANG || 'ko', now = new Date(), hm = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
  const 때 = { ko: ['아침', '점심', '저녁', '자기 전'], en: ['Morning', 'Midday', 'Evening', 'Bedtime'], es: ['De la mañana', 'Del mediodía', 'De la tarde', 'De la noche'], ja: ['朝', '昼', '夕', '寝る前'], zh: ['早上', '中午', '晚上', '睡前'] }[L] || ['아침', '점심', '저녁', '자기 전'];
  const i = h < 11 ? 0 : h < 15 ? 1 : h < 20 ? 2 : 3;
  const 글 = { ko: `${때[i]} 약 먹었어요 · ${hm}`, en: `${때[i]} medicine taken · ${hm}`, es: `${때[i]}: medicina tomada · ${hm}`, ja: `${때[i]}の薬を飲みました · ${hm}`, zh: `${때[i]}的药吃了 · ${hm}` }[L] || `${때[i]} 약 먹었어요 · ${hm}`;
  try { localStorage.setItem(CK, JSON.stringify({ d: day, k: 오늘.concat(새) })); } catch (e) {}
  famRpc('yak_family_list').then(d => { FAMQ.list = d || FAMQ.list; (d || []).filter(x => x.role === 'owner' && 대화된연결(x)).forEach(x => { try { 가족대화.카드보내기(x.id, 글); } catch (e) {} }); }).catch(() => {});
} catch (e) {} };
(() => { const 원 = window.tick; if (typeof 원 === 'function') window.tick = (id, t) => { const k = id + '@' + t, 전 = (((ME.taken || {})[todayKey()]) || []).includes(k); 원(id, t); if (!전 && (((ME.taken || {})[todayKey()]) || []).includes(k)) 대화카드([k]); };
  const 원2 = window.tickFromNote; if (typeof 원2 === 'function') window.tickFromNote = (key, day) => { const k0 = day || todayKey(), 전 = [...(((ME.taken || {})[k0]) || [])]; 원2(key, day); if (k0 === todayKey()) 대화카드((((ME.taken || {})[k0]) || []).filter(x => !전.includes(x))); }; })();
try { const st = document.createElement('style'); st.textContent = '.famdot{display:flex;align-items:center;gap:10px;width:100%;margin:8px 0 4px;min-height:48px;padding:10px 14px;border:1px solid var(--hairline);border-radius:14px;background:var(--card,#fff);color:inherit;font:inherit;text-align:left;cursor:pointer}.famdot b{display:inline-grid;place-items:center;min-width:26px;height:26px;padding:0 6px;border-radius:13px;background:var(--accent,#2f6b5a);color:#fff;font-size:.86em}'; document.head.appendChild(st); } catch (e) {}

/* 내 정보·동의·로그인·약관 화면을 보고 있었으면 다시 그린다(이 파일이 늦게 오므로) */
try { if (/^#\/(me|consent|login|notify|sgoal|sstage|doc|hello\/3|supp$|supp\?|sgoal|sstage|rx|about|search|myths|askdoc|talk|p\/|p\?|p$)/.test(location.hash)) route(); } catch (e) {}
