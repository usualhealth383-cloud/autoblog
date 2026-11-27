// 약지도 사본 — 정본은 yozm-health _도구/세로정렬_재기.mjs(11-27). 바꾼 것: http 주소 · SEED(localStorage) · ONLY_HASH · W(폭)
// 세로 가운데 정렬 재기 — 아홉 앱 공용 (2026-11-27)
//   현욱님 11-27: 「가운데 정렬 잘해 — ClinicScore 만 봐도 세로로 너무 상단 정렬」.
//   재는 법: 보이는 칸마다 «그 칸 위쪽 빈칸»과 «아래쪽 빈칸»을 재서 차이가 4px 넘으면 흠.
//     위빈칸 = 자식들 가장 위 - 칸 위        아래빈칸 = 칸 아래 - 자식들 가장 아래
//   ⚠️ 글이 여러 줄인 본문 카드는 위 정렬이 «맞다» — 자동으로 뺀다(아래 「본문」 조건).
//   쓰임: /opt/node22/bin/node _도구/세로정렬_재기.mjs <html경로> [해시 ...]
//   예:   … _도구/세로정렬_재기.mjs med/medcalc_plus/ClinicScore_본이식.html sofa curb65
import path from 'path';
const [,, 앱, ...해시들] = process.argv;
if (!앱) { console.log('쓰임: node _도구/세로정렬_재기.mjs <html경로> [해시 ...]'); process.exit(2); }
const U = /^https?:/.test(앱) ? 앱 : 'file://' + path.resolve(앱);   // 약지도: 자료를 서버에서 읽으므로 http 주소도 받는다
const { chromium } = await import('/opt/node22/lib/node_modules/playwright/index.mjs');
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const p = await b.newPage({ viewport: { width: +(process.env.W || 390), height: 844 } });
if (process.env.SEED) await p.addInitScript(process.env.SEED);
const errs = []; p.on('pageerror', e => errs.push(String(e).slice(0, 120)));
await p.goto(U, { waitUntil: 'load' }); await p.waitForTimeout(2000);
// 첫 관문(동의·역할 고르기)이 있으면 지난다 — 앱마다 글자가 달라 넓게 집는다
for (const 말 of ['의료인', '시작하기', '동의하고 시작', '둘러보기', '확인']) {
  const el = p.locator('*').filter({ hasText: new RegExp('^' + 말 + '$') }).last();
  if (await el.count().catch(() => 0)) { await el.click({ force: true }).catch(() => {}); await p.waitForTimeout(900); break; }
}

const 재기 = async (화면) => await p.evaluate((화면) => {
  const 흠 = [];
  const 길 = e => { const a = []; let n = e, i = 0;
    while (n && n.nodeType === 1 && i++ < 3) { a.unshift(n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + (n.className && typeof n.className === 'string' ? '.' + n.className.trim().split(/\s+/).slice(0, 2).join('.') : '')); n = n.parentElement; }
    return a.join(' > '); };
  document.querySelectorAll('*').forEach(e => {
    const r = e.getBoundingClientRect();
    const cs0 = getComputedStyle(e);
    if (cs0.display === 'none' || cs0.visibility === 'hidden' || cs0.opacity === '0') return;
    if (r.height < 24 || r.width < 24) return;
    if (r.bottom < 0 || r.top > innerHeight) return;              // 화면 밖
    const cs = getComputedStyle(e);
    if (cs.overflowY === 'auto' || cs.overflowY === 'scroll') return;   // 스크롤 칸은 세로 가운데가 아니다
    if (e.scrollHeight > e.clientHeight + 2) return;              // 내용이 넘치면 남는 공간이 없다
    const kids = [...e.children].filter(k => { const kr = k.getBoundingClientRect();
      return kr.height > 0 && kr.width > 0 && getComputedStyle(k).position !== 'absolute' && getComputedStyle(k).position !== 'fixed'; });
    if (!kids.length) return;
    /* ⚠️ 자식 «요소»만 보면 틀린다 — 그 뒤에 이어지는 «글자»가 줄을 더 차지한다.
       11-27 실측: `<p class="c-used"><b>언제</b> · 긴 설명…` 이 두 줄인데 <b> 만 보고 26px 흠으로 잘못 셌다.
       Range 로 내용 «전체»의 범위를 잰다. */
    /* ⚠️ Range 를 통째로 쓰면 «화면에 안 보이는» 것에 속는다 — 11-27 실측:
       `.fd-sch` 안의 `label.sr-only`(높이 1px · margin -1px)가 범위를 늘려 8px 흠으로 잘못 셌다.
       그래서 보이는 자식 요소와 «글자 노드»만 따로 모아 잰다. */
    const 범위 = [];
    [...e.childNodes].forEach(n => {
      if (n.nodeType === 3) {
        if (!n.nodeValue.trim()) return;
        try { const rg = document.createRange(); rg.selectNodeContents(n);
          const rr = rg.getBoundingClientRect(); if (rr.height > 0) 범위.push(rr); } catch (err) {}
        return;
      }
      if (n.nodeType !== 1) return;
      const nr = n.getBoundingClientRect(), ncs = getComputedStyle(n);
      if (nr.height <= 2 || nr.width <= 2) return;                 // sr-only 같은 숨김
      if (ncs.display === 'none' || ncs.visibility === 'hidden') return;
      if (ncs.position === 'absolute' || ncs.position === 'fixed') return;
      범위.push(nr);
    });
    if (!범위.length) return;
    const 위자식 = Math.min(...범위.map(x => x.top));
    const 아래자식 = Math.max(...범위.map(x => x.bottom));
    const 위 = 위자식 - r.top, 아래 = r.bottom - 아래자식;
    if (위 < -1 || 아래 < -1) return;
    if (위 + 아래 < 8) return;                                     // 남는 공간이 거의 없다
    const 차 = Math.round(Math.abs(위 - 아래));
    if (차 <= 4) return;
    // ⚠️ 글이 여러 줄인 «본문» 칸은 위 정렬이 맞다 — 뺀다
    const 글 = (e.innerText || '').trim();
    const 줄수 = kids.reduce((a, k) => a + Math.round(k.getBoundingClientRect().height / (parseFloat(getComputedStyle(k).lineHeight) || 20)), 0);
    if (글.length > 120 || 줄수 >= 4) return;
    흠.push({ 화면, 길: 길(e), 위: Math.round(위), 아래: Math.round(아래), 차, 높이: Math.round(r.height), 글: 글.replace(/\s+/g, ' ').slice(0, 24) });
  });
  // 화면 수준 — 내용이 위에 몰리고 아래가 크게 비는가(현욱님 「세로로 너무 상단 정렬」)
  const 바닥 = (window.__bar ? window.__bar.getBoundingClientRect().top : innerHeight);
  document.querySelectorAll('.screen-page.on, #detail.on').forEach(sc => {
    const r = sc.getBoundingClientRect();
    const kids = [...sc.querySelectorAll('*')].filter(k => { const kr = k.getBoundingClientRect();
      const kcs = getComputedStyle(k);
      return kr.height > 0 && kr.width > 0 && kcs.display !== 'none' && kcs.visibility !== 'hidden'; });
    if (!kids.length) return;
    const 끝 = Math.max(...kids.map(k => k.getBoundingClientRect().bottom));
    if (sc.scrollHeight > sc.clientHeight + 2) return;            // 스크롤되면 빈 게 아니다
    const 남 = Math.round(바닥 - 끝);
    if (남 > 150) 흠.push({ 화면, 길: '[화면] ' + (sc.id || sc.className), 위: 0, 아래: 남, 차: 남, 높이: Math.round(r.height), 글: '아래가 빈다' });
  });

  // 같은 모양이 여러 번이면 한 줄로 묶는다
  const 통 = {};
  흠.forEach(x => { const k = x.화면 + '|' + x.길 + '|' + x.차; (통[k] = 통[k] || { ...x, 개수: 0 }).개수++; });
  return Object.values(통).sort((a, b2) => b2.차 - a.차);
}, 화면);

