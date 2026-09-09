#!/usr/bin/env python3
"""플레이 스토어 등록용 스크린샷 8장을 만든다 (1080×1920, 9:16).

앱 화면을 그대로 찍은 뒤, 브랜드 배경 위에 기기 틀과 한 줄 설명을 얹는다.
사용: python3 tools/store_shots.py        (앱이 http://127.0.0.1:8765 에 떠 있어야 한다)
결과: store/screenshots/01~08.png
"""
import asyncio, pathlib, sys
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'store' / 'screenshots'; OUT.mkdir(parents=True, exist_ok=True)
RAW = ROOT / 'store' / '_raw'; RAW.mkdir(parents=True, exist_ok=True)
SANS = '/root/.fonts/NotoSansKR.ttf'
W, H = 1080, 1920
BRAND, DARK, PAPER, INK, MUTED = (20,125,111), (15,99,87), (250,248,244), (30,42,46), (107,122,128)

SHOTS = [
    ('01', '하루 한 개념, 5분이면 끝', '학원 교재를 그대로 옮겼습니다'),
    ('02', '오늘 배울 개념 하나', '읽고, 빈칸을 채우고, 문제를 풉니다'),
    ('03', '문제 은행 1,695문항', '범위와 유형을 골라 원하는 만큼'),
    ('04', '틀린 이유까지 알려 줍니다', '오답은 3일 뒤 한 번 더'),
    ('05', '학원·학교·과외를 한 곳에', '시험 범위에서 바로 문제 풀기'),
    ('06', '서로 묻고 답하는 이야기', '닉네임으로, 안전하게'),
    ('07', '오늘의 한 마디', '출처를 밝힌 글귀와 그날의 과학'),
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
        pg = await ctx.new_page()
        pg.on('dialog', lambda dlg: asyncio.ensure_future(dlg.accept()))
        async def fresh(who='student'):
            await pg.evaluate("['pcs.v2','pcs.local.sid','pcs.session'].forEach(k=>localStorage.removeItem(k))")
            await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(700)
            if who:
                await pg.click('#goLogin'); await pg.click(f'[data-demo^="{who}"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(3000)
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(900)
        await pg.screenshot(path=RAW/'01.png')
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
        await pg.click('.tab[data-v="today"]'); await pg.wait_for_timeout(600)
        await pg.evaluate("document.querySelector('.qsay').scrollIntoView({block:'center'})"); await settle(pg, 400)
        await pg.screenshot(path=RAW/'07.png')
        await fresh('owner'); await settle(pg); await pg.screenshot(path=RAW/'08.png')
        await b.close()

async def main():
    await capture()
    for num, title, sub in SHOTS:
        compose(RAW/f'{num}.png', OUT/f'{num}.png', title, sub)
    print(f'스토어 스크린샷 {len(SHOTS)}장 → {OUT}')
asyncio.run(main())
