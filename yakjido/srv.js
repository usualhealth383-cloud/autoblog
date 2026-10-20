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
  var LIB = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js';
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
    var a = document.getElementById('srvAge'), g = document.getElementById('srvAgree'), 막 = !!((a && !a.checked) || (g && !g.checked));
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
    h += '<div class="door-seg" role="tablist" aria-label="로그인 또는 회원가입">' + ['login', 'signup'].map(function (k) { var on = (k === 'signup') === 가입;
      return '<button type="button" role="tab" aria-selected="' + on + '"' + (on ? ' class="on"' : '') + ' onclick="계정문탭(\'' + k + '\')">' + (k === 'login' ? '로그인' : '회원가입') + '</button>'; }).join('') + '</div>';
    if (소셜.length) h += '<div class="door-social">' + 소셜.map(function (x, i) { return '<button type="button" onclick="소셜켜짐()[' + i + '].열기()">' + 글자안전(x.n) + '로 계속하기</button>'; }).join('') + '</div><p class="door-or"><span>또는 이메일로</span></p>';
    h += '<label class="door-f" for="srvEmail">이메일</label><input id="srvEmail" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" enterkeyhint="next" value="' + 글자안전(st.email || '') + '">'
      + 비번칸('srvPw', '비밀번호' + (가입 ? ' <small>6자 이상</small>' : ''), 가입 ? 'new-password' : 'current-password', 'go');
    if (가입 && 설정.가입확인) h += '<label class="door-ck"><input id="srvAge" type="checkbox" onchange="this.dataset.at=this.checked?new Date().toISOString():\'\';계정문확인()"><span><b>' + 글자안전(설정.가입확인.글) + ' <em class="door-tag">필수</em></b>' + (설정.가입확인.설명 ? '<small>' + 글자안전(설정.가입확인.설명) + '</small>' : '') + '</span></label>';
    if (!동의됨) h += '<label class="door-ck"><input id="srvAgree" type="checkbox" onchange="계정문확인()"><span><b>「서버에 저장하기」에 동의해요 <em class="door-tag">필수</em></b><small>건강에 관한 민감정보라 따로 여쭤요. 로그인하시면 이 휴대폰의 기록이 계정으로 이어져요.</small></span></label>'
      + '<details class="door-more"><summary>무엇이 올라가나요<svg class="i chev" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></summary><dl>'
      + '<dt>올라가는 것</dt><dd>' + 글자안전(항목.ko || '약지도 기록') + '</dd><dt>어디에</dt><dd>메디나눔 서버(Supabase, 서울)</dd><dt>왜</dt><dd>폰을 바꿔도 이어 보려고</dd>'
      + '<dt>언제까지</dt><dd>계정을 지우실 때까지 — 동의를 거두시면 서버 기록을 바로 지워요</dd></dl><p>동의하지 않으셔도 되고, 동의하지 않아도 약지도는 이 휴대폰에서 그대로 쓰실 수 있어요. 보기 설정과 날씨는 올라가지 않아요.</p></details>';
    var 막힘 = (가입 && !!설정.가입확인) || !동의됨;
    h += 말칸 + '<button type="button" id="srvDoorGo" class="door-go" onclick="계정문동작()"' + (막힘 ? ' disabled aria-describedby="doorWhy"' : '') + '>' + (가입 ? '계정 만들기' : '로그인') + '</button>'
      + (막힘 ? '<p id="doorWhy" class="door-why">필수에 체크하시면 눌려요</p>' : '')
      + (가입 ? '<p class="door-note">계정을 만들면 메일함에 확인 링크가 가요. 한 번 누르면 끝이에요.</p>'
              : '<button type="button" class="srvlink door-forgot" onclick="계정문동작(\'reset\')">비밀번호를 잊으셨나요?</button>');
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

/* ═══ 2026-10-14 약지도 — 첫 동의 · 로그인 문 · 약관 읽기 (현욱님 「이용약관을 체크하지 못하게 돼있잖아」 「회원가입/로그인 화면」) ═══
   첫 화면 예산(index.html 압축 228 KB) 때문에 화면 코드는 여기(따로 받는 파일)에 둔다. index 에는 문지기(consentGate)와 길(#/consent·#/login·#/doc)만.
   본보기: ClinicScore renderConsent(로고·이름·한 줄 → 세 줄 카드 → 모두 동의 → 필수 줄 → 큰 단추 → 발문).
   ⚖️ 들어올 때 받는 동의는 필수 둘(이용약관·개인정보 처리방침)뿐 — 계약 이행에 필요한 처리는 동의가 필요 없고(개인정보 보호법 15조 1항 4호, 2023 개정),
      건강 민감정보는 «모으는 그 순간» 따로 받는다(23조) → 「서버에 저장하기」·만 14세 확인은 계정을 만들 때(로그인 문). 선택 항목·광고 동의는 없다. */
