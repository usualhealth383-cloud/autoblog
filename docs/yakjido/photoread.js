/* 메디나눔 공용 사진읽기 부품 — 원본은 yozm-health _도구/사진읽기_부품.js. 여기를 고치지 말고 원본을 고친 뒤 다시 복사한다. 약지도는 인식 파일 주소를 vendor/ocr 로 바꿔 쓴다(app-shell prLoad). */
/* ▼▼ 사진읽기 부품 시작 ▼▼ — 판 2026-11-26a
   현욱님 11-26 「사진·엑셀을 올리면 잘 분석」 — 아홉 앱 공용, 1단계(폰 안에서 읽기).
   받는 것: 사진 찍기·고르기 · 엑셀(.xlsx 첫 시트, 라이브러리 없이) · CSV(UTF-8/EUC-KR) · 표 붙여넣기.
   ⛔ 읽은 값은 바로 쓰지 않는다 — 「읽은 값 확인」 표(사진 속 그 자리 + 고칠 수 있는 값)에서 「맞아요, 넣기」를 눌러야 받기().
   ⛔ 사진은 폰 밖으로 나가지 않는다 — 글자 인식(Tesseract.js)은 폰 안에서. 받는 것은 인식 엔진·글자 파일(jsdelivr, 판 고정)뿐.
   ⛔ EXIF(위치·기기)는 캔버스로 다시 그려 지운 뒤 다룬다. 사진·파일은 메모리에만, 창을 닫으면 버린다.
   「더 정확하게(AI)」는 자리만 — 서버·비용 승인 전까지 꺼 둔다(켤 때 규칙은 아래 AI규칙).
   설치: 사진읽기.설치({ 앱:'너스마트', 읽을것:'명단', 받기:function(값){ 값.줄 = [[칸,…],…] }, 자리:'.ndr-card', 단추글:'사진·파일로 읽기' })
   또는 사진읽기.열기({ 읽을것:'검사지', 받기:… }) 로 바로 연다.
   읽을것: '표' | '검사지' | '약' | '접종' | '명단' — 확인 표의 안내 말과 숫자·단위 나누기가 달라진다. */
