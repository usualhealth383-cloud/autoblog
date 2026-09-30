#!/usr/bin/env python3
"""플레이 스토어 등록용 스크린샷 8장을 만든다 (1080×1920, 9:16).

앱 화면을 그대로 찍은 뒤, 브랜드 배경 위에 기기 틀과 한 줄 설명을 얹는다.
사용: python3 tools/store_shots.py        (앱이 http://127.0.0.1:8765 에 떠 있어야 한다)
결과: store/screenshots/01~08.png
"""
import asyncio, pathlib, sys
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from _ui import auto_yes
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'store' / 'screenshots'; OUT.mkdir(parents=True, exist_ok=True)
RAW = ROOT / 'store' / '_raw'; RAW.mkdir(parents=True, exist_ok=True)
SANS = '/root/.fonts/NotoSansKR.ttf'
W, H = 1080, 1920
BRAND, DARK, PAPER, INK, MUTED = (20,125,111), (15,99,87), (250,248,244), (30,42,46), (107,122,128)

SHOTS = [
    ('01', '하루 한 개념, 5분이면 끝', '학원 교재 그대로 · 매일 다른 한 마디'),
    ('02', '오늘 배울 개념 하나', '읽고, 빈칸을 채우고, 문제를 풉니다'),
    ('03', '문제 은행 1,695문항', '범위와 유형을 골라 원하는 만큼'),
    ('04', '틀린 이유까지 알려 줍니다', '오답은 3일 뒤 한 번 더'),
    ('05', '학원·학교·과외를 한 곳에', '시험 범위에서 바로 문제 풀기'),
    ('06', '서로 묻고 답하는 이야기', '닉네임으로, 안전하게'),
    ('07', '공부한 내용은 노트로', '달력에서 다시 보는 나만의 요약'),
    ('08', '보호자도 원장님도 같은 앱', '출석·진도·공지를 한눈에'),
]