/* 다른 폰의 기록을 받아 오면 다시 그린다(서버.설치의 다시그리기) — 10-14 app-shell 에서 옮김(첫 화면 예산). 함수 선언이라 위 설치 줄보다 먼저 있다 */
function srvReload(){ try { ME = loadMe(localStorage.getItem(ME_KEY)); snapMe(); } catch (e) {} try { armNotifications(); } catch (e) {} try { route(); } catch (e) {} }
/* ── 「서버에 저장하기」 동의 켜기·거두기(설정의 계정 칸) — 10-14 app-shell 에서 옮김(첫 화면 예산). 내용은 그대로 ── */
/* Z4 #22 — 올라가는 것에 아이 정보(부르는 말·생년월일·몸무게)·약 알레르기가 빠져 있었다. 처리방침 1절 표와 같게 */
window.계정항목 = { ko: '드시는 약·복용 시간과 기록·몸 상태(임신·지병 등)·약 알레르기·불편했던 일·혈압 수첩·진료 예약·아이 정보(부르는 말·생년월일·몸무게)', 뒤: ' 목적은 폰을 바꿔도 이어 보기, 보관은 계정을 지우시거나 동의를 거두실 때까지(거두시면 바로 지워요). 건강에 관한 민감정보라 따로 동의를 받고, 동의하지 않으셔도 약지도는 이 폰에서 그대로 쓰실 수 있어요. 보기 설정과 날씨는 올라가지 않아요.' };
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
  ${동의줄('privacy', '개인정보 처리방침', '드시는 약·기록·몸 상태는 기본으로 이 휴대폰에만 저장되고, 광고·분석에 쓰지 않아요. 계정을 만들고 따로 동의하실 때만 메디나눔 서버(서울)에 복사돼요.', [
    '계정 없이 모든 기능을 쓰실 수 있어요.',
    '광고나 이용자 분석 도구를 넣지 않았어요.',
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
    <p class="small muted" style="margin:4px 0 12px">계정 없이도 약지도는 그대로 쓰실 수 있어요. 로그인하시면 기록을 메디나눔 서버(서울)에 복사해 두어 다른 폰에서 이어 받아요.</p>
    ${계정화면HTML()}
    ${srvAgreed() ? `<button type="button" class="srvlink" onclick="서버동의끄기()">「서버에 저장하기」 동의 거두기</button>` : ''}
  </section>`;
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
    <li>${I.check}<span>로그인하지 않아도 약지도는 모두 쓰실 수 있어요</span></li></ul>`}
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
  ${sub ? `<p class="sg-when">${fmt(sub)}</p>` : ''}${x.mfds || x.human || (x.src || []).length ? fold('왜 그런가요', `${x.mfds ? `<p><b>식약처 기능성</b> — ${fmt(x.mfds)}</p>` : ''}${x.human ? `<p style="margin-top:6px"><b>사람 연구</b> — ${fmt(x.human)}</p>` : ''}${srcChips(x.src, true)}`) : ''}</div>`;
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
  ${(g.picks || []).length ? `<section class="sec"><div class="sech"><h2 class="sec-h">챙길 것</h2></div><div class="card rows">${g.picks.map(x => 영양칸({ ...x, human: x.why }, x.dose)).join('')}</div></section>` : ''}
  ${값못함(g.skip)}
  ${(g.check || []).length ? `<section class="sec card"><h2>먼저 확인할 것</h2>${list(g.check)}</section>` : ''}
  ${disclaimer(D.meta?.suppDisclaimer)}`; };
try { const css = document.createElement('style'); css.textContent = `.sg-pick,.sg-skip{padding:12px 0;border-bottom:1px solid var(--hairline)}.sg-pick:last-child,.sg-skip:last-child{border-bottom:0}
.sg-h{display:flex;align-items:center;gap:8px;width:100%;min-height:48px;text-align:left}.sg-h b{flex:1;min-width:0;font-size:1.0625rem;font-weight:800}.sg-h .badge{flex:none}
.sg-when{font-size:.9375rem;color:var(--body);line-height:1.6}.sg-skip p{font-size:.9375rem;color:var(--body);line-height:1.6}`; document.head.appendChild(css); } catch (e) {}

/* 내 정보·동의·로그인·약관 화면을 보고 있었으면 다시 그린다(이 파일이 늦게 오므로) */
try { if (/^#\/(me|consent|login|doc|hello\/3|supp$|supp\?|sgoal|sstage)/.test(location.hash)) route(); } catch (e) {}
