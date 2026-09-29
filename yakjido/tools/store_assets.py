#!/usr/bin/env python3
"""구글 플레이 등록용 그림 — 휴대폰 화면 6장(1080×1920) + 대표 이미지(1024×500) + 앱 아이콘(512×512).

실제 앱(docs/yakjido)을 브라우저로 열어 찍고, 위에 한 줄 설명을 얹는다. 화면 속 약·기록은 «예시»다.
설명 문구는 앱이 실제로 하는 것만 쓴다(과장 금지 — 스토어 정책·의료 광고 기준).
사용: python3 yakjido/tools/store_assets.py   → yakjido/store/*.png
"""
import base64, functools, http.server, json, pathlib, socketserver, threading
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT.parent / 'docs' / 'yakjido'
OUT = ROOT / 'store'; OUT.mkdir(exist_ok=True)
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'

SENIOR = {'age': 'senior', 'easy': False, 'taking': ['cls:bp.ccb', 'acetaminophen', 'magnesium-oxide'], 'prn': {'acetaminophen': True},
          'sched': {'cls:bp.ccb': ['08:00'], 'magnesium-oxide': ['08:00', '19:00']},
          'prnLog': {'2026-09-29': [{'id': 'acetaminophen', 't': '08:10'}]}, 'taken': {'2026-09-29': ['cls:bp.ccb@08:00']}, 'pub': {}}
SHOTS = [
    ('01-home', '/home', SENIOR, '어디가 불편하세요?', '증상을 고르면 약국에서 무엇을 찾을지 알려 드려요'),
    ('02-symptom', '/symptom/cold', SENIOR, '증상에 맞는 약, 의사가 고르듯', '성분·용량·주의할 점을 쉬운 말로'),
    ('03-together', '/symptom/arthritis', {**SENIOR, 'taking': ['cls:blood.warf', 'cls:bp.ccb']}, '드시는 약과 겹치면 먼저 알려요', '와파린·혈압약과 진통제처럼 조심할 조합', '.ixline, .ix-h', 120),
    ('04-schedule', '/schedule', SENIOR, '앱을 닫아도 약 시간에 울려요', '먹었어요 · 10분 뒤 다시 · 약 떨어지기 전 알림', '.dose-list', 70),
    ('05-kids', '/kids', {'age': 'child', 'child': {'weight': '14', 'birth': '2023-03-01', 'name': '아이'}, 'taking': [], 'pub': {}}, '아이 해열제, 몸무게로 mL까지', '아세트아미노펜·이부프로펜 시럽 용량 계산', 'text=/mL · 한 번에/', 150),
    ('06-pill', '/pill', SENIOR, '모르는 알약, 모양으로 찾아요', '식약처 낱알식별 자료로 색·모양·글자 검색'),
]

def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS)); h.log_message = lambda *a: None
    srv = socketserver.TCPServer(('127.0.0.1', 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{srv.server_address[1]}/index.html'

FRAME = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@500;700;800&display=swap">
<style>
html,body{margin:0;width:360px;height:640px;overflow:hidden}
body{background:linear-gradient(170deg,#3E9DBA 0%,#1F7494 55%,#155F7C 100%);font-family:'Noto Sans KR',sans-serif;word-break:keep-all;color:#fff}
.t{padding:30px 22px 0;text-align:center}
.t h1{font-size:25px;line-height:1.3;font-weight:800;margin:0;letter-spacing:-.3px;text-wrap:balance}
.t p{font-size:14px;line-height:1.5;margin:8px 0 0;color:#DDF1F7;font-weight:500;text-wrap:balance}
.ph{position:absolute;left:34px;right:34px;top:146px;height:560px;border-radius:26px;overflow:hidden;background:#fff;
    box-shadow:0 18px 40px rgba(6,40,56,.35), 0 0 0 7px rgba(255,255,255,.18)}
.ph img{width:100%;display:block}
.ex{position:absolute;right:42px;top:152px;background:rgba(20,40,50,.55);color:#fff;font-size:10px;padding:2px 8px;border-radius:99px;z-index:2}
</style></head><body><div class="t"><h1>{h}</h1><p>{p}</p></div><div class="ex">예시 화면</div><div class="ph"><img src="{img}"></div></body></html>"""

def main():
    from playwright.sync_api import sync_playwright
    url = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for name, route, me, h, p, *focus in SHOTS:
            pg = br.new_page(viewport={'width': 360, 'height': 700}, device_scale_factor=3)
            pg.clock.install(time='2026-09-29T09:30:00')
            pg.add_init_script("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1'," + json.dumps(json.dumps(me)) + ")")
            pg.goto(url + '#' + route); pg.wait_for_selector('.app', timeout=15000); pg.wait_for_timeout(1800)
            if focus:                                        # 그 화면의 핵심(경고·오늘 목록·mL)이 첫 화면에 오게
                el = pg.locator(focus[0]).first
                if el.count(): el.scroll_into_view_if_needed(); pg.evaluate("(y)=>scrollBy(0,y)", el.bounding_box()['y'] - focus[1] if el.bounding_box() else 0); pg.wait_for_timeout(400)
                else: print('!! 못 찾음', name, focus[0])
            raw = pg.screenshot()
            pg.close()
            fr = br.new_page(viewport={'width': 360, 'height': 640}, device_scale_factor=3)
            fr.set_content(FRAME.replace('{h}', h).replace('{p}', p).replace('{img}', 'data:image/png;base64,' + base64.b64encode(raw).decode()))
            fr.wait_for_timeout(900)
            fr.screenshot(path=str(OUT / f'{name}.png')); fr.close()
        # 대표 이미지 1024×500
        icon = base64.b64encode((DOCS / 'icon-512.png').read_bytes()).decode()
        fg = br.new_page(viewport={'width': 1024, 'height': 500})
        fg.set_content(f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@500;800&display=swap">
<style>body{{margin:0;width:1024px;height:500px;background:linear-gradient(160deg,#3E9DBA,#155F7C);font-family:'Noto Sans KR',sans-serif;color:#fff;
display:flex;align-items:center;gap:44px;padding:0 80px;box-sizing:border-box;word-break:keep-all}}
img{{width:210px;height:210px;border-radius:48px;box-shadow:0 16px 40px rgba(6,40,56,.35)}}
h1{{font-size:72px;margin:0;font-weight:800;letter-spacing:-1px}} p{{font-size:30px;margin:10px 0 0;color:#DDF1F7;font-weight:500;line-height:1.4}}</style></head>
<body><img src="data:image/png;base64,{icon}"><div><h1>약지도</h1><p>증상에 맞는 약, 의사가 고르듯<br>복용 알림까지 한 앱에서</p></div></body></html>""")
        fg.wait_for_timeout(900); fg.screenshot(path=str(OUT / 'feature-1024x500.png')); fg.close()
        br.close()
    Image.open(DOCS / 'icon-512.png').convert('RGBA').save(OUT / 'icon-512.png')
    for f in sorted(OUT.glob('*.png')):
        print(f.name, Image.open(f).size)

if __name__ == '__main__':
    main()