def compose(raw_path, out_path, title, sub):
    bg = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(bg)
    for y in range(560):                                   # 위쪽에 브랜드 색을 옅게 깐다
        k = 1 - y / 560
        d.line([(0, y), (W, y)], fill=tuple(int(p + (q - p) * k) for p, q in zip(PAPER, BRAND)))
    ft = ImageFont.truetype(SANS, 62); fs = ImageFont.truetype(SANS, 34)
    ft.set_variation_by_name('Black'); fs.set_variation_by_name('Medium')   # 가변 폰트라 굵기를 지정해야 한다
    d.text((W//2, 132), title, font=ft, fill=(255,255,255), anchor='mm')
    d.text((W//2, 205), sub,   font=fs, fill=(226,240,236), anchor='mm')

    shot = Image.open(raw_path).convert('RGB')
    tw = 760                                                # 기기 틀 너비
    th = int(shot.height * tw / shot.width)
    maxh = H - 300 - 60
    if th > maxh: th = maxh; tw = int(shot.width * th / shot.height)
    shot = shot.resize((tw, th), Image.LANCZOS)
    x, y = (W - tw)//2, 300
    pad, rad = 14, 46
    sh = Image.new('RGBA', (tw + pad*2 + 40, th + pad*2 + 40), (0,0,0,0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 26, tw + pad*2 + 20, th + pad*2 + 26], rad, fill=(30,42,46,46))
    bg.paste(Image.alpha_composite(bg.crop((x-pad-20, y-pad-20, x-pad-20+sh.width, y-pad-20+sh.height)).convert('RGBA'), sh).convert('RGB'), (x-pad-20, y-pad-20))
    frame = Image.new('RGB', (tw + pad*2, th + pad*2), (255,255,255))
    mask = Image.new('L', frame.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0,0,frame.size[0]-1,frame.size[1]-1], rad, fill=255)
    inner = Image.new('L', shot.size, 0); ImageDraw.Draw(inner).rounded_rectangle([0,0,tw-1,th-1], rad-10, fill=255)
    frame.paste(shot, (pad, pad), inner)
    bg.paste(frame, (x-pad, y-pad), mask)
    bg.save(out_path, quality=95)

async def settle(pg, ms=700):
    """토스트가 남아 있으면 스토어 사진에 찍힌다 — 사라질 때까지 기다린다."""
    await pg.wait_for_timeout(ms)
    for _ in range(12):
        if not await pg.locator('.toast').count(): return
        await pg.wait_for_timeout(300)

async def capture():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':780}, device_scale_factor=2)
        await ctx.add_init_script("try { if (!localStorage.getItem('pcs.v2')) localStorage.setItem('pcs.v2', JSON.stringify({ introSeen: true })); } catch (e) {}")   # 첫 실행 소개는 건너뛴다
        pg = await ctx.new_page()
        await auto_yes(pg)
        async def fresh(who='student'):
            await pg.evaluate("['pcs.v2','pcs.local.sid','pcs.session'].forEach(k=>localStorage.removeItem(k))")
            await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(700)
            if who:
                await pg.click('#goLogin'); await pg.click(f'[data-demo^="{who}"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(3000)
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(900)
        await pg.screenshot(path=RAW/'01.png')
        await pg.evaluate("DBX.addClass('임시', '19:00').then(() => DBX.removeClass('임시'))")   # 기기 안 DB 를 저장소에 한 번 쓰게 한다
        await pg.evaluate("""(()=>{ const d = JSON.parse(localStorage.getItem('pcs.db.v2')); const ago = h => new Date(Date.now() - h*36e5).toISOString();
          const P = (id, nick, board, title, body, h, extra={}) => ({ id, uid:'demo-'+id, nick, board, title, body, at:ago(h), likes:[], reports:[], solved:false, deleted:false, staff:false, ...extra });
          d.posts = [
            P('p1', '충격량파이터', 'qna', '충격량이랑 운동량 변화량이 왜 같은 건가요?', '교재 III-1에서 F×Δt = Δp 라고 하는데 그림으로 이해가 잘 안 돼요', 3, { solved:true }),
            P('p2', '원소수집가', 'share', '산화·환원 한 줄로 외우는 법', '산소를 얻으면 산화, 전자를 잃으면 산화! "잃산얻환" 으로 외웠어요', 9),
            P('p3', '새벽공부', 'talk', '모의고사 끝났다 다들 수고했어요', '과학 그래프 문제 너무 어려웠는데 자료 탐구 한 번 더 보려고요', 20) ];
          d.comments = [
            { id:'c1', postId:'p1', uid:'a-owner', nick:'원장님', body:'힘-시간 그래프 아래 넓이가 충격량이고, 그게 곧 운동량의 변화량이에요. 에어백은 시간을 늘려 힘을 줄입니다.', at:ago(2), likes:['x','y'], reports:[], picked:true, deleted:false, staff:true },
            { id:'c2', postId:'p1', uid:'demo-u2', nick:'원소수집가', body:'저도 이거 헷갈렸는데 그래프 넓이로 보니까 이해돼요', at:ago(1), likes:[], reports:[], picked:false, deleted:false, staff:false },
            { id:'c3', postId:'p2', uid:'demo-u3', nick:'새벽공부', body:'오 이거 좋다 저장!', at:ago(5), likes:[], reports:[], picked:false, deleted:false, staff:false } ];
          d.posts[0].likes = ['a','b','c','d']; d.posts[1].likes = ['a','b','c','d','e','f','g'];
          localStorage.setItem('pcs.db.v2', JSON.stringify(d)); })()""")
        await fresh()
        await settle(pg); await pg.screenshot(path=RAW/'02.png')
        await pg.click('.tab[data-v="bank"]'); await settle(pg); await pg.screenshot(path=RAW/'03.png')
        await pg.click('#bankStart'); await pg.wait_for_timeout(600)
        ans = await pg.evaluate('bs.items[bs.i].answer')
        wrong = 'X' if ans == 'O' else 'O'
        if await pg.locator('[data-ox]').count(): await pg.click(f'[data-ox="{wrong}"]')
        elif await pg.locator('[data-bp]').count(): await pg.click('[data-bp="1"]')
        await settle(pg); await pg.screenshot(path=RAW/'04.png')
        await pg.click('#bankQuit'); await pg.wait_for_timeout(300)
        # 일정: 시간표·D-day·시험을 채워 실제로 쓰는 화면을 보여 준다
        await pg.evaluate("""(()=>{ const u=()=>Math.random().toString(36).slice(2,8);
          S.sched.fixed=[{id:u(),title:'박찬 과학 월목반',place:'2층 A강의실',tag:'academy',days:[1,4],from:'19:00',to:'22:00'},
                         {id:u(),title:'○○고 2학년',tag:'school',days:[1,2,3,4,5],from:'08:20',to:'16:40'}];
          S.sched.ddays=[{id:u(),title:'2학기 중간고사',date:'2026-10-14'}];
          S.sched.events=[{id:u(),title:'2학기 중간고사 · 통합과학',date:'2026-10-14',kind:'exam',from:'',memo:'II~III단원',scope:{book:'1',unit:'III',lesson:'1304'}}];
          save(S); })()""")
        await pg.click('.tab[data-v="plan"]'); await settle(pg); await pg.screenshot(path=RAW/'05.png')
        await pg.click('.tab[data-v="talk"]'); await settle(pg); await pg.screenshot(path=RAW/'06.png')
        # 공부 노트: 오늘 정리 한 편 + 지난 며칠의 노트(달력 점) — 달 중간처럼 보이게 이 장면만 날짜를 10월 20일로
        await pg.clock.set_fixed_time('2026-10-20T19:30:00+09:00')
        await pg.evaluate("""(()=>{ const t = todayISO(), c = CONCEPTS.find(x => x.title.includes('충격량')) || CONCEPTS[0];
          const mk = (d, title, body, cids) => putNote({ id:newId(), date:d, title, body, cids });
          [-6,-5,-4,-2,-1,0].forEach(k => { const d = addDays(t,k); if (!S.days.includes(d)) S.days.push(d); }); save(S);
          mk(addDays(t,-6), '원소의 주기성', '같은 족 = 원자가 전자 수가 같다 → 화학적 성질이 비슷', []);
          mk(addDays(t,-4), '', '모의고사 과학 42점 → 틀린 5문제 중 3개가 그래프 해석. 주말에 자료 탐구 다시.', []);
          mk(addDays(t,-2), '산화·환원', '산소를 얻으면 산화, 잃으면 환원 · 전자를 잃으면 산화', []);
          mk(t, c.title + ' 정리', '오늘 배운 것\\n· 충격량 = 힘 × 시간 = 운동량의 변화량\\n\\n헷갈린 것\\n· 에어백은 힘을 줄이는 게 아니라 시간을 늘린다\\n\\n다음에 할 것\\n· 문제 은행 III-1 10문제', [c.id]);
        })()""")
        await pg.evaluate("openNotes('today', todayISO())"); await settle(pg, 500)
        await pg.screenshot(path=RAW/'07.png')
        await fresh('owner'); await settle(pg); await pg.screenshot(path=RAW/'08.png')
        await b.close()

async def main():
    await capture()
    for num, title, sub in SHOTS:
        compose(RAW/f'{num}.png', OUT/f'{num}.png', title, sub)
    print(f'스토어 스크린샷 {len(SHOTS)}장 → {OUT}')
asyncio.run(main())
