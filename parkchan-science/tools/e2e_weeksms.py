#!/usr/bin/env python3
"""원장 → 보호자 '이번 주 요약 문자'(벤치마크 ★5) — 보호자 화면과 같은 숫자 · 보호자 번호로 sms: · 고치면 링크도 바뀜 · 복사.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_weeksms.py
"""
import asyncio, sys, os, urllib.parse
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
SC = '/tmp/pcs-e2e-weeksms'; os.makedirs(SC, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); await ctx.add_init_script(NO_INTRO)
        await ctx.grant_permissions(['clipboard-read','clipboard-write'], origin='http://127.0.0.1:8765')
        o = await ctx.new_page(); errs=[]; o.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(o)
        await o.goto('http://127.0.0.1:8765/index.html'); await o.wait_for_timeout(800)
        await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', '2580'); await o.click('#lgGo'); await o.wait_for_timeout(700)
        assert await o.evaluate('view') == 'admin'
        # 이번 주 진도 심기: 공부한 날 2 · 개념 3 · 문제 10(맞힘 8) · 다시 볼 문제 · 선생님 한 마디
        await o.evaluate("""async () => { const wk = weekDays(), dq = {}, dc = {}; dq[wk[0]] = [6,5]; dq[wk[1]] = [4,3]; dc[wk[0]] = 2; dc[wk[1]] = 1;
            const st = await DBX.loadProgress('DEMO01') || {}; const L = LESSONS[0].id, q = (BANK||[]).find(x => x.lessonId === L) || {};
            await DBX.saveProgress('DEMO01', { ...st, days:[wk[0], wk[1]], dq, dc, wrong:[{ id:q.id || (L+'-q1'), l:L, d:wk[1] }] });
            await DBX.updateStudent('DEMO01', { phone:'010-1234-5678' });
            await DBX.noteSave({ date:todayISO(), body:'공부 노트', parts:['공부 노트'], tpl:'line3' });   // 2026-10-13: 로컬 DB 에 공부 노트가 있으면 한 마디가 안 남던 것(d.notes 겸용)
            await DBX.noteSet('DEMO01', '이번 주 원자 구조를 끝까지 붙잡았어요.'); }""")
        await o.click('[data-stu="DEMO01"]'); await o.wait_for_timeout(600)
        await o.click('#wsmsOpen'); await o.wait_for_timeout(900)
        t = await o.input_value('#wsmsText')
        for k in ['박○○ 학생 이번 주', '공부한 날 2/7일', '개념 3개', '문제 10개(정답률 80%)', '선생님 한 마디: 이번 주 원자 구조', "앱 '자녀' 화면"]:
            assert k in t, (k, t)
        for bad in ['순위', '평균', '연속', '노트']: assert bad not in t, (bad, t)
        await o.screenshot(path=f'{SC}/w1_sheet.png')
        href = await o.get_attribute('#wsmsGo', 'href'); assert href.startswith('sms:') and urllib.parse.unquote(href.split('body=')[1]) == t, href[:120]
        sheet = await o.locator('.sheet').inner_text(); assert '학생 연락처 010-1234-5678' in sheet and '보호자 번호가 없어요' in sheet, sheet
        assert href.startswith('sms:010-1234-5678'), href[:40]
        # 고치면 링크 글도 바뀐다
        await o.fill('#wsmsText', t + '\n다음 주에 뵐게요.'); href2 = await o.get_attribute('#wsmsGo', 'href')
        assert urllib.parse.unquote(href2.split('body=')[1]).endswith('다음 주에 뵐게요.'), href2[-60:]
        await o.click('#wsmsCopy'); await o.wait_for_timeout(300)
        assert (await o.evaluate('navigator.clipboard.readText()')).endswith('다음 주에 뵐게요.')
        assert not errs, errs
        print('WEEKSMS OK'); await b.close()
asyncio.run(main())