(function () {
  if (window.사진읽기) return;
  var 판 = '2026-11-26a';
  var OCR = {   /* 판 고정 — 바꿀 때는 크기를 다시 재고 「약 ○MB」 줄을 같이 고친다 */
    js: 'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js',
    worker: 'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/worker.min.js',
    core: 'https://cdn.jsdelivr.net/npm/tesseract.js-core@5.1.1',
    lang: 'https://cdn.jsdelivr.net/gh/naptha/tessdata@806cd9adc8c6e8abc11c782db1818c990576bebc/4.0.0_best_int',
    MB: 5.4   /* 11-26 실측(시험_사진읽기 받은 바이트 5.42MB): 엔진 + 한글 + 영어 + 스크립트 */
  };
  var AI규칙 = { 켬: false, 안내: '환자 이름·등록번호가 보이는 사진은 쓰지 마세요. 보내기 전에 위치 정보를 지우고, 서버에 남기지 않아요.' };
  var 말 = {
    표: { 제목: '표 읽기', 확인: '사진에서 읽은 값이에요. 틀린 곳을 고친 뒤 넣어 주세요.' },
    검사지: { 제목: '검사지 읽기', 확인: '숫자와 단위를 함께 확인해 주세요. 틀린 곳은 고친 뒤 넣어 주세요.' },
    약: { 제목: '약 봉투·처방전 읽기', 확인: '약 이름과 용량을 함께 확인해 주세요.' },
    접종: { 제목: '접종 기록 읽기', 확인: '날짜와 백신 이름을 확인해 주세요.' },
    명단: { 제목: '명단 읽기', 확인: '이름과 병실을 확인해 주세요. 틀린 곳은 고친 뒤 넣어 주세요.' }
  };
  function e(t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  /* ── 1. 엑셀·CSV·붙여넣기 (너스마트_명단.js 에서 올림) ── */
  function u16(b, o) { return b[o] | (b[o + 1] << 8); }
  function u32(b, o) { return (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0; }
  function 압축목록(b) {
    var i = b.length - 22; while (i >= 0 && u32(b, i) !== 0x06054b50) i--; if (i < 0) throw new Error('엑셀(xlsx) 파일이 아니에요');
    var n = u16(b, i + 10), o = u32(b, i + 16), 목 = {}, d = new TextDecoder();
    for (var k = 0; k < n; k++) { if (u32(b, o) !== 0x02014b50) break; var 방 = u16(b, o + 10), 크 = u32(b, o + 20), 길 = u16(b, o + 28), 덧 = u16(b, o + 30), 말길 = u16(b, o + 32), 자 = u32(b, o + 42);
      목[d.decode(b.subarray(o + 46, o + 46 + 길))] = { 방: 방, 크: 크, 자: 자 }; o += 46 + 길 + 덧 + 말길; }
    return 목;
  }
  function 풀기(b, 항) {
    if (!항) return Promise.resolve('');
    var o = 항.자, 시작 = o + 30 + u16(b, o + 26) + u16(b, o + 28), 날 = b.subarray(시작, 시작 + 항.크);
    if (항.방 === 0) return Promise.resolve(new TextDecoder().decode(날));
    if (항.방 !== 8 || !window.DecompressionStream) return Promise.reject(new Error('이 기기에서는 xlsx 를 풀 수 없어요 — CSV 로 저장하거나 표를 복사해 붙여 주세요'));
    return new Response(new Blob([날]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text();
  }
  function 열번호(r) { var m = /^([A-Z]+)/.exec(r || ''), n = 0; if (!m) return -1; for (var i = 0; i < m[1].length; i++) n = n * 26 + m[1].charCodeAt(i) - 64; return n - 1; }
  function xlsx읽기(buf) {
    var b = new Uint8Array(buf), 목 = 압축목록(b), 시트 = Object.keys(목).filter(function (k) { return /^xl\/worksheets\/sheet\d+\.xml$/.test(k); }).sort(function (a, c) { return parseInt(a.match(/\d+/)) - parseInt(c.match(/\d+/)); })[0];
    if (!시트) return Promise.reject(new Error('시트를 찾지 못했어요'));
    return Promise.all([풀기(b, 목['xl/sharedStrings.xml']), 풀기(b, 목[시트])]).then(function (r) {
      var P = new DOMParser(), 공 = [], 줄 = [];
      if (r[0]) { var sd = P.parseFromString(r[0], 'application/xml'); [].forEach.call(sd.getElementsByTagName('si'), function (si) { 공.push([].map.call(si.getElementsByTagName('t'), function (t) { return t.textContent; }).join('')); }); }
      var d = P.parseFromString(r[1], 'application/xml');
      [].forEach.call(d.getElementsByTagName('row'), function (row) { var 칸 = [];
        [].forEach.call(row.getElementsByTagName('c'), function (c) { var i = 열번호(c.getAttribute('r')), t = c.getAttribute('t'), v = c.getElementsByTagName('v')[0], 값 = '';
          if (t === 's' && v) 값 = 공[+v.textContent] || ''; else if (t === 'inlineStr') 값 = [].map.call(c.getElementsByTagName('t'), function (x) { return x.textContent; }).join(''); else if (v) 값 = v.textContent;
          if (i < 0) i = 칸.length; while (칸.length < i) 칸.push(''); 칸[i] = 값; });
        if (칸.some(function (x) { return String(x).trim(); })) 줄.push(칸); });
      return 줄;
    });
  }
  function 표나누기(t) {
    t = String(t || '').replace(/\r\n?/g, '\n'); var 첫 = t.split('\n')[0] || '', 구 = 첫.indexOf('\t') >= 0 ? '\t' : (첫.split(',').length >= 2 ? ',' : (첫.split(';').length >= 2 ? ';' : '\t'));
    var 줄 = [], 칸 = [], 값 = '', 따 = false;
    for (var i = 0; i < t.length; i++) { var ch = t[i];
      if (따) { if (ch === '"') { if (t[i + 1] === '"') { 값 += '"'; i++; } else 따 = false; } else 값 += ch; continue; }
      if (ch === '"' && !값) 따 = true; else if (ch === 구) { 칸.push(값.trim()); 값 = ''; } else if (ch === '\n') { 칸.push(값.trim()); if (칸.some(function (x) { return x; })) 줄.push(칸); 칸 = []; 값 = ''; } else 값 += ch; }
    칸.push(값.trim()); if (칸.some(function (x) { return x; })) 줄.push(칸); return 줄;
  }
  function csv읽기(buf) { var u = new TextDecoder('utf-8').decode(buf); if (/�/.test(u)) { try { u = new TextDecoder('euc-kr').decode(buf); } catch (x) {} } return 표나누기(u.replace(/^﻿/, '')); }

  /* ── 2. 사진 — EXIF 지우기(캔버스로 다시 그림) · 크기 맞추기 ── */
  function 사진캔버스(file) {
    var 그리기 = function (src, w, h) { var 긴 = Math.max(w, h), 배 = 긴 > 2600 ? 2600 / 긴 : (긴 < 1200 ? 1200 / 긴 : 1); var c = document.createElement('canvas'); c.width = Math.round(w * 배); c.height = Math.round(h * 배);
      var g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.imageSmoothingQuality = 'high'; g.drawImage(src, 0, 0, c.width, c.height); return c; };
    if (window.createImageBitmap) return createImageBitmap(file, { imageOrientation: 'from-image' }).then(function (bm) { var c = 그리기(bm, bm.width, bm.height); try { bm.close(); } catch (x) {} return c; });
    return new Promise(function (ok, no) { var u = URL.createObjectURL(file), im = new Image(); im.onload = function () { URL.revokeObjectURL(u); ok(그리기(im, im.naturalWidth, im.naturalHeight)); }; im.onerror = function () { URL.revokeObjectURL(u); no(new Error('사진을 열지 못했어요')); }; im.src = u; });
  }
  function 흑백(c) {   /* 인식 전 — 회색 · 대비 · 표의 긴 가로·세로 줄 지우기(줄이 「ㅣ」「」」로 읽혀 칸이 뭉개진다, 11-26 실측). 원본 캔버스는 확인 표 잘라 보기에 그대로 쓴다 */
    var W = c.width, H = c.height, d = document.createElement('canvas'); d.width = W; d.height = H; var g = d.getContext('2d'); g.drawImage(c, 0, 0);
    var im = g.getImageData(0, 0, W, H), p = im.data, y8 = new Uint8ClampedArray(W * H), 합 = 0;
    for (var i = 0, j = 0; i < p.length; i += 4, j++) { var y = 0.299 * p[i] + 0.587 * p[i + 1] + 0.114 * p[i + 2]; y8[j] = Math.max(0, Math.min(255, (y - 128) * 1.25 + 128)); 합 += y8[j]; }
    var 문 = Math.min(200, 합 / (W * H) - 40), 검 = new Uint8Array(W * H); for (j = 0; j < W * H; j++) 검[j] = y8[j] < 문 ? 1 : 0;
    var 가길 = Math.max(80, Math.round(W * 0.06)), 세길 = Math.max(60, Math.round(Math.max(W, H) * 0.045)), 지울 = new Uint8Array(W * H), x, yy, s0;
    for (yy = 0; yy < H; yy++) { s0 = -1; for (x = 0; x <= W; x++) { var k = x < W && 검[yy * W + x]; if (k && s0 < 0) s0 = x; if (!k && s0 >= 0) { if (x - s0 >= 가길) for (var q = s0; q < x; q++) 지울[yy * W + q] = 1; s0 = -1; } } }
    for (x = 0; x < W; x++) { s0 = -1; for (yy = 0; yy <= H; yy++) { var k2 = yy < H && 검[yy * W + x]; if (k2 && s0 < 0) s0 = yy; if (!k2 && s0 >= 0) { if (yy - s0 >= 세길) for (var q2 = s0; q2 < yy; q2++) 지울[q2 * W + x] = 1; s0 = -1; } } }
    for (j = 0, i = 0; j < W * H; j++, i += 4) { var v = 지울[j] ? 255 : y8[j]; p[i] = p[i + 1] = p[i + 2] = v; }
    g.putImageData(im, 0, 0); return d;
  }
  function 한글붙이기(t) {   /* 「최 성 호」처럼 한 글자씩 띄어 읽힌 것을 붙인다(두 글자 이상 낱말 사이 띄어쓰기는 둔다) */
    var 낱 = String(t).split(' '), 끝 = [];
    낱.forEach(function (w) { var 앞 = 끝[끝.length - 1]; if (앞 != null && /^[가-힣]$/.test(w) && /[가-힣]$/.test(앞) && (앞.length === 1 || 끝._붙임)) { 끝[끝.length - 1] = 앞 + w; 끝._붙임 = true; } else { 끝.push(w); 끝._붙임 = /^[가-힣]$/.test(w); } });
    return 끝.join(' ');
  }

  /* ── 3. 글자 인식(폰 안) ── */
  var 엔진 = null;
  function 스크립트(src) { return new Promise(function (ok, no) { if (window.Tesseract) return ok(); var s = document.createElement('script'); s.src = src; s.crossOrigin = 'anonymous'; s.onload = ok; s.onerror = function () { no(new Error('글자 인식 파일을 받지 못했어요 — 인터넷을 확인해 주세요')); }; document.head.appendChild(s); }); }
  function 엔진준비(진행) {
    if (엔진) return 엔진;
    엔진 = 스크립트(OCR.js).then(function () {
      return Tesseract.createWorker('kor+eng', 1, { workerPath: OCR.worker, corePath: OCR.core, langPath: OCR.lang, logger: function (m) { if (진행 && m && typeof m.progress === 'number') 진행(m.status, m.progress); } });
    }).then(function (w) { try { localStorage.setItem('pr_ocr_got', 판); } catch (x) {} return w; }, function (x) { 엔진 = null; throw x; });
    return 엔진;
  }
  function 칸나누기(줄들) {   /* 한 줄의 낱말을 x 간격으로 칸에 나눈다 — 표는 칸 사이가 글자 사이보다 넓다 */
    return 줄들.map(function (ln) {
      var ws = (ln.words || []).map(function (w) { w.text = String(w.text || '').replace(/[|¦「」、。，：]/g, '').replace(/^ㅣ+|ㅣ+$/g, '').replace(/^[_\s]+|[_\s]+$/g, '').trim(); return w; }).filter(function (w) { return w.text && !/^[\[\]{}()_—\-=~:;'"`.,]+$/.test(w.text); }).sort(function (a, b) { return a.bbox.x0 - b.bbox.x0; });
      if (!ws.length) return null;
      var 높 = ws.reduce(function (a, w) { return a + (w.bbox.y1 - w.bbox.y0); }, 0) / ws.length, 칸 = [], 지금 = null;
      ws.forEach(function (w) {
        if (지금 && w.bbox.x0 - 지금.bbox.x1 <= 높 * 0.9) { 지금.text += ' ' + w.text.trim(); 지금.bbox.x1 = Math.max(지금.bbox.x1, w.bbox.x1); 지금.bbox.y0 = Math.min(지금.bbox.y0, w.bbox.y0); 지금.bbox.y1 = Math.max(지금.bbox.y1, w.bbox.y1); 지금.conf = Math.min(지금.conf, w.confidence); }
        else { 지금 = { text: w.text.trim(), bbox: { x0: w.bbox.x0, y0: w.bbox.y0, x1: w.bbox.x1, y1: w.bbox.y1 }, conf: w.confidence }; 칸.push(지금); }
      });
      칸.forEach(function (c) { c.text = 한글붙이기(c.text); });
      return { bbox: ln.bbox, 칸: 칸 };
    }).filter(Boolean);
  }
  function 겹(a0, a1, b0, b1) { return Math.max(0, Math.min(a1, b1) - Math.max(a0, b0)); }
  function 합치기(가, 나) {   /* 같은 사진을 두 언어로 읽은 결과 — 같은 자리 칸끼리 확신도가 높은 쪽 */
    var 쓴 = {};
    가.forEach(function (l) {
      var 짝 = -1, 최 = 0; 나.forEach(function (m, i) { var o = 겹(l.bbox.y0, l.bbox.y1, m.bbox.y0, m.bbox.y1) / Math.max(1, Math.min(l.bbox.y1 - l.bbox.y0, m.bbox.y1 - m.bbox.y0)); if (o > 최) { 최 = o; 짝 = i; } });
      if (짝 < 0 || 최 < 0.5) return; 쓴[짝] = 1; var m = 나[짝], 씀 = {};
      l.칸 = l.칸.map(function (c) { var 고 = c; m.칸.forEach(function (d, k) { var o = 겹(c.bbox.x0, c.bbox.x1, d.bbox.x0, d.bbox.x1) / Math.max(1, Math.min(c.bbox.x1 - c.bbox.x0, d.bbox.x1 - d.bbox.x0)); if (o >= 0.5) { 씀[k] = 1; if (d.conf > 고.conf) 고 = d; } }); return 고; });
      m.칸.forEach(function (d, k) { if (!씀[k]) l.칸.push(d); }); l.칸.sort(function (x, y) { return x.bbox.x0 - y.bbox.x0; });
    });
    나.forEach(function (m, i) { if (!쓴[i]) 가.push(m); });
    return 가.sort(function (x, y) { return x.bbox.y0 - y.bbox.y0; });
  }
  function 사진읽기(c, 진행) {
    var bw = 흑백(c), w, 첫;
    var 판짜 = { tessedit_pageseg_mode: '6', preserve_interword_spaces: '1' };   /* 6 = 한 덩어리 표 — 자동(3)보다 칸이 덜 흩어진다(11-26 실측) */
    return 엔진준비(진행).then(function (x) { w = x; return w.setParameters(판짜); })
      .then(function () { return w.recognize(bw); })
      .then(function (r) { 첫 = 칸나누기((r && r.data && r.data.lines) || []); if (진행) 진행('recognizing text', 0.6); return w.reinitialize('kor').then(function () { return w.setParameters(판짜); }); })
      .then(function () { return w.recognize(bw); })
      .then(function (r) { var 둘 = 칸나누기((r && r.data && r.data.lines) || []); return w.reinitialize('kor+eng').then(function () { return 합치기(첫, 둘); }, function () { 엔진 = null; return 합치기(첫, 둘); }); });
  }

  /* ── 4. 화면 ── */
  var 지금 = null;   /* { o, 캔버스, 줄:[{칸:[{text,bbox,conf}], bbox}] | 표:[[...]], 출처, 파일 } — 창을 닫으면 버린다 */
  var css = '#pr-veil{position:fixed;inset:0;z-index:2147482500;background:rgba(15,20,19,.45);display:flex;align-items:flex-end;justify-content:center}'
    + '#pr-sh{background:var(--bg,var(--card,#fff));color:var(--ink,#1b2422);width:100%;max-width:560px;max-height:92vh;overflow:auto;overscroll-behavior:contain;border-radius:22px 22px 0 0;padding:14px 18px 22px;box-sizing:border-box;font-family:inherit;word-break:keep-all;letter-spacing:-.012em}'
    + '#pr-sh *{box-sizing:border-box}.pr-hd{display:flex;align-items:center;gap:12px;margin:4px 0 10px}.pr-hd h3{flex:1;margin:0;font-size:19px;font-weight:700}.pr-x{width:40px;height:40px;border-radius:50%;border:1px solid var(--line,#e3e6e4);background:none;font-size:20px;color:inherit;cursor:pointer}'
    + '.pr-p{margin:0 0 12px;font-size:14px;line-height:1.55;color:var(--muted,var(--ink2,#5b6563))}'
    + '.pr-g{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pr-b{position:relative;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;gap:2px;min-height:74px;padding:12px 14px;border:1px solid var(--line,#e3e6e4);border-radius:16px;background:var(--card,#fff);color:inherit;font:inherit;font-size:15px;font-weight:700;text-align:left;cursor:pointer;overflow:hidden}'
    + '.pr-b small{font-size:12px;font-weight:500;color:var(--muted,var(--ink2,#5b6563))}.pr-b input{position:absolute;inset:0;opacity:0;cursor:pointer}.pr-b[disabled]{opacity:.5;cursor:default}'
    + '.pr-go{width:100%;min-height:52px;border:0;border-radius:14px;background:var(--accent,#2F6F62);color:#fff;font:inherit;font-size:16px;font-weight:700;cursor:pointer;margin-top:12px}.pr-gh{width:100%;min-height:46px;border:1px solid var(--line,#e3e6e4);border-radius:14px;background:none;color:inherit;font:inherit;font-size:15px;font-weight:600;cursor:pointer;margin-top:8px}'
    + '.pr-ta{width:100%;min-height:120px;border:1px solid var(--line,#e3e6e4);border-radius:12px;padding:10px;font:inherit;font-size:14px;background:var(--card,#fff);color:inherit}'
    + '.pr-bar{height:6px;border-radius:9px;background:var(--line,#e3e6e4);overflow:hidden;margin:6px 0}.pr-bar i{display:block;height:100%;background:var(--accent,#2F6F62);width:0;transition:width .2s}'
    + '.pr-row{border:1px solid var(--line,#e3e6e4);border-radius:14px;padding:10px;margin-top:10px;background:var(--card,#fff)}.pr-row img{display:block;max-width:100%;height:auto;max-height:46px;border-radius:6px;background:#fff;margin-bottom:8px}'
    + '.pr-cells{display:flex;flex-wrap:wrap;gap:6px}.pr-cells input{flex:1 1 84px;min-width:0;min-height:42px;border:1px solid var(--line,#e3e6e4);border-radius:10px;padding:0 10px;font:inherit;font-size:15px;background:var(--bg,#fff);color:inherit}'
    + '.pr-cells input.n{font-weight:800;font-feature-settings:"tnum"}.pr-cells input.low{border-color:#D98A2B;background:rgba(217,138,43,.08)}.pr-cells input.u{flex:0 1 76px;font-size:13px}'
    + '.pr-key{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--muted,var(--ink2,#5b6563));margin:4px 0 0}.pr-key i{display:inline-block;width:12px;height:12px;border-radius:4px;border:1.5px solid #D98A2B;background:rgba(217,138,43,.08);vertical-align:-2px;margin-right:4px}'
    + '.pr-tb{width:100%;border-collapse:collapse;font-size:14px}.pr-tb td{border-top:1px solid var(--line,#e3e6e4);padding:4px}.pr-tb input{width:100%;min-width:0;min-height:38px;border:1px solid var(--line,#e3e6e4);border-radius:8px;padding:0 8px;font:inherit;font-size:14px;background:var(--bg,#fff);color:inherit}'
    + '.pr-wrap{overflow-x:auto;max-width:100%}.pr-del{border:0;background:none;color:var(--muted,#5b6563);font:inherit;font-size:13px;cursor:pointer;padding:6px 0 0}';
  function 틀(h) {
    var v = document.getElementById('pr-veil');
    if (!v) { if (!document.getElementById('pr-css')) { var s = document.createElement('style'); s.id = 'pr-css'; s.textContent = css; document.head.appendChild(s); }
      v = document.createElement('div'); v.id = 'pr-veil'; v.innerHTML = '<div id="pr-sh" role="dialog" aria-modal="true" aria-labelledby="pr-t"></div>'; document.body.appendChild(v);
      v.addEventListener('click', function (ev) { if (ev.target === v) 닫기(); }); }
    document.getElementById('pr-sh').innerHTML = h;
  }
  function 머리(t) { return '<div class="pr-hd"><h3 id="pr-t">' + e(t) + '</h3><button type="button" class="pr-x" aria-label="닫기" data-pr="x">×</button></div>'; }
  function 첫화면() {
    var o = 지금.o, m = 말[o.읽을것] || 말.표, 받은 = (function () { try { return localStorage.getItem('pr_ocr_got') === 판; } catch (x) { return false; } })();
    틀(머리(o.제목 || m.제목)
      + '<p class="pr-p">사진은 이 폰 안에서만 읽어요. 읽은 값은 확인한 뒤에 넣어요.</p>'
      + '<div class="pr-g">'
      + '<label class="pr-b">사진 찍기<small>카메라로 바로</small><input type="file" accept="image/*" capture="environment" data-pr="img"></label>'
      + '<label class="pr-b">사진 고르기<small>앨범에서</small><input type="file" accept="image/*" data-pr="img"></label>'
      + '<label class="pr-b">엑셀·CSV<small>.xlsx 첫 시트 · .csv</small><input type="file" accept=".xlsx,.csv,.txt,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" data-pr="file"></label>'
      + '<button type="button" class="pr-b" data-pr="paste">표 붙여넣기<small>엑셀에서 복사한 표</small></button>'
      + '</div>'
      + (받은 ? '' : '<p class="pr-p" style="margin-top:12px">사진을 처음 읽을 때 글자 인식 파일 약 ' + OCR.MB + 'MB를 한 번 받아요. 와이파이에서 하시면 좋아요.</p>')
      + '<button type="button" class="pr-gh" disabled aria-disabled="true" title="준비 중">더 정확하게(AI) — 준비 중</button>');
  }
  function 붙여넣기화면() {
    틀(머리('표 붙여넣기') + '<p class="pr-p">엑셀이나 화면의 표를 복사해 아래에 붙여 주세요.</p><textarea class="pr-ta" data-pr="ta" aria-label="붙일 표"></textarea>'
      + '<button type="button" class="pr-go" data-pr="pasteGo">읽기</button><button type="button" class="pr-gh" data-pr="back">뒤로</button>');
  }
  function 진행화면(t) { 틀(머리('읽는 중') + '<p class="pr-p" data-pr="st">' + e(t) + '</p><div class="pr-bar"><i data-pr="bar"></i></div>'); }
  var 진말 = { 'loading tesseract core': '인식 엔진 받는 중', 'loading language traineddata': '글자 파일 받는 중', 'initializing api': '준비 중', 'recognizing text': '글자 읽는 중' };
  function 진행(st, p) { var a = document.querySelector('[data-pr="st"]'), b = document.querySelector('[data-pr="bar"]'); if (a) a.textContent = (진말[st] || '준비 중') + ' · ' + Math.round(p * 100) + '%'; if (b) b.style.width = Math.round(p * 100) + '%'; }
  function 잘라(bb) {   /* 사진에서 그 자리만 잘라 보여 준다(메모리 안 data URL) */
    var c = 지금.캔버스, 여 = 6, x = Math.max(0, bb.x0 - 여), y = Math.max(0, bb.y0 - 여), w = Math.min(c.width - x, bb.x1 - bb.x0 + 여 * 2), h = Math.min(c.height - y, bb.y1 - bb.y0 + 여 * 2);
    if (w <= 0 || h <= 0) return ''; var d = document.createElement('canvas'), 배 = Math.min(1, 640 / w); d.width = Math.round(w * 배); d.height = Math.round(h * 배); d.getContext('2d').drawImage(c, x, y, w, h, 0, 0, d.width, d.height); return d.toDataURL('image/jpeg', .85);
  }
  var 숫자 = /^[<>≤≥±+\-]?\d[\d,.]*$/, 단위 = /^([<>≤≥]?[\d][\d,.]*)\s*(%|mg\/dL|g\/dL|mmol\/L|mEq\/L|U\/L|IU\/L|ng\/mL|pg\/mL|μg\/dL|ug\/dL|mg|g|mL|ml|kg|cm|mmHg|bpm|회|정|캡슐|포|세|개월|일|℃|°C|\/μL|\/uL|x10\^?\d+\/L|10\^?\d+\/μL)$/i;
  function 확인화면() {
    var o = 지금.o, m = 말[o.읽을것] || 말.표, h = 머리('읽은 값 확인') + '<p class="pr-p">' + e(m.확인) + '</p>';
    if (지금.줄) {
      var 낮 = 0; h += '<div class="pr-key"><span><i></i>흐리게 읽힌 칸 — 꼭 봐 주세요</span><span><b>굵은 글씨</b> = 숫자</span></div>';
      지금.줄.forEach(function (ln, r) {
        var 그림 = 잘라(ln.bbox);
        h += '<div class="pr-row" data-r="' + r + '">' + (그림 ? '<img alt="사진 속 ' + (r + 1) + '번째 줄" src="' + 그림 + '">' : '') + '<div class="pr-cells">'
          + ln.칸.map(function (c, k) {
            var t = c.text, 저 = c.conf < 70; if (저) 낮++;
            var 단 = o.읽을것 === '검사지' || o.읽을것 === '약' ? 단위.exec(t.replace(/\s+/g, '')) : null;
            if (단) return '<input class="n' + (저 ? ' low' : '') + '" data-c="' + k + '" value="' + e(단[1]) + '" aria-label="' + (r + 1) + '번째 줄 ' + (k + 1) + '번째 값' + (저 ? ' — 흐리게 읽힘' : '') + '"><input class="u' + (저 ? ' low' : '') + '" data-c="' + k + '" data-u="1" value="' + e(단[2]) + '" aria-label="단위">';
            return '<input class="' + (숫자.test(t.replace(/\s+/g, '')) ? 'n' : '') + (저 ? ' low' : '') + '" data-c="' + k + '" value="' + e(t) + '" aria-label="' + (r + 1) + '번째 줄 ' + (k + 1) + '번째 칸' + (저 ? ' — 흐리게 읽힘' : '') + '">';
          }).join('') + '</div><button type="button" class="pr-del" data-pr="del">이 줄 빼기</button></div>';
      });
      h = h.replace('<div class="pr-key">', '<p class="pr-p" style="margin:-4px 0 6px"><b>' + 지금.줄.length + '줄</b> 읽었어요' + (낮 ? ' · 흐린 칸 ' + 낮 + '개' : '') + '</p><div class="pr-key">');
    } else {
      var 표 = 지금.표, 보일 = 표.slice(0, 60);
      h += '<p class="pr-p" style="margin:-4px 0 6px"><b>' + 표.length + '줄</b>' + (지금.파일 ? ' · ' + e(지금.파일) : '') + (표.length > 60 ? ' · 앞 60줄만 고칠 수 있게 보여요(나머지도 같이 넣어요)' : '') + '</p>'
        + '<div class="pr-wrap"><table class="pr-tb"><tbody>' + 보일.map(function (row, r) { return '<tr data-r="' + r + '">' + row.map(function (v, k) { return '<td><input data-c="' + k + '" value="' + e(v) + '" aria-label="' + (r + 1) + '번째 줄 ' + (k + 1) + '번째 칸"></td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div>';
    }
    h += '<button type="button" class="pr-go" data-pr="ok">맞아요, 넣기</button><button type="button" class="pr-gh" data-pr="back">처음으로</button>';
    틀(h);
  }
  function 모으기() {
    if (지금.줄) return [].map.call(document.querySelectorAll('#pr-sh .pr-row'), function (row) {
      var 칸 = []; [].forEach.call(row.querySelectorAll('input'), function (i) { var k = +i.getAttribute('data-c'); if (i.getAttribute('data-u')) 칸[k] = (칸[k] || '') + ' ' + i.value.trim(); else 칸[k] = i.value.trim(); });
      return 칸.map(function (x) { return String(x || '').trim(); });
    }).filter(function (r) { return r.some(Boolean); });
    var 표 = 지금.표.map(function (r) { return r.slice(); });
    [].forEach.call(document.querySelectorAll('#pr-sh .pr-tb tr'), function (tr) { var r = +tr.getAttribute('data-r'); [].forEach.call(tr.querySelectorAll('input'), function (i) { 표[r][+i.getAttribute('data-c')] = i.value.trim(); }); });
    return 표;
  }
  function 넣기() {
    var 줄 = 모으기(), o = 지금.o, 값 = { 줄: 줄, 출처: 지금.출처, 파일: 지금.파일 || '', 읽을것: o.읽을것 || '표' };
    닫기();
    try { o.받기 && o.받기(값); } catch (x) { try { console.warn('사진읽기 받기', x); } catch (y) {} }
  }
  function 닫기() {
    var v = document.getElementById('pr-veil'); if (v) v.remove();
    if (지금 && 지금.캔버스) { 지금.캔버스.width = 지금.캔버스.height = 0; }
    지금 = null;   /* 사진·표를 버린다 */
  }
  function 오류(x) { 틀(머리('읽지 못했어요') + '<p class="pr-p">' + e(x && x.message ? x.message : '다시 해 주세요') + '</p><button type="button" class="pr-gh" data-pr="back">처음으로</button>'); }
  document.addEventListener('change', function (ev) {
    var t = ev.target; if (!지금 || !t || !t.closest || !t.closest('#pr-sh') || !t.files || !t.files[0]) return;
    var f = t.files[0], 이름 = f.name || '', k = t.getAttribute('data-pr'); t.value = '';
    if (k === 'file') { f.arrayBuffer().then(function (buf) { return /\.xlsx$/i.test(이름) ? xlsx읽기(buf) : csv읽기(buf); }).then(function (표) { if (!표.length) throw new Error('읽을 줄이 없어요'); 지금.표 = 표; 지금.줄 = null; 지금.출처 = /\.xlsx$/i.test(이름) ? '엑셀' : 'CSV'; 지금.파일 = 이름; 확인화면(); }, 오류); return; }
    if (k === 'img') {
      진행화면('사진 준비 중');
      사진캔버스(f).then(function (c) { 지금.캔버스 = c; 지금.출처 = '사진'; 지금.파일 = ''; return 사진읽기(c, 진행); })
        .then(function (줄) { if (!지금) return; if (!줄.length) throw new Error('글자를 찾지 못했어요 — 밝은 곳에서 표가 화면에 꽉 차게 다시 찍어 주세요'); 지금.줄 = 줄; 지금.표 = null; 확인화면(); }, 오류);
    }
  });
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('#pr-sh [data-pr]'); if (!b || !지금) return; var k = b.getAttribute('data-pr');
    if (k === 'x') 닫기(); else if (k === 'back') 첫화면(); else if (k === 'paste') 붙여넣기화면(); else if (k === 'ok') 넣기();
    else if (k === 'pasteGo') { var ta = document.querySelector('#pr-sh [data-pr="ta"]'), 표 = 표나누기(ta ? ta.value : ''); if (!표.length) { 오류(new Error('붙인 표가 비어 있어요')); return; } 지금.표 = 표; 지금.줄 = null; 지금.출처 = '붙여넣기'; 지금.파일 = ''; 확인화면(); }
    else if (k === 'del') { var row = b.closest('.pr-row'); if (row) row.remove(); }
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && document.getElementById('pr-veil')) 닫기(); });

  function 열기(o) { 닫기(); 지금 = { o: o || {} }; 첫화면(); }
  var 설치들 = [];
  function 단추달기() {
    설치들.forEach(function (o) { if (!o.자리) return; [].forEach.call(document.querySelectorAll(o.자리), function (곳) {
      if (곳.querySelector('.pr-open') || 곳.getAttribute('data-pr-no')) return;
      if (o.자리걸러 && !o.자리걸러(곳)) return;
      var b = document.createElement('button'); b.type = 'button'; b.className = (o.단추모양 || 'pr-open-def') + ' pr-open'; b.textContent = o.단추글 || '사진·파일로 읽기';
      b.addEventListener('click', function () { 열기(o); }); 곳.appendChild(b); }); });
  }
  function 설치(o) {
    설치들.push(o || {});
    if (!document.getElementById('pr-css-open')) { var s = document.createElement('style'); s.id = 'pr-css-open'; s.textContent = '.pr-open-def{width:100%;min-height:50px;border:1.5px solid var(--accent,#2F6F62);border-radius:14px;background:none;color:var(--accent-ink,var(--accent,#2F6F62));font:inherit;font-size:15px;font-weight:700;cursor:pointer}'; document.head.appendChild(s); }
    var 시작 = function () { 단추달기(); var 대 = 0; new MutationObserver(function () { if (대) return; 대 = requestAnimationFrame(function () { 대 = 0; 단추달기(); }); }).observe(document.body, { childList: true, subtree: true }); };
    if (document.body) 시작(); else document.addEventListener('DOMContentLoaded', 시작);
  }
  window.사진읽기 = { _흑백: 흑백, 설치: 설치, 열기: 열기, 닫기: 닫기, 표나누기: 표나누기, xlsx읽기: xlsx읽기, csv읽기: csv읽기, AI규칙: AI규칙, 판: 판, _OCR: OCR, _칸나누기: 칸나누기, _사진읽기: 사진읽기, _사진캔버스: 사진캔버스 };
})();
/* ▲▲ 사진읽기 부품 끝 ▲▲ */
