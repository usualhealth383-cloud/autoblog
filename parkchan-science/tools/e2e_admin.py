#!/usr/bin/env python3
"""원장 운영 도구 E2E — 학생 정보 고치기·수강 연장(한 명/반 전체)·계정 연결 풀기·출석 취소·공지 삭제·출석부 내려받기·오류 기록.

전제: docs/parkchan 이 :8765 에 떠 있다. --server 면 tools/testbed_up.sh 시험대(:8767)에 붙는다.
사용: python3 tools/e2e_admin.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, datetime as dt, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes
SRV = '--server' in sys.argv
GW = 'http://127.0.0.1:8767'
APP = 'http://127.0.0.1:8765/index.html' + (f"?server={GW}&key={json.loads(U.urlopen(GW + '/__anon').read())['anon']}" if SRV else '?server=')
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_admin'; os.makedirs(SC, exist_ok=True)
OWNER = ('owner@parkchan.kr', 'owner-pass') if SRV else ('owner@parkchan.kr', '2580')


async def main():
    if SRV: U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 400, 'height': 820}, accept_downloads=True); await ctx.add_init_script(NO_INTRO); o = await ctx.new_page()
        o.on('pageerror', lambda e: errs.append(str(e)))
        o.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
        await auto_yes(o)
        await o.goto(APP); await o.wait_for_timeout(700)
        async def login(em, pw):
            await o.click('#goLogin'); await o.fill('#lgEmail', em); await o.fill('#lgPw', pw); await o.click('#lgGo'); await o.wait_for_timeout(900)
        async def logout():
            await o.click('.tab[data-v="me"]'); await o.wait_for_timeout(300); await o.click('#logout'); await o.wait_for_timeout(600)
        await login(*OWNER); assert await o.evaluate('view') == 'admin'
        # 학생 둘 등록
        for nm in ('운영학생', '둘째학생'):
            await o.fill('#stName', nm); await o.select_option('#stCls', '월목반'); await o.fill('#stUntil', '2026-12-31'); await o.click('#stAdd'); await o.wait_for_timeout(600)
        code = await o.evaluate('issued.code')
        codes = await o.evaluate("DBX.students().then(r=>r.filter(s=>s.name==='운영학생'||s.name==='둘째학생').map(s=>s.code))")
        c1 = [c for c in codes if c != code][0]
        # ① 한 명 고치기: 이름·반·연락처 + '+3개월'
        await o.click(f'[data-stu="{c1}"]'); await o.wait_for_timeout(700)
        await o.click('.sheet .stuedit summary'); await o.fill('#seName', '운영학생(고침)'); await o.select_option('#seCls', '화금반'); await o.fill('#sePhone', '01012345678')
        await o.click('[data-seplus="3"]'); assert await o.input_value('#seUntil') == '2027-03-31', await o.input_value('#seUntil')
        await o.screenshot(path=f'{SC}/a01_student_edit.png'); await o.click('#seSave'); await o.wait_for_timeout(700)
        st = await o.evaluate(f"DBX.students().then(r=>r.find(s=>s.code==='{c1}'))")
        assert st['name'] == '운영학생(고침)' and st['cls'] == '화금반' and st['until'] == '2027-03-31' and st['phone'] == '01012345678', st
        # ② 반 전체 연장: 월목반 → 2027-02-28 (먼저 끝나는 학생만)
        await o.click('#v-admin details:has(#exCls) summary'); await o.select_option('#exCls', '월목반'); await o.fill('#exUntil', '2027-02-28'); await o.click('#exGo'); await o.wait_for_timeout(800)
        st2 = await o.evaluate(f"DBX.students().then(r=>r.find(s=>s.code==='{code}'))"); assert st2['until'] == '2027-02-28', st2
        st1 = await o.evaluate(f"DBX.students().then(r=>r.find(s=>s.code==='{c1}'))"); assert st1['until'] == '2027-03-31', '다른 반·더 긴 학생까지 바뀜'
        # ③ 수동 출석 → 학생 상세에서 취소
        await o.click('[data-adm="attend"]'); await o.wait_for_timeout(900); await o.click(f'[data-manual="{code}"]'); await o.wait_for_timeout(800)
        await o.click('[data-adm="students"]'); await o.wait_for_timeout(600); await o.click(f'[data-stu="{code}"]'); await o.wait_for_timeout(800)
        assert await o.locator('[data-attcancel]').count() == 1; await o.click('[data-attcancel]'); await o.wait_for_timeout(900)
        assert await o.locator('[data-attcancel]').count() == 0 and '출석 기록이 없습니다' in await o.locator('.sheet').inner_text(), '출석 취소 실패'
        await o.click('#sheetClose')
        # ④ 공지 보내고 지우기
        await o.click('[data-adm="notice"]'); await o.wait_for_timeout(500); await o.fill('#ntT', '지울 공지'); await o.click('#ntSend'); await o.wait_for_timeout(700)
        assert await o.locator('.sent').count() == 1; await o.click('[data-ntdel]'); await o.wait_for_timeout(700); assert await o.locator('.sent').count() == 0, '공지 삭제 실패'
        # ⑤ 출석부 내려받기(오늘 출석 1건을 다시 넣고)
        await o.click('[data-adm="attend"]'); await o.wait_for_timeout(900); await o.click(f'[data-manual="{code}"]'); await o.wait_for_timeout(800)
        await o.click('[data-adm="stats"]'); await o.wait_for_timeout(900)
        async with o.expect_download() as dl: await o.click('#attCsv')
        f = await dl.value; path = f'{SC}/{f.suggested_filename}'; await f.save_as(path)
        raw = open(path, 'rb').read(); assert raw.startswith(b'\xef\xbb\xbf'), '엑셀용 BOM 없음'
        rows = raw.decode('utf-8-sig').splitlines(); d = dt.date.today()
        assert rows[0].startswith('반,이름,코드,') and rows[0].endswith(',출석,지각'), rows[0]
        line = [r for r in rows if code in r][0]; assert ('출석 ' in line or '지각 ' in line) and line.split(',')[-2] == '1', line
        print('  출석부:', f.suggested_filename, len(rows) - 1, '명')
        await o.screenshot(path=f'{SC}/a02_stats.png')
        # ⑤-2 여러 명 한꺼번에: 엑셀 붙여 넣기(탭) · 쉼표 · 제목 줄 · 없는 반 · 이미 있는 학생
        await o.click('[data-adm="students"]'); await o.wait_for_timeout(700)
        await o.click('#bulkBox summary')
        await o.fill('#bulkIn', '이름\t반\t연락처\n일괄하나\t월목반\t010-1111-0001\n일괄둘, 화금반, 01011110002\n없는반학생, 토요반, \n운영학생(고침)\t화금반\t')
        await o.fill('#bulkUntil', '2027-08-31'); await o.click('#bulkCheck'); await o.wait_for_timeout(700)
        t = await o.locator('#bulkBox').inner_text()
        assert '2명 등록 준비' in t and '2줄 확인 필요' in t and '제목 줄' in t and "'토요반' 반이 없습니다" in t and '이미 있는 학생' in t, t[:400]
        await o.screenshot(path=f'{SC}/a04_bulk_preview.png', full_page=True)
        await o.click('#bulkGo'); await o.wait_for_timeout(2000)
        t = await o.locator('#bulkBox').inner_text(); assert '2명의 코드를 만들었습니다' in t, t[:300]
        assert await o.locator('#bulkBox a.mini[href^="sms:"]').count() == 2
        async with o.expect_download() as dl: await o.click('#bulkCsv')
        f = await dl.value; raw = open(await f.path(), 'rb').read().decode('utf-8-sig').splitlines()
        assert raw[0] == '이름,반,연락처,코드,만료일' and len(raw) == 3 and all(r.endswith(',2027-08-31') for r in raw[1:]), raw
        st = await o.evaluate("DBX.students().then(r=>r.filter(s=>s.name.startsWith('일괄')).map(s=>s.cls+':'+s.until).sort())")
        assert st == ['월목반:2027-08-31', '화금반:2027-08-31'], st
        await o.click('#bulkReset'); await o.wait_for_timeout(500)
        # ⑥ 학생 계정 연결 풀기: 학생 A 가 코드를 쓰고 있으면 B 는 막힘 → 원장이 풀면 B 가 등록
        await logout()
        for em in ('ka@t.kr', 'kb@t.kr'):
            await signup(o, em[:2], em, code=code)
            if em == 'kb@t.kr': assert await o.evaluate('S.auth') is None, '같은 코드가 두 번째 계정에도 연결됨'
            await logout()
        await login(*OWNER); await o.click(f'[data-stu="{code}"]'); await o.wait_for_timeout(800)
        assert '학생 앱 연결됨' in await o.locator('.sheet').inner_text(); await o.click('.sheet .stuedit summary'); await o.click('#seRelease'); await o.wait_for_timeout(900)
        assert '아직 연결 전' in await o.locator('.sheet').inner_text(), '연결 풀기 실패'
        await o.click('#sheetClose'); await logout(); await login('kb@t.kr', 'pass1234')
        await o.click('.tab[data-v="me"]'); await o.wait_for_timeout(300); await o.fill('#codeIn', code); await o.click('#codeGo'); await o.wait_for_timeout(900)
        assert await o.evaluate('S.auth && S.auth.code') == code, '풀어 준 뒤에도 새 계정이 등록 못 함'
        # ⑦ 오류 기록이 원장 설정에 보인다
        await o.evaluate("DBX.logError({ ver:CFG.version, msg:'TypeError: 시험용 오류', stack:'', url:'x', ua:'e2e' })")
        await logout(); await login(*OWNER); await o.click('[data-adm="settings"]'); await o.wait_for_timeout(900)
        assert '시험용 오류' in await o.locator('#v-admin').inner_text(), '오류 기록이 원장에게 안 보임'
        await o.screenshot(path=f'{SC}/a03_settings_errors.png', full_page=True)
        assert not errs, errs
        print(('SERVER ' if SRV else 'LOCAL ') + 'ADMIN E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
