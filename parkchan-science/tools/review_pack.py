#!/usr/bin/env python3
"""검수용 화면 모음 PDF(2026-10-13) — 브라우저를 못 쓰는 검수자(ChatGPT 일반 대화 등)에게 올릴 화면 묶음.

review.html 로 예시 기록(9일 사용)을 넣고 학생·보호자·원장·처음 온 사람 화면을 실제로 눌러 가며 찍는다(폰 390×844).
화면마다 번호·역할·무엇을 보면 되는지를 붙여 docs/parkchan/review-screens.pdf 로 낸다. 찍다 실패한 화면은 끝에 목록으로(그것도 검수 거리).

사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/review_pack.py [--out 파일]
"""
import asyncio, sys, os, base64, html, pathlib
from playwright.async_api import async_playwright

BASE = 'http://127.0.0.1:8765/'
OUT = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'parkchan' / 'review-screens.pdf'
SHOTS, FAIL = [], []
DUMP = pathlib.Path(sys.argv[sys.argv.index('--dump') + 1]) if '--dump' in sys.argv else None   # 낱장도 남기기(자체 검수용)
if DUMP: DUMP.mkdir(parents=True, exist_ok=True)
MAXH = 2600   # 긴 화면은 위에서 이만큼(px, CSS)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')

        async def open_as(sc, dark=False):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, color_scheme='dark' if dark else 'light', locale='ko-KR', timezone_id='Asia/Seoul')
            pg = await ctx.new_page(); await pg.goto(BASE + 'review.html'); await pg.wait_for_timeout(300)
            await pg.click(f'[data-sc="{sc}"]'); await pg.wait_for_url('**/index.html', timeout=10000); await pg.wait_for_timeout(1500)
            try: await pg.evaluate('loadMore()'); await pg.wait_for_function('MORE.ok', timeout=20000)
            except Exception: pass
            return ctx, pg

        async def shot(pg, role, title, look, full=True):
            try:
                await pg.wait_for_timeout(350)
                h = await pg.evaluate('Math.min(document.scrollingElement.scrollHeight, %d)' % MAXH) if full else 844
                sheet = await pg.locator('.sheet').count() and await pg.is_visible('.sheet')
                png = await pg.screenshot(type='jpeg', quality=72, full_page=False, clip={'x': 0, 'y': 0, 'width': 390, 'height': 844}) if (sheet or not full) else \
                      await pg.screenshot(type='jpeg', quality=72, full_page=True, clip={'x': 0, 'y': 0, 'width': 390, 'height': h})
                SHOTS.append((role, title, look, base64.b64encode(png).decode()))
                if DUMP: (DUMP / f'{len(SHOTS):02d}.jpg').write_bytes(png)
            except Exception as e: FAIL.append((role, title, str(e)[:160]))

        async def step(role, title, fn):
            try: await fn()
            except Exception as e: FAIL.append((role, title, str(e).split('\n')[0][:160]))

        async def close_sheet(pg):
            try: await pg.evaluate('closeSheet()'); await pg.wait_for_timeout(250)
            except Exception: pass

        # ── 처음 온 사람 ──
        ctx, pg = await open_as('guest')
        for i in range(3):
            await shot(pg, '처음 온 사람', f'소개 {i + 1}/3', '첫 진입이 가벼운가(면책·동의 벽 없이) · 한 장 한 문장', full=False)
            await step('처음 온 사람', '소개 넘기기', lambda: pg.click('#introNext'))
        await shot(pg, '처음 온 사람', '시작 화면', '무엇을 하는 앱인지 한눈에 · 로그인/가입/둘러보기 구분')
        async def guest():
            await pg.click('#goGuest'); await pg.wait_for_timeout(900)
        await step('처음 온 사람', '둘러보기', guest); await shot(pg, '처음 온 사람', '둘러보기 · 오늘', '가입 없이 쓸 수 있는 범위 · 체험 안내가 압박스럽지 않은가')
        await step('처음 온 사람', '이용권', lambda: pg.evaluate("show('plans')")); await shot(pg, '처음 온 사람', '이용권 화면', '가격(9,900/39,000/59,000) · 자동 결제 없음 · 미성년자 취소권 고지')
        await ctx.close()

        # ── 학생 ──
        ctx, pg = await open_as('student')
        R = '학생'
        await shot(pg, R, '오늘(홈)', '하루 경로 · 과제 카드 · 공지 · 시험 D-9 한 줄 · 정보가 많아도 차분한가')
        async def read():
            await pg.click('#pRead'); await pg.wait_for_timeout(700)
        await step(R, '개념 읽기', read); await shot(pg, R, '개념 상세(오늘의 개념)', '①②③ 뼈대 · 그림 · 포인트 · 용어 · 과학 내용이 정확한가')
        async def blank():
            await pg.click('#markDone'); await pg.wait_for_timeout(300); await pg.click('#dPathGo'); await pg.wait_for_timeout(400); await pg.click('#pBlank'); await pg.wait_for_timeout(400)
        await step(R, '빈칸', blank); await shot(pg, R, '빈칸 ㉠㉡㉢ 떠올리기', '떠올린 뒤 답 보기 · 칸마다 떠올렸어요/헷갈렸어요')
        async def quiz():
            await pg.click('#bkGo'); await pg.wait_for_timeout(200); await pg.click('#bkDone'); await pg.wait_for_timeout(300); await pg.click('#goQuiz'); await pg.wait_for_timeout(500)
        await step(R, '오늘의 문제', quiz); await shot(pg, R, '오늘의 문제', '발문 16px 고딕 · 선지 · 확신/헷갈림')
        async def wrong():
            a = await pg.evaluate('qState.q.answer'); await pg.click(f'.opt[data-p="{1 if a != 1 else 2}"]'); await pg.wait_for_timeout(400)
        await step(R, '오늘의 문제 틀림', wrong); await shot(pg, R, '오늘의 문제 · 틀렸을 때', '틀려도 다그치지 않는 말투 · 해설이 정확하고 왜 갈렸는지 보이는가')
        async def review():
            await pg.click('#grade'); await pg.wait_for_timeout(500); await pg.click('#revStart'); await pg.wait_for_timeout(500)
        await step(R, '오늘의 복습', review); await shot(pg, R, '오늘의 복습(간격 복습)', '다시 볼 문제·개념 카드·지난 소단원 섞임 · 진행 막대 · 그만 풀기', full=False)
        async def rev_ans():
            q = await pg.evaluate("(() => { const q = bs.items[bs.i]; return { t:q.type, a:q.answer, n:(q.choices||[]).length }; })()")
            if q['t'] == 'card': await pg.click('#csFlip')
            elif q['t'] == 'ox': await pg.click(f'[data-ox="{q["a"]}"]')
            elif q['t'] == 'blank': await pg.fill('#blankIn', str(q['a'])); await pg.click('#blankGo')
            elif q['t'] in ('mc', 'multi'): await pg.click(f'[data-bp="{q["a"]}"]')
            await pg.wait_for_timeout(400)
        await step(R, '복습 채점', rev_ans); await shot(pg, R, '채점 시트', '아래에서 올라오는 시트 · 해설 펼치기 · 다음 문제', full=False)
        await step(R, '문제 탭', lambda: pg.evaluate("bs = null; show('bank')")); await shot(pg, R, '문제 탭', '오늘 추천 10문제 히어로 · 직접 고르기 · 실전처럼 풀기 · 탐구')
        async def multi():
            await pg.evaluate("startBank(BANK.filter(q => !isUM(q) && multiSplit(q) && multiSplit(q).rows.length === 3).slice(0, 3), '합답형')"); await pg.wait_for_timeout(500)
            if await pg.locator('.sjbox').count() == 0: await pg.click('#sjTog'); await pg.wait_for_timeout(300)
        await step(R, '합답형 하나씩', multi); await shot(pg, R, '합답형 · ㄱㄴㄷ 하나씩 판정', '보기마다 옳아요/틀려요 → 조합이 선지로')
        await step(R, '교재', lambda: pg.evaluate("bs = null; show('list')")); await shot(pg, R, '교재(목차·숙련도)', '대단원 접기 · 숙련도 네모 · 소단원 진도')
        await step(R, '이야기', lambda: pg.evaluate("show('talk')")); await shot(pg, R, '이야기(질문·자료)', '빈 상태 · 함께 쓰는 규칙 · 안전장치가 조용한가')
        await step(R, '일정', lambda: pg.evaluate("show('plan')")); await shot(pg, R, '일정', '시간표 · D-day · 시험 일정 범위')
        async def eplan():
            await pg.click('[data-ev="ev-mid"]'); await pg.wait_for_timeout(500); await pg.click('.sheet [data-eplan]'); await pg.wait_for_timeout(500)
        await step(R, '시험까지 계획', eplan); await shot(pg, R, '시험까지 계획', '남은 날 × 소단원 · 마지막 섞어 풀기 · 밀린 날 없음', full=False)
        await close_sheet(pg)
        await step(R, '공부 노트', lambda: pg.evaluate("show('note')")); await shot(pg, R, '공부 노트', '노트 3개 · 달력 · 지난 기록 한 장')
        await step(R, '내 정보', lambda: pg.evaluate("show('me')")); await shot(pg, R, '내 정보', '설정 · 보호자에게 보이는 것 · 이용권 · 약관/처리방침')
        await step(R, '통계', lambda: pg.evaluate("show('stats')")); await shot(pg, R, '학습 통계', '이번 주 리듬 · 달력 점 · 숙련도 · 소단원별 정답률')
        async def plusd():   # 2026-10-13 본책 '시험에 나오는 보강' 칸(개념 상세) · 실력 다지기 문항
            await pg.evaluate("bs = null; (() => { const i = CONCEPTS.findIndex(c => c.id === '1303-02'); dOpenSet(CONCEPTS[i].id, true); detailIdx = i; show('detail'); })()"); await pg.wait_for_timeout(700)
            if await pg.locator('#dMoreBtn').count() and await pg.get_attribute('#dMoreBtn', 'aria-expanded') != 'true': await pg.click('#dMoreBtn'); await pg.wait_for_timeout(300)
            await pg.locator('#v-detail .dplus summary').first.click(); await pg.wait_for_timeout(300)
            await pg.locator('#v-detail .dplus').scroll_into_view_if_needed(); await pg.wait_for_timeout(200)
        await step(R, '시험에 나오는 보강', plusd); await shot(pg, R, '개념 상세 · 시험에 나오는 보강', '본책 보강 쪽(완자 대조로 채운 주제)이 폰에서 읽기 좋은가 · 그림·표·한 줄 정리', full=False)
        async def upq():
            await pg.evaluate("startBank(BANK.filter(q => q.up && q.figure).slice(0, 2), '실력 다지기')"); await pg.wait_for_timeout(600)
        await step(R, '실력 다지기 문항', upq); await shot(pg, R, '문제 · 실력 다지기(자료·추론)', '머리 표시 · 그림·표 자료 · 난도가 STEP 3 다음 한 걸음인가')
        await pg.evaluate("bs = null")
        async def asg():
            await pg.evaluate("show('today')"); await pg.wait_for_timeout(500); await pg.locator('.asgcard').first.click(); await pg.wait_for_timeout(600)
        await step(R, '학원 과제', asg); await shot(pg, R, '학원 과제 풀기(이어서 4/5)', '이어 풀기 · 마감 표시', full=False)
        await ctx.close()
        ctx, pg = await open_as('student', dark=True)
        await shot(pg, R, '오늘(홈) · 어두운 화면', '어두운 화면에서 글자·카드 대비')
        await step(R, '개념 상세 어두운', read); await shot(pg, R, '개념 상세 · 어두운 화면', '그림 받침 · 글자 대비')
        await ctx.close()

        # ── 보호자 ──
        ctx, pg = await open_as('parent')
        await shot(pg, '보호자', '자녀 화면 · 이번 주 요약', '출석 · 공부한 날 · 정답률 4주 · 과제 · 선생님 한 마디 · 비교·순위 없음')
        await ctx.close()

        # ── 원장 ──
        ctx, pg = await open_as('owner')
        R = '원장'
        for tab, title, look in [('students', '학생', '처리할 것 · 수강생 등록·코드 발급 · 학생 목록'), ('attend', '출석', '4자리 숫자(30초마다 바뀜) · 오늘 출석'),
                                 ('notice', '공지', '반별 공지 · 읽음 수 · 안 읽은 학생 문자'), ('asg', '과제', '과제 내기(무엇을·누구에게·언제까지) · 제출 현황'),
                                 ('sched', '일정', '반별 일정 보내기'), ('talk', '이야기 관리', '신고 · 이용 제한 · 처리 기록'), ('stats', '통계', '반별 출석 · 학생별 · 정답률이 낮은 문항'),
                                 ('settings', '설정', '반·수업 시각 · 이용권 코드 발급 · 운영 안내')]:
            async def go(tab=tab):
                await pg.click(f'[data-adm="{tab}"]'); await pg.wait_for_timeout(800)
            await step(R, title, go); await shot(pg, R, title, look)
            if tab == 'students':
                async def stu():
                    await pg.click('[data-stu="DEMO01"]'); await pg.wait_for_timeout(800)
                await step(R, '학생 시트', stu); await shot(pg, R, '학생 시트(박○○)', '출석·진도·정답률 · 선생님 한 마디 · 정보 고치기', full=False)
                async def wsms():
                    await pg.click('#wsmsOpen'); await pg.wait_for_timeout(900)
                await step(R, '이번 주 요약 문자', wsms); await shot(pg, R, '이번 주 요약 문자', '보호자에게 보낼 글 미리 보기 · 문자/복사', full=False)
                await close_sheet(pg)
            if tab == 'students':
                async def qr():
                    await pg.click('#qrBox summary'); await pg.wait_for_timeout(500); await pg.locator('#qrBox').scroll_into_view_if_needed()
                await step(R, '학원 QR', qr); await shot(pg, R, '학원 QR(수강 등록)', 'QR·주소 · A4 포스터 · 새 QR로 바꾸기 · 명단의 앱/앱 없음 표시', full=False)
            if tab == 'asg':
                async def rep():
                    await pg.locator('[data-asgrep]').first.click(); await pg.wait_for_timeout(800)
                await step(R, '과제 보고서', rep); await shot(pg, R, '과제 보고서', '제출 n/N · 많이 틀린 문항 · 틀린 학생에게만 다시 내기', full=False)
                await close_sheet(pg)
        await ctx.close()

        # ── PDF ──
        cards = ''.join(f'''<section class="s"><div class="h"><span class="n">{i + 1}</span><b>{html.escape(r)}</b> · {html.escape(t)}</div><p class="l">볼 것: {html.escape(l)}</p>
          <img src="data:image/jpeg;base64,{d}"></section>''' for i, (r, t, l, d) in enumerate(SHOTS))
        fails = ''.join(f'<li>{html.escape(r)} · {html.escape(t)} — {html.escape(e)}</li>' for r, t, e in FAIL)
        doc = f'''<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>
          @page{{size:A4;margin:12mm}} body{{font-family:'Noto Sans KR',sans-serif;color:#1E2A2E;word-break:keep-all}}
          h1{{font-size:20pt;margin:0 0 4mm}} .lead{{font-size:10.5pt;color:#3A484D;line-height:1.7}}
          .grid{{columns:2;column-gap:8mm}} .s{{break-inside:avoid;margin:0 0 6mm}} .h{{font-size:10pt;margin-bottom:1mm}} .n{{display:inline-block;min-width:7mm;font-weight:900;color:#147D6F}}
          .l{{font-size:8.5pt;color:#566268;margin:0 0 2mm;line-height:1.5}} img{{width:100%;border:1px solid #E2DED6;border-radius:3mm}}
        </style></head><body><h1>박찬 과학 · 하루 한 개념 — 검수용 화면 모음</h1>
        <p class="lead">폰 화면(가로 390px)으로 찍었습니다. 9일 동안 쓴 예시 기록(학생 박○○ · 월목반)이 들어 있고 '오늘'은 그날 공부 전입니다. 긴 화면은 위쪽 {MAXH}px까지만 실었습니다.
        직접 눌러 볼 수 있는 곳: https://usualhealth383-cloud.github.io/autoblog/parkchan/review.html · 화면 {len(SHOTS)}장</p>
        <div class="grid">{cards}</div>{f'<h2>찍지 못한 화면</h2><ul>{fails}</ul>' if fails else ''}</body></html>'''
        ctx = await b.new_context(); pg = await ctx.new_page(); await pg.set_content(doc, wait_until='load'); await pg.wait_for_timeout(800)
        await pg.pdf(path=str(OUT), format='A4', print_background=True); await ctx.close(); await b.close()
        print(f'PACK OK {OUT.name} {OUT.stat().st_size / 1e6:.1f} MB · 화면 {len(SHOTS)} · 실패 {len(FAIL)}')
        for f in FAIL: print('  ✗', *f)

asyncio.run(main())
