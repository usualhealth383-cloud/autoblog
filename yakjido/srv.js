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
        + '<button type="button" class="srvlink" onclick="window.계정&&계정.지우기?계정.지우기():계정동작(\'delete\')">계정 지우기 — 약지도의 서버 기록을 지웁니다</button>';
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
                 기본:'year',                                     // (11-13) 결제 화면 주 단추 — 'year'(기본) | 'month'
                 가격:{ 월:4900, 연:39900, 학생연:29900,                 // 월만 꼭. 연·학생월·학생연은 있으면 막힘 시트·관리 화면에 함께 보인다(11-13 — 학생 월 상품 없음)
                        출시:null },                                     // 출시 기념가 — 11-13 앱 하나는 없앰(있으면 한 줄 더)
                 회원권:{ 월:12900, 연:99000, 출시월:9900, 출시연:79000, 판매:false },   // 다섯 앱 공용. 판매:false 면 「곧 열려요」
                 잠금:{ sync:'서버 동기화·여러 기기', lab:{ ko:'검사 추이', en:'Lab trends' }, … },   // id → 화면에 보일 이름(글 또는 {ko,en})
                 응급:['crisis', …],                                // 늘 열림(기본 목록에 더해진다)
                 면제:function(){ return false; },                  // 길동무: 확인된 환자
                 계정:true,                                         // 계정(로그인) 화면이 없는 앱은 false — 로그인·체험 시작 글/단추를 감추고
                                                                    //   「계정이 열리면 체험을 시작할 수 있어요」로 사실대로
                 말:function(){ return 'ko'; },                     // 'ko' | 'en' — 부품 글 두 벌 중 고른다(CS: 앱의 ko())
                 문구:{ 응급안내:'…', 막힘앞:'…', 막힘뒤:'…', 관리뒤:'…',   // ⬅ 앱별 말 끼울 자리(HTML · {ko,en} · function(id, 말){…})
                        학생:{ko:'학생·수련의', en:'students and trainees'}, 학생조건:{ko:'학교·병원 메일 인증 뒤', en:'…'} },
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
     화면:    구독.전환카드HTML() (홈 맨 위 · 체험 끝 3일 전부터) · 구독.체험끝줄HTML() (홈 한 줄을 따로 둘 때) · 구독.관리HTML() (설정) · 구독.가입동의HTML() (가입 화면)
   ⚠️ 서버 동기화 잠금은 서버 부품이 `동기화허용` 갈고리를 받을 때만 자동 동기화까지 멈춘다(곁에 서버 부품에 있음).
      이 부품은 「지금 동기화」 단추(계정동작('sync'))와 가입 동의 체크만 감싼다.
   ⚠️ 영어 글도 우리말과 같은 금지 낱말 규칙을 따른다(요금이 없다는 뜻의 낱말을 쓰지 않는다).
   판 2026-09-23b(검수 #7) — 결제사 없을 때 「결제됩니다」 대신 「다시 동의를 받아요」 · 잠금 이름 뒤 조사(은/는)를 받침으로 고른다.
     검증은 구독.판 으로 새 부품인지 본다(다시 심기 전 앱은 구독.판 이 없다).
   판 2026-11-13c — 체험 끝 3일 전 알림(약지도에서 옮김 · 약관 「자동 결제 전 알림」 약속). 구독.체험끝날() · 구독.체험끝줄HTML() (홈 한 줄) ·
    기기 알림은 부품이 스스로 건다 — 안드로이드 예약 알림(Capacitor LocalNotifications, 허락받은 경우만) · 웹 알림(탭이 열려 있고 허락받은 경우만).
    해지 예약자·스위치 꺼짐이면 아무것도 없다. 전환 카드도 3일 전부터(전엔 2일).
  판 2026-11-13d — 알림 번호 864003 → 2864003. 864003 은 약지도 「내 약 알림(<900000)」 범위라 그 앱의 옛 알림 지우기에 걸렸다(Main 11-13).
    지금 앱들이 쓰는 범위: 알림 부품 100000~189999 · 990001 · 길동무 200000~289999·300000000~1199999999 · 약지도 <900000 — 2,000,000번대는 비어 있다. extra.구독 표시는 그대로.
  판 2026-11-03 — 체험 14일(약관 11-29-1 덧붙임 · Main 11-03). 판 2026-10-08(결제 다리) — 스토어 껍데기(_껍데기/src/껍데기.js)가 window.껍데기.결제 를 내놓으면 결제 자리를 그것으로 쓴다(앱 설치 줄은 그대로 결제사:null).
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
  var 판 = '2026-11-13d';
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
      회원권권함: '앱을 3개 이상 쓰시면 메디나눔 회원권이 더 알뜰해요 — 다섯 앱을 월 {회원권값}에', 회원권보기: '회원권 보기',
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
              used_account: '이 계정은 14일 체험을 이미 쓰셨어요.', used_device: '이 기기에서는 14일 체험을 이미 쓰셨어요.', used_person: '이 계정의 메일이나 로그인 정보로 14일 체험을 이미 쓰셨어요.',
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
      체험끝줄: '14일 체험이 {n}일 뒤 끝나요 · 요금·해지 방법 보기', 체험끝줄내일: '14일 체험이 내일 끝나요 · 요금·해지 방법 보기', 체험끝줄오늘: '14일 체험이 오늘 끝나요 · 요금·해지 방법 보기', 체험끝제목: '체험이 3일 뒤 끝나요', 체험끝몸: '이어 쓰지 않으시려면 {날} 전에 해지하세요. 요금과 해지 방법은 앱의 구독 화면에 있어요.', 
      연시작: '1년으로 시작 · {값}', 연구독: '1년으로 구독 · {값}', 월시작: '1개월로 시작 · {값}', 월구독: '1개월로 구독 · {값}', 꼴: '{값} 꼴',
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
      회원권권함: 'Using three or more apps? The MediNanum pass is better value — all five apps for {회원권값} a month', 회원권보기: 'See the pass',
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
              used_account: 'This account has already used the 14-day trial.', used_device: 'This device has already used the 14-day trial.', used_person: 'The 14-day trial has already been used with this email or sign-in.',
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
      체험끝줄: 'Your 14-day trial ends in {n} days · See price and how to cancel', 체험끝줄내일: 'Your 14-day trial ends tomorrow · See price and how to cancel', 체험끝줄오늘: 'Your 14-day trial ends today · See price and how to cancel', 체험끝제목: 'Your trial ends in 3 days', 체험끝몸: 'If you do not want to continue, cancel before {날}. The price and how to cancel are on the Subscription screen in the app.', 
      연시작: 'Start with 1 year · {값}', 연구독: 'Subscribe for 1 year · {값}', 월시작: 'Start with 1 month · {값}', 월구독: 'Subscribe for 1 month · {값}', 꼴: 'about {값}',
      동의둘: '(Required) When the 14-day trial ends on {날}, the plan you choose ({값}) will be charged. You can cancel any time before then.',
      전환둘날: 'After the 14-day trial, the plan you choose ({값}) will be charged from {날}. You can cancel any time before then.',
      복원됨: 'Purchases restored.', 복원없음: 'No purchases to restore. Please check that the Google account you bought with is signed in on this phone.'
    },
    /* 11-03 소아 요청 — es·ja·zh(다섯 앱 막힘 시트·관리·고지) */
    es: {"체험끝줄": "Su prueba de 14 días termina en {n} días · Ver precio y cómo cancelar", "체험끝줄내일": "Su prueba de 14 días termina mañana · Ver precio y cómo cancelar", "체험끝줄오늘": "Su prueba de 14 días termina hoy · Ver precio y cómo cancelar", "체험끝제목": "Su prueba termina en 3 días", "체험끝몸": "Si no quiere continuar, cancele antes del {날}. El precio y cómo cancelar están en la pantalla Suscripción de la app.", "꼴": "unos {값}", "구독": "Suscripción", "이기능": "Esta función", "잠김": "<b>{이름}</b> forma parte de la suscripción.", "응급기본": "La ayuda de urgencia siempre está abierta.", "계정으로": "La prueba empieza desde una cuenta. Inicie sesión y confirme su correo para usarlo todo durante 14 días.", "계정없음": "La prueba y la suscripción aún se están preparando. Esta función todavía no se puede abrir.", "전환날": "Tras la prueba de 14 días, se cobrará {값} a partir del {날}. Puede cancelar cuando quiera antes de esa fecha.", "전환": "Cuando termine la prueba de 14 días, se cobrará {값}. Puede cancelar cuando quiera antes.", "동의": "(Obligatorio) Cuando la prueba de 14 días termine el {날}, se cobrará {값}. Puede cancelar cuando quiera antes de esa fecha.", "체험끝": "Su prueba de 14 días ha terminado.", "기간끝": "Su periodo de suscripción ha terminado.", "기록그대로": "Todo lo que anotó sigue aquí.", "기록그대로2": "Todo lo que anotó sigue aquí.", "로그인하러": "Iniciar sesión", "닫기": "Cerrar", "체험시작": "Empezar la prueba de 14 días", "결제수단": "Añadir método de pago", "결제준비": "Los pagos aún no están configurados. Ahora no se cobra nada.", "결제준비짧게": "Los pagos aún no están configurados.", "고지첫결제": "Primer cobro: {값} el {날}, cuando termine la prueba de 14 días.", "고지첫결제날없음": "Primer cobro: {값} el día en que termine la prueba de 14 días.", "고지갱신": "Renovación: se renueva automáticamente cada {주기}. Se cobra hasta que cancele.", "고지주기월": "mes", "고지주기연": "año", "고지해지스토어": "Cancelar: cuando quiera, en la tienda donde la compró: Google Play “Pagos y suscripciones → Suscripciones”, App Store “Cuenta → Suscripciones”. Borrar la app no la cancela.", "고지해지앱": "Cancelar: cuando quiera, en la pantalla “Suscripción y pagos” de esta app. Borrar la app no la cancela.", "고지검토": "<b>Vista previa de revisión</b>: esto es lo que aparecerá sobre el botón de pago cuando se abran los pagos. Ahora no se cobra nada.", "고지복원": "Restaurar: si cambia de teléfono o reinstala, “Restaurar compra” recupera su suscripción.", "약관": "Condiciones del servicio", "처리방침": "Política de privacidad", "환불안내": "Reembolsos y cancelación", "다시동의": "Antes de que empiece cualquier pago, le mostraremos el precio y la fecha de cobro y volveremos a pedirle su consentimiento.", "동의준비": "(Obligatorio) La prueba de 14 días termina el {날}. Antes de que empiece cualquier pago, le mostraremos el precio y la fecha de cobro y volveremos a pedirle su consentimiento.", "요금": "Precio", "학생기본": "estudiantes", "학생인증준비": "la verificación llegará pronto", "학생인증단추": "Verificar que es estudiante", "출시가": "Precio de lanzamiento", "출시조건": "el primer año, si se suscribe en los 3 meses siguientes al lanzamiento", "회원권": "Pase MediNanum", "회원권설명": "un plan para las cinco apps", "회원권자격": "Las herramientas profesionales de ClinicScore se abren tras la verificación profesional", "곧": "muy pronto", "출시값": "{값} (precio de lanzamiento el primer año; {정가} desde el segundo año)", "출시값둘": "precio de lanzamiento {값} el primer año; {정가} desde el segundo año", "초대중": "<b>Acceso por invitación</b> · hasta el {날}", "초대뒤": "Durante este periodo no se cobra nada. Después vuelve a lo normal.", "회원권시작": "Empezar con el pase", "회원권연시작": "Empezar un pase de 1 año · {값}", "회원권중": "Abierto con su pase MediNanum.", "이유": {"login": "Inicie sesión primero.", "verify": "Abra primero el enlace de confirmación de su correo. La prueba empieza en una cuenta confirmada.", "used_account": "Esta cuenta ya usó la prueba de 14 días.", "used_device": "Este dispositivo ya usó la prueba de 14 días.", "used_person": "La prueba de 14 días ya se usó con este correo o inicio de sesión.", "device": "No se puede empezar la prueba en este navegador. Pruebe con otro navegador.", "app": "Algo salió mal. Inténtelo de nuevo.", "noacct": "Podrá empezar la prueba cuando se abran las cuentas."}, "체크": "Lea el aviso de cobro y marque la casilla.", "인터넷": "No hay conexión a internet. Inténtelo de nuevo cuando esté conectado.", "체험됨": "Su prueba de 14 días ha empezado. Todo está abierto hasta el {날}.", "해지취소됨": "Cancelación retirada. Su plan continúa.", "해지됨": "Cancelado. ", "까지그대로": "Puede seguir usándolo hasta el {날}.", "카드결제": "Se cobrará {값} el {날}. Si no lo desea, puede cancelar antes.", "카드준비": "Su prueba de 14 días termina el {날}. Antes de que empiece cualquier pago, le mostraremos el precio y la fecha de cobro y volveremos a pedirle su consentimiento.", "해지자세히": "Cancelar · detalles", "카드닫기이름": "Cerrar aviso de cobro", "관리로그인": "Inicie sesión para ver su suscripción.", "관리계정없음": "Cuando se abran las cuentas, podrá empezar la prueba y ver aquí su suscripción.", "아직": "Todavía no ha empezado la prueba.", "관리전환": "Tras la prueba de 14 días, se cobrará {값}. Puede cancelar cuando quiera antes.", "구독중": "Suscrito", "체험중": "En prueba", "남음": " · quedan {n} días", "까지괄호": " (hasta el {날})", "해지예약": "Cancelación programada. ", "해지예약뒤": "Puede seguir usándolo hasta el {날} y después no se cobrará nada.", "해지취소": "Deshacer la cancelación", "다음결제": "Próximo pago {날} · {값}", "해지하기": "Cancelar", "해지해도": "Aunque cancele, puede seguir usándolo hasta el {날}.", "기간끝말": "el final del periodo", "휴대폰": "Verificar por teléfono", "공동": "Verificar con certificado", "미연결": "Aún no está conectado.", "문제": "Algo salió mal.", "복원": "Restaurar compras", "다시구독": "Suscribirse de nuevo", "스토어관리": "Gestionar en la tienda", "스토어해지": "Cancele desde los ajustes de suscripción de la tienda. Aunque cancele, puede seguir usándolo hasta el {날}.", "결제취소": "Pago cancelado. No ha cambiado nada.", "결제안됨": "El pago no se completó. Inténtelo de nuevo en un momento.", "결제반영중": "Pago completado. Su suscripción aparecerá en breve. Vuelva a abrir en un momento.", "구독됨": "Su suscripción ha empezado. Ya está todo abierto.", "관리전환둘": "Tras la prueba de 14 días, se cobrará el plan que elija ({값}). Puede cancelar cuando quiera antes.", "연시작": "Empezar con 1 año · {값}", "연구독": "Suscribirse por 1 año · {값}", "월시작": "Empezar con 1 mes · {값}", "월구독": "Suscribirse por 1 mes · {값}", "동의둘": "(Obligatorio) Cuando la prueba de 14 días termine el {날}, se cobrará el plan que elija ({값}). Puede cancelar cuando quiera antes de esa fecha.", "전환둘날": "Tras la prueba de 14 días, se cobrará el plan que elija ({값}) a partir del {날}. Puede cancelar cuando quiera antes de esa fecha.", "복원됨": "Compras restauradas.", "복원없음": "No hay compras que restaurar. Compruebe que la cuenta de Google con la que compró tiene la sesión iniciada en este teléfono.", "회원권권함": "¿Usa tres apps o más? El pase MediNanum sale más a cuenta: las cinco apps por {회원권값} al mes", "회원권보기": "Ver el pase"},
    ja: {"체험끝줄": "14日間の体験はあと{n}日で終わります · 料金と解約方法を見る", "체험끝줄내일": "14日間の体験は明日で終わります · 料金と解約方法を見る", "체험끝줄오늘": "14日間の体験は今日で終わります · 料金と解約方法を見る", "체험끝제목": "体験はあと3日で終わります", "체험끝몸": "続けない場合は{날}より前に解約してください。料金と解約方法はアプリの定期購入画面にあります。", "꼴": "{값}ほど", "구독": "定期購入", "이기능": "この機能", "잠김": "<b>{이름}</b>は定期購入の機能です。", "응급기본": "緊急時の連絡はいつでも使えます。", "계정으로": "お試しはアカウントから始まります。ログインしてメールの確認を済ませると、14日間すべて使えます。", "계정없음": "お試しと定期購入はまだ準備中です。この機能はまだ開けません。", "전환날": "14日間のお試しのあと、{날}から{값}が請求されます。それまではいつでも解約できます。", "전환": "14日間のお試しが終わると{값}が請求されます。それまではいつでも解約できます。", "동의": "（必須）14日間のお試しが終わる{날}に{값}が請求されます。それまではいつでも解約できます。", "체험끝": "14日間のお試しが終わりました。", "기간끝": "定期購入の期間が終わりました。", "기록그대로": "これまでの記録はそのまま残っています。", "기록그대로2": "記録はそのまま残っています。", "로그인하러": "ログインする", "닫기": "閉じる", "체험시작": "14日間のお試しを始める", "결제수단": "支払い方法を登録", "결제준비": "支払いはまだ準備中です。今は何も請求されません。", "결제준비짧게": "支払いはまだ準備中です。", "고지첫결제": "初回の請求 — 14日間のお試しが終わる{날}に{값}。", "고지첫결제날없음": "初回の請求 — 14日間のお試しが終わる日に{값}。", "고지갱신": "更新 — {주기}ごとに自動で更新されます。解約するまで請求されます。", "고지주기월": "1か月", "고지주기연": "1年", "고지해지스토어": "解約 — 購入したストアでいつでも：Google Play「お支払いと定期購入 → 定期購入」、App Store「アカウント → サブスクリプション」。アプリを削除しても解約にはなりません。", "고지해지앱": "解約 — このアプリの「定期購入と支払い」画面でいつでも。アプリを削除しても解約にはなりません。", "고지검토": "<b>確認用プレビュー</b> — 支払いが始まると、支払いボタンの上にこの内容が表示されます。今は何も請求されません。", "고지복원": "復元 — スマホを替えたり入れ直したりしたときは「購入を復元」で定期購入が戻ります。", "약관": "利用規約", "처리방침": "個人情報の取り扱い", "환불안내": "返金と解約", "다시동의": "支払いが始まる前に、料金と請求日をお見せして、もう一度同意をいただきます。", "동의준비": "（必須）14日間のお試しは{날}に終わります。支払いが始まる前に、料金と請求日をお見せして、もう一度同意をいただきます。", "요금": "料金", "학생기본": "学生", "학생인증준비": "確認はまもなく始まります", "학생인증단추": "学生であることを確認", "출시가": "発売記念価格", "출시조건": "発売から3か月以内の登録で最初の1年間", "회원권": "メディナヌム会員パス", "회원권설명": "5つのアプリをまとめて使えるプラン", "회원권자격": "ClinicScore の専門家向け機能は、医療者の確認のあとに使えます", "곧": "まもなく開始", "출시값": "{값}（最初の1年は発売記念価格、2年目から{정가}）", "출시값둘": "発売記念価格 {값} — 最初の1年、2年目から{정가}", "초대중": "<b>招待コードでお試し中</b> · {날}まで", "초대뒤": "この期間は何も請求されません。その後は通常に戻ります。", "회원권시작": "会員パスで始める", "회원권연시작": "1年の会員パスで始める · {값}", "회원권중": "メディナヌム会員パスで使えています。", "이유": {"login": "先にログインしてください。", "verify": "先にメールの確認リンクを開いてください。確認済みのアカウントでお試しが始まります。", "used_account": "このアカウントは14日間のお試しをすでに使っています。", "used_device": "この端末は14日間のお試しをすでに使っています。", "used_person": "このメールやログイン情報で14日間のお試しをすでに使っています。", "device": "このブラウザではお試しを始められません。別のブラウザでお試しください。", "app": "問題が起きました。もう一度お試しください。", "noacct": "アカウントが使えるようになると、お試しを始められます。"}, "체크": "請求のお知らせを読んで、チェックを入れてください。", "인터넷": "インターネットにつながりません。つながってからもう一度お試しください。", "체험됨": "14日間のお試しを始めました。{날}まですべて使えます。", "해지취소됨": "解約を取り消しました。プランは続きます。", "해지됨": "解約しました。", "까지그대로": "{날}までそのまま使えます。", "카드결제": "{날}に{값}が請求されます。望まない場合は、その前に解約できます。", "카드준비": "14日間のお試しは{날}に終わります。支払いが始まる前に、料金と請求日をお見せして、もう一度同意をいただきます。", "해지자세히": "解約 · くわしく", "카드닫기이름": "請求のお知らせを閉じる", "관리로그인": "ログインすると定期購入の状態を確認できます。", "관리계정없음": "アカウントが使えるようになると、ここでお試しを始めて定期購入を確認できます。", "아직": "まだお試しを始めていません。", "관리전환": "14日間のお試しのあと、{값}が請求されます。それまではいつでも解約できます。", "구독중": "定期購入中", "체험중": "お試し中", "남음": " · 残り{n}日", "까지괄호": "（{날}まで）", "해지예약": "解約を予約しました。", "해지예약뒤": "{날}までそのまま使え、その後は請求されません。", "해지취소": "解約を取り消す", "다음결제": "次回の支払い {날} · {값}", "해지하기": "解約する", "해지해도": "解約しても{날}までは使えます。", "기간끝말": "期間の終わり", "휴대폰": "電話番号で確認", "공동": "証明書で確認", "미연결": "まだつながっていません。", "문제": "問題が起きました。", "복원": "購入を復元", "다시구독": "もう一度購入する", "스토어관리": "ストアで管理", "스토어해지": "ストアの定期購入設定から解約してください。解約しても{날}までは使えます。", "결제취소": "支払いを取り消しました。何も変わっていません。", "결제안됨": "支払いが完了しませんでした。少ししてからもう一度お試しください。", "결제반영중": "支払いが完了しました。まもなく定期購入が表示されます。少ししてから開き直してください。", "구독됨": "定期購入が始まりました。すべて使えます。", "관리전환둘": "14日間のお試しのあと、選んだ料金（{값}）が請求されます。それまではいつでも解約できます。", "연시작": "1年で始める · {값}", "연구독": "1年で購入する · {값}", "월시작": "1か月で始める · {값}", "월구독": "1か月で購入する · {값}", "동의둘": "（必須）14日間のお試しが終わる{날}に、選んだ料金（{값}）が請求されます。それまではいつでも解約できます。", "전환둘날": "14日間のお試しのあと、{날}から選んだ料金（{값}）が請求されます。それまではいつでも解約できます。", "복원됨": "購入を復元しました。", "복원없음": "復元できる購入がありません。購入したGoogleアカウントがこのスマホでログインしているか確認してください。", "회원권권함": "アプリを3つ以上使うなら、メディナヌム会員パスがお得です — 5つのアプリが月{회원권값}で", "회원권보기": "会員パスを見る"},
    zh: {"체험끝줄": "14天体验还有{n}天结束 · 查看价格和取消方法", "체험끝줄내일": "14天体验明天结束 · 查看价格和取消方法", "체험끝줄오늘": "14天体验今天结束 · 查看价格和取消方法", "체험끝제목": "体验还有3天结束", "체험끝몸": "如果不想继续，请在{날}之前取消。价格和取消方法在应用的订阅页面。", "꼴": "约{값}", "구독": "订阅", "이기능": "这个功能", "잠김": "<b>{이름}</b>属于订阅功能。", "응급기본": "紧急求助始终开放。", "계정으로": "试用从账号开始。登录并完成邮箱确认后，14 天内可使用全部功能。", "계정없음": "试用和订阅仍在准备中。这个功能暂时还不能打开。", "전환날": "14 天试用结束后，将从{날}起收取{값}。在此之前可随时取消。", "전환": "14 天试用结束后将收取{값}。在此之前可随时取消。", "동의": "（必选）14 天试用于{날}结束时将收取{값}。在此之前可随时取消。", "체험끝": "14 天试用已结束。", "기간끝": "订阅期已结束。", "기록그대로": "您记下的内容都还在。", "기록그대로2": "记录都还在。", "로그인하러": "去登录", "닫기": "关闭", "체험시작": "开始 14 天试用", "결제수단": "添加付款方式", "결제준비": "付款尚未开通。现在不会收取任何费用。", "결제준비짧게": "付款尚未开通。", "고지첫결제": "首次扣款——14 天试用结束的{날}收取{값}。", "고지첫결제날없음": "首次扣款——14 天试用结束当天收取{값}。", "고지갱신": "续订——每{주기}自动续订。取消前会持续扣款。", "고지주기월": "个月", "고지주기연": "年", "고지해지스토어": "取消——可随时在购买的应用商店取消：Google Play「付款和订阅 → 订阅」，App Store「账户 → 订阅」。删除应用不会取消订阅。", "고지해지앱": "取消——可随时在本应用的「订阅与付款」页面取消。删除应用不会取消订阅。", "고지검토": "<b>审核预览</b>——开通付款后，付款按钮上方会显示这些内容。现在不会收取任何费用。", "고지복원": "恢复——换手机或重新安装时，点「恢复购买」即可找回订阅。", "약관": "服务条款", "처리방침": "隐私政策", "환불안내": "退款与取消", "다시동의": "在开始任何扣款之前，我们会向您展示价格和扣款日期，并再次征得您的同意。", "동의준비": "（必选）14 天试用于{날}结束。在开始任何扣款之前，我们会向您展示价格和扣款日期，并再次征得您的同意。", "요금": "价格", "학생기본": "学生", "학생인증준비": "认证即将开放", "학생인증단추": "认证学生身份", "출시가": "上线纪念价", "출시조건": "上线 3 个月内订阅，第一年适用", "회원권": "MediNanum 会员卡", "회원권설명": "五个应用通用的方案", "회원권자격": "ClinicScore 专业工具需通过医务人员认证后开放", "곧": "即将开放", "출시값": "{값}（第一年为上线纪念价，第二年起{정가}）", "출시값둘": "上线纪念价{값}——第一年，第二年起{정가}", "초대중": "<b>邀请码试用中</b> · 至{날}", "초대뒤": "此期间不收取任何费用。之后恢复正常。", "회원권시작": "用会员卡开始", "회원권연시작": "开始 1 年会员卡 · {값}", "회원권중": "已通过 MediNanum 会员卡开放。", "이유": {"login": "请先登录。", "verify": "请先打开邮件中的确认链接。试用从已确认的账号开始。", "used_account": "这个账号已使用过 14 天试用。", "used_device": "这台设备已使用过 14 天试用。", "used_person": "这个邮箱或登录信息已使用过 14 天试用。", "device": "无法在这个浏览器中开始试用。请换一个浏览器。", "app": "出了点问题。请再试一次。", "noacct": "账号开放后即可开始试用。"}, "체크": "请阅读扣款说明并勾选。", "인터넷": "无法连接网络。联网后请再试一次。", "체험됨": "14 天试用已开始。至{날}可使用全部功能。", "해지취소됨": "已撤回取消。您的方案将继续。", "해지됨": "已取消。", "까지그대로": "至{날}仍可继续使用。", "카드결제": "将于{날}收取{값}。如不需要，可在此之前取消。", "카드준비": "14 天试用于{날}结束。在开始任何扣款之前，我们会向您展示价格和扣款日期，并再次征得您的同意。", "해지자세히": "取消 · 详情", "카드닫기이름": "关闭扣款说明", "관리로그인": "登录后可查看订阅状态。", "관리계정없음": "账号开放后，可在这里开始试用并查看订阅。", "아직": "您还没有开始试用。", "관리전환": "14 天试用结束后将收取{값}。在此之前可随时取消。", "구독중": "订阅中", "체험중": "试用中", "남음": " · 剩余 {n} 天", "까지괄호": "（至{날}）", "해지예약": "已预约取消。", "해지예약뒤": "至{날}仍可使用，之后不再扣款。", "해지취소": "撤回取消", "다음결제": "下次扣款 {날} · {값}", "해지하기": "取消订阅", "해지해도": "即使取消，至{날}仍可使用。", "기간끝말": "期满", "휴대폰": "用手机认证", "공동": "用证书认证", "미연결": "尚未连接。", "문제": "出了点问题。", "복원": "恢复购买", "다시구독": "重新订阅", "스토어관리": "在商店管理", "스토어해지": "请在应用商店的订阅设置中取消。即使取消，至{날}仍可使用。", "결제취소": "已取消付款。没有任何变化。", "결제안됨": "付款未完成。请稍后再试。", "결제반영중": "付款完成。订阅很快就会显示。请稍后重新打开。", "구독됨": "订阅已开始。现在全部开放。", "관리전환둘": "14 天试用结束后，将收取您选择的方案（{값}）。在此之前可随时取消。", "연시작": "按 1 年开始 · {값}", "연구독": "订阅 1 年 · {값}", "월시작": "按 1 个月开始 · {값}", "월구독": "订阅 1 个月 · {값}", "동의둘": "（必选）14 天试用于{날}结束时，将收取您选择的方案（{값}）。在此之前可随时取消。", "전환둘날": "14 天试用结束后，将从{날}起收取您选择的方案（{값}）。在此之前可随时取消。", "복원됨": "已恢复购买。", "복원없음": "没有可恢复的购买。请确认购买时使用的 Google 账号已在这台手机上登录。", "회원권권함": "使用三个及以上应用时，Medinanum 会员更划算——五个应用每月{회원권값}", "회원권보기": "查看会员"}
  };
  var 달이름 = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function 말() { try { var l = typeof 설정.말 === 'function' ? 설정.말() : 'ko'; if (l === 'en' || l === 'es' || l === 'ja' || l === 'zh') return l; } catch (e) {} return 'ko'; }   /* 11-03 다섯 말 */
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
  function 원(n) { n = Number(n || 0); var l = 말(); return l === 'ko' ? n.toLocaleString('ko-KR') + '원' : '₩' + n.toLocaleString(l === 'es' ? 'es-ES' : 'en-US'); }
  function 월값(n) { n = n == null ? (설정.가격 || {}).월 : n; var l = 말(); return l === 'en' ? 원(n) + '/month' : l === 'es' ? 원(n) + ' al mes' : l === 'ja' ? '月額' + 원(n) : l === 'zh' ? '每月' + 원(n) : '월 ' + 원(n); }
  function 연값(n) { var l = 말(); return l === 'en' ? 원(n) + '/year' : l === 'es' ? 원(n) + ' al año' : l === 'ja' ? '年額' + 원(n) : l === 'zh' ? '每年' + 원(n) : '연 ' + 원(n); }
  function 날(t) { var d = new Date(t), l = 말(); return l === 'en' ? 달이름[d.getMonth()] + ' ' + d.getDate() : l === 'es' ? d.getDate() + ' de ' + ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'][d.getMonth()] : (l === 'ja' || l === 'zh') ? (d.getMonth() + 1) + '月' + d.getDate() + '日' : (d.getMonth() + 1) + '월 ' + d.getDate() + '일'; }
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
  /* 11-13 현욱님 — 결제 화면 기본 선택은 1년(월 환산 함께). 설정.기본: 'month' 이면 예전처럼 1개월이 주 단추 */
  function 연기본() { return 연있나() && (!!설정.기본연 || 설정.기본 !== 'month'); }
  function 연환산() { var g = 설정.가격 || {}; return g.연 ? ' (' + 말글('꼴', { 값: 월값(Math.round(g.연 / 12)) }) + ')' : ''; }
  function 시작단추(부르기) {   /* 부르기: 'subscribe' → 체험시작 · 'again' → 결제등록 */
    var 함 = 부르기 === 'again' ? '구독.결제등록' : '구독.체험시작';
    if (연기본()) return 단추(말글(부르기 === 'again' ? '연구독' : '연시작', { 값: 첫연값() + 연환산() }), 함 + "('year')", true) + 단추(말글(부르기 === 'again' ? '월구독' : '월시작', { 값: 첫월값() }), 함 + '()', false);
    if (부르기 === 'again') return 단추(말글('다시구독'), 함 + '()', true) + (연있나() ? 단추(말글('연구독', { 값: 첫연값() }), 함 + "('year')", false) : '');
    return 단추(말글('체험시작'), 함 + '()', true) + (연있나() ? 단추(말글('연시작', { 값: 첫연값() }), 함 + "('year')", false) : '');
  }
  function 연있나() { return !!(껍데기결제() && 설정.가격 && 설정.가격.연); }   /* 2026-10-13 — 스토어 길에서 1년 이용권도 판다 */
  function 연먼저() { return 연기본(); }   /* 11-12 곁에(기본연:true) 와 11-13 기본 연 — 같은 판단 하나로 */
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
    w = String(w || '').replace(/\s*\([^()]*\)\s*$/, '').replace(/[\s.,·'"’”」\u300F]+$/, '');
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
    try { 체험알림걸기(); } catch (e) {}   /* 11-13c */
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
    v.style.cssText = 'position:fixed;left:0;right:0;bottom:0;max-height:85vh;overflow:auto;overscroll-behavior:contain;z-index:2147482000;padding:16px;background:inherit;border-top:1px solid rgba(0,0,0,.15)';
    v.innerHTML = '<div class="srvbox"><b>' + esc(제목 || '') + '</b>' + html + '</div>';
    document.body.appendChild(v); 내시트 = v;
  }
  function 시트닫기() {
    if (내시트) { try { 내시트.remove(); } catch (e) {} 내시트 = null; return; }
    if (typeof 설정.시트닫기 === 'function') { try { 설정.시트닫기(); } catch (e) {} }
  }
  function 동의줄(id) {
    var 끝 = Date.now() + 14 * 864e5;
    return '<label class="subagree"><input type="checkbox" id="' + id + '"> <span>' + (연있나() ? 말글('동의둘', { 날: 날(끝), 값: 두요금() }) : 말글(결제있나() ? '동의' : '동의준비', { 날: 날(끝), 값: 첫월값() })) + '</span></label>';
  }
  function 결제줄(s) {
    if (껍데기결제()) {
      /* 2026-10-08 스토어 결제 — 체험 전에는 「14일 체험 시작」이 곧 스토어 구매라 단추를 겹치지 않는다. 끝난 뒤(체험 끝·기간 끝)에만 「다시 구독하기」 */
      return (s && s.status && !s.열림) ? 줄(시작단추('again')) : '';
    }
    if (결제있나()) {
      /* 결제사가 붙은 뒤: 설정.결제.등록() 이 결제수단 등록 창을 연다 */
      return 줄(단추(말글('결제수단'), '구독.결제등록()', false));
    }
    return 작은(말글('결제준비'));
  }
  function 회원권권함() {
    try { if (!window.회원권 || !회원권.열기 || !설정.가격 || !설정.가격.월) return '';
      var 회 = (회원권.값표 && 회원권.값표.회원권 && 회원권.값표.회원권.월) || (설정.회원권 && 설정.회원권.월) || 12900;
      return '<p class="' + (모('작은글') || '') + '">' + 말글('회원권권함', { 앱값: 원(설정.가격.월), 회원권값: 원(회) }) + ' <button type="button" class="' + (모('보조') || '') + '" onclick="회원권.열기()">' + esc(말글('회원권보기')) + '</button></p>'; } catch (e) { return ''; }
  }
  function 막힘HTML(id) {
    var s = 상태(), 끝 = Date.now() + 14 * 864e5, 몸 = '', 단 = '', 동 = '';
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
      동 = 동의줄('subAgreeT') + 회원권권함();   /* 11-11 — 기본 선택은 누른 상품 그대로, 한 줄만 */
      단 = 시작단추('subscribe') + 단추(말글('닫기'), '구독.닫기()', false);
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
        return 조회().then(function () { 시트닫기(); 알림(말글('체험됨', { 날: 날(때(d.until) || Date.now() + 14 * 864e5) })); return true; });
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
        알림(s.열림 ? (s.status === 'trial' ? 말글('체험됨', { 날: 날(s.until || Date.now() + 14 * 864e5) }) : 말글('구독됨')) : 말글('결제반영중'));
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
  function 운영자() { try { return !!(window.가입 && 가입.운영자 && 가입.운영자()); } catch (e) { return false; } }   /* 10-30 */
  function 전환카드HTML() {
    if (!켜짐() || 운영자()) return '';
    var s = 상태(); if (s.status !== 'trial' || s.cancel || !s.열림) return '';
    var t = s.converts_at || s.until, now = Date.now(); if (!t || t <= now || t - now > 3 * 864e5) return '';   /* 11-13c 3일 전부터(약관 약속) */
    var 닫음 = null; try { 닫음 = localStorage.getItem(카드키()); } catch (e) {}
    if (닫음 === String(t)) return '';   /* 이 주기에는 이미 닫았다 */
    var 스토어 = /^(google|apple)$/.test(String(s.source || ''));   /* 2026-10-08 — 스토어에서 산 체험은 스토어가 결제수단을 쥐고 있다 */
    var 글 = ((s.pay_ready || 스토어) && 결제있나()) ? 말글('카드결제', { 날: 날(t), 값: 첫값(s) }) : 말글('카드준비', { 날: 날(t) });   /* 결제사가 없으면 서버가 pay_ready 라 해도 「결제됩니다」를 말하지 않는다 */
    return '<div class="' + 모('카드') + ' subcard" id="subcard" role="status"><p><b>' + 체험끝머리(s) + '</b></p><p>' + 글 + '</p>' +
      줄(단추(말글('해지자세히'), '구독.관리열기()', false) + 단추(말글('닫기'), '구독.카드닫기()', false, 말글('카드닫기이름'))) + '</div>';
  }

  /* ── 11-13c 체험 끝 3일 전 알림(약지도 11-12 에서 옮김) — 스위치 꺼짐·해지 예약·체험 아님이면 늘 null ── */
  function 체험끝날() {
    try { if (!켜짐()) return null; var s = 상태(); if (!s || s.status !== 'trial' || !s.until || s.cancel) return null;
      return { until: new Date(s.converts_at || s.until), days: s.days }; } catch (e) { return null; }
  }
  function 체험끝글(n) { return n > 1 ? 말글('체험끝줄', { n: n }) : n === 1 ? 말글('체험끝줄내일') : 말글('체험끝줄오늘'); }
  function 체험끝머리(s) { return 체험끝글(s && s.days).split(' · ')[0]; }
  function 체험끝줄HTML() {
    var t = 체험끝날(); if (!t || t.days == null || t.days > 3 || 운영자()) return '';
    return '<button type="button" class="' + 모('줄') + ' subline" onclick="구독.관리열기()">' + 체험끝글(t.days) + '</button>';
  }
  var 알림번호 = 2864003, 옛번호 = 864003, 웹알림틀 = null;   /* 11-13d 어느 앱 범위와도 안 겹치는 자리 */
  function 알림키() { return '_sub_te_' + 설정.app; }
  function 기기알림() { var C = window.Capacitor; if (!C) return null; var p = C.Plugins && C.Plugins.LocalNotifications;
    if (!p && typeof C.registerPlugin === 'function') { try { if (!C.isPluginAvailable || C.isPluginAvailable('LocalNotifications')) p = C.registerPlugin('LocalNotifications'); } catch (e) {} } return p || null; }
  function 체험알림걸기() {
    var t = 체험끝날(), 걸림 = null; try { 걸림 = localStorage.getItem(알림키()); } catch (e) {}
    var at = t ? new Date(t.until.getTime() - 3 * 864e5) : null; if (at) at.setHours(10, 0, 0, 0);
    if (at && at.getTime() <= Date.now()) at = null;   /* 이미 3일 안이면 홈 줄·카드가 대신한다 */
    var 열쇠 = at ? String(at.getTime()) : '';
    if (웹알림틀) { clearTimeout(웹알림틀); 웹알림틀 = null; }
    var 제목 = 말글('체험끝제목'), 몸 = t ? 말글('체험끝몸', { 날: 날(t.until) }) : '';
    /* 안드로이드 — 허락받은 경우만 건다(여기서 허락을 묻지 않는다). 바뀌었을 때만 다시 건다 */
    var LN = 기기알림();
    if (LN && 걸림 !== 열쇠) {
      Promise.resolve().then(function () { return 걸림 ? LN.cancel({ notifications: [{ id: 알림번호 }, { id: 옛번호 }] }) : null; }).catch(function () {})
        .then(function () { if (!at) return null; return LN.checkPermissions().then(function (p) { if (!p || p.display !== 'granted') return null;
          return LN.schedule({ notifications: [{ id: 알림번호, title: 제목, body: 몸, schedule: { at: at, allowWhileIdle: true }, extra: { 구독: 'trial-end' } }] }); }); })
        .then(function () { try { if (열쇠) localStorage.setItem(알림키(), 열쇠); else localStorage.removeItem(알림키()); } catch (e) {} }).catch(function () {});
    }
    /* 웹 — 탭이 열려 있는 동안만, 허락받은 경우만 */
    if (!LN && at && window.Notification && Notification.permission === 'granted') {
      var ms = at.getTime() - Date.now();
      if (ms > 0 && ms < 2147000000) 웹알림틀 = setTimeout(function () {
        if (!체험끝날()) return;
        try { if (navigator.serviceWorker && navigator.serviceWorker.ready) navigator.serviceWorker.ready.then(function (r) { r.showNotification(제목, { body: 몸, tag: 'sub-trial-end' }); }).catch(function () { new Notification(제목, { body: 몸, tag: 'sub-trial-end' }); });
          else new Notification(제목, { body: 몸, tag: 'sub-trial-end' }); } catch (e) {}
      }, ms);
    }
  }
  function 카드닫기() {
    var s = 상태(), t = s.converts_at || s.until;
    try { if (t) localStorage.setItem(카드키(), String(t)); } catch (e) {}
    var el = document.getElementById('subcard'); if (el) el.remove();
  }
  function 관리HTML() {
    if (운영자()) return '<div id="subman" class="subman"><p><b>' + (({ en: 'Operator · all features', es: 'Operador · todas las funciones', ja: '運営者 · すべての機能', zh: '运营者 · 全部功能' })[말()] || '운영자 · 모든 기능') + '</b></p></div>';   /* 10-30 — 회원권·체험 글 대신 */
    if (!켜짐()) return '';
    var s = 상태(), h = '', 스토어길 = !!껍데기결제();
    /* 2026-10-20 — 사는 자리에서만 고지한다(아직 시작 안 함 · 끝남). 구독 중이면 「다음 결제일」이 이미 말한다. */
    var 고지 = (!s.status || !s.열림) ? 결제고지(!s.status ? Date.now() + 14 * 864e5 : null) : '';
    if (!계정있나() && !스토어길) {
      h = '<p>' + 말글('관리계정없음') + '</p><p>' + (결제있나() ? 말글('관리전환', { 값: 첫월값() }) : 말글('다시동의')) + '</p>' + 요금줄();
    } else if (!스토어길 && (!서버있나() || !s.로그인)) {
      h = '<p>' + 말글('관리로그인') + '</p>' + 요금줄() + (typeof 설정.로그인열기 === 'function' ? 줄(단추(말글('로그인하러'), '구독.로그인()', true)) : '');
    } else if (!s.status) {
      h = '<p><b>' + 말글('아직') + '</b></p><p>' + (결제있나() ? (연있나() ? 말글('관리전환둘', { 값: 두요금() }) : 말글('관리전환', { 값: 첫월값() })) : 말글('다시동의')) + '</p>' + 요금줄() + 동의줄('subAgreeT') +
        고지 +
        줄(시작단추('subscribe'));
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
    ['app', '유료화', '가격', '회원권', '면제', '결제사', '결제', '인증', '시트열기', '시트닫기', '알림', '로그인열기', '바뀜', '계정', '말', '학생인증', '기본연'].forEach(function (k) { if (k in o) 설정[k] = o[k]; });
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
        '.subnotice{margin:8px 0 10px;padding:0;list-style:none;font-size:15px;line-height:1.65}' +
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
    전환카드HTML: 전환카드HTML, 카드닫기: 카드닫기, 체험끝날: 체험끝날, 체험끝줄HTML: 체험끝줄HTML, 체험알림걸기: 체험알림걸기, 관리HTML: 관리HTML, 가입동의HTML: 가입동의HTML,
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
/* ▼▼ 홈보내기 부품 시작 ▼▼ */
/* 메디나눔 홈 2단계 — 다른 주소 앱(약지도·소아·길동무 등)의 기록을 사용자가 누를 때만 「내 홈」으로 넘긴다.
   설계: _시안/메디나눔홈_설계/설계서_v2.md §9-3 · 실험: _시안/메디나눔홈_설계/어댑터_실험_1113.md
   §9-3 세 조건을 코드로 지킨다
     ① 0단계 실험 — 11-13 약지도 실제 화면 + 다른 주소 가짜 홈에서 창 메시지·파일 두 길 동작 확인(검증_홈보내기.mjs)
     ② 법무 판단 전에는 열지 않는다 — 스위치 기본 꺼짐(켜짐:false). 꺼지면 보내기·받기 모두 아무것도 하지 않는다
     ③ 보안 — 보내는 쪽은 홈 주소 하나에만 targetOrigin 을 정확히 걸고, 받는 쪽은 허용 주소 목록 + 모양 검사.
        파일 가져오기도 모양 검사를 통과한 것만 넘긴다. 글은 textContent 로만 그리도록 HTML 을 품은 글자는 거부한다.
   정본 원칙(§9-3): 원래 앱이 정본. 이 꾸러미는 «사본 보기용»이며 홈은 이걸 원래 앱에 다시 쓰지 않는다.
   쓰는 법(보내는 앱):
     홈보내기.설치({ app:'yakjido', 켜짐:false, 홈:'https://gyeote.medinanum.com/', 모으기:{ P8: function(){ return [...]; } },
                    묻기: function(요약){ return Promise.resolve(confirm(요약)); } });
     홈보내기.보내기('P8')   — 단추를 누를 때만(사용자 동작). 창이 막히거나 15초 안에 답이 없으면 파일로 내려받기.
   쓰는 법(홈):
     홈보내기.받기설치({ 켜짐:false, 허용:['https://yakjido.medinanum.com', …], 받음: function(꾸러미){ … } });
     홈보내기.파일읽기(file) → Promise<꾸러미>(모양 검사 통과만)
   판 2026-11-13a — 첫 판. */
(function () {
  'use strict';
  var 판 = '2026-11-13a';
  var 설정 = { app: '', 켜짐: false, 홈: '', 모으기: {}, 묻기: null, 말: null };
  var 받기 = { 켜짐: false, 허용: [], 받음: null, 설치됨: false };
  var 칸목록 = { P8: 1, P9: 1, P11: 1 };
  var 최대항목 = 2000, 최대글 = 80, 최대크기 = 200000;

  var 글 = {
    ko: { 요약: '{칸} {n}건을 메디나눔 「내 홈」으로 보낼까요?\n이 기기에서 홈 화면으로만 넘어가고, 서버로 가지 않아요. 원래 기록은 이 앱에 그대로 있어요.',
          P8: '혈압·혈당', P9: '체온', P11: '건강 수첩', 없음: '보낼 기록이 아직 없어요.', 꺼짐: '아직 준비 중이에요.',
          됨: '내 홈으로 보냈어요({n}건).', 파일: '창이 열리지 않아 파일로 내려받았어요. 내 홈에서 「파일 가져오기」로 넣어 주세요.' },
    en: { 요약: 'Send {n} {칸} records to your MediNanum Home?\nThey move only on this device to the Home screen, not to a server. The original records stay in this app.',
          P8: 'blood pressure and glucose', P9: 'temperature', P11: 'health notebook', 없음: 'There is nothing to send yet.', 꺼짐: 'This is not ready yet.',
          됨: 'Sent to your Home ({n}).', 파일: 'The window did not open, so a file was downloaded. Use “Import file” in your Home.' }
  };
  function 말() { try { var l = typeof 설정.말 === 'function' ? 설정.말() : 'ko'; return 글[l] ? l : (l === 'ko' ? 'ko' : 'en'); } catch (e) { return 'ko'; } }
  function 말글(k, v) { var s = (글[말()] || 글.ko)[k] || 글.ko[k] || ''; v = v || {}; return s.replace(/\{(\w+)\}/g, function (_, n) { return v[n] != null ? v[n] : ''; }); }
  function 원(u) { try { return new URL(u).origin; } catch (e) { return ''; } }

  /* ── 모양 검사 — 보내기 전과 받은 뒤 같은 함수 ── */
  var 때꼴 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
  function 수(x, lo, hi) { return typeof x === 'number' && isFinite(x) && x >= lo && x <= hi; }
  function 글자(x, 길이) { return typeof x === 'string' && x.length <= (길이 || 최대글) && !/[<>]/.test(x); }
  function 항목검사(칸, x) {
    if (!x || typeof x !== 'object' || Array.isArray(x)) return false;
    var 키 = Object.keys(x);
    if (칸 === 'P8') {
      if (!때꼴.test(x.t)) return false;
      if (x.k === 'bp') return 수(x.s, 40, 300) && 수(x.d, 20, 200) && (x.p == null || 수(x.p, 20, 250)) && (x.w == null || 글자(x.w, 10)) && 키.every(function (k) { return /^(t|k|s|d|p|w)$/.test(k); });
      if (x.k === 'bg') return 수(x.v, 10, 1000) && (x.w == null || 글자(x.w, 10)) && 키.every(function (k) { return /^(t|k|v|w)$/.test(k); });
      return false;
    }
    if (칸 === 'P9') return 때꼴.test(x.t) && 수(x.c, 30, 45) && (x.w == null || 글자(x.w, 10)) && 키.every(function (k) { return /^(t|c|w)$/.test(k); });
    if (칸 === 'P11') {
      if (!/^(allergy|med)$/.test(x.k) || !/^(list|none_confirmed|no_record)$/.test(x.state)) return false;
      if (x.state === 'list' && !(Array.isArray(x.names) && x.names.length <= 100 && x.names.every(function (n) { return 글자(n); }))) return false;
      if (x.state !== 'list' && x.names != null) return false;
      return (x.confirmed_at == null || /^\d{4}-\d{2}-\d{2}$/.test(x.confirmed_at)) && 키.every(function (k) { return /^(k|state|names|confirmed_at)$/.test(k); });
    }
    return false;
  }
  function 꾸러미검사(o) {
    try {
      if (!o || typeof o !== 'object' || o.mnx !== 1) return null;
      if (!칸목록[o.kind] || !/^[a-z]{2,20}$/.test(o.app) || o.subject !== 'self' || !/^\d{4}-\d{2}-\d{2}T/.test(o.made)) return null;
      if (!Array.isArray(o.items) || o.items.length > 최대항목) return null;
      if (Object.keys(o).some(function (k) { return !/^(mnx|app|kind|subject|made|items)$/.test(k); })) return null;
      if (JSON.stringify(o).length > 최대크기) return null;
      for (var i = 0; i < o.items.length; i++) if (!항목검사(o.kind, o.items[i])) return null;
      return { mnx: 1, app: o.app, kind: o.kind, subject: 'self', made: o.made, items: o.items.slice() };
    } catch (e) { return null; }
  }

  /* ── 보내는 쪽 ── */
  function 꾸리기(칸) {
    var f = 설정.모으기[칸]; if (typeof f !== 'function') return null;
    var items = []; try { items = (f() || []).filter(function (x) { return 항목검사(칸, x); }).slice(-최대항목); } catch (e) { items = []; }
    return 꾸러미검사({ mnx: 1, app: 설정.app, kind: 칸, subject: 'self', made: new Date().toISOString(), items: items });
  }
  function 파일로(꾸) {
    var 이름 = 'medinanum-home-' + 꾸.app + '-' + 꾸.kind + '-' + 꾸.made.slice(0, 10) + '.json';
    var b = new Blob([JSON.stringify(꾸)], { type: 'application/json' });
    try { if (navigator.canShare && window.File) { var fl = new File([b], 이름, { type: 'application/json' }); if (navigator.canShare({ files: [fl] }) && window.Capacitor) return navigator.share({ files: [fl] }).then(function () { return 'share'; }, function () { return 'cancel'; }); } } catch (e) {}
    var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 이름; document.body.appendChild(a); a.click();
    setTimeout(function () { try { URL.revokeObjectURL(a.href); a.remove(); } catch (e) {} }, 1000);
    return Promise.resolve('file');
  }
  function 창으로(꾸) {
    var 홈원 = 원(설정.홈); if (!홈원) return Promise.resolve('nohome');
    var w = null; try { w = window.open(설정.홈.split('#')[0] + '#mnx-wait', '_blank'); } catch (e) {}
    if (!w || window.Capacitor) { try { if (w) w.close(); } catch (e) {} return Promise.resolve('blocked'); }
    return new Promise(function (풀) {
      var 끝 = false, 틀 = setTimeout(function () { 마침('timeout'); }, 15000);
      function 마침(r) { if (끝) return; 끝 = true; clearTimeout(틀); window.removeEventListener('message', 귀); 풀(r); }
      function 귀(ev) {
        if (ev.origin !== 홈원 || ev.source !== w || !ev.data || typeof ev.data !== 'object') return;   /* 홈 주소·그 창에서 온 것만 */
        if (ev.data.mnx === 'ready') { try { w.postMessage(꾸, 홈원); } catch (e) { 마침('error'); } }   /* targetOrigin 을 정확히 */
        else if (ev.data.mnx === 'got') 마침(ev.data.n === 꾸.items.length ? 'ok' : 'error');
        else if (ev.data.mnx === 'refused') 마침('refused');
      }
      window.addEventListener('message', 귀);
    });
  }
  function 보내기(칸) {
    if (!설정.켜짐) { 알림(말글('꺼짐')); return Promise.resolve('off'); }
    var 꾸 = 꾸리기(칸); if (!꾸) return Promise.resolve('bad');
    if (!꾸.items.length) { 알림(말글('없음')); return Promise.resolve('empty'); }
    var 요약 = 말글('요약', { 칸: 말글(칸), n: 꾸.items.length });
    var 묻 = typeof 설정.묻기 === 'function' ? 설정.묻기(요약, 꾸) : Promise.resolve(window.confirm(요약));
    return Promise.resolve(묻).then(function (좋아) {
      if (!좋아) return 'cancel';
      return 창으로(꾸).then(function (r) {
        if (r === 'ok') { 알림(말글('됨', { n: 꾸.items.length })); return 'ok'; }
        if (r === 'refused') return 'refused';
        return 파일로(꾸).then(function (f) { if (f !== 'cancel') 알림(말글('파일')); return f; });
      });
    });
  }
  function 알림(t) { try { if (typeof 설정.알림 === 'function') 설정.알림(t); else if (typeof 잠깐말 === 'function') 잠깐말(t); else if (typeof toast === 'function') toast(t); } catch (e) {} }

  /* ── 받는 쪽(홈) ── */
  function 받기설치(o) {
    o = o || {}; 받기.켜짐 = !!o.켜짐; 받기.허용 = (o.허용 || []).map(원).filter(Boolean); 받기.받음 = o.받음;
    if (받기.설치됨) return; 받기.설치됨 = true;
    window.addEventListener('message', function (ev) {
      if (!받기.켜짐 || 받기.허용.indexOf(ev.origin) < 0 || !ev.source || ev.source !== window.opener) return;   /* 허용 주소 + 이 창을 연 앱만 */
      var 꾸 = 꾸러미검사(ev.data);
      if (!꾸) { try { ev.source.postMessage({ mnx: 'refused' }, ev.origin); } catch (e) {} return; }
      var ok = false; try { ok = 받기.받음 ? 받기.받음(꾸, ev.origin) !== false : false; } catch (e) { ok = false; }
      try { ev.source.postMessage(ok ? { mnx: 'got', n: 꾸.items.length } : { mnx: 'refused' }, ev.origin); } catch (e) {}
    });
    /* 기다림 표시(#mnx-wait)로 열렸으면 연 앱에 「준비됨」을 알린다 — 허용 주소에만 */
    try {
      if (받기.켜짐 && /#mnx-wait$/.test(location.hash) && window.opener) {
        받기.허용.forEach(function (o2) { try { window.opener.postMessage({ mnx: 'ready' }, o2); } catch (e) {} });
        history.replaceState(null, '', location.pathname + location.search);
      }
    } catch (e) {}
  }
  function 파일읽기(file) {
    return new Promise(function (풀, 막) {
      if (!받기.켜짐) return 막(new Error('off'));
      if (!file || file.size > 최대크기) return 막(new Error('size'));
      var r = new FileReader();
      r.onload = function () { var o = null; try { o = JSON.parse(String(r.result)); } catch (e) {} var 꾸 = 꾸러미검사(o); if (꾸) 풀(꾸); else 막(new Error('shape')); };
      r.onerror = function () { 막(new Error('read')); };
      r.readAsText(file);
    });
  }

  window.홈보내기 = {
    판: 판,
    설치: function (o) { o = o || {}; ['app', '켜짐', '홈', '모으기', '묻기', '말', '알림'].forEach(function (k) { if (k in o) 설정[k] = o[k]; }); 설정.모으기 = 설정.모으기 || {}; },
    켜짐: function () { return !!설정.켜짐; }, 보내기: 보내기, 꾸리기: 꾸리기,
    받기설치: 받기설치, 파일읽기: 파일읽기, 꾸러미검사: 꾸러미검사
  };
})();
/* ▲▲ 홈보내기 부품 끝 ▲▲ */
/* 11-13 메디나눔 홈 2단계 — 수첩의 혈압·혈당(P8)을 사용자가 누를 때만 「내 홈」으로 넘긴다. 스위치 꺼짐(법무 판단 전 비공개).
   원래 기록은 이 앱이 정본 — 꾸러미는 사본 보기용. 모양은 부품이 다시 검사한다 */
try {
  홈보내기.설치({ app: 'yakjido', 켜짐: false, 홈: 'https://gyeote.medinanum.com/',
    모으기: { P8: function () { return (typeof vitals === 'function' ? vitals() : []).map(function (x) {
      var o = x.k === 'bp' ? { t: x.t, k: 'bp', s: x.s, d: x.d } : x.k === 'bg' ? { t: x.t, k: 'bg', v: x.v } : null;
      if (!o) return null; if (x.k === 'bp' && x.p != null) o.p = x.p; if (x.w) o.w = x.w; return o; }).filter(Boolean)
      .sort(function (a, b) { return a.t < b.t ? -1 : a.t > b.t ? 1 : 0; }); } },
    묻기: function (요약) { return Promise.resolve(confirm(요약)); },
    말: function () { return window.LANG || 'ko'; },
    알림: function (t) { try { toast(t); } catch (e) {} } });
} catch (e) {}


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
  서버.설치({ app: 'yakjido', 동기화허용: function () { return !window.가입 || 가입.됨(); },   /* 11-11 가입 전에는 올리지 않는다 */
    열쇠: /^yakjido\.(me|fam|hx)\.v1$/, 병합: function (k, mine, theirs) { return k === 'yakjido.me.v1' && typeof mergeMe === 'function' ? mergeMe(mine, theirs) : null; },   /* 11-03 fam.v1 = 알림 설정(시간대·기다리는 시간·쉬는 시간·정시 알림) — 서버 알림 함수가 읽는다 */ 준비됨: function () { return !!(typeof D !== 'undefined' && D.meta && D.meta.account === true); }, 허용: srvAgreed, 다시그리기: srvReload,
    가입확인: { 글: '만 14세 이상이에요', 설명: '메디나눔 계정은 만 14세 이상만 만들 수 있어요. 아이 약은 보호자 계정에 담아 주세요.' },
    /* 2026-10-14 로그인 문의 「서버에 저장하기」 체크 — 설정의 서버동의켜기와 같은 꼴로 적는다 */
    동의기록: function () { try { localStorage.setItem(AGREE_KEY, JSON.stringify({ server: true, at: new Date().toISOString() })); } catch (e) {} } });
} catch (e) {}

/* 2026-10-22 공용 구독 부품(다섯 앱 같은 것) — 유료화 스위치는 끈 채로. 꺼져 있는 동안 요금·체험 글은 어디에도 나오지 않는다(되는 척 금지). 검토는 주소에 ?paywall=1.
   요금 = 10-21 결정(앱 하나 월 5,900 · 연 49,000 / 출시 기념가 4,900 · 39,900 / 회원권). 무료로 남는 것 = 10-22 현욱님 답 9번(약 찾기·약봉투 읽기·복약 알림·안전 신호·겹침 확인).
   잠금 목록 = 현욱님 10-22 답 A(기록을 쌓아 보는 것만). */
try {
  구독.설치({ app: 'yakjido', 유료화: false,
    가격: { 월: 4900, 연: 39900 },   /* 11-12 현욱님 결정 — 월 4,900 · 연 39,900, 기념가 없음 · 단건 없음(근거 yozm-health _시안/요금판단_1112/요금_yak.md) */
    회원권: { 월: 12900, 연: 99000, 출시월: 9900, 출시연: 79000, 판매: false },
    /* 11-12 현욱님 잠금 추천안 — 찾아보기·위험 경고·병용 확인·낱알 식별·약통·매일 복약 알림은 늘 열림. 이용권 = 아래 일곱. 약 개수로는 막지 않는다 */
    잠금: { family: '가족·보호자와 함께 보기', refill: '남은 약 떨어지기 전 알림', trend: '혈압·혈당 흐름 그림', visitdoc: '진료 준비 한 장(첫 장은 그냥 드려요)', sync: '여러 기기에서 이어 보기', suppcap: '영양제 상한 나란히 비교', history: '7일 넘는 복약 기록' },
    응급: ['emergency', 'redflag', 'call119', 'find', 'bag', 'schedule', 'together'],
    문구: { 응급안내: '약 찾기·위험 신호·같이 먹어도 되는지 확인·낱알로 약 찾기·약통·매일 복약 알림은 언제나 열려 있어요.', 막힘앞: function (id) { return window.회원권 ? 회원권.강조HTML(id) : ''; } },   /* 11-11 회원권 부품 */
    결제사: null, 인증: { 휴대폰: false, 공동: false },
    시트열기: function (html, 제목) { var v = document.getElementById('view'); if (!v) return; v.innerHTML = topBar({ back: '뒤로' }) + '<h1>' + esc(제목 || '구독') + '</h1>' + html; scrollTo(0, 0); },
    시트닫기: function () { route(); },
    알림: function (t) { try { toast(t); } catch (e) {} },
    로그인열기: function () { go('/login'); },
    바뀜: function () { try { if (/^#\/me/.test(location.hash)) route(); } catch (e) {} } });
} catch (e) {}
/* ▼▼ 가입 부품 시작 ▼▼ */
/* ═══ 앱별 가입 · 초대 코드 · 관리자 — 다섯 앱 공용 부품 (2026-10-21) ═══════════════════════
   요청: docs/requests/20261021_메디나눔_앱별가입·초대코드·관리자.md · 서버: _서버/메디나눔_가입초대관리_1021.sql
   · 계정은 하나(메디나눔 공용 서버), 앱 이용은 앱마다 «가입(그 앱 약관 동의)» 기록이 따로(app_members).
     다른 앱에서 만든 계정으로 처음 로그인하면 바로 들어가지 않고 「<앱> 가입」 시트를 거친다. 가입 전에는 동기화를 멈춘다(가입.됨()).
     이 앱에서 «가입 동의를 하고» 계정을 만든 분은 다시 묻지 않는다(설치 옵션 가입표시 — 앱의 가입 단추에서 가입.이앱가입() 을 부른다).
   · 초대 코드 — 로그인한 가입자만. 서버 함수 redeem_invite 로만(앱이 표를 직접 고치지 못한다). 받은 기간은 구독 부품이
     subscription_status 의 plan 'invite' 로 알아보고 「초대 코드로 체험 중 · ○월 ○일까지」로 보인다.
   · 관리자 — 서버 admins 표에 있는 계정에만 「관리자」 단추가 보인다(아니면 자리 자체가 없다). 화면의 모든 일은 서버가 다시 확인한다(is_admin).
   · 서버 부품(window.서버 — 준비 · 세션)이 없거나 준비 중이면 조용히 비활성.
   쓰는 법(앱 끝, 서버.설치 · 구독.설치 뒤):
     가입.설치({ app:'clinicscore', 약관판:'2026-10-21', 이름:{ko:'ClinicScore',en:'ClinicScore'},
                 말:function(){return 'ko';}, 약관:'…주소', 처리방침:'…주소',
                 추가동의:[{ko:'(필수) 의료인 또는 의료 관련 학생입니다', en:'…'}],      // 앱마다 더 받을 확인(모두 필수)
                 시트열기:function(html, 제목){…}, 시트닫기:function(){…}, 알림:function(말){…},
                 모양:{ 줄:'rcta', 주:'p', 보조:'s', 작은글:'bandnote' } });
     화면:  가입.초대HTML() (설정 → 구독 아래) · 가입.관리자HTML() (설정 맨 아래 — 관리자에게만 단추 하나)
     동기화: 서버.설치({ 동기화허용: function(){ return !window.가입 || 가입.됨(); } })
   ⛔ 「돈 안 드는」 뜻의 그 낱말(원칙 금지어)을 쓰지 않는다 — 초대는 「초대 코드로 체험」. */
(function () {
  var 판 = '2026-10-21';   /* 부품 판 11-11a — 앱별 민감 동의 · 회원권이면 동의 한 번 · 두 번째 앱 회원권 한 줄 */
  var 앱들 = ['kids', 'gildongmu', 'clinicscore', 'gyeote', 'yakjido'];
  var 앱이름 = { kids: '우리 집 소아과', gildongmu: '길동무', clinicscore: 'ClinicScore', gyeote: '곁에', yakjido: '약지도' };
  var 설정 = { 초대길: null, app: 'app', 약관판: '', 이름: null, 말: null, 약관: '', 처리방침: '', 추가동의: [], 민감동의: null, 서버1111: false, 시트열기: null, 시트닫기: null, 알림: null, 모양: {} };   /* 11-11 민감동의(앱 글 {ko,en}) · 서버1111(join_app2 쓰기 — SQL 적용 뒤 켬) */
  var 글 = {
    ko: {
      가입제목: '{앱} 가입', 가입말: '이 계정은 메디나눔의 다른 앱에서 만들어졌어요. {앱}을(를) 쓰시려면 이 앱의 약관에 따로 동의해 주세요. 다른 앱의 기록은 이 앱에 보이지 않아요.',
      가입동의: '(필수) {앱} <a href="{약관}" target="_blank" rel="noopener">이용약관</a>과 <a href="{처리방침}" target="_blank" rel="noopener">개인정보 처리방침</a>에 동의합니다',
      회원권가입말: '메디나눔 회원권으로 다섯 앱이 열려 있어요. {앱}에서는 이 앱의 동의만 한 번 받을게요 — 다른 앱의 기록은 이 앱에 보이지 않아요.', 회원권권함: '앱을 3개 이상 쓰시면 메디나눔 회원권이 더 알뜰해요 — 다섯 앱을 월 {회원권값}에', 회원권보기: '회원권 보기', 민감없음: '건강정보 동의에 체크해 주세요. 이 앱은 건강정보를 다뤄서, 회원권이어도 따로 여쭤요.',
      가입단추: '동의하고 가입', 나중: '로그아웃', 가입됨: '{앱}에 가입했어요.', 체크: '필수 항목에 모두 체크해 주세요.', 문제: '잠시 문제가 있었어요. 다시 해 주세요.',
      인터넷: '인터넷이 닿지 않아요. 연결되면 다시 해 주세요.', 가입대기: '{앱} 가입 동의 전이라 동기화를 멈춰 두었어요.', 가입열기: '가입 동의하기',
      초대: '초대 코드', 초대말: '받으신 초대 코드가 있으면 넣어 주세요.', 초대넣기: '코드 넣기', 초대칸: '예: MN-AB12-CD34',
      초대됨: '초대 코드가 확인됐어요. {날}까지 모든 기능을 쓸 수 있어요.', 초대중: '<b>초대 코드로 체험 중</b> · {날}까지',
      초대꺼짐: '지금은 모든 기능이 열려 있어요. 결제가 시작되어도 이 코드로 받은 기간 동안은 그대로 열려요.',
      초대시험: '시험용 계정에는 실제 환자 정보를 넣지 마세요.',
      이유: { login: '먼저 로그인해 주세요.', member: '먼저 이 앱에 가입해 주세요.', rate: '오늘은 더 넣을 수 없어요. 내일 다시 해 주세요.',
              notfound: '맞는 코드가 없어요. 글자를 다시 확인해 주세요.', off: '사용이 멈춘 코드예요.', expired: '기한이 지난 코드예요.',
              full: '정해진 인원이 다 쓴 코드예요.', scope: '이 앱에는 쓸 수 없는 코드예요.', used: '이미 쓰신 코드예요.', app: '잠시 문제가 있었어요.' },
      관리자: '관리자', 관리제목: '관리자', 앱별: '앱별 숫자', 가입자: '가입', 체험: '체험', 구독: '구독', 초대받음: '초대', 문의대기: '답 기다리는 문의',
      회원권: '회원권', 계정: '계정', 새코드: '새 초대 코드', 범위: '쓸 수 있는 앱', 모든앱: '다섯 앱 모두', 기간: '받는 기간(일)', 인원: '쓸 수 있는 사람 수',
      유효: '코드 유효(일, 비우면 끝없음)', 메모: '메모(누구에게 주나)', 만들기: '만들기', 만듦: '만들었어요: {코드}', 복사: '복사',
      코드들: '초대 코드', 사용: '사용', 켜짐: '쓰는 중', 꺼짐: '멈춤', 멈추기: '멈추기', 다시켜기: '다시 켜기', 사람: '받은 사람', 회수: '거두기',
      회수확인: '한 번 더 누르면 거둬요', 회수됨: '거뒀어요.', 문의: '문의', 모든문의: '모든 앱', 없음: '아직 없어요.', 닫기: '닫기', 새로: '새로 고침', 까지: '{날}까지',
      /* 관리자다듬기1030 */
      만들제목: '초대 코드 만들기', 받는기간: '받는 기간', 일30: '30일', 일90: '90일', 년1: '1년', 앱칸: '쓸 수 있는 앱', 다섯모두: '다섯 앱 모두', 이앱만: '끄면 {앱}에서만 써요',
      메모칸: '메모 (선택)', 메모예: '예: 사연 주신 ○○님', 자세히: '자세히', 사람수: '쓸 수 있는 사람 수', 넣는기간: '코드를 넣을 수 있는 기간 (일)', 코드만들기: '코드 만들기', 만드는중: '만드는 중…',
      새코드카드: '새 초대 코드', 넣어야: '{날}까지 넣어야 해요', 기한없음: '넣는 기한 없음', 코드복사: '코드 복사', 답장복사: '답장 문장 복사', 복사됨: '복사했어요.',
      만든코드: '만든 코드', 메모없음: '메모 없음', 남은날: '{n}일 남음', 기한지남: '넣는 기한 지남', 받은사람보기: '받은 사람 보기', 숫자제목: '앱별 숫자',
      답장: '안녕하세요, 메디나눔 운영팀이에요.\n보내 주신 이야기 잘 읽었어요. 아래 초대 코드를 넣으시면 {기간} 동안 {앱}의 모든 기능을 쓰실 수 있어요.\n\n초대 코드: {코드}\n넣는 곳: {길}\n{날}까지 넣어 주세요.\n\n치료하시는 길에 늘 함께할게요.\n— 메디나눔 운영팀',
      다섯앱이름: '메디나눔 다섯 앱', 기본길: '설정 → 초대 코드', 운영자줄: '운영자 · 모든 기능'
    },
    en: {
      가입제목: 'Join {앱}', 가입말: 'This account was created in another MediNanum app. To use {앱}, please agree to this app’s terms separately. Records from other apps are not shown here.',
      가입동의: '(Required) I agree to the {앱} <a href="{약관}" target="_blank" rel="noopener">Terms</a> and <a href="{처리방침}" target="_blank" rel="noopener">Privacy Policy</a>',
      회원권가입말: 'Your MediNanum pass opens all five apps. {앱} just needs your consent once for this app — records from other apps are not shown here.', 회원권권함: 'Using three or more apps? The MediNanum pass is better value — all five apps for {회원권값} a month', 회원권보기: 'See the pass', 민감없음: 'Please tick the health information consent. This app handles health information, so we ask separately even with the pass.',
      가입단추: 'Agree and join', 나중: 'Sign out', 가입됨: 'You joined {앱}.', 체크: 'Please tick all required boxes.', 문제: 'Something went wrong. Please try again.',
      인터넷: 'No connection. Please try again when you are online.', 가입대기: 'Sync is paused until you agree to {앱}’s terms.', 가입열기: 'Agree and join',
      초대: 'Invite code', 초대말: 'If you received an invite code, enter it here.', 초대넣기: 'Apply code', 초대칸: 'e.g. MN-AB12-CD34',
      초대됨: 'Invite code accepted. Everything is open until {날}.', 초대중: '<b>Invite access</b> · until {날}',
      초대꺼짐: 'Everything is open right now. When billing starts, this code keeps it open for the period it gives.',
      초대시험: 'Please do not enter real patient information in test accounts.',
      이유: { login: 'Please sign in first.', member: 'Please join this app first.', rate: 'Too many tries today. Please try tomorrow.',
              notfound: 'That code was not found. Please check the letters.', off: 'This code has been switched off.', expired: 'This code has expired.',
              full: 'This code has been used by everyone it was meant for.', scope: 'This code is not for this app.', used: 'You already used this code.', app: 'Something went wrong.' },
      관리자: 'Admin', 관리제목: 'Admin', 앱별: 'By app', 가입자: 'Joined', 체험: 'Trial', 구독: 'Paid', 초대받음: 'Invited', 문의대기: 'Open questions',
      회원권: 'Pass', 계정: 'Accounts', 새코드: 'New invite code', 범위: 'Apps', 모든앱: 'All five apps', 기간: 'Access (days)', 인원: 'People',
      유효: 'Code valid (days, blank = no end)', 메모: 'Note (who it is for)', 만들기: 'Create', 만듦: 'Created: {코드}', 복사: 'Copy',
      코드들: 'Invite codes', 사용: 'Used', 켜짐: 'Active', 꺼짐: 'Stopped', 멈추기: 'Stop', 다시켜기: 'Turn on', 사람: 'People', 회수: 'Revoke',
      회수확인: 'Tap again to revoke', 회수됨: 'Revoked.', 문의: 'Questions', 모든문의: 'All apps', 없음: 'Nothing yet.', 닫기: 'Close', 새로: 'Refresh', 까지: 'until {날}',
      만들제목: 'Create an invite code', 받는기간: 'Access period', 일30: '30 days', 일90: '90 days', 년1: '1 year', 앱칸: 'Apps', 다섯모두: 'All five apps', 이앱만: 'Off = {앱} only',
      메모칸: 'Note (optional)', 메모예: 'e.g. for Ms. Kim who wrote to us', 자세히: 'Details', 사람수: 'How many people can use it', 넣는기간: 'Days the code can be entered', 코드만들기: 'Create code', 만드는중: 'Creating…',
      새코드카드: 'New invite code', 넣어야: 'Must be entered by {날}', 기한없음: 'No entry deadline', 코드복사: 'Copy code', 답장복사: 'Copy reply', 복사됨: 'Copied.',
      만든코드: 'Codes', 메모없음: 'No note', 남은날: '{n} days left', 기한지남: 'Entry deadline passed', 받은사람보기: 'See who used it', 숫자제목: 'By app',
      답장: 'Hello, this is the MediNanum team.\nThank you for sharing your story with us. Enter the invite code below to use every feature of {앱} for {기간}.\n\nInvite code: {코드}\nWhere: {길}\nPlease enter it by {날}.\n\nWe are with you on this path.\n— The MediNanum team',
      다섯앱이름: 'all five MediNanum apps', 기본길: 'Settings → Invite code', 운영자줄: 'Operator · all features'
    }
  };
  function 말() { try { return typeof 설정.말 === 'function' && 설정.말() === 'en' ? 'en' : 'ko'; } catch (e) { return 'ko'; } }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function 두벌(v) { if (v == null) return ''; if (typeof v === 'object') return v[말()] || v.ko || ''; return String(v); }
  function 이앱() { return 두벌(설정.이름) || 앱이름[설정.app] || 설정.app; }
  function 말글(k, 값) {
    var t = 글[말()][k]; if (t == null) t = 글.ko[k]; t = String(t == null ? '' : t);
    var v = { 앱: esc(이앱()) }; for (var a in 값 || {}) v[a] = 값[a];
    return t.replace(/\{([^}]+)\}/g, function (_, n) { return v[n] != null ? v[n] : ''; });
  }
  function 날(t) { var d = new Date(t); if (isNaN(d)) return '—'; return 말() === 'en' ? d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0') : (d.getMonth() + 1) + '월 ' + d.getDate() + '일'; }
  function 모(k) { return (설정.모양 && 설정.모양[k]) || ''; }
  function 단추(t, 부름, 주, 이름) { var c = 주 ? 모('주') : 모('보조'); return '<button type="button"' + (c ? ' class="' + c + '"' : '') + (이름 ? ' aria-label="' + esc(이름) + '"' : '') + ' onclick="' + 부름 + '">' + esc(t) + '</button>'; }
  function 줄(안) { return '<div class="' + 모('줄') + '">' + 안 + '</div>'; }
  function 작은(t) { return '<p class="' + 모('작은글') + '">' + t + '</p>'; }
  function 알림(t) { try { if (typeof 설정.알림 === 'function') return 설정.알림(t); } catch (e) {} }
  function 시트열기(html, 제목) { try { if (typeof 설정.시트열기 === 'function') return 설정.시트열기(html, 제목); } catch (e) {} }
  function 시트닫기() { try { if (typeof 설정.시트닫기 === 'function') 설정.시트닫기(); } catch (e) {} }

  /* ── 서버 ── */
  function 서버() { return window.서버 && typeof window.서버.준비 === 'function' && (!window.서버.준비됨 || window.서버.준비됨()) ? window.서버 : null; }
  function 세션() { try { var s = 서버(); return s && s.세션 ? s.세션() : null; } catch (e) { return null; } }
  function 사용자() { var s = 세션(); return s && s.user ? s.user.id : null; }
  function 키() { return '_join_' + 설정.app; }
  function 읽기() { var o = null; try { o = JSON.parse(localStorage.getItem(키()) || 'null'); } catch (e) {} var u = 사용자(); return o && u && o.user === u ? o : null; }
  function 쓰기(o) { try { if (o) localStorage.setItem(키(), JSON.stringify(o)); else localStorage.removeItem(키()); } catch (e) {} }
  function rpc(이름, 인자) {
    var s = 서버(); if (!s) return Promise.reject(new Error('noserver'));
    return s.준비().then(function (sb) { if (!sb) throw new Error('noserver'); return sb.rpc(이름, 인자 || {}); }).then(function (r) {
      if (r && r.error) throw r.error; return r ? r.data : null;
    });
  }
  var 확인중 = null, 시트떴다 = false;
  function 확인(조용히) {
    if (!사용자()) return Promise.resolve(null);
    if (확인중) return 확인중;
    확인중 = rpc('my_app', { p_app: 설정.app }).then(function (d) {
      if (!d || d.why) return null;
      var o = { user: 사용자(), member: !!d.member, grant_until: d.grant_until ? Date.parse(d.grant_until) : null, admin: !!d.admin, pass: !!d.pass, apps: +d.apps || 0, at: Date.now() };   /* 11-11 pass·apps(서버 1111 뒤에만 옴) */
      if (!o.member && 이앱가입표시()) {   /* 이 앱에서 가입 동의를 하고 계정을 만든 분 — 다시 묻지 않고 기록만 */
        return rpc('join_app', { p_app: 설정.app, p_terms: 설정.약관판 || 판 }).then(function (r) { if (r && r.ok) { o.member = true; 가입표시지움(); } 쓰기(o); return o; });
      }
      쓰기(o); return o;
    }).then(function (o) {
      확인중 = null; 바뀜();
      if (o && !o.member && !조용히 && !시트떴다) { 시트떴다 = true; 가입열기(); }
      return o;
    }, function () { 확인중 = null; return null; });
    return 확인중;
  }
  function 이앱가입표시() { try { return sessionStorage.getItem('_join_signup_' + 설정.app) === '1' || localStorage.getItem('_join_signup_' + 설정.app) === '1'; } catch (e) { return false; } }
  function 가입표시지움() { try { sessionStorage.removeItem('_join_signup_' + 설정.app); localStorage.removeItem('_join_signup_' + 설정.app); } catch (e) {} }
  function 바뀜() {
    try { var el = document.getElementById('joininv'); if (el) el.outerHTML = 초대HTML(); } catch (e) {}
    try { var el2 = document.getElementById('joinadmbtn'); if (el2) el2.outerHTML = 관리자HTML(); } catch (e) {}
    try { var el3 = document.getElementById('joinwait'); if (el3) el3.outerHTML = 대기HTML(); } catch (e) {}
  }

  /* ── 가입 ── */
  function 됨() { if (!사용자()) return true; var o = 읽기(); return !!(o && o.member); }
  function 원(n) { n = +n || 0; return 말() === 'en' ? '₩' + n.toLocaleString('en-US') : n.toLocaleString('ko-KR') + '원'; }
  function 가입HTML() {
    var o = 읽기() || {};
    var 칸 = '<label class="subagree"><input type="checkbox" class="joinchk"> <span>' + 말글('가입동의', { 약관: esc(설정.약관 || '#'), 처리방침: esc(설정.처리방침 || '#') }) + '</span></label>';
    (설정.추가동의 || []).forEach(function (x) { 칸 += '<label class="subagree"><input type="checkbox" class="joinchk"> <span>' + esc(두벌(x)) + '</span></label>'; });
    if (설정.민감동의) 칸 += '<label class="subagree"><input type="checkbox" class="joinchk joinsens"> <span>' + esc(두벌(설정.민감동의)) + '</span></label>';   /* 11-11 — 앱마다 따로 · 회원권이어도 생략 안 함 */
    /* 11-11 회원권 권하기 — 두 번째 앱부터 작은 한 줄(압박 말 없음 · 가입 단추는 그대로) */
    var 권함 = (!o.pass && o.apps >= 1 && window.회원권 && 회원권.열기)
      ? 작은(말글('회원권권함', { 앱값: 원((window.회원권.값표 && 회원권.값표.앱 && 회원권.값표.앱.월) || 4900), 회원권값: 원((window.회원권.값표 && 회원권.값표.회원권 && 회원권.값표.회원권.월) || 12900) }) + ' <button type="button" class="' + (모('보조') || '') + '" onclick="회원권.열기()">' + esc(말글('회원권보기')) + '</button>') : '';
    return '<div id="joinbox"><p>' + 말글(o.pass ? '회원권가입말' : '가입말') + '</p>' + 칸 + 줄(단추(말글('가입단추'), '가입.가입하기()', true) + 단추(말글('나중'), '가입.나가기()', false)) + 권함 + '</div>';
  }
  function 가입열기() { 시트열기(가입HTML(), 말글('가입제목')); }
  function 가입하기() {
    var 칸 = document.querySelectorAll('#joinbox .joinchk'), 다 = 칸.length > 0;
    for (var i = 0; i < 칸.length; i++) if (!칸[i].checked) 다 = false;
    if (!다) { 알림(말글(document.querySelector('#joinbox .joinsens:not(:checked)') ? '민감없음' : '체크')); return Promise.resolve(false); }
    var 민감 = !!document.querySelector('#joinbox .joinsens:checked');
    return (설정.서버1111 ? rpc('join_app2', { p_app: 설정.app, p_terms: 설정.약관판 || 판, p_sensitive: 민감 }) : rpc('join_app', { p_app: 설정.app, p_terms: 설정.약관판 || 판 })).then(function (r) {
      if (r && r.why === 'sensitive') { 알림(말글('민감없음')); return false; }
      if (!r || !r.ok) { 알림(말글('문제')); return false; }
      var o = 읽기() || { user: 사용자() }; o.member = true; o.at = Date.now(); 쓰기(o);
      시트닫기(); 알림(말글('가입됨')); 바뀜();
      try { var 동 = window.서버 && window.서버.동기화 ? window.서버.동기화() : null; if (동 && 동.catch) 동.catch(function () {}); } catch (e) {}
      return true;
    }, function () { 알림(navigator.onLine === false ? 말글('인터넷') : 말글('문제')); return false; });
  }
  function 나가기() { 시트닫기(); try { if (typeof window.계정동작 === 'function') return window.계정동작('logout'); } catch (e) {} }
  function 대기HTML() {
    if (!사용자() || 됨()) return '<span id="joinwait"></span>';
    return '<div id="joinwait">' + 작은(말글('가입대기')) + 줄(단추(말글('가입열기'), '가입.가입열기()', true)) + '</div>';
  }

  /* ── 초대 코드 ── */
  function 운영자() { var o = 읽기(); return !!(o && o.admin); }   /* 10-30 현욱님 — 관리자는 다섯 앱 모든 기능(서버 grants all·admin) */
  function 초대HTML() {
    if (!서버() || !사용자()) return '<div id="joininv"></div>';
    if (운영자()) return '<div id="joininv" class="joininv jadm-op"><b>' + 말글('운영자줄') + '</b></div>';   /* 회원권·체험·초대 코드 글 대신 한 줄 */
    var o = 읽기(), 지금 = Date.now(), h = '<div id="joininv" class="joininv"><b>' + 말글('초대') + '</b>';
    if (o && o.grant_until && o.grant_until > 지금) {
      h += '<p>' + 말글('초대중', { 날: 날(o.grant_until) }) + '</p>' + (구독꺼짐() ? 작은(말글('초대꺼짐')) : '') + 작은(말글('초대시험'));
    } else {
      h += 작은(말글('초대말')) + '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
        '<input id="joinInvIn" type="text" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="32" style="flex:1;min-width:0" ' +
        'placeholder="' + esc(말글('초대칸')) + '" aria-label="' + esc(말글('초대')) + '" onkeydown="if(event.key===\'Enter\'&&!event.isComposing){event.preventDefault();가입.초대넣기();}">' +
        단추(말글('초대넣기'), '가입.초대넣기()', false) + '</div>';
    }
    return h + '</div>';
  }
  function 구독꺼짐() { try { return !(window.구독 && 구독.켜짐 && 구독.켜짐()); } catch (e) { return true; } }
  var 넣는중 = false;
  function 초대넣기() {
    var el = document.getElementById('joinInvIn'), v = el ? String(el.value || '').trim() : '';
    if (!v || 넣는중) return Promise.resolve(false);
    if (!됨()) { 알림(글[말()].이유.member); 가입열기(); return Promise.resolve(false); }
    넣는중 = true;
    return rpc('redeem_invite', { p_code: v, p_app: 설정.app }).then(function (r) {
      넣는중 = false;
      if (!r || !r.ok) { 알림(글[말()].이유[(r && r.why) || 'app'] || 말글('문제')); return false; }
      var o = 읽기() || { user: 사용자(), member: true }; o.grant_until = Date.parse(r.until); o.at = Date.now(); 쓰기(o);
      알림(말글('초대됨', { 날: 날(o.grant_until) })); 바뀜();
      try { if (window.구독 && 구독.조회) 구독.조회(); } catch (e) {}
      return true;
    }, function () { 넣는중 = false; 알림(navigator.onLine === false ? 말글('인터넷') : 말글('문제')); return false; });
  }

  /* ── 관리자 ── */
  function 관리자HTML() {
    var o = 읽기();
    if (!o || !o.admin) return '<span id="joinadmbtn"></span>';   /* 관리자가 아니면 자리 자체가 없다 */
    return '<span id="joinadmbtn">' + 줄(단추(말글('관리자'), '가입.관리자열기()', false)) + '</span>';
  }
  var 관 = { stats: null, codes: [], 사람: {}, 문의: [], 문의앱: null, 새코드: '', 회수대기: '' };
  function 관리자열기() { 시트열기('<div id="joinadm">' + 관리몸() + '</div>', 말글('관리제목')); return 관리새로(); }
  function 관리그리기() { var el = document.getElementById('joinadm'); if (el) el.innerHTML = 관리몸(); }
  function 관리새로() {
    return Promise.all([rpc('admin_stats'), rpc('admin_invites'), rpc('admin_inquiries', { p_app: 관.문의앱, p_limit: 30 })]).then(function (r) {
      관.stats = r[0] || {}; 관.codes = r[1] || []; 관.문의 = r[2] || []; 관리그리기();
    }, function () { 알림(말글('문제')); });
  }
  /* 관리자다듬기1030 — 만들기 한 장 → 새 코드 카드 → 만든 코드 행 → (접기) 문의 · 앱별 숫자 */
  function 기간글(d) { return d >= 365 ? 말글('년1') : d === 30 ? 말글('일30') : d === 90 ? 말글('일90') : d + (말() === 'en' ? ' days' : '일'); }
  function 남은(c) { if (!c.expires_at) return 말글('기한없음'); var n = Math.ceil((Date.parse(c.expires_at) - Date.now()) / 86400000); return n > 0 ? 말글('남은날', { n: n }) : 말글('기한지남'); }
  function 관리몸() {
    var s = 관.stats, h = '<div class="jadm">', 기 = 관.기간 || 90;
    h += '<section class="jadm-card"><h3>' + 말글('만들제목') + '</h3>'
      + '<p class="jadm-lab">' + 말글('받는기간') + '</p><div class="jadm-chips" role="group">'
      + [30, 90, 365].map(function (d) { var on = 기 === d; return '<button type="button" class="jadm-chip' + (on ? ' on' : '') + '" aria-pressed="' + on + '" onclick="가입.관리기간(' + d + ')">' + esc(기간글(d)) + '</button>'; }).join('') + '</div>'
      + '<div class="jadm-grp"><p class="jadm-lab">' + 말글('앱칸') + '</p><label class="jadm-tog"><input type="checkbox" id="jaAll"' + (관.모두 ? ' checked' : '') + ' onchange="가입.관리모두(this.checked)"><span>' + 말글('다섯모두') + '</span></label>'
      + '<p class="jadm-dim">' + esc(관.모두 ? 말글('다섯앱이름') : 말글('이앱만', { 앱: 앱이름[설정.app] || 설정.app })) + '</p>' + '</div>'
      + '<label class="jadm-lab" for="jaNote">' + 말글('메모칸') + '</label><input id="jaNote" class="jadm-in" type="text" maxlength="200" placeholder="' + esc(말글('메모예')) + '" value="' + esc(관.메모 || '') + '">'
      + '<details class="jadm-more"><summary>' + 말글('자세히') + '</summary>'
      + '<label class="jadm-lab" for="jaMax">' + 말글('사람수') + '</label><input id="jaMax" class="jadm-in" type="number" inputmode="numeric" min="1" max="1000" value="1">'
      + '<label class="jadm-lab" for="jaValid">' + 말글('넣는기간') + '</label><input id="jaValid" class="jadm-in" type="number" inputmode="numeric" min="1" max="366" value="14"></details>'
      + '<button type="button" class="jadm-go" id="jaGo" onclick="가입.관리만들기()">' + 말글('코드만들기') + '</button></section>';
    if (관.새) {
      var n = 관.새;
      h += '<section class="jadm-new" id="jaNew"><p class="jadm-lab">' + 말글('새코드카드') + '</p><p class="jadm-code">' + esc(n.code) + '</p>'
        + '<p class="jadm-due">' + (n.expires_at ? 말글('넣어야', { 날: 날(n.expires_at) }) : 말글('기한없음')) + '</p>'
        + '<p class="jadm-dim">' + esc(기간글(n.days | 0)) + ' · ' + esc(n.scope === 'all' ? 말글('다섯앱이름') : (앱이름[n.scope] || n.scope)) + (n.note ? ' · ' + esc(n.note) : '') + '</p>'
        + '<div class="jadm-two"><button type="button" class="jadm-go" onclick="가입.관리복사(\'' + esc(n.code) + '\')">' + 말글('코드복사') + '</button>'
        + '<button type="button" class="jadm-alt" onclick="가입.관리답장()">' + 말글('답장복사') + '</button></div></section>';
    }
    h += '<h3 class="jadm-h">' + 말글('만든코드') + '</h3>';
    if (!관.codes.length) h += '<p class="jadm-dim">' + 말글('없음') + '</p>';
    관.codes.forEach(function (c) {
      var 사람 = 관.사람[c.code];
      h += '<div class="jadm-row' + (c.active ? '' : ' off') + '"><div class="jadm-rowtx"><b class="jadm-mono">' + esc(c.code) + '</b>'
        + '<span>' + esc(c.note || 말글('메모없음')) + '</span>'
        + '<span class="jadm-dim jadm-pcs">' + [esc(기간글(c.days | 0)), esc(c.scope === 'all' ? 말글('모든앱') : (앱이름[c.scope] || c.scope)), esc(남은(c)), 말글('사용') + ' ' + (c.used_count | 0) + '/' + (c.max_uses | 0), (c.active ? 말글('켜짐') : 말글('꺼짐'))].map(function (x) { return '<span class="jadm-pc">' + x + '</span>'; }).join(' · ') + '</span>'   /* 10-30 — 조각 단위로만 줄이 바뀐다 */
        + '<button type="button" class="jadm-link" onclick="가입.관리사람(\'' + esc(c.code) + '\')">' + 말글('받은사람보기') + '</button></div>'
        + '<button type="button" class="jadm-stop" onclick="가입.관리켜기(\'' + esc(c.code) + '\',' + (c.active ? 'false' : 'true') + ')">' + (c.active ? 말글('멈추기') : 말글('다시켜기')) + '</button></div>';
      if (사람) {
        h += '<div class="jadm-people">' + (사람.length ? '' : '<p class="jadm-dim">' + 말글('없음') + '</p>');
        사람.forEach(function (u) {
          var 열림 = u.grant_until && Date.parse(u.grant_until) > Date.now(), 키 = u.user_id;
          h += '<p>' + esc(u.email || '—') + ' · ' + esc(앱이름[u.app] || u.app) + (u.grant_until ? ' · ' + 말글('까지', { 날: 날(u.grant_until) }) : '')
            + (열림 ? ' <button type="button" class="jadm-link" onclick="가입.관리회수(\'' + esc(키) + '\',\'' + esc(c.code) + '\')">' + (관.회수대기 === 키 ? 말글('회수확인') : 말글('회수')) + '</button>' : '') + '</p>';
        });
        h += '</div>';
      }
    });
    h += '<details class="jadm-more"><summary>' + 말글('문의') + ' (' + 관.문의.length + ')</summary>'
      + '<select id="joinAdmInqApp" class="jadm-in" onchange="가입.관리문의앱(this.value)"><option value="">' + 말글('모든문의') + '</option>'
      + 앱들.map(function (a) { return '<option value="' + a + '"' + (관.문의앱 === a ? ' selected' : '') + '>' + esc(앱이름[a]) + '</option>'; }).join('') + '</select>'
      + (관.문의.length ? 관.문의.map(function (q) { return '<div class="jadm-inq"><p class="jadm-dim">' + esc(앱이름[q.app] || q.app) + ' · ' + esc(String(q.created_at || '').slice(0, 10)) + (q.screen ? ' · ' + esc(q.screen) : '') + '</p><p>' + esc(q.text) + '</p></div>'; }).join('') : '<p class="jadm-dim">' + 말글('없음') + '</p>')
      + '</details>';
    h += '<details class="jadm-more"><summary>' + 말글('숫자제목') + '</summary>';
    if (s) {
      h += '<div style="overflow-x:auto"><table class="jadm-tab"><tr><th></th><th>' + 말글('가입자') + '</th><th>' + 말글('체험') + '</th><th>' + 말글('구독') + '</th><th>' + 말글('초대받음') + '</th><th>' + 말글('문의대기') + '</th></tr>';
      앱들.forEach(function (a) { var x = s[a] || {}; h += '<tr><th>' + esc(앱이름[a]) + '</th><td>' + (x.members | 0) + '</td><td>' + (x.trial | 0) + '</td><td>' + (x.active | 0) + '</td><td>' + (x.invited | 0) + '</td><td>' + (x.inquiries_open | 0) + '</td></tr>'; });
      h += '</table></div><p class="jadm-dim">' + esc(말글('회원권')) + ' ' + (s.pass | 0) + ' · ' + esc(말글('계정')) + ' ' + (s.accounts | 0) + '</p>';
    } else h += '<p class="jadm-dim">…</p>';
    return h + '</details></div>';
  }
  function 관리기간(d) { 관.기간 = d; 관.메모 = (document.getElementById('jaNote') || {}).value || 관.메모 || ''; 관리그리기(); }
  function 관리모두(v) { 관.모두 = !!v; 관.메모 = (document.getElementById('jaNote') || {}).value || 관.메모 || ''; 관리그리기(); }
  function 관리답장() {
    var n = 관.새; if (!n) return;
    var 길 = 설정.초대길 ? 두벌(설정.초대길) : 말글('기본길');
    var t = 말글('답장', { 기간: 기간글(n.days | 0), 앱: n.scope === 'all' ? 말글('다섯앱이름') : (앱이름[n.scope] || n.scope), 코드: n.code, 길: 길, 날: n.expires_at ? 날(n.expires_at) : '—' }).replace(/\\n/g, '\n');
    try { navigator.clipboard.writeText(t).then(function () { 알림(말글('복사됨')); }, function () { 알림(t); }); } catch (e) { 알림(t); }
  }
  function 숫자(id, 기본) { var el = document.getElementById(id), n = el ? parseInt(el.value, 10) : NaN; return isNaN(n) ? 기본 : n; }
  function 관리만들기() {
    var sc = 관.모두 ? 'all' : 설정.app, 메 = String((document.getElementById('jaNote') || {}).value || '').trim().slice(0, 200), 기 = 관.기간 || 90;
    var 유값 = Math.max(1, Math.min(366, 숫자('jaValid', 14))), 사람수 = Math.max(1, Math.min(1000, 숫자('jaMax', 1)));
    var b = document.getElementById('jaGo'); if (b) { b.disabled = true; b.textContent = 말글('만드는중'); }
    return rpc('admin_create_invite', { p_scope: sc, p_days: 기, p_max_uses: 사람수, p_valid_days: 유값, p_note: 메 }).then(function (r) {
      var code = (r && r.code) || ''; 관.메모 = '';
      return 관리새로().then(function () {
        var c = 관.codes.filter(function (x) { return x.code === code; })[0];
        관.새 = c || { code: code, days: 기, scope: sc, note: 메, expires_at: new Date(Date.now() + 유값 * 86400000).toISOString() };
        관리그리기(); try { var el = document.getElementById('jaNew'); if (el) el.scrollIntoView({ block: 'start', behavior: 'smooth' }); } catch (e) {}
      });
    }, function () { 알림(말글('문제')); if (b) { b.disabled = false; b.textContent = 말글('코드만들기'); } });
  }
  function 관리켜기(code, 켜) { return rpc('admin_set_invite', { p_code: code, p_active: !!켜 }).then(관리새로, function () { 알림(말글('문제')); }); }
  function 관리사람(code) {
    return rpc('admin_invite_users', { p_code: code }).then(function (r) { 관.사람[code] = r || []; 관리그리기(); }, function () { 알림(말글('문제')); });
  }
  function 관리회수(user, code) {
    if (관.회수대기 !== user) { 관.회수대기 = user; 관리그리기(); return Promise.resolve(false); }   /* 두 번 누름 */
    관.회수대기 = '';
    return rpc('admin_revoke', { p_user: user, p_scope: null }).then(function () { 알림(말글('회수됨')); return 관리사람(code); }, function () { 알림(말글('문제')); });
  }
  function 관리문의앱(a) { 관.문의앱 = a || null; return rpc('admin_inquiries', { p_app: 관.문의앱, p_limit: 30 }).then(function (r) { 관.문의 = r || []; 관리그리기(); }, function () { 알림(말글('문제')); }); }
  function 관리복사(t) { try { navigator.clipboard.writeText(t).then(function () { 알림(t); }); } catch (e) { 알림(t); } }

  /* ── 로그인 갈고리 — 로그인·가입·소셜 뒤 앱 가입을 확인한다 ── */
  function 갈고리() {
    var f = window.계정동작; if (typeof f !== 'function' || f.__가입) return;
    var g = function (what) {
      if (what === 'signup') { try { sessionStorage.setItem('_join_signup_' + 설정.app, '1'); localStorage.setItem('_join_signup_' + 설정.app, '1'); } catch (e) {} }
      if (what === 'logout') { 쓰기(null); 시트떴다 = false; }
      var r = f.apply(this, arguments);
      if (what === 'login' || what === 'signup') Promise.resolve(r).then(function () { setTimeout(function () { 확인(); }, 400); });
      return r;
    };
    g.__가입 = true; window.계정동작 = g;
  }

  window.가입 = {
    판: 판,
    설치: function (o) {
      o = o || {};
      ['app', '약관판', '이름', '말', '약관', '처리방침', '추가동의', '민감동의', '서버1111', '시트열기', '시트닫기', '알림', '모양', '초대길'].forEach(function (k) { if (k in o) 설정[k] = o[k]; });
      if (앱들.indexOf(설정.app) < 0) return;
      if (!document.getElementById('jadm-css')) { var 꼴 = document.createElement('style'); 꼴.id = 'jadm-css'; 꼴.textContent = ''   /* 관리자다듬기1030 — 왼쪽 선 하나 · 칸 48 · 간격 12 · 17px */
        + '.jadm{--g:12px;display:flex;flex-direction:column;gap:var(--g);font-size:17px;line-height:1.55}.jadm h3{margin:0;font-size:19px}.jadm .jadm-h{margin-top:8px}'
        + '.jadm-card,.jadm-new{display:flex;flex-direction:column;gap:var(--g);padding:18px;border:1px solid var(--line,rgba(0,0,0,.14));border-radius:16px;background:var(--card,#fff)}'
        + '.jadm-new{border-color:var(--accent,#2f5d50);box-shadow:0 0 0 1px var(--accent,#2f5d50) inset}'
        + '.jadm-pc{white-space:nowrap}.jadm-grp{display:flex;flex-direction:column;gap:4px}.jadm-lab{margin:0;font-weight:700;font-size:15px;display:block}.jadm-dim{margin:0;font-size:15px;opacity:.72;word-break:keep-all}'
        + '.jadm-chips{display:flex;gap:8px}.jadm-chip{flex:1;min-height:48px;border:1px solid var(--line,rgba(0,0,0,.18));border-radius:12px;background:var(--card,#fff);color:inherit;font-weight:700;font-size:17px;line-height:1.2;font-family:inherit;cursor:pointer}'
        + '.jadm-chip.on{border-color:var(--accent,#2f5d50);box-shadow:0 0 0 2px var(--accent,#2f5d50) inset;color:var(--accent,#2f5d50)}'
        + '.jadm-tog{display:flex;align-items:center;gap:10px;min-height:48px;font-size:17px;cursor:pointer}.jadm-tog input{width:24px;height:24px;margin:0;accent-color:var(--accent,#2f5d50)}'
        + '.jadm-in{width:100%;box-sizing:border-box;min-height:48px;padding:0 14px;border:1px solid var(--line,rgba(0,0,0,.18));border-radius:12px;background:var(--card,#fff);color:inherit;font-size:17px;font-family:inherit}'
        + '.jadm-go,.jadm-alt{width:100%;min-height:52px;border-radius:14px;font-weight:700;font-size:17px;line-height:1.2;font-family:inherit;cursor:pointer}.jadm-go{border:0;background:var(--accent,#2f5d50);color:var(--on-accent,#fff)}.jadm-go:disabled{opacity:.6}'
        + '.jadm-alt{border:1px solid var(--accent,#2f5d50);background:var(--card,#fff);color:var(--accent,#2f5d50)}.jadm-two{display:flex;flex-direction:column;gap:8px}'
        + '.jadm-code{margin:0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:28px;font-weight:800;letter-spacing:.06em;word-break:break-all}.jadm-due{margin:0;font-size:19px;font-weight:800;color:var(--clay-ink,#8a3b22)}'
        + '.jadm-more{border:0}.jadm-more>summary{min-height:48px;display:flex;align-items:center;font-weight:700;font-size:15px;color:var(--accent,#2f5d50);cursor:pointer}.jadm-more[open]{display:flex;flex-direction:column;gap:var(--g)}'
        + '.jadm-row{display:flex;align-items:flex-start;gap:12px;padding:14px 16px;border:1px solid var(--line,rgba(0,0,0,.14));border-radius:14px;background:var(--card,#fff)}.jadm-row.off{opacity:.62}'
        + '.jadm-rowtx{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}.jadm-mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:17px;letter-spacing:.04em}'
        + '.jadm-stop{flex:none;min-height:44px;padding:0 14px;border:1px solid var(--line,rgba(0,0,0,.2));border-radius:999px;background:transparent;color:inherit;font-weight:700;font-size:15px;font-family:inherit;cursor:pointer}'
        + '.jadm-link{align-self:flex-start;min-height:40px;padding:0;border:0;background:none;color:var(--accent,#2f5d50);font-weight:700;font-size:15px;font-family:inherit;cursor:pointer}'
        + '.jadm-people{padding:0 16px;font-size:15px}.jadm-inq{padding:12px 0;border-top:1px solid var(--line,rgba(0,0,0,.1))}.jadm-inq p{margin:0}.jadm-tab{border-collapse:collapse;font-size:15px}.jadm-tab th,.jadm-tab td{padding:6px 10px;text-align:right;white-space:nowrap}.jadm-tab th:first-child{text-align:left}';
        document.head.appendChild(꼴); }
      갈고리(); setTimeout(갈고리, 0);   /* 다른 부품이 계정동작을 늦게 감쌀 때 */
      setTimeout(function () { if (사용자()) 확인(); else { var s = 서버(); if (s) s.준비().then(function () { if (사용자()) 확인(); }, function () {}); } }, 600);
      document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible' && 사용자()) 확인(true); });
    },
    됨: 됨, 운영자: 운영자, 확인: 확인, 상태: 읽기, 가입열기: 가입열기, 가입하기: 가입하기, 나가기: 나가기, 대기HTML: 대기HTML, 이앱가입: function () { try { sessionStorage.setItem('_join_signup_' + 설정.app, '1'); } catch (e) {} },
    초대HTML: 초대HTML, 초대넣기: 초대넣기,
    관리자HTML: 관리자HTML, 관리자열기: 관리자열기, 관리기간: 관리기간, 관리모두: 관리모두, 관리답장: 관리답장, 관리새로: 관리새로, 관리만들기: 관리만들기, 관리켜기: 관리켜기, 관리사람: 관리사람, 관리회수: 관리회수, 관리문의앱: 관리문의앱, 관리복사: 관리복사,
    닫기: 시트닫기
  };
})();
/* ▲▲ 가입 부품 끝 ▲▲ */
/* 11-11 현욱님 결정 「앱별 가입 + 메디나눔 회원권 때 통합」 — 공용 가입 부품(11-11a, 길동무 정본 그대로). 서버1111 은 서버 적용 뒤 켠다.
   약지도는 건강정보를 서버에 두므로 민감정보 동의(개인정보 보호법 23조)를 따로 받는다. 약지도 문에서 만든 계정도 이 시트에서 한 번 더 — 그 문에는 민감 동의 칸이 없다. */
try {
  가입.설치({ app: 'yakjido', 약관판: (typeof CONSENT_VER !== 'undefined' ? CONSENT_VER : '2026-10-20'), 이름: { ko: '약지도', en: 'Yakjido' },
    말: function () { return window.LANG === 'ko' || !window.LANG ? 'ko' : 'en'; }, 약관: 'terms.html', 처리방침: 'privacy.html',
    민감동의: { ko: '(필수) 드시는 약·지병·복용 기록 같은 건강정보(민감정보)를 약 안내·복약 알림·기기 사이 이어 보기에 쓰는 데 동의합니다', en: '(Required) I agree to the use of my health information (sensitive data) such as my medicines, conditions and dose records for medicine guidance, dose reminders and syncing between devices' },
    서버1111: false,
    시트열기: function (html, 제목) { var v = document.getElementById('view'); if (!v) return; v.innerHTML = topBar({ back: '뒤로' }) + '<h1>' + esc(제목 || '가입') + '</h1>' + html; scrollTo(0, 0); },
    시트닫기: function () { route(); },
    알림: function (t) { try { toast(t); } catch (e) {} },
    모양: { 줄: 'actions', 주: 'btn', 보조: 'btn line', 작은글: 'small muted' } });
} catch (e) {}
/* ▼▼ 계정 부품 시작 ▼▼ */
/* ═══ 계정 단추 · 계정 시트 · 설정 계정 카드 — 메디나눔 다섯 앱 공통 규격 (2026-10-29 현욱님 「설정 안에 숨겨 놓으면 어떡해 · 로그인할 수 있는 시스템을 명확하게」)
   규격(Main 10-29 A)
   1. 홈 머리 오른쪽 계정 단추가 늘 보인다 — 로그인 전 「로그인」, 로그인 뒤 메일 첫 글자 동그라미. 누르면 계정 시트.
   2. 계정 시트 한 화면 — 「메일로 계속하기」 하나(처음이면 계정을 만들고, 있으면 로그인). 서버 저장 동의는 이 시트 안 체크 한 줄.
      「설정 → 내 동의 내용 → 서버 저장 동의 → 계속」 같은 숨은 앞 단계가 없다.
   3. 설정 맨 위 첫 칸 = 계정 카드(로그인 전 큰 단추 · 로그인 뒤 메일·이용권·동기화·로그아웃·계정 지우기는 맨 아래 작게).
   4. 온보딩 끝 — 「로그인 · 계정 만들기」와 「로그인 없이 둘러보기」 같은 크기 두 단추(벽 금지).
   기댐: 서버 부품(window.서버 · window.계정동작) — 이 부품은 서버 부품을 고치지 않고 그 위에 얹는다.
   쓰는 법(앱):
     계정.설치({ app:'gildongmu', 앱이름:'길동무', 웹주소:'https://gildongmu.medinanum.com/',   // 메일 링크가 돌아올 웹 주소(설치 앱 localhost 막기)
       열림: function(){ return 서버 켜짐 && !만14미만 },            // false 면 시트가 까닭을 말한다(되는 척 금지)
       닫힘까닭: function(){ return '만 14세 미만은 …' },
       동의됨: fn, 동의하기: fn, 동의글: '증상·체온… 기록을 암호화된 연결로 보내 메디나눔 서버(서울)에 저장하고 …', 처리방침: fn,
       시트열기: function(html, 제목){…}, 시트닫기: fn, 알림: function(t){…}, 다시그리기: fn, 이용권글: function(){ return '체험 중 · 5일 남음' | '' },
       동의이름: '건강정보(민감정보) 서버 저장', 나이글: '만 14세 이상이에요',   // 선택 — 동의 칸 제목 · 만 14세 확인 칸(둘 다 필수로 그려진다)
       앱동의됨: function(){ return 이 앱 첫 화면 약관 동의를 지금 판으로 했나 },   // 「이 앱 가입」을 조용히(메일 확인·소셜·다른 기기 모두)
       말: { en: { '길동무': 'Wayfellow' } } });   // 선택 — 부품 다섯 말 사전에 앱 이름·앱 글을 보탠다(부품 글은 부품이 이미 옮김)
     머리: '<span class="acctslot"></span>' 자리에 계정.머리단추HTML() — 상태가 바뀌면 부품이 .acctbtn 을 스스로 고친다.
     설정 맨 위: 계정.카드HTML() · 온보딩 끝: 계정.시작단추HTML(둘러보기부름) */
(function () {
  if (window.계정 && window.계정.__v) return;
  var 설정 = { 말: null, 앱동의됨: null, 프로필켜짐: false, 프로필필수: ['name', 'gender', 'age_range'], app: 'app', 앱이름: '이 앱', 웹주소: '', 열림: null, 닫힘까닭: null, 동의됨: null, 동의하기: null, 동의글: '', 처리방침: null, 시트열기: null, 시트닫기: null, 알림: null, 다시그리기: null, 이용권글: null };
  /* 10-29 Main — 부품 글은 부품이 다섯 말(ko·en·es·ja·zh)로 들고 다닌다. 말은 <html lang> 으로 고르고, 앱은 설치({ 말: { en: { '길동무': 'Wayfellow', 앱 동의글: '…' } } }) 로 앱 이름·앱 글을 보탤 수 있다.
     앱 쪽 번역층이 같은 한국어를 또 옮기려 해도, 이미 옮긴 글이라 겹치지 않는다. */
  var 사전 = {"en":{"로그인":"Log in","로그인 · 계정 만들기":"Log in · Create account","내 계정":"My account","계정":"Account","이용권":"Plan","동기화":"Sync","아직":"Not yet","로그인 전이에요":"You're not logged in","기록은 이 기기에 있어요. 로그인하면 폰을 바꿔도 이어져요.":"Your records are on this device. Log in to keep them when you change phones.","로그인됨":"Logged in","지금 동기화":"Sync now","로그아웃":"Log out","계정 지우기":"Delete account","지금은 계정을 쓸 수 없어요. 기록은 이 기기에 그대로 있어요.":"Accounts aren't available right now. Your records are still on this device.","계정은 준비 중이에요. 기록은 이 기기에 그대로 있어요.":"Accounts are coming soon. Your records are still on this device.","이메일":"Email","비밀번호":"Password","(6자 이상)":"(6+ characters)","필수":"Required","무엇을 · 왜 · 언제까지 — 처리방침 보기":"What · why · how long — read the privacy policy","메일로 계속하기":"Continue with email","처음이시면 계정이 만들어지고, 있으시면 로그인돼요. 처음이면 메일함에 확인 링크가 가요.":"If you're new, an account is created; if you already have one, you're logged in. New accounts get a confirmation link by email.","비밀번호를 잊으셨나요":"Forgot your password?","계속하려면 서버 저장 동의에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.":"To continue, please check the server storage consent. Without it you can still use the app on this device.","이메일을 적어 주세요.":"Please enter your email.","비밀번호는 6자 이상이에요.":"Passwords need at least 6 characters.","확인하는 중…":"Checking…","로그인했어요. 기록을 맞추는 중이에요.":"You're logged in. Syncing your records.","메일함의 확인 링크를 먼저 눌러 주세요. 메일이 안 보이면 스팸함도 봐 주세요.":"Please tap the confirmation link in your email first. If you can't find it, check your spam folder.","이 메일로 만든 계정이 있어요. 비밀번호를 다시 확인해 주세요. 잊으셨으면 「비밀번호를 잊으셨나요」를 눌러 주세요.":"There's already an account with this email. Please check your password. If you forgot it, tap “Forgot your password?”.","계정을 만들었어요. 기록을 올리는 중이에요.":"Account created. Uploading your records.","처음이시군요. 메일함에 확인 링크를 보냈어요. 링크를 누른 뒤 여기서 다시 「메일로 계속하기」를 눌러 주세요.":"Welcome! We sent a confirmation link to your email. Tap it, then come back and tap “Continue with email” again.","인터넷에 닿지 않아요. 연결된 뒤 다시 눌러 주세요. 기록은 이 기기에 그대로 있어요.":"Can't reach the internet. Please try again once you're connected. Your records are still on this device.","잠시 너무 여러 번 시도했어요. 몇 분 뒤 다시 해 주세요.":"Too many attempts. Please try again in a few minutes.","로그인이 되지 않았어요. 잠시 뒤 다시 해 주세요.":"Couldn't log in. Please try again shortly.","비밀번호를 다시 정할 메일 주소를 위 칸에 적어 주세요.":"Enter the email to reset the password in the box above.","메일함에 비밀번호를 다시 정하는 링크를 보냈어요.":"We sent a password reset link to your email.","메일을 보내지 못했어요. 잠시 뒤 다시 해 주세요.":"Couldn't send the email. Please try again shortly.","로그인 없이 둘러보기":"Look around without logging in","둘러보셔도 기록은 이 기기에 남아요. 로그인은 언제든 화면 맨 위 「로그인」에서 하실 수 있어요.":"Your records stay on this device while you look around. You can log in anytime with “Log in” at the top.","{앱} 기록을 계정에 이어 두면 <b>폰을 바꿔도 그대로</b>예요.":"Link your {앱} records to an account and <b>they stay with you even if you change phones</b>.","내 계정 — {메일}":"My account — {메일}","만 14세 이상이에요":"I'm 14 or older","만 14세 이상만 계정을 만들 수 있어요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"Only people aged 14 or older can create an account. If you're younger, you can keep using the app on this device without logging in.","건강정보(민감정보) 서버 저장":"Storing health information (sensitive data) on the server","기록을 암호화된 연결로 보내 메디나눔 서버(서울)에 저장하고, 로그인한 기기에서 이어 쓰는 데 동의해요.":"I agree to have my records sent over an encrypted connection and stored on the Medinanum server in Seoul, and to continue them on devices where I log in.","만 14세 미만":"Under 14","14~19세":"14–19","20대":"20s","30대":"30s","40대":"40s","50대":"50s","60대":"60s","70대 이상":"70 or older","처음 한 번만 여쭤요. 나중에 설정에서 고치실 수 있어요.":"We only ask once. You can change this later in Settings.","고치실 것만 바꾸고 저장해 주세요.":"Change what you need, then save.","이름":"Name","성별":"Sex","여성":"Female","남성":"Male","연령대":"Age range","생일":"Birthday","(선택 · 생일 알림)":"(optional · birthday reminder)","월":"Month","일":"Day","연락 이메일":"Contact email","(선택)":"(optional)","로그인한 서비스의 프로필 사진 쓰기":"Use the profile photo from the service you logged in with","저장":"Save","저장하는 중…":"Saving…","이름·성별·연령대는 계정을 쓰는 데 필요해요. 생일·이메일·사진은 넣지 않으셔도 돼요.":"Name, sex and age range are needed for your account. Birthday, email and photo are optional.","프로필 만들기":"Create your profile","프로필 고치기":"Edit profile","만 14세 미만은 계정을 쓸 수 없어요. 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"Under-14s can't use an account. You can keep using the app on this device without logging in.","이름을 적어 주세요.":"Please enter your name.","성별을 골라 주세요.":"Please choose your sex.","연령대를 골라 주세요.":"Please choose your age range.","생일은 월과 일을 함께 골라 주세요. 넣지 않으셔도 돼요.":"Please choose both month and day for your birthday — or leave it blank.","이메일을 다시 확인해 주세요. 넣지 않으셔도 돼요.":"Please check the email — or leave it blank.","프로필을 저장했어요.":"Profile saved.","저장하지 못했어요. 잠시 뒤 다시 해 주세요.":"Couldn't save. Please try again shortly.","운영자 · 모든 기능":"Operator · all features","또는":"or","Google로 계속하기":"Continue with Google","카카오로 계속하기":"Continue with Kakao","네이버로 계속하기":"Continue with Naver","또는 메일로":"or with email","만 14세 이상인지 체크해 주세요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"Please confirm you are 14 or older. If not, you can keep using the app on this device without logging in.","계속하려면 이 칸에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.":"To continue, please tick this box. Without it, you can keep using the app on this device.","내 기기":"My devices","이 기기":"This device","마지막 사용":"Last used","내보내기":"Sign out device","이 기기에서는 로그아웃":"Log out on this device instead","이 계정으로 로그인한 기기예요. 계정 하나로 기기 두 대까지 쓸 수 있어요. 가족의 기록은 각자 계정으로 — 같은 계정이면 기록이 서로 보여요.":"These devices are logged in to this account. One account can be used on up to two devices. Family members should each have their own account — on a shared account, records are visible to each other.","이 계정은 이미 두 대에서 쓰고 있어요. 이 기기에서 쓰시려면 아래에서 내보낼 기기를 직접 골라 주세요. 내보낸 기기는 로그아웃되고, 기록은 계정에 그대로 있어요.":"This account is already used on two devices. To use it on this device, choose below which device to sign out. That device will be logged out; your records stay in the account.","가장 오래 안 쓴 기기":"Unused the longest","내보냈어요. 이 기기에서 이어서 쓰실 수 있어요.":"Done. You can keep using it on this device.","내보냈어요.":"Signed out.","다른 기기에서 이 기기를 내보냈어요. 다시 로그인하시면 이어서 쓸 수 있어요.":"This device was signed out from another device. Log in again to continue.","기기 목록을 불러오지 못했어요. 잠시 뒤 다시 해 주세요.":"Couldn't load the device list. Please try again shortly.","기기":"Device","Android 폰":"Android phone","Android 태블릿":"Android tablet","어떻게 지울까요?":"How would you like to delete?","이 앱에서만 탈퇴":"Leave this app only","이 앱의 서버 기록과 가입만 지워요. 다른 메디나눔 앱은 그대로 써요.":"Deletes only this app’s server records and membership. Other MediNanum apps keep working.","메디나눔 계정 전체 삭제":"Delete my whole MediNanum account","다섯 앱의 서버 기록과 계정을 모두 지워요. 되돌릴 수 없어요.":"Deletes the server records of all five apps and your account. This cannot be undone.","이 앱의 서버 기록과 가입을 지울까요? 되돌릴 수 없어요.":"Delete this app’s server records and membership? This cannot be undone.","이 앱에서 탈퇴했어요.":"You have left this app.","지우지 못했어요. 잠시 뒤 다시 해 주세요.":"Couldn’t delete. Please try again shortly.","지우기":"Delete","취소":"Cancel"},"es":{"로그인":"Iniciar sesión","로그인 · 계정 만들기":"Iniciar sesión · Crear cuenta","내 계정":"Mi cuenta","계정":"Cuenta","이용권":"Plan","동기화":"Sincronización","아직":"Todavía no","로그인 전이에요":"No ha iniciado sesión","기록은 이 기기에 있어요. 로그인하면 폰을 바꿔도 이어져요.":"Sus registros están en este dispositivo. Inicie sesión para conservarlos al cambiar de móvil.","로그인됨":"Sesión iniciada","지금 동기화":"Sincronizar ahora","로그아웃":"Cerrar sesión","계정 지우기":"Eliminar cuenta","지금은 계정을 쓸 수 없어요. 기록은 이 기기에 그대로 있어요.":"Ahora no se pueden usar cuentas. Sus registros siguen en este dispositivo.","계정은 준비 중이에요. 기록은 이 기기에 그대로 있어요.":"Las cuentas llegarán pronto. Sus registros siguen en este dispositivo.","이메일":"Correo electrónico","비밀번호":"Contraseña","(6자 이상)":"(mínimo 6 caracteres)","필수":"Obligatorio","무엇을 · 왜 · 언제까지 — 처리방침 보기":"Qué · por qué · hasta cuándo: ver la política de privacidad","메일로 계속하기":"Continuar con correo","처음이시면 계정이 만들어지고, 있으시면 로그인돼요. 처음이면 메일함에 확인 링크가 가요.":"Si es nuevo, se crea una cuenta; si ya tiene una, inicia sesión. Si es nueva, le llegará un enlace de confirmación al correo.","비밀번호를 잊으셨나요":"¿Ha olvidado la contraseña?","계속하려면 서버 저장 동의에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.":"Para continuar, marque el consentimiento de almacenamiento. Sin marcarlo puede seguir usando la app en este dispositivo.","이메일을 적어 주세요.":"Escriba su correo electrónico.","비밀번호는 6자 이상이에요.":"La contraseña debe tener al menos 6 caracteres.","확인하는 중…":"Comprobando…","로그인했어요. 기록을 맞추는 중이에요.":"Ha iniciado sesión. Sincronizando sus registros.","메일함의 확인 링크를 먼저 눌러 주세요. 메일이 안 보이면 스팸함도 봐 주세요.":"Pulse primero el enlace de confirmación del correo. Si no lo ve, mire en spam.","이 메일로 만든 계정이 있어요. 비밀번호를 다시 확인해 주세요. 잊으셨으면 「비밀번호를 잊으셨나요」를 눌러 주세요.":"Ya hay una cuenta con este correo. Revise la contraseña. Si la ha olvidado, pulse “¿Ha olvidado la contraseña?”.","계정을 만들었어요. 기록을 올리는 중이에요.":"Cuenta creada. Subiendo sus registros.","처음이시군요. 메일함에 확인 링크를 보냈어요. 링크를 누른 뒤 여기서 다시 「메일로 계속하기」를 눌러 주세요.":"¡Bienvenido! Le hemos enviado un enlace de confirmación. Púlselo y vuelva aquí a pulsar “Continuar con correo”.","인터넷에 닿지 않아요. 연결된 뒤 다시 눌러 주세요. 기록은 이 기기에 그대로 있어요.":"No hay conexión a internet. Vuelva a intentarlo cuando tenga conexión. Sus registros siguen en este dispositivo.","잠시 너무 여러 번 시도했어요. 몇 분 뒤 다시 해 주세요.":"Demasiados intentos. Vuelva a intentarlo en unos minutos.","로그인이 되지 않았어요. 잠시 뒤 다시 해 주세요.":"No se pudo iniciar sesión. Vuelva a intentarlo en un momento.","비밀번호를 다시 정할 메일 주소를 위 칸에 적어 주세요.":"Escriba arriba el correo para restablecer la contraseña.","메일함에 비밀번호를 다시 정하는 링크를 보냈어요.":"Le hemos enviado un enlace para restablecer la contraseña.","메일을 보내지 못했어요. 잠시 뒤 다시 해 주세요.":"No se pudo enviar el correo. Vuelva a intentarlo en un momento.","로그인 없이 둘러보기":"Explorar sin iniciar sesión","둘러보셔도 기록은 이 기기에 남아요. 로그인은 언제든 화면 맨 위 「로그인」에서 하실 수 있어요.":"Mientras explora, sus registros se quedan en este dispositivo. Puede iniciar sesión cuando quiera con “Iniciar sesión” arriba.","{앱} 기록을 계정에 이어 두면 <b>폰을 바꿔도 그대로</b>예요.":"Si vincula sus registros de {앱} a una cuenta, <b>se conservan aunque cambie de teléfono</b>.","내 계정 — {메일}":"Mi cuenta — {메일}","만 14세 이상이에요":"Tengo 14 años o más","만 14세 이상만 계정을 만들 수 있어요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"Solo las personas de 14 años o más pueden crear una cuenta. Si es menor, puede seguir usando la app en este dispositivo sin iniciar sesión.","건강정보(민감정보) 서버 저장":"Guardar información de salud (datos sensibles) en el servidor","기록을 암호화된 연결로 보내 메디나눔 서버(서울)에 저장하고, 로그인한 기기에서 이어 쓰는 데 동의해요.":"Acepto que mis registros se envíen por una conexión cifrada y se guarden en el servidor de Medinanum en Seúl, y seguir usándolos en los dispositivos donde inicie sesión.","만 14세 미만":"Menor de 14","14~19세":"14–19 años","20대":"20–29","30대":"30–39","40대":"40–49","50대":"50–59","60대":"60–69","70대 이상":"70 o más","처음 한 번만 여쭤요. 나중에 설정에서 고치실 수 있어요.":"Solo se lo preguntamos una vez. Puede cambiarlo después en Ajustes.","고치실 것만 바꾸고 저장해 주세요.":"Cambie lo que necesite y guarde.","이름":"Nombre","성별":"Sexo","여성":"Mujer","남성":"Hombre","연령대":"Edad","생일":"Cumpleaños","(선택 · 생일 알림)":"(opcional · aviso de cumpleaños)","월":"Mes","일":"Día","연락 이메일":"Correo de contacto","(선택)":"(opcional)","로그인한 서비스의 프로필 사진 쓰기":"Usar la foto de perfil del servicio con el que inició sesión","저장":"Guardar","저장하는 중…":"Guardando…","이름·성별·연령대는 계정을 쓰는 데 필요해요. 생일·이메일·사진은 넣지 않으셔도 돼요.":"El nombre, el sexo y la edad son necesarios para la cuenta. El cumpleaños, el correo y la foto son opcionales.","프로필 만들기":"Crear su perfil","프로필 고치기":"Editar perfil","만 14세 미만은 계정을 쓸 수 없어요. 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"Los menores de 14 no pueden usar una cuenta. Puede seguir usando la app en este dispositivo sin iniciar sesión.","이름을 적어 주세요.":"Escriba su nombre.","성별을 골라 주세요.":"Elija su sexo.","연령대를 골라 주세요.":"Elija su edad.","생일은 월과 일을 함께 골라 주세요. 넣지 않으셔도 돼요.":"Elija mes y día de su cumpleaños, o déjelo en blanco.","이메일을 다시 확인해 주세요. 넣지 않으셔도 돼요.":"Revise el correo, o déjelo en blanco.","프로필을 저장했어요.":"Perfil guardado.","저장하지 못했어요. 잠시 뒤 다시 해 주세요.":"No se pudo guardar. Inténtelo de nuevo en un momento.","운영자 · 모든 기능":"Operador · todas las funciones","또는":"o","Google로 계속하기":"Continuar con Google","카카오로 계속하기":"Continuar con Kakao","네이버로 계속하기":"Continuar con Naver","또는 메일로":"o con correo","만 14세 이상인지 체크해 주세요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"Confirma que tienes 14 años o más. Si no, puedes seguir usando la app en este dispositivo sin iniciar sesión.","계속하려면 이 칸에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.":"Para continuar, marca esta casilla. Sin ella, puedes seguir usando la app en este dispositivo.","내 기기":"Mis dispositivos","이 기기":"Este dispositivo","마지막 사용":"Último uso","내보내기":"Cerrar sesión ahí","이 기기에서는 로그아웃":"Cerrar sesión en este dispositivo","이 계정으로 로그인한 기기예요. 계정 하나로 기기 두 대까지 쓸 수 있어요. 가족의 기록은 각자 계정으로 — 같은 계정이면 기록이 서로 보여요.":"Estos dispositivos tienen la sesión iniciada en esta cuenta. Una cuenta sirve para dos dispositivos como máximo. Cada familiar debe tener su propia cuenta: en una cuenta compartida, los registros se ven entre sí.","이 계정은 이미 두 대에서 쓰고 있어요. 이 기기에서 쓰시려면 아래에서 내보낼 기기를 직접 골라 주세요. 내보낸 기기는 로그아웃되고, 기록은 계정에 그대로 있어요.":"Esta cuenta ya se usa en dos dispositivos. Para usarla en este, elija abajo qué dispositivo quiere desconectar. Ese dispositivo saldrá de la cuenta; sus registros siguen en la cuenta.","가장 오래 안 쓴 기기":"El que lleva más tiempo sin usarse","내보냈어요. 이 기기에서 이어서 쓰실 수 있어요.":"Hecho. Puede seguir usándola en este dispositivo.","내보냈어요.":"Sesión cerrada.","다른 기기에서 이 기기를 내보냈어요. 다시 로그인하시면 이어서 쓸 수 있어요.":"Se cerró la sesión de este dispositivo desde otro. Inicie sesión de nuevo para continuar.","기기 목록을 불러오지 못했어요. 잠시 뒤 다시 해 주세요.":"No se pudo cargar la lista de dispositivos. Inténtelo de nuevo en un momento.","기기":"Dispositivo","Android 폰":"Teléfono Android","Android 태블릿":"Tableta Android","어떻게 지울까요?":"¿Cómo quiere borrar?","이 앱에서만 탈퇴":"Salir solo de esta app","이 앱의 서버 기록과 가입만 지워요. 다른 메디나눔 앱은 그대로 써요.":"Borra solo los registros del servidor y la inscripción de esta app. Las demás apps de MediNanum siguen igual.","메디나눔 계정 전체 삭제":"Borrar toda la cuenta MediNanum","다섯 앱의 서버 기록과 계정을 모두 지워요. 되돌릴 수 없어요.":"Borra los registros del servidor de las cinco apps y la cuenta. No se puede deshacer.","이 앱의 서버 기록과 가입을 지울까요? 되돌릴 수 없어요.":"¿Borrar los registros del servidor y la inscripción de esta app? No se puede deshacer.","이 앱에서 탈퇴했어요.":"Ha salido de esta app.","지우지 못했어요. 잠시 뒤 다시 해 주세요.":"No se pudo borrar. Inténtelo de nuevo en un momento.","지우기":"Borrar","취소":"Cancelar"},"ja":{"로그인":"ログイン","로그인 · 계정 만들기":"ログイン · アカウント作成","내 계정":"マイアカウント","계정":"アカウント","이용권":"利用券","동기화":"同期","아직":"まだ","로그인 전이에요":"ログイン前です","기록은 이 기기에 있어요. 로그인하면 폰을 바꿔도 이어져요.":"記録はこの端末にあります。ログインすれば機種変更しても続きます。","로그인됨":"ログイン中","지금 동기화":"今すぐ同期","로그아웃":"ログアウト","계정 지우기":"アカウントを削除","지금은 계정을 쓸 수 없어요. 기록은 이 기기에 그대로 있어요.":"今はアカウントを使えません。記録はこの端末にそのままあります。","계정은 준비 중이에요. 기록은 이 기기에 그대로 있어요.":"アカウントは準備中です。記録はこの端末にそのままあります。","이메일":"メールアドレス","비밀번호":"パスワード","(6자 이상)":"（6文字以上）","필수":"必須","무엇을 · 왜 · 언제까지 — 처리방침 보기":"何を · なぜ · いつまで — 処理方針を見る","메일로 계속하기":"メールで続ける","처음이시면 계정이 만들어지고, 있으시면 로그인돼요. 처음이면 메일함에 확인 링크가 가요.":"初めてならアカウントが作られ、すでにあればログインします。初めてのときはメールに確認リンクが届きます。","비밀번호를 잊으셨나요":"パスワードをお忘れですか","계속하려면 서버 저장 동의에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.":"続けるにはサーバー保存の同意にチェックしてください。チェックしなくてもこの端末でそのまま使えます。","이메일을 적어 주세요.":"メールアドレスを入力してください。","비밀번호는 6자 이상이에요.":"パスワードは6文字以上です。","확인하는 중…":"確認しています…","로그인했어요. 기록을 맞추는 중이에요.":"ログインしました。記録を合わせています。","메일함의 확인 링크를 먼저 눌러 주세요. 메일이 안 보이면 스팸함도 봐 주세요.":"まずメールの確認リンクを押してください。見当たらなければ迷惑メールも見てください。","이 메일로 만든 계정이 있어요. 비밀번호를 다시 확인해 주세요. 잊으셨으면 「비밀번호를 잊으셨나요」를 눌러 주세요.":"このメールで作ったアカウントがあります。パスワードをもう一度確認してください。お忘れなら「パスワードをお忘れですか」を押してください。","계정을 만들었어요. 기록을 올리는 중이에요.":"アカウントを作りました。記録を上げています。","처음이시군요. 메일함에 확인 링크를 보냈어요. 링크를 누른 뒤 여기서 다시 「메일로 계속하기」를 눌러 주세요.":"はじめまして。メールに確認リンクを送りました。リンクを押したあと、ここでもう一度「メールで続ける」を押してください。","인터넷에 닿지 않아요. 연결된 뒤 다시 눌러 주세요. 기록은 이 기기에 그대로 있어요.":"インターネットにつながりません。つながってからもう一度押してください。記録はこの端末にそのままあります。","잠시 너무 여러 번 시도했어요. 몇 분 뒤 다시 해 주세요.":"短い間に何度も試しました。数分後にもう一度お試しください。","로그인이 되지 않았어요. 잠시 뒤 다시 해 주세요.":"ログインできませんでした。少ししてからもう一度お試しください。","비밀번호를 다시 정할 메일 주소를 위 칸에 적어 주세요.":"パスワードを設定し直すメールアドレスを上の欄に書いてください。","메일함에 비밀번호를 다시 정하는 링크를 보냈어요.":"パスワードを設定し直すリンクをメールに送りました。","메일을 보내지 못했어요. 잠시 뒤 다시 해 주세요.":"メールを送れませんでした。少ししてからもう一度お試しください。","로그인 없이 둘러보기":"ログインせずに見てみる","둘러보셔도 기록은 이 기기에 남아요. 로그인은 언제든 화면 맨 위 「로그인」에서 하실 수 있어요.":"見ている間も記録はこの端末に残ります。ログインはいつでも画面上の「ログイン」からできます。","{앱} 기록을 계정에 이어 두면 <b>폰을 바꿔도 그대로</b>예요.":"{앱}の記録をアカウントにつないでおけば、<b>スマホを替えてもそのまま</b>です。","내 계정 — {메일}":"マイアカウント — {메일}","만 14세 이상이에요":"14歳以上です","만 14세 이상만 계정을 만들 수 있어요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"アカウントを作れるのは14歳以上の方だけです。そうでない方も、ログインせずにこの端末でそのまま使えます。","건강정보(민감정보) 서버 저장":"健康情報（要配慮個人情報）のサーバー保存","기록을 암호화된 연결로 보내 메디나눔 서버(서울)에 저장하고, 로그인한 기기에서 이어 쓰는 데 동의해요.":"記録を暗号化された接続で送り、メディナヌムのサーバー（ソウル）に保存して、ログインした端末で続けて使うことに同意します。","만 14세 미만":"14歳未満","14~19세":"14〜19歳","20대":"20代","30대":"30代","40대":"40代","50대":"50代","60대":"60代","70대 이상":"70代以上","처음 한 번만 여쭤요. 나중에 설정에서 고치실 수 있어요.":"最初に一度だけお尋ねします。あとで設定から直せます。","고치실 것만 바꾸고 저장해 주세요.":"直したいところだけ変えて保存してください。","이름":"名前","성별":"性別","여성":"女性","남성":"男性","연령대":"年代","생일":"誕生日","(선택 · 생일 알림)":"（任意 · 誕生日のお知らせ）","월":"月","일":"日","연락 이메일":"連絡用メール","(선택)":"（任意）","로그인한 서비스의 프로필 사진 쓰기":"ログインしたサービスのプロフィール写真を使う","저장":"保存","저장하는 중…":"保存中…","이름·성별·연령대는 계정을 쓰는 데 필요해요. 생일·이메일·사진은 넣지 않으셔도 돼요.":"名前・性別・年代はアカウントに必要です。誕生日・メール・写真は入れなくても大丈夫です。","프로필 만들기":"プロフィールを作る","프로필 고치기":"プロフィールを直す","만 14세 미만은 계정을 쓸 수 없어요. 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"14歳未満の方はアカウントを使えません。ログインせずにこの端末でそのまま使えます。","이름을 적어 주세요.":"名前を入力してください。","성별을 골라 주세요.":"性別を選んでください。","연령대를 골라 주세요.":"年代を選んでください。","생일은 월과 일을 함께 골라 주세요. 넣지 않으셔도 돼요.":"誕生日は月と日を一緒に選んでください。入れなくても大丈夫です。","이메일을 다시 확인해 주세요. 넣지 않으셔도 돼요.":"メールをもう一度確かめてください。入れなくても大丈夫です。","프로필을 저장했어요.":"プロフィールを保存しました。","저장하지 못했어요. 잠시 뒤 다시 해 주세요.":"保存できませんでした。少したってからもう一度お試しください。","운영자 · 모든 기능":"運営者 · すべての機能","또는":"または","Google로 계속하기":"Googleで続ける","카카오로 계속하기":"Kakaoで続ける","네이버로 계속하기":"NAVERで続ける","또는 메일로":"またはメールで","만 14세 이상인지 체크해 주세요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"14歳以上であることにチェックしてください。そうでない場合は、ログインせずにこの端末でそのままお使いいただけます。","계속하려면 이 칸에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.":"続けるには、この項目にチェックしてください。チェックしなくても、この端末でそのままお使いいただけます。","내 기기":"わたしの端末","이 기기":"この端末","마지막 사용":"最後に使った日","내보내기":"ログアウトさせる","이 기기에서는 로그아웃":"この端末でログアウトする","이 계정으로 로그인한 기기예요. 계정 하나로 기기 두 대까지 쓸 수 있어요. 가족의 기록은 각자 계정으로 — 같은 계정이면 기록이 서로 보여요.":"このアカウントでログインしている端末です。アカウント一つで端末二台まで使えます。家族の記録はそれぞれのアカウントで — 同じアカウントだと記録がお互いに見えます。","이 계정은 이미 두 대에서 쓰고 있어요. 이 기기에서 쓰시려면 아래에서 내보낼 기기를 직접 골라 주세요. 내보낸 기기는 로그아웃되고, 기록은 계정에 그대로 있어요.":"このアカウントはすでに二台で使われています。この端末で使うには、下からログアウトさせる端末を自分で選んでください。その端末はログアウトし、記録はアカウントにそのまま残ります。","가장 오래 안 쓴 기기":"いちばん長く使っていない端末","내보냈어요. 이 기기에서 이어서 쓰실 수 있어요.":"ログアウトさせました。この端末で続けて使えます。","내보냈어요.":"ログアウトさせました。","다른 기기에서 이 기기를 내보냈어요. 다시 로그인하시면 이어서 쓸 수 있어요.":"別の端末からこの端末がログアウトされました。もう一度ログインすれば続けて使えます。","기기 목록을 불러오지 못했어요. 잠시 뒤 다시 해 주세요.":"端末の一覧を読み込めませんでした。少ししてからもう一度お試しください。","기기":"端末","Android 폰":"Androidスマホ","Android 태블릿":"Androidタブレット","어떻게 지울까요?":"どのように消しますか？","이 앱에서만 탈퇴":"このアプリだけ退会","이 앱의 서버 기록과 가입만 지워요. 다른 메디나눔 앱은 그대로 써요.":"このアプリのサーバーの記録と登録だけを消します。ほかのメディナヌムのアプリはそのまま使えます。","메디나눔 계정 전체 삭제":"メディナヌムのアカウントをすべて消す","다섯 앱의 서버 기록과 계정을 모두 지워요. 되돌릴 수 없어요.":"5つのアプリのサーバーの記録とアカウントをすべて消します。元に戻せません。","이 앱의 서버 기록과 가입을 지울까요? 되돌릴 수 없어요.":"このアプリのサーバーの記録と登録を消しますか？元に戻せません。","이 앱에서 탈퇴했어요.":"このアプリを退会しました。","지우지 못했어요. 잠시 뒤 다시 해 주세요.":"消せませんでした。少ししてからもう一度お試しください。","지우기":"消す","취소":"やめる"},"zh":{"로그인":"登录","로그인 · 계정 만들기":"登录 · 创建账号","내 계정":"我的账号","계정":"账户","이용권":"使用权","동기화":"同步","아직":"尚未","로그인 전이에요":"尚未登录","기록은 이 기기에 있어요. 로그인하면 폰을 바꿔도 이어져요.":"记录在这台设备上。登录后换手机也能接着用。","로그인됨":"已登录","지금 동기화":"立即同步","로그아웃":"退出登录","계정 지우기":"删除账号","지금은 계정을 쓸 수 없어요. 기록은 이 기기에 그대로 있어요.":"现在无法使用账号。记录还在这台设备上。","계정은 준비 중이에요. 기록은 이 기기에 그대로 있어요.":"账号功能即将推出。记录还在这台设备上。","이메일":"邮箱","비밀번호":"密码","(6자 이상)":"（6 位以上）","필수":"必选","무엇을 · 왜 · 언제까지 — 처리방침 보기":"什么 · 为什么 · 保存多久——查看隐私政策","메일로 계속하기":"用邮箱继续","처음이시면 계정이 만들어지고, 있으시면 로그인돼요. 처음이면 메일함에 확인 링크가 가요.":"第一次使用会创建账号，已有账号就直接登录。新账号会收到一封确认链接邮件。","비밀번호를 잊으셨나요":"忘记密码了吗","계속하려면 서버 저장 동의에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.":"要继续，请勾选服务器存储同意。不勾选也可以在这台设备上照常使用。","이메일을 적어 주세요.":"请填写邮箱。","비밀번호는 6자 이상이에요.":"密码至少 6 位。","확인하는 중…":"正在确认…","로그인했어요. 기록을 맞추는 중이에요.":"已登录。正在同步记录。","메일함의 확인 링크를 먼저 눌러 주세요. 메일이 안 보이면 스팸함도 봐 주세요.":"请先点邮件里的确认链接。找不到的话也看看垃圾邮件箱。","이 메일로 만든 계정이 있어요. 비밀번호를 다시 확인해 주세요. 잊으셨으면 「비밀번호를 잊으셨나요」를 눌러 주세요.":"这个邮箱已有账号。请再确认密码。忘记了就点“忘记密码了吗”。","계정을 만들었어요. 기록을 올리는 중이에요.":"账号已创建。正在上传记录。","처음이시군요. 메일함에 확인 링크를 보냈어요. 링크를 누른 뒤 여기서 다시 「메일로 계속하기」를 눌러 주세요.":"欢迎！确认链接已发到您的邮箱。点了链接后，回来再点一次“用邮箱继续”。","인터넷에 닿지 않아요. 연결된 뒤 다시 눌러 주세요. 기록은 이 기기에 그대로 있어요.":"连不上网络。联网后再点一次。记录还在这台设备上。","잠시 너무 여러 번 시도했어요. 몇 분 뒤 다시 해 주세요.":"尝试次数过多。请过几分钟再试。","로그인이 되지 않았어요. 잠시 뒤 다시 해 주세요.":"没能登录。请稍后再试。","비밀번호를 다시 정할 메일 주소를 위 칸에 적어 주세요.":"请在上面填写要重设密码的邮箱。","메일함에 비밀번호를 다시 정하는 링크를 보냈어요.":"重设密码的链接已发到您的邮箱。","메일을 보내지 못했어요. 잠시 뒤 다시 해 주세요.":"邮件没发出去。请稍后再试。","로그인 없이 둘러보기":"不登录先看看","둘러보셔도 기록은 이 기기에 남아요. 로그인은 언제든 화면 맨 위 「로그인」에서 하실 수 있어요.":"浏览期间记录也会留在这台设备上。随时可以在页面顶部的“登录”登录。","{앱} 기록을 계정에 이어 두면 <b>폰을 바꿔도 그대로</b>예요.":"把{앱}的记录接到账号上，<b>换手机也不会丢</b>。","내 계정 — {메일}":"我的账号 — {메일}","만 14세 이상이에요":"我已满14岁","만 14세 이상만 계정을 만들 수 있어요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"只有年满14岁的人可以创建账号。未满14岁也可以不登录，在这台设备上照常使用。","건강정보(민감정보) 서버 저장":"在服务器上保存健康信息（敏感信息）","기록을 암호화된 연결로 보내 메디나눔 서버(서울)에 저장하고, 로그인한 기기에서 이어 쓰는 데 동의해요.":"我同意通过加密连接把记录发送并保存在 Medinanum 服务器（首尔），并在登录的设备上继续使用。","만 14세 미만":"未满14岁","14~19세":"14–19岁","20대":"20多岁","30대":"30多岁","40대":"40多岁","50대":"50多岁","60대":"60多岁","70대 이상":"70岁以上","처음 한 번만 여쭤요. 나중에 설정에서 고치실 수 있어요.":"只问一次，之后可以在设置里修改。","고치실 것만 바꾸고 저장해 주세요.":"只改需要改的地方，然后保存。","이름":"姓名","성별":"性别","여성":"女","남성":"男","연령대":"年龄段","생일":"生日","(선택 · 생일 알림)":"（可选 · 生日提醒）","월":"月","일":"日","연락 이메일":"联系邮箱","(선택)":"（可选）","로그인한 서비스의 프로필 사진 쓰기":"使用登录服务的头像","저장":"保存","저장하는 중…":"正在保存…","이름·성별·연령대는 계정을 쓰는 데 필요해요. 생일·이메일·사진은 넣지 않으셔도 돼요.":"姓名、性别、年龄段是使用账号所需的。生日、邮箱、照片可以不填。","프로필 만들기":"创建个人资料","프로필 고치기":"修改个人资料","만 14세 미만은 계정을 쓸 수 없어요. 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"未满14岁不能使用账号。不登录也可以在这台设备上照常使用。","이름을 적어 주세요.":"请填写姓名。","성별을 골라 주세요.":"请选择性别。","연령대를 골라 주세요.":"请选择年龄段。","생일은 월과 일을 함께 골라 주세요. 넣지 않으셔도 돼요.":"生日请同时选择月和日，也可以不填。","이메일을 다시 확인해 주세요. 넣지 않으셔도 돼요.":"请再检查一下邮箱，也可以不填。","프로필을 저장했어요.":"个人资料已保存。","저장하지 못했어요. 잠시 뒤 다시 해 주세요.":"保存失败，请稍后再试。","운영자 · 모든 기능":"运营者 · 全部功能","또는":"或","Google로 계속하기":"使用 Google 继续","카카오로 계속하기":"使用 Kakao 继续","네이버로 계속하기":"使用 NAVER 继续","또는 메일로":"或使用邮箱","만 14세 이상인지 체크해 주세요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.":"请勾选确认您已满14岁。如未满，可以不登录，继续在本设备上使用。","계속하려면 이 칸에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.":"如需继续，请勾选此项。不勾选也可以继续在本设备上使用。","내 기기":"我的设备","이 기기":"本设备","마지막 사용":"最近使用","내보내기":"移出","이 기기에서는 로그아웃":"改为在本设备退出登录","이 계정으로 로그인한 기기예요. 계정 하나로 기기 두 대까지 쓸 수 있어요. 가족의 기록은 각자 계정으로 — 같은 계정이면 기록이 서로 보여요.":"这些设备登录了此账号。一个账号最多可在两台设备上使用。家人的记录请各用自己的账号——同一账号下记录会互相看到。","이 계정은 이미 두 대에서 쓰고 있어요. 이 기기에서 쓰시려면 아래에서 내보낼 기기를 직접 골라 주세요. 내보낸 기기는 로그아웃되고, 기록은 계정에 그대로 있어요.":"此账号已在两台设备上使用。要在本设备使用，请在下面自己选择要移出的设备。被移出的设备会退出登录，记录仍保留在账号中。","가장 오래 안 쓴 기기":"最久未使用","내보냈어요. 이 기기에서 이어서 쓰실 수 있어요.":"已移出。可以在本设备继续使用。","내보냈어요.":"已移出。","다른 기기에서 이 기기를 내보냈어요. 다시 로그인하시면 이어서 쓸 수 있어요.":"此设备已被其他设备移出。重新登录即可继续使用。","기기 목록을 불러오지 못했어요. 잠시 뒤 다시 해 주세요.":"无法加载设备列表。请稍后再试。","기기":"设备","Android 폰":"安卓手机","Android 태블릿":"安卓平板","어떻게 지울까요?":"要怎样删除？","이 앱에서만 탈퇴":"只退出此应用","이 앱의 서버 기록과 가입만 지워요. 다른 메디나눔 앱은 그대로 써요.":"只删除此应用在服务器上的记录和注册。其他 Medinanum 应用照常使用。","메디나눔 계정 전체 삭제":"删除整个 Medinanum 账号","다섯 앱의 서버 기록과 계정을 모두 지워요. 되돌릴 수 없어요.":"删除五个应用在服务器上的全部记录和账号，无法恢复。","이 앱의 서버 기록과 가입을 지울까요? 되돌릴 수 없어요.":"删除此应用在服务器上的记录和注册？无法恢复。","이 앱에서 탈퇴했어요.":"已退出此应用。","지우지 못했어요. 잠시 뒤 다시 해 주세요.":"删除失败。请稍后再试。","지우기":"删除","취소":"取消"}};
  function 말언어() { var l = String((document.documentElement && document.documentElement.lang) || 'ko').toLowerCase().slice(0, 2); return 사전[l] ? l : 'ko'; }
  function 말(k) { var l = 말언어(); if (l === 'ko' || k == null) return k; if (사전[l][k]) return 사전[l][k]; var a = null; try { a = typeof 설정.말 === 'function' ? 설정.말(k, l) : (설정.말 && 설정.말[l] && 설정.말[l][k]); } catch (e) {} return a || k; }   /* 부품 사전이 먼저 — 앱 사전에서 「빠진 말」로 잘못 세지 않게 */   /* 설정.말 = { en: {…} } 또는 function(한국어, 말) — 앱 사전을 그대로 빌려 쓸 수 있다 */
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function 부름(f, 기본) { try { return typeof f === 'function' ? f() : 기본; } catch (e) { return 기본; } }
  function 알림(t) {
    // 11-03 현욱님 「메일로 계속하기 눌러도 안 넘어간다」 — 앱 알림 띠가 시트 뒤에 가려져 안내가 안 보였다. 시트 안 안내 줄에도 같은 글을 쓴다.
    try { var say = document.getElementById('acct-say'); if (say) { say.textContent = 말(t); say.hidden = false; if (say.scrollIntoView) say.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); } } catch (e) {}
    try { if (typeof 설정.알림 === 'function') return 설정.알림(말(t)); } catch (e) {}
  }
  function 시트(html, 제목) { try { if (typeof 설정.시트열기 === 'function') return 설정.시트열기(html, 제목); } catch (e) {} }
  function 닫기() { try { if (typeof 설정.시트닫기 === 'function') 설정.시트닫기(); } catch (e) {} }
  function 서버() { return window.서버 && typeof window.서버.준비 === 'function' ? window.서버 : null; }
  function 켜짐() { var s = 서버(); try { return !!(s && (!s.준비됨 || s.준비됨())); } catch (e) { return false; } }
  function 열림() { return 켜짐() && 부름(설정.열림, true) !== false; }
  function 세션() { var s = 서버(); try { return s && s.세션 ? s.세션() : null; } catch (e) { return null; } }
  function 상태() { try { return JSON.parse(localStorage.getItem('_srv_' + 설정.app) || '{}') || {}; } catch (e) { return {}; } }
  function 상태쓰기(o) { try { localStorage.setItem('_srv_' + 설정.app, JSON.stringify(o)); } catch (e) {} }
  function 메일() { var s = 세션(); if (!s || !s.user) return ''; var u = s.user, m = u.user_metadata || {}; return u.email || m.email || m.name || '계정'; }
  function 첫글자() { var m = 메일(); return m ? m.charAt(0).toUpperCase() : ''; }
  /* 메일 속 돌아올 주소 — 설치 앱은 location 이 https://localhost 라 메일 링크가 죽는다(허브 §3) → 앱이 준 웹 주소를 먼저 */
  function 네이티브() { try { return !!(window.Capacitor && typeof window.Capacitor.isNativePlatform === 'function' && window.Capacitor.isNativePlatform()); } catch (e) { return false; } }
  function 앱주소() { try { if (설정.웹주소) return 설정.웹주소; if (네이티브() || /localhost|127\.0\.0\.1/.test(location.hostname)) return ''; return /^https?:/.test(location.protocol) ? location.origin + location.pathname : ''; } catch (e) { return ''; } }

  var 사람 = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20c1.4-3.6 4.2-5.5 7.5-5.5s6.1 1.9 7.5 5.5"/></svg>';
  /* ── 머리 단추 ── */
  function 머리단추HTML() {
    var 글 = 첫글자();
    return 글 ? '<button type="button" class="acctbtn in" onclick="계정.열기()" aria-label="' + esc(말('내 계정 — {메일}').replace('{메일}', 메일())) + '"><span aria-hidden="true">' + esc(글) + '</span></button>'
      : '<button type="button" class="acctbtn" onclick="계정.열기()" aria-label="' + 말('로그인 · 계정 만들기') + '">' + 사람.replace('<svg ', '<svg class="acct-ic" ') + '<span class="acct-lb">' + 말('로그인') + '</span></button>';   /* 아주 좁은 폰은 앱 CSS 가 글 대신 사람 그림만 */
  }
  var 지난 = null;
  function 머리단추새로(굳이) {
    var 지금 = 메일();
    if (!굳이 && 지금 === 지난) return;
    if (지난 === '' && 지금 && !굳이) setTimeout(프로필확인, 600);
    if ((지난 === '' || 지난 === null) && 지금 && !굳이) setTimeout(function () { 기기확인(false); }, 1100);   /* 기기두대1110 — 앱을 열 때·소셜 로그인으로 돌아온 때 */   /* 프로필1030 — 소셜 로그인으로 돌아와 로그인이 막 생긴 때 */
    if (!지금) { 프.줄 = null; 프.읽음 = false; }
    지난 = 지금;
    var 새 = 머리단추HTML();
    [].forEach.call(document.querySelectorAll('.acctbtn'), function (b) { var t = document.createElement('div'); t.innerHTML = 새; b.parentNode.replaceChild(t.firstChild, b); });
    var 카 = document.getElementById('acctcard'); if (카) 카.outerHTML = 카드HTML();
  }

  /* ── 이용권 · 동기화 줄 ── */
  function 이용권() { var t = 부름(설정.이용권글, ''); try { if (window.가입 && 가입.운영자 && 가입.운영자()) t = 말('운영자 · 모든 기능'); } catch (e) {}   /* 10-30 */ return t ? '<div class="acct-row"><i>' + 말('이용권') + '</i><b>' + esc(t) + '</b></div>' : ''; }
  function 동기화줄() {
    var st = 서버() && 서버().상태 ? 부름(서버().상태, {}) : 상태(), t = st && (st.last_push || st.last_pull);
    var 언제 = t ? new Date(t).toLocaleString(말언어() === 'ko' ? 'ko-KR' : 말언어(), { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 말('아직');
    return '<div class="acct-row"><i>' + 말('동기화') + '</i><b>' + esc(언제) + '</b></div>';
  }

  /* 10-30 현욱님 실사용 — 「가입 동의 전이라 동기화를 멈춰 두었어요」가 떴다. 이 앱 약관은 첫 화면에서 이미 동의했으니 가입 부품이 조용히 가입하게,
     표시를 localStorage 에 둔다(메일 확인 링크로 새 탭에 돌아옴 · 소셜 돌아옴 · 다른 기기에서 로그인 — 그 기기에서도 첫 화면 동의를 했으니). 가입 부품이 가입한 뒤 지운다. */
  function 가입표시() { try { localStorage.setItem('_join_signup_' + 설정.app, '1'); } catch (e) {} }
  /* 프로필1030 — 가입 프로필 한 화면. 설정.프로필켜짐(함수 또는 참/거짓)이 참일 때만 묻고 보인다 */
  var 나이칸 = [['u14', '만 14세 미만'], ['14-19', '14~19세'], ['20-29', '20대'], ['30-39', '30대'], ['40-49', '40대'], ['50-59', '50대'], ['60-69', '60대'], ['70+', '70대 이상']];
  var 프 = { 줄: null, 읽음: false, 고름: {} };
  function 프로필켜짐() { return 열림() && 부름(typeof 설정.프로필켜짐 === 'function' ? 설정.프로필켜짐 : function () { return !!설정.프로필켜짐; }, false) === true; }
  function 사용자() { var s = 세션(); return s && s.user ? s.user : null; }
  function 소셜() { var u = 사용자(); var p = u && u.app_metadata && u.app_metadata.provider; return p && p !== 'email' ? p : ''; }
  function 미리값() {   /* 소셜이 준 값 — 구글(full_name·picture) · 카카오(name/nickname·avatar_url) · 네이버(naver-login 이 둔 name·gender·age_range·birthday·contact_email·avatar_url) */
    var u = 사용자() || {}, m = u.user_metadata || {};
    var 나 = String(m.age_range || '').replace(/^(\d0)-(\d)9$/, '$1-$29');
    var 생 = String(m.birthday || '').replace(/^(\d{2})(\d{2})$/, '$1-$2');
    return { name: String(m.full_name || m.name || m.nickname || m.user_name || '').slice(0, 40),
      gender: /^(f|female|여)/i.test(m.gender || '') ? 'female' : /^(m|male|남)/i.test(m.gender || '') ? 'male' : '',
      age_range: 나칸있나(나) ? 나 : '', birthday: /^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.test(생) ? 생 : '',
      contact_email: 소셜() ? String(m.contact_email || m.email || u.email || '').slice(0, 254) : '',
      avatar_url: /^https:\/\//.test(m.avatar_url || m.picture || '') ? String(m.avatar_url || m.picture).slice(0, 500) : '' };
  }
  function 필수(k) { return (설정.프로필필수 || []).indexOf(k) >= 0 || k === 'age_range'; }   /* 연령대는 만 14세 확인이라 늘 필수 */
  function 나칸있나(v) { return 나이칸.some(function (x) { return x[0] === v && v !== 'u14'; }); }
  function 프로필읽기() {
    var u = 사용자(); if (!u || !서버()) return Promise.resolve(null);
    return 서버().준비().then(function (sb) { return sb.from('profiles').select('name,gender,age_range,birthday,contact_email,avatar_url').eq('user_id', u.id).maybeSingle(); })
      .then(function (r) { 프.읽음 = true; 프.줄 = r && !r.error ? r.data : null; return 프.줄; }, function () { return null; });
  }
  function 프로필확인() {   /* 로그인 직후 — 비었으면 한 화면 */
    if (!프로필켜짐() || !사용자()) return;
    프로필읽기().then(function (줄) { if (!줄 || !줄.age_range || (필수('name') && !줄.name) || (필수('gender') && !줄.gender)) 프로필열기(true); });
  }
  function 칩(묶음, v, 글, on) { return '<button type="button" class="acct-chip' + (on ? ' on' : '') + '" aria-pressed="' + (on ? 'true' : 'false') + '" onclick="계정.프로필고름(\'' + 묶음 + '\',\'' + v + '\',this)">' + esc(말(글)) + '</button>'; }
  function 프로필열기(처음) {
    if (!프로필켜짐()) return;
    var 줄 = 프.줄 || {}, 미 = 미리값(), 값 = {}; ['name', 'gender', 'age_range', 'birthday', 'contact_email', 'avatar_url'].forEach(function (k) { 값[k] = 줄[k] || 미[k] || ''; });
    프.고름 = { gender: 값.gender, age_range: 값.age_range, avatar: !!값.avatar_url, avatar_url: 값.avatar_url };
    var 달 = 값.birthday ? 값.birthday.slice(0, 2) : '', 날 = 값.birthday ? 값.birthday.slice(3, 5) : '';
    function 고르개(id, 끝, 고른, 글) { var o = '<option value="">' + esc(말(글)) + '</option>'; for (var i = 1; i <= 끝; i++) { var v = (i < 10 ? '0' : '') + i; o += '<option value="' + v + '"' + (v === 고른 ? ' selected' : '') + '>' + i + '</option>'; } return '<select id="' + id + '" class="acct-sel">' + o + '</select>'; }
    var h = '<div class="acctsheet acct-prof">'
      + '<p class="acct-lead">' + 말(처음 ? '처음 한 번만 여쭤요. 나중에 설정에서 고치실 수 있어요.' : '고치실 것만 바꾸고 저장해 주세요.') + '</p>'
      + '<label for="pfName">' + 말('이름') + (필수('name') ? ' <span class="acct-req">' + 말('필수') + '</span>' : ' <span class="acct-dim">' + 말('(선택)') + '</span>') + '</label><input id="pfName" type="text" autocomplete="name" maxlength="40" value="' + esc(값.name) + '">'
      + '<label>' + 말('성별') + (필수('gender') ? ' <span class="acct-req">' + 말('필수') + '</span>' : ' <span class="acct-dim">' + 말('(선택)') + '</span>') + '</label><div class="acct-chips" role="group">' + 칩('gender', 'female', '여성', 값.gender === 'female') + 칩('gender', 'male', '남성', 값.gender === 'male') + '</div>'
      + '<label>' + 말('연령대') + ' <span class="acct-req">' + 말('필수') + '</span></label><div class="acct-chips" role="group">' + 나이칸.map(function (x) { return 칩('age_range', x[0], x[1], 값.age_range === x[0]); }).join('') + '</div>'
      + '<label>' + 말('생일') + ' <span class="acct-dim">' + 말('(선택 · 생일 알림)') + '</span></label><div class="acct-birth">' + 고르개('pfMon', 12, 달, '월') + 고르개('pfDay', 31, 날, '일') + '</div>'
      + (소셜() ? '<label for="pfMail">' + 말('연락 이메일') + ' <span class="acct-dim">' + 말('(선택)') + '</span></label><input id="pfMail" type="email" inputmode="email" autocomplete="email" value="' + esc(값.contact_email) + '">' : '')
      + (값.avatar_url ? '<label class="acct-chk"><input type="checkbox" id="pfPic"' + (프.고름.avatar ? ' checked' : '') + '><span>' + 말('로그인한 서비스의 프로필 사진 쓰기') + ' <span class="acct-dim">' + 말('(선택)') + '</span></span></label>' : '')
      + '<button type="button" class="acct-main" id="pfGo" onclick="계정.프로필저장()">' + 말('저장') + '</button>'
      + '<p class="acct-tiny">' + 말('이름·성별·연령대는 계정을 쓰는 데 필요해요. 생일·이메일·사진은 넣지 않으셔도 돼요.') + '</p>'
      + '</div>';
    시트(h, 말(처음 ? '프로필 만들기' : '프로필 고치기'));
  }
  function 프로필고름(묶음, v, b) {
    프.고름[묶음] = v;
    if (b && b.parentNode) [].forEach.call(b.parentNode.querySelectorAll('.acct-chip'), function (x) { var on = x === b; x.classList.toggle('on', on); x.setAttribute('aria-pressed', on ? 'true' : 'false'); });
    if (묶음 === 'age_range' && v === 'u14') 알림('만 14세 미만은 계정을 쓸 수 없어요. 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.');
  }
  function 프로필저장() {
    var 이름 = String((document.getElementById('pfName') || {}).value || '').trim().slice(0, 40);
    var 고 = 프.고름 || {};
    if (!이름 && 필수('name')) { 알림('이름을 적어 주세요.'); return; }
    if (!고.gender && 필수('gender')) { 알림('성별을 골라 주세요.'); return; }
    if (!고.age_range) { 알림('연령대를 골라 주세요.'); return; }
    if (고.age_range === 'u14') { 알림('만 14세 미만은 계정을 쓸 수 없어요. 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.'); 닫기(); 나가기(); return; }
    var 달 = (document.getElementById('pfMon') || {}).value || '', 날 = (document.getElementById('pfDay') || {}).value || '';
    if ((달 && !날) || (!달 && 날)) { 알림('생일은 월과 일을 함께 골라 주세요. 넣지 않으셔도 돼요.'); return; }
    var 메 = String((document.getElementById('pfMail') || {}).value || '').trim();
    if (메 && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(메)) { 알림('이메일을 다시 확인해 주세요. 넣지 않으셔도 돼요.'); return; }
    var 사진 = document.getElementById('pfPic');
    var u = 사용자(); if (!u || !서버()) return;
    var 줄 = { user_id: u.id, name: 이름 || null, gender: 고.gender || null, age_range: 고.age_range, birthday: 달 && 날 ? 달 + '-' + 날 : null,
      contact_email: 메 || null, avatar_url: 사진 && 사진.checked ? (고.avatar_url || null) : null, source: 소셜() || 'email' };
    var b = document.getElementById('pfGo'); if (b) { b.disabled = true; b.textContent = 말('저장하는 중…'); }
    서버().준비().then(function (sb) { return sb.from('profiles').upsert(줄, { onConflict: 'user_id' }); }).then(function (r) {
      if (r && r.error) throw r.error;
      프.줄 = 줄; 프.읽음 = true; 알림('프로필을 저장했어요.'); 닫기(); 머리단추새로(true);
    }).catch(function () { 알림('저장하지 못했어요. 잠시 뒤 다시 해 주세요.'); if (b) { b.disabled = false; b.textContent = 말('저장'); } });
  }

  /* ── 설정 맨 위 카드 ── */
  function 카드HTML() {
    var h = '<div id="acctcard" class="acctcard">';
    if (!열림()) return h + '<div class="acct-me"><span class="acct-av off" aria-hidden="true">' + 사람 + '</span><div><b>' + 말('계정') + '</b><span>' + esc(닫힘까닭()) + '</span></div></div></div>';
    var m = 메일();
    if (!m) return h + '<div class="acct-me"><span class="acct-av off" aria-hidden="true">' + 사람 + '</span><div><b>' + 말('로그인 전이에요') + '</b><span>' + 말('기록은 이 기기에 있어요. 로그인하면 폰을 바꿔도 이어져요.') + '</span></div></div>'
      + '<button type="button" class="acct-main" onclick="계정.열기()">' + 말('로그인 · 계정 만들기') + '</button></div>';
    return h + '<div class="acct-me"><span class="acct-av" aria-hidden="true">' + esc(첫글자()) + '</span><div><b>' + esc(m) + '</b><span>' + 말('로그인됨') + '</span></div></div>'
      + 이용권() + 동기화줄()
      + (프로필켜짐() ? '<button type="button" class="acct-link" onclick="계정.프로필()">' + 말('프로필 고치기') + '</button>' : '')   /* 프로필1030 */
      + '<div class="acct-btns"><button type="button" onclick="계정.동기화()">' + 말('지금 동기화') + '</button><button type="button" onclick="계정.나가기()">' + 말('로그아웃') + '</button></div>'
      + '<button type="button" class="acct-del" onclick="계정.지우기()">' + 말('계정 지우기') + '</button></div>';
  }
  function 닫힘까닭() { var t = 부름(설정.닫힘까닭, ''); return t || 말(켜짐() ? '지금은 계정을 쓸 수 없어요. 기록은 이 기기에 그대로 있어요.' : '계정은 준비 중이에요. 기록은 이 기기에 그대로 있어요.'); }

  /* ── 계정 시트 (한 화면) ── */
  function 로그인HTML() {
    var st = 상태(), 동 = 부름(설정.동의됨, false);
    var 소 = 소셜HTML();   /* 10-31 소아 검수 — 소셜 단추를 맨 위로(어르신은 한 번 누르기가 쉽다). 순서: 동의 체크 → 소셜 → 「또는 메일로」 → 메일 칸 */
    var 체크 = ''
      + (동 || !설정.나이글 ? '' : '<label class="acct-chk"><input type="checkbox" id="acctAge"><span>' + esc(말(설정.나이글)) + ' <span class="acct-req">' + 말('필수') + '</span></span></label>')   /* 10-29 한 번 시작 — 만 14세 확인은 계정 만들 때 */
      + (동 ? '' : '<label class="acct-chk"><input type="checkbox" id="acctAgree"><span>' + (설정.동의이름 ? '<b>' + esc(말(설정.동의이름)) + '</b> — ' : '') + esc(말(설정.동의글 || '기록을 암호화된 연결로 보내 메디나눔 서버(서울)에 저장하고, 로그인한 기기에서 이어 쓰는 데 동의해요.')) + ' <span class="acct-req">' + 말('필수') + '</span></label>'
          + (설정.처리방침 ? '<button type="button" class="acct-link" onclick="계정.처리방침()">' + 말('무엇을 · 왜 · 언제까지 — 처리방침 보기') + '</button>' : ''));
    return '<div class="acctsheet">'
      + '<p class="acct-lead">' + 말('{앱} 기록을 계정에 이어 두면 <b>폰을 바꿔도 그대로</b>예요.').replace('{앱}', esc(말(설정.앱이름))) + '</p>'
      + (소 ? 체크 + 소 + '<div class="acct-or"><span>' + 말('또는 메일로') + '</span></div>' : '')
      + '<label for="srvEmail">' + 말('이메일') + '</label><input id="srvEmail" type="email" inputmode="email" autocomplete="email" enterkeyhint="next" value="' + esc(st.email || '') + '">'
      + '<label for="srvPw">' + 말('비밀번호') + ' <span class="acct-dim">' + 말('(6자 이상)') + '</span></label><input id="srvPw" type="password" autocomplete="current-password" enterkeyhint="go">'
      + (소 ? '' : 체크)
      + '<button type="button" class="acct-main" id="acctGo" onclick="계정.계속()">' + 말('메일로 계속하기') + '</button><p id="acct-say" class="acct-say" role="status" aria-live="polite" hidden></p>'
      + '<p class="acct-tiny">' + 말('처음이시면 계정이 만들어지고, 있으시면 로그인돼요. 처음이면 메일함에 확인 링크가 가요.') + '</p>'
      + '<button type="button" class="acct-link" onclick="계정.비번()">' + 말('비밀번호를 잊으셨나요') + '</button>'
      + '</div>';
  }
  /* 소셜 로그인 단추 — 서버 부품이 켠 것만. 동의 체크는 메일과 같은 자리·같은 검사(동의확인)를 거친다 */
  var 소셜글 = { google: 'Google로 계속하기', kakao: '카카오로 계속하기', naver: '네이버로 계속하기' };
  var 소셜꼴 = { google: 'background:#fff;color:#1f1f1f;border:1px solid #747775', kakao: 'background:#FEE500;color:rgba(0,0,0,.85);border:0', naver: 'background:#03C75A;color:#fff;border:0' };
  var 소셜그림 = { google: '<svg viewBox="0 0 48 48" width="18" height="18" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>',
    kakao: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#000" d="M12 3C6.48 3 2 6.58 2 11c0 2.85 1.86 5.35 4.66 6.77l-.95 3.5c-.08.3.26.54.52.37l4.14-2.75c.53.07 1.08.11 1.63.11 5.52 0 10-3.58 10-8S17.52 3 12 3z"/></svg>',
    naver: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="#fff" d="M16.273 12.845 7.376 0H0v24h7.726V11.156L16.624 24H24V0h-7.727z"/></svg>' };
  function 소셜목록() { try { return window.서버 && typeof window.서버.소셜 === 'function' ? window.서버.소셜() : []; } catch (e) { return []; } }
  function 소셜HTML() {
    var l = 소셜목록().filter(function (p) { return 소셜글[p]; }); if (!l.length) return '';
    return l.map(function (p) {
      return '<button type="button" class="acct-soc" style="' + 소셜꼴[p] + '" onclick="계정.소셜(\'' + p + '\')">' + 소셜그림[p] + '<span>' + 말(소셜글[p]) + '</span></button>';
    }).join('');
  }
  function 소셜(p) {
    if (소셜목록().indexOf(p) < 0) return;
    if (!동의확인()) return;
    try { if (window.가입 && typeof 가입.이앱가입 === 'function') 가입.이앱가입(); } catch (e) {}
    가입표시();
    동작(p);
  }
  function 열기() {
    if (!열림()) { 시트('<div class="acctsheet">' + 카드HTML() + '</div>', 말('계정')); return; }
    if (메일()) { 시트('<div class="acctsheet">' + 카드HTML() + '</div>', 말('내 계정')); return; }
    시트(로그인HTML(), 말('로그인 · 계정 만들기'));
    if (!소셜목록().length) setTimeout(function () { var e = document.getElementById(상태().email ? 'srvPw' : 'srvEmail'); if (e) try { e.focus({ preventScroll: true }); } catch (x) {} }, 120);
  }
  var 바쁨 = false;
  function 단추글(t, 끔) { var b = document.getElementById('acctGo'); if (b) { b.textContent = 말(t); b.disabled = !!끔; } }
  /* 11-03 — 알림 띠는 시트 뒤에 깔려 안 보였다(현욱님 폰: 「눌러도 진행이 안 돼요」). 빠진 체크 칸 바로 아래에 빨간 글로 알리고 그 칸으로 데려간다 */
  function 칸경고(c, 글) {
    var 칸 = c && c.closest ? c.closest('.acct-chk') : null;
    try { [].forEach.call(document.querySelectorAll('.acct-err'), function (e) { e.remove(); }); [].forEach.call(document.querySelectorAll('.acct-chk.bad'), function (e) { e.classList.remove('bad'); }); } catch (e) {}
    if (!칸) { 알림(글); return; }
    칸.classList.add('bad');
    var p = document.createElement('p'); p.className = 'acct-err'; p.setAttribute('role', 'alert'); p.textContent = 말(글);
    칸.parentNode.insertBefore(p, 칸.nextSibling);
    try { 칸.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) {}
    try { c.focus({ preventScroll: true }); } catch (e) {}
    c.addEventListener('change', function 풀기() { if (c.checked) { 칸.classList.remove('bad'); if (p.parentNode) p.remove(); } }, { once: true });
  }
  function 동의확인() {
    if (부름(설정.동의됨, false)) return true;
    var 나 = document.getElementById('acctAge');
    if (나 && !나.checked) { 칸경고(나, '만 14세 이상인지 체크해 주세요. 아니시면 로그인 없이 이 기기에서 그대로 쓰실 수 있어요.'); return false; }
    var c = document.getElementById('acctAgree');
    if (!c || !c.checked) { 칸경고(c, '계속하려면 이 칸에 체크해 주세요. 체크하지 않으셔도 이 기기에서 그대로 쓰실 수 있어요.'); return false; }
    try { if (typeof 설정.동의하기 === 'function') 설정.동의하기(); } catch (e) {}
    return true;
  }
  function 성공(말) {
    var st = 상태(), m = 메일(); if (m && m.indexOf('@') > 0) st.email = m; 상태쓰기(st);
    알림(말); 머리단추새로(true);
    try { if (typeof 설정.다시그리기 === 'function') 설정.다시그리기(); } catch (e) {}
    닫기();
    setTimeout(프로필확인, 400);   /* 프로필1030 */
    setTimeout(function () { 기기확인(true); }, 900);   /* 기기두대1110 */
  }
  function 계속() {
    if (바쁨) return;
    var email = String((document.getElementById('srvEmail') || {}).value || '').trim(), pw = String((document.getElementById('srvPw') || {}).value || '');
    if (!email || email.indexOf('@') < 1) { 알림('이메일을 적어 주세요.'); return; }
    if (pw.length < 6) { 알림('비밀번호는 6자 이상이에요.'); return; }
    if (!동의확인()) return;
    var st = 상태(); st.email = email; 상태쓰기(st);
    /* 앱 약관은 첫 화면에서 이미 동의했다 — 가입 부품이 로그인 뒤 「이 앱 가입」 시트를 또 띄우지 않고 조용히 가입하게 표시해 둔다 */
    try { if (window.가입 && typeof 가입.이앱가입 === 'function') 가입.이앱가입(); } catch (e) {}
    가입표시();   /* 10-30 — sessionStorage 만으로는 메일 확인 링크(새 탭)에서 사라졌다 */
    바쁨 = true; 단추글('확인하는 중…', true);
    var sbr = null;
    서버().준비().then(function (sb) { sbr = sb; return sb.auth.signInWithPassword({ email: email, password: pw }); }).then(function (r) {
      if (r && !r.error) return 성공('로그인했어요. 기록을 맞추는 중이에요.');
      var m = String((r && r.error && r.error.message) || '');
      if (/not confirmed/i.test(m)) { 알림('메일함의 확인 링크를 먼저 눌러 주세요. 메일이 안 보이면 스팸함도 봐 주세요.'); return; }
      if (!/invalid login credentials/i.test(m)) throw r.error;
      /* 없는 계정이거나 비밀번호가 틀렸다 — 만들어 보고, 이미 있으면(identities 빈 배열) 비밀번호 탓이라고 말한다 */
      var 주소 = 앱주소();
      return sbr.auth.signUp(주소 ? { email: email, password: pw, options: { emailRedirectTo: 주소 } } : { email: email, password: pw }).then(function (r2) {
        if (r2 && r2.error) { if (/already registered|already exists/i.test(r2.error.message || '')) { 알림('이 메일로 만든 계정이 있어요. 비밀번호를 다시 확인해 주세요. 잊으셨으면 「비밀번호를 잊으셨나요」를 눌러 주세요.'); return; } throw r2.error; }
        var u = r2 && r2.data && r2.data.user;
        if (u && Array.isArray(u.identities) && u.identities.length === 0) { 알림('이 메일로 만든 계정이 있어요. 비밀번호를 다시 확인해 주세요. 잊으셨으면 「비밀번호를 잊으셨나요」를 눌러 주세요.'); return; }
        if (r2 && r2.data && r2.data.session) return 성공('계정을 만들었어요. 기록을 올리는 중이에요.');
        알림('처음이시군요. 메일함에 확인 링크를 보냈어요. 링크를 누른 뒤 여기서 다시 「메일로 계속하기」를 눌러 주세요.');
      });
    }).catch(function (e) {
      var m = String((e && e.message) || '');
      알림(/fetch|network|lib/i.test(m) ? '인터넷에 닿지 않아요. 연결된 뒤 다시 눌러 주세요. 기록은 이 기기에 그대로 있어요.' : /rate|too many/i.test(m) ? '잠시 너무 여러 번 시도했어요. 몇 분 뒤 다시 해 주세요.' : '로그인이 되지 않았어요. 잠시 뒤 다시 해 주세요.');
    }).then(function () { 바쁨 = false; 단추글('메일로 계속하기', false); });
  }
  function 비번() {
    var email = String((document.getElementById('srvEmail') || {}).value || '').trim();
    if (!email || email.indexOf('@') < 1) { 알림('비밀번호를 다시 정할 메일 주소를 위 칸에 적어 주세요.'); var e = document.getElementById('srvEmail'); if (e) e.focus(); return; }
    if (!동의확인()) return;
    var 주소 = 앱주소();
    서버().준비().then(function (sb) { return 주소 ? sb.auth.resetPasswordForEmail(email, { redirectTo: 주소 }) : sb.auth.resetPasswordForEmail(email); })
      .then(function (r) { if (r && r.error) throw r.error; 알림('메일함에 비밀번호를 다시 정하는 링크를 보냈어요.'); })
      .catch(function () { 알림('메일을 보내지 못했어요. 잠시 뒤 다시 해 주세요.'); });
  }
  function 동작(what) { try { if (typeof window.계정동작 === 'function') return Promise.resolve(window.계정동작(what)); } catch (e) {} return Promise.resolve(); }
  function 나가기() { return 동작('logout').then(function () { 머리단추새로(true); try { if (typeof 설정.다시그리기 === 'function') 설정.다시그리기(); } catch (e) {} }); }
  function 동기화() { return 동작('sync').then(function () { 머리단추새로(true); }); }
  function 지우기전부() { return 동작('delete').then(function () { setTimeout(function () { 머리단추새로(true); }, 400); }); }
  /* 11-11 현욱님 「앱별 가입」 — 지우기 둘: 이 앱에서만 탈퇴(그 앱 기록·가입만 · delete_own_account(p_app)) / 메디나눔 계정 전체 삭제(앱의 기존 지우기). 설치({ 지우기둘: true })일 때만 */
  function 지우기() {
    if (부름(설정.지우기둘, false) !== true && 설정.지우기둘 !== true) return 지우기전부();
    시트('<div class="acctsheet"><p class="acct-lead">' + esc(말('어떻게 지울까요?')) + '</p>'
      + '<button type="button" class="acct-alt" onclick="계정.이앱탈퇴()">' + esc(말('이 앱에서만 탈퇴')) + '</button><p class="acct-tiny">' + esc(말('이 앱의 서버 기록과 가입만 지워요. 다른 메디나눔 앱은 그대로 써요.')) + '</p>'
      + '<button type="button" class="acct-alt" onclick="계정.전부지우기()">' + esc(말('메디나눔 계정 전체 삭제')) + '</button><p class="acct-tiny">' + esc(말('다섯 앱의 서버 기록과 계정을 모두 지워요. 되돌릴 수 없어요.')) + '</p></div>', 말('계정 지우기'));
    return Promise.resolve();
  }
  function 이앱탈퇴(확정) {   /* 11-11 CS — confirm() 은 웹뷰에서 막혀 아무 일도 안 했다 → 시트 안에서 한 번 더 묻는다(붉은 지우기 · 취소) */
    if (확정 !== true) {
      시트('<div class="acctsheet"><p class="acct-lead">' + esc(말('이 앱의 서버 기록과 가입을 지울까요? 되돌릴 수 없어요.')) + '</p>'
        + '<button type="button" class="acct-alt acct-danger" style="background:#B42318;color:#fff;border-color:#B42318" onclick="계정.이앱탈퇴(true)">' + esc(말('지우기')) + '</button>'
        + '<button type="button" class="acct-alt" onclick="계정.기기닫기()">' + esc(말('취소')) + '</button></div>', 말('이 앱에서만 탈퇴'));
      return Promise.resolve(false);
    }
    return 서버().준비().then(function (sb) { return sb.rpc('delete_own_account', { p_app: 설정.app }); }).then(function (r) {
      if (r && r.error) throw r.error; 닫기(); 알림(말('이 앱에서 탈퇴했어요.')); return 나가기(); }).catch(function () { 알림(말('지우지 못했어요. 잠시 뒤 다시 해 주세요.')); });
  }

  /* ── 온보딩 끝 두 단추 — 같은 크기, 둘러보기도 떳떳하게 ── */
  function 시작단추HTML(둘러보기) {
    if (!열림()) return '';
    return '<div class="acct-start"><button type="button" class="acct-main" onclick="' + esc(둘러보기 || '') + ';계정.열기()">' + 말('로그인 · 계정 만들기') + '</button>'
      + '<button type="button" class="acct-alt" onclick="' + esc(둘러보기 || '') + '">' + 말('로그인 없이 둘러보기') + '</button>'
      + '<p class="acct-tiny">' + 말('둘러보셔도 기록은 이 기기에 남아요. 로그인은 언제든 화면 맨 위 「로그인」에서 하실 수 있어요.') + '</p></div>';
  }

  /* ── 기기 두 대(11-10 현욱님 「이용권 하나 = 기기 두 대까지 · 가족과 나눠 써도 됨」) ──
     설치({ 기기두대: true })일 때만 돈다(서버 _서버/메디나눔_기기두대_1110.sql 을 붙인 뒤 · 유료화 켜기 전에). 셈은 앱마다 따로.
     로그인 직후·앱을 열 때 device_touch → 가득이면 기기 목록 시트(오래 안 쓴 것 먼저)에서 하나를 내보낸다 · 내보내진 기기는 다음 확인 때 로그아웃. */
  var 기기 = { 본: '', 가득: false };
  function 기기켜짐() { var v = 설정.기기두대; return (typeof v === 'function' ? 부름(v, false) : v) === true && 열림(); }
  function 기기아이디() {
    try { var v = localStorage.getItem('_dev_' + 설정.app); if (v && v.length >= 16) return v;
      var a = new Uint8Array(16); (window.crypto || {}).getRandomValues ? crypto.getRandomValues(a) : a.forEach(function (_, i) { a[i] = Math.random() * 256; });
      v = 'd' + [].map.call(a, function (b) { return ('0' + b.toString(16)).slice(-2); }).join(''); localStorage.setItem('_dev_' + 설정.app, v); return v; } catch (e) { return ''; }
  }
  function 기기갈래() { var u = navigator.userAgent || ''; return /iPhone/.test(u) ? 'iPhone' : /iPad/.test(u) ? 'iPad' : /Android/.test(u) ? (/Mobile/.test(u) ? 'Android 폰' : 'Android 태블릿') : /Windows/.test(u) ? 'Windows PC' : /Mac OS X/.test(u) ? 'Mac' : '기기'; }
  function 기기날(t) { try { var d = new Date(t); return d.getFullYear() + '.' + (d.getMonth() + 1) + '.' + d.getDate(); } catch (e) { return ''; } }
  function 기기확인(굳이) {
    if (!기기켜짐()) return; var m = 메일(); if (!m || (!굳이 && 기기.본 === m)) return; 기기.본 = m;
    var id = 기기아이디(); if (!id) return;
    서버().준비().then(function (sb) { return sb.rpc('device_touch', { p_app: 설정.app, p_device: id, p_label: 기기갈래() }); }).then(function (r) {
      var d = r && r.data; if (!d || d.ok) { 기기.가득 = false; return; }
      if (d.why === 'revoked') { 알림(말('다른 기기에서 이 기기를 내보냈어요. 다시 로그인하시면 이어서 쓸 수 있어요.')); 기기.본 = ''; 나가기(); return; }
      if (d.why === 'full') { 기기.가득 = true; 기기시트(d.devices || []); }
    }).catch(function () {});
  }
  function 기기시트(목록) {
    var 나 = 기기아이디(), 가득 = 기기.가득;
    var h = '<div class="acctsheet"><p class="acct-lead">' + esc(말(가득 ? '이 계정은 이미 두 대에서 쓰고 있어요. 이 기기에서 쓰시려면 아래에서 내보낼 기기를 직접 골라 주세요. 내보낸 기기는 로그아웃되고, 기록은 계정에 그대로 있어요.' : '이 계정으로 로그인한 기기예요. 계정 하나로 기기 두 대까지 쓸 수 있어요. 가족의 기록은 각자 계정으로 — 같은 계정이면 기록이 서로 보여요.')) + '</p>'
      + 목록.map(function (x, i) { var 이 = x.device === 나;
          return '<div class="acctcard"><div class="acct-row"><b>' + esc(x.label ? 말(x.label) : 말('기기')) + (이 ? ' · ' + esc(말('이 기기')) : '') + '</b>'
            + '</div>'   /* 11-11 법무 — 자동으로 고르지 않는다(가장 오래 안 쓴 기기 표시 뺌) · 사용자가 직접 고름 */
            + '<div class="acct-row"><i>' + esc(말('마지막 사용')) + '</i><b>' + esc(기기날(x.last_at)) + '</b></div>'
            + '<button type="button" class="acct-alt" onclick="계정.기기내보내기(\'' + esc(x.device) + '\')">' + esc(말('내보내기')) + '</button></div>'; }).join('')
      + (가득 ? '<button type="button" class="acct-link" onclick="계정.나가기();계정.기기닫기()">' + esc(말('이 기기에서는 로그아웃')) + '</button>' : '') + '</div>';
    시트(h, 말('내 기기'));
  }
  function 기기열기() {
    if (!기기켜짐() || !메일()) return;
    기기.가득 = false;
    서버().준비().then(function (sb) { return sb.rpc('device_list', { p_app: 설정.app }); }).then(function (r) {
      if (!r || r.error || !Array.isArray(r.data)) throw 0; 기기시트(r.data); }).catch(function () { 알림(말('기기 목록을 불러오지 못했어요. 잠시 뒤 다시 해 주세요.')); });
  }
  function 기기내보내기(id) {
    var 나 = 기기아이디();
    서버().준비().then(function (sb) { return sb.rpc('device_release', { p_app: 설정.app, p_device: id }); }).then(function (r) {
      if (!r || r.error) throw 0;
      if (id === 나) { 닫기(); 기기.본 = ''; 나가기(); return; }
      if (기기.가득) { 기기.가득 = false; 닫기(); 알림(말('내보냈어요. 이 기기에서 이어서 쓰실 수 있어요.')); 기기확인(true); return; }
      알림(말('내보냈어요.')); 기기열기();
    }).catch(function () { 알림(말('기기 목록을 불러오지 못했어요. 잠시 뒤 다시 해 주세요.')); });
  }

  window.계정 = { __v: 1,
    설치: function (o) {
      for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) 설정[k] = o[k];
      if (부름(설정.앱동의됨, false) === true) 가입표시();   /* 10-30 — 가입 부품의 첫 확인(설치 600ms 뒤)보다 먼저 */
      document.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' || e.isComposing || !e.target || !e.target.closest || !e.target.closest('.acctsheet')) return;
        if (e.target.id === 'srvEmail') { e.preventDefault(); e.stopPropagation(); var p = document.getElementById('srvPw'); if (p) p.focus(); }
        else if (e.target.id === 'srvPw') { e.preventDefault(); e.stopPropagation(); 계속(); }
      }, true);
      setInterval(function () { 머리단추새로(false); }, 2000);
      document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') 머리단추새로(false); });
      var css = document.createElement('style');
      css.textContent = ''
        + '.acctbtn{flex:0 0 auto;min-width:44px;height:44px;padding:0 12px;border:1px solid var(--line,rgba(0,0,0,.15));border-radius:999px;background:var(--card,#fff);color:var(--accent,#2f5d50);font-weight:700;font-size:15px;line-height:1;font-family:inherit;cursor:pointer;white-space:nowrap}'
        + '.acctbtn .acct-ic{display:none}.acctbtn{display:inline-flex;align-items:center;justify-content:center}.acctbtn.in{width:44px;padding:0;border:0;background:var(--accent,#2f5d50);color:var(--on-accent,#fff);font-size:17px}'
        + '.acctcard,.acctsheet{display:flex;flex-direction:column;gap:10px}'
        + '.acctcard{padding:16px;margin-bottom:12px;border:1px solid var(--line,rgba(0,0,0,.12));border-radius:16px;background:var(--card,#fff)}'
        + '.acctsheet .acctcard{margin-bottom:0}'
        + '.acct-me{display:flex;align-items:center;gap:12px}.acct-me>div{display:flex;flex-direction:column;gap:2px;min-width:0}.acct-me b{font-size:16px;word-break:break-all}.acct-me span{font-size:15px;opacity:.75;line-height:1.5;word-break:keep-all}'
        + '.acct-av{flex:0 0 44px;width:44px;height:44px;border-radius:50%;display:grid;place-items:center;background:var(--accent,#2f5d50);color:var(--on-accent,#fff);font-weight:700;font-size:18px}.acct-av.off{background:var(--sage-t,var(--line,#eee));color:var(--accent,#333)}'
        + '.acct-row{display:flex;justify-content:space-between;gap:12px;font-size:15px;padding:2px 0}.acct-row i{font-style:normal;opacity:.7}.acct-row b{font-weight:600;text-align:right}'
        + '.acct-btns{display:flex;gap:8px}.acct-say{margin:10px 0 0;padding:12px 14px;border-radius:12px;background:var(--accent-soft,rgba(47,111,104,.10));color:inherit;font-size:15px;line-height:1.55;word-break:keep-all;overflow-wrap:anywhere}.acct-btns button{flex:1;min-height:44px;display:inline-flex;align-items:center;justify-content:center;text-align:center;padding:0 12px;border:1px solid var(--line,rgba(0,0,0,.18));border-radius:999px;background:transparent;color:inherit;font-weight:600;font-size:15px;line-height:1;font-family:inherit;cursor:pointer}'
        + '.acct-del{align-self:flex-start;background:none;border:0;min-height:40px;padding:6px 0;color:inherit;opacity:.6;font:inherit;font-size:15px;cursor:pointer;text-decoration:none}'
        + '.acct-main,.acct-alt{width:100%;min-height:52px;border-radius:14px;font-weight:700;font-size:17px;line-height:1.2;font-family:inherit;cursor:pointer}'
        + '.acct-or{display:flex;align-items:center;gap:10px;margin:6px 0 2px;font-size:14px;opacity:.7}.acct-or:before,.acct-or:after{content:"";flex:1;border-top:1px solid currentColor;opacity:.35}'
        + '.acct-soc{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;min-height:48px;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;font-family:inherit}'
        + '.acct-main{border:0;background:var(--accent,#2f5d50);color:var(--on-accent,#fff)}.acct-main:disabled{opacity:.6;cursor:wait}'
        + '.acct-alt{border:1px solid var(--line,rgba(0,0,0,.18));background:var(--card,#fff);color:inherit}'
        + '.acct-start{display:flex;flex-direction:column;gap:10px;margin-top:14px}'
        + '.acctsheet label{font-weight:600;font-size:15px;margin-top:2px}.acctsheet input[type=email],.acctsheet input[type=password]{width:100%;box-sizing:border-box;min-height:48px;padding:10px 12px;border:1px solid var(--line,rgba(0,0,0,.18));border-radius:12px;font:inherit;font-size:max(16px,1em);background:var(--card,#fff);color:inherit}'
        + '.acct-chk.bad{outline:2px solid #c0392b;outline-offset:4px;border-radius:8px}.acct-err{margin:4px 0 2px 32px;color:#c0392b;font-size:15px;font-weight:600;line-height:1.5}.acct-chk{display:flex;align-items:flex-start;gap:10px;font-weight:400 !important;line-height:1.55;cursor:pointer;margin-top:4px}.acct-chk input{flex:none;width:22px;height:22px;margin:1px 0 0;accent-color:var(--accent,#2f5d50)}'
        + '.acct-req{display:inline-block;margin-left:4px;padding:0 6px;border-radius:6px;font-size:15px;font-weight:700;background:var(--clay-t,#f6e3dc);color:var(--clay-ink,#8a3b22)}'
        + '.acct-lead{margin:0 0 4px;line-height:1.6;word-break:keep-all}.acct-dim{font-weight:400;opacity:.7}.acct-tiny{margin:0;font-size:15px;opacity:.75;line-height:1.6;word-break:keep-all}'
        + '.acct-chips{display:flex;flex-wrap:wrap;gap:8px}.acct-chip{min-height:44px;padding:0 16px;border:1px solid var(--line,rgba(0,0,0,.18));border-radius:999px;background:var(--card,#fff);color:inherit;font-weight:600;font-size:15px;line-height:1.2;font-family:inherit;cursor:pointer}.acct-chip.on{border-color:var(--accent,#2f5d50);box-shadow:0 0 0 2px var(--accent,#2f5d50) inset;color:var(--accent,#2f5d50)}'
        + '.acct-birth{display:flex;gap:8px}.acct-sel{flex:1;min-height:48px;padding:0 10px;border:1px solid var(--line,rgba(0,0,0,.18));border-radius:12px;background:var(--card,#fff);color:inherit;font-size:16px;font-family:inherit}.acct-pic{width:28px;height:28px;border-radius:50%;vertical-align:middle;object-fit:cover}'
        + '.acctsheet input[type=text]{width:100%;box-sizing:border-box;min-height:48px;padding:10px 12px;border:1px solid var(--line,rgba(0,0,0,.18));border-radius:12px;font:inherit;font-size:max(16px,1em);background:var(--card,#fff);color:inherit}'
        + '.acct-link{align-self:flex-start;background:none;border:0;min-height:40px;padding:6px 0;color:var(--accent,inherit);font:inherit;font-size:15px;font-weight:700;cursor:pointer;text-decoration:none}';
      document.head.appendChild(css);
    },
    머리단추HTML: 머리단추HTML, 머리단추새로: function () { 머리단추새로(true); }, 카드HTML: 카드HTML, 시작단추HTML: 시작단추HTML,
    열기: 열기, 계속: 계속, 소셜: 소셜, 비번: 비번, 나가기: 나가기, 동기화: 동기화, 지우기: 지우기,
    처리방침: function () { try { if (typeof 설정.처리방침 === 'function') 설정.처리방침(); } catch (e) {} },
    로그인됨: function () { return !!메일(); }, 열림: 열림,
    프로필: function () { 프로필읽기().then(function () { 프로필열기(false); }); }, 프로필고름: 프로필고름, 프로필저장: 프로필저장, 프로필확인: 프로필확인   /* 프로필1030 */,
    기기켜짐: 기기켜짐, 기기확인: function () { 기기확인(true); }, 기기열기: 기기열기, 기기내보내기: 기기내보내기, 기기닫기: 닫기,   /* 기기두대1110 */
    이앱탈퇴: 이앱탈퇴, 전부지우기: function () { 닫기(); return 지우기전부(); }   /* 앱별가입1111 */
  };
})();
/* ▲▲ 계정 부품 끝 ▲▲ */
/* ▼▼ 회원권 부품 시작 ▼▼ */
/* ═══ 메디나눔 회원권 — 「가입하면 뭐가 좋은지」 한 장 시트 · 다섯 앱 공용 (2026-11-03 현욱님 「가장 중요한 것」 · 주인: 길동무 세션)
   요청서 docs/requests/20261103_메디나눔_회원권_혜택화면.md
   1등은 이렇게 한다 → 우리는 여기서 앞선다
     · 결제 화면 1등(Headspace·Calm·Apple One·Medisafe)은 혜택 3개 이하 · 가격 한 줄 · 체험 강조 · 해지 쉬움.
       혜택을 길게 늘어놓으면 체험 수락이 떨어진다(Strava 시험, lazyweb.com/research/strava-low-density-trial-paywall).
     · 체험이 「며칠째 무엇이 일어나는지」 보여 주는 곳은 결제 화면 1,204개 중 3.2%뿐(lazyweb.com/research/is-a-7-day-free-trial-the-default).
     · 우리: 한 번 가입으로 가족 건강 다섯 갈래(아이·암·마음·약·진료 계산)가 열리고, 응급·안전 기능은 늘 열림 — 첫 줄에서 느끼게.
       잠긴 기능을 누르면 그 기능이 강조된 채 「어디서 쓰는지」 경로까지 · 회원이면 같은 자리에서 바로 열기(회원이 기능을 못 찾는 일 막기).
   시트 한 장(위에서 아래로): 머리(한 줄 · 값 · 14일 체험) → 좋은 점 셋 → 이 앱에서 열리는 것(경로·작은 그림·회원이면 열기)
     → 다른 네 앱 → 늘 열려 있는 것 → 14일 흐름 → 단추(판매 전 「열리면 알려 주세요」 · 판매 뒤 「14일 써 보기」) · 해지·환불 작은 글
   들어오는 길: 설정 줄(회원권.줄() · 회원권.줄HTML()) · 홈 띠(회원권.띠HTML() — 닫으면 7일 · 처음 쓰신 날부터 이틀 뒤에) · 잠긴 기능(구독.막힘 을 감싼다)
   기댐: 구독 부품(window.구독 — 상태·회원권구매·관리열기·막힘) · 가입 부품(운영자). 없어도 시트는 열린다(값과 「곧 열려요」).
   ⛔ 판매 전에는 결제 단추 없음(되는 척 금지) · 돈 안 드는 뜻의 그 낱말 없음 · 이중 꺾쇠 없음 · 이모지 없음.

   쓰는 법(앱 끝, 구독.설치 · 가입.설치 뒤):
     회원권.설치({ app:'gildongmu',
       언어: function(){ return 'ko'|'en'|'es'|'ja'|'zh' },            // 없으면 <html lang>
       가격: { 월:12900, 연:99000, 출시월:9900, 출시연:79000 },          // 구독.설치 의 회원권 값과 같게
       판매: function(){ return false },                               // 스토어 상품 등록 뒤 true — 그때부터 「14일 써 보기」
       자료: { 앱:'gildongmu', 정체:{ko:'…',en:'…',es,ja,zh},
               기능:[{ id:'labs', 이름:{…}, 쓸모:{…}, 어디서:{…}, 그림:'trend', 가기:"closeSheet();openSheet('tool-labs')" }, …],   // 3~5개 · id = 구독 잠금 id
               늘열림:[{…}, {…}, {…}] },                                // 회원이 아니어도 늘 열린 안전 기능 2~4개
       시트열기: function(html, 제목){…}, 시트닫기: function(){…}, 알림: function(t){…},
       알림받기: function(){…},     // 선택 — 「열리면 알려 주세요」를 누른 뒤 앱 알림 설정을 열고 싶으면
       모양: { 주:'btn wide', 보조:'btn line wide' } });                 // 앱의 기존 단추 클래스(새 색 없음)
     설정 줄:  회원권.줄() → { 제목, 설명, 값 } 을 앱의 줄 모양으로 · 또는 회원권.줄HTML()
     홈 띠:    회원권.띠HTML() (조건이 안 맞으면 '')
     잠긴 기능: 구독.설치 문구에 막힘앞: function(id){ return window.회원권 ? 회원권.강조HTML(id) : ''; } 한 줄 — 막힘 시트 맨 위에
                그 기능(강조·어디서)과 「회원권 하나로 다섯 앱」 줄이 얹힌다. 이 앱 체험·로그인·동의 흐름은 구독 부품 그대로.
                (가로채기:true 면 막힘 시트 대신 회원권 시트를 연다 — 판매 시작 뒤 고를 일)
     그림 이름: sync · trend · paper · cal · family · book · leaf · star · copy · case · bell · chart

   다섯 앱 자료 틀(각 앱 세션이 자기 앱 설치에 채운다 — 이름·쓸모·어디서는 다섯 말 {ko,en,es,ja,zh})
     kids        기능: sync(동기화·여러 기기) · kids3(아이 셋째부터) · growth(성장곡선 백분위 추이, trend) · baby_trend(아기 하루 7일 넘는 이력·주간 그래프, chart) · ics(접종 달력, cal) · visit(진료 준비 한 장 PDF, paper)   (유료화 v2 · 11-03 소아)
                 늘열림: 지금 병원에 가야 하는지 · 해열제 양 계산 · 응급실 찾기
     gildongmu   기능: sync · labs(피검사 추이, trend) · visit(진료 준비 한 장·PDF, paper) · calendar(달력 내보내기, cal)
                 늘열림: 체온과 열날 때 할 일 · 위험 신호와 지금 연락 · 응급실 찾기·마음 위기 · 암 정보 글
     clinicscore 기능: sync · trend(검사 추이, chart) · cases(사례집, case) · fav(즐겨찾기 6개째부터, star) · handoff(인계용 복사, copy) · deep(깊은 해설, book)
                 늘열림: 모든 계산기 · 응급 알고리즘
     gyeote      기능: sync · tests(유형 검사 전부) · history(결과 보관·추이, trend) · report(마음 리포트, chart) · visit(진료 준비 한 장·PDF, paper) · garden(마음 정원 꾸미기, leaf)
                 늘열림: 힘들 땐(109 · 1577-0199 · 119) · 숨 고르기 · 나만의 안전 계획
     yakjido     (약지도 세션이 같은 꼴로 따로 — 가족 약통 · 가족 알림)
*/
(function () {
  if (window.회원권 && window.회원권.__v) return;
  var 판 = '2026-11-13a';   /* 11-11c 법무 — 가족 나눠 쓰기 문구 폐기(기기 두 대 · 각자 계정) · 두 구독 겹침 결제 안내 */   /* 11-11b 베이지 상자 안쪽 여백 고정(앱 ul 초기화에 지지 않게) · 제목 왼쪽 */
  /* 값은 여기 한 곳(원칙_결정 10-21·11-03) — 앱 하나: 월 5,900 · 연 49,000(출시 4,900 · 39,900) / 다섯 앱 회원권: 월 12,900 · 연 99,000(출시 9,900 · 79,000) · 체험 14일 */
  var 값표 = { 앱: { 월: 4900, 연: 39900 }, 회원권: { 월: 12900, 연: 99000, 출시월: 9900, 출시연: 79000 } };   /* 11-13 현욱님 — 앱 하나 늘 4,900·39,900(기념가 없음) · 회원권 그대로 */
  var 설정 = { app: 'app', 가로채기: false, 언어: null, 가격: 값표.회원권, 앱가격: 값표.앱, 판매: null, 자료: null,
               시트열기: null, 시트닫기: null, 알림: null, 알림받기: null, 모양: {} };
  var 말들 = ['ko', 'en', 'es', 'ja', 'zh'];

  /* 다섯 앱 — 다른 앱 카드(정체 한 줄 · 회원이면 열리는 대표 하나). 아이콘은 공개 누리집의 앱 아이콘(못 받으면 첫 글자 동그라미) */
  var 앱들 = {
    kids: { 주소: 'https://kids.medinanum.com/', 그림: 'https://medinanum.com/img/kids.png', 색: '#E58F65',
      이름: { ko: '우리 집 소아과', en: 'Our Home Pediatrics', es: 'Our Home Pediatrics', ja: 'Our Home Pediatrics', zh: 'Our Home Pediatrics' },
      정체: { ko: '아이가 아플 때 — 지금 병원에 가야 하는지부터', en: 'When your child is unwell — starting with whether to go now', es: 'Cuando su hijo se pone malo: primero, si hay que ir ya', ja: '子どもの具合が悪いとき — まず今すぐ受診すべきかから', zh: '孩子不舒服时——先判断要不要马上就医' },
      대표: { ko: '성장곡선 백분위 추이', en: 'Growth percentile trends', es: 'Evolución de los percentiles de crecimiento', ja: '成長曲線のパーセンタイル推移', zh: '生长曲线百分位变化' } },
    gildongmu: { 주소: 'https://gildongmu.medinanum.com/', 그림: 'https://medinanum.com/img/gildongmu.png', 색: '#356A63',
      이름: { ko: '길동무', en: 'Wayfellow', es: 'Wayfellow', ja: 'Wayfellow', zh: 'Wayfellow' },
      정체: { ko: '암과 함께 걷는 길 — 체온·증상·진료 준비', en: 'Walking alongside cancer — temperature, symptoms, visit prep', es: 'Acompañarle con el cáncer: temperatura, síntomas y consultas', ja: 'がんと歩む道 — 体温・症状・受診の準備', zh: '与癌同行——体温、症状、就诊准备' },
      대표: { ko: '피검사 추이', en: 'Blood test trends', es: 'Evolución de los análisis de sangre', ja: '血液検査の推移', zh: '血液检查变化趋势' } },
    clinicscore: { 주소: 'https://cs.medinanum.com/', 그림: 'https://medinanum.com/img/cs.png', 색: '#2F4C7A',
      이름: { ko: 'ClinicScore', en: 'ClinicScore', es: 'ClinicScore', ja: 'ClinicScore', zh: 'ClinicScore' },
      정체: { ko: '의료인용 임상 점수 — 계산 뒤 할 일까지', en: 'Clinical scores for clinicians — including what to do next', es: 'Escalas clínicas para profesionales, con el paso siguiente', ja: '医療者向けの臨床スコア — 計算の後にすることまで', zh: '面向医务人员的临床评分——连同下一步该做什么' },
      대표: { ko: '사례집 · 깊은 해설', en: 'Case library · in-depth notes', es: 'Casos clínicos · notas a fondo', ja: '症例集 · くわしい解説', zh: '病例集 · 深度解析' } },
    gyeote: { 주소: 'https://gyeote.medinanum.com/', 그림: 'https://medinanum.com/img/gyeote.png', 색: '#7A6AA8',
      이름: { ko: '곁에', en: 'Gyeote', es: 'Gyeote', ja: 'Gyeote', zh: 'Gyeote' },
      정체: { ko: '마음이 힘들 때 곁에서 — 살펴보기와 나만의 계획', en: 'Beside you when your mind is heavy — check-ins and your own plan', es: 'A su lado cuando la mente pesa: autoevaluación y su propio plan', ja: '心がつらいときにそばで — セルフチェックと自分の計画', zh: '心里难受时陪在身边——自我检查和自己的计划' },
      대표: { ko: '마음 리포트', en: 'Mood report', es: 'Informe del estado de ánimo', ja: 'こころのレポート', zh: '心情报告' } },
    yakjido: { 주소: 'https://yakjido.medinanum.com/', 그림: 'https://medinanum.com/img/yakjido.png', 색: '#3D7A5A',
      이름: { ko: '약지도', en: 'Yakjido', es: 'Yakjido', ja: 'Yakjido', zh: 'Yakjido' },
      정체: { ko: '집에서 할 일 · 약국 약 · 진료 신호를 차례로', en: 'Home care, pharmacy medicines and when to see a doctor — in order', es: 'Qué hacer en casa, qué pedir en la farmacia y cuándo ir al médico', ja: '家でできること・薬局の薬・受診のサインを順番に', zh: '居家处理、药店用药、就医信号——依次告诉你' },
      대표: { ko: '가족 약통 · 가족 알림', en: 'Family medicine box · family reminders', es: 'Botiquín familiar · avisos para la familia', ja: '家族の薬箱 · 家族への通知', zh: '家庭药箱 · 家人提醒' } }
  };
  var 앱차례 = ['kids', 'gildongmu', 'yakjido', 'gyeote', 'clinicscore'];

  var 글표 = {
    ko: { 강조줄: '이 기능을 포함해 다섯 앱의 회원 기능 · 값과 늘 열린 것 보기', 제목: '메디나눔 회원권', 머리: '회원권 하나로 <b>다섯 앱</b>이 모두 열려요', 갈래: '아이 · 암 · 마음 · 약 · 진료 계산 — 가족 건강 다섯 갈래를 한 번에',
      월: '월 {n}원', 연: '연 {n}원', 출시: '출시 기념가', 출시뒤: '출시 3개월 안에 가입하면 첫해 동안 · 그 뒤 {월} · {연}', 체험: '14일 써 보고 정하세요', 이앱하나: '이 앱 하나', 회원권다섯: '다섯 앱 회원권', 그뒤: '그 뒤 {월} · {연}', 출시때: '출시 기념가는 회원권이 열리는 날부터 3개월 안에 가입하면 첫해 동안이에요', 겹침: '이미 앱 이용권을 구독 중이면 회원권과 두 구독이 함께 결제될 수 있어요 — 회원권으로 바꾸실 때는 스토어의 구독 관리에서 앱 이용권을 해지해 주세요', 두대: '계정 하나로 기기 두 대까지 · 가족의 기록은 각자 계정으로(같은 계정이면 서로 보여요)', 자동: '14일 체험 뒤 자동 결제돼요 · 부가세 포함 · 설정에서 언제든 해지', 자동곧: '열리면 이렇게 결제돼요 — 체험 14일이 끝나는 날 고르신 요금이 자동 결제 · 부가세 포함 · 설정에서 언제든 해지',
      좋은점: '회원이 되면', 좋1: '폰을 바꿔도 기록이 그대로', 좋1말: '계정에 저장해 새 폰·다른 기기에서 이어서 써요', 좋2: '진료 갈 때 한 장으로', 좋2말: '그동안의 기록을 한 장·PDF로 정리해 보여 드려요', 좋3: '가족과 함께', 좋3말: '아이 여럿 · 가족 약 알림까지 한 계정으로',
      이앱: '{앱}에서 열리는 것', 지금: '지금 누르신 기능', 강조말: '이 기능은 회원권으로 열려요. 어디서 쓰는지 아래에 적어 두었어요.', 어디서: '어디서', 열기: '열기',
      다른: '다른 네 앱에서도', 앱열기: '열어 보기', 회원이면: '회원이면', 늘: '늘 열려 있는 것', 늘말: '응급·안전 기능은 회원이 아니어도 <b>늘 열려 있어요</b>.',
      흐름: '14일 체험은 이렇게', 흐1: '<b>오늘</b> — 다섯 앱이 모두 열려요', 흐2: '<b>12일째</b> — 끝나기 2일 전에 앱에서 미리 알려 드려요', 흐3: '<b>14일째</b> — 해지하지 않으면 고르신 요금으로 이어져요',
      곧: '곧 열려요', 곧말: '회원권은 스토어 등록을 마치는 대로 열려요. 지금은 값과 내용을 미리 보여 드려요.', 알림받기: '열리면 알려 주세요', 알림됨: '열리면 이 앱에서 알려 드릴게요',
      시작: '14일 써 보기', 연시작: '1년으로 시작 · {값}', 이앱만: '이 앱만 쓰기', 해지: '언제든 해지할 수 있어요', 환불: '환불 규정',
      회원: '회원 · 다섯 앱 열림', 까지: '{날}까지', 회원말: '이 앱에서 바로 쓸 수 있어요', 운영자: '운영자 · 모든 기능', 관리: '구독 관리',
      이앱구독: '이 앱은 구독으로 열려 있어요. 회원권으로 바꾸면 다른 네 앱도 함께 열려요.',
      줄설명: '다섯 앱이 한 번에 열려요 · 무엇이 열리는지', 띠: '회원권 하나로 다섯 앱이 모두 열려요', 띠열림: '메디나눔 회원권이 열렸어요', 띠보기: '무엇이 열리나', 닫기: '닫기', 날: '{m}월 {d}일' },
    en: { 강조줄: 'This feature and the member features of all five apps · price and what stays open', 제목: 'Medinanum Pass', 머리: 'One pass opens <b>all five apps</b>', 갈래: 'Children · cancer · mind · medicines · clinical scores — five sides of family health at once',
      월: '₩{n}/month', 연: '₩{n}/year', 출시: 'Launch price', 출시뒤: 'Join within 3 months of launch for your first year · then {월} · {연}', 체험: 'Try it for 14 days, then decide', 이앱하나: 'This app only', 회원권다섯: 'Five-app pass', 그뒤: 'then {월} · {연}', 출시때: 'Launch prices apply for your first year if you join within 3 months of the day the pass opens', 겹침: 'If you already subscribe to a single-app plan, both subscriptions may be charged — when switching to the pass, cancel the app plan in your store’s subscription settings', 두대: 'One account on up to two devices · family members each use their own account (records are visible on a shared account)', 자동: 'Billed automatically after the 14-day trial · VAT included · cancel any time in Settings', 자동곧: 'When it opens, billing works like this — the plan you choose is charged automatically on the day the 14-day trial ends · VAT included · cancel any time in Settings',
      좋은점: 'As a member', 좋1: 'Your records stay when you change phones', 좋1말: 'Saved to your account so you can carry on on a new phone or another device', 좋2: 'One page for your visit', 좋2말: 'Your records gathered on one page or a PDF to show your doctor', 좋3: 'Together with family', 좋3말: 'Several children and family medicine reminders under one account',
      이앱: 'What opens in {앱}', 지금: 'The feature you just tapped', 강조말: 'This feature opens with the pass. Where to find it is written below.', 어디서: 'Where', 열기: 'Open',
      다른: 'Also in the other four apps', 앱열기: 'Take a look', 회원이면: 'Members get', 늘: 'Always open', 늘말: 'Emergency and safety features are <b>always open</b>, member or not.',
      흐름: 'How the 14-day trial works', 흐1: '<b>Today</b> — all five apps open', 흐2: '<b>Day 12</b> — the app reminds you 2 days before the trial ends', 흐3: '<b>Day 14</b> — unless you cancel, it continues at the price you chose',
      곧: 'Coming soon', 곧말: 'The pass opens as soon as store registration is done. For now you can see the price and what it includes.', 알림받기: 'Tell me when it opens', 알림됨: "We'll let you know in this app when it opens",
      시작: 'Try 14 days', 연시작: 'Start yearly · {값}', 이앱만: 'Just this app', 해지: 'Cancel any time', 환불: 'Refund policy',
      회원: 'Member · all five apps open', 까지: 'until {날}', 회원말: 'You can use these in this app now', 운영자: 'Operator · all features', 관리: 'Manage subscription',
      이앱구독: 'This app is open with its own subscription. Switch to the pass and the other four apps open too.',
      줄설명: 'All five apps at once · see what opens', 띠: 'One pass opens all five apps', 띠열림: 'The Medinanum Pass is now open', 띠보기: 'See what opens', 닫기: 'Close', 날: '{mon} {d}' },
    es: { 강조줄: 'Esta función y las funciones para miembros de las cinco apps · precio y lo que sigue abierto', 제목: 'Pase Medinanum', 머리: 'Un solo pase abre <b>las cinco apps</b>', 갈래: 'Niños · cáncer · salud mental · medicamentos · escalas clínicas: cinco áreas de la salud familiar a la vez',
      월: '₩{n} al mes', 연: '₩{n} al año', 출시: 'Precio de lanzamiento', 출시뒤: 'Si se suscribe en los 3 primeros meses, durante el primer año · después {월} · {연}', 체험: 'Pruébelo 14 días y luego decida', 이앱하나: 'Solo esta app', 회원권다섯: 'Pase de cinco apps', 그뒤: 'después {월} · {연}', 출시때: 'El precio de lanzamiento se aplica el primer año si se suscribe en los 3 meses siguientes al día en que se abre el pase', 겹침: 'Si ya está suscrito al plan de una app, pueden cobrarse las dos suscripciones; al pasar al pase, cancele el plan de la app en la gestión de suscripciones de la tienda', 두대: 'Una cuenta en hasta dos dispositivos · cada familiar con su propia cuenta (en una cuenta compartida los registros se ven)', 자동: 'Se cobra automáticamente al terminar la prueba de 14 días · IVA incluido · cancele cuando quiera en Ajustes', 자동곧: 'Cuando se abra, el cobro será así: el plan elegido se cobra automáticamente el día en que termina la prueba de 14 días · IVA incluido · cancele cuando quiera en Ajustes',
      좋은점: 'Como miembro', 좋1: 'Sus registros se quedan aunque cambie de móvil', 좋1말: 'Se guardan en su cuenta para seguir en un móvil nuevo u otro dispositivo', 좋2: 'Una hoja para la consulta', 좋2말: 'Sus registros reunidos en una hoja o un PDF para enseñar al médico', 좋3: 'En familia', 좋3말: 'Varios hijos y avisos de medicación familiar en una sola cuenta',
      이앱: 'Lo que se abre en {앱}', 지금: 'La función que acaba de tocar', 강조말: 'Esta función se abre con el pase. Abajo le indicamos dónde encontrarla.', 어디서: 'Dónde', 열기: 'Abrir',
      다른: 'También en las otras cuatro apps', 앱열기: 'Ver', 회원이면: 'Con el pase', 늘: 'Siempre abierto', 늘말: 'Las funciones de urgencia y seguridad están <b>siempre abiertas</b>, sea o no miembro.',
      흐름: 'Así funciona la prueba de 14 días', 흐1: '<b>Hoy</b>: se abren las cinco apps', 흐2: '<b>Día 12</b>: la app le avisa 2 días antes de que termine', 흐3: '<b>Día 14</b>: si no cancela, continúa con el precio que eligió',
      곧: 'Muy pronto', 곧말: 'El pase se abrirá en cuanto terminemos el registro en la tienda. Por ahora puede ver el precio y lo que incluye.', 알림받기: 'Avísenme cuando se abra', 알림됨: 'Le avisaremos en esta app cuando se abra',
      시작: 'Probar 14 días', 연시작: 'Empezar con el plan anual · {값}', 이앱만: 'Solo esta app', 해지: 'Puede cancelar cuando quiera', 환불: 'Política de reembolso',
      회원: 'Miembro · cinco apps abiertas', 까지: 'hasta el {날}', 회원말: 'Puede usarlas ya en esta app', 운영자: 'Operador · todas las funciones', 관리: 'Gestionar la suscripción',
      이앱구독: 'Esta app está abierta con su propia suscripción. Con el pase se abren también las otras cuatro.',
      줄설명: 'Las cinco apps a la vez · qué se abre', 띠: 'Un solo pase abre las cinco apps', 띠열림: 'El Pase Medinanum ya está abierto', 띠보기: 'Qué se abre', 닫기: 'Cerrar', 날: '{d} de {mes}' },
    ja: { 강조줄: 'この機能を含む5つのアプリの会員機能 · 料金といつでも使えるもの', 제목: 'メディナヌム会員パス', 머리: 'パスひとつで<b>5つのアプリ</b>がすべて使えます', 갈래: '子ども・がん・こころ・薬・臨床スコア — 家族の健康の5つの分野をまとめて',
      월: '月額₩{n}', 연: '年額₩{n}', 출시: '発売記念価格', 출시뒤: '発売から3か月以内の登録で最初の1年間 · その後は{월} · {연}', 체험: '14日間使ってから決めてください', 이앱하나: 'このアプリだけ', 회원권다섯: '5つのアプリの会員パス', 그뒤: 'その後は{월} · {연}', 출시때: '発売記念価格は、会員パスが始まる日から3か月以内に登録すると最初の1年間適用されます', 겹침: 'すでにアプリの利用プランを購読中なら、会員パスと二つの購読が両方課金されることがあります — 会員パスに切り替えるときは、ストアの定期購入の管理でアプリのプランを解約してください', 두대: 'アカウント一つで端末二台まで · 家族の記録はそれぞれのアカウントで（同じアカウントだと見えます）', 자동: '14日間の体験後に自動で課金されます · 税込 · 設定からいつでも解約', 자동곧: '開始後はこのように課金されます — 14日間の体験が終わる日に選んだ料金を自動課金 · 税込 · 設定からいつでも解約',
      좋은점: '会員になると', 좋1: 'スマホを替えても記録はそのまま', 좋1말: 'アカウントに保存され、新しいスマホや別の端末で続けられます', 좋2: '受診のときは1枚にまとめて', 좋2말: 'これまでの記録を1枚・PDFにまとめて見せられます', 좋3: '家族と一緒に', 좋3말: '子ども複数人・家族の薬の通知までひとつのアカウントで',
      이앱: '{앱}で使えるようになるもの', 지금: 'いまタップした機能', 강조말: 'この機能は会員パスで使えます。どこで使うかを下に書いてあります。', 어디서: '場所', 열기: '開く',
      다른: 'ほかの4つのアプリでも', 앱열기: '見てみる', 회원이면: '会員なら', 늘: 'いつでも使えるもの', 늘말: '緊急・安全の機能は会員でなくても<b>いつでも使えます</b>。',
      흐름: '14日間の体験の流れ', 흐1: '<b>今日</b> — 5つのアプリがすべて使えます', 흐2: '<b>12日目</b> — 終わる2日前にアプリでお知らせします', 흐3: '<b>14日目</b> — 解約しなければ選んだ料金で続きます',
      곧: 'まもなく開始', 곧말: '会員パスはストアへの登録が済みしだい始まります。いまは料金と内容を先にご覧いただけます。', 알림받기: '始まったら知らせてください', 알림됨: '始まったらこのアプリでお知らせします',
      시작: '14日間使ってみる', 연시작: '年額で始める · {값}', 이앱만: 'このアプリだけ使う', 해지: 'いつでも解約できます', 환불: '返金の規定',
      회원: '会員 · 5つのアプリが使えます', 까지: '{날}まで', 회원말: 'このアプリですぐに使えます', 운영자: '運営者 · すべての機能', 관리: 'サブスクリプションの管理',
      이앱구독: 'このアプリは個別のサブスクリプションでご利用いただけます。会員パスに替えるとほかの4つのアプリも使えます。',
      줄설명: '5つのアプリがまとめて使えます · 中身を見る', 띠: 'パスひとつで5つのアプリがすべて使えます', 띠열림: 'メディナヌム会員パスが始まりました', 띠보기: '中身を見る', 닫기: '閉じる', 날: '{m}月{d}日' },
    zh: { 강조줄: '包括这个功能在内的五个应用会员功能 · 价格和一直开放的功能', 제목: 'Medinanum 会员卡', 머리: '一份会员订阅即可使用<b>全部五个应用</b>的会员功能', 갈래: '儿童 · 癌症 · 心理 · 用药 · 临床评分——家庭健康的五个方面一次全开',
      월: '每月₩{n}', 연: '每年₩{n}', 출시: '上线纪念价', 출시뒤: '上线 3 个月内加入，第一年适用 · 之后{월} · {연}', 체험: '先用 14 天再决定', 이앱하나: '仅此应用', 회원권다섯: '五个应用会员', 그뒤: '之后{월} · {연}', 출시때: '自会员开放之日起 3 个月内加入，第一年享受上线纪念价', 겹침: '如果已订阅单个应用的方案，会员和该订阅可能会同时扣费——改用会员时，请在应用商店的订阅管理中取消单个应用方案', 두대: '一个账号最多两台设备 · 家人各用自己的账号（同一账号记录会互相看到）', 자동: '14 天试用结束后自动扣费 · 含增值税 · 可随时在设置中取消', 자동곧: '开放后将这样扣费——14 天试用结束当天自动扣除所选方案的费用 · 含增值税 · 可随时在设置中取消',
      좋은점: '成为会员后', 좋1: '换手机记录也还在', 좋1말: '保存在账号里，换新手机或其他设备也能接着用', 좋2: '就诊时一页就够', 좋2말: '把这段时间的记录整理成一页或 PDF 给医生看', 좋3: '和家人一起', 좋3말: '多个孩子、家人的用药提醒都在一个账号里',
      이앱: '{앱}里会打开的功能', 지금: '您刚才点的功能', 강조말: '这个功能需要会员卡。在哪里使用写在下面。', 어디서: '位置', 열기: '打开',
      다른: '另外四个应用里也有', 앱열기: '去看看', 회원이면: '会员可用', 늘: '一直开放的功能', 늘말: '急救和安全功能不是会员也<b>一直开放</b>。',
      흐름: '14 天试用是这样的', 흐1: '<b>今天</b>——即可使用全部五个应用的会员功能', 흐2: '<b>第 12 天</b>——结束前 2 天在应用里提前提醒您', 흐3: '<b>第 14 天</b>——如果不取消，就按您选的价格继续',
      곧: '即将开放', 곧말: '会员卡在应用商店登记完成后就会开放。现在可以先看价格和内容。', 알림받기: '开放时通知我', 알림됨: '开放时会在这个应用里通知您',
      시작: '试用 14 天', 연시작: '按年开始 · {값}', 이앱만: '只用这个应用', 해지: '随时可以取消', 환불: '退款规定',
      회원: '会员 · 已开通五个应用的会员功能', 까지: '到{날}', 회원말: '在这个应用里马上就能用', 운영자: '运营者 · 全部功能', 관리: '管理订阅',
      이앱구독: '您已单独订阅此应用。改用会员订阅后，也可使用另外四个应用的会员功能。',
      줄설명: '五个应用一次全开 · 看看有什么', 띠: '一份会员订阅即可使用全部五个应用的会员功能', 띠열림: 'Medinanum 会员卡已开放', 띠보기: '看看有什么', 닫기: '关闭', 날: '{m}月{d}日' }
  };
  var 달en = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var 달es = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

  function 언어() {
    var l = null;
    try { if (typeof 설정.언어 === 'function') l = 설정.언어(); } catch (e) {}
    if (!l) l = (document.documentElement && document.documentElement.lang) || 'ko';
    l = String(l).toLowerCase().slice(0, 2);
    return 말들.indexOf(l) >= 0 ? l : 'ko';
  }
  function 채움(t, o) { return String(t).replace(/\{([^{}]+)\}/g, function (m, k) { return o && k in o ? o[k] : m; }); }
  function 글(k, o) { var t = 글표[언어()][k]; if (t == null) t = 글표.en[k]; if (t == null) t = 글표.ko[k]; return 채움(t, o); }
  function 골라(v) {   /* 앱이 준 글 — 글 · {ko,en,es,ja,zh} */
    if (v == null) return '';
    if (typeof v !== 'object') return String(v);
    var l = 언어(); return v[l] != null ? v[l] : (v.en != null && l !== 'ko' ? v.en : (v.ko != null ? v.ko : ''));
  }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function 수(n) { var l = 언어(); return Number(n || 0).toLocaleString(l === 'es' ? 'es-ES' : (l === 'ko' ? 'ko-KR' : 'en-US')); }
  function 월값(n) { return 글('월', { n: 수(n) }); }
  function 연값(n) { return 글('연', { n: 수(n) }); }
  function 날(t) {
    var d = new Date(t), l = 언어();
    return 글('날', { m: d.getMonth() + 1, d: d.getDate(), mon: 달en[d.getMonth()], mes: 달es[d.getMonth()] });
  }
  function 모(k, 기본) { var a = 설정.모양 && 설정.모양[k]; return a && a !== 기본 ? a + ' ' + 기본 : 기본; }   /* 11-10 — 앱 클래스가 그 자리에서만 꾸며지는 앱(곁에 .p)도 부품 단추 모양은 늘 */
  function 판매() { try { return typeof 설정.판매 === 'function' ? !!설정.판매() : !!설정.판매; } catch (e) { return false; } }
  function 키(k) { return '_pass_' + k + '_' + 설정.app; }
  function 읽(k) { try { return localStorage.getItem(키(k)); } catch (e) { return null; } }
  function 씀(k, v) { try { if (v == null) localStorage.removeItem(키(k)); else localStorage.setItem(키(k), String(v)); } catch (e) {} }
  function 알림(t) { try { if (typeof 설정.알림 === 'function') 설정.알림(t); } catch (e) {} }
  function 닫기() { try { if (typeof 설정.시트닫기 === 'function') 설정.시트닫기(); } catch (e) {} }

  function 구독() { return window.구독 && typeof window.구독.상태 === 'function' ? window.구독 : null; }
  function 운영자() { try { return !!(window.가입 && 가입.운영자 && 가입.운영자()); } catch (e) { return false; } }
  function 지금상태() {   /* 'op' 운영자 · 'pass' 회원권 · 'app' 이 앱만 구독 · null */
    if (운영자()) return { 종류: 'op' };
    var g = 구독(); if (!g) return null;
    try { var s = g.상태(); if (s && s.열림) return { 종류: s.회원권 ? 'pass' : 'app', until: s.until || null, status: s.status }; } catch (e) {}
    return null;
  }
  function 회원() { var s = 지금상태(); return !!(s && (s.종류 === 'pass' || s.종류 === 'op')); }

  /* ── 작은 그림 — 한 줄 획(앱 색을 따른다) ── */
  var 그림들 = {
    sync: '<rect x="6" y="6" width="14" height="24" rx="3"/><rect x="36" y="10" width="14" height="24" rx="3"/><path d="M22 14h10l-3-3M34 24H24l3 3"/>',
    trend: '<path d="M6 32h44M6 32V6"/><path d="M10 26l9-7 8 4 10-10 9 3"/><circle cx="19" cy="19" r="1.6"/><circle cx="27" cy="23" r="1.6"/><circle cx="37" cy="13" r="1.6"/>',
    chart: '<path d="M6 32h44"/><rect x="10" y="20" width="6" height="12" rx="1"/><rect x="22" y="12" width="6" height="20" rx="1"/><rect x="34" y="16" width="6" height="16" rx="1"/>',
    paper: '<path d="M14 4h20l8 8v22H14z"/><path d="M34 4v8h8M19 16h16M19 22h16M19 28h10"/>',
    cal: '<rect x="8" y="8" width="40" height="26" rx="3"/><path d="M8 15h40M16 5v6M40 5v6"/><path d="M15 21h4M26 21h4M37 21h4M15 28h4M26 28h4"/>',
    family: '<circle cx="18" cy="12" r="5"/><circle cx="38" cy="12" r="5"/><circle cx="28" cy="20" r="3.6"/><path d="M8 34c0-7 4-11 10-11s8 3 8 6M48 34c0-7-4-11-10-11s-8 3-8 6M22 34c0-4 2.5-6.5 6-6.5s6 2.5 6 6.5"/>',
    book: '<path d="M28 10c-5-3-12-4-20-3v24c8-1 15 0 20 3 5-3 12-4 20-3V7c-8-1-15 0-20 3z"/><path d="M28 10v24"/>',
    leaf: '<path d="M12 32C12 16 24 6 46 6c0 22-12 30-26 30"/><path d="M12 32c8-8 16-14 24-18"/>',
    star: '<path d="M28 5l6.5 13 14 2-10 9.8 2.4 14L28 37.3 15.1 43.8l2.4-14-10-9.8 14-2z" transform="scale(.82) translate(6 -1)"/>',
    copy: '<rect x="10" y="10" width="22" height="24" rx="3"/><path d="M18 10V6h22a3 3 0 0 1 3 3v19h-11"/>',
    case: '<path d="M6 12h16l4 4h24v18H6z"/><path d="M6 18h44"/>',
    bell: '<path d="M18 28V18a10 10 0 0 1 20 0v10l4 4H14z"/><path d="M24 35a4 4 0 0 0 8 0"/>'
  };
  function 그림(n, 클) { var p = 그림들[n] || 그림들.paper; return '<svg class="' + (클 || 'mb-pic') + '" viewBox="0 0 56 40" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + p + '</svg>'; }
  var 닫기그림 = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';

  function 앱아이콘(k) {
    var a = 앱들[k]; if (!a) return '';
    var 첫 = esc(String(골라(a.이름)).charAt(0));
    return '<span class="mb-ic" style="background:' + a.색 + '"><span aria-hidden="true">' + 첫 + '</span><img src="' + a.그림 + '" alt="" width="40" height="40" loading="lazy" onerror="this.remove()"></span>';
  }

  /* ── 시트 ── */
  function 줄값(g, 이름, 강조) {
    return '<div class="mb-plan' + (강조 ? ' on' : '') + '"><b class="mb-pn">' + 이름 + '</b>'
      + (g.출시월 ? '<span class="mb-chip">' + 글('출시') + '</span><p class="mb-price"><b>' + 월값(g.출시월) + '</b>' + (g.출시연 ? '<b>' + 연값(g.출시연) + '</b>' : '') + '</p>'
          + '<p class="mb-after">' + 글('그뒤', { 월: 월값(g.월), 연: 연값(g.연) }) + '</p>'
        : '<p class="mb-price"><b>' + 월값(g.월) + '</b>' + (g.연 ? '<b>' + 연값(g.연) + '</b>' : '') + '</p>') + '</div>';
  }
  function 값머리() {
    var g = 설정.가격 || 값표.회원권, a = 설정.앱가격 || 값표.앱, 앱 = 앱들[(설정.자료 && 설정.자료.앱) || 설정.app], h = '';
    /* 전자상거래법 8·13조(11-09): 결제 전이면 「곧 열려요」를 값보다 위에 · 값 바로 아래 자동 결제·부가세·해지 한 줄 · 기념가는 기간과 그 뒤 값을 한 줄로
       11-10 Main — 「이 앱 하나」와 「다섯 앱 회원권」을 이름 붙여 나란히(값은 값표 한 곳) */
    if (!판매()) h += '<p class="mb-soonchip"><span class="mb-chip">' + 글('곧') + '</span></p>';
    h += '<div class="mb-plans">' + 줄값(a, 글('이앱하나') + (앱 ? ' · ' + esc(골라(앱.이름)) : ''), false) + 줄값(g, 글('회원권다섯'), true) + '</div>';
    if (g.출시월 || a.출시월) h += '<p class="mb-small">' + 글('출시때') + '</p>';
    h += '<p class="mb-auto">' + 글(판매() ? '자동' : '자동곧') + '</p>';
    h += '<p class="mb-auto">' + 글('겹침') + '</p>';   /* 11-11 법무 — 앱 이용권과 회원권이 함께 결제될 수 있음 · 바꾸는 법 */
    var 덧 = 설정.자료 && 설정.자료.덧말;   /* 11-10 — 앱별 덧말 한 줄(예: CS 학생 요금) */
    if (덧) h += '<p class="mb-small mb-add">' + 골라(덧) + '</p>';
    return h;
  }
  function 좋은점() {
    var 줄 = [['sync', '좋1', '좋1말'], ['paper', '좋2', '좋2말'], ['family', '좋3', '좋3말']];
    return '<h3 class="mb-h">' + 글('좋은점') + '</h3><ul class="mb-three">' + 줄.map(function (r) {
      return '<li>' + 그림(r[0], 'mb-ico') + '<span><b>' + 글(r[1]) + '</b><span>' + 글(r[2]) + '</span></span></li>';
    }).join('') + '</ul>';
  }
  function 기능목록(강조, 열림) {
    var d = 설정.자료 || {}, 목 = (d.기능 || []).slice(), 앱 = 앱들[d.앱 || 설정.app];
    if (!목.length) return '';
    if (강조) 목.sort(function (a, b) { return (b.id === 강조) - (a.id === 강조); });
    var 이름 = 앱 ? 골라(앱.이름) : (골라(d.이름) || '');
    return '<h3 class="mb-h">' + 글('이앱', { 앱: esc(이름) }) + '</h3>' + (열림 ? '<p class="mb-small">' + 글('회원말') + '</p>' : '')
      + '<ul class="mb-feats">' + 목.map(function (f) {
        var on = 강조 && f.id === 강조;
        var 가기 = 열림 && f.가기 ? '<button type="button" class="mb-open" onclick="회원권.가기(\'' + esc(f.id) + '\')">' + 글('열기') + ' <span aria-hidden="true">›</span></button>' : '';
        return '<li class="mb-feat' + (on ? ' on' : '') + '" data-id="' + esc(f.id) + '">' + 그림(f.그림) +
          '<span class="mb-ft">' + (on ? '<span class="mb-chip">' + 글('지금') + '</span>' : '') + '<b>' + 골라(f.이름) + '</b>' +
          (f.쓸모 ? '<span>' + 골라(f.쓸모) + '</span>' : '') +
          (f.어디서 ? '<span class="mb-path"><span class="mb-pk">' + 글('어디서') + '</span> ' + 골라(f.어디서) + '</span>' : '') + '</span>' + 가기 + '</li>';
      }).join('') + '</ul>';
  }
  function 다른앱(열림) {
    var 지금 = (설정.자료 && 설정.자료.앱) || 설정.app;
    return '<h3 class="mb-h">' + 글('다른') + '</h3><ul class="mb-apps">' + 앱차례.filter(function (k) { return k !== 지금; }).map(function (k) {
      var a = 앱들[k];
      return '<li><a class="mb-app" href="' + a.주소 + '" target="_blank" rel="noopener">' + 앱아이콘(k) +
        '<span class="mb-at"><b>' + esc(골라(a.이름)) + '</b><span>' + 골라(a.정체) + '</span>' +
        '<span class="mb-rep">' + 글('회원이면') + ' · ' + 골라(a.대표) + '</span></span><span class="mb-go">' + 글('앱열기') + ' <span aria-hidden="true">›</span></span></a></li>';
    }).join('') + '</ul>';
  }
  function 늘열림() {
    var 목 = (설정.자료 && 설정.자료.늘열림) || [];
    return '<div class="mb-always"><h3 class="mb-h">' + 글('늘') + '</h3><p>' + 글('늘말') + '</p>' +
      (목.length ? '<ul>' + 목.map(function (x) { return '<li>' + 골라(x) + '</li>'; }).join('') + '</ul>' : '') + '</div>';
  }
  function 흐름() {
    return '<h3 class="mb-h">' + 글('흐름') + '</h3><ol class="mb-flow"><li>' + 글('흐1') + '</li><li>' + 글('흐2') + '</li><li>' + 글('흐3') + '</li></ol>';
  }
  function 단추들(강조) {
    var g = 구독(), h = '', 앱만 = '';
    if (g && typeof g.켜짐 === 'function' && g.켜짐()) 앱만 = '<button type="button" class="' + 모('보조', 'mb-btn2') + '" onclick="회원권.이앱만(\'' + esc(강조 || '') + '\')">' + 글('이앱만') + '</button>';
    if (판매()) {
      var 연 = (설정.가격 || {}).연;
      h = '<button type="button" class="' + 모('주', 'mb-btn') + '" onclick="회원권.시작()">' + 글('시작') + '</button>' +
        (연 ? '<button type="button" class="' + 모('보조', 'mb-btn2') + '" onclick="회원권.시작(\'year\')">' + 글('연시작', { 값: 연값((설정.가격 || {}).출시연 || 연) }) + '</button>' : '') + 앱만 +
        '<p class="mb-small mb-c">' + 글('해지') + ' · <a href="https://medinanum.com/refund.html" target="_blank" rel="noopener">' + 글('환불') + '</a></p>';
    } else {
      var 됨 = !!읽('notify');
      h = '<p class="mb-soon">' + 글('곧말') + '</p>' +
        '<button type="button" id="mbNotify" class="' + 모(됨 ? '보조' : '주', 됨 ? 'mb-btn2' : 'mb-btn') + '" onclick="회원권.알림받기()"' + (됨 ? ' disabled aria-disabled="true"' : '') + '>' + 글(됨 ? '알림됨' : '알림받기') + '</button>' + 앱만 +
        '<p class="mb-small mb-c">' + 글('해지') + ' · <a href="https://medinanum.com/refund.html" target="_blank" rel="noopener">' + 글('환불') + '</a></p>';
    }
    return '<div class="mb-cta">' + h + '</div>';
  }
  function 시트HTML(강조) {
    var s = 지금상태(), 열림 = !!(s && (s.종류 === 'pass' || s.종류 === 'op'));
    var h = '<div class="mb" id="mbSheet"><div class="mb-xbar"><button type="button" class="mb-x" aria-label="' + 글('닫기') + '" onclick="회원권.닫기()">' + 닫기그림 + '</button></div>';
    if (열림) {
      h += '<div class="mb-head mb-member"><p class="mb-lead"><b>' + 글(s.종류 === 'op' ? '운영자' : '회원') + '</b>' + (s.until && s.종류 !== 'op' ? ' · ' + 글('까지', { 날: 날(s.until) }) : '') + '</p>' +
        '<p class="mb-small">' + 글('갈래') + '</p></div>' + 기능목록(강조, true) + 다른앱(true) + 늘열림() +
        (s.종류 === 'pass' && 구독() && 구독().관리열기 ? '<div class="mb-cta"><button type="button" class="' + 모('보조', 'mb-btn2') + '" onclick="구독.관리열기()">' + 글('관리') + '</button></div>' : '');
    } else {
      var 이유 = (설정.자료 && 설정.자료.이유) || [];   /* 11-10 — 이 앱에서 회원권이 좋은 까닭 세 줄을 먼저 */
      if (이유.length) h += '<ul class="mb-why">' + 이유.slice(0, 3).map(function (x) { return '<li>' + 골라(x) + '</li>'; }).join('') + '</ul>';
      h += '<div class="mb-head"><p class="mb-lead">' + 글('머리') + '</p><p class="mb-small">' + 글('갈래') + '</p>' + 값머리() + '<p class="mb-trial">' + 글('체험') + '</p><p class="mb-small">' + 글('두대') + '</p></div>' +
        (강조 ? '<p class="mb-note">' + 글('강조말') + '</p>' : '') +
        (s && s.종류 === 'app' ? '<p class="mb-note">' + 글('이앱구독') + '</p>' : '') +
        (강조 ? 기능목록(강조, false) + 좋은점() : 좋은점() + 기능목록(null, false)) + 다른앱(false) + 늘열림() + 흐름() + 단추들(강조);
    }
    return h + '</div>';
  }
  var 키걸림 = false;
  function 열기(강조) {
    스타일();
    if (!키걸림) { 키걸림 = true; try { document.addEventListener('keydown', function (e) { if ((e.key === 'Escape' || e.key === 'Esc') ) { var m = document.getElementById('mbSheet'); if (m && m.getClientRects().length) 닫기(); } }); } catch (e) {} }
    try { if (typeof 설정.시트열기 === 'function') 설정.시트열기(시트HTML(강조 || null), 글('제목')); } catch (e) {}
    if (강조) setTimeout(function () { try { var el = document.querySelector('#mbSheet .mb-feat.on'); if (el && el.scrollIntoView) el.scrollIntoView({ block: 'center' }); } catch (e) {} }, 80);
    setTimeout(function () { try {   /* 11-10 — 앱 시트에 늘 보이는 닫기가 이미 있으면 부품 ✕ 는 숨긴다(✕ 하나) */
      var m = document.getElementById('mbSheet'), x = m && m.querySelector('.mb-xbar'); if (!x) return;
      var 위 = m.parentElement, 있음 = false;
      var sc = m.parentElement; while (sc && sc !== document.body && !(sc.scrollHeight > sc.clientHeight + 2 && /auto|scroll/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
      function 늘보임(b) { if (sc && sc !== document.body && !sc.contains(b)) return true; for (var e = b; e && e !== sc; e = e.parentElement) { if (/sticky|fixed/.test(getComputedStyle(e).position)) return true; } return false; }   /* 내려도 보이는 닫기만 센다 */
      while (위 && 위 !== document.body && !있음) { 있음 = [].some.call(위.querySelectorAll('button[aria-label]'), function (b) { return !m.contains(b) && /^(닫기|Close|Cerrar|閉じる|关闭)$/.test(b.getAttribute('aria-label')) && b.getClientRects().length && getComputedStyle(b).visibility !== 'hidden' && 늘보임(b); }); 위 = 위.parentElement; }
      if (있음) { x.hidden = true; x.style.display = 'none'; } } catch (e) {} }, 60);
    return false;
  }

  /* ── 잠긴 기능 칸 — 구독 막힘 시트 맨 위(구독.설치 문구.막힘앞)에 얹는다. 이 앱 체험·로그인·동의 흐름은 구독 부품 그대로 ── */
  function 강조HTML(id) {
    스타일();
    var f = ((설정.자료 || {}).기능 || []).filter(function (x) { return x.id === id; })[0];
    var 칸 = f ? '<ul class="mb-feats"><li class="mb-feat on" data-id="' + esc(f.id) + '">' + 그림(f.그림) + '<span class="mb-ft"><b>' + 골라(f.이름) + '</b>' +
      (f.쓸모 ? '<span>' + 골라(f.쓸모) + '</span>' : '') + (f.어디서 ? '<span class="mb-path"><span class="mb-pk">' + 글('어디서') + '</span> ' + 골라(f.어디서) + '</span>' : '') + '</span></li></ul>' : '';
    return '<div class="mb mb-lock">' + 칸 + '<button type="button" class="mb-row mb-passlink" onclick="회원권.열기(\'' + esc(id || '') + '\')">' + 그림('family', 'mb-ico') +
      '<span class="mb-rt"><b>' + 글('띠') + '</b><span>' + 글('강조줄') + '</span></span><span aria-hidden="true" class="mb-rc">›</span></button></div>';
  }

  /* ── 설정 줄 · 홈 띠 ── */
  function 줄() {
    var s = 지금상태();
    if (s && s.종류 === 'op') return { 제목: 글('제목'), 설명: 글('운영자'), 값: '' };
    if (s && s.종류 === 'pass') return { 제목: 글('제목'), 설명: 글('회원'), 값: s.until ? 글('까지', { 날: 날(s.until) }) : '' };
    return { 제목: 글('제목'), 설명: 글('줄설명'), 값: 판매() ? '' : 글('곧') };
  }
  function 줄HTML() {
    스타일();   /* 11-03 CS — 줄만 먼저 그리면 그림이 화면 폭만큼 커졌다 */
    var r = 줄();
    return '<button type="button" class="mb-row" onclick="회원권.열기()">' + 그림('family', 'mb-ico') + '<span class="mb-rt"><b>' + r.제목 + '</b><span>' + r.설명 + '</span></span>' + (r.값 ? '<span class="mb-rv">' + r.값 + '</span>' : '') + '<span aria-hidden="true" class="mb-rc">›</span></button>';
  }
  function 띠HTML() {
    스타일();
    if (회원()) return '';
    var now = Date.now(), 첫 = Number(읽('first') || 0);
    if (!첫) { 씀('first', now); 첫 = now; }
    if (판매() && 읽('notify') && !읽('told')) {   /* 「열리면 알려 주세요」를 누른 분께 — 열린 뒤 한 번 */
      return '<div class="mb-band" id="mbBand"><button type="button" class="mb-band-go" onclick="회원권.띠열기(\'told\')">' + 그림('bell', 'mb-bico') + '<span>' + 글('띠열림') + '</span><span aria-hidden="true">›</span></button>' +
        '<button type="button" class="mb-band-x" aria-label="' + 글('닫기') + '" onclick="회원권.띠닫기(\'told\')">' + 닫기그림 + '</button></div>';
    }
    if (now - 첫 < 2 * 864e5) return '';                       /* 처음 이틀은 조용히 — 앱부터 써 보시게 */
    var 닫음 = Number(읽('band') || 0); if (닫음 && now - 닫음 < 7 * 864e5) return '';
    return '<div class="mb-band" id="mbBand"><button type="button" class="mb-band-go" onclick="회원권.띠열기()">' + 그림('family', 'mb-bico') + '<span>' + 글('띠') + ' · <b>' + 글('띠보기') + '</b></span><span aria-hidden="true">›</span></button>' +
      '<button type="button" class="mb-band-x" aria-label="' + 글('닫기') + '" onclick="회원권.띠닫기()">' + 닫기그림 + '</button></div>';
  }
  function 띠닫기(k) { 씀(k === 'told' ? 'told' : 'band', Date.now()); try { var b = document.getElementById('mbBand'); if (b) b.remove(); } catch (e) {} }

  /* ── 잠긴 기능 → 이 시트(강조) ── */
  function 감싸기() {
    var g = window.구독; if (!g || typeof g.막힘 !== 'function' || g.막힘.__회원권) return;
    var 원 = g.막힘;
    var 새 = function (id) { try { if (g.열림(id)) return true; } catch (e) {} 열기(id); return false; };
    새.__회원권 = true; 새.원 = 원; g.막힘 = 새;
  }
  function 이앱만(id) {
    var g = window.구독; if (!g) return;
    var 원 = g.막힘 && g.막힘.원;
    if (id && 원) return 원(id);
    if (typeof g.관리열기 === 'function') g.관리열기();
  }

  var 스타일됨 = false;
  function 스타일() {
    if (스타일됨 || !document.head) return; 스타일됨 = true;
    var A = 'var(--mb-accent,var(--accent,var(--teal,#23685A)))', L = 'var(--mb-line,var(--line,rgba(127,127,127,.28)))', S = 'var(--mb-soft,var(--accent-soft,rgba(47,93,80,.08)))', D = 'var(--mb-dim,var(--ink2,inherit))', C = 'var(--mb-card,var(--card,transparent))';
    var st = document.createElement('style'); st.id = 'mb-style';
    st.textContent =
      '.mb{word-break:keep-all;overflow-wrap:anywhere;line-height:1.55}.mb p{margin:0 0 8px}.mb ul,.mb ol{list-style:none;margin:0;padding:0}' +
      '.mb-head{padding:4px 0 6px}.mb-lead{font-size:1.18em;font-weight:800;line-height:1.4;margin:0 0 6px!important}.mb-lead b{color:' + A + '}' +
      '.mb-small{font-size:.86em;color:' + D + '}.mb-c{text-align:center;margin-top:10px!important}.mb-small a{color:' + A + ';font-weight:700;text-decoration:none}' +
      '.mb-plans{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0 6px}.mb-plan{padding:12px;border:1.5px solid ' + L + ';border-radius:14px}.mb-plan.on{border-color:' + A + '}.mb-pn{display:block;font-size:.92em;margin-bottom:4px}.mb-plan .mb-price{margin:6px 0 2px!important;font-size:1.02em}.mb-plan .mb-price b{display:block;white-space:nowrap}.mb-plan .mb-after{font-size:.9em;margin:0!important}@media (max-width:359px){.mb-plans{grid-template-columns:1fr}}' +
      '.mb-why{list-style:none;margin:0 0 12px;padding:12px 14px;border-radius:14px;background:' + S + ';display:flex;flex-direction:column;gap:6px}.mb-why li{font-weight:700;line-height:1.5}.mb-after{font-size:1.02em;margin:2px 0 6px!important}.mb-auto{font-weight:800;font-size:1.02em;line-height:1.5;margin:8px 0 6px!important}.mb-plans{width:100%}.mb-soonchip{margin:8px 0 0!important}.mb-auto{margin-top:2px!important}.mb-price{font-size:1.02em;margin:10px 0 2px!important}.mb-trial{font-weight:700;color:' + A + ';margin-top:8px!important}' +
      '.mb-chip{display:inline-block;font-size:.82em;font-weight:800;padding:2px 8px;border-radius:999px;background:' + S + ';color:' + A + ';vertical-align:1px;margin-right:4px}' +
      '.mb-h{font-size:.98em;font-weight:800;margin:20px 0 8px;text-align:left !important}.mb-why,.mb-always{padding:12px 14px !important}.mb-note{padding:10px 12px !important}.mb-why li{margin:0;padding:0}' +
      '.mb-three li{display:flex;gap:12px;align-items:flex-start;padding:8px 0}.mb-three li>span{display:flex;flex-direction:column;min-width:0}.mb-three li>span>span{font-size:.88em;color:' + D + '}' +
      '.mb-ico{flex:none;width:34px;height:26px;color:' + A + ';margin-top:2px}' +
      '.mb-feats li{display:flex;flex-wrap:wrap;gap:10px 12px;align-items:flex-start;padding:12px;border:1px solid ' + L + ';border-radius:14px;margin:0 0 8px;background:' + C + '}' +
      '.mb-feat.on{border:2px solid ' + A + ';background:' + S + '}.mb-feat.on .mb-chip{background:' + A + ';color:var(--mb-on-accent,var(--on-accent,Canvas))}' +
      '.mb-lead b{font-weight:800}.mb-three b,.mb-ft>b,.mb-at>b,.mb-rt>b{font-weight:700}' +
      '.mb-pic{flex:none;width:52px;height:38px;color:' + A + ';background:' + S + ';border-radius:10px;padding:4px}' +
      '.mb-ft{flex:1 1 180px;min-width:0;display:flex;flex-direction:column;gap:2px}.mb-ft>span{font-size:.88em;color:' + D + '}.mb-ft .mb-chip{align-self:flex-start;margin-bottom:2px}' +
      '.mb-path{margin-top:2px}.mb-pk{font-weight:800;color:' + A + '}' +
      '.mb-open{flex:none;margin-left:auto;min-height:44px;padding:0 16px;border-radius:12px;border:1px solid ' + A + ';background:transparent;color:' + A + ';font:inherit;font-weight:800;cursor:pointer}' +
      '.mb-apps li{margin:0 0 8px}.mb-app{display:flex;gap:12px;align-items:center;padding:12px;border:1px solid ' + L + ';border-radius:14px;color:inherit;text-decoration:none;background:' + C + '}' +
      '.mb-ic{position:relative;flex:none;width:40px;height:40px;border-radius:11px;overflow:hidden;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800}' +
      '.mb-ic img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}' +
      '.mb-at{flex:1;min-width:0;display:flex;flex-direction:column;gap:1px}.mb-at>span{font-size:.86em;color:' + D + '}.mb-at .mb-rep{color:' + A + ';font-weight:700}' +
      '.mb-go{flex:none;font-size:.86em;font-weight:800;color:' + A + ';white-space:nowrap}' +
      '.mb-always{margin-top:16px;padding:12px 14px;border-radius:14px;background:' + S + '}.mb-always .mb-h{margin-top:0}.mb-always li{position:relative;padding:3px 0 3px 16px;font-size:.92em}' +
      '.mb-always li:before{content:"";position:absolute;left:2px;top:.75em;width:7px;height:7px;border-radius:50%;background:' + A + '}' +
      '.mb-flow{counter-reset:mb}.mb-flow li{position:relative;padding:6px 0 6px 34px;font-size:.92em}.mb-flow li:before{counter-increment:mb;content:counter(mb);position:absolute;left:0;top:5px;width:24px;height:24px;border-radius:50%;background:' + S + ';color:' + A + ';font-weight:800;font-size:.85em;display:flex;align-items:center;justify-content:center}' +
      '.mb-note{padding:10px 12px;border-radius:12px;background:' + S + ';font-size:.92em}' +
      '.mb-cta{margin-top:18px;display:flex;flex-direction:column;gap:8px}.mb-soon{font-size:.9em;color:' + D + '}' +
      '.mb-btn,.mb-btn2{min-height:52px;border-radius:14px;font:inherit;font-weight:800;cursor:pointer;width:100%}.mb-btn{border:0;background:' + A + ';color:var(--mb-on-accent,var(--on-accent,Canvas))}.mb-btn2{border:1px solid ' + A + ';background:transparent;color:' + A + '}' +
      '.mb-cta button[disabled]{opacity:.7;cursor:default}' +
      '.mb-lock{margin:0 0 12px}.mb-lock .mb-feats li{margin-bottom:8px}.mb-row{display:flex;gap:12px;align-items:center;width:100%;padding:14px 12px;border:1px solid ' + L + ';border-radius:14px;background:' + C + ';color:inherit;font:inherit;text-align:left;cursor:pointer}' +
      '.mb-rt{flex:1;min-width:0;display:flex;flex-direction:column}.mb-rt>span{font-size:.94em;color:' + D + '}.mb-rv{flex:none;font-size:.94em;font-weight:800;color:' + A + '}.mb-rc{flex:none;color:' + D + '}' +
      '.mb-band{display:flex;align-items:stretch;gap:4px;margin:12px 0;border-radius:14px;background:' + S + '}' +
      '.mb-band-go{flex:1;min-width:0;display:flex;gap:10px;align-items:center;min-height:48px;padding:8px 4px 8px 12px;border:0;background:transparent;color:inherit;font:inherit;font-size:.92em;text-align:left;cursor:pointer;word-break:keep-all}' +
      '.mb-band-go>span:nth-child(2){flex:1;min-width:0}.mb-band-go b{color:' + A + '}.mb-bico{flex:none;width:30px;height:22px;color:' + A + '}' +
      '.mb-xbar:not([hidden])+*>:first-child{padding-right:48px}' +   /* 11-10 — 위 ✕ 가 첫 상자 글을 가리지 않게 */
      '.mb-xbar{position:sticky;top:0;z-index:6;height:0;display:flex;justify-content:flex-end;pointer-events:none}' +
      '.mb-x{pointer-events:auto;width:44px;height:44px;margin:-4px -6px 0 0;border:1px solid ' + L + ';border-radius:50%;background:var(--mb-card,var(--card,var(--bg,#fff)));color:inherit;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,.12)}' +
      '.mb-band-x{flex:none;width:44px;border:0;background:transparent;color:' + D + ';cursor:pointer;display:flex;align-items:center;justify-content:center;border-radius:0 14px 14px 0}';
    document.head.appendChild(st);
  }

  function 설치(o) {
    o = o || {};
    Object.keys(o).forEach(function (k) { 설정[k] = o[k]; });
    if (설정.자료 && 설정.자료.앱 && !o.app) 설정.app = 설정.자료.앱;
    if (설정.가로채기) { 감싸기(); try { document.addEventListener('DOMContentLoaded', 감싸기); } catch (e) {} }
    return window.회원권;
  }

  window.회원권 = {
    __v: 판, 판: 판, 값표: 값표, 설치: 설치, 열기: 열기, 닫기: 닫기, 강조HTML: 강조HTML, 시트HTML: 시트HTML, 줄: 줄, 줄HTML: 줄HTML, 띠HTML: 띠HTML, 띠닫기: 띠닫기, 회원: 회원, 상태: 지금상태, 앱들: 앱들,
    띠열기: function (k) { if (k === 'told') 씀('told', Date.now()); 열기(); },
    가기: function (id) {
      var f = ((설정.자료 || {}).기능 || []).filter(function (x) { return x.id === id; })[0];
      if (!f || !f.가기) return;
      닫기();
      setTimeout(function () { try { if (typeof f.가기 === 'function') f.가기(); else (new Function(f.가기))(); } catch (e) {} }, 60);
    },
    알림받기: function () {
      씀('notify', Date.now());
      var b = document.getElementById('mbNotify');
      if (b) { b.textContent = 글('알림됨'); b.disabled = true; b.setAttribute('aria-disabled', 'true'); b.className = 모('보조', 'mb-btn2'); }
      알림(글('알림됨'));
      try { if (typeof 설정.알림받기 === 'function') 설정.알림받기(); } catch (e) {}
    },
    시작: function (plan) { var g = 구독(); if (g && typeof g.회원권구매 === 'function') return g.회원권구매(plan); 알림(글('곧')); },
    이앱만: 이앱만,
    글: 글
  };
})();
/* ▲▲ 회원권 부품 끝 ▲▲ */
/* 11-11 Main(현욱님) — 공용 계정 부품 · 회원권 부품. 약지도의 로그인 문·계정 카드는 그대로 두고, 「계정 지우기」만 계정.지우기() 를 거친다.
   지우기둘 은 끈 채 — 서버(delete_own_account(p_app) 두 갈래)를 붙인 뒤 켠다. 꺼져 있으면 지금처럼 계정동작('delete'). 회원권 판매도 끈 채(「곧 열려요」). */
try {
  계정.설치({ app: 'yakjido', 앱이름: '약지도', 웹주소: 'https://yakjido.medinanum.com/', 지우기둘: false,
    열림: function () { return D.meta && D.meta.account === true; },
    동의됨: function () { return srvAgreed(); },
    동의하기: function () { try { localStorage.setItem(AGREE_KEY, JSON.stringify({ server: true, at: new Date().toISOString() })); } catch (e) {} },
    동의이름: '건강정보(민감정보) 서버 저장', 나이글: '만 14세 이상이에요',
    동의글: '드시는 약·복용 기록·몸 상태 같은 기록을 암호화된 연결로 보내 메디나눔 서버(서울)에 저장하고, 로그인한 기기에서 이어 보는 데 동의해요.',
    앱동의됨: function () { try { return !!localStorage.getItem('yakjido.consent.v1'); } catch (e) { return false; } },
    처리방침: function () { location.href = 'privacy.html'; },
    시트열기: function (html, 제목) { var v = document.getElementById('view'); if (!v) return; v.innerHTML = topBar({ back: '뒤로' }) + '<h1>' + esc(제목 || '계정') + '</h1>' + html; scrollTo(0, 0); },
    시트닫기: function () { route(); },
    알림: function (t) { try { toast(t); } catch (e) {} },
    다시그리기: function () { try { route(); } catch (e) {} },
    이용권글: function () { try { var sv = window.구독 && 구독.상태 && 구독.상태(); return sv && sv.status === 'active' ? '구독 중' : ''; } catch (e) { return ''; } } });
} catch (e) {}
try {
  var 약말 = function (ko, en) { return { ko: ko, en: en }; };
  회원권.설치({ app: 'yakjido', 언어: function () { return window.LANG || 'ko'; },
    가격: { 월: 12900, 연: 99000, 출시월: 9900, 출시연: 79000 }, 판매: function () { return false; },
    자료: { 앱: 'yakjido', 정체: 약말('먹는 약을 쉽게 풀어 알려 주는 약 안내', 'Plain-language guide to the medicines you take'),
      기능: [
        { id: 'sync', 그림: 'sync', 가기: "go('/me?t=set')", 이름: 약말('여러 기기에서 이어 보기', 'Continue on several devices'), 쓸모: 약말('약통·복용 기록을 계정에 두고 새 폰에서도 그대로', 'Keep your medicine box and dose log in your account, the same on a new phone'), 어디서: 약말('내 정보 → 설정 → 맨 위 계정 칸', 'My info → Settings → account box at the top') },
        { id: 'trend', 그림: 'trend', 가기: "go('/vitals')", 이름: 약말('혈압·혈당 2주 흐름 그림', 'Two-week blood pressure and sugar chart'), 쓸모: 약말('적어 둔 혈압·혈당이 어떻게 움직였는지 한 장으로', 'See how your readings have moved on one chart'), 어디서: 약말('홈 → 혈압·혈당 수첩', 'Home → Blood pressure and sugar log') },
        { id: 'visitdoc', 그림: 'paper', 가기: "go('/bag')", 이름: 약말('진료실 한 장 종이로 뽑기', 'One-page sheet for your doctor'), 쓸모: 약말('드시는 약과 기록을 진료 때 보여 드릴 종이 한 장으로', 'Your medicines and log on one page to show at the visit'), 어디서: 약말('약통 → 진료 때 보여 드리기', 'Medicine box → Show at your visit') },
        { id: 'rx', 그림: 'book', 가기: "go('/rx')", 이름: 약말('처방약 길잡이', 'Prescription medicine guide'), 쓸모: 약말('혈압·당뇨·콜레스테롤 약을 왜·어떻게 드시는지 쉽게', 'Why and how you take blood pressure, diabetes and cholesterol medicines'), 어디서: 약말('홈 → 처방약 길잡이', 'Home → Prescription medicine guide') }
      ],
      늘열림: [ 약말('약 찾기·약봉투 읽기', 'Medicine search and reading your medicine bag'), 약말('복약 알림', 'Dose reminders'), 약말('응급 신호와 겹침 확인', 'Emergency signs and overlap check') ] },
    시트열기: function (html, 제목) { var v = document.getElementById('view'); if (!v) return; v.innerHTML = topBar({ back: '뒤로' }) + '<h1>' + esc(제목 || '메디나눔 회원권') + '</h1>' + html; scrollTo(0, 0); },
    시트닫기: function () { route(); },
    알림: function (t) { try { toast(t); } catch (e) {} },
    알림받기: function () { go('/notify'); },
    모양: { 주: 'btn primary', 보조: 'btn line' } });
} catch (e) {}
/* ▼▼ 보내기 부품 시작 ▼▼ */
/* ═══ 보내기 — 카카오톡으로 보내기 · 문자 · 복사 (다섯 앱 공용 부품, 2026-11-11 현욱님 「카카오톡으로 보내기」) ═══
   흐름: 앱이 보낼 글을 만든다 → 이 부품이 «미리보기 시트»를 띄운다(받는 사람이 보는 글 그대로 · 고쳐 쓰기) →
         사용자가 누를 때만 보낸다(자동 발송 없음).
   보내는 길(위에서부터 되는 것):
     ① kakaoJsKey 가 있고 글이 200자 이하 → Kakao.Share.sendDefault(텍스트 템플릿 · 링크 버튼 하나)
        (카카오 텍스트 템플릿은 글 200자까지 — 넘으면 ②로. 키가 없으면 SDK 를 아예 불러오지 않는다)
     ② navigator.share({text}) — 안드로이드·아이폰 공유창에 카카오톡이 뜬다 · 설치 앱은 Capacitor Share 플러그인(@capacitor/share, _껍데기/package.json)
     ③ 문자(sms:?body=) · 복사
   지킬 것: 주민등록번호·이메일은 기본으로 지운다. 앱이 이름 목록(빼기)을 주면 그 이름도 「보호자」 같은 말로 바꾼다.
            보낸 글은 부품이 어디에도 저장하지 않는다. 카카오 키를 켜면 보내는 글이 카카오(주) 서버를 거친다(처리방침 사실 메모 _서버/보내기_카카오_문서사실.md).
   쓰는 법(앱 끝):
     보내기.설치({ app:'gildongmu', 앱이름:'길동무', 링크:'https://gildongmu.medinanum.com/',
                   언어: function(){ return 'ko'; }, 시트열기: openSheetHTML, 시트닫기: closeSheet, 알림: function(m){...},
                   빼기: function(){ return [내 이름, ...]; } });
     보내기.열기({ 제목:'가족에게 보내기', 설명:'받는 분에게 이렇게 보여요', 글: '...' });
   키: 아래 값표 kakaoJsKey 한 곳(기본 빈칸 — 현욱님이 Kakao Developers 에 앱·도메인 등록 뒤 넣는다). 설치({kakaoJsKey}) 로 앱별로 덮을 수도 있다.
   SDK: 카카오 공식 CDN t1.kakaocdn.net 2.8.2 · 무결성(sha384) 고정. */
(function () {
  if (window.보내기 && window.보내기.판) return;   /* 11-11b 소아 — 앱에 같은 이름 전역 함수가 있으면 덮지 않고 window.mn보내기 로만 */
  var 판 = '2026-11-12a';   /* 11-11d CS — 알림 예비는 console.info(기본 대화상자 금지) · 설치({안제목:false}) 면 시트 안 h2 를 빼고 제목은 시트열기 둘째 값으로만 */   /* 11-11c 약지도 — 설치 앱(껍데기)에는 navigator.share 가 없다 → Capacitor Share 플러그인 · 설치 앱에서는 카카오 SDK 대신 공유창(웹뷰에서 카카오톡이 안 열리는 일이 있다) */
  var 값표 = { kakaoJsKey: '07a59184ffa26f6894c241191f0013b6', sdk: 'https://t1.kakaocdn.net/kakao_js_sdk/2.8.2/kakao.min.js', sdkSri: 'sha384-zt/G7/KfaRQ9dT/QIkS0ujMtzouJqzuSJcXVQu50x0rl/+mD1dc70AeOejVbMD9E', 카카오글한도: 200 };
  var 설정 = { 안제목: true, app: '', 앱이름: '', 링크: 'https://medinanum.com/', 언어: null, 시트열기: null, 시트닫기: null, 알림: null, 빼기: null };
  var 말 = {
    ko: { 카톡: '카카오톡으로 보내기', 문자: '문자로', 복사: '복사', 또는: '또는', 복사됨: '복사했어요 — 카카오톡이나 문자에 붙여 넣어 보내 주세요', 못함: '이 기기에서는 바로 보낼 수 없어요. 글을 길게 눌러 복사해 주세요.',
          미리: '받는 분에게 이렇게 보여요. 고쳐서 보내셔도 돼요.', 조용: '보내는 글은 이 기기에서 만들어지고, 앱은 보관하지 않아요. 누르실 때만 보내져요.', 카조용: '카카오톡으로 보내기를 누르시면 이 글이 카카오를 거쳐 전달돼요.', 뺌: '주민등록번호·이메일처럼 알아볼 수 있는 정보는 빼고 담았어요.', 버튼: '앱에서 보기', 보낼글: '보낼 글' },
    en: { 카톡: 'Send via KakaoTalk', 문자: 'Text message', 복사: 'Copy', 또는: 'or', 복사됨: 'Copied — paste it into KakaoTalk or a text message', 못함: 'This device can’t send it directly. Press and hold the text to copy it.',
          미리: 'This is what they’ll see. You can edit it before sending.', 조용: 'The message is made on this device and the app doesn’t keep it. It is only sent when you tap.', 카조용: 'If you tap Send via KakaoTalk, this message passes through Kakao to be delivered.', 뺌: 'Identifying details such as ID numbers and email addresses have been left out.', 버튼: 'Open the app', 보낼글: 'Message to send' },
    es: { 카톡: 'Enviar por KakaoTalk', 문자: 'Por SMS', 복사: 'Copiar', 또는: 'o', 복사됨: 'Copiado: péguelo en KakaoTalk o en un SMS', 못함: 'Este dispositivo no puede enviarlo directamente. Mantenga pulsado el texto para copiarlo.',
          미리: 'Así lo verá quien lo reciba. Puede editarlo antes de enviar.', 조용: 'El mensaje se crea en este dispositivo y la app no lo guarda. Solo se envía cuando usted pulsa.', 카조용: 'Si pulsa Enviar por KakaoTalk, el mensaje pasa por Kakao para entregarse.', 뺌: 'Se han quitado datos identificativos como números de identidad o correos.', 버튼: 'Abrir la app', 보낼글: 'Mensaje para enviar' },
    ja: { 카톡: 'カカオトークで送る', 문자: 'SMSで', 복사: 'コピー', 또는: 'または', 복사됨: 'コピーしました — カカオトークやSMSに貼り付けて送ってください', 못함: 'この端末からは直接送れません。文字を長押ししてコピーしてください。',
          미리: '受け取る人にはこう見えます。直してから送ってもかまいません。', 조용: '送る文はこの端末で作られ、アプリは保存しません。押したときだけ送られます。', 카조용: 'カカオトークで送るを押すと、この文はカカオを通って届きます。', 뺌: '住民登録番号・メールアドレスなど、個人がわかる情報は外しました。', 버튼: 'アプリで見る', 보낼글: '送る文' },
    zh: { 카톡: '用 KakaoTalk 发送', 문자: '发短信', 복사: '复制', 또는: '或', 복사됨: '已复制——请粘贴到 KakaoTalk 或短信里发送', 못함: '这台设备无法直接发送。请长按文字复制。',
          미리: '对方看到的就是这样。发送前可以修改。', 조용: '要发送的内容在本设备上生成，应用不会保存。只有您点按时才会发送。', 카조용: '点按“用 KakaoTalk 发送”时，这条内容会经由 Kakao 传送。', 뺌: '身份证号、邮箱等可识别个人的信息已去掉。', 버튼: '在应用中查看', 보낼글: '要发送的内容' }
  };
  function 언() { var l = 'ko'; try { l = (설정.언어 && 설정.언어()) || document.documentElement.lang || 'ko'; } catch (e) {} l = String(l).slice(0, 2); return 말[l] ? l : 'ko'; }
  function 글(k) { return (말[언()] || 말.ko)[k] || 말.ko[k]; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function 키() { return 설정.kakaoJsKey || 값표.kakaoJsKey || ''; }
  /* 알아볼 수 있는 정보 빼기 — 주민등록번호 · 이메일 · 앱이 준 이름 */
  function 다듬기(t) {
    var s = String(t || ''), 뺐다 = false;
    var 주 = /\b\d{6}\s?-\s?[1-8]\d{6}\b/g, 메 = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
    if (주.test(s) || 메.test(s)) { 뺐다 = true; s = s.replace(주, '').replace(메, ''); }
    try { var 이름들 = typeof 설정.빼기 === 'function' ? (설정.빼기() || []) : [];
      이름들.forEach(function (n) { n = String(n || '').trim(); if (n.length < 2) return; if (s.indexOf(n) >= 0) { 뺐다 = true; s = s.split(n).join(''); } }); } catch (e) {}
    return { 글: s.replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim(), 뺐다: 뺐다 };
  }
  /* 카카오 SDK — 키가 있을 때만, 처음 누를 때 한 번 */
  var sdk약속 = null;
  function sdk() {
    if (!키()) return Promise.reject(new Error('nokey'));
    if (window.Kakao && window.Kakao.Share) { try { if (!Kakao.isInitialized()) Kakao.init(키()); } catch (e) {} return Promise.resolve(window.Kakao); }
    if (sdk약속) return sdk약속;
    sdk약속 = new Promise(function (res, rej) {
      var sc = document.createElement('script'); sc.src = 값표.sdk; sc.integrity = 값표.sdkSri; sc.crossOrigin = 'anonymous'; sc.async = true;
      sc.onload = function () { try { if (!Kakao.isInitialized()) Kakao.init(키()); res(window.Kakao); } catch (e) { rej(e); } };
      sc.onerror = function () { sdk약속 = null; rej(new Error('sdk')); };
      document.head.appendChild(sc);
    });
    return sdk약속;
  }
  function 알림(m) { try { if (typeof 설정.알림 === 'function') return 설정.알림(m); } catch (e) {} try { console.info(m); } catch (e) {} }   /* 11-11 CS — 브라우저 기본 대화상자 금지(웹뷰에서 막힘 · CS 대화상자 시험). 앱은 설치 알림: 으로 넘긴다 */
  function 지금글() { var t = document.getElementById('mnSendTx'); return t ? String(t.value || '') : ''; }
  function 네이티브() { try { var C = window.Capacitor; return !!(C && typeof C.isNativePlatform === 'function' && C.isNativePlatform()); } catch (e) { return false; } }
  function 앱공유() {
    try { var C = window.Capacitor; if (!네이티브()) return null;
      if (C.Plugins && C.Plugins.Share) return C.Plugins.Share;
      if (typeof C.registerPlugin === 'function') return C.registerPlugin('Share'); } catch (e) {}
    return null;
  }
  function 공유창(t) {
    try { if (navigator.share) { return navigator.share({ text: t }).then(function () { return true; }, function (e) { return !(e && e.name !== 'AbortError') ? true : false; }); } } catch (e) {}
    try { var P = 앱공유(); if (P && typeof P.share === 'function') {   /* 설치 앱 — @capacitor/share */
      return P.share({ text: t, dialogTitle: 글('카톡') }).then(function () { return true; }, function (e) { return /cancel/i.test(String((e && (e.message || e.code)) || '')); }); } } catch (e) {}
    return Promise.resolve(false);
  }
  function 복사(t) {
    function 옛() { try { var a = document.createElement('textarea'); a.value = t; a.setAttribute('readonly', ''); a.style.cssText = 'position:fixed;left:-9999px'; document.body.appendChild(a); a.select(); var ok = document.execCommand('copy'); a.remove(); return ok; } catch (e) { return false; } }
    try { if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(t).then(function () { 알림(글('복사됨')); }, function () { if (옛()) 알림(글('복사됨')); else 알림(글('못함')); }); } catch (e) {}
    if (옛()) 알림(글('복사됨')); else 알림(글('못함'));
    return Promise.resolve();
  }
  function 카톡() {
    var t = 지금글(); if (!t.trim()) return;
    var 링크 = 설정.링크 || 'https://medinanum.com/';
    var 카카오되나 = !!키() && t.length <= 값표.카카오글한도 && !네이티브();   /* 설치 앱은 공유창(카카오톡이 그 안에 뜸) */
    var 길 = 카카오되나 ? sdk().then(function (K) {
        K.Share.sendDefault({ objectType: 'text', text: t, link: { mobileWebUrl: 링크, webUrl: 링크 }, buttonTitle: 글('버튼') });
        return true;
      }) : Promise.reject(new Error('skip'));
    return 길.catch(function () { return 공유창(t); }).then(function (됨) { if (!됨) return 복사(t); });
  }
  function 문자() {
    var t = 지금글(); if (!t.trim()) return;
    try { location.href = 'sms:?body=' + encodeURIComponent(t); } catch (e) { 복사(t); }
  }
  function 스타일() {
    if (document.getElementById('mnsend-css')) return;
    var A = 'var(--accent,var(--teal,#23685A))', L = 'var(--line,rgba(127,127,127,.28))', D = 'var(--ink2,var(--muted,inherit))';
    var st = document.createElement('style'); st.id = 'mnsend-css';
    st.textContent = '.mnsend{word-break:keep-all;overflow-wrap:anywhere}.mnsend-sub{margin:0 0 10px;color:' + D + ';line-height:1.55}'
      + '.mnsend textarea{display:block;box-sizing:border-box;width:100%;min-height:140px;padding:14px;border-radius:16px;border:1px solid ' + L + ';background:var(--card,transparent);color:inherit;font:inherit;font-size:17px;line-height:1.6;resize:vertical}'
      + '.mnsend-kk{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;min-height:56px;margin-top:12px;border:0;border-radius:14px;background:#FEE500;color:#191919;font:inherit;font-size:1.05em;font-weight:800;cursor:pointer}'
      + '.mnsend-kk svg{width:22px;height:22px;flex:none}'
      + '.mnsend-sm{display:flex;justify-content:center;align-items:center;gap:6px;margin-top:8px;color:' + D + ';font-size:.92em}'
      + '.mnsend-sm button{min-height:44px;padding:0 10px;border:0;background:none;color:' + A + ';font:inherit;font-weight:700;cursor:pointer}'
      + '.mnsend-note{margin:8px 0 0;font-size:.82em;line-height:1.5;color:' + D + '}';
    document.head.appendChild(st);
  }
  var 말풍선 = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="#191919" d="M12 3.5c-5 0-9 3.2-9 7.1 0 2.5 1.6 4.7 4.1 6l-1 3.6c-.1.3.3.6.6.4l4.2-2.8c.4 0 .7.1 1.1.1 5 0 9-3.2 9-7.2S17 3.5 12 3.5z"/></svg>';
  function 시트HTML(o, d) {
    return '<div class="mnsend">' + (o.설명 !== false ? '<p class="mnsend-sub">' + esc(o.설명 || 글('미리')) + '</p>' : '')
      + '<label class="sr-only" for="mnSendTx" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">' + esc(글('보낼글')) + '</label>'
      + '<textarea id="mnSendTx" rows="6" data-raw="1">' + esc(d.글) + '</textarea>'
      + '<button type="button" class="mnsend-kk" onclick="mn보내기.카톡()">' + 말풍선 + esc(글('카톡')) + '</button>'
      + '<div class="mnsend-sm"><span>' + esc(글('또는')) + '</span><button type="button" onclick="mn보내기.문자()">' + esc(글('문자')) + '</button><span aria-hidden="true">·</span><button type="button" onclick="mn보내기.복사()">' + esc(글('복사')) + '</button></div>'
      + (d.뺐다 ? '<p class="mnsend-note">' + esc(글('뺌')) + '</p>' : '')
      + '<p class="mnsend-note">' + esc(글('조용')) + (키() ? ' ' + esc(글('카조용')) : '') + '</p></div>';
  }
  var 손잡이 = {
    판: 판, 값표: 값표,
    설치: function (o) { o = o || {}; for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) 설정[k] = o[k]; return this; },
    열기: function (o) {
      o = o || {}; 스타일();
      var d = 다듬기(typeof o.글 === 'function' ? o.글() : o.글);
      var h = (o.제목 && 설정.안제목 !== false ? '<h2>' + esc(o.제목) + '</h2>' : '') + 시트HTML(o, d);
      if (typeof 설정.시트열기 === 'function') { try { 설정.시트열기(h, o.제목 || 글('카톡')); return; } catch (e) {} }
      var v = document.getElementById('mnSendSheet'); if (v) v.remove();
      v = document.createElement('div'); v.id = 'mnSendSheet'; v.setAttribute('role', 'dialog'); v.setAttribute('aria-modal', 'true'); v.setAttribute('aria-label', o.제목 || 글('카톡'));
      v.style.cssText = 'position:fixed;left:0;right:0;bottom:0;max-height:88vh;overflow:auto;overscroll-behavior:contain;z-index:2147482000;padding:16px;background:var(--bg,#fff);border-top:1px solid rgba(0,0,0,.15)';
      v.innerHTML = h; document.body.appendChild(v);
    },
    카톡: 카톡, 문자: 문자, 복사: function () { var t = 지금글(); if (t.trim()) 복사(t); },
    다듬기: function (t) { return 다듬기(t).글; },
    키있나: function () { return !!키(); }
  };
  window.mn보내기 = 손잡이;
  if (window.보내기) { try { console.warn('보내기 부품: 앱에 같은 이름(보내기)이 있어 window.mn보내기 로만 엽니다'); } catch (e) {} }
  else window.보내기 = 손잡이;
})();
/* ▲▲ 보내기 부품 끝 ▲▲ */
/* 11-11 Main(현욱님) — 카카오톡으로 보내기 공용 부품. 키는 빈칸(없으면 카카오 SDK 를 부르지 않고 휴대폰 공유창 → 문자·복사).
   설치 앱(웹뷰)은 11-11c 부품이 Capacitor Share 플러그인으로 공유창을 연다(껍데기 @capacitor/share 8). */
try {
  mn보내기.설치({ app: 'yakjido', 앱이름: '약지도', 링크: 'https://yakjido.medinanum.com/',
    kakaoJsKey: '07a59184ffa26f6894c241191f0013b6',   /* 11-11 카카오 JavaScript 키(공개용 · yakjido.medinanum.com 등록) — 여기 한 곳 */
    언어: function () { return window.LANG || 'ko'; },
    시트열기: function (html, 제목) { var v = document.getElementById('view'); if (!v) return; v.innerHTML = topBar({ back: '뒤로' }) + html.replace(/^<h2>/, '<h1>').replace(/<\/h2>/, '</h1>'); scrollTo(0, 0); },
    시트닫기: function () { route(); },
    알림: function (t) { try { toast(t); } catch (e) {} } });
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


/* 설정의 「약관·개인정보」 칸 · 내 정보 맨 위 계정 줄 · 처음 안내 끝의 계정 칸 — index 는 ext('이름') 으로 부른다(첫 화면 예산) */
/* 11-11 Main — 사업자 정보 한 줄(정본 yozm-health _서버/운영자.json · 전화는 050 개통 뒤) */
window.BIZ_LINE = '메디나눔 · 대표 박민욱 · 사업자등록번호 799-14-03176 · 서울특별시 강동구 천중로 147, 204호 · contact@medinanum.com · 통신판매업 신고 준비 중';
window.약관칸 = () => { const c = consentRec(); return `<section class="sec card" id="legal"><h2>약관·개인정보</h2><div class="rows-l" style="margin-top:10px">${lrow(I.book, '이용약관', '약지도를 쓰실 때의 약속', "go('/doc/terms')")}${lrow(I.lock, '개인정보 처리방침', '무엇을 어디에 두는지', "go('/doc/privacy')")}</div>
  <p class="small muted" style="margin-top:8px">${c && c.at ? `동의한 날 ${esc(c.at)} · 판 ${esc(c.v || '')}` : '동의 기록이 이 휴대폰에 없어요'}</p>
  <p class="small muted biz-line" style="margin-top:10px">${esc(BIZ_LINE)}</p></section>`; };   /* 11-10 C4 — 등록증이 오면 Main 이 다섯 앱 한 번에(대표·상호·번호) */
/* 설정의 계정 칸(meta.account 가 켜졌을 때만) — 10-14 app-shell 에서 옮김(첫 화면 예산). 내용은 그대로 */
window.계정칸 = () => D.meta?.account !== true ? '' : `<section class="sec card" id="acct"><h2>계정 <small>폰을 바꿔도 이어 보기 · 선택</small></h2>
    <p class="small muted" style="margin:4px 0 12px">로그인하지 않아도 약지도는 쓰실 수 있어요. 로그인하시면 기록을 메디나눔 서버(서울)에 복사해 두어 다른 폰에서 이어 받아요.</p>
    ${계정화면HTML()}
    ${srvAgreed() ? `<button type="button" class="srvlink" onclick="서버동의끄기()">「서버에 저장하기」 동의 거두기</button>` : ''}
  </section>`;
/* 2026-10-29 현욱님 — 설정 맨 위 첫 칸 = 계정 카드. 로그인 전엔 큰 단추 하나, 뒤엔 메일 · 이용권 · 동기화 · 로그아웃 · 계정 지우기(작게). 상세 칸(#acct)은 아래 그대로 */
/* 계정 카드·메디나눔 서명 모양 — 첫 화면 예산 때문에 여기서 붙인다 */
try { const st = document.createElement('style'); st.textContent = ".acct-card .acct-hd{display:flex;align-items:center;gap:12px}.acct-card .acct-hd>span:last-child{display:flex;flex-direction:column;min-width:0}.acct-card .acct-hd b{font-size:1.0625rem;overflow-wrap:anywhere}.acct-card .acct-hd small{color:var(--muted);font-size:.875rem;margin-top:2px}.acct-card .acct-ic,.acct-card .acct-av{flex:none;width:44px;height:44px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:var(--tint);color:var(--primary-deep)}.acct-card .acct-av{background:var(--primary);color:var(--on-primary,#fff);font-weight:700;font-size:1.125rem}.acct-card .acct-go{width:100%;margin-top:14px;min-height:52px;font-size:1.0625rem}.acct-card .acct-act{display:flex;gap:10px;margin-top:14px}.acct-card .acct-act .btn{flex:1;margin:0;min-height:48px}.acct-card .srvrow{margin-top:12px}.acct-card .acct-del{margin-top:6px;font-size:.8125rem;opacity:1;color:var(--primary);font-weight:600}.mn-logo{width:1.35em;height:1.35em;vertical-align:-.3em;margin-right:5px;color:#1A2B4A}.mn-logo path{fill:none;stroke:currentColor;stroke-width:236;stroke-linecap:round;stroke-linejoin:round}.mn-logo .mn-tile{fill:#FFFFFF;stroke:#CBD2DC;stroke-width:24}:root[data-theme=\"dark\"] .mn-logo .mn-tile{display:none}:root[data-theme=\"dark\"] .mn-logo{color:#FFFFFF}@media (prefers-color-scheme:dark){ :root:not([data-theme=\"light\"]) .mn-logo{color:#FFFFFF} :root:not([data-theme=\"light\"]) .mn-logo .mn-tile{display:none} }"; document.head.appendChild(st); } catch (e) {}
/* 10-30 현욱님 「알림 설정은?」 — 알림 한 화면: 무엇을 · 언제 · 켜기/끄기(다섯 앱 같은 꼴: 머리 + 권한 줄 + 종류별 스위치 행) */
window.문_notify = (_, q) => {
  const n = takingItems().length, timed = takingItems().filter(d => !schedUnset(d)).length;
  const perm = NATIVE ? NATIVE_PERM : ('Notification' in window ? Notification.permission : 'unsupported');
  const sw = (k, on, fn) => `<span class="sw-st">${on ? '켜짐' : '꺼짐'}</span><button class="sw ${on ? 'on' : ''}" role="switch" aria-checked="${on}" aria-label="${k}" onclick="event.stopPropagation();${fn}"></button>`;
  /* 11-10 디자인 검수 B8 — 줄 전체(56px)를 눌러도 켜고 끄며, 「켜짐/꺼짐」 글자를 함께(색만으로 가르지 않는다) */
  const row = (ic, t, s2, on, fn) => `<div class="nt-row" onclick="${fn}" style="cursor:pointer;min-height:56px"><span class="nt-ic">${ic}</span><span class="nt-t"><b>${t}</b><small>${s2}</small></span>${sw(t, on, fn)}</div>`;
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
  ${famOn() ? `<button type="button" class="link fam-jump" style="margin-top:10px" onclick="document.getElementById('fam')?.scrollIntoView({behavior:'smooth'})">가족에게 알리기 — 약 체크가 없으면 가족에게 ›</button>` : ''}
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
function famInvite(){ if (잠김('family')) return 구독.막힘('family'); const ok = document.getElementById('famOk'), ok2 = document.getElementById('famOk2'); if (!ok || !ok.checked || !ok2 || !ok2.checked) { FAMQ.msg = '가족 알림을 쓰려면 두 가지 동의에 모두 체크해 주세요. 동의하지 않아도 다른 기능은 그대로 쓸 수 있어요.'; route(); return; }
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
function famJoin(){ if (잠김('family')) return 구독.막힘('family'); const c = (document.getElementById('famCode')?.value || '').replace(/\D/g, ''); FAMQ.code = c;
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

try { const st2 = document.createElement('style'); st2.textContent = '.fam-h{display:flex;align-items:center;justify-content:flex-start;gap:8px;margin:0 0 6px;font-size:1.125rem}.fam-h .i{width:22px;height:22px}.fam-s{margin:14px 0 4px;font-size:1rem;color:var(--muted)}.fam-ul{list-style:none;margin:0;padding:0}.fam-ul li{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:10px 0;border-top:1px solid var(--hairline)}.fam-ul li>span:first-child{min-width:0}.fam-ul b{display:block;overflow-wrap:anywhere}.fam-ul small{display:block;color:var(--muted);font-size:.875rem}.fam-b{display:flex;align-items:center;gap:6px}.fam-b .btn{width:auto;min-height:44px;padding:0 14px;margin:0}.fam-b .link{min-height:44px;padding:0 8px}.fam-hot{background:var(--caution-tint);border-radius:12px;padding:10px!important}.fam-form{display:flex;flex-direction:column;gap:8px;margin-top:12px;padding-top:12px;border-top:1px dashed var(--hairline)}.fam-l{font-weight:700}.fam-form input:not([type=checkbox]){min-height:48px;padding:10px 12px;border:1.5px solid var(--ui-line);border-radius:12px;font:inherit;background:var(--card);color:var(--text)}.fam-rule{margin:6px 0 4px;padding-left:1.1em;color:var(--body);font-size:.9375rem;line-height:1.6}.fam-det{margin:4px 0;border:1px solid var(--hairline);border-radius:12px;padding:8px 12px}.fam-det summary{font-weight:700;cursor:pointer;min-height:40px;display:flex;align-items:center}.fam-det dl{margin:6px 0 0}.fam-det dt{font-weight:700;margin-top:8px}.fam-det dd{margin:2px 0 0;color:var(--body);font-size:.9375rem;line-height:1.6}.fam-off{display:block;min-height:44px;margin-top:6px}.fam-seg{display:flex;gap:6px}.fam-seg button{flex:1;min-height:44px;border:1.5px solid var(--ui-line);border-radius:12px;background:var(--card);color:var(--text);font:inherit;font-weight:700}.fam-seg button.on{background:var(--primary);color:var(--on-primary);border-color:var(--primary)}.fam-q{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.fam-q input{min-height:44px;padding:6px 10px;border:1.5px solid var(--ui-line);border-radius:12px;font:inherit;background:var(--card);color:var(--text)}.fam-q .btn{width:auto;margin:0;min-height:44px}.fam-ios{margin-top:10px}.fam-msg{padding:10px 12px;border-radius:12px;background:var(--accent-tint);color:var(--accent-text)}.nt-perm{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:10px 0 4px;padding:12px 14px;border-radius:14px;background:var(--accent-tint);color:var(--accent-text);font-size:1rem}.nt-perm.ok{background:var(--normal-tint);color:var(--normal)}.nt-perm .btn{width:auto;margin:0 0 0 auto;min-height:44px}.nt-list{padding:4px 16px}.nt-row{display:flex;align-items:center;gap:12px;padding:14px 0;border-top:1px solid var(--hairline)}.nt-row:first-child{border-top:0}.nt-ic{flex:none;width:40px;height:40px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:var(--tint);color:var(--primary-deep)}.nt-t{flex:1;min-width:0;display:flex;flex-direction:column}.nt-t b{font-size:1.0625rem}.nt-t small{color:var(--muted);font-size:.9375rem;margin-top:2px}.nt-row .sw{flex:none}.sw-st{flex:none;font-size:.875rem;font-weight:700;color:var(--muted);margin-right:2px}'; document.head.appendChild(st2); } catch (e) {}
window.계정카드 = () => { if (D.meta?.account !== true) return ''; const 나 = srvLoggedIn(), m = 나 ? (서버.세션()?.user?.email || '') : '';
  if (!나) return `<section class="sec card acct-card"><div class="acct-hd"><span class="acct-ic" aria-hidden="true">${I.user}</span><span><b>메디나눔 계정</b><small>폰을 바꿔도 약통·복용 기록을 이어 봐요 · 선택</small></span></div>
    <button type="button" class="btn primary acct-go" onclick="go('/login')">로그인 · 계정 만들기</button>${window.회원권 ? (() => { try { return '<div style="margin-top:12px">' + 회원권.줄HTML() + '</div>'; } catch (e) { return ''; } })() : ''}
    <a class="link acct-del" href="delete-account.html" style="display:inline-block;margin-top:12px;min-height:44px;line-height:44px">계정과 기록 지우기 ›</a></section>`;   /* 11-09 B4 — 로그인 전에도 늘(심사관: 계정 삭제 길이 안 보임). 웹 삭제 주소와 같은 말 */
  return `<section class="sec card acct-card"><div class="acct-hd"><span class="acct-av" aria-hidden="true">${esc(m.charAt(0).toUpperCase())}</span><span><b>${esc(m)}</b><small>로그인돼 있어요 · 이어 보기 켜짐</small></span></div>
    ${window.이용권줄HTML ? 이용권줄HTML() : ''}${window.회원권 ? (() => { try { return '<div style="margin-top:12px">' + 회원권.줄HTML() + '</div>'; } catch (e) { return ''; } })() : ''}${window.가입 && 가입.대기HTML ? (() => { try { return 가입.대기HTML() || ''; } catch (e) { return ''; } })() : ''}
    <div class="acct-act"><button type="button" class="btn line" onclick="계정동작('sync')">지금 맞추기</button><button type="button" class="btn line" onclick="계정동작('logout');setTimeout(route,600)">로그아웃</button></div>
    <button type="button" class="srvlink acct-del" onclick="go('/me?t=set');setTimeout(()=>document.getElementById('acct')?.scrollIntoView({block:'start'}),300)">계정 지우기·동의 거두기는 아래 「계정」 칸에서</button></section>`; };
window.계정줄 = () => D.meta?.account !== true ? '' : `<div class="rows-l acct-line">${srvLoggedIn() ? lrow(I.user, '메디나눔 계정', esc((서버.세션()?.user?.email || '') + ' · 이어 보기 켜짐'), "go('/login')") : lrow(I.user, '계정 만들기 · 로그인 <em class="door-tag">선택</em>', '폰을 바꿔도 이어 봐요', "go('/login')")}</div>`;
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
.cs-opt{margin:10px 2px 0;font-size:.875rem;color:var(--muted)}.cs-why{margin:8px 2px 0;font-size:.875rem;color:var(--muted);text-align:center}.cs-all{margin-top:14px;border:1.5px solid var(--hairline);background:var(--card)}.cs-item{margin-top:10px;border:1.5px solid var(--hairline);border-radius:14px;background:var(--card)}
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
.door.cs{padding-bottom:84px}.cs #csGo{position:sticky;bottom:calc(10px + env(safe-area-inset-bottom));z-index:3;box-shadow:0 6px 18px rgba(0,0,0,.18)}.cs-foot{margin-top:18px;text-align:center;font-size:.875rem;color:var(--muted);line-height:1.6}
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
.acct-line{margin-top:12px}.hello-acct{margin-top:var(--s5);padding:16px;border-radius:14px;border:1px solid var(--hairline);background:var(--card)}.hello-acct>b{display:block}.hello-acct>span{display:block;font-size:.875rem;color:var(--muted)}.hello-acct .actions{margin-top:12px}
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
  return `${topBar({ back:'뒤로' })}<h1>근거와 검수 기준</h1>
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
    if (!Object.keys(S).length && typeof SRC !== 'undefined' && SRC !== 3) return `<section class="sec"><h2>참고 문헌·지침</h2><p class="muted">출처 목록을 받는 중이에요.</p></section>`;   /* 11-12 출처는 data/src.json — 오면 이 화면만 다시 그린다 */
    return `<section class="sec"><h2>참고 문헌·지침 <small>${Object.keys(S).length}건</small></h2>
      <p class="small muted" style="margin-bottom:8px">근거가 센 것부터 묶어 두었어요. 갈래를 누르면 펼쳐져요.</p>
      ${keys.map(t => `<details class="acc"><summary>${esc(t)}<small>${g.get(t).length}건</small>${I.chev}</summary><div class="bd"><div class="rows">${g.get(t).map(row).join('')}</div></div></details>`).join('')}
    </section>`;
  })()}
  ${fold(`${I.book}오픈소스 고지`, ossList(), { cls:'oss-fold' })}
  ${disclaimer()}<p class="small muted biz-line" style="margin-top:10px">${esc(BIZ_LINE)}</p>`;
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
      '<p class="mnp-eb" style="margin:0 0 4px;font-weight:700;color:var(--ms-accent,inherit)">Language · 언어</p><h2 id="mnpT">' + 곳('제목', l) + '</h2><p class="mnp-sub">' + 곳('설명', l) + '</p>' +
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
   판: 이 파일 안 «판» 한 곳(코드의 판 값). 고치면 판을 올리고 다섯 앱에 다시 심는다. 지금 판 2026-11-05c.
   심는 순서(앱마다 같다): ① 위기번호 표 → ② 설정 부품 → ③ 응급카드 부품 — 표가 앞에 있어야 말과 나라 고르개·응급 번호가 표를 쓴다.
   심기·비교: python3 _도구/공용부품_심기.py 비교 · python3 _도구/공용부품_심기.py <소아|곁에|길동무|CS> · 다른 저장소(약지도): python3 _도구/공용부품_심기.py 파일 <경로>
   ⛔ 앱 사본을 직접 고치지 않는다 — 이 파일을 고치고 다시 심는다(심기 스크립트는 정본과 다른 사본을 보면 멈춘다).
*/
(function () {
  if (window.응급카드 && window.응급카드.__v) return;
  var 판 = '2026-11-05c', 주소열쇠 = 'mn.addr';   /* 11-05c 1330 필리핀어 표시 뺌(1330 이 필리핀어를 하지 않음) · 11-05b 1345 시간 말별·1330 시간 뺌 · 11-05a 내 말 응급 카드(10개 말) 합침 · 11-04b 머리 주석 정리 · 11-04 첫 판은 통역 줄 없음 */
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
    tl: { n: 'Filipino', t: 'Tulong pang-emergency sa Filipino', d: 'Kung nasa panganib ka ngayon, tumawag agad', a: 'ambulansya', p: 'pulis', s: 'Kung gusto mong may makausap kapag mabigat ang loob mo', k: '24 oras, sa wikang Korean', m: 'Tulong sa wikang Filipino', w: 'Lunes–Biyernes 9–18', l: 'Tumawag sa emergency number ng bansang tinitirhan mo.', c: 'Tawagan' },
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
    기본: () => ({ lang: window.LANG || 'ko', country: window.CC && window.CC !== 'XX' ? window.CC : ((window.LANG || 'ko') === 'ko' ? 'KR' : 'XX') }),   /* 11-12 사용자25 #4 — 나라를 못 맞히면(XX) 한국어 사용자는 한국으로 미리 채움(고칠 수 있음) */
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
    <div data-noko>${ko && 풀이 ? `<p class="small muted" lang="${window.LANG}">${esc(풀이)}</p>` : ''}<label class="small" for="askIn" style="display:block;margin-top:8px">약사님께 묻고 싶은 것 한 줄 <small class="muted">선택 · 서버에 올리지 않아요</small></label>
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

/* 11-09 실사용 검수 A1 — 「잊었을 때」와 짝인 한 화면. 근거: NHS 파라세타몰(«최대량을 넘겼으면 괜찮아도 곧바로 응급실 — 간 손상은 늦게»)·NHS 중독(«토하게 하지 말 것·포장을 가져갈 것»).
   ⛔ 번호는 119·응급실만 — 1339 는 질병관리청 감염병 상담이라 중독 번호가 아니다(한국 일반인용 단일 중독센터는 확인 전). 적은 것은 이 기기에만(od.v1) */
var OD_KEY = 'yakjido.od.v1';
window.odGet = function(){ try { return JSON.parse(localStorage.getItem(OD_KEY) || '{}') || {}; } catch (e) { return {}; } };
window.odSet = function(k, v){ const o = odGet(); o[k] = String(v || '').slice(0, 80); try { localStorage.setItem(OD_KEY, JSON.stringify(o)); } catch (e) {} };
window.odNow = function(){ const t = new Date(), v = String(t.getHours()).padStart(2, '0') + ':' + String(t.getMinutes()).padStart(2, '0'); odSet('at', v); const el = document.getElementById('od-at'); if (el) el.value = v; };
window.vOdS = function(_, q){ q = q || {};
  const o = odGet(), kid = q.kid === '1';
  const fld = (k, label, ph, id) => `<label class="od-f"><span>${label}</span><input type="text"${id ? ` id="${id}"` : ''} value="${esc(o[k] || '')}" placeholder="${ph}" oninput="odSet('${k}',this.value)"></label>`;
  const kidCard = `<section class="sec card od-c"><h2>아이가 먹었어요</h2><p>양이 적어 보여도 <b>바로 119</b>에 전화하세요. 아이 <b>몸무게</b>와 먹은 약·양을 알려 주시면 위험한 양인지 바로 판단해요.</p><a class="call" href="tel:119"><svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z" fill="currentColor"/></svg> 119 전화</a></section>`;
  return `${topBar({ back:'뒤로' })}
  <section class="sec"><h1>많이 먹었을 때 · 두 번 먹었을 때</h1></section>
  <div class="flag od-top" role="alert">${I.alert}<div><b>많이 먹었거나, 얼마나 먹었는지 모르거나, 아이가 먹었다면 — 증상이 없어도 지금 119에 전화하거나 응급실로 가세요.</b><p>약 상자와 남은 약을 들고 가세요. 억지로 토하게 하지 마시고, 직접 운전해서 가지 마세요.</p></div></div><a class="call od-big" href="tel:119"><svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z" fill="currentColor"/></svg> 119 전화</a>
  ${kid ? kidCard : ''}
  <section class="sec card od-c"><h2>한 번 몫을 더 먹었어요</h2><p>다음 차례는 <b>건너뛰고</b> 원래 시간으로 돌아가세요. 한 번 몫을 또 드시지 마세요.</p><p>이럴 땐 지금 <b>119</b>에 전화해 상담하세요 — 아세트아미노펜이 하루 최대량을 넘었을 때, 혈압약·당뇨약·심장약·피를 묽게 하는 약·수면제·신경안정제를 두 번 드셨을 때, 어지럽거나 가슴이 두근거리거나 몹시 졸릴 때.</p></section>
  <section class="sec card od-c"><h2>아세트아미노펜(타이레놀 등)이라면</h2><p><b>하루 최대량을 넘겨 드셨다면 아프지 않아도 지금 응급실</b>로 가세요. 첫날은 증상이 거의 없어요. 해독제는 빨리 쓸수록 잘 들어요.</p><p class="small muted">감기약·몸살약·복합진통제에도 들어 있어요. 여러 개를 함께 드셨다면 모두 더해 보세요.</p></section>
  ${kid ? '' : kidCard}
  <section class="sec card od-c"><h2>119에 알릴 것 적어 두기</h2><div class="od-fs">${fld('drug', '먹은 약', '예: 타이레놀 500 mg')}${fld('amt', '먹은 양', '예: 6알')}${fld('at', '먹은 시각', '예: 14:30', 'od-at')}${fld('kg', '몸무게(아이)', '예: 14 kg')}</div><button type="button" class="btn line" onclick="odNow()">지금 시각 넣기</button><p class="small muted">적은 내용은 서버에 올리지 않아요.</p></section>
  <p class="small muted od-src">근거: 영국 국민보건서비스(NHS) 중독 안내 · 파라세타몰 안내</p>
  ${disclaimer()}`;
};
try { const st = document.createElement('style'); st.textContent = '.od-fs{display:grid;gap:10px;margin:8px 0 12px}.od-f{display:grid;gap:4px}.od-f input{width:100%;box-sizing:border-box;min-height:48px;padding:0 12px;border:1px solid var(--hairline);border-radius:12px;font:inherit}.od-c .call{margin-left:calc(-1 * var(--s4));margin-right:calc(-1 * var(--s4));width:calc(100% + 2 * var(--s4))!important;border-radius:0!important}.od-big{margin-top:10px!important}.od-c .call,.od-top .call,.od-big{margin-top:12px;display:flex;width:100%;min-height:56px;justify-content:center;font-size:1.0625rem;background:var(--alert)!important;color:var(--on-alert,#fff)!important;text-decoration:none!important;border-radius:14px}'; document.head.appendChild(st); } catch (e) {}

/* 11-12 앱 껍데기에서 옮김 + 혈당 공복·식후 따로 · 7일 평균 */
window.vitalChart = function (k){
  const L = vitals().filter(x => x.k === k && x.t.slice(0, 10) >= dayBefore(13)).sort((a, b) => a.t.localeCompare(b.t));
  if (L.length < 2) return `<p class="small muted" style="margin-top:8px">두 번 이상 적으시면 2주 흐름을 그림으로 보여 드려요.</p>`;
  /* 3차 #7 — 축 글자도 최소 14 px, 글자 크기 설정을 따라 커지고 여백도 함께 */
  const fz = Math.max(14, Math.round((parseFloat(getComputedStyle(document.documentElement).fontSize) || 16) * .875));
  const W = Math.round(Math.min(560, Math.max(280, (innerWidth || 390) - 72))), H = 170 + fz * 2, pl = Math.ceil(fz * 1.9) + 8, pr = 12, pt = fz + 4, pb = fz + 14;
  const t0 = new Date(dayBefore(13) + 'T00:00').getTime(), t1 = new Date(dayKey(new Date()) + 'T23:59').getTime();
  const X = t => pl + (new Date(t).getTime() - t0) / (t1 - t0) * (W - pl - pr);
  const vals = k === 'bp' ? L.flatMap(x => [x.s, x.d]) : L.map(x => x.v);
  const ref = k === 'bp' ? [VREF.bp.s, VREF.bp.d] : [];
  let lo = Math.min(...vals, ...ref), hi = Math.max(...vals, ...ref);
  const step = k === 'bp' ? 20 : 50; lo = Math.floor((lo - 5) / step) * step; hi = Math.ceil((hi + 5) / step) * step;
  const Y = v => pt + (hi - v) / (hi - lo) * (H - pt - pb);
  const ticks = []; for (let v = lo; v <= hi; v += step) ticks.push(v);
  const grid = ticks.map(v => `<line x1="${pl}" x2="${W - pr}" y1="${Y(v)}" y2="${Y(v)}" class="vz-grid"/><text x="${pl - 6}" y="${Y(v) + 4}" text-anchor="end" class="vz-ax">${v}</text>`).join('');
  const days = [13, 6, 0].map(n => { const d = new Date(); d.setDate(d.getDate() - n); return `<text x="${Math.max(pl + fz * 1.3, Math.min(W - pr - fz * 1.3, X(dayKey(d) + 'T12:00')))}" y="${H - 6}" text-anchor="middle" class="vz-ax">${d.getMonth() + 1}/${d.getDate()}</text>`; }).join('');
  const refs = ref.map((v, i) => `<line x1="${pl}" x2="${W - pr}" y1="${Y(v)}" y2="${Y(v)}" class="vz-ref"/>`).join('');
  const line = (f, c, LL = L) => `<polyline points="${LL.map(x => `${X(x.t).toFixed(1)},${Y(x[f]).toFixed(1)}`).join(' ')}" class="vz-line ${c}"/>` +
    LL.map(x => `<circle cx="${X(x.t).toFixed(1)}" cy="${Y(x[f]).toFixed(1)}" r="4.5" class="vz-dot ${c}"><title>${x.t.slice(5, 10).replace('-', '/')} ${x.t.slice(11)} · ${k === 'bp' ? x.s + '/' + x.d + ' mmHg' : x.v + ' mg/dL'}</title></circle>`).join('');
  const sub = w => L.filter(x => (x.w || '') === w), oth = L.filter(x => !['공복', '식후 2시간'].includes(x.w || ''));
  const series = k === 'bp' ? line('s', 'v1') + line('d', 'v2') : line('v', 'v1', sub('공복')) + line('v', 'v2', sub('식후 2시간')) + oth.map(x => `<circle cx="${X(x.t).toFixed(1)}" cy="${Y(x.v).toFixed(1)}" r="4.5" class="vz-dot v3"><title>${x.t.slice(5, 10).replace('-', '/')} ${esc(x.w || '')} · ${x.v} mg/dL</title></circle>`).join('');   /* 11-12 Main 잠정 8 — 공복·식후를 한 선으로 잇지 않는다 */
  const legend = k === 'bp' ? `<div class="vz-legend"><span><i class="v1"></i>위 혈압(수축기)</span><span><i class="v2"></i>아래 혈압(이완기)</span></div>` : `<div class="vz-legend"><span><i class="v1"></i>공복</span><span><i class="v2"></i>식후 2시간</span>${oth.length ? '<span><i class="v3"></i>그 밖(점만)</span>' : ''}</div>`;
  /* 외부 검수 4차 #5 — 가장 큰 글씨에서 기준선 글자(위 135·아래 85)가 마지막 점과 겹쳤다. 글자는 그래프 위 한 줄로, 그래프 안에는 점선만 */
  const L7 = vitals().filter(x => x.k === 'bg' && x.t.slice(0, 10) >= dayBefore(6)), avg = w => { const v = L7.filter(x => x.w === w).map(x => x.v); return v.length ? Math.round(v.reduce((a, b) => a + b, 0) / v.length) + ` (${v.length}번)` : ''; };
  const refLine = k === 'bp' ? `<p class="vz-refl"><i class="ref"></i>가정혈압 기준: 위 ${VREF.bp.s} / 아래 ${VREF.bp.d}</p>` : (avg('공복') || avg('식후 2시간') ? `<p class="vz-refl">최근 7일 평균 — ${[avg('공복') && '공복 ' + avg('공복'), avg('식후 2시간') && '식후 2시간 ' + avg('식후 2시간')].filter(Boolean).join(' · ')} mg/dL</p>` : '');
  return `${refLine}<svg class="vz" style="--vz:${fz}px" viewBox="0 0 ${W} ${H}" role="img" aria-label="최근 2주 ${k === 'bp' ? '혈압' : '혈당'} 흐름 — 아래 목록에 같은 숫자가 있어요">${grid}${refs}${days}${series}</svg>${legend}`;
}
try { const st = document.createElement('style'); st.textContent = '.vz-dot.v3{fill:var(--muted)}.vz-legend i.v3{background:var(--muted)}'; document.head.appendChild(st); } catch (e) {}
/* 11-09 앱 껍데기에서 옮김(첫 화면 예산) */
window.vVitalsS = function(){
  const k = VT.k, L = vitals(), mine = L.map((x, i) => ({ ...x, i })).filter(x => x.k === k).reverse();
  const av = bpAvg(7), hiAvg = av && av.n >= 3 && (av.s >= VREF.bp.s || av.d >= VREF.bp.d);
  const takesBp = takingItems().some(d => ingOf(d).ings.some(e => (e.cls || []).some(c => ['arb', 'acei', 'ccb', 'beta', 'diuretic', 'bp-any'].includes(c))));
  const lastBp = L.filter(x => x.k === 'bp').slice(-1)[0];
  const form = k === 'bp' ? `
    <div class="vt-row"><label class="vt-f"><span>위 혈압</span><input id="vs" type="number" inputmode="numeric" min="60" max="260" placeholder="128" aria-label="위 혈압(수축기)"></label>
      <b class="vt-sl">/</b><label class="vt-f"><span>아래 혈압</span><input id="vd" type="number" inputmode="numeric" min="30" max="160" placeholder="82" aria-label="아래 혈압(이완기)"></label>
      <label class="vt-f"><span>맥박 <small>(선택)</small></span><input id="vp" type="number" inputmode="numeric" min="30" max="220" placeholder="72" aria-label="맥박(선택)"></label></div>
    <div class="times vt-wchips" style="margin-top:10px">${['아침', '낮', '저녁'].map(w => `<button class="chip ${(VT.w || slotWord(new Date())) === w ? 'on' : ''}" data-w="${w}" aria-pressed="${(VT.w || slotWord(new Date())) === w}" onclick="VT.w='${w}';document.querySelectorAll('.vt-wchips .chip').forEach(b=>{const on=b===this;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on)})">${w}</button>`).join('')}</div>${vtWhenBox()}`
  : `<div class="vt-row"><label class="vt-f"><span>혈당 (mg/dL)</span><input id="vg" type="number" inputmode="numeric" min="20" max="600" placeholder="110" aria-label="혈당"></label></div>
    <div class="times vt-gchips" style="margin-top:10px">${['공복', '식후 2시간', '그 밖'].map(w => `<button class="chip ${(VT.gw || '공복') === w ? 'on' : ''}" aria-pressed="${(VT.gw || '공복') === w}" onclick="VT.gw='${w}';document.querySelectorAll('.vt-gchips .chip').forEach(b=>{const on=b===this;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on)})">${w}</button>`).join('')}</div>${vtWhenBox()}`;
  return `${topBar({ back:'내 정보' })}<div class="eyebrow">혈압·혈당 수첩</div><h1>적어 두신 숫자, 진료 때 한눈에</h1>
  <p style="margin-top:6px">집에서 잰 혈압·혈당을 적어 두면 <b>2주 흐름</b>과 <b>7일 평균</b>을 보여 드려요. ${savedWhere()}</p>
  <div class="seg" style="margin-top:14px" role="group" aria-label="무엇을 적을까요">${[['bp', '혈압'], ['bg', '혈당']].map(([v, n]) => `<button class="${k === v ? 'on' : ''}" onclick="VT.k='${v}';VT.alert=null;route()" aria-pressed="${k === v}">${n}</button>`).join('')}</div>
  ${vitalAlert()}
  <section class="sec card"><h2>지금 잰 값 적기</h2>${form}
    <div class="actions" style="margin-top:12px"><button class="btn" onclick="vitalSave()">${I.check} 적어 두기</button></div></section>
  ${k === 'bp' && av ? `<section class="sec card vt-sum"><div class="vt-big"><span>최근 7일 평균</span><b>${av.s}<small>/</small>${av.d}</b><em>mmHg · ${av.days}일 ${av.n}번</em></div>
    ${hiAvg ? `<div class="note" style="margin-top:10px">${I.info}<span><b>가정혈압 기준(135/85)보다 높은 편이에요.</b> ${takesBp ? '혈압약을 드시고 계시니, 이 기록을 <b>다음 진료 때 보여 주세요.</b>' : '며칠 더 재 보시고, 계속 높으면 <b>내과 진료</b>를 받아 보세요.'}</span></div>` : av.n < 3 ? `<p class="small muted" style="margin-top:8px">아침·저녁으로 며칠 더 적으시면 평균이 믿을 만해져요.</p>` : ''}
    ${lastBp && hiAvg ? `<p class="small muted" style="margin-top:8px">코막힘약(슈도에페드린·페닐레프린·에페드린)은 혈압을 올릴 수 있어요 — 약국에서 「혈압이 높다」고 말씀하세요.</p>` : ''}
  </section>` : ''}
  ${window.홈보내기 && 홈보내기.켜짐() && mine.length ? `<div class="actions" style="margin-top:8px"><button class="btn line" onclick="홈보내기.보내기('P8')">혈압·혈당 기록을 내 홈으로 보내기${I.chev}</button></div>` : ''}
  <section class="sec card"><h2>2주 흐름</h2>${잠김('trend') ? `<button class="btn line" style="margin-top:8px" onclick="구독.막힘('trend')">2주 흐름 그림은 구독하면 보여요${I.chev}</button>` : vitalChart(k)}</section>
  ${k === 'bp' && NATIVE ? `<section class="sec card"><div class="toggle"><div class="t"><b>혈압 재기 알림</b><span>${((ME.vitalRemind || {}).bp || []).length ? '아침 7:30 · 저녁 9:00 — 켜져 있어요' : '매일 아침·저녁 잴 시간을 알려 드려요'}</span></div><button class="btn ghost" style="width:auto;min-height:46px;padding:0 14px" onclick="vitalRemindToggle()">${((ME.vitalRemind || {}).bp || []).length ? '끄기' : '켜기'}</button></div></section>` : ''}
  <section class="sec card"><h2>적은 기록 <small>${mine.length}번</small></h2>
    ${mine.length ? `<div class="vt-list">${mine.slice(0, 30).map(x => `<div class="vt-li"><span class="vt-t">${x.t.slice(5, 10).replace('-', '/')} <small>${x.t.slice(11)} · ${esc(x.w || '')}</small></span><b>${k === 'bp' ? `${x.s}/${x.d}<small> mmHg${x.p ? ` · 맥박 ${x.p}` : ''}</small>` : `${x.v}<small> mg/dL${bgTag(x)}</small>`}</b><button class="vt-x" onclick="vitalDel(${x.i})" aria-label="이 기록 지우기">${I.x}</button></div>`).join('')}</div>` : `<div class="empty"><span class="em-ic">${I.heart}</span><b>아직 적은 기록이 없어요</b>오늘 한 번이 시작이에요. 위에서 적어 보세요.</div>`}
    ${mine.length && !NATIVE ? `<div class="actions" style="margin-top:12px"><button class="btn line" onclick="진료장()">${I.book} 진료 때 보여 드리기(인쇄·PDF)</button></div>` : ''}
  </section>
  <details class="why-more sec" ${vitals().filter(x => x.k === k).length < 3 || VT.alert === 'bp-first' ? 'open' : ''}><summary>${k === 'bp' ? '혈압, 바르게 재는 법' : '혈당, 언제 재고 어떻게 볼까요'}${I.chev}</summary>
    ${k === 'bp' ? `<ul class="how-list">
      <li><b>등을 기대고 앉아 5분 쉰 뒤</b> 재세요. 발은 바닥에, 다리는 꼬지 않아요.</li>
      <li><b>팔을 탁자에 올려 커프가 심장 높이</b>에 오게 하세요. 팔을 늘어뜨려 낮게 재면 높게 나와요.</li>
      <li><b>커프는 맨팔에, 손가락 하나가 들어갈 만큼만</b> 감으세요. 세게 감으면 높게 나와요.</li>
      <li>재는 동안 <b>말하지 않기</b>. 한 번 더 재서 두 번을 적으면 더 정확해요.</li>
      <li><b>아침</b> — 일어나 1시간 안, 소변 본 뒤, 혈압약 먹기 전 · <b>저녁</b> — 잠자기 전. <b>주 5일 이상</b> 재서 평균을 봐요.</li>
    </ul><p class="why" style="margin-top:6px">가정혈압은 <b>135/85 mmHg 이상</b>이면 높은 것으로 봐요.</p>${srcChips(VREF.bp.src, true)}`
    : `<ul class="how-list">
      <li><b>공복</b> — 아침 식사 전. 당뇨가 있으면 목표 <b>80~130 mg/dL</b></li>
      <li><b>식후 2시간</b> — 식사를 시작하고 2시간 뒤. 당뇨가 있으면 목표 <b>180 mg/dL 미만</b></li>
      <li><b>${VREF.bg.hi} mg/dL 이상</b> — 증상(구토·숨참·심한 갈증·처짐)이 있으면 바로 진료, 없으면 다시 재세요.</li>
      <li><b>70 mg/dL 미만이면 저혈당</b> — 당분 15~20 g(주스 반 컵 정도)을 드시고 15분 뒤 다시 재세요.</li>
    </ul><p class="why" style="margin-top:6px">목표는 사람마다 다를 수 있어요 — <b>담당 의사가 따로 정해 준 숫자가 있으면 그것이 우선</b>이에요.</p>${srcChips(VREF.bg.src, true)}`}
  </details>
  <div class="note soft" style="margin-top:12px">${I.alert}<span><b>갑자기 심한 두통·가슴 통증·숨참·한쪽 팔다리 힘 빠짐·말이 어눌함</b>이 있으면 숫자와 상관없이 <b>119</b>에 연락하세요.</span></div>
  ${disclaimer('기록은 진료를 돕는 참고 자료예요. 약을 늘리거나 줄이는 것은 의사와 상의하세요.')}`;
};

/* 11-09 C2 — 말과 나라 창 「맞아요」 단추: 공용 강조색(갈색 #B5711C, 흰 글자 대비 3.9:1) 대신 약지도 청록(대비 5.8:1) */
try { const st = document.createElement('style'); st.textContent = ':root{--ms-accent:#0B6E8F;--ms-on-accent:#fff}.mnp{align-items:flex-start!important}.mnp-box{margin-top:8px!important}.mnp .ms-sb{display:flex!important;flex-wrap:wrap;gap:8px;justify-content:flex-start}.mnp .ms-sb button{flex:0 0 auto!important;font-size:1rem!important;padding:0 16px;min-height:48px}';   /* 11-10 첫 실행 사진 대조 — 위 빈 띠·칩 크기 제각각 */ document.head.appendChild(st); } catch (e) {}
/* 11-10 앱 껍데기에서 옮김(첫 화면 예산) */
window.vSuppDetailS = function(id){
  const s = supp(id); if (!s) return vSupp();
  const w = suppWho(), nd = s.need ? needOf(s.need, w) : null;
  return `${topBar({ back:'영양제' })}
  <div class="drug-hero"><span class="cls">영양제 성분</span><h1>${esc(s.name)}</h1><div class="en">${evTag(s.evidence)}</div>${s.role ? `<p class="supp-role">${fmt(s.role)}</p>` : ''}</div>
  ${suppBox(s)}
  ${nd ? whoPick(w) : ''}
  ${suppFoods(s, nd)}
  <section class="sec card sq"><h2 class="sq-h"><span class="qn" aria-hidden="true">${s.foods ? 2 : 1}</span>뭐에 좋아요?</h2>
  ${s.plain ? `<div class="vrow2 yes"><b>도움 돼요</b><p>${fmt(s.plain.who)}</p></div><div class="vrow2 no"><b>도움 안 돼요</b><p>${fmt(s.plain.no)}</p></div>` : `<p class="sq-p">${fmt(s.lead || s.for || '')}</p>`}
  ${s.plain && (s.lead || s.evidenceNote) ? `<details class="acc" style="margin-top:12px"><summary>근거를 자세히<small>숫자와 시험 이름까지</small>${I.chev}</summary><div class="bd">
    ${s.lead ? `<p>${fmt(s.lead)}</p>` : ''}${s.evidenceNote ? `<p style="margin-top:10px">${fmt(s.evidenceNote)}</p>` : ''}</div></details>`
   : (s.evidenceNote ? `<details class="acc" style="margin-top:12px"><summary>어디까지 입증됐나${I.chev}</summary><div class="bd"><p>${fmt(s.evidenceNote)}</p></div></details>` : '')}
  </section>
  ${s.dose || nd ? `<section class="sec card sq"><h2 class="sq-h"><span class="qn" aria-hidden="true">${s.foods ? 3 : 2}</span>하루에 얼마나?</h2>
    ${nd ? suppNeed(s, nd, w) : ''}
    ${s.dose ? `<h3 class="sq-h3">영양제로 드신다면</h3><div class="kv" style="margin-top:8px"><div><small>흔히 쓰는 양</small><b>${fmt(s.dose.typical || '—')}</b></div><div><small>하루 상한</small><b>${fmt(s.dose.ul || '—')}</b></div></div>${s.dose.kr ? `<p class="small muted" style="margin-top:10px">${fmt(s.dose.kr)}</p>` : ''}${/확인 필요/.test(JSON.stringify(s.dose)) ? `<p class="small muted" style="margin-top:8px">「확인 필요」는 공식 문서 원문을 아직 확인하지 못했다는 뜻이에요. 라벨과 약사 안내를 따르세요.</p>` : ''}` : ''}
    ${s.plain?.watch || s.timing ? `<h3 class="sq-h3">언제, 어떻게</h3>${s.plain?.watch ? `<p class="sq-p">${fmt(s.plain.watch)}</p>` : ''}${s.timing ? `<p class="sq-p">${fmt(s.timing)}</p>` : ''}` : ''}
  </section>` : ''}
  ${s.cautions?.length ? `<section class="sec card"><h2>이것만 조심</h2>${list(s.cautions, 'plain x')}</section>` : ''}
  ${s.forms?.length || s.label?.length || s.calc || s.priceTip ? `<details class="acc pick-more"><summary>제품 고를 때<small>${[s.forms?.length && '제형', s.label?.length && '라벨', s.calc && '함량 계산', s.priceTip && '가격'].filter(Boolean).join(' · ')}</small>${I.chev}</summary><div class="bd">
  ${s.forms?.length ? `<section class="sec card"><h2>제형별 차이 <small>흡수·부작용</small></h2>${cmpRows(['흡수', '특징'], s.forms.map(f => [esc(f.name), [esc(f.bio || '—'), fmt(f.note || '')]]), { first:'제형', more:'제형 더' })}</section>` : ''}
  ${s.label?.length ? `<section class="sec card"><h2>라벨에서 볼 것</h2>${list(s.label, 'steps')}</section>` : ''}
  ${s.calc ? `<section class="sec card"><h2>내 제품 계산해 보기 <small>참고량 대비 %</small></h2><p class="small muted" style="margin-top:4px">라벨의 1회 함량과 가격을 넣으면 참고량 대비 몇 %인지, 참고량 1회분 가격이 얼마인지 보여드려요.</p>
    <div class="calc"><label>1알 또는 1포에 든 양 (${esc(s.calc.unit)})<input type="number" inputmode="decimal" id="c-amt" placeholder="${esc(String(s.calc.typical))}"></label><label>1회 분량 (정·포)<input type="number" inputmode="numeric" id="c-per" value="1" min="1" step="1"></label><label>제품 가격 (원)<input type="number" inputmode="numeric" id="c-price" placeholder="25000"></label><label>총 개수 (정·포)<input type="number" inputmode="numeric" id="c-n" placeholder="90"></label></div>
    <p class="small muted">라벨이 2알 합계로 적혀 있으면 나눠 넣어요 — 2알에 100이면 첫 칸에는 50을 넣어요.</p><p id="c-err" class="small" role="alert" style="color:var(--alert)"></p>
    <div class="calc-out"><div><small>참고량 대비</small><b id="c-pct">—</b><span class="small muted">기준 ${esc(String(s.calc.typical))} ${esc(s.calc.unit)}${s.calc.note ? ' · ' + fmt(s.calc.note) : ''}</span></div><div><small>참고량 1회분 가격</small><b id="c-won">—</b><span class="small muted">낮을수록 경제적</span></div></div>
    <p class="small muted" style="margin-top:8px">${s.calc.caveat ? fmt(s.calc.caveat) : '기준량은 함량·가격 비교용이에요. 효과가 보장되는 양이나 하루 안전 상한을 뜻하지 않아요.'}</p></section>` : ''}
  ${s.priceTip ? `<section class="sec card"><h2>가격 비교는 이렇게</h2><p>${fmt(s.priceTip)}</p></section>` : ''}
  </div></details>` : ''}
  ${s.faq?.length ? `<section class="sec card"><h2>자주 묻는 질문</h2>${faqList(s.faq)}</section>` : ''}
  ${(() => {
    /* 비타민·미네랄은 「약」으로도 팔린다 — 같은 성분이 든 일반의약품을 이어 준다 */
    /* 아직 안 왔으면 받아 두고 다시 그린다 */
    if (!PUB.index) { pubIndex().then(redraw); return ''; }
    const ps = PUB.index.filter(p => (p.map || []).includes('supp:' + s.id));
    if (!ps.length) return '';
    return `<section class="sec card"><h2>같은 성분이 든 「약」 <small class="muted" style="font-weight:500">${ps.length}개 · 식약처 e약은요</small></h2>
      <p class="small muted" style="margin:-2px 0 10px">이 성분은 <b>건강기능식품으로도, 일반의약품으로도</b> 팔려요. ${/\d/.test(s.dose?.ul || '') ? '둘을 같이 드시면 하루 상한을 넘기기 쉬워요.' : '약과 영양제에 같은 성분이 들어 있으면 먹는 양이 겹쳐요. 합친 양을 약사에게 확인하세요.'}</p>
      ${(() => { const r = p => `<button class="row" onclick="go('/pub/${p.id}')">${pubThumb(p)}<div class="body"><b>${esc(p.n)}</b><span>${esc(p.m)}</span></div>${I.chev}</button>`, L = ps.slice(0, 150);
        return `<div class="rows">${L.slice(0, 3).map(r).join('')}</div>${L.length > 3 ? `<details class="more-rows"><summary>더 보기 <span class="muted">${L.length - 3}개</span>${I.chev}</summary><div class="rows">${L.slice(3).map(r).join('')}</div></details>` : ''}`; })()}
      ${ps.length > 150 ? `<p class="small muted" style="margin-top:8px">150개만 보여 드려요 — 모두 ${ps.length}개예요. 제품 이름은 위 검색창에서 찾아 주세요.</p>` : ''}</section>`; })()}
  ${srcChips(s.sources)}
  <div class="actions two">${(() => { const on = (ME.taking || []).includes('supp:' + s.id); return `<button class="btn ${on ? 'ghost' : 'line'}" aria-pressed="${on}" onclick="toggleTaking('supp:${s.id}')">${on ? I.check + ' 내 약통에 있어요' : I.pill + ' 내 약통에 담기'}</button>`; })()}<button class="btn ghost" onclick="toggleCmp('${s.id}',true);go('/supp')">${I.scale} 비교 목록에 담기</button></div>
  ${disclaimer(D.meta?.suppDisclaimer)}`;
};
window.vPillInfoS = function(seq){
  const p = findPill(seq);
  if (!p) { if (!PUB.pills) { pubPills().then(route); return `${topBar({ back:'뒤로' })}<p class="loading">불러오는 중…</p>`; } if (!PUB.rx) { Promise.all([pubPillsRx(), rxNames()]).then(route); return `${topBar({ back:'뒤로' })}<p class="loading">처방약 자료를 불러오는 중…</p>`; }
    /* 낱알 자료를 못 받았어도(미리보기·끊긴 인터넷) 이름 목록에 있는 처방약이면 이름·회사·성분과 식약처 허가정보로 */
    const rn = (PUB.rxn || []).find(x => x[1] === String(seq)); if (!rn) return vPill();
    return `${topBar({ back:'뒤로' })}<div class="eyebrow">${rn[3] === 0 ? '약국 · 일반의약품' : '처방약'}</div><h1 style="font-size:1.25rem">${esc(rn[0].replace(/\(.*?\)/g, ''))}</h1><p class="small muted">${[rn[2], (rn[0].match(/\((.+)\)/) || [])[1]].filter(Boolean).map(esc).join(' · ')}</p><p style="margin-top:12px">${rn[3] === 0 ? '사용법은 제품 설명서를 따르고, 궁금하면 약사에게 여쭤 보세요.' : '처방약이에요. 용법·용량은 약봉투와 처방한 의사·약사 지시가 우선이에요.'}</p><div class="links" style="margin-top:12px"><a class="plink" href="https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq=${esc(rn[1])}" target="_blank" rel="noopener">${I.link}식약처 허가정보</a></div>`; }
  const img = pillImg(p); const d = drugByIngr(p.ingr, p);
  const pubHit = (PUB.index || []).find(x => x.seq === p.seq);
  const id = 'pub:' + p.seq; const taking = (ME.taking || []).includes(id) || (d && (ME.taking || []).includes(d.id));
  return `${topBar({ back:'약 알아보기' })}
  <div class="pill-hero"><div class="ph">${img ? `<img src="${esc(img)}" alt="${esc(p.n)}" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'small muted',textContent:'사진 없음'}))">` : '<span class="small muted">사진 없음</span>'}</div>
    <div><div class="eyebrow">${p.rx ? '처방약' : p.cvs ? '편의점 · 일반의약품' : '약국 · 일반의약품'}</div>${EXPORT.test(p.n) ? '<span class="badge warn">수출용 — 국내 약국에서 팔지 않아요</span>' : ''}<h1 style="font-size:1.25rem">${esc(p.n.replace(/\(.*?\)/g, ''))}</h1><p class="small muted">${esc(p.m)}${p.ingr ? ' · ' + esc(p.ingr) : ''}</p>${p.cls ? `<p class="small muted">${esc(String(p.cls).replace(/\./g, '·'))}</p>` : ''}</div></div>
  <div class="kv3"><div><small>앞 글자</small><b>${esc(p.f || '—')}</b></div><div><small>뒤 글자</small><b>${esc(p.b || '—')}</b></div><div><small>모양·색</small><b>${esc(p.sh)} · ${esc(p.c)}</b></div><div><small>크기</small><b>${p.sz ? esc(p.sz) + ' mm' : '—'}</b></div><div><small>분할선</small><b>${p.ln ? '있음' : '없음'}</b></div><div><small>구분</small><b>${p.rx ? '처방 필요' : '처방 없이'}</b></div></div>
  ${d ? `<section class="sec"><h2>약지도 성분 해설</h2><div class="card rows"><button class="row" onclick="go('/drug/${d.id}')"><div class="ic">${icon(cls(d.class)?.icon || 'pill')}</div><div class="body"><b>${esc(d.name)}</b><span>${fmt(d.tagline || '')}</span></div>${I.chev}</button></div>${meWarnings(d)}<div class="found" style="margin-top:10px"><div class="eyebrow">복용법 (약국 구입 기준)</div><div class="simple">${fmt(d.simple || '')}</div>${p.rx ? '<p class="small muted" style="margin-top:6px">처방약은 봉투에 적힌 용법이 우선이에요.</p>' : ''}</div></section>` : p.rx ? `<section class="sec"><div class="note">${I.info}<span>처방약이에요. 용법·용량은 약봉투와 처방한 의사·약사 지시가 우선이에요. 궁금하면 약봉투를 사진 찍어 올려 주세요.</span></div></section>` : ''}
  ${pubHit ? `<section class="sec card rows"><button class="row" onclick="go('/pub/${pubHit.id}')"><div class="ic">${I.info}</div><div class="body"><b>식약처 e약은요 설명 보기</b><span>효능·사용법·주의사항 평문</span></div>${I.chev}</button></section>` : ''}
  ${(() => {
    /* 이 약 자체의 항콜린 부담 — 처방약도 성분으로 풀어 본다 */
    const es = ingFind(p.ingr).concat(ingFind(p.n)).filter(e => e.ach);
    if (!es.length) return '';
    const e = es.sort((a, b) => b.ach - a.ach)[0];
    return `<section class="sec"><div class="ach ${e.ach >= 3 ? 'warn' : 'ok'}"><div class="ach-h">${e.ach >= 3 ? I.alert : I.check}<b>이 약의 항콜린 부담 — ${esc(ACH_WORD[e.ach])}</b><span class="ach-n">${e.ach}점</span></div>
      <p class="ach-w">${esc(e.n)}이 들어 있어요.${e.achNote ? ' ' + esc(e.achNote) + '.' : ''} 입마름·변비·어지럼·소변이 잘 안 나오는 것과 관계있는 성분이에요.${e.achAlt ? ` <b>${fmt(e.achAlt)}</b>` : ''}</p></div></section>`;
  })()}
  <div class="actions"><button class="btn ${taking ? 'line' : ''}" onclick="togglePub('${p.seq}')">${taking ? I.check + ' 내 약통에 있어요 (빼기)' : I.pill + ' 내 약통에 담기'}</button>${taking && takingItems().length >= 2 ? `<button class="btn ghost" onclick="go('/together')">${I.shield} 다른 약과 같이 먹어도 되는지 보기</button>` : ''}${taking ? `<button class="btn ghost" onclick="go('/schedule')">${I.clock} 복용 시간 알림 만들기</button>` : ''}</div>
  <div class="links" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px"><a class="plink" href="https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq=${esc(p.seq)}" target="_blank" rel="noopener">${I.link}식약처 허가정보</a><a class="plink" href="https://www.health.kr/searchDrug/search_detail.asp" target="_blank" rel="noopener" onclick="copyName('${esc(p.n.replace(/\(.*?\)/g, '')).replace(/'/g, "\\'")}')">${I.search}약학정보원에서 찾기</a></div>
  <div class="srcs"><span class="src-chip">${I.link}출처: 식약처 의약품 낱알식별 정보(사진 포함)</span></div>
  ${disclaimer('낱알 정보는 참고용이에요. 같은 모양의 다른 약도 있으니 확실하지 않으면 약사에게 실물을 보여 주세요.')}`;
};
window.vPubS = function(id){
  id = +id; const ix = (PUB.index || [])[id];
  if (!PUB.index) { pubIndex().then(route); return `${topBar({ back:'뒤로' })}<p class="loading">식약처 제품 정보를 불러오는 중…</p>`; }
  if (!ix) return vDrugs('', {});
  const det = PUB.chunks[Math.floor(id / (D.public?.chunk || 200))]?.[id % (D.public?.chunk || 200)];
  if (!det) { pubDetail(id).then(redraw).catch(() => {}); }
  /* map 에는 약 id 와 「supp:영양제 id」 가 섞여 있다 — 비타민 복합제도 일반의약품으로 팔리기 때문 */
  const drugIds = ix.map.filter(x => !String(x).startsWith('supp:'));
  const suppIds = ix.map.filter(x => String(x).startsWith('supp:')).map(x => String(x).slice(5));
  const ours = drugIds.map(drug).filter(Boolean);
  const oursSupp = suppIds.map(i => (D.supplements || []).find(sp => sp.id === i)).filter(Boolean);
  const dup = ours.length ? dupCheck(drugIds) : [];
  return `${topBar({ back:'약 사전' })}
  <div class="pub-hero">${ix.img ? `<img class="pillimg" src="${esc(ix.img)}" alt="${esc(ix.n)} 낱알 사진" onerror="this.remove()">` : ''}<div><div class="eyebrow">식약처 e약은요</div><h1 style="font-size:1.25rem">${esc(ix.n)}</h1><p class="small muted">${esc(ix.m)} ${ix.cvs ? '<span class="badge cvs">편의점 가능</span>' : '<span class="badge otc">약국 구입</span>'}</p></div></div>
  <div class="chips" style="margin-top:12px">${ix.i.map(x => `<span class="chip" style="min-height:32px;font-size:.875rem">${esc(x)}</span>`).join('')}</div>
  ${recallNote(ix.seq, false, ix.n)}
  ${(() => { const kf = pubKeyFacts(det); return kf.length ? `<section class="sec"><h2>먼저 보실 것</h2>
    <div class="card keyfacts">${kf.map(f => `<div class="kf"><b>${esc(f.k)}</b><span>${esc(f.v)}</span></div>`).join('')}</div>
    <p class="small muted" style="margin-top:8px">식약처 허가 용법에 적힌 그대로예요. 아래 원문에서 다시 확인하실 수 있어요.</p></section>` : ''; })()}
  ${(() => {
    /* 2026-09-30 — 성분마다 따로 뜨던 「내 정보 기준 확인」 카드 셋과 겹침 경고를 한 상자로, 위쪽에 */
    const w = meWarningsMany(ours); const dd = dup.length ? `<ul class="plain">${dup.map(t => `<li>${fmt(t)}</li>`).join('')}</ul>` : '';
    return w || dd ? `<div class="dup dupbox ${/stop/.test(w) ? 'stop' : 'warn'}" style="margin-top:16px"><div class="dup-h">${I.alert}<b>내 정보 기준 확인</b></div>${w}${dd}</div>` : ''; })()}
  ${(() => {
    /* ClinicScore 문법 — 약사 안내 · 허가 내용 · 성분 해설을 탭으로(한 번에 한 칸) */
    const hasOurs = ours.length || oursSupp.length;
    const T = [['pb2', '허가 내용'], ...(hasOurs ? [['pb3', '성분 해설', ours.length + oursSupp.length]] : [])];
    return `<nav class="tabs" role="tablist" aria-label="이 제품" style="margin-top:20px">${T.map(([k, n, c], i) => `<button class="tab ${i ? '' : 'on'}" role="tab" data-p="${k}">${n}${c ? `<span class="n">${c}</span>` : ''}</button>`).join('')}</nav>
  <div class="pane on" id="pb2">
  <section class="sec card qa">${det ? `
    <h2 class="qa-h">이 약의 효능은 무엇입니까?</h2><p>${esc(pubText(det.e))}</p>
    <h2 class="qa-h">이 약은 어떻게 사용합니까?</h2><p>${esc(pubText(det.u))}</p>
    <details class="pub-more"><summary>허가사항 원문 더 보기 — 주의사항 · 같이 쓰면 안 되는 것 · 부작용${I.chev}</summary><div class="bd">
    <h2 class="qa-h">사용상 주의사항</h2><p>${esc(pubText(det.c))}</p>
    ${det.x ? `<h2 class="qa-h">주의해야 할 약 또는 음식</h2><p>${esc(pubText(det.x))}</p>` : ''}
    ${det.s ? `<h2 class="qa-h">나타날 수 있는 이상반응</h2><p>${esc(pubText(det.s))}</p>` : ''}
    ${det.k ? `<h2 class="qa-h">보관 방법</h2><p>${esc(pubText(det.k))}</p>` : ''}
    </div></details>` : '<p class="loading">허가사항 요약을 불러오는 중…</p>'}
    <div class="srcs"><span class="src-chip">${I.link}출처: 식품의약품안전처 e약은요(의약품개요정보) · 공공데이터포털</span>${ix.img ? `<span class="src-chip">${I.link}낱알 사진: 약학정보원·식약처</span>` : ''}</div>
  </section>
  </div>
  ${hasOurs ? `<div class="pane" id="pb3">  ${ours.length ? `<section class="sec"><h2>약지도 성분 해설 <small>부담 정도·같이 먹을 때·같은 계열 비교</small></h2><div class="card rows">${ours.map(d => `<button class="row" onclick="go('/drug/${d.id}')"><div class="ic">${icon(cls(d.class)?.icon || 'pill')}</div><div class="body"><b>${esc(d.name)}</b><span>${fmt(d.tagline || (d.for || []).join(' · '))}</span></div>${I.chev}</button>`).join('')}</div></section>` : ''}
  ${oursSupp.length ? `<section class="sec"><h2>영양 성분 해설 <small>얼마나 듣는지·상한·겹침</small></h2><div class="card rows">${oursSupp.map(sp => `<button class="row" onclick="go('/supp/${sp.id}')"><div class="ic">${I.leaf}</div><div class="body"><b>${esc(sp.name)}</b><span>${esc(sp.for || '')}</span></div>${I.chev}</button>`).join('')}</div>
    <p class="small muted" style="margin-top:8px">비타민·미네랄은 <b>약으로도, 건강기능식품으로도</b> 팔려요. 다른 영양제와 겹쳐 상한을 넘기기 쉬우니 한 번 확인해 보세요.</p></section>` : ''}
</div>` : ''}`; })()}
  <div class="actions">${(() => {
    /* Z4 #1 — 복합제도 제품 그대로(모든 성분) 담는다. 전에는 성분이 하나일 때만 단추가 있었다 */
    const pid = 'pub:' + pubKeyOf(ix), on = (ME.taking || []).includes(pid);
    return on ? `<button class="btn line" onclick="togglePub('${esc(pubKeyOf(ix))}')">${I.check} 내 약통에 있어요 (빼기)</button>` : `<button class="btn ghost" onclick="addPubIx(${id});route()">${I.pill} 내 약통에 담기</button>`; })()}</div>
  ${disclaimer('식약처 허가사항의 공공데이터 요약이에요. 원문은 공백이 제거된 형태라 읽기 어려운 부분이 있을 수 있어요. 최종 확인은 약 상자의 설명서와 약사에게.')}`;
};

/* 내 정보·동의·로그인·약관 화면을 보고 있었으면 다시 그린다(이 파일이 늦게 오므로) */
/* 11-12 사용자25 #20 — 「한국어 원문 보기」로 바꾼 뒤 원래 말로 돌아갈 단추(그 말로 적음) */
(function(){ let pv = null; try { pv = localStorage.getItem('yakjido.lang.prev'); } catch (e) {} const W = { en: 'Back to English', es: 'Volver al español', ja: '日本語に戻す', zh: '返回中文' };
  if (pv && W[pv] && (localStorage.getItem('yakjido.lang') || 'ko') === 'ko') (() => { const b = document.createElement('button'); b.type = 'button'; b.className = 'lang-back'; b.textContent = W[pv]; b.onclick = () => { try { localStorage.removeItem('yakjido.lang.prev'); } catch (e) {} setLang(pv); }; document.body.appendChild(b); })(); })();
try { const st = document.createElement('style'); st.textContent = '.lang-back{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(84px + env(safe-area-inset-bottom));z-index:40;min-height:44px;padding:0 16px;border-radius:22px;border:1px solid var(--hairline);background:var(--card);color:var(--primary);font:inherit;font-weight:700;box-shadow:0 4px 14px rgba(0,0,0,.15)}'; document.head.appendChild(st); } catch (e) {}
/* 11-12 사용자25 #35 — 같은 때 약 여러 개를 한 번에 「먹음」 */
window.tickAll = function (keys) { const arr = takenSet(), L = String(keys || '').split(',').filter(Boolean); for (const k of L) if (!arr.includes(k)) arr.push(k); unskip(todayKey(), L); rollDay(); saveMe(); if (NATIVE) nativeArm(); toast(L.length + '가지를 먹음으로 적었어요'); route(); };
try { const st = document.createElement('style'); st.textContent = '.dp-h{display:flex;align-items:center;justify-content:space-between;gap:8px}.dp-all{min-height:40px;padding:0 12px;border-radius:20px;border:1px solid var(--hairline);background:var(--card);color:var(--primary);font:inherit;font-size:.875rem;font-weight:700}'; document.head.appendChild(st); } catch (e) {}
/* 11-12 사용자25 #37 — 필요할 때만 드시는 약(아이 해열제 포함): 홈에 마지막 먹은 시각과 다음 가능 시각 한 줄 */
window.필요약줄 = function () { try {
  const L = takingItems().filter(d => isPrn(d.id)).map(d => [d, prnState(d)]).filter(([, st]) => st.last); if (!L.length) return '';
  const kid = ME.age === 'child', now = new Date();
  return `<section class="sec card prn-home"><div class="rows-l">${L.slice(0, 3).map(([d, st]) => lrow(I.clock, esc(d.name), `마지막 ${hhmm(st.last)}${st.last.getDate() !== now.getDate() ? '(어제)' : ''} · ${st.next && st.next > now ? `다음은 ${hhmm(st.next)}부터` : `지금 ${kid ? '먹여도' : '드셔도'} 되는 간격이에요`}${st.max ? ` · 오늘 ${st.count}/${st.max}번` : ''}`, "go('/schedule')")).join('')}</div></section>`;
} catch (e) { return ''; } };
/* 11-12 매일 쓸 이유(10-30 현욱님) — 약통이 빈 분께 홈 첫 화면에 「오늘의 한 장」과 「약 담으면 매일 체크·연속 기록」 */
window.오늘한장 = function () { try {
  if (takingItems().length || (window.LANG && window.LANG !== 'ko')) return ''; const T = D.tips || []; if (!T.length) return '';   /* 약 상식 글은 한국어만 있어 외국어 화면에서는 뺀다 */ const t = T[new Date().getDate() % T.length];
  return `<div class="rows-l today-one" style="margin-top:10px">${lrow(icon(t.icon), '오늘의 한 장 — ' + esc(t.title), '하루 한 가지, 1분이면 읽어요', `go('/tips?open=${t.id}')`)}</div>`;
} catch (e) { return ''; } };
window.약담기권함 = function () { try { return takingItems().length ? '' : `<div class="rows-l" style="margin-top:10px">${lrow(I.clock, '드시는 약이 있으면 담아 두세요', '매일 「드셨어요」 체크와 연속 기록이 생겨요', "go('/kinds')")}</div>`; } catch (e) { return ''; } };
/* ▼ 11-12 첫 화면 예산 — 앱 껍데기에서 옮긴 화면(복용 시간 알림 · 약 상세 · 같이 먹어도 되나요). 내용은 그대로 */
window.vScheduleS = function (_, q){
  if (q && (q.tick || q.later)) { q.tick ? tickFromNote(q.tick, q.day) : webSnooze(q.later, q.day); setTimeout(() => { try { history.replaceState(null, '', '#/schedule'); } catch (e) {} }, 0); }
  const taking = takingItems(); rollDay();
  const perm = ('Notification' in window) ? Notification.permission : 'unsupported';
  const now = new Date(); const nowMin = now.getHours() * 60 + now.getMinutes(); const taken = takenSet();
  const todays = []; for (const d of taking) for (const t of schedOf(d.id, d)) { const [h, m] = t.split(':').map(Number); todays.push({ d, t, min: h * 60 + m, done: taken.includes(d.id + '@' + t), skip: isSkipped(d.id + '@' + t) }); }
  todays.sort((a, b) => a.min - b.min);
  const lateL = todays.filter(x => !x.done && !x.skip && x.min < nowMin - 60);
  return `${topBar({ back:'내 정보' })}<div class="eyebrow">복용 시간 알림 · <button type="button" class="link" onclick="go('/notify')">알림 설정</button></div><h1>오늘 약, 잊지 않게</h1>${todays.length ? todayHero(todays, nowMin) : taking.length ? '' : art('schedule', 'banner')}
  ${leadHtml('먹는 약마다 시간을 고르면 오늘 할 일이 체크 목록으로 나오고, 시간이 되면 알려드려요. **시간을 정한 약만** 알려 드려요 — 설명서·안내 간격대로 시간을 제안해 드리니 맞으면 「이 시간으로 정하기」를 누르세요.', 'margin-top:6px', todays.length || taking.length ? 'small muted' : '')}
  ${taking.filter(schedUnset).length ? `<div class="note" style="margin-top:10px">${I.clock}<span><b>시간을 아직 정하지 않은 약이 ${taking.filter(schedUnset).length}가지 있어요</b> — 아래 「약마다 시간 고르기」에서 매일 드시는지, 필요할 때만 드시는지 골라 주세요.</span></div>` : ''}
  ${!taking.length ? `<section class="sec card"><div class="empty"><b>아직 담아 둔 약이 없어요</b>약 사전에서 약을 찾아 ‘내 약통에 담기’를 누르면 여기 나와요.</div><div class="actions"><button class="btn ghost" onclick="go('/drugs')">${I.search} 약 찾기</button></div></section>` : ''}
  ${todays.length ? `<section class="sec"><h2>오늘 <small>${now.getMonth() + 1}월 ${now.getDate()}일 · ${todays.filter(x => x.done).length}/${todays.length} 완료</small></h2>${daypartGroups(todays).map(([part, list]) => `<div class="dp"><div class="dp-h">${part}${(L => L.length > 1 ? `<button class="dp-all" onclick="window.tickAll&&tickAll('${L.join(',')}')">모두 먹음</button>` : '')(list.filter(x => !x.done && !x.skip).map(x => x.d.id + '@' + x.t))}</div><div class="dose-list">${list.map(x => `<button class="dose-tick ${x.done ? 'done' : x.skip ? 'skip' : (x.min < nowMin - 60 ? 'late' : '')}" onclick="tick('${x.d.id}','${x.t}')" aria-pressed="${x.done}"><span class="bx">${x.done ? I.check : x.skip ? '–' : ''}</span><span class="n"><b>${esc(x.d.name)}</b><small>${x.done ? '<b>먹음</b> · ' : x.skip ? '' : '아직 · '}<span class="t">${x.t}</span> · ${x.skip ? '건너뛰었어요 — 드셨으면 눌러 주세요' : fmt((x.d.simple || '').split('.')[0])}</small></span></button>`).join('')}</div></div>`).join('')}${todays.length && todays.every(x => x.done) ? `<div class="care ok" style="margin-top:12px"><div class="hd">${I.check}오늘 약 다 드셨어요 · 수고하셨어요</div><div class="bd"><button class="btn line" style="width:100%;min-height:48px" onclick="sendCare()">${I.family} 보호자에게 오늘 상태 보내기</button></div></div>` : ''}${lateL.length ? `<details class="why-more" style="margin-top:10px"><summary>드셨는지 기억이 안 나요${I.chev}</summary><div class="why" style="margin-top:6px"><p>확실하지 않으면 <b>이번 회는 건너뛰고</b> 다음 시간부터 원래대로 드세요. 대부분의 약은 <b>두 번 드시는 쪽이 더 위험</b>해요. 피임약·항생제처럼 놓치면 곤란한 약은 약사에게 물어보세요. 앞으로는 드시자마자 위 칸을 눌러 두시면 헷갈리지 않아요.</p>
    <p style="margin-top:8px">건너뛰기로 하셨으면 눌러 두세요 — <b>못 드신 것과 따로</b> 적어서 진료 때 구분돼요.</p><div class="skip-l">${lateL.map(x => `<button type="button" class="btn line" onclick="skipDose('${x.d.id}','${x.t}')">${esc(hourWord(x.t))} ${esc(x.d.name)} — 건너뛰기</button>`).join('')}</div></div></details>` : ''}</section>` : ''}
  ${taking.filter(d => isPrn(d.id)).length ? `<section class="sec card"><h2>필요할 때 드신 약</h2>
    <p class="small muted" style="margin-top:4px">아플 때만 드시는 약은 드실 때마다 눌러 적어 두세요. <b>다음은 몇 시부터</b>인지, 오늘 몇 번째인지 알려 드려요.</p>
    ${taking.filter(d => isPrn(d.id)).map(d => { const st = prnState(d); return `<div class="sched-row prn-row"><div class="nm"><span>${esc(d.name)}</span>${st.count ? `<b class="${st.full ? 'stockwarn' : 'stockok'}">오늘 ${st.count}번${st.max ? ` / ${st.max}번` : ''}</b>` : ''}</div>${painBadge(d) ? `<div class="pain-row">${painBadge(d)}</div>` : ''}
      <div class="small" style="margin-top:4px">${st.last ? `마지막 <b>${hhmm(st.last)}</b>${st.last.getDate() !== new Date().getDate() ? '(어제)' : ''}` : '오늘은 아직 안 드셨어요'}${st.early ? ` · <b>${hhmm(st.next)}부터</b> 다시 드실 수 있어요` : ''}${st.gap ? `<span class="muted"> · ${st.gap}시간 간격${st.max ? `, 하루 ${st.max}번까지` : ''}</span>` : ''}</div>
      ${st.full ? `<div class="note" style="margin-top:8px">${I.alert}<span><b>오늘 드실 만큼 드셨어요.</b> 더 아프시면 더 드시기보다 약사·의사와 상의하세요.</span></div>` : ''}
      <div class="prn-qty" role="group" aria-label="한 번에 몇 알"><span>한 번에</span>${[1, 2].map(k => `<button class="${prnQty(d.id) === k ? 'on' : ''}" aria-pressed="${prnQty(d.id) === k}" onclick="setPrnQty('${d.id}',${k})">${k}알</button>`).join('')}</div>
      <div class="actions" style="margin-top:8px"><button class="btn ${st.early || st.full ? 'ghost' : ''}" onclick="prnTook('${d.id}')">${I.check} ${kidFever(d.id) ? `지금 먹였어요${kidPrnMl(d.id) ? ' (' + kidPrnMl(d.id) + ')' : ''}` : `지금 먹었어요 (${prnQty(d.id)}알)`}</button></div>${st.count ? `<button class="prn-undo" onclick="prnUndo('${d.id}')">잘못 눌렀어요 — 방금 적은 것 지우기</button>` : ''}</div>`; }).join('')}
  </section>` : ''}
  ${taking.length ? schTabs(q) : ''}
  ${taking.length ? `<div class="pane${schOn('sc1')}" id="sc1"><section class="sec card" style="margin-top:8px"><h2>약마다 시간 고르기</h2>${taking.map(d => `<div class="sched-row"><div class="nm"><span>${esc(d.name)}</span>${d.d ? `<a class="link small" href="#/drug/${d.d.id}">복용법 ›</a>` : ''}</div><div class="small muted">${fmt((d.simple || '').split('.')[0])}</div><div class="times">${isPrn(d.id) ? '' : SLOTS.map(([n, t]) => `<button class="chip ${schedOf(d.id, d).includes(t) ? 'on' : ''}" aria-pressed="${schedOf(d.id, d).includes(t)}" onclick="toggleSlot('${d.id}','${t}')">${schedOf(d.id, d).includes(t) ? I.check : ''}${n} ${t}</button>`).join('')
      + schedOf(d.id, d).filter(t => !SLOTS.some(x => x[1] === t)).map(t => `<button class="chip on" aria-pressed="true" aria-label="${t} 빼기" onclick="toggleSlot('${d.id}','${t}')">${I.check}${t}</button>`).join('')
      + `<button type="button" class="chip" aria-expanded="false" onclick="const f=this.nextElementSibling;f.classList.toggle('hide');this.setAttribute('aria-expanded',!f.classList.contains('hide'))">${I.clock}직접 시각</button><span class="tadd-f hide"><input type="time" value="07:00" aria-label="${esc(d.name)} 알림 시각"><button type="button" class="chip" onclick="addSlot('${d.id}', this.previousElementSibling.value)">넣기</button></span>`}<button class="chip ${isPrn(d.id) ? 'on' : ''}" onclick="togglePrn('${d.id}')" aria-pressed="${isPrn(d.id)}">${isPrn(d.id) ? I.check : ''}필요할 때만</button></div>${isPrn(d.id) ? `<p class="small muted" style="margin-top:6px">시간 알림 없이, 드실 때마다 위의 <b>「필요할 때 드신 약」</b>에 적어요.</p>` : schedUnset(d) ? (() => { const sug = defaultSlots(d); return `<div class="sched-ask"><p class="small"><b>아직 시간을 정하지 않았어요.</b> 매일 정해진 시간에 드시면 위에서 시각을 누르시고, 아플 때만 드시면 「필요할 때만」을 누르세요.</p>${sug.length ? `<p class="small muted" style="margin-top:4px">제안(설명서·안내 간격): ${sug.map(t => esc((SLOT_WORD[t] ? SLOT_WORD[t] + ' ' : '') + t)).join(' · ')}</p><button type="button" class="btn line" style="margin-top:8px" onclick="schedConfirm('${d.id}')">${I.check} 매일 — 이 시간으로 정하기</button>` : ''}</div>`; })() : schedWarn(d)}</div>`).join('')}</section></div>
  ${taking.length ? `<div class="pane${schOn('sc5')}" id="sc5"><section class="sec card" style="margin-top:8px"><h2>보호자에게 오늘 상황 보내기</h2>
    <p class="small" style="margin-top:6px">오늘 무엇을 드셨고 무엇이 남았는지 한 장으로 만들어, 카카오톡·문자 보내기 창을 바로 열어 드려요.</p>
    <div class="actions"><button class="btn" onclick="sendCare()">${I.family} 부모님께 오늘 상태 보내기</button></div>
    <p class="small muted" style="margin-top:6px">이 앱이 대신 보내지 않아요 · ${savedWhere()}</p>
    <details class="why-more" style="margin-top:10px"><summary>무엇이 보내지나요${I.chev}</summary><p class="why" style="margin-top:6px">${esc(careReport())}</p></details>
  </section></div>
  <div class="pane${schOn('sc2')}" id="sc2"><section class="sec card" style="margin-top:8px"><h2>약이 며칠 남았나요</h2>
    <p class="small" style="margin-top:6px">남은 알 수를 넣어 두시면 <b>떨어지기 전에</b> 알려드려요. 주말·연휴 전에 미리 받아 두시라고요.</p>
    ${taking.map(d => { const dl = daysLeft(d.id), pl = prnLeft(d.id); return `<div class="sched-row"><div class="nm"><span>${esc(d.name)}</span>${dl != null ? `<b class="${dl <= 3 ? 'stockwarn' : 'stockok'}">${dl === 0 ? '오늘 떨어져요' : dl + '일치 남음'}</b>` : ''}${pl != null ? `<b class="${pl <= 3 ? 'stockwarn' : 'stockok'}">${pl === 0 ? '다 드셨어요' : pl + '번 분 남음'}</b>` : ''}</div>
      <div class="times stock-row"><input class="stock" type="number" inputmode="numeric" min="0" step="1" placeholder="남은 알 수" value="${stockOf(d.id) ? esc(String(stockOf(d.id).left)) : ''}" onchange="setStock('${d.id}', this.value)" aria-label="${esc(d.name)} 남은 알 수"><span class="stock-u" aria-hidden="true">알</span></div>
      ${isPrn(d.id) ? '' : `<div class="prn-qty" role="group" aria-label="${esc(d.name)} 한 번에 몇 알"><span>한 번에</span>${[1, 2].map(k => `<button class="${doseQty(d.id) === k ? 'on' : ''}" aria-pressed="${doseQty(d.id) === k}" onclick="setDoseQty('${d.id}',${k})">${k}알</button>`).join('')}</div>`}</div>`; }).join('')}
    ${잠김('refill') ? `<button class="btn line" style="margin-top:10px" onclick="구독.막힘('refill')">${I.clock} 떨어지기 전 알림은 이용권으로 받아요${I.chev}</button>` : ''}
    ${lowStock().length ? `<div class="note" style="margin-top:10px">${I.alert}<span><b>곧 떨어져요</b> — ${lowStock().map(x => esc(x.n) + ' ' + x.days + '일치').join(' · ')}. 처방약이면 <b>미리 진료를 잡아 두세요.</b> <a class="link" href="#/visits">진료 예약 적기</a></span></div>` : ''}
  </section></div>` : ''}
  ${taking.length ? `<div class="pane${schOn('sc3')}" id="sc3">${calCard()}</div>` : ''}
  ${taking.length ? `<div class="pane${schOn('sc4')}" id="sc4">` : ''}${NATIVE ? `<section class="sec card"><h2>알림 방법</h2>
    <div class="toggle"><div class="t"><b>휴대폰 알림</b><span>${NATIVE_PERM === 'granted' ? '켜져 있어요 — 앱을 닫아도, 휴대폰을 껐다 켜도 울려요' : NATIVE_PERM === 'denied' ? '꺼져 있어요 — 휴대폰 설정 → 앱 → 약지도 → 알림' : '허용하면 시간에 맞춰 알려드려요'}</span></div><button class="btn ghost" style="width:auto;min-height:46px;padding:0 14px" onclick="askNativeNoti()">${NATIVE_PERM === 'granted' ? '켜짐' : '켜기'}</button></div>
    ${NATIVE_PERM === 'granted' && NATIVE_EXACT !== 'granted' ? `<div class="toggle"><div class="t"><b>정확한 시각에 울리기</b><span>지금은 휴대폰이 몇 분 늦게 울릴 수 있어요. 「알람 및 리마인더」를 허용해 주세요</span></div><button class="btn ghost" style="width:auto;min-height:46px;padding:0 14px" onclick="askExact()">허용</button></div>` : ''}
    ${noteNameRow()}${noteMore()}
    <p class="small muted" style="margin-top:10px">알림의 <b>「먹었어요」</b>를 누르면 약지도가 열리며 바로 체크돼요. <b>「10분 뒤 다시」</b>·<b>「건너뛰기」</b>도 있어요. 30분이 지나도 체크가 없으면 <b>한 번만 더</b> 알려 드려요. 알림은 앞으로 며칠치를 미리 걸어 두고, 앱을 여실 때마다 이어서 다시 걸어요.</p>
    <details class="why-more" style="margin-top:10px" ${NOTE_HELP ? 'open' : ''}><summary>알림이 늦거나 안 와요${I.chev}</summary><div class="why" style="margin-top:6px">
      <button type="button" class="btn line" style="margin:4px 0 10px" onclick="testNote()">${I.clock} 시험 알림 보내기</button>
      ${NOTE_HELP && NATIVE_PERM !== 'granted' ? `<p class="note soft" style="margin-bottom:8px">${I.info}<span>알림이 꺼져 있어요. <b>휴대폰 설정 → 앱 → 약지도 → 알림</b>에서 「알림 허용」을 켜 주세요. 그다음 다시 눌러 보세요.</span></p>` : ''}
      <p>휴대폰이 전기를 아끼려고 오래 안 연 앱의 알림을 늦추거나 막을 수 있어요. 한 번만 바꿔 두시면 돼요.</p>
      <p style="margin-top:6px"><b>삼성 갤럭시</b> — 설정 → 배터리 → 백그라운드 사용 제한 → 「절전 안 함 앱」에 약지도를 넣어 주세요. 「절전 앱」·「깊은 절전 앱」 목록에 있으면 빼 주세요.</p>
      <p style="margin-top:6px"><b>그 밖의 휴대폰</b> — 설정 → 앱 → 약지도 → 배터리 → 「제한 없음」(또는 「최적화하지 않음」)으로 바꿔 주세요.</p>
      <p style="margin-top:6px"><b>정확한 시각</b> — 설정 → 앱 → 약지도 → 「알람 및 리마인더」를 허용해 두시면 몇 분씩 늦지 않아요. 허용하지 않으셔도 알림은 와요 — 몇 분 늦을 수 있을 뿐이에요. 이 권한으로 모으는 정보는 없어요.</p>
      <p style="margin-top:6px">앱 정보에서 <b>「강제 중지」</b>를 누르시면 걸어 둔 알림이 모두 지워져요. 그랬다면 약지도를 한 번 열어 주세요 — 다시 걸려요.</p>
    </div></details>
  </section>` : `<section class="sec card"><h2>알림 방법</h2>
    <div class="toggle"><div class="t"><b>휴대폰 달력에 매일 알림 넣기 · 추천</b><span>앱을 닫아도 울려요. 파일을 열면 달력이 등록해요</span></div><button class="btn ghost" style="width:auto;min-height:46px;padding:0 14px" onclick="downloadIcs()">${I.clock} 받기</button></div>
    <div class="toggle"><div class="t"><b>앱이 열려 있을 때 알림</b><span>${perm === 'granted' ? '켜져 있어요' : perm === 'denied' ? '브라우저 설정에서 차단됨' : perm === 'unsupported' ? '이 브라우저는 지원하지 않아요' : '허용하면 시간에 맞춰 알려드려요'}</span></div><button class="btn ghost" style="width:auto;min-height:46px;padding:0 14px" onclick="askNoti()">${perm === 'granted' ? '켜짐' : '켜기'}</button></div>
    ${noteNameRow()}${noteMore()}
    <p class="small muted" style="margin-top:10px">알림의 <b>「먹었어요」</b>를 누르면 바로 체크돼요. <b>「10분 뒤 다시」</b>도 있어요. 30분이 지나도 체크가 없으면 <b>한 번만 더</b> 알려 드려요. 앱을 완전히 닫아 두시면 울리지 않으니, 그럴 땐 <b>달력 알림</b>을 함께 켜 두세요.</p>
    <details class="why-more" style="margin-top:10px" ${NOTE_HELP ? 'open' : ''}><summary>알림이 늦거나 안 와요${I.chev}</summary><div class="why" style="margin-top:6px">
      <button type="button" class="btn line" style="margin:4px 0 10px" onclick="testNote()">${I.clock} 시험 알림 보내기</button>
      ${NOTE_HELP && perm !== 'granted' ? `<p class="note soft" style="margin-bottom:8px">${I.info}<span>${perm === 'unsupported' ? '이 브라우저는 알림을 지원하지 않아요. 위의 <b>「휴대폰 달력에 매일 알림 넣기」</b>를 써 주세요.' : '알림이 막혀 있어요. 주소창 왼쪽의 <b>자물쇠(또는 설정) 표시 → 사이트 설정 → 알림 → 허용</b>으로 바꾼 뒤 다시 눌러 주세요.'}</span></p>` : ''}
      <p>웹에서는 <b>약지도 창이 열려 있을 때만</b> 알림이 울려요. 창을 닫거나 오래 다른 앱을 쓰면 늦거나 안 올 수 있어요.</p>
      <p style="margin-top:6px">휴대폰이 <b>무음·방해 금지 모드</b>면 소리 없이 와요. 확실하게 받으시려면 <b>휴대폰 달력에 매일 알림 넣기</b>나 설치한 약지도 앱을 써 주세요.</p>
    </div></details>
  </section>`}${taking.length ? '</div>' : ''}` : ''}
  ${fold(`${I.info}약을 깜빡했을 때`, `<p class="why">많은 약의 설명서는 이렇게 적고 있어요 — <b>생각난 즉시 드시고, 다음 드실 때가 가까우면 잊은 것은 건너뛰고 다음 때 한 번 몫만</b> 드세요. <b>두 번 몫을 한꺼번에 드시지 마세요.</b></p><p class="why" style="margin-top:6px">피임약·피 묽게 하는 약(와파린 등)·골다공증 약·당뇨 주사처럼 약마다 따로 정해진 방법이 있는 약이 있어요. 그런 약은 약봉투 설명서와 약사·의사 안내를 따르세요. 자주 잊으시면 알림 시각을 식사·양치 같은 습관에 맞춰 보세요.</p>`, { cls:'miss-fold' })}
  ${disclaimer('알림은 잊지 않도록 돕는 도구예요. 용량·간격은 약 상자와 약사·의사 지시가 우선이에요.')}`;
};
window.vDrugFull = function (id, q = {}){
  const d0 = drug(id); if (!d0) return vDrugs('', {});
  if (svOn(q)) return vDrugS(d0, q);
  const d = pView(d0, q.p), c = cls(d.class);
  const same = (D.drugs || []).filter(x => x.class === d.class && x.id !== d.id);
  /* 아직 안 왔으면 받아 두고, 오면 다시 그린다 */
  if (!PUB.index) pubIndexSoon();
  const pub = (PUB.index || []).filter(p => (p.map || []).includes(d.id));
  const pubHtml = pub.length ? `<h3 style="margin-top:20px">식약처 등록 제품 <small class="muted" style="font-weight:500">${pub.length}개 · e약은요 공공데이터${pub.length > 30 ? ' · 30개만 표시' : ''}</small></h3>${(() => { const rowP = p => `<button class="row" onclick="go('/pub/${p.id}')">${pubThumb(p)}<div class="body"><b>${esc(p.n)}</b><span>${esc(p.m)}${p.map.length > 1 ? ' · 복합제(' + p.map.length + '성분)' : ''}</span></div>${p.cvs ? '<span class="badge cvs">편의점</span>' : ''}${I.chev}</button>`;
    const L = pub.slice(0, 30); return `<div class="rows">${L.slice(0, 5).map(rowP).join('')}</div>${L.length > 5 ? `<details class="more-rows"><summary>제품 더 보기 <span class="muted">${L.length - 5}개</span>${I.chev}</summary><div class="rows">${L.slice(5).map(rowP).join('')}</div></details>` : ''}`; })()}` : (PUB.index ? '' : '<p class="loading">식약처 제품 목록을 불러오는 중…</p>');
  /* 제품 머리가 이 약 이름과 같으면(게보린정 → 게보린정) 아래 제목·대표 제품 줄은 겹친다 — 갈래 링크만 남긴다(10-14) */
  /* 복합제 항목은 이름이 곧 제품 이름 */
  const top = prodTop(d, q.p), dupTop = !!top && (d.contains || []).length > 0;
  return `${topBar({ back:'약 사전', unreviewed:d.reviewed === false })}${top}
  <div class="drug-hero">${c ? `<a class="cls link" href="#/class/${c.id}">${esc(c.name)} ›</a>` : ''}${dupTop ? '' : `<h1>${esc(d.name)}</h1>`}
    ${(() => { /* 3-3 ① 대표 제품을 제목 아래(NHS) */
      const P = (d.products || []).slice(0, 3); if (!P.length || dupTop) return '';
      /* 4차 뒤 자체 대조 — 단일 성분 약에 복합제(우루사 옆 「베아제·훼스탈 등 소화제」)를 같은 줄로 두면 같은 약으로 읽힌다. 복합제는 따로 부른다 */
      const mix = x => !(d.contains || []).length && !d.prodMix && !/단일제/.test(x.name) && (/복합|소화제/.test(x.name + ' ' + (x.amount || '')) || MIXBRAND.test(x.name)), S = P.filter(x => !mix(x)), M = P.filter(mix);
      if (!/^ko/.test(document.documentElement.lang || 'ko')) return `<button class="rep-line" onclick="jumpTab('p3')"><span>한국 제품 이름 보기</span>${I.chev}</button>`;   /* 11-09 C3 해외 말 — 한국 상품명은 접는다(성분명이 먼저) */
      return `<button class="rep-line" onclick="jumpTab('p3')"><span>${S.length ? `대표 제품 <b>${esc(S[0].name)}</b>${S.length > 1 ? ` · 그 밖에 ${esc(S.slice(1).map(x => x.name).join(', '))}` : ''}` : ''}${M.length ? `${S.length ? ' · ' : ''}이 성분이 든 복합제 ${S.length ? esc(M.map(x => x.name).join(', ')) : `<b>${esc(M.map(x => x.name).join(', '))}</b>`}` : ''}</span>${I.chev}</button>`; })()}
    <div class="en">${rxMix(d) && /^ko/.test(document.documentElement.lang || 'ko') ? `<span class="small">${esc(rxMix(d))}</span>` : badge(d.rx)}${d.ach ? `<span class="badge ${d.ach >= 3 ? 'stop' : d.ach === 2 ? 'warn' : ''}" style="margin-left:4px">항콜린 ${esc(ACH_WORD[d.ach])}</span>` : ''}</div>
    <div class="hero-speak">${speakBtn(`drugSpeech(pView(drug('${d.id}'), ${d.pSel ? `'${esc(d.pSel.name).replace(/'/g, '')}'` : 'null'}))`, (d.pSel?.name || d.name) + ' 읽어 주기')}</div></div>
  ${allergyWarn(d)}
  ${ixLine([d])}
  ${d.useNote ? `<div class="usebar">${I.alert}<span>${fmt(d.useNote)}</span></div>` : ''}
  ${meSummary(d)}
  ${d.kidSel ? `<div class="dose-hero"><small>먹는 양</small><div class="sv-dose">${esc(KIDDOSE)}</div></div>${kidDoseBtn(d)}` : d.dose ? (() => { const mx = d.dose.max || '설명서의 하루 최대량을 따르세요'; const rule = /세요|따르|달라져|줄이/.test(mx);
    /* 3-3 ③ — 큰 숫자는 알 수(「1~2정」), mg·간격·하루 최대는 그 아래 17 px. 용량 글은 그대로 두고 알 수만 크게 뽑는다(정해진 꼴일 때만) */
    const pc = isOral(d) && String(d.dose.adult || '').match(/^[\d,~.\s]*(?:mg|g|mL)?\s*\(?\s*(?:[\d,.]+\s*(?:mg|g|mL)\s*)?(\d+(?:\s*~\s*\d+)?)\s*(정|캡슐|알|포)\)?$/);
    /* 파스·연고는 「하루 최대 몇 개」가 없다 — 그럴 땐 그 말을 붙이지 않는다 */
    /* 11-10 디자인 검수 B3 — 1회·하루 최대는 굵은 한 줄, 간격은 회색 한 줄, 숫자+단위는 끊지 않는다 */
    const nb = t => String(t).replace(/(\d[\d,.~]*)\s(mg|g|mL|정|캡슐|알|포|시간|번|회)/g, '$1\u00a0$2');
    const [m0, ...mR] = String(mx).split(' · '), senA = ME.age === 'senior' && d.id === 'acetaminophen' && !/서방|이알/.test(q?.p || '');   /* 11-12 서방정(650 mg)은 그 제품 하루 최대 */
    const meta = `<b class="dl-m">${nb([pc ? fmt(d.dose.adult) : '', senA ? '하루 최대 6정(3,000 mg) — 65세 이상' : maxLine(m0, rule)].filter(Boolean).join(' · '))}</b>${d.dose.interval ? `<span class="dl-i">${/하루|식후|식전|취침|자기 전/.test(d.dose.interval) ? '먹는 때' : '간격'} ${nb(fmt(d.dose.interval))}</span>` : ''}${senA || mR.length ? `<details class="dl-more"><summary>${senA ? '설명서 최대' : '더 보기'}${I.chev}</summary>${nb(senA ? fmt(m0) : fmt(mR.join(' · ')))}</details>` : ''}`;
    return `<div class="dose-hero"><small>${isOral(d) ? '성인 1회 용량' : '쓰는 양'}</small><div class="big${pc ? ' pc' : ''}">${pc ? esc(pc[1].replace(/\s/g, '') + pc[2]) : fmt(d.dose.adult || '')}</div><small class="dl">${meta}</small>${d.dose.child ? `<small style="margin-top:6px">소아: ${fmt(d.dose.child)}</small>` : ''}</div>`; })() : ''}
  ${d.dose && !d.kidSel ? `<p class="small muted dose-src">식약처 허가 · 확인한 날 ${esc(D.meta?.labelCheck || '')}</p>` : ''}
  ${leadHtml(d.lead, 'margin-top:12px')}
  ${otcAltCard(d)}
  ${d.ach ? `<div class="usebar" style="${d.ach >= 2 ? '' : 'background:var(--tint2);color:var(--body)'}">${d.ach >= 2 ? I.alert : I.info}<span><b>항콜린 부담 ${esc(ACH_WORD[d.ach])}</b> — ${esc(d.achNote || '')}${d.achAlt ? '<br>' + fmt(d.achAlt) : ''}</span></div>` : ''}
  ${aeRemind(d)}
  
  ${picts(d.pict)}
  ${(() => { const pr = (d.products || []).find(x => pimg(x.name)); return pr ? `<div class="drug-photo">${imgTag(pimg(pr.name), '', pr.name)}<div><b>${esc(pr.name)}</b><small>${esc(pr.maker || '')} · ${esc(pr.amount || '')}</small><small style="display:block;margin-top:2px">사진: 식약처 낱알식별</small></div></div>` : ''; })()}
  ${(() => {
    /* 값이 없는 칸에 「— · —」 를 남기지 않는다 — 빈 상자는 「자료가 없는 앱」으로 읽힌다 */
    const cells = [];
    if ((d.for || []).length) cells.push(`<div><small>이런 때</small><b>${esc(d.for.join(', '))}</b></div>`);
    /* 자료에 「—」 한 글자로 적힌 곳이 있다 */
    const real = v => v && !/^[\s—–-]+$/.test(v);
    if (real(d.onset) || real(d.duration)) cells.push(`<div><small>효과 시작·지속</small><b>${esc([d.onset, d.duration].filter(real).join(' · '))}</b></div>`);
    return cells.length ? `<div class="kv"${cells.length === 1 ? ' style="grid-template-columns:1fr"' : ''}>${cells.join('')}</div>` : '';
  })()}
  ${APAP_FIRST.has(d.id) ? `<div class="rows-l" style="margin-top:12px">${lrow(I.shield, `위가 약하거나 ${ME.age === 'senior' ? '<b>65세 이상이시면</b>' : '65세 이상이면'} — 아세트아미노펜을 먼저`, '위·콩팥 부담이 적어요. 그래도 안 들으면 그때 소염제를', "go('/drug/acetaminophen')")}</div>` : ''}
  ${KID_DRUG.has(d.id) && ME.age !== 'child' ? `<div class="kid-line">${I.user}<span>위 용량은 <b>어른 기준</b>이에요. 어린이는 몸무게로 따로 정해요 — <a class="link" href="#/kids">아이 약 용량 계산 ›</a></span></div>` : ''}
  ${(() => {
    /* 2026-09-29 — ClinicScore 문법: 아래로 이어 붙던 「같은 계열」·출처 7개도 탭 안으로. 한 번에 한 칸만 */
    const T = [['p1', '복용법'], ['p2', '주의·부작용'], ['p4', '같이 먹으면', (d.interactions || []).length], ['p3', '제품', (d.products || []).length], ...(same.length ? [['p5', '같은 계열', same.length]] : []), ...((d.sources || []).length ? [['p6', '근거', d.sources.length]] : [])];
    return `<div class="rows-l" style="margin-top:14px">${lrow((ME.taking || []).includes(d.id) ? I.check : I.pill, (ME.taking || []).includes(d.id) ? '내 약통에 있어요' : '내 약통에 담기', (ME.taking || []).includes(d.id) ? '누르면 빼요' : '겹치는 성분·복용 알림을 챙겨 드려요', `toggleTaking('${d.id}')`)}</div>
  <nav class="tabs dtabs" role="tablist" aria-label="약 정보">${T.map(([k, n, c], i) => `<button class="tab ${i ? '' : 'on'}" role="tab" data-p="${k}">${n}${c ? `<span class="n">${c}</span>` : ''}</button>`).join('')}</nav>`; })()}
  <div class="pane on" id="p1"><section class="card">
    ${d.simple ? `<div class="dose-hero" style="margin-top:0;margin-bottom:16px"><small>간단히 — 약국 구입 기준</small><div style="font-size:1.0625rem;font-weight:700;line-height:1.5;margin-top:4px">${fmt(d.simple)}</div></div>` : ''}
    ${d.how?.length ? `<h2>알아 두실 것</h2>${list(d.how)}` : ''}
    ${d.tips?.length ? `<h2${d.how?.length ? ' style="margin-top:20px"' : ''}>${isOral(d) ? '어떻게 먹나요?' : '어떻게 쓰나요?'}</h2>${list(d.tips)}` : ''}
    ${(() => { const F = (d.faq || []).filter(x => !d.kidSel || !/\d\s*(~\s*\d+\s*)?(정|알|캡슐)/.test((x.q || '') + ' ' + (x.a || ''))); return F.length ? `<h2 style="margin-top:20px">자주 묻는 질문</h2>${faqList(F)}` : ''; })()}
    ${keepToss(d)}
  </section></div>
  <div class="pane" id="p2"><section class="card">
    ${d.risk ? `<h2>부담 정도 <small class="muted" style="font-weight:500;font-size:.875rem">같은 계열 안에서 상대 비교</small></h2><div class="risk-bars">${riskBar('위장', d.risk.gi, d.riskNote?.gi)}${riskBar('심혈관', d.risk.cv, d.riskNote?.cv)}${riskBar('신장', d.risk.renal, d.riskNote?.renal)}${riskBar('간', d.risk.liver, d.riskNote?.liver)}</div>` : ''}
    ${d.pregnancy || d.children || d.lact ? `<div class="kv" style="grid-template-columns:1fr">${d.pregnancy ? `<div><small>${d.lact || !/수유|젖/.test(d.pregnancy) ? '임신' : '임신·수유'}</small><b>${fmt(d.pregnancy)}</b></div>` : ''}${lactCell(d)}${d.children ? `<div><small>소아</small><b>${fmt(d.children)}</b></div>` : ''}</div>` : ''}
    ${d.risk || d.pregnancy || d.children || d.lact ? '<div style="height:20px"></div>' : ''}
    ${d.avoid?.length ? `<h2>${isOral(d) ? '누가 먹으면 안 되나요?' : '누가 쓰면 안 되나요?'}</h2>${list(d.avoid.map(a => a.text || a), 'plain x')}` : ''}
    ${d.caution?.length ? `<h2 style="margin-top:20px">누가 먼저 상의해야 하나요?</h2>${list(d.caution.map(a => a.text || a))}` : ''}
    ${sideFreqHtml(d)}
    ${d.sideEffects?.length ? `<h2 style="margin-top:20px">${d.sideFreq ? '알아 두실 것' : '흔한 부작용'}</h2>${list(d.sideEffects)}` : ''}
    ${d.stop?.length ? `<div style="margin-top:20px">${flagBox('이런 증상이 나타나면 바로 중단하고 진료', d.stop)}</div>` : ''}
    ${missOdCards(d)}
  </section></div>
  <div class="pane" id="p3"><section class="card"><h2>이 성분이 든 제품</h2><p class="small muted" style="margin-top:4px">성분·함량·제형이 같으면 같은 약이에요 — 확실하지 않으면 약사에게 확인하세요.</p>
    <div class="products">${(d.products || []).map(p => `<div class="prod" style="flex-wrap:wrap">${prodArt(pimg(p.name), p.name)}<div style="flex:1 1 7em;min-width:0"><b>${esc(p.name)}</b><span>${esc(p.maker || '')} · ${esc(p.amount || '')}${p.note ? ' · ' + esc(p.note) : ''}</span>${formTag(p.name)}${recallNote(prodSeq(p.name), true, p.name)}</div>${badge(p.rx || d.rx)}<div class="links" style="display:flex;gap:6px;flex-wrap:wrap;width:100%;margin-top:8px">${prodSeq(p.name) ? `<a class="plink" href="https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq=${esc(prodSeq(p.name))}" target="_blank" rel="noopener">${I.link}식약처 허가정보</a>` : ''}<a class="plink" href="https://www.health.kr/searchDrug/search_detail.asp" target="_blank" rel="noopener" onclick="copyName('${esc(p.name.split('·')[0]).replace(/'/g, "\\'")}')">${I.search}약학정보원에서 찾기</a></div></div>`).join('') || '<p class="small muted">대표 제품 정보를 준비 중이에요.</p>'}</div>
    ${pubHtml}${d.en && !(d.sources || []).length ? `<p class="small muted" style="margin-top:12px">영어 이름: ${esc(d.en)}</p>` : ''}
  </section></div>
  <div class="pane" id="p4"><section class="card"><h2>같이 먹으면 안 되거나 조심할 것</h2>
    ${(d.interactions || []).map(x => `<div class="prod" style="margin-top:8px;align-items:flex-start"><div><b>${esc(x.with)}</b><span style="font-size:.875rem;color:var(--body);margin-top:2px">${fmt(x.note || x.what || '')}</span></div>${x.level ? `<span class="badge ${x.level === '금기' ? 'stop' : 'warn'}">${x.level === '금기' ? '같이 안 돼요' : esc(x.level)}</span>` : ''}</div>`).join('') || `<div class="note">${I.info}<span><b>이 약 하나만 보면 특별히 적어 둘 조합이 없습니다.</b> 하지만 <b>「안전하다」는 뜻은 아니에요</b> — 부딪히는 자리는 「드시는 약 전체」를 함께 봐야 보여요.</span></div>
      <div class="actions" style="margin-top:10px"><button class="btn" onclick="go('/together')">${I.scale} 내 약통 전부와 함께 확인하기</button></div>`}
  </section></div>
  ${same.length ? `<div class="pane" id="p5"><section class="sec" style="margin-top:0"><h2>같은 계열 다른 성분 <small>비교해서 고르기</small></h2><div class="card rows">${same.map(x => `<button class="row" onclick="go('/drug/${x.id}')"><div class="body"><b>${esc(x.name)}</b><span>${esc(x.tagline || (x.for || []).join(' · '))}</span>${useTag(x)}</div>${badge(x.rx)}</button>`).join('')}</div>${c ? `<a class="btn ghost" style="margin-top:12px" href="#/class/${c.id}">${I.scale} ${esc(c.name)} 한눈에 비교</a>` : ''}</section></div>` : ''}
  ${(d.sources || []).length ? `<div class="pane" id="p6"><section class="card"><h2>이 화면의 근거 <small>${d.sources.length}건</small></h2>${d.en ? `<p class="small muted" style="margin:4px 0 8px">영어 이름: ${esc(d.en)}</p>` : ''}${srcChips(d.sources, true)}${D.meta?.labelCheck ? `<p class="small muted" style="margin-top:10px">식약처 허가사항 변경명령과 대조한 날: <b>${esc(D.meta.labelCheck)}</b> · 매달 1일 다시 대조해요. 그 사이 바뀐 설명서가 있으면 약 상자 설명서가 우선이에요.</p>` : ''}</section></div>` : ''}
  ${aeDrugCard(d)}
  ${disclaimer()}`;
};
window.vTogetherS = function (){
  pubIngrFill();
  const res = ixRun([]);
  const n = res.items.length;
  /* 3-7 ① — 요약 띠의 세 숫자 = 아래 카드 수 = 머리 문장의 숫자(전에는 머리 「2가지」인데 빨간 카드가 4장이었다) */
  const C = ixCards(res), S = C.filter(c => c.lv === 'stop').length, W = C.filter(c => c.lv === 'warn').length, N = C.length - S - W;
  const ach = achPanel([], { always: true });
  const unk = res.unknown.map(i => i.name);
  /* 항콜린 점수도 '걸리는 것'이다 — 아래 패널이 12점을 띄우는데 위에서 "없어요" 라고 하면 안 된다 */
  const aLv = achLevel(achScore(achList([])));
  const head = !n ? ''
    : S ? `<div class="ix-sum stop">${I.alert}<div><b>안 되는 것이 ${S}가지${W ? `, 조심할 것이 ${W}가지` : ''} 있어요</b><p>아래를 약봉투와 함께 약사님께 보여 드리세요.</p></div></div>`
    : W ? `<div class="ix-sum warn">${I.alert}<div><b>조심할 것이 ${W}가지 있어요</b><p>끊으라는 뜻이 아니라, 한 번 여쭤볼 만하다는 뜻이에요.</p></div></div>`
    : aLv !== 'ok' ? ''
      /* 항콜린만 걸리면 아래 게이지가 말한다 */
    /* 3-16 — 성분을 모르는 약이 섞여 있으면 초록 「안 나왔어요」가 아니라 노랑 「다 보지 못했어요」 */
    /* Z7 A3 — 성분을 모르는 약이 있으면 안심 문장을 쓰지 않는다 — 그 약의 겹침은 볼 수 없다고 분명히 */
    : unk.length ? `<div class="ix-sum warn">${I.info}<div><b>${esc(unk.join(', '))}${josa(unk[unk.length - 1], '은', '는')} 성분을 몰라 겹침을 확인하지 못했어요</b><p>다른 약과 성분이 겹치는지 볼 수 없어요. 상자 뒷면의 <b>성분</b>을 약사에게 보여 주세요.</p></div></div>`
    : N ? `<div class="ix-sum ok">${I.info}<div><b>크게 걸리는 조합은 없어요 — 알아 두실 것이 ${N}가지 있어요</b><p>맨 아래 「알아 두기」를 눌러 보세요. 다만 <b>모든 조합을 담지는 못합니다</b>.</p></div></div>`
    : `<div class="ix-sum ok">${I.check}<div><b>걸리는 조합은 나오지 않았어요</b><p>다만 <b>모든 조합을 담지는 못합니다</b> — 아무것도 안 나온 것이 “안전하다”는 뜻은 아니에요.</p></div></div>`;
  /* 11-10 디자인 검수 B4 — 맨 위 한 줄(약 + 약 → 어디 · 판정), 칸 셋 대신 0 이 아닌 것만 아이콘 칩으로(색만으로 가르지 않는다) */
  const C0 = C.find(c => c.lv === 'stop') || C.find(c => c.lv === 'warn');
  const topL = C0 ? `<p class="ix-top">${esc(C0.items.map(i => i.name).slice(0, 3).join(' + '))} → ${C0.organ?.n ? esc(C0.organ.n) + ' ' : ''}${C0.lv === 'stop' ? '안 돼요' : '조심'}</p>` : '';
  const band = S + W + N ? `<div class="ix-band2" role="group" aria-label="판정 묶음">${[['stop', '안 돼요', S], ['warn', '조심', W], ['info', '알아 두기', N]].filter(x => x[2]).map(([k, w, c]) => `<button class="chip ${k}" onclick="ixJump('${k}')" aria-label="${w} ${c}가지">${k === 'info' ? I.info : I.alert}${w} ${c}</button>`).join('')}</div><p class="small muted ix-scope">이 앱이 아는 규칙 안에서 센 수예요. 0이어도 처음 함께 드시는 약이면 약사에게 한 번 보여 주세요.</p>` : '';
  const grp = lv => C.filter(c => c.lv === lv).map(ixRow).join('');
  return `${topBar({ back: '이전' })}
    <div class="eyebrow">병원에서 받아 온 약</div>
    <h1>같이 먹어도 되나요</h1>
    <p class="ix-lead">내 약통에 담아 두신 약들을 <b>성분</b>으로 풀어서, 서로 부딪히는 자리가 있는지 봐요. 처방약도 함께 봐요.</p>
    ${!n ? `<div class="empty">${emptyArt()}<p><b>아직 담아 두신 약이 없어요.</b><br>약봉투에 적힌 이름이나 약 사진으로 담으시면 바로 봐 드려요.</p>
        <div class="ix-cta"><a class="btn" href="#/photo">${I.eye}약봉투·약 사진으로 담기</a><a class="btn line" href="#/pill">${I.search}이름으로 찾아 담기</a><a class="btn line" href="#/kinds">${I.pill}이름을 모르면 — 종류만 고르기</a></div></div>`
      : `${C0 ? topL + `<p class="ix-sub">${S ? '아래를 약봉투와 함께 약사님께 보여 드리세요.' : '끊으라는 뜻이 아니라, 한 번 여쭤볼 만하다는 뜻이에요.'}</p>` : head}${band}
      <button class="tog-cta" onclick="go('/bag')">${I.eye}<div><b>약사님께 보여드리기</b><span>내 약 목록과 이 판정을 큰 글씨 한 장으로</span></div>${I.chev}</button>
      <div class="ix-list">${res.items.map(it => `<span class="ix-chip ${it.approx || it.est ? 'approx' : it.known ? '' : 'unk'}">${it.link ? `<a href="${it.link}">${esc(it.name)}</a>` : esc(it.name)}${it.approx ? '<em>대략</em>' : !it.known ? '<em>성분 모름</em>' : it.est ? '<em>성분 추정</em>' : ''}</span>`).join('')}</div>
      ${res.items.some(i => i.est && i.known) ? `<p class="ix-unk">${I.info}<span><b>‘성분 추정’</b>은 이름이 같은 다른 제형의 성분으로 본 것이에요. 상자 뒷면 성분과 같은지 확인해 주세요.</span></p>` : ''}
      ${res.items.some(i => i.approx) ? `<p class="ix-unk">${I.info}<span><b>‘대략’</b>으로 담으신 약이 있어요. 종류만 담으면 일부 위험만 먼저 살펴봐요. <b>항콜린 점수처럼 성분마다 다른 것</b>은 이름을 담아야 정확해요. <a class="link" href="#/pill">이름으로 찾아 담기</a></span></p>` : ''}
      ${unk.length && (S || W || N || aLv !== 'ok') ? `<p class="ix-unk">${I.info}<span><b>${esc(unk.join(', '))}</b>${josa(unk[unk.length - 1], '은', '는')} 성분을 몰라 판정에서 빠졌어요 — 이 약의 겹침은 확인하지 못했어요.</span></p>` : ''}
      ${S ? `<h2 class="ix-gh stop" id="ixg-stop">${I.alert}안 돼요<small>${S}가지</small></h2>${grp('stop')}` : ''}
      ${W ? `<h2 class="ix-gh warn" id="ixg-warn">${I.alert}조심<small>${W}가지</small></h2>${grp('warn')}` : ''}
      ${ach}
      ${N ? `<details class="ix-infos" id="ixg-info"><summary>알아 두기<small>${N}가지 · 먼저 알릴 만큼은 아니에요</small>${I.chev}</summary><div class="bd">${grp('info')}</div></details>` : ''}
      <div class="ix-ask">${I.cart}<div><b>약국에서 이렇게 말씀하세요</b>
        <p>“처방약을 드시는 중인데 이거 같이 먹어도 될까요? 약봉투 가져왔어요.”</p>
        <p class="small">약봉투를 보여 드리는 것이 가장 빠르고 정확해요.</p></div></div>`}
    <details class="ix-how"><summary>이 판정은 어떻게 만들어졌나요${I.chev}</summary><div class="bd">
      <p>약국·병원 컴퓨터가 처방할 때 띄우는 <b>병용 점검(식약처 DUR)</b>과 같은 자리를 보되, 환자가 읽을 수 있는 말로 옮긴 것이에요. 성분은 <b>식약처 낱알식별 자료</b>의 성분명과 제품명으로 맞춰 봐요.</p>
      <p><b>담지 못한 것</b> — 모든 약과 모든 조합을 담지는 못해요. 용량·콩팥 기능·먹는 기간에 따라 달라지는 판단도 담지 못해요. 여기서 아무것도 안 나와도 <b>“안전하다”는 뜻이 아니에요</b>.</p>
      <p><b>해 주셨으면 하는 것</b> — 새 처방을 받으실 때 <b>드시는 약을 모두 적은 목록</b>이나 약봉투를 함께 보여 주세요. 그것이 어떤 앱보다 확실해요.</p>
    </div></details>
    ${disclaimer('이 판정은 참고용이에요. 약을 스스로 끊거나 바꾸지 마시고, 걸리는 것이 있으면 약사·의사와 상의하세요.')}`;
};
/* ▲ */
/* ▼ 11-11 다른 앱 입구 — 띠·아이 설명(app-shell 에서 옮김) */
window.KID_TRI = { clinic: '병원에서는 아이가 얼마나 마시고 소변을 보는지, 열과 다른 병의 신호가 있는지 먼저 살펴봐요. 검사나 약은 아이 상태에 따라 필요한 경우에만 써요.',
  pharmacy: '아이 약은 나이와 몸무게에 따라 달라요. 약국에서는 아이 나이(개월 수)와 몸무게를 먼저 말씀하시고 약사와 함께 골라요. 어른 약을 줄여서 먹이지 마세요.',
  escalate: '아이가 축 처지거나, 잘 마시지 못하거나, 소변이 크게 줄면 바로 진료를 받으세요.' };
window.symKS = s => ENTRY?.from !== 'kids' || !s ? s : Object.assign({}, s, { triage: Object.assign({}, KID_TRI, s.kid?.triage || {}), care: s.kid?.care ? Object.assign({}, s.care, s.kid.care) : s.care, lead: s.kid?.lead || s.lead });
window.KID_AGES = [['3개월 전', 2], ['3~5개월', 4], ['6~11개월', 8], ['1세', 12], ['2~4세', 36], ['5~11세', 84], ['12세 넘음', 144]];
window.entryAge = function (m){ if (!ENTRY) return; ENTRY.age = m; try { sessionStorage.setItem('yakjido.entry', JSON.stringify(ENTRY)); } catch (e) {} route(); }
window.entryBandS = function (s){
  if (!ENTRY || !ENTRY_APPS[ENTRY.from]) return ''; const [nm, url] = ENTRY_APPS[ENTRY.from], m = ENTRY.age;
  const back = `<a class="link" href="${url}">${esc(nm)}로 돌아가기 ›</a>`;
  if (ENTRY.from === 'kids') return `<section class="sec entry-band eb-kid"><details><summary><b>${esc(nm)}에서 · ${m != null ? (m >= 24 ? '만 ' + Math.floor(m / 12) + '세' : '생후 ' + m + '개월') + ' 기준' : '아이 기준'}</b>${I.chev}</summary>
    <p class="small" style="margin-top:6px">${m != null ? '설명서상 이 나이에 쓰지 않는 약은 뺐어요.' : '아이 나이를 모르면 나이·몸무게 확인이 필요한 약과 양은 보여 드리지 않아요. 물·전해질 같은 기본 돌봄과 진료 신호는 그대로예요.'} 보호자의 건강정보는 아이에게 적용하지 않았어요. 아이의 알레르기·앓고 있는 병·먹는 약은 따로 확인해 주세요.</p>
    <div class="actions two" style="margin-top:8px"><button class="btn line" onclick="go('/kids')">아이 해열제 양 보기</button><button class="btn line" onclick="entryOff()">어른 기준으로 보기</button></div>${back}</details>
    ${m == null ? `<div class="chips" role="group" aria-label="아이 나이" style="margin-top:8px">${KID_AGES.map(([t, v]) => `<button class="chip" onclick="entryAge(${v})">${t}</button>`).join('')}</div>` : ''}
    ${s && s.id === 'fever' && m != null && m >= 3 && m < 6 ? `<p style="margin-top:8px"><b>생후 ${m}개월 아기가 38도 이상이면 오늘 의료진에게 먼저 연락해 진료 시점을 확인하세요.</b> 해열제 양을 확인하더라도 진료를 미루지 마세요.</p>` : ''}</section>`;   /* 11-11 Main 사진 재검증 — 한 줄로 접어 119 상자가 첫 화면 위쪽에 */
  if (ENTRY.from === 'gildongmu') return `<section class="sec card entry-band"><b>${esc(nm)}에서 오셨어요 — 항암 치료 중이시면 먼저 보세요</b>
    <ul class="plain" style="margin-top:6px"><li><b>38.0도 이상 열이 한 번이라도</b> 나면 해열제로 기다리지 말고 바로 치료받는 병원에 연락하거나 응급실로 가세요. 항암 중 열은 응급이에요.</li>
    <li><b>새 진통제·감기약은 드시기 전에 치료팀에 확인</b>하세요. 아스피린·이부프로펜·나프록센은 출혈 위험을 높일 수 있어요. 혈소판이 낮거나 멍·코피가 늘면 특히요. 심장·뇌혈관 때문에 처방받아 드시는 아스피린은 임의로 끊지 마세요.</li>
    <li>관장약·항문 좌약은 치료팀이 괜찮다고 하기 전에는 쓰지 마세요.</li>
    <li>처음 생긴 증상이나 평소와 다른 증상은 횟수를 기다리지 말고 오늘 치료팀에 알려 주세요.</li></ul>
    ${srcChips(['cdc_chemo_fever', 'idsa_fn2011', 'medline_cancer_bleed', 'nci_bleeding'])}${back}</section>`;
  return `<section class="sec card entry-band"><b>${esc(nm)}에서 오셨어요</b> ${back}</section>`;
}
/* ▲ */
try { if (window.ENTRY && /^#\/(symptom|send)/.test(location.hash)) route(); } catch (e) {}
try { if (/^(#\/?(home)?)?$/.test(location.hash) && (window.오늘한장 || window.필요약줄)) route(); } catch (e) {}   /* 11-12 홈의 오늘 한 장·필요할 때 약 줄은 srv.js 가 온 뒤 다시 그린다 */
try { if (/^#\/(drug\/|schedule|together|od|vitals|pillinfo|pub|supp\/|me|consent|login|notify|sgoal|sstage|doc|hello\/3|supp$|supp\?|sgoal|sstage|rx|about|search|myths|askdoc|talk|p\/|p\?|p$)/.test(location.hash)) route(); } catch (e) {}