const 모음 = [];
// 바닥 막대가 있으면 탭을 돌고, 없으면 지금 화면만
const 탭수 = await p.evaluate(() => {
  const bars = [...document.querySelectorAll('nav,[class*=tab],[class*=bot],[id*=bot]')]
    .filter(e => { const r = e.getBoundingClientRect(); return r.width > 300 && r.height > 40 && r.height < 110 && r.bottom > innerHeight - 130; });
  /* ⚠️ 막대의 «직접 자식»이 탭이 아닐 수 있다(CS 는 래퍼 하나 안에 탭 다섯).
     안쪽에서 누를 수 있는 것을 찾아 센다. 그런 것이 셋 이상인 막대를 고른다. */
  const 탭들 = e => [...e.querySelectorAll('button,a,[role="tab"],[onclick]')]
    .filter(k => { const r = k.getBoundingClientRect(); return r.width > 30 && r.height > 24; });
  const 후보 = bars.map(e => ({ e, t: 탭들(e) })).filter(x => x.t.length >= 3);
  if (!후보.length) return 0;
  후보.sort((a, b) => b.e.getBoundingClientRect().bottom - a.e.getBoundingClientRect().bottom || b.t.length - a.t.length);
  window.__bar = 후보[0].e; window.__tabs = 후보[0].t; return 후보[0].t.length;
});
if (탭수 && !process.env.ONLY_HASH) {
  for (let i = 0; i < 탭수; i++) {
    await p.evaluate(i => { if (window.__tabs && window.__tabs[i]) window.__tabs[i].click(); }, i).catch(() => {});
    await p.waitForTimeout(900);
    모음.push(...await 재기('탭' + (i + 1)));
  }
} else if (!process.env.ONLY_HASH) 모음.push(...await 재기('첫 화면'));
for (const h of 해시들) {
  await p.evaluate(h => { location.hash = '#' + h; }, h); await p.waitForTimeout(1500);
  모음.push(...await 재기('#' + h));
}

const 통 = {};
모음.forEach(x => { const k = x.길 + '|' + x.차; (통[k] = 통[k] || { ...x, 곳: 0 }).곳 += x.개수; });
const 줄 = Object.values(통).sort((a, b2) => b2.차 - a.차);
console.log('■ ' + path.basename(앱) + ' — 세로 정렬 흠 ' + 줄.reduce((a, x) => a + x.곳, 0) + '곳 (모양 ' + 줄.length + ')');
줄.slice(0, 24).forEach(x => console.log('  ' + String(x.차).padStart(3) + 'px  위' + String(x.위).padStart(3) + '/아래' + String(x.아래).padStart(3) +
  '  ×' + String(x.곳).padStart(2) + '  ' + x.화면.padEnd(8) + '  ' + x.길.slice(0, 64) + (x.글 ? '  「' + x.글 + '」' : '')));
if (줄.length > 24) console.log('  … 그 밖 ' + (줄.length - 24) + ' 모양');
if (errs.length) console.log('JS 오류 ' + errs.length + ' — ' + errs[0]);
await b.close();
process.exit(0);
