#!/usr/bin/env python3
"""플레이 스토어 그래픽 이미지(1024×500) 시안 3장.

규격(Play Console 도움말 9866151): JPEG 또는 24비트 PNG(알파 없음) · 1024×500 · 순위·가격·할인 문구 금지 ·
아이콘과 겹치는 과한 브랜딩 피하기 · 작은 글씨 금지(폰에서 작게 보인다).
앱 화면은 store/_raw 의 실제 캡처(tools/store_shots.py)를 쓴다.
사용: python3 tools/feature_graphic.py   → store/feature/A.png · B.png · C.png
"""
import asyncio, base64, pathlib
from playwright.async_api import async_playwright
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / 'store' / '_raw', ROOT / 'store' / 'feature'; OUT.mkdir(parents=True, exist_ok=True)
img = lambda n: 'data:image/png;base64,' + base64.b64encode((RAW / f'{n}.png').read_bytes()).decode()
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@500;700;900&family=Noto+Serif+KR:wght@600;700&display=block" rel="stylesheet">'
BASE = """*{margin:0;box-sizing:border-box} body{width:1024px;height:500px;overflow:hidden;font-family:'Noto Sans KR',sans-serif;word-break:keep-all}
.phone{position:absolute;width:236px;height:472px;border-radius:30px;background:#fff;padding:7px;box-shadow:0 24px 60px rgba(8,40,36,.35)}
.phone img{width:100%;height:100%;object-fit:cover;object-position:top;border-radius:24px;display:block}"""

A = f"""{FONTS}<style>{BASE}
body{{background:linear-gradient(115deg,#0F6357 0%,#147D6F 55%,#1C9280 100%);color:#fff}}
.t{{position:absolute;left:64px;top:118px}} .k{{font-size:21px;font-weight:700;letter-spacing:.14em;color:#CFF1EA}}
h1{{font-size:62px;font-weight:900;line-height:1.18;margin:14px 0 20px;letter-spacing:-.02em}}
p{{font-size:25px;font-weight:500;color:#E3F6F2;line-height:1.5}}
.orb{{position:absolute;right:-60px;top:-80px;width:560px;height:560px;border-radius:50%;border:2px dashed rgba(255,255,255,.16)}}
</style><div class="orb"></div><div class="t"><div class="k">통합과학 · 박찬 과학</div><h1>하루 한 개념,<br>5분이면 끝</h1><p>학원 교재 그대로 · 문제 은행 1,696문항</p></div>
<div class="phone" style="right:250px;top:62px;transform:rotate(-5deg)"><img src="{img('02')}"></div>
<div class="phone" style="right:44px;top:28px;transform:rotate(4deg)"><img src="{img('03')}"></div>"""

B = f"""{FONTS}<style>{BASE}
body{{background:#FAF8F4;color:#1E2A2E}}
.band{{position:absolute;left:0;top:0;bottom:0;width:10px;background:#147D6F}}
.t{{position:absolute;left:70px;top:96px;width:470px}}
h1{{font-family:'Noto Serif KR',serif;font-size:52px;font-weight:700;line-height:1.32;letter-spacing:-.02em}}
h1 b{{color:#147D6F}}
p{{font-size:24px;font-weight:500;color:#3A484D;margin-top:22px;line-height:1.55}}
.phone{{box-shadow:0 22px 54px rgba(30,42,46,.18);border:1px solid #E2DED6}}
</style><div class="band"></div><div class="t"><h1>오늘 배운 한 가지를<br><b>내일의 실력</b>으로</h1><p>개념 · 문제 · 공부 노트를 한 앱에서</p></div>
<div class="phone" style="right:262px;top:40px"><img src="{img('02')}"></div>
<div class="phone" style="right:40px;top:40px"><img src="{img('07')}"></div>"""

C = f"""{FONTS}<style>{BASE}
body{{background:radial-gradient(circle at 78% 40%,#1C9280 0%,#0F6357 45%,#0B4A42 100%);color:#fff}}
.t{{position:absolute;left:64px;top:92px;width:560px}}
h1{{font-size:58px;font-weight:900;line-height:1.2;letter-spacing:-.02em}}
.chips{{display:flex;gap:12px;margin-top:30px;flex-wrap:wrap}}
.chip{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.28);border-radius:16px;padding:12px 18px;min-width:140px}}
.chip b{{display:block;font-size:34px;font-weight:900;line-height:1.1}} .chip span{{font-size:18px;font-weight:700;color:#CFF1EA}}
.ring{{position:absolute;right:92px;top:70px;width:360px;height:360px;border-radius:50%;border:2px solid rgba(255,255,255,.14)}}
.ring2{{position:absolute;right:30px;top:10px;width:480px;height:480px;border-radius:50%;border:2px dashed rgba(255,255,255,.1)}}
</style><div class="ring2"></div><div class="ring"></div>
<div class="t"><h1>통합과학을<br>매일 조금씩, 끝까지</h1>
<div class="chips"><div class="chip"><b>140</b><span>교재 개념</span></div><div class="chip"><b>1,696</b><span>문제 은행</span></div><div class="chip"><b>396</b><span>날마다 명언</span></div></div></div>
<div class="phone" style="right:152px;top:14px"><img src="{img('02')}"></div>"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg = await b.new_page(viewport={'width': 1024, 'height': 500}, device_scale_factor=1)
        for name, html in (('A', A), ('B', B), ('C', C)):
            await pg.set_content(html, wait_until='networkidle'); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
            assert await pg.evaluate("document.fonts.check('900 40px \"Noto Sans KR\"')"), '웹폰트가 안 들어옴'
            tmp = OUT / f'{name}.tmp.png'; await pg.screenshot(path=str(tmp))
            Image.open(tmp).convert('RGB').save(OUT / f'{name}.png', optimize=True); tmp.unlink()   # 알파 없는 24비트
        await b.close()
    for n in 'ABC':
        im = Image.open(OUT / f'{n}.png'); assert im.size == (1024, 500) and im.mode == 'RGB', (n, im.size, im.mode)
    print('그래픽 이미지 시안 3장 →', OUT)
asyncio.run(main())
