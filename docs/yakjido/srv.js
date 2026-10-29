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

  /* ── 구독 상태 ── 서버 표 subscriptions 를 RPC 로 읽는다(처음이면 체험 7일이 생긴다). 표가 아직 없거나 오프라인이면 조용히 지난 값을 쓴다. */
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
     소셜 단추는 앱이 켠 것(window.소셜켜짐() → [{ n:'카카오', 열기:function }])만 그린다 — 지금 약지도에는 없다(눌러도 안 되는 단추 금지). */
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
    b.disabled = 막; if (w) w.hidden = !막;
  };
  window.계정문동작 = function (what) {
    what = what || (문탭 === 'signup' ? 'signup' : 'login');
    var g = document.getElementById('srvAgree'), a = document.getElementById('srvAge'), em = document.getElementById('srvEmail'), pw = document.getElementById('srvPw');
    if (!서버허용()) {
      if (!g || !g.checked) { 문말('「서버에 저장하기」에 동의하셔야 계정을 쓸 수 있어요. 동의하지 않으셔도 약지도는 그대로 쓰실 수 있어요.'); if (g) g.focus(); return; }
      if (typeof 설정.동의기록 === 'function') { try { 설정.동의기록(); } catch (e) {} }
    }
    if (what === 'signup' && 설정.가입확인 && (!a || !a.checked)) { 문말('계정을 만들려면 「' + 설정.가입확인.글 + '」에 체크해 주세요.'); if (a) a.focus(); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(((em || {}).value || '').trim())) { 문말('이메일 주소를 다시 확인해 주세요.'); if (em) em.focus(); return; }
    if (what !== 'reset' && ((pw || {}).value || '').length < 6) { 문말('비밀번호는 6자 이상이에요.'); if (pw) pw.focus(); return; }
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
    if (소셜.length) h += '<div class="door-social">' + 소셜.map(function (x, i) { return '<button type="button" onclick="소셜켜짐()[' + i + '].열기()">' + 글자안전(x.n) + '로 계속하기</button>'; }).join('') + '</div><p class="door-or"><span>또는 이메일로</span></p>';
    h += '<label class="door-f" for="srvEmail">이메일</label><input id="srvEmail" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" enterkeyhint="next" value="' + 글자안전(st.email || '') + '">'
      + 비번칸('srvPw', '비밀번호 <small>처음이면 새로 정할 비밀번호 · 6자 이상</small>', 'current-password', 'go');
    if (설정.가입확인) h += '<label class="door-ck"><input id="srvAge" type="checkbox" onchange="this.dataset.at=this.checked?new Date().toISOString():\'\'"><span><b>' + 글자안전(설정.가입확인.글) + ' <em class="door-tag">처음 만들 때 필수</em></b>' + (설정.가입확인.설명 ? '<small>' + 글자안전(설정.가입확인.설명) + '</small>' : '') + '</span></label>';
    if (가입 && 설정.가입확인) h += '<label class="door-ck"><input id="srvAge" type="checkbox" onchange="this.dataset.at=this.checked?new Date().toISOString():\'\';계정문확인()"><span><b>' + 글자안전(설정.가입확인.글) + ' <em class="door-tag">필수</em></b>' + (설정.가입확인.설명 ? '<small>' + 글자안전(설정.가입확인.설명) + '</small>' : '') + '</span></label>';
    if (!동의됨) h += '<label class="door-ck"><input id="srvAgree" type="checkbox" onchange="계정문확인()"><span><b>「서버에 저장하기」에 동의해요 <em class="door-tag">필수</em></b><small>건강에 관한 민감정보라 따로 여쭤요. 로그인하시면 이 휴대폰의 기록이 계정으로 이어져요.</small></span></label>'
      + '<details class="door-more"><summary>무엇이 올라가나요<svg class="i chev" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></summary><dl>'
      + '<dt>올라가는 것</dt><dd>' + 글자안전(항목.ko || '약지도 기록') + '</dd><dt>어디에</dt><dd>메디나눔 서버(Supabase, 서울)</dd><dt>왜</dt><dd>폰을 바꿔도 이어 보려고</dd>'
      + '<dt>언제까지</dt><dd>계정을 지우실 때까지 — 동의를 거두시면 서버 기록을 바로 지워요</dd></dl><p>동의하지 않으셔도 되고, 동의하지 않아도 약지도는 이 휴대폰에서 그대로 쓰실 수 있어요. 보기 설정과 날씨는 올라가지 않아요.</p></details>';
    var 막힘 = !동의됨;
    h += 말칸 + '<button type="button" id="srvDoorGo" class="door-go" onclick="계정문동작(\'continue\')"' + (막힘 ? ' disabled aria-describedby="doorWhy"' : '') + '>메일로 계속하기</button>'
      + (막힘 ? '<p id="doorWhy" class="door-why">필수에 체크하시면 눌려요</p>' : '')
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
      return 준비().then(function () { return typeof 설정.지우기전 === 'function' ? Promise.resolve(설정.지우기전(sb, 세션)).catch(function () {}) : null; }).then(function () { return sb.rpc('delete_own_account', { p_app: 설정.app }); }).then(function (r) {
        if (r && r.error) throw r.error;
        try { 내열쇠().forEach(function (k) { localStorage.removeItem(k); }); } catch (e) {}
        try { localStorage.removeItem('_srv_' + 설정.app); localStorage.removeItem(구독키()); } catch (e) {}
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
    세션: function () { return 세션; }, 동기화: function () { return 준비().then(지운것올리기).then(끌어오기).then(밀어올리기); },
    /* 2026-09-22 — 지운 것을 서버에도 지운다. 로그인 전이거나 오프라인이면 묘비만 남기고,
       연결되면 그때 지운다. 앱은 열쇠를 지울 때 이걸 부르면 된다. */
    지움: function (열쇠들) { 지움표시(열쇠들); if (sb && 세션 && 온라인()) return 지운것올리기(); return Promise.resolve(0); },
    전부지움: function () { 전부지움표시(); if (sb && 세션 && 온라인()) return 지운것올리기(); return Promise.resolve(0); },
    /* 2026-10-13 — 「서버에 저장하기」 동의를 거둘 때: 이 앱의 서버 기록을 지우고(다른 앱 기록이 없으면 계정도) 로그아웃. 이 기기 기록은 그대로. */
    서버만지움: function () {
      return 준비().then(function () {
        if (!세션) return { skipped: true };
        return sb.rpc('delete_own_account', { p_app: 설정.app }).then(function (r) {
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
     · 「7일 체험 시작」·「다시 구독하기」 → 껍데기.결제.구매('<app>_month') → 웹훅이 서버 표를 고치면 subscription_status 를 다시 읽는다(몇 번 되읽음).
       start_trial RPC 는 스토어 길에서는 부르지 않는다(체험은 스토어 상품의 7일 체험이다).
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
      계정으로: '체험은 계정으로 시작해요. 로그인하고 메일 확인을 마치면 7일 동안 모두 쓸 수 있어요.',
      계정없음: '체험과 구독은 준비 중이에요. 지금은 이 기능을 열 수 없어요.',
      전환날: '7일 체험 뒤 {날}부터 {값}이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      전환: '7일 체험이 끝나면 {값}이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      동의: '(필수) 7일 체험이 끝나는 {날}에 {값}이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      체험끝: '7일 체험이 끝났어요.', 기간끝: '구독 기간이 끝났어요.', 기록그대로: '그동안 남긴 기록은 그대로 있어요.', 기록그대로2: '남긴 기록은 그대로 있어요.',
      로그인하러: '로그인하러 가기', 닫기: '닫기', 체험시작: '7일 체험 시작', 결제수단: '결제수단 등록',
      결제준비: '결제 준비 중이에요. 지금은 결제되지 않아요.', 결제준비짧게: '결제 준비 중이에요.',
      /* 2026-10-20 — 결제 단추 바로 위 고지(전자상거래법 13조 · Play 구독 정책). 요청 20261020_ClinicScore_메디나눔_구독부품글표 */
      고지첫결제: '첫 결제 — 7일 체험이 끝나는 {날}에 {값}이 결제됩니다.',
      고지첫결제날없음: '첫 결제 — 7일 체험이 끝나는 날에 {값}이 결제됩니다.',
      고지갱신: '갱신 — 이후 {주기}마다 자동으로 갱신됩니다. 해지하지 않으면 계속 결제됩니다.',
      고지주기월: '한 달', 고지주기연: '1년',
      고지해지스토어: '해지 — 구독을 산 스토어에서 언제든 해지할 수 있습니다. Google Play 는 「결제 및 정기 결제 → 정기 결제」, App Store 는 「계정 → 구독」. 앱을 지워도 해지되지 않습니다.',
      고지해지앱: '해지 — 이 앱의 「구독과 결제」 화면에서 언제든 해지할 수 있습니다. 앱을 지워도 해지되지 않습니다.',
      고지검토: '<b>검토용 미리 보기</b> — 결제가 열린 뒤 결제 단추 위에 보일 안내입니다. 지금은 결제되지 않습니다.',
      고지복원: '복원 — 폰을 바꾸거나 앱을 다시 설치하면 「구매 복원」으로 이용권을 되살릴 수 있습니다.',
      약관: '이용약관', 처리방침: '개인정보 처리방침', 환불안내: '환불·해지 안내',
      다시동의: '결제가 시작되기 전에 요금·결제일을 보여 드리고 다시 동의를 받아요.',
      동의준비: '(필수) 7일 체험은 {날}에 끝나요. 결제가 시작되기 전에 요금·결제일을 보여 드리고 다시 동의를 받아요.',
      요금: '요금', 학생기본: '학생', 학생인증준비: '인증은 준비 중이에요', 학생인증단추: '학생 인증하기',
      출시가: '출시 기념가', 출시조건: '출시 3개월 안에 가입하면 첫 1년', 회원권: '메디나눔 회원권', 회원권설명: '다섯 앱을 함께 쓰는 이용권', 회원권자격: 'ClinicScore 의료인 기능은 의료인 확인 뒤 열려요',
      곧: '곧 열려요', 출시값: '{값}(출시 기념가 · 첫 1년, 둘째 해부터 {정가})', 출시값둘: '출시 기념가 {값} — 첫 1년, 둘째 해부터 {정가}', 초대중: '<b>초대 코드로 체험 중</b> · {날}까지', 초대뒤: '이 기간에는 결제되지 않아요. 기간이 끝나면 일반 상태로 돌아가요.', 회원권시작: '회원권으로 시작', 회원권연시작: '회원권 1년으로 시작 · {값}', 회원권중: '메디나눔 회원권으로 열려 있어요.',
      이유: { login: '먼저 로그인해 주세요.', verify: '메일함의 확인 링크를 먼저 눌러 주세요. 확인한 계정에서 체험이 시작돼요.',
              used_account: '이 계정은 7일 체험을 이미 쓰셨어요.', used_device: '이 기기에서는 7일 체험을 이미 쓰셨어요.',
              device: '이 브라우저에서는 체험을 시작할 수 없어요. 다른 브라우저로 해 주세요.', app: '잠시 문제가 있었어요. 다시 해 주세요.',
              noacct: '계정이 열리면 체험을 시작할 수 있어요.' },
      체크: '결제 안내를 확인하고 체크해 주세요.', 인터넷: '인터넷이 닿지 않아요. 연결되면 다시 해 주세요.',
      체험됨: '7일 체험을 시작했어요. {날}까지 모두 쓸 수 있어요.',
      해지취소됨: '해지를 취소했어요. 그대로 이어져요.', 해지됨: '해지했어요. ', 까지그대로: '{날}까지는 그대로 쓸 수 있어요.',
      카드결제: '{날}에 {값}이 결제됩니다. 원하지 않으시면 그 전에 해지할 수 있어요.',
      카드준비: '{날}에 7일 체험이 끝나요. 결제가 시작되기 전에 요금·결제일을 보여 드리고 다시 동의를 받아요.',
      해지자세히: '해지·자세히', 카드닫기이름: '결제 안내 닫기',
      관리로그인: '로그인하면 구독 상태를 볼 수 있어요.',
      관리계정없음: '계정이 열리면 여기서 체험을 시작하고 구독 상태를 볼 수 있어요.',
      아직: '아직 체험을 시작하지 않았어요.', 관리전환: '7일 체험 뒤 {값}이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      구독중: '구독 중이에요', 체험중: '체험 중이에요', 남음: ' · {n}일 남았어요', 까지괄호: ' ({날}까지)',
      해지예약: '해지를 예약했어요. ', 해지예약뒤: '{날}까지는 그대로 쓸 수 있고, 그 뒤로 결제되지 않아요.',
      해지취소: '해지 취소', 다음결제: '다음 결제일 {날} · {값}', 해지하기: '해지하기', 해지해도: '해지해도 {날}까지는 그대로 쓸 수 있어요.', 기간끝말: '기간 끝',
      휴대폰: '휴대폰으로 인증', 공동: '공동인증서로 인증', 미연결: '아직 연결되지 않았어요.', 문제: '잠시 문제가 있었어요.',
      /* 2026-10-08 스토어 결제(껍데기) */
      복원: '구매 복원', 다시구독: '다시 구독하기', 스토어관리: '스토어에서 구독 관리',
      스토어해지: '해지는 스토어의 구독 관리 화면에서 해요. 해지해도 {날}까지는 그대로 쓸 수 있어요.',
      결제취소: '결제를 취소했어요. 바뀐 것은 없어요.', 결제안됨: '결제가 되지 않았어요. 잠시 뒤 다시 해 주세요.',
      결제반영중: '결제는 끝났어요. 구독 상태가 곧 반영돼요. 잠시 뒤 다시 열어 주세요.', 구독됨: '구독을 시작했어요. 바로 모두 쓸 수 있어요.',
      관리전환둘: '7일 체험 뒤 고르신 요금({값})이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      연시작: '1년으로 시작 · {값}', 연구독: '1년으로 구독 · {값}',
      동의둘: '(필수) 7일 체험이 끝나는 {날}에 고르신 요금({값})이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      전환둘날: '7일 체험 뒤 {날}부터 고르신 요금({값})이 결제됩니다. 그 전에 언제든 해지할 수 있습니다.',
      복원됨: '구매를 복원했어요.', 복원없음: '복원할 구매가 없어요. 구매한 Google 계정이 이 폰에 로그인되어 있는지 확인해 주세요.'
    },
    en: {
      구독: 'Subscription', 이기능: 'This feature',
      잠김: '<b>{이름}</b> is part of the subscription.',
      응급기본: 'Emergency help is always open.',
      계정으로: 'The trial starts from an account. Sign in and confirm your email to use everything for 7 days.',
      계정없음: 'The trial and subscription are still being prepared. This feature cannot be opened yet.',
      전환날: 'After the 7-day trial, {값} will be charged from {날}. You can cancel any time before then.',
      전환: 'When the 7-day trial ends, {값} will be charged. You can cancel any time before then.',
      동의: '(Required) When the 7-day trial ends on {날}, {값} will be charged. You can cancel any time before then.',
      체험끝: 'Your 7-day trial has ended.', 기간끝: 'Your subscription period has ended.', 기록그대로: 'Everything you recorded is still here.', 기록그대로2: 'Everything you recorded is still here.',
      로그인하러: 'Sign in', 닫기: 'Close', 체험시작: 'Start 7-day trial', 결제수단: 'Add payment method',
      결제준비: 'Payments are not set up yet. Nothing is charged now.', 결제준비짧게: 'Payments are not set up yet.',
      고지첫결제: 'First charge — {값} on {날}, when the 7-day trial ends.',
      고지첫결제날없음: 'First charge — {값} on the day the 7-day trial ends.',
      고지갱신: 'Renewal — renews automatically every {주기}. You are charged until you cancel.',
      고지주기월: 'month', 고지주기연: 'year',
      고지해지스토어: 'Cancel — any time in the store you bought it from: Google Play ‘Payments and subscriptions → Subscriptions’, App Store ‘Account → Subscriptions’. Deleting the app does not cancel it.',
      고지해지앱: 'Cancel — any time on the ‘Subscription and billing’ screen in this app. Deleting the app does not cancel it.',
      고지검토: '<b>Review preview</b> — this is what appears above the payment button once billing opens. Nothing is charged now.',
      고지복원: 'Restore — if you change phones or reinstall, ‘Restore purchase’ brings your subscription back.',
      약관: 'Terms of Service', 처리방침: 'Privacy Policy', 환불안내: 'Refunds and cancellation',
      다시동의: 'Before any payment starts, we will show you the price and billing date and ask for your consent again.',
      동의준비: '(Required) The 7-day trial ends on {날}. Before any payment starts, we will show you the price and billing date and ask for your consent again.',
      요금: 'Price', 학생기본: 'students', 학생인증준비: 'verification is coming soon', 학생인증단추: 'Verify student status',
      출시가: 'Launch price', 출시조건: 'first year, if you join within 3 months of launch', 회원권: 'MediNanum pass', 회원권설명: 'one plan for all five apps', 회원권자격: 'ClinicScore professional tools open after the professional check',
      곧: 'coming soon', 출시값: '{값} (launch price for the first year; {정가} from the second year)', 출시값둘: 'launch price {값} for the first year; {정가} from the second year', 초대중: '<b>Invite access</b> · until {날}', 초대뒤: 'Nothing is charged during this period. Afterwards it returns to normal.', 회원권시작: 'Start with the pass', 회원권연시작: 'Start a 1-year pass · {값}', 회원권중: 'Open through your MediNanum pass.',
      이유: { login: 'Please sign in first.', verify: 'Please open the confirmation link in your email first. The trial starts on a confirmed account.',
              used_account: 'This account has already used the 7-day trial.', used_device: 'This device has already used the 7-day trial.',
              device: 'The trial cannot be started in this browser. Please try another browser.', app: 'Something went wrong. Please try again.',
              noacct: 'You can start the trial once accounts open.' },
      체크: 'Please read the billing notice and tick the box.', 인터넷: 'Cannot reach the internet. Please try again once you are connected.',
      체험됨: 'Your 7-day trial has started. Everything is open until {날}.',
      해지취소됨: 'Cancellation withdrawn. Your plan continues.', 해지됨: 'Cancelled. ', 까지그대로: 'You can keep using it until {날}.',
      카드결제: '{값} will be charged on {날}. If you do not want this, you can cancel before then.',
      카드준비: 'Your 7-day trial ends on {날}. Before any payment starts, we will show you the price and billing date and ask for your consent again.',
      해지자세히: 'Cancel · details', 카드닫기이름: 'Close billing notice',
      관리로그인: 'Sign in to see your subscription.',
      관리계정없음: 'Once accounts open, you can start the trial and see your subscription here.',
      아직: 'You have not started the trial yet.', 관리전환: 'After the 7-day trial, {값} will be charged. You can cancel any time before then.',
      구독중: 'Subscribed', 체험중: 'On trial', 남음: ' · {n} days left', 까지괄호: ' (until {날})',
      해지예약: 'Cancellation scheduled. ', 해지예약뒤: 'You can keep using it until {날}, and nothing will be charged after that.',
      해지취소: 'Undo cancellation', 다음결제: 'Next payment {날} · {값}', 해지하기: 'Cancel', 해지해도: 'Even if you cancel, you can keep using it until {날}.', 기간끝말: 'the end of the period',
      휴대폰: 'Verify by phone', 공동: 'Verify with certificate', 미연결: 'Not connected yet.', 문제: 'Something went wrong.',
      /* 2026-10-08 store billing (shell) */
      복원: 'Restore purchases', 다시구독: 'Subscribe again', 스토어관리: 'Manage in the store',
      스토어해지: 'Cancel from the store’s subscription settings. Even if you cancel, you can keep using it until {날}.',
      결제취소: 'Payment cancelled. Nothing has changed.', 결제안됨: 'The payment did not go through. Please try again in a moment.',
      결제반영중: 'Payment complete. Your subscription will show up shortly. Please reopen in a moment.', 구독됨: 'Your subscription has started. Everything is open now.',
      관리전환둘: 'After the 7-day trial, the plan you choose ({값}) will be charged. You can cancel any time before then.',
      연시작: 'Start with 1 year · {값}', 연구독: 'Subscribe for 1 year · {값}',
      동의둘: '(Required) When the 7-day trial ends on {날}, the plan you choose ({값}) will be charged. You can cancel any time before then.',
      전환둘날: 'After the 7-day trial, the plan you choose ({값}) will be charged from {날}. You can cancel any time before then.',
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
      /* 2026-10-08 스토어 결제 — 체험 전에는 「7일 체험 시작」이 곧 스토어 구매라 단추를 겹치지 않는다. 끝난 뒤(체험 끝·기간 끝)에만 「다시 구독하기」 */
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
    if (껍데기결제()) return 구매흐름(plan);   /* 스토어 길: 체험은 스토어 상품의 7일 체험. start_trial 은 부르지 않는다 · 2026-10-13 로그인 없이도 */
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
  서버.설치({ app: 'yakjido', 열쇠: /^yakjido\.me\.v1$/, 병합: function (k, mine, theirs) { return typeof mergeMe === 'function' ? mergeMe(mine, theirs) : null; }, 준비됨: function () { return !!(typeof D !== 'undefined' && D.meta && D.meta.account === true); }, 허용: srvAgreed, 다시그리기: srvReload,
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
    '<p class="small muted" style="margin-top:10px">사는 나라 · Country — 응급 번호</p><div class="fs-seg lang-seg" role="group" aria-label="나라" style="flex-wrap:wrap">' + CN.map(function (x) { return b(window.CC === x[0], "setLang(window.LANG,'" + x[0] + "')", x[1]); }).join('') + '</div></section>';
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
        if (위험) d.innerHTML = esc(위험.말) + (위험.전화 ? '<br><a href="tel:' + esc(위험.전화) + '">' + esc(위험.전화) + '</a>' : '');
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
    ko: { hr: ['(24시간)', '(상담 시간은 지역마다 달라요)'], s: function (e) { return '스스로 해치려고 약을 먹었거나, 깨우기 어렵거나, 숨쉬기 어렵거나, 경련하면 지금 ' + e + '에 전화하세요. 혼자 있지 말고 직접 운전하지 마세요. 약 상자와 남은 약을 챙기세요.'; }, p: function (P, e) { return '실수로 많이 먹었고 깨어 있고 숨을 평소처럼 쉬면, 증상이 없어도 지금 ' + P + '에 연락하세요. 스스로 해치려고 먹었거나 숨쉬기 어렵거나 경련·쓰러짐·깨우기 어려움이 있으면 ' + e + '. 억지로 토하게 하지 마시고, 약 상자와 남은 약을 챙기세요. 아세트아미노펜은 처음엔 멀쩡해도 몇 시간~며칠 뒤 간이 상할 수 있어요.'; }, o: function (e) { return '약을 너무 많이 먹었거나 아이가 약을 주워 먹었다면 증상이 없어도 지금 ' + e + '에 연락하세요. 억지로 토하게 하지 마시고, 약 상자와 남은 약을 챙기세요. 직접 운전해서 가지 마세요. 아세트아미노펜은 처음엔 멀쩡해도 몇 시간~며칠 뒤 간이 상할 수 있어요.'; }, m: function (p, e) { return '많이 힘드시군요. 혼자 견디지 마세요 — 지금 ' + p + '에 전화하면 바로 이야기를 들어 줘요(24시간). 위험이 급하면 ' + e + '.'; }, b: function (e) { return '3개월이 안 된 아기가 38℃ 이상이면 해열제보다 진료가 먼저예요. 지금 응급실로 가거나 ' + e + '에 전화하세요.'; }, h: function (e) { return '41℃ 이상이면 지금 응급실로 가거나 ' + e + '에 전화하세요.'; }, c: function (e) { return '항암 치료 중 38℃ 이상은 바로 병원에 알려야 하는 열이에요. 치료받는 병원 응급 연락처나 ' + e + '로.'; }, r: function (e) { return '약보다 진료가 먼저예요. 지금 ' + e + '에 전화하거나 응급실로 가세요. 직접 운전하지 마세요.'; } },
    en: { hr: [' (24 hours)', ' (hours vary by region)'], s: function (e) { return 'If the medicine was taken to self-harm, or the person is hard to wake, has trouble breathing or is having a seizure, call ' + e + ' now. Do not stay alone and do not drive yourself. Bring the medicine box and any pills left.'; }, p: function (P, e) { return 'If this was accidental and the person is awake and breathing normally, call ' + P + ' now, even if there are no symptoms. For intentional self-harm, trouble breathing, seizures, collapse or difficulty waking, call ' + e + '. Do not make yourself vomit. Bring the medicine box and any pills left. With acetaminophen you can feel fine at first, but liver damage can show up hours to days later.'; }, o: function (e) { return 'If you took too much, call ' + e + ' now for advice even if you feel fine. Do not make yourself vomit. Bring the medicine box and any pills left. Do not drive yourself. With acetaminophen you can feel fine at first, but liver damage can show up hours to days later.'; }, m: function (p, e) { return "It sounds like things are really hard right now. You don't have to face this alone — call " + p + ' now to talk to someone (24 hours). If you are in immediate danger, call ' + e + '.'; }, b: function (e) { return 'A baby under 3 months with a temperature of 38°C or higher needs a doctor before any fever medicine. Go to the emergency room now or call ' + e + '.'; }, h: function (e) { return 'A temperature of 41°C or higher needs the emergency room now — or call ' + e + '.'; }, c: function (e) { return 'A temperature of 38°C or higher during cancer treatment must be reported right away. Call your treatment hospital’s emergency line or ' + e + '.'; }, r: function (e) { return 'See a doctor before taking any medicine. Call ' + e + ' or go to the emergency room now. Do not drive yourself.'; } },
    es: { hr: [' (24 horas)', ' (el horario varía según la región)'], s: function (e) { return 'Si tomó el medicamento para hacerse daño, o si cuesta despertarle, respira con dificultad o tiene convulsiones, llame ahora al ' + e + '. No se quede solo y no conduzca usted mismo. Lleve la caja del medicamento y las pastillas que queden.'; }, p: function (P, e) { return 'Si la ingestión fue accidental y la persona está consciente y respira con normalidad, llame ahora ' + P + ', aunque no tenga síntomas. Si fue para hacerse daño o hay dificultad para respirar, convulsiones, desmayo o cuesta despertarla, llame al ' + e + '. No se provoque el vómito. Lleve la caja del medicamento y las pastillas que queden. Con el paracetamol puede sentirse bien al principio, pero el daño en el hígado puede aparecer horas o días después.'; }, o: function (e) { return 'Si ha tomado demasiado, llame ahora al ' + e + ' para que le orienten, aunque se encuentre bien. No se provoque el vómito. Lleve la caja del medicamento y las pastillas que queden. No conduzca usted mismo. Con el paracetamol puede sentirse bien al principio, pero el daño en el hígado puede aparecer horas o días después.'; }, m: function (p, e) { return 'Parece que está pasando por un momento muy difícil. No tiene que afrontarlo solo: llame ahora al ' + p + ' para hablar con alguien (24 horas). Si corre peligro inmediato, llame al ' + e + '.'; }, b: function (e) { return 'Un bebé de menos de 3 meses con 38 °C o más necesita atención médica antes que cualquier antitérmico. Vaya a urgencias ahora o llame al ' + e + '.'; }, h: function (e) { return 'Con 41 °C o más, vaya a urgencias ahora o llame al ' + e + '.'; }, c: function (e) { return 'Durante un tratamiento contra el cáncer, 38 °C o más debe comunicarse enseguida. Llame al teléfono de urgencias de su hospital o al ' + e + '.'; }, r: function (e) { return 'Antes que cualquier medicamento, necesita atención médica. Llame ahora al ' + e + ' o vaya a urgencias. No conduzca usted mismo.'; } },
    ja: { hr: ['（24時間）', '（受付時間は地域によって異なります）'], s: function (e) { return '自分を傷つける目的で薬を飲んだ場合や、起こしても起きにくい・呼吸が苦しい・けいれんしている場合は、今すぐ ' + e + ' に電話してください。ひとりにならず、ご自分で運転しないでください。薬の箱と残りの薬を手元に置いてください。'; }, p: function (P, e) { return '誤って飲みすぎ、意識がはっきりしていて呼吸も普段どおりなら、症状がなくても' + P + 'へすぐ相談してください。自分を傷つける目的で飲んだ場合や、意識・呼吸の異常、けいれんがある場合は ' + e + ' へ。無理に吐かせず、薬の箱と残りの薬を手元に置いてください。アセトアミノフェンは最初は何ともなくても、数時間〜数日後に肝臓が傷むことがあります。'; }, o: function (e) { return '飲みすぎた場合は、平気そうでも今すぐ ' + e + ' に電話して相談してください。無理に吐かせないでください。薬の箱と残りの薬を持って行き、ご自分で運転しないでください。アセトアミノフェンは最初は何ともなくても、数時間〜数日後に肝臓が傷むことがあります。'; }, m: function (p, e) { return 'とてもつらい状態なのですね。ひとりで抱え込まないでください。今すぐ ' + p + ' に電話すれば話を聞いてもらえます（24時間）。命の危険が迫っているときは ' + e + ' へ。'; }, b: function (e) { return '生後3か月未満の赤ちゃんが38℃以上なら、解熱剤より先に受診が必要です。今すぐ救急外来へ行くか ' + e + ' に電話してください。'; }, h: function (e) { return '41℃以上なら今すぐ救急外来へ行くか ' + e + ' に電話してください。'; }, c: function (e) { return 'がん治療中の38℃以上の熱はすぐに病院へ連絡が必要です。治療中の病院の緊急連絡先か ' + e + ' へ。'; }, r: function (e) { return '薬より先に受診が必要です。今すぐ ' + e + ' に電話するか救急外来へ行ってください。ご自分で運転しないでください。'; } },
    zh: { hr: ['（24小时）', '（服务时间因地区而异）'], s: function (e) { return '如果是为了伤害自己而服药，或者叫不醒、呼吸困难、抽搐，请立即拨打 ' + e + '。不要独处，不要自己开车。请带上药盒和剩下的药。'; }, p: function (P, e) { return '如果是误服过量，且人清醒、呼吸正常，即使没有症状也请现在联系' + P + '。如果是为了伤害自己而服药，或出现呼吸困难、抽搐、昏倒、叫不醒，请拨打 ' + e + '。不要催吐，请带上药盒和剩下的药。对乙酰氨基酚刚开始可能没有不适，但数小时到数天后可能出现肝损伤。'; }, o: function (e) { return '如果服用过量，即使感觉没事，也请现在拨打 ' + e + ' 咨询。不要催吐。请带上药盒和剩下的药，不要自己开车。对乙酰氨基酚刚开始可能没有不适，但数小时到数天后可能出现肝损伤。'; }, m: function (p, e) { return '听起来您现在非常难受。请不要一个人扛着——现在拨打 ' + p + '，会有人倾听您（24小时）。如果情况紧急，请拨打 ' + e + '。'; }, b: function (e) { return '不满3个月的婴儿体温达到38°C或以上，应先就医，而不是先用退烧药。请立即去急诊或拨打 ' + e + '。'; }, h: function (e) { return '体温达到41°C或以上，请立即去急诊或拨打 ' + e + '。'; }, c: function (e) { return '抗癌治疗期间体温达到38°C或以上，需要立即告知医院。请联系治疗医院的急诊电话或拨打 ' + e + '。'; }, r: function (e) { return '比起用药，您需要先就医。请立即拨打 ' + e + ' 或去急诊。请不要自己开车。'; } }
  };
  function 위험(글, 값) {
    var t = String(글 || ''), N = (window.I18N && window.I18N.emg) || { e: '119', m: ['109', '1577-0199'] }, M = 위험말[window.LANG] || 위험말.ko, p = N.m[0] || N.e;
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
      box.innerHTML = h;
    }).catch(function () { box.innerHTML = '<p class="small muted">목록을 못 읽었어요 — 인터넷이 될 때 다시 열어 주세요.</p>'; });
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
  <h2 class="cs-h">시작하기 전에 동의를 받아요</h2>
  <button type="button" class="cs-row cs-all" role="checkbox" aria-checked="${both ? 'true' : (동의칸.terms || 동의칸.privacy) ? 'mixed' : 'false'}" onclick="동의누름('all')"><span class="cs-bx">${I.check}</span><span class="cs-tx"><b>모두 동의해요</b><span>아래 필수 두 가지를 한 번에 체크해요</span></span></button>
  ${동의줄('terms', '이용약관', '의료기기가 아니에요. 약 정보를 드리고 기록을 도와요. 약을 고르고 드시는 결정은 의사·약사와 함께 하세요.', [
    '약 설명은 <b>식약처 허가 설명서</b>가 기본이에요. 해외 지침이나 진료실 관행이 다르면 둘 다 보여 드려요.',
    '위험 신호가 있으면 약보다 진료가 먼저예요. 급하면 119예요.',
    '약을 팔거나 건네지 않아요. 약은 약국에서 약사와 상의해 사세요.',
    '계정은 고르실 수 있고, 만 14세 이상만 만들 수 있어요.',
    '지금은 돈을 내는 기능이 없어요. 생기면 요금과 해지·환불 조건을 미리 알리고 따로 동의를 받아요.'], '약관 전문 보기')}
  ${동의줄('privacy', '개인정보 처리방침', '드시는 약·기록·몸 상태는 먼저 쓰시는 휴대폰에 저장되고, 광고·분석에 쓰지 않아요. 계정을 만들고 따로 동의하실 때만 메디나눔 서버(서울)에 복사돼요.', [
    '로그인하지 않고도 대부분의 기능을 쓰실 수 있어요.',
    '광고나 이용자 분석 도구를 넣게 되면 먼저 알려요.',
    '서버 저장은 계정을 만들 때 「서버에 저장하기」에 따로 동의하셔야 해요. 거두시면 서버 기록을 바로 지워요.',
    '「부모님께 보내기」를 링크로 보내실 때만 고른 약 목록·호칭·메모가 7일 동안 서버에 머문 뒤 지워져요.',
    '약 사진은 휴대폰 안에서 글자를 읽는 데만 쓰고 보내지 않아요.',
    '기록은 내 정보 → 설정에서 언제든 지우실 수 있어요.'], '전문 보기')}
  <button type="button" class="door-go" id="csGo" onclick="동의하기()"${both ? '' : ' disabled'} aria-describedby="csWhy">${다시 ? '동의하고 계속하기' : '동의하고 시작하기'}</button>
  <p class="door-why" id="csWhy"${both ? ' hidden' : ''}>필수 두 가지에 체크하시면 눌려요</p>
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
window.계정카드 = () => { if (D.meta?.account !== true) return ''; const 나 = srvLoggedIn(), m = 나 ? (서버.세션()?.user?.email || '') : '';
  if (!나) return `<section class="sec card acct-card"><div class="acct-hd"><span class="acct-ic" aria-hidden="true">${I.user}</span><span><b>메디나눔 계정</b><small>폰을 바꿔도 약통·복용 기록을 이어 봐요 · 선택</small></span></div>
    <button type="button" class="btn primary acct-go" onclick="go('/login')">로그인 · 계정 만들기</button></section>`;
  return `<section class="sec card acct-card"><div class="acct-hd"><span class="acct-av" aria-hidden="true">${esc(m.charAt(0).toUpperCase())}</span><span><b>${esc(m)}</b><small>로그인돼 있어요 · 이어 보기 켜짐</small></span></div>
    ${window.이용권줄HTML ? 이용권줄HTML() : ''}
    <div class="acct-act"><button type="button" class="btn line" onclick="계정동작('sync')">지금 맞추기</button><button type="button" class="btn line" onclick="계정동작('logout');setTimeout(route,600)">로그아웃</button></div>
    <button type="button" class="srvlink acct-del" onclick="go('/me?t=set');setTimeout(()=>document.getElementById('acct')?.scrollIntoView({block:'start'}),300)">계정 지우기·동의 거두기는 아래 「계정」 칸에서</button></section>`; };
window.계정줄 = () => D.meta?.account !== true ? '' : `<div class="rows-l acct-row">${srvLoggedIn() ? lrow(I.user, '메디나눔 계정', esc((서버.세션()?.user?.email || '') + ' · 이어 보기 켜짐'), "go('/login')") : lrow(I.user, '계정 만들기 · 로그인 <em class="door-tag">선택</em>', '폰을 바꿔도 이어 봐요', "go('/login')")}</div>`;
window.처음계정 = () => D.meta?.account !== true || srvLoggedIn() ? '' : `<div class="hello-acct"><b>계정 만들기 · 로그인 <em class="door-tag">선택</em></b><span>폰을 바꿔도 이어 봐요</span>
  <div class="actions two"><button class="btn line" onclick="helloFinish();go('/login')">${I.user} 로그인</button><button class="btn ghost" onclick="helloFinish()">나중에</button></div></div>`;
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
.door-s{text-align:center;color:var(--muted);margin-top:6px;font-size:.9375rem}
.cs-new{display:flex;gap:10px;align-items:flex-start;margin-top:18px;padding:12px 14px;border-radius:12px;background:var(--accent-tint);color:var(--accent-text);font-size:.9375rem;font-weight:600;line-height:1.55}
.cs-new svg.i{margin-top:2px}
.cs-list{list-style:none;margin:20px 0 0;padding:2px 16px;background:var(--card);border:1px solid var(--hairline);border-radius:var(--r-card);box-shadow:var(--shadow-card)}
.cs-list li{display:flex;gap:12px;align-items:flex-start;padding:13px 0;line-height:1.6;color:var(--body);font-size:.9375rem}
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
.door-social{display:flex;flex-direction:column;gap:8px}.door-social button{min-height:50px;border-radius:12px;border:1.5px solid var(--ui-line);font-weight:700}
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
  <p style="margin-top:6px">약국·진료실에서 자주 듣는 질문에, <b>이 앱을 검수하는 응급실 의사가 실제로 하는 대답</b>을 그대로 옮겼어요. 모두 ${A.length}가지.</p>
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

/* 내 정보·동의·로그인·약관 화면을 보고 있었으면 다시 그린다(이 파일이 늦게 오므로) */
try { if (/^#\/(me|consent|login|doc|hello\/3|supp$|supp\?|sgoal|sstage|rx|about|search|myths|askdoc|talk|p\/|p\?|p$)/.test(location.hash)) route(); } catch (e) {}
