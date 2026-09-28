#!/usr/bin/env python3
"""약지도 안드로이드 앱의 아이콘·스플래시·상태바 아이콘을 icons/icon.svg 한 장에서 만든다.

원본(icons/*)은 고치지 않는다 — 읽어서 그리기만 한다.
· 적응형 아이콘: 배경은 브랜드 색 단색, 전경은 흰 심볼(받쳐 든 손 + 알약)만. 안드로이드가 바깥을 잘라 내므로 심볼은 가운데 60% 안에.
· 옛 안드로이드(8.0 미만)용 네모 아이콘: icons/icon-1024.png 를 줄여서.
· 스플래시: 브랜드 색 위에 흰 심볼.
· 상태바 작은 아이콘(ic_stat_pill): 흰 단색 벡터 — 컬러 그림을 쓰면 흰 네모로 보인다.
사용: python3 yakjido/tools/make_native_icons.py   (app-native/android 가 있어야 한다)
"""
import pathlib, re
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / 'app-native/android/app/src/main/res'
assert RES.exists(), 'app-native/android 가 없습니다 — npx cap add android 먼저'
BRAND = '#0B6E8F'
svg = (ROOT / 'icons/icon.svg').read_text()
# 심볼만 — 배경 사각형은 뺀다(알약 가운데 줄은 그림에는 두고, 단색 상태바 아이콘에서만 뺀다)
sym_all = [l for l in svg.splitlines() if '<path' in l or '<circle' in l]
sym = [l for l in sym_all if '#0A5E7C' not in l]
SYM_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="112 100 288 332" width="{w}" height="{h}">' + ''.join(sym_all) + '</svg>'

def render_symbol(h):
    """흰 심볼을 투명 배경 PNG 로(크로미움으로 그린다 — 선 끝 둥글기까지 원본 그대로)"""
    from playwright.sync_api import sync_playwright
    w = round(h * 288 / 332); out = pathlib.Path('/tmp/yakjido-symbol.png')
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg = br.new_page(viewport={'width': w, 'height': h})
        pg.set_content('<html><body style="margin:0;background:transparent">' + SYM_SVG.format(w=w, h=h) + '</body></html>')
        pg.screenshot(path=str(out), omit_background=True, clip={'x': 0, 'y': 0, 'width': w, 'height': h}); br.close()
    return Image.open(out).convert('RGBA')

S = render_symbol(1024)
def on_canvas(size_wh, frac, bg):
    W, H = size_wh; c = Image.new('RGBA', (W, H), bg)
    h = int(min(W, H) * frac); s = S.resize((round(h * S.width / S.height), h), Image.LANCZOS)
    c.alpha_composite(s, ((W - s.width) // 2, (H - s.height) // 2)); return c

square = Image.open(ROOT / 'icons/icon-1024.png').convert('RGBA')
dens = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
for d, px in dens.items():
    f = RES / f'mipmap-{d}'; f.mkdir(exist_ok=True)
    sq = square.resize((px, px), Image.LANCZOS); sq.save(f / 'ic_launcher.png', optimize=True)
    rd = Image.new('RGBA', (px, px), (0, 0, 0, 0)); m = Image.new('L', (px * 4, px * 4), 0)
    from PIL import ImageDraw; ImageDraw.Draw(m).ellipse((0, 0, px * 4 - 1, px * 4 - 1), fill=255)
    rd.paste(on_canvas((px, px), 0.52, BRAND), (0, 0), m.resize((px, px), Image.LANCZOS)); rd.save(f / 'ic_launcher_round.png', optimize=True)
    fg = int(px * 108 / 48)                           # 적응형 전경 캔버스 = 108dp
    on_canvas((fg, fg), 0.46, (0, 0, 0, 0)).save(f / 'ic_launcher_foreground.png', optimize=True)
(RES / 'values/ic_launcher_background.xml').write_text(
    f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">{BRAND}</color>\n</resources>\n')
# 템플릿의 초록 격자 배경 벡터는 쓰지 않는다
for junk in (RES / 'drawable/ic_launcher_background.xml', RES / 'drawable-v24/ic_launcher_foreground.xml'):
    if junk.exists(): junk.unlink()
# 스플래시
sizes = {'drawable': (480, 320), 'drawable-land-mdpi': (480, 320), 'drawable-land-hdpi': (800, 480), 'drawable-land-xhdpi': (1280, 720),
         'drawable-land-xxhdpi': (1600, 960), 'drawable-land-xxxhdpi': (1920, 1280), 'drawable-port-mdpi': (320, 480),
         'drawable-port-hdpi': (480, 800), 'drawable-port-xhdpi': (720, 1280), 'drawable-port-xxhdpi': (960, 1600), 'drawable-port-xxxhdpi': (1280, 1920)}
for d, wh in sizes.items():
    f = RES / d; f.mkdir(exist_ok=True); on_canvas(wh, 0.26, BRAND).convert('RGB').save(f / 'splash.png', optimize=True)
# 상태바 작은 아이콘 — 같은 심볼을 흰 벡터로(24dp 안에 20dp 높이)
k = 20 / 332; tx = 12 - (112 + 144) * k; ty = 12 - (100 + 166) * k
PD = re.compile(r'd="([^"]+)"')
paths = ''.join('\n        <path android:strokeColor="#FFFFFFFF" android:strokeWidth="40" android:strokeLineCap="round" android:fillColor="#00000000" android:pathData="' + PD.search(l).group(1) + '"/>'
                for l in sym if '<path' in l)
circle = '\n        <path android:fillColor="#FFFFFFFF" android:pathData="M200,176a56,56 0 1,0 112,0a56,56 0 1,0 -112,0z"/>'
(RES / 'drawable/ic_stat_pill.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<!-- 약지도 심볼(받쳐 든 손 + 알약) — tools/make_native_icons.py 가 만든다 -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24">
    <group android:translateX="{tx:.3f}" android:translateY="{ty:.3f}" android:scaleX="{k:.5f}" android:scaleY="{k:.5f}">{paths}{circle}
    </group>
</vector>
''')
print('안드로이드 아이콘 5밀도 · 스플래시 11장 · 상태바 아이콘 갱신')
