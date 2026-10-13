/* 약지도 — 계정·기록 이어 두기(메디나눔 공용 서버). app-shell.html 뒤에 따로 받는 파일(2026-10-13). */
/* ▼▼ 서버 부품 시작 ▼▼ */
/* 약지도 메디나눔 합류 1013 — 길동무.html(yozm-health, 10-13 정본)의 서버 부품 사본. 바꾼 것: 계정 지우기에 p_app · 결과 문구 · 동의 안내 글 · 버튼 색(약지도 색) · 복구 표시 이름 */
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
  var LIB = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js';
  var 설정 = { app: 'app', 열쇠: /^$/, 다시그리기: null, 준비됨: true };
  var sb = null, 준비중 = null, 세션 = null, 동기화중 = false;
  /* 2026-09-23 검수 #8 — 서버에 표(스키마)가 아직 없으면 앱이 서버.설치({ 준비됨:false }) 로 알린다.
     그동안 계정 칸은 「준비 중」 한 줄뿐 — 가입·로그인·문의 칸과 단추를 보이지 않고, 라이브러리도 받지 않는다(되는 척 금지). */
  function 준비됨() { var r = 설정.준비됨; try { if (typeof r === 'function') r = r(); } catch (e) { r = false; } return r !== false; }
  var 준비중말 = '계정·동기화는 준비 중입니다. 지금은 이 기기에서 그대로 쓰실 수 있습니다.';
  var 복구모드 = false, 복구중 = false;   /* 2026-09-23 큰문제 #10 — 메일의 복구 링크로 들어와 새 비밀번호를 정하는 중 */
  /* 메일 링크가 돌아올 주소 — 지금 앱 주소. file:// 등 웹 주소가 아니면 넘기지 않는다(Supabase Site URL 로 간다). */
  function 앱주소() { try { return /^https?:$/.test(location.protocol) ? location.origin + location.pathname : null; } catch (e) { return null; } }
  function 복구대기() { try { return sessionStorage.getItem('yj_recovery'); } catch (e) { return null; } }
  function 복구처리() {
    if (!준비됨()) return;
    var h = 복구대기(); if (!h || 복구중) return;
    var p = {}; h.split('&').forEach(function (kv) { var i = kv.indexOf('='); if (i > 0) { try { p[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' ')); } catch (e) {} } });
    if (p.error || p.error_code) {
      try { sessionStorage.removeItem('yj_recovery'); } catch (e) {}
      알림('메일의 링크가 만료되었거나 이미 쓰였습니다. 비밀번호를 바꾸려면 「비밀번호 다시 정하기」로 새 링크를 받아 주세요.');
      return;
    }
    if (!p.access_token || !p.refresh_token) { try { sessionStorage.removeItem('yj_recovery'); } catch (e) {} return; }
    if (!서버허용()) { 알림('서버 저장 동의 후 새 비밀번호를 정할 수 있습니다. 내 정보 → 설정 → 계정에서 동의해 주세요.'); return; }
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
      알림('메일의 링크가 만료되었거나 이미 쓰였습니다. 비밀번호를 바꾸려면 「비밀번호 다시 정하기」로 새 링크를 받아 주세요.');
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
      var s = document.createElement('script'); s.src = LIB; s.async = true;
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
      try { 알림('다른 계정으로 들어와서, 이 기기에 있던 이전 계정의 기록은 비웠습니다.'); } catch (e) {}
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
        if (지금 === null || !내바뀜) { try { localStorage.setItem(row.key, v); 해시들[row.key] = 해시(v); 바뀜++; } catch (e) {} return; }
        if (!서버바뀜) return;   /* 내 것만 바뀜 — 밀어올리기가 올린다 */
        var 합친 = 병합(지금, v);
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
  var 알림 = function (t) { try { if (typeof 잠깐말 === 'function') 잠깐말(t); else if (typeof tell === 'function') tell(t, ''); else if (typeof toast === 'function') toast(t); else console.log(t); } catch (e) { console.log(t); } };
  function 말(e) { var m = (e && e.message) || String(e || '');
    if (m === 'off') return 준비중말;
    if (/offline|lib|Failed to fetch|NetworkError/i.test(m)) return '인터넷이 닿지 않습니다. 연결되면 자동으로 이어집니다.';
    if (/Invalid login/i.test(m)) return '이메일이나 비밀번호가 맞지 않습니다.';
    if (/already registered|already exists/i.test(m)) return '이미 가입된 이메일입니다. 로그인해 주세요.';
    if (/Password should be/i.test(m)) return '비밀번호는 6자 이상이어야 합니다.';
    if (/Email not confirmed/i.test(m)) return '메일함의 확인 링크를 먼저 눌러 주세요.';
    if (/rate limit/i.test(m)) return '잠시 뒤에 다시 해 주세요.';
    if (/different from the old/i.test(m)) return '이전과 다른 비밀번호를 써 주세요.';
    return '잠시 문제가 있었습니다. ' + m.slice(0, 60); }

  function 이용권줄() {
    if (!window.구독 || !구독.켜짐()) return '';   /* 2026-09-23 구독 틀 — 유료화 스위치가 꺼져 있으면 체험·요금 글을 보이지 않는다(되는 척 금지) */
    var sv = window.구독상태(); if (!sv) return '';
    var 날 = sv.until ? new Date(sv.until).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' }) : '';
    var t = sv.status === 'active' ? '구독 중' + (sv.plan === 'year' ? ' · 연 결제' : sv.plan === 'month' ? ' · 월 결제' : '') + (날 ? ' · ' + 날 + '까지' : '')
      : (sv.status === 'trial' && sv.열림) ? '체험 중 · ' + sv.days + '일 남음' + (날 ? ' (' + 날 + '까지)' : '')
      : '체험이 끝났습니다 · 결제는 아직 붙기 전이라 요금이 나가지 않습니다';
    return '<div class="srvrow"><b>이용권</b><span>' + t + '</span></div>';
  }
  function 화면갱신() { var el = document.getElementById('srvbox'); if (el) el.outerHTML = window.계정화면HTML(); }

  window.계정화면HTML = function () {
    var st = 상태읽기(), 이메일 = 세션 && 세션.user ? 세션.user.email : '';
    var 시각 = st.last_push || st.last_pull; var 언제 = 시각 ? new Date(시각).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '아직';
    var h = '<div id="srvbox" class="srvbox">';
    if (!준비됨()) return h + '<div class="srvrow"><b>계정·동기화는 준비 중입니다</b><span>지금은 이 기기에서 그대로 쓰실 수 있습니다.</span></div></div>';   /* 검수 #8 */
    if (!서버허용()) {   /* 2026-09-22 — 동의 전·철회 상태: 되는 척 로그인 칸을 보이지 않고, 계정을 만드는 그 자리에서 동의를 받는다 */
      return h + '<p class="srvtiny">계정을 만들거나 로그인하려면 「서버에 저장하기」 동의가 필요해요 — ' + (window.계정항목 ? 계정항목.ko : '') + '이 계정에 묶여 메디나눔 서버(서울)에 저장됩니다.' + (window.계정항목 && 계정항목.뒤 != null ? 계정항목.뒤 : '') + '</p>'
        + '<div class="srvbtns"><button type="button" onclick="if(window.서버동의켜기)서버동의켜기()">동의하고 계속</button></div>'
        + (window.방침주소 ? '<a class="srvlink" href="' + 글자안전(방침주소()) + '#acct"' + (window.Capacitor && Capacitor.isNativePlatform && Capacitor.isNativePlatform() ? ' target="_blank" rel="noopener"' : '') + '>무엇이 올라가는지 자세히</a>' : '') + '</div>';
    }
    if (!이메일 && 복구대기() && !복구중) setTimeout(복구처리, 0);   /* 동의를 막 켠 뒤라면 여기서 이어 간다 */
    if (이메일 && 복구모드) {   /* 2026-09-23 큰문제 #10 — 메일의 복구 링크로 들어왔다 */
      h += '<div class="srvrow"><b>새 비밀번호 정하기</b><span>' + 글자안전(이메일) + ' · 메일의 링크로 들어왔습니다</span></div>'
        + '<input id="srvNewPw" type="password" autocomplete="new-password" enterkeyhint="next" aria-label="새 비밀번호 (6자 이상)" placeholder="새 비밀번호 (6자 이상)">'
        + '<input id="srvNewPw2" type="password" autocomplete="new-password" enterkeyhint="done" aria-label="새 비밀번호 한 번 더" placeholder="새 비밀번호 한 번 더">'
        + '<div class="srvbtns"><button type="button" onclick="계정동작(\'newpw\')">새 비밀번호 저장</button></div>'
        + '<p class="srvtiny">저장하면 이 기기에서 로그인된 채로 이어집니다.</p>';
    }
    if (이메일) {
      h += '<div class="srvrow"><b>' + 이메일 + '</b><span>로그인됨 · 마지막 동기화 ' + 언제 + '</span></div>' + 이용권줄()
        + '<div class="srvbtns"><button type="button" onclick="계정동작(\'sync\')">지금 동기화</button><button type="button" onclick="계정동작(\'logout\')">로그아웃</button></div>'
        + '<p class="srvtiny">기록은 이 기기와 메디나눔 서버(서울)에 함께 있습니다. 폰을 바꿔도 같은 이메일로 로그인하면 이어집니다. 메디나눔의 다른 앱과 계정은 하나지만 기록은 앱마다 따로입니다.</p>'
        + '<button type="button" class="srvlink" onclick="계정동작(\'delete\')">계정 지우기 — 약지도의 서버 기록을 지웁니다</button>';
    } else {
      /* 2026-09-21 — 바로 위 화면 설명이 같은 말을 이미 하고 있었다(한 화면에 두 번). */
      h += '<input id="srvEmail" type="email" inputmode="email" autocomplete="email" enterkeyhint="next" aria-label="이메일" placeholder="이메일" value="' + (st.email || '') + '">'
        + '<input id="srvPw" type="password" autocomplete="current-password" enterkeyhint="go" aria-label="비밀번호 (6자 이상)" placeholder="비밀번호 (6자 이상)">'
        /* 2026-09-23 결정 0923 나 — 가입확인 갈고리: 앱이 넘기면 계정 만들기 앞에 필수 체크를 둔다(체크 전에는 계정 만들기 단추가 막힘). 로그인은 그대로. */
        + (설정.가입확인 ? '<label class="srvage"><input id="srvAge" type="checkbox" onchange="var b=document.getElementById(\'srvSignup\');if(b)b.disabled=!this.checked"><span>' + 글자안전(설정.가입확인.글) + '</span></label>'
            + (설정.가입확인.설명 ? '<p class="srvtiny">' + 글자안전(설정.가입확인.설명) + '</p>' : '') : '')
        + (window.구독 ? 구독.가입동의HTML() : '')   /* 2026-09-23 구독 틀 — 유료화 켜짐일 때만: 체험 뒤 결제 안내 필수 체크 */
        + '<div class="srvbtns"><button type="button" onclick="계정동작(\'login\')">로그인</button><button type="button" id="srvSignup" onclick="계정동작(\'signup\')"' + (설정.가입확인 ? ' disabled' : '') + '>계정 만들기</button></div>'
        + '<p class="srvtiny">계정을 만들면 메일함에 확인 링크가 옵니다. 한 번 누르면 끝입니다. 비밀번호를 잊으면 아래 「비밀번호 다시 정하기」.</p>'
        + '<button type="button" class="srvlink" onclick="계정동작(\'reset\')">비밀번호 다시 정하기</button>';
    }
    /* 2026-10-13 — 문의는 로그인해야 보내진다(답할 곳). 로그인 전엔 칸을 숨긴다 — 바로 아래 「이 앱에 대해」의 메일 주소가 그 자리. */
    if (이메일) h += '<div class="srvask"><b>문의 · 잘못된 내용 알리기</b><textarea id="srvAsk" rows="3" aria-label="문의 · 잘못된 내용 알리기" placeholder="어느 화면의 무엇이 이상한지 적어 주세요. 답은 이메일로 드립니다."></textarea>'
      + '<div class="srvbtns"><button type="button" onclick="계정동작(\'ask\')">보내기</button></div></div>';
    h += '</div>';
    return h;
  };

  var 지우기예약 = 0;   /* 2026-09-22 — 계정 지우기 두 번 누르기 */
  /* 2026-09-22 — 엔터로 로그인. 칸이 <form> 안에 있지 않아 엔터가 아무 데도 닿지 않았다. */
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' || e.isComposing) return;
    var id = e.target && e.target.id;
    if (id === 'srvEmail') { e.preventDefault(); var pw = document.getElementById('srvPw'); if (pw) pw.focus(); }
    else if (id === 'srvPw') { e.preventDefault(); window.계정동작('login'); }
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
    if (!서버허용() && what !== 'logout') { 알림('서버 저장 동의를 철회한 상태입니다. 내 정보 → 설정 → 계정에서 다시 동의하면 계정을 쓸 수 있습니다.'); return; }
    var email = (document.getElementById('srvEmail') || {}).value || '', pw = (document.getElementById('srvPw') || {}).value || '';
    email = email.trim();
    if (what === 'ask') {
      var t = ((document.getElementById('srvAsk') || {}).value || '').trim(); if (!t) { 알림('내용을 적어 주세요.'); return; }
      return 준비().then(function () {
        if (!세션) { 알림('문의는 로그인한 뒤에 보낼 수 있습니다(답을 드릴 곳이 필요합니다).'); return; }
        return sb.from('inquiries').insert({ user_id: 세션.user.id, app: 설정.app, kind: 'ask', text: t, screen: location.hash || '' }).then(function (r) {
          if (r.error) throw r.error; 알림('보냈습니다. 이메일로 답해 드리겠습니다.'); var ta = document.getElementById('srvAsk'); if (ta) ta.value = '';
        });
      }).catch(function (e) { 알림(말(e)); });
    }
    if (what === 'delete') {
      /* 2026-09-22 — 계정 지우기(탈퇴). 서버 함수 delete_own_account 가 본인 행과 계정을 지운다(_시안/계정_지우기.sql). */
      if (!세션) { 알림('먼저 로그인해 주세요.'); return; }
      if (Date.now() - 지우기예약 > 10000) {
        지우기예약 = Date.now();
        알림('약지도의 서버 기록을 지우고, 다른 메디나눔 앱 기록이 없으면 계정까지 지웁니다. 되돌릴 수 없습니다. 10초 안에 「계정 지우기」를 한 번 더 누르면 지웁니다.');
        return;
      }
      지우기예약 = 0;
      return 준비().then(function () { return typeof 설정.지우기전 === 'function' ? Promise.resolve(설정.지우기전(sb, 세션)).catch(function () {}) : null; }).then(function () { return sb.rpc('delete_own_account', { p_app: 설정.app }); }).then(function (r) {
        if (r && r.error) throw r.error;
        try { 내열쇠().forEach(function (k) { localStorage.removeItem(k); }); } catch (e) {}
        try { localStorage.removeItem('_srv_' + 설정.app); localStorage.removeItem(구독키()); } catch (e) {}
        세션 = null; try { sb.auth.signOut(); } catch (e) {}
        알림(r && r.data && r.data.account_deleted === false ? '약지도의 서버 기록과 이 기기의 기록을 지웠습니다. 다른 메디나눔 앱 기록이 남아 있어 계정은 그대로예요.' : '계정과 약지도 서버 기록을 지웠습니다. 이 기기에 있던 약지도 기록도 비웠습니다.');
        화면갱신();
        if (typeof 설정.다시그리기 === 'function') { try { 설정.다시그리기(); } catch (e) {} }
      }).catch(function (e) { 알림(말(e)); });
    }
    if (what === 'newpw') {   /* 2026-09-23 큰문제 #10 — 복구 링크로 들어온 세션에서 새 비밀번호를 저장한다 */
      var n1 = (document.getElementById('srvNewPw') || {}).value || '', n2 = (document.getElementById('srvNewPw2') || {}).value || '';
      if (n1.length < 6) { 알림('비밀번호는 6자 이상이어야 합니다.'); return; }
      if (n1 !== n2) { 알림('두 칸의 비밀번호가 다릅니다.'); return; }
      return 준비().then(function () { if (!세션) throw new Error('login'); return sb.auth.updateUser({ password: n1 }); }).then(function (r) {
        if (r && r.error) throw r.error;
        복구모드 = false; 알림('새 비밀번호를 저장했습니다.'); 화면갱신();
      }).catch(function (e) { 알림(/^login$/.test((e && e.message) || '') ? '복구 링크가 만료되었습니다. 「비밀번호 다시 정하기」로 새 링크를 받아 주세요.' : 말(e)); });
    }
    if (what === 'logout') { return 준비().then(function () { return sb.auth.signOut(); }).then(function () { 세션 = null; try { localStorage.removeItem(구독키()); } catch (e) {} 알림('로그아웃했습니다. 이 기기의 기록은 그대로 있습니다.'); 화면갱신(); }).catch(function (e) { 알림(말(e)); }); }
    if (what === 'sync') { return 준비().then(function () { if (!세션) { 알림('먼저 로그인해 주세요.'); return; } return 끌어오기().then(function () { return 밀어올리기(); }).then(function (n) { 알림('동기화했습니다' + (n ? ' (' + n + '건 올림)' : '') + '.'); 화면갱신(); }); }).catch(function (e) { 알림(말(e)); }); }
    if (what === 'signup' && 설정.가입확인 && !(document.getElementById('srvAge') || {}).checked) { 알림('계정을 만들려면 「' + 설정.가입확인.글 + '」에 체크해 주세요.'); return; }   /* 2026-09-23 나 */
    if (!email || email.indexOf('@') < 0) { 알림('이메일을 적어 주세요.'); return; }
    var st = 상태읽기(); st.email = email; 상태쓰기(st);
    if (what === 'reset') { return 준비().then(function () { var u = 앱주소(); return u ? sb.auth.resetPasswordForEmail(email, { redirectTo: u }) : sb.auth.resetPasswordForEmail(email); }).then(function (r) { if (r && r.error) throw r.error; }).then(function () { 알림('메일함을 확인해 주세요. 링크를 누르면 새 비밀번호를 정할 수 있습니다.'); }).catch(function (e) { 알림(말(e)); }); }
    if (pw.length < 6) { 알림('비밀번호는 6자 이상이어야 합니다.'); return; }
    return 준비().then(function () {
      if (what === 'signup' && 설정.가입확인 && typeof 설정.가입확인.기록 === 'function') { try { 설정.가입확인.기록(); } catch (e) {} }   /* 2026-09-23 나 — 확인한 때를 앱이 적는다 */
      if (what === 'signup') return sb.auth.signUp(앱주소() ? { email: email, password: pw, options: { emailRedirectTo: 앱주소() } } : { email: email, password: pw }).then(function (r) {
        if (r.error) throw r.error;
        if (r.data && r.data.session) { 세션 = r.data.session; 알림('계정을 만들었습니다. 기록을 올리는 중…'); 화면갱신(); }
        else 알림('메일함에 확인 링크를 보냈습니다. 누른 뒤 로그인해 주세요.');
      });
      return sb.auth.signInWithPassword({ email: email, password: pw }).then(function (r) {
        if (r.error) throw r.error; 세션 = r.data.session; 알림('로그인했습니다. 기록을 맞추는 중…'); 화면갱신();
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
      설정.준비됨 = o.준비됨 !== false;   /* 검수 #8 — 서버 표가 올라가면 앱의 설치 줄에서 true 로(또는 줄을 지운다) */   /* 2026-09-23 나 — { 글, 설명, 기록 } : 계정 만들기 앞 필수 체크 */
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
    준비됨: 준비됨   /* 검수 #8 — false 면 계정·동기화 준비 중 */
  };
})();
/* ▲▲ 서버 부품 끝 ▲▲ */
try {
  /* 준비됨 = meta.json 의 account 스위치 — 공용 서버에 약지도 칸(메디나눔_약지도_추가_1013.sql)이 열린 뒤에 true 로 켠다. 그 전엔 「준비 중」 한 줄(되는 척 금지). */
  서버.설치({ app: 'yakjido', 열쇠: /^yakjido\.me\.v1$/, 준비됨: function () { return !!(typeof D !== 'undefined' && D.meta && D.meta.account === true); }, 허용: srvAgreed, 다시그리기: srvReload,
    가입확인: { 글: '만 14세 이상이에요', 설명: '메디나눔 계정은 만 14세 이상만 만들 수 있어요. 아이 약은 보호자 계정에 담아 주세요.' } });
} catch (e) {}
/* 내 정보 화면을 보고 있었으면 계정 칸을 다시 그린다 */
try { if (/^#\/me/.test(location.hash)) route(); } catch (e) {}
