/* ▼▼ 위기번호 표 시작 ▼▼ */
/* ═══ 메디나눔 위기·응급 번호 표 — 나라 기준(말 기준 아님) · 2026-11-04 곁에에서 꺼냄(다섯 앱 공용 · 길동무 「말과 나라」가 재사용)
   나라: ISO 2자. 위기[0] = 한국 109(자살예방) 자리, 위기[1] = 한국 1577-0199(정신건강) 자리. 위기가 비면 응급 번호로.
   확인된 번호만 넣는다(멕시코는 응급 911 만 · 위기 전용 번호 확인 전). 표에 없는 나라는 XX — 번호 null: 누르는 단추 없이 「그 나라 응급 번호로 전화하세요」 글만.
   11-04b: XX 112 기본값 없앰 · 응급 번호 12나라(VN TH PH ID NP UZ KH MN LK BD IN GB) — 출처는 줄 옆.
   나라 고르는 순서: ① localStorage mn.place.country(사용자가 「말과 나라」에서 고른 값) ② 앱이 가진 값 ③ 시간대·기기 지역 짐작.
   ── 공용 부품 셋(위기번호 표 · 설정 부품 · 응급카드 부품) 공통 약속 · 주인: 길동무 세션 ──
   판: 이 파일 안 «판» 한 곳(코드의 판 값). 고치면 판을 올리고 다섯 앱에 다시 심는다. 지금 판 2026-11-04d.
   심는 순서(앱마다 같다): ① 위기번호 표 → ② 설정 부품 → ③ 응급카드 부품 — 표가 앞에 있어야 말과 나라 고르개·응급 번호가 표를 쓴다.
   심기·비교: python3 _도구/공용부품_심기.py 비교 · python3 _도구/공용부품_심기.py <소아|곁에|길동무|CS> · 다른 저장소(약지도): python3 _도구/공용부품_심기.py 파일 <경로>
   ⛔ 앱 사본을 직접 고치지 않는다 — 이 파일을 고치고 다시 심는다(심기 스크립트는 정본과 다른 사본을 보면 멈춘다).
*/
(function () {
  if (window.메디나눔위기번호) return;
  var 판 = '2026-11-04d';   /* 11-04d 라오스 LA 구급 1195 · TH 1669·VN 115·KH 119 gov.uk 다시 확인 · 11-04c 머리 주석 정리 */
  var 표 = {
    KR: { 이름: { ko: '한국', en: 'Korea', es: 'Corea', ja: '韓国', zh: '韩国' }, 응급: '119', 경찰: '112', 위기: ['109', '1577-0199'] },
    US: { 이름: { ko: '미국', en: 'United States', es: 'Estados Unidos', ja: 'アメリカ', zh: '美国' }, 응급: '911', 경찰: '911', 위기: ['988'] },
    ES: { 이름: { ko: '스페인', en: 'Spain', es: 'España', ja: 'スペイン', zh: '西班牙' }, 응급: '112', 경찰: '112', 위기: ['024'] },
    JP: { 이름: { ko: '일본', en: 'Japan', es: 'Japón', ja: '日本', zh: '日本' }, 응급: '119', 경찰: '110', 위기: ['0570-783-556', '0570-064-556'] }   /* 109(자살예방) 자리 → いのちの電話, 1577-0199(정신건강) 자리 → こころの健康相談統一ダイヤル */,
    CN: { 이름: { ko: '중국', en: 'China', es: 'China', ja: '中国', zh: '中国' }, 응급: '120', 경찰: '110', 위기: ['12356'] },
    MX: { 이름: { ko: '멕시코', en: 'Mexico', es: 'México', ja: 'メキシコ', zh: '墨西哥' }, 응급: '911', 경찰: '911', 위기: [] },   /* 11-03 Main — 확인된 응급 911 만(위기 전용 번호는 확인 전이라 넣지 않음 → 위기 자리도 911) */
    HK: { 이름: { ko: '홍콩', en: 'Hong Kong', es: 'Hong Kong', ja: '香港', zh: '香港' }, 응급: '999', 경찰: '999', 위기: ['2896 0000'] },   /* 10-27 Main 표 — The Samaritans(英文) */
    /* 11-04 Main — 한국에 많이 사는 나라부터 «응급(구급) 번호만». 공식 출처 두 곳이 맞는 것만. 위기 상담 번호는 아직 넣지 않음(위기 자리도 응급 번호).
       경찰은 한 번호로 모두 받는 나라만 같은 번호, 나머지는 null(→ 글로 「그 나라 경찰 번호」, 누르는 단추 없음).
       뺀 나라: 미얀마(영국 정부 192 · 미국 대사관은 192 를 고속도로 번호로·다른 번호와 엇갈림) → 그 밖. */
    VN: { 이름: { ko: '베트남', en: 'Vietnam', es: 'Vietnam', ja: 'ベトナム', zh: '越南' }, 응급: '115', 경찰: null, 위기: [] },   /* gov.uk/foreign-travel-advice/vietnam/getting-help · vietnam.travel(베트남 관광청) — 115 구급, 112 아님 */
    TH: { 이름: { ko: '태국', en: 'Thailand', es: 'Tailandia', ja: 'タイ', zh: '泰国' }, 응급: '1669', 경찰: null, 위기: [] },   /* gov.uk Thailand health(1669 보건부) · th.usembassy.gov */
    PH: { 이름: { ko: '필리핀', en: 'Philippines', es: 'Filipinas', ja: 'フィリピン', zh: '菲律宾' }, 응급: '911', 경찰: '911', 위기: [] },   /* gov.uk Philippines getting-help(911 구급·소방·경찰) · ph.usembassy.gov */
    ID: { 이름: { ko: '인도네시아', en: 'Indonesia', es: 'Indonesia', ja: 'インドネシア', zh: '印度尼西亚' }, 응급: '118', 경찰: null, 위기: [] },   /* gov.uk Indonesia getting-help(118) · indonesia.travel(118·119) */
    NP: { 이름: { ko: '네팔', en: 'Nepal', es: 'Nepal', ja: 'ネパール', zh: '尼泊尔' }, 응급: '102', 경찰: null, 위기: [] },   /* gov.uk Nepal getting-help · np.usembassy.gov · heoc.mohp.gov.np */
    UZ: { 이름: { ko: '우즈베키스탄', en: 'Uzbekistan', es: 'Uzbekistán', ja: 'ウズベキスタン', zh: '乌兹别克斯坦' }, 응급: '103', 경찰: null, 위기: [] },   /* gov.uk Uzbekistan getting-help · uzbekistan.travel */
    KH: { 이름: { ko: '캄보디아', en: 'Cambodia', es: 'Camboya', ja: 'カンボジア', zh: '柬埔寨' }, 응급: '119', 경찰: null, 위기: [] },   /* gov.uk Cambodia getting-help · travel.state.gov Cambodia */
    LA: { 이름: { ko: '라오스', en: 'Laos', es: 'Laos', ja: 'ラオス', zh: '老挝' }, 응급: '1195', 경찰: null, 위기: [] },   /* 11-04d 구급 1195(경찰 1191·화재 1190 따로) — gov.uk/foreign-travel-advice/laos/getting-help · travel.gc.ca Laos 둘 다 1195. 일부 생활 안내의 195 는 공식 아님 */
    MN: { 이름: { ko: '몽골', en: 'Mongolia', es: 'Mongolia', ja: 'モンゴル', zh: '蒙古' }, 응급: '103', 경찰: null, 위기: [] },   /* gov.uk Mongolia getting-help · mn.usembassy.gov */
    LK: { 이름: { ko: '스리랑카', en: 'Sri Lanka', es: 'Sri Lanka', ja: 'スリランカ', zh: '斯里兰卡' }, 응급: '1990', 경찰: null, 위기: [] },   /* gov.uk Sri Lanka health · lk.usembassy.gov(1990 Suwa Seriya) */
    BD: { 이름: { ko: '방글라데시', en: 'Bangladesh', es: 'Bangladés', ja: 'バングラデシュ', zh: '孟加拉国' }, 응급: '999', 경찰: '999', 위기: [] },   /* gov.uk Bangladesh getting-help · 999.gov.bd */
    IN: { 이름: { ko: '인도', en: 'India', es: 'India', ja: 'インド', zh: '印度' }, 응급: '112', 경찰: '112', 위기: [] },   /* gov.uk India health(112) · India ERSS(112 · 내무부) */
    GB: { 이름: { ko: '영국', en: 'United Kingdom', es: 'Reino Unido', ja: 'イギリス', zh: '英国' }, 응급: '999', 경찰: '999', 위기: [] },   /* gov.uk · NHS 999 */
    XX: { 이름: { ko: '그 밖', en: 'Other', es: 'Otro', ja: 'その他', zh: '其他' }, 응급: null, 경찰: null, 위기: [] }   /* 11-04 Main — 모르는 나라는 누르는 번호 없음(112 기본값 없앰) */
  };
  function 고른곳() { try { var v = JSON.parse(localStorage.getItem('mn.place') || 'null'); if (v && v.country) return 표[v.country] ? v.country : 'XX'; } catch (e) {} return null; }
  window.메디나눔위기번호 = { 판: 판, 표: 표, 고른곳: 고른곳 };   /* 표를 쓰는 앱은 읽기만 */
})();
/* ▲▲ 위기번호 표 끝 ▲▲ */
/* ═══ 약지도 다섯 언어(ko · en · es · ja · zh) — 10-27 현욱님 · 요청서 yozm-health docs/requests/20261027_메디나눔_전앱_다섯언어.md ═══
   한국어이고 한국에 있으면 이 파일을 받지 않는다(첫 화면 예산). 받으면 하는 일:
   ① 그 언어 사전(data/i18n/<lang>.json)을 받아 — 증상 응급·진료 신호, 처방약 길잡이 응급 칸(안전 먼저), 화면 글
   ② 그린 화면의 글을 사전으로 바꾼다(없는 글은 한국어 그대로 — 안전 칸을 숨기지 않는다)
   ③ 응급·마음 위기 번호를 «있는 나라» 표로 바꾼다(언어가 아니라 나라 — 표에 있는 숫자만)
   ④ 한국어가 아닌 화면 맨 위에 「번역은 의료진 검수 전」 한 줄 + 원문 보기 */
