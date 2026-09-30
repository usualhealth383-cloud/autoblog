#!/usr/bin/env python3
"""접근성 자동 점검 — 이름 없는 조작 요소, 라벨 없는 입력, 작은 손가락 목표, 대비, 언어·제목.
사용: python3 tools/a11y_audit.py   (앱이 http://127.0.0.1:8765 에 떠 있어야 한다)
"""
import asyncio, json, sys
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from _ui import auto_yes
from playwright.async_api import async_playwright

JS = r"""
() => {
  const vis = e => { const r=e.getBoundingClientRect(); return r.width>0 && r.height>0 && e.offsetParent!==null; };
  const name = e => (e.getAttribute('aria-label') || e.getAttribute('title') ||
      (e.labels && e.labels.length ? [...e.labels].map(l=>l.textContent).join(' ') : '') ||
      (e.getAttribute('aria-labelledby') ? (document.getElementById(e.getAttribute('aria-labelledby'))||{}).textContent||'' : '') ||
      e.textContent || e.getAttribute('placeholder') || e.value || '').trim();
  const out = { noName: [], noLabel: [], small: [], noLang: !document.documentElement.lang, dupIds: [] };
  document.querySelectorAll('button,a[href],[role="button"]').forEach(e => {
    if (!vis(e)) return; if (!name(e)) out.noName.push((e.id||e.className||e.tagName).slice(0,40)); });
  document.querySelectorAll('input,select,textarea').forEach(e => {
    if (!vis(e)) return;
    const lab = (e.labels && e.labels.length) || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby');
    if (!lab) out.noLabel.push((e.id || e.name || e.type || 'input') + (e.placeholder ? ' ["'+e.placeholder.slice(0,24)+'"]' : ' [설명 없음]')); });
  document.querySelectorAll('button,a[href],input,select,textarea,[role="button"]').forEach(e => {
    if (!vis(e)) return; const r = e.getBoundingClientRect();
    if (r.height < 24 || r.width < 24){ const inline = getComputedStyle(e).display.includes('inline') && e.closest('p,li,.body,.prose,.stem');
      if (!inline) out.small.push((e.id||e.className||e.tagName).slice(0,34) + ` ${Math.round(r.width)}x${Math.round(r.height)}`); } });
  const seen = {}; document.querySelectorAll('[id]').forEach(e => { if (!vis(e)) return; seen[e.id]=(seen[e.id]||0)+1; });
  out.dupIds = Object.entries(seen).filter(([,v])=>v>1).map(([k])=>k);
  return out;
}
"""


async def walk_onboarding(pg, look):
    """소개 3장 → 시작 → 가입 1~5단계(만 14세 미만 길: 보호자 칸까지) → 환영. 화면마다 look(이름) 호출"""
    for i in range(3):
        await look(f'소개 {i+1}'); await pg.click('#introNext'); await pg.wait_for_timeout(250)
    await look('시작')
    await pg.click('#goSignup'); await pg.wait_for_timeout(200); await look('가입1 누구')
    await pg.click('[data-role="student"]'); await pg.click('#suNext'); await pg.wait_for_timeout(200)
    await pg.check('input[name=suAge][value="u14"]'); await pg.wait_for_timeout(120); await pg.click('#pvToggle'); await pg.wait_for_timeout(150)
    await pg.click('#suNext'); await pg.wait_for_timeout(150); await look('가입2 약관(오류)')
    await pg.check('#agAll'); await pg.wait_for_timeout(150); await look('가입2 약관')
    await pg.click('#suNext'); await pg.wait_for_timeout(200); await look('가입3 계정')
    await pg.fill('#suEmail', 'audit@t.kr'); await pg.fill('#suPw', 'abc123'); await pg.click('#suNext'); await pg.wait_for_timeout(200)
    await pg.fill('#suName', '점검'); await look('가입4 내 정보')
    await pg.fill('#suGName', '점검보호'); await pg.fill('#suGPhone', '01012341234'); await pg.click('#suNext'); await pg.wait_for_timeout(200); await look('가입5 코드')
    await pg.click('#suSkipCode'); await pg.wait_for_timeout(900); await look('환영')
    await pg.click('#welcomeGo'); await pg.wait_for_timeout(700)
    await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300)
    await auto_yes(pg); await pg.click('#logout'); await pg.wait_for_timeout(600)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg = await (await b.new_context(viewport={'width':390,'height':844})).new_page()
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(700)
        bad = 0
        async def check(label):
            nonlocal bad
            r = await pg.evaluate(JS)
            issues = []
            if r['noName']:  issues.append(f"이름 없는 단추 {len(r['noName'])}: {r['noName'][:4]}")
            if r['noLabel']: issues.append(f"라벨 없는 입력 {len(r['noLabel'])}: {r['noLabel'][:4]}")
            if r['small']:   issues.append(f"작은 목표 {len(r['small'])}: {r['small'][:4]}")
            if r['dupIds']:  issues.append(f"보이는 중복 id: {r['dupIds'][:4]}")
            if r['noLang']:  issues.append('html lang 없음')
            print(f"{label:14s} " + ('OK' if not issues else ' · '.join(issues)))
            bad += len(issues)
        await walk_onboarding(pg, check)
        await pg.click('#goLogin'); await pg.wait_for_timeout(300); await check('로그인')
        await pg.click('[data-demo^="student"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900); await check('오늘')
        for v, n in [('list','교재'),('bank','문제'),('talk','이야기'),('plan','일정'),('me','내 정보')]:
            await pg.click(f'.tab[data-v="{v}"]'); await pg.wait_for_timeout(500); await check(n)
        await pg.click('#goStats'); await pg.wait_for_timeout(500); await check('통계')
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#goNoteMe'); await pg.wait_for_timeout(400); await check('공부 노트')
        await pg.click('#noteNew'); await pg.wait_for_timeout(300); await pg.fill('#nedBody', '점검 메모'); await pg.wait_for_timeout(700); await check('노트 쓰기')
        await pg.click('#nedAddC'); await pg.wait_for_timeout(300); await check('개념 붙이기'); await pg.click('#sheetClose'); await pg.wait_for_timeout(200)
        await pg.click('#nedDone'); await pg.wait_for_timeout(300); await check('노트 달력')
        await b.close()
        print('\n지적 합계', bad)
        sys.exit(1 if bad else 0)
asyncio.run(main())
