#!/usr/bin/env python3
"""원장 '처리할 것' E2E — 학생 탭 맨 위 목록(벤치마크 ★6).

· 최근 7일 출석했는데 7일 동안 앱 공부 기록 없음 · 정답률이 지난주보다 20%p 이상 떨어짐 · 최근 공지 안 읽음 · 기한 지난 다시 볼 문제 30개 넘게
· 한 학생은 한 줄(이유를 모음) · 할 일 하나: 공지만 안 읽었으면 '공지 보내기'(문자), 아니면 '학생 보기'(학생 상세)
· 방금(3시간 안) 보낸 공지는 아직 묻지 않는다 · 아무도 없으면 '오늘 챙길 학생이 없습니다' · 접어 두면 다음에도 접힌 채
· 로컬: 기기 저장소에 바로 심는다 · --server: 시험대(:8767)에 서비스 키로 심고 원장 계정으로 읽는다(원장 읽기 정책 그대로)

전제: docs/parkchan 이 :8765 에 떠 있다. --server 면 tools/testbed_up.sh.   사용: python3 tools/e2e_owner_todo.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, datetime as dt, urllib.request as U
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
SRV = '--server' in sys.argv
GW = 'http://127.0.0.1:8767'
KEYS = json.loads(U.urlopen(GW + '/__anon').read()) if SRV else {}
APP = 'http://127.0.0.1:8765/index.html' + (f"?server={GW}&key={KEYS['anon']}" if SRV else '?server=')
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_owner_todo'; os.makedirs(SC, exist_ok=True)
OWNER = ('owner@parkchan.kr', 'owner-pass') if SRV else ('owner@parkchan.kr', '2580')
T = dt.datetime.now(ZoneInfo('Asia/Seoul')).date()
D = lambda n: (T - dt.timedelta(days=n)).isoformat()
NOW = dt.datetime.now(dt.timezone.utc)
AGO = lambda h: (NOW - dt.timedelta(hours=h)).isoformat().replace('+00:00', 'Z')

# 학생: 코드 → (이름, 반, 연락처)
STU = {'TODO01': ('출석만학생', '월목반', '01011112222'), 'TODO02': ('급락학생', '화금반', ''), 'TODO03': ('공지학생', '월목반', '01033334444'),
       'TODO04': ('밀린학생', '수토반', ''), 'TODO05': ('괜찮은학생', '월목반', ''), 'TODO06': ('공지만연락처없음', '월목반', '')}
PROG = {
    'TODO01': {'days': [D(10)], 'wrong': [], 'dq': {}},                                                    # 출석 O · 7일 공부 X
    'TODO02': {'days': [D(0), D(8)], 'wrong': [], 'dq': {D(1): [10, 4], D(9): [10, 9]}},                     # 90% → 40%
    'TODO03': {'days': [D(1)], 'wrong': [], 'dq': {}},                                                     # 공지만 안 읽음
    'TODO04': {'days': [D(0)], 'wrong': [{'b': f'1101-q{i}', 'iso': D(9), 'a': D(9), 'd': D(1), 'x': 1, 'k': 1} for i in range(35)], 'dq': {}},
    'TODO05': {'days': [D(0)], 'wrong': [{'b': f'1101-q{i}', 'iso': D(9), 'a': D(9), 'd': D(1), 'x': 1, 'k': 1} for i in range(30)], 'dq': {D(1): [6, 5], D(9): [6, 6]}},   # 30개는 '넘게'가 아님 · 6%p
    'TODO06': {'days': [D(2)], 'wrong': [], 'dq': {}},
}
ATT = [('TODO01', D(2)), ('TODO05', D(1))]
READ_OK = ['TODO05']                 # 월목반 공지를 읽은 학생(01·03·06 은 안 읽음)


def rest(path, body=None, method='GET', prefer='return=minimal'):
    h = {'Content-Type': 'application/json', 'apikey': KEYS['anon'], 'Authorization': 'Bearer ' + KEYS['service'], 'Prefer': prefer}
    r = U.urlopen(U.Request(GW + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method=method)).read()
    return json.loads(r) if r else None


def seed_server():
    U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    rest('/rest/v1/students', [{'code': c, 'name': n, 'cls': k, 'phone': ph, 'until': '2027-02-28'} for c, (n, k, ph) in STU.items()], 'POST')
    rest('/rest/v1/attendance', [{'code': c, 'date': d, 'time': '18:01:00'} for c, d in ATT], 'POST')
    rest('/rest/v1/progress', [{'code': c, 'state': {**p, 'at': AGO(1)}} for c, p in PROG.items()], 'POST')
    n1 = rest('/rest/v1/notices', {'cls': '월목반', 'title': '목요일 보강 안내', 'body': '7시에 시작합니다', 'at': AGO(5)}, 'POST', 'return=representation')[0]
    rest('/rest/v1/notices', {'cls': '전체', 'title': '방금 보낸 공지', 'body': '', 'at': AGO(0.1)}, 'POST')
    rest('/rest/v1/notices', {'cls': '화금반', 'title': '오래된 공지', 'body': '', 'at': AGO(24 * 20)}, 'POST')
    rest('/rest/v1/notice_reads', [{'notice_id': n1['id'], 'code': c} for c in READ_OK], 'POST')


SEED_LOCAL = """(async ([stu, prog, att, readOk, at5, at0, at20]) => { if (!localStorage.getItem('pcs.db.v2')) await DBX.removeClass('__없음__');   // 시연 저장소를 한 번 쓰게
  const d = JSON.parse(localStorage.getItem('pcs.db.v2'));
  d.students = d.students.filter(s => !s.code.startsWith('TODO')).concat(Object.entries(stu).map(([code, [name, cls, phone]]) => ({ code, name, cls, phone, until:'2027-02-28', joined:'2026-09-01' })));
  d.attendance = att.map(([code, date]) => ({ code, date, time:'18:01', late:false, manual:true }));
  Object.entries(prog).forEach(([k, p]) => { d.progress[k] = { ...p, at:at0 }; });
  const others = d.students.map(s => s.code).filter(c => !c.startsWith('TODO'));
  d.notices = [{ id:'n-now', cls:'전체', t:'방금 보낸 공지', d:'', at:at0, read:[] },
               { id:'n-5h', cls:'월목반', t:'목요일 보강 안내', d:'7시에 시작합니다', at:at5, read:[...readOk, ...others] },
               { id:'n-old', cls:'화금반', t:'오래된 공지', d:'', at:at20, read:[] }];
  localStorage.setItem('pcs.db.v2', JSON.stringify(d)); })"""


async def main():
    if SRV: seed_server()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []

        async def owner(color='light'):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=color); await ctx.add_init_script(NO_INTRO)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(700)
            if not SRV:
                await pg.evaluate(SEED_LOCAL, [STU, PROG, ATT, READ_OK, AGO(5), AGO(0.1), AGO(24 * 20)])
                await pg.reload(); await pg.wait_for_timeout(700)
            await pg.click('#goLogin'); await pg.fill('#lgEmail', OWNER[0]); await pg.fill('#lgPw', OWNER[1]); await pg.click('#lgGo'); await pg.wait_for_timeout(1200)
            assert await pg.evaluate('view') == 'admin', await pg.evaluate('view')
            await pg.wait_for_selector('#todoBox', timeout=8000)
            return pg, ctx

        o, ctx = await owner()
        box = o.locator('#todoBox'); txt = await box.inner_text()
        # 학생 탭 맨 위(등록 양식보다 앞)
        assert await o.evaluate("(() => { const t = document.getElementById('todoBox'), f = document.querySelector('#v-admin .form'); return !!(t && f && (t.compareDocumentPosition(f) & Node.DOCUMENT_POSITION_FOLLOWING)); })()"), '처리할 것이 맨 위가 아님'
        assert await box.get_attribute('open') is not None, '처음에는 펼쳐져 있어야 함'
        rows = {}
        for r in await box.locator('.todo-row').all():
            nm = (await r.locator('.nm').inner_text()).strip(); rows[nm] = (await r.locator('.why').inner_text(), r)
        names = sorted(k for k in rows)
        print('  행:', names)
        get = lambda name: next(v for k, v in rows.items() if k.startswith(name))
        assert any(k.startswith('출석만학생') for k in rows) and '앱 공부 기록 없음' in get('출석만학생')[0] and '출석 1번' in get('출석만학생')[0], rows.get('출석만학생')
        assert '목요일 보강 안내' in get('출석만학생')[0], '출석만학생: 공지 미확인도 같은 줄에 모여야 함'
        assert '90% → 이번 주 40%' in get('급락학생')[0], get('급락학생')[0]
        assert '35개' in get('밀린학생')[0], get('밀린학생')[0]
        assert get('공지학생')[0].strip() == '공지 ‘목요일 보강 안내’ 아직 안 읽음', get('공지학생')[0]
        assert not any(k.startswith('괜찮은학생') for k in rows), '읽음·공부·출석 다 한 학생(밀린 30개·6%p)이 목록에 있음'
        assert '방금 보낸 공지' not in txt and '오래된 공지' not in txt, '3시간 안 · 14일 넘은 공지는 묻지 않아야 함'
        assert all(len(v[0].split('\n')) >= 1 for v in rows.values())
        # 반 표시(이름·반) · 할 일 하나
        assert '월목반' in await get('공지학생')[1].locator('.nm').inner_text()
        for k, (why, r) in rows.items():
            assert await r.locator('.todo-act').count() == 1, k
        a = get('공지학생')[1].locator('.todo-act')
        assert (await a.inner_text()).strip() == '공지 보내기' and (await a.get_attribute('href')).startswith('sms:01033334444'), await a.get_attribute('href')
        assert '%EB%AA%A9%EC%9A%94%EC%9D%BC' in await a.get_attribute('href'), '문자 본문에 공지 제목이 없음'
        nophone = get('공지만연락처없음')[1].locator('.todo-act'); assert (await nophone.inner_text()).strip() == '공지 보내기'
        assert (await get('출석만학생')[1].locator('.todo-act').inner_text()).strip() == '학생 보기'
        # 44px 이상
        hs = await o.evaluate("[...document.querySelectorAll('#todoBox .todo-act, #todoBox summary')].map(e => e.getBoundingClientRect().height)")
        assert min(hs) >= 44, hs
        await o.screenshot(path=f'{SC}/t01_todo_light.png')
        await box.screenshot(path=f'{SC}/t01b_todo_box_light.png')
        # 학생 보기 → 학생 상세
        await get('급락학생')[1].locator('.todo-act').click(); await o.wait_for_timeout(800)
        assert '급락학생 학생' in await o.locator('.sheet').inner_text(); await o.click('#sheetClose'); await o.wait_for_timeout(300)
        # 연락처 없는 공지 → 공지 탭으로
        await o.locator('#todoBox .todo-row', has_text='공지만연락처없음').locator('.todo-act').click(); await o.wait_for_timeout(700)
        assert await o.evaluate('admTab') == 'notice', '연락처 없는 학생의 공지 보내기 → 공지 탭'
        # 접어 두기 → 다시 그려도 접힌 채
        await o.click('[data-adm="students"]'); await o.wait_for_selector('#todoBox'); await o.click('#todoBox summary'); await o.wait_for_timeout(200)
        await o.click('[data-adm="stats"]'); await o.wait_for_timeout(500); await o.click('[data-adm="students"]'); await o.wait_for_selector('#todoBox')
        assert await o.locator('#todoBox').get_attribute('open') is None, '접은 상태가 기억되지 않음'
        await o.click('#todoBox summary'); await o.wait_for_timeout(200)
        assert await o.locator('#todoBox').get_attribute('open') is not None
        # 어두운 화면
        d, dctx = await owner('dark')
        await d.screenshot(path=f'{SC}/t02_todo_dark.png'); await d.locator('#todoBox').screenshot(path=f'{SC}/t02b_todo_box_dark.png'); await dctx.close()
        # 아무도 없으면 — 학생을 모두 정리한 상태
        if SRV:
            rest('/rest/v1/notice_reads?code=like.TODO*', None, 'DELETE'); rest('/rest/v1/progress?code=like.TODO*', None, 'DELETE')
            rest('/rest/v1/attendance?code=like.TODO*', None, 'DELETE'); rest('/rest/v1/notices?title=neq.x', None, 'DELETE')
        else:
            await o.evaluate("(() => { const d = JSON.parse(localStorage.getItem('pcs.db.v2')); d.notices = []; d.attendance = []; d.progress = {}; localStorage.setItem('pcs.db.v2', JSON.stringify(d)); })()")
            await o.reload(); await o.wait_for_timeout(1200)
            if await o.evaluate('view') != 'admin': await o.evaluate("show('admin')")
        await o.click('[data-adm="stats"]'); await o.wait_for_timeout(400); await o.click('[data-adm="students"]'); await o.wait_for_selector('#todoBox')
        t2 = await o.locator('#todoBox summary').inner_text()
        assert '오늘 챙길 학생이 없습니다' in t2 and await o.locator('#todoBox .todo-row').count() == 0, t2
        await o.locator('#todoBox').screenshot(path=f'{SC}/t03_todo_empty.png')
        assert not errs, errs
        print(('SERVER ' if SRV else 'LOCAL ') + 'OWNER TODO E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