(function () {
  if (window.I18N) return;
  var L = window.LANG || 'ko', CC = window.CC || 'KR';
  /* 나라별 번호 — 요청서 표만(새 나라·번호는 Main 이 원문 확인 뒤 더함). m = 마음 위기 */
  var EMG = { KR: { e: '119', m: ['109', '1577-0199'] }, US: { e: '911', m: ['988'] }, ES: { e: '112', m: ['024'] },
              JP: { e: '119', m: ['0570-064-556', '0570-783-556'] }, CN: { e: '120', m: ['12356'] } };
  /* 11-04b 약지도 표(KR·US·ES·JP·CN) 먼저, 없으면 공용 위기번호 표(_도구/위기번호_표.js). 표에도 없으면 번호 없음(null) — 누르는 단추 없이 「그 나라 응급 번호」 글 */
  var 공표 = window.메디나눔위기번호 && window.메디나눔위기번호.표, 공 = 공표 && 공표[CC];
  var N = EMG[CC] || (공 && 공.응급 ? { e: 공.응급, m: 공.위기 || [] } : { e: null, m: [], unknown: true });
  var 현지 = { ko: '그 나라 응급 번호', en: 'the local emergency number', es: 'el número de emergencias del país', ja: '現地の緊急番号', zh: '当地急救电话' }[L] || 'the local emergency number';
  var DICT = null, ui = {}, uiN = {};
  var NOTE = { en: 'Translation not yet reviewed by our medical team', es: 'Traducción aún no revisada por nuestro equipo médico', ja: '翻訳は医療スタッフの確認前です', zh: '翻译尚未经医疗团队审核' };
  var ORIG = { en: 'Show Korean original', es: 'Ver original en coreano', ja: '韓国語の原文を見る', zh: '查看韩文原文' };
  var KRNOTE = { en: 'Medicine doses follow Korean approval — check with a pharmacist or doctor where you live.', es: 'Las dosis siguen la aprobación de Corea: confírmelas con un farmacéutico o médico de su país.', ja: '薬の量は韓国の承認基準です。お住まいの国の薬剤師・医師に確認してください。', zh: '药物剂量依据韩国批准标准，请向您所在国家的药师或医生确认。' };
  var key = function (t) { return String(t).replace(/\s+/g, ' ').trim(); };
  var numKey = function (t) { return t.replace(/\d[\d,.]*/g, '#'); };

  /* 글꼴·줄바꿈 — ja·zh 는 낱말 단위가 아니라 글자 단위(keep-all 이면 한 줄이 통째로 넘침) */
  var root = document.documentElement;
  root.lang = L === 'zh' ? 'zh-Hans' : L; root.classList.add('lang-' + L);
  /* ja·zh 는 기기 글꼴(10-27 바깥 파일 0 — 중국은 구글 글꼴이 막히고 Noto CJK 는 너무 커서 싣지 않는다) */
  var st = document.createElement('style');
  st.textContent = '.lang-ja body,.lang-ja button,.lang-ja input,.lang-ja textarea{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans CJK JP","Noto Sans JP","Yu Gothic UI","Meiryo","Pretendard Variable",system-ui,sans-serif}.lang-zh body,.lang-zh button,.lang-zh input,.lang-zh textarea{font-family:"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Noto Sans SC","Microsoft YaHei","Pretendard Variable",system-ui,sans-serif}' +
    'html:not(.lang-ko) nav.tabbar button{white-space:normal;text-align:center;font-size:12.5px;line-height:1.15;padding-inline:2px;overflow-wrap:normal;hyphens:auto;letter-spacing:-.01em}@media (min-width:1024px){html:not(.lang-ko) nav.tabbar button{text-align:left;font-size:1rem}}' +
    '.lang-ja *,.lang-zh *{word-break:normal!important;line-break:strict;overflow-wrap:anywhere}.lang-en *,.lang-es *{word-break:normal!important;overflow-wrap:break-word}' +
    'html:not(.lang-ko) .review-stamp{white-space:normal;flex:0 1 auto;min-width:0;text-align:right;line-height:1.25}html:not(.lang-ko) .chip,html:not(.lang-ko) .hq-c{white-space:normal;max-width:100%;min-width:0;overflow-wrap:anywhere}' +
    '.i18n-note{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;margin:24px 0 8px;padding-top:10px;border-top:1px solid var(--hairline);font-size:.8125rem;color:var(--muted)}.i18n-note button{color:var(--primary);font-weight:600;min-height:36px}';
  document.head.appendChild(st);

  function 받기() {
    if (L === 'ko') { DICT = {}; return Promise.resolve(); }
    var d = window.__I18N__ && window.__I18N__[L];   /* 아티팩트(파일 하나)는 사전을 안에 싣는다 */
    var p = d ? Promise.resolve(d) : fetch('data/i18n/' + L + '.json').then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; });
    return p.then(function (j) {
      DICT = j || {}; ui = DICT.ui || {};
      /* 숫자만 다른 글 — 번역의 숫자도 틀(#)로 바꿔 둔다. 숫자 개수가 원문과 다르면(°F 병기 등) 틀로 쓰지 않는다(같은 글일 때만 씀) */
      for (var k in ui) if (/\d/.test(k)) { var a = k.match(/\d[\d,.]*/g) || [], b = String(ui[k]).match(/\d[\d,.]*/g) || []; if (a.length === b.length) uiN[numKey(k)] = numKey(String(ui[k])); }
    });
  }
  /* 본문 덮어쓰기 — 증상·처방약 길잡이의 안전 칸. 자료가 늦게 오므로 그릴 때마다 한 번씩 본다(이미 했으면 건너뜀) */
  function 본문() {
    if (!DICT || typeof D === 'undefined' || !D) return;   /* D·RXG 는 앱 스크립트의 전역 const — window 속성이 아니다 */
    var S = DICT.sym || {};
    (D.symptoms || []).forEach(function (s) {
      var t = S[s.id]; if (!t) return;   /* 본문(core.json)이 늦게 와 덮을 수 있어 그릴 때마다 다시 얹는다(값이 같으면 그대로) */
      if (t.name) s.name = t.name; if (t.short) s.short = t.short;
      if (s.care) ['er', 'clinic', 'pharmacy'].forEach(function (k) { if (t[k] && s.care[k]) s.care[k] = s.care[k].map(function (x, i) { return t[k][i] || x; }); });
      if (s.triage && t.escalate) s.triage.escalate = t.escalate;
      if (t.find && !s._find) { s._find = 1; s.tags = (s.tags || []).concat(t.find); }   /* 안 보이는 찾는 말 — 검색에서만(화면엔 안 보임) */
    });
    /* 11-02 본문 — 많이 보는 증상부터 주마다(장부). 안전 칸과 따로 body 에 두고 칸마다 번호로 맞춘다. 빈 칸·모자란 칸은 한국어 그대로 */
    var B = DICT.body || {};
    (D.symptoms || []).forEach(function (s) {
      var b = B[s.id]; if (!b) return;
      ['lead', 'planTitle', 'planLabel'].forEach(function (k) { if (b[k] && s[k]) s[k] = b[k]; });
      ['how', 'pharmacy', 'selfcare', 'avoid'].forEach(function (k) { if (b[k] && Array.isArray(s[k])) s[k] = s[k].map(function (x, i) { return b[k][i] || x; }); });
      if (b.plan && Array.isArray(s.plan)) s.plan.forEach(function (o, i) { var x = b.plan[i]; if (x) ['slot', 'title', 'why', 'either'].forEach(function (f) { if (x[f] && o[f]) o[f] = x[f]; }); });
      if (b.notWorking && s.notWorking) { if (b.notWorking.title) s.notWorking.title = b.notWorking.title; if (b.notWorking.steps && s.notWorking.steps) s.notWorking.steps = s.notWorking.steps.map(function (x, i) { return b.notWorking.steps[i] || x; }); }
      if (b.faq && Array.isArray(s.faq)) s.faq.forEach(function (o, i) { var x = b.faq[i]; if (x) { if (x.q) o.q = x.q; if (x.a) o.a = x.a; } });
    });
    var R = typeof RXG !== 'undefined' ? RXG : window.RXG, RX = DICT.rx || {};
    if (R && R.guides) {
      for (var g in RX) { var G = R.guides[g]; if (!G) continue; var x = RX[g];
        if (x.title) G.title = x.title; if (x.short) G.short = x.short; if (x.lead) G.lead = x.lead;
        ['er', 'do'].forEach(function (f) { if (x[f] && G[f]) G[f].forEach(function (o, i) { if (x[f][i]) o.t = x[f][i]; }); });
        if (x.miss && G.miss) G.miss.t = x.miss; }
    }
  }
  function 글(t) {
    var k = key(t); if (!k || !/[가-힣]/.test(k)) return null;
    if (ui[k] != null) return ui[k];
    if (/\d/.test(k)) { var nk = numKey(k), v = uiN[nk]; if (v != null) { var nums = k.match(/\d[\d,.]*/g) || [], i = 0; return v.replace(/#/g, function () { return nums[i++] || ''; }); } }
    return null;
  }
  /* 번호 — 한국 번호를 있는 나라 번호로. 마음 위기 번호가 그 나라 표에 없으면 응급 번호로 */
  function 번호(s) {
    if (CC === 'KR') return s;
    var E = N.e || 현지;
    return s.replace(/1577-0199/g, N.m[1] || N.m[0] || E).replace(/(^|[^\d-])109(?![\d-])/g, function (a, p) { return p + (N.m[0] || E); }).replace(/(^|[^\d-])119(?![\d-])/g, function (a, p) { return p + E; });
  }
  /* 11-03 아래 탭은 칸이 좁아 긴 번역이 겹친다 — 탭에만 짧은 이름(화면 제목은 그대로) */
  var TABS = { en: { 'Medicine dictionary': 'Medicines', 'My information': 'My info' }, es: { 'Diccionario de medicamentos': 'Medicinas' } };
  function 탭() { var m = TABS[L], nav = document.querySelector('nav.tabbar'); if (!m || !nav || innerWidth >= 1024) return;
    var w = document.createTreeWalker(nav, NodeFilter.SHOW_TEXT, null), n; while ((n = w.nextNode())) { var k = n.nodeValue.trim(); if (m[k]) n.nodeValue = n.nodeValue.replace(k, m[k]); } }
  function 바꾸기(el) {
    if (!el) return;
    var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), n, todo = [];
    while ((n = w.nextNode())) todo.push(n);
    todo.forEach(function (n) {
      if (n.parentNode && /^(SCRIPT|STYLE|TEXTAREA)$/.test(n.parentNode.nodeName)) return;
      var 칸ko = n.parentNode && n.parentNode.closest ? n.parentNode.closest('[data-ko],[data-noko]') : null; if (칸ko && 칸ko.hasAttribute('data-ko')) return;   /* 11-04 약사에게 보여 줄 한국어 칸(한국에 사는 외국어 사용자) — 번역하지 않음 */
      var v = n.nodeValue, t = L !== 'ko' ? 글(v) : null;
      if (t != null) { var lead = v.match(/^\s*/)[0], tail = v.match(/\s*$/)[0]; if (/^[.,:;!?。，、．）)]/.test(t)) lead = ''; v = lead + t + tail; }   /* 굵은 글씨로 나뉜 문장 — 「labels .」 빈칸 없애기 */
      v = 번호(v); if (v !== n.nodeValue) n.nodeValue = v;
    });
    el.querySelectorAll('[placeholder],[aria-label],[title]').forEach(function (e) {
      ['placeholder', 'aria-label', 'title'].forEach(function (a) { var v = e.getAttribute(a); if (!v) return; var t = L !== 'ko' ? 글(v) : null; var nv = 번호(t != null ? t : v); if (nv !== v) e.setAttribute(a, nv); });
    });
    if (CC !== 'KR') el.querySelectorAll('a[href^="tel:"]').forEach(function (a) { var h = a.getAttribute('href'), nh = 'tel:' + 번호(h.slice(4));
      if (!N.e && /^tel:(119|109|1577-0199)$/.test(h)) { a.removeAttribute('href'); a.setAttribute('aria-disabled', 'true'); a.classList.add('tel-none'); return; }   /* 번호 모르는 나라 — 누르는 단추 없음 */
      if (nh !== h) a.setAttribute('href', nh); });
  }
  function 알림줄(view) {
    if (L === 'ko' || !view || view.querySelector('.i18n-note')) return;
    var d = document.createElement('div'); d.className = 'i18n-note';
    d.innerHTML = '<span>' + NOTE[L] + '</span><button type="button" onclick="setLang(\'ko\')">' + ORIG[L] + '</button>';
    view.appendChild(d);   /* 11-03 Main — 첫 3초에 경고가 먼저 보이지 않게 화면 맨 아래 작은 한 줄로(첫 진입 경고 벽 금지) */
    /* 약 용량 칸 — 「한국 허가 기준 — 사는 나라 약사와 확인」 */
    view.querySelectorAll('.dose-card,.dose-hero,.sv-dose').forEach(function (c) { if (c.querySelector('.i18n-kr')) return; var p = document.createElement('p'); p.className = 'i18n-kr small muted'; p.textContent = KRNOTE[L]; c.appendChild(p); });
  }
  window.I18N = {
    lang: L, cc: CC, emg: N,
    tr: function (el) { if (DICT && el) 바꾸기(el); },   /* 11-03 늦게 채우는 칸(기내용 받아 두기 등) */
    t: function (s) { var r = L !== 'ko' ? 글(s) : null; return 번호(r != null ? r : s); },   /* 11-03 그린 뒤에 넣는 글(로그인 필수 안내 등) */
    apply: function (view) { if (!DICT) return; 본문(); 바꾸기(view); 바꾸기(document.querySelector('nav.tabbar')); 탭(); 알림줄(view); },
    ready: 받기().then(function () { 본문(); if (typeof route === 'function') route(); })
  };
})();
