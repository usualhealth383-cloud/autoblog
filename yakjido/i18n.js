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
  var N = EMG[CC] || { e: '112', m: [], unknown: true };
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
    '.lang-ja *,.lang-zh *{word-break:normal!important;line-break:strict;overflow-wrap:anywhere}.lang-en *,.lang-es *{word-break:normal!important;overflow-wrap:break-word}' +
    'html:not(.lang-ko) .review-stamp{white-space:normal;flex:0 1 auto;min-width:0;text-align:right;line-height:1.25}html:not(.lang-ko) .chip,html:not(.lang-ko) .hq-c{white-space:normal;max-width:100%;min-width:0;overflow-wrap:anywhere}' +
    '.i18n-note{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;margin:6px 0 12px;font-size:.8125rem;color:var(--muted)}.i18n-note button{color:var(--primary);font-weight:600;min-height:36px}';
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
    return s.replace(/1577-0199/g, N.m[1] || N.m[0] || N.e).replace(/(^|[^\d-])109(?![\d-])/g, function (a, p) { return p + (N.m[0] || N.e); }).replace(/(^|[^\d-])119(?![\d-])/g, function (a, p) { return p + N.e; });
  }
  function 바꾸기(el) {
    if (!el) return;
    var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), n, todo = [];
    while ((n = w.nextNode())) todo.push(n);
    todo.forEach(function (n) {
      if (n.parentNode && /^(SCRIPT|STYLE|TEXTAREA)$/.test(n.parentNode.nodeName)) return;
      var v = n.nodeValue, t = L !== 'ko' ? 글(v) : null;
      if (t != null) { var lead = v.match(/^\s*/)[0], tail = v.match(/\s*$/)[0]; v = lead + t + tail; }
      v = 번호(v); if (v !== n.nodeValue) n.nodeValue = v;
    });
    el.querySelectorAll('[placeholder],[aria-label],[title]').forEach(function (e) {
      ['placeholder', 'aria-label', 'title'].forEach(function (a) { var v = e.getAttribute(a); if (!v) return; var t = L !== 'ko' ? 글(v) : null; var nv = 번호(t != null ? t : v); if (nv !== v) e.setAttribute(a, nv); });
    });
    if (CC !== 'KR') el.querySelectorAll('a[href^="tel:"]').forEach(function (a) { var h = a.getAttribute('href'), nh = 'tel:' + 번호(h.slice(4)); if (nh !== h) a.setAttribute('href', nh); });
  }
  function 알림줄(view) {
    if (L === 'ko' || !view || view.querySelector('.i18n-note')) return;
    var top = view.querySelector('.topfind') || view.querySelector('.top');
    var d = document.createElement('div'); d.className = 'i18n-note';
    d.innerHTML = '<span>' + NOTE[L] + '</span><button type="button" onclick="setLang(\'ko\')">' + ORIG[L] + '</button>';
    if (top && top.parentNode) top.parentNode.insertBefore(d, top.nextSibling); else view.insertBefore(d, view.firstChild);
    /* 약 용량 칸 — 「한국 허가 기준 — 사는 나라 약사와 확인」 */
    view.querySelectorAll('.dose-card,.dose-hero,.sv-dose').forEach(function (c) { if (c.querySelector('.i18n-kr')) return; var p = document.createElement('p'); p.className = 'i18n-kr small muted'; p.textContent = KRNOTE[L]; c.appendChild(p); });
  }
  window.I18N = {
    lang: L, cc: CC, emg: N,
    apply: function (view) { if (!DICT) return; 본문(); 바꾸기(view); 바꾸기(document.querySelector('nav.tabbar')); 알림줄(view); },
    ready: 받기().then(function () { 본문(); if (typeof route === 'function') route(); })
  };
})();
