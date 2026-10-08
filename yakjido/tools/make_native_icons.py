#!/usr/bin/env python3
"""약지도 안드로이드 앱의 아이콘·스플래시·상태바 아이콘을 «정본 아이콘» 한 장에서 만든다.

정본 = yakjido/art/icon-1024.png (현욱님이 주신 그림 — 위치 핀 속 캡슐). 읽기만 하고 고치지 않는다.
(2026-09-29: 처음엔 옛 초안 icons/icon.svg 로 만들었다가 정본과 달라 다시 만듦 — build.py 머리말 참고)

· 적응형 아이콘: 배경 = 정본의 청록 세로 그러데이션, 전경 = 정본에서 흰 핀·빛줄기·고리만 떼어 낸 것.
  (정본을 통째로 넣으면 둥근 네모 안에 또 둥근 네모가 들어가 테두리가 두 겹이 된다)
· 옛 안드로이드(8.0 미만) 네모 아이콘: 정본 그대로, 바깥 크림색만 투명하게.
· 스플래시: 청록 바탕 위 흰 심볼.
· 상태바 작은 아이콘(ic_stat_pill): 흰 단색 실루엣 — 컬러 그림을 쓰면 흰 네모로 보인다.
사용: python3 yakjido/tools/make_native_icons.py   (app-native/android 가 있어야 한다)
"""
import pathlib
import numpy as np
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / 'app-native/android/app/src/main/res'
assert RES.exists(), 'app-native/android 가 없습니다 — npx cap add android 먼저'
SRC = ROOT / 'art/icon-1024.png'
src = Image.open(SRC).convert('RGBA')
assert src.size == (1024, 1024), src.size
A = np.asarray(src.convert('RGB')).astype(float)

# 1) 줄마다 바탕 청록(왼쪽 가장자리 안쪽에서 잰다) — 세로 그러데이션
rows = np.array([A[min(max(y, 110), 920), 110] for y in range(1024)])
TOP, BOT = rows[110], rows[920]

# 2) 흰 심볼 떼어 내기: 바탕색→흰색 선 위로 투영한 만큼을 불투명도로
W = np.array([253, 253, 250.])
T = rows[:, None, :]                                   # (1024,1,3)
d = W - T
a = ((A - T) * d).sum(-1) / (d * d).sum(-1)
a = np.clip(a, 0, 1)
box = np.zeros_like(a); box[80:860, 200:880] = 1       # 심볼이 있는 곳만(바깥 크림색·가장자리 그림자 제외)
a *= box
a[a < 0.06] = 0
rgb = np.where(a[..., None] > 0, T + (A - T) / np.maximum(a[..., None], 1e-3), 255)
sym = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
SYM = Image.fromarray(sym, 'RGBA')
bb = SYM.getbbox(); SYM = SYM.crop(bb)                 # 심볼만 딱 맞게

def grad(w, h):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (TOP * (1 - g) + BOT * g) * np.ones((1, w, 1))
    return Image.fromarray(arr.astype(np.uint8), 'RGB').convert('RGBA')

def place(canvas, frac):
    W_, H_ = canvas.size; h = int(min(W_, H_) * frac)
    s = SYM.resize((round(h * SYM.width / SYM.height), h), Image.LANCZOS)
    canvas.alpha_composite(s, ((W_ - s.width) // 2, (H_ - s.height) // 2)); return canvas

# 옛 네모 아이콘 — 바깥 크림색을 투명하게(네 모서리에서 번지게 칠해 경계를 찾는다)
sq = src.copy(); m = Image.new('L', sq.size, 0); probe = sq.convert('RGB').copy()
for c in ((0, 0), (1023, 0), (0, 1023), (1023, 1023)):
    ImageDraw.floodfill(probe, c, (255, 0, 255), thresh=60)
pa = np.asarray(probe); outer = (pa[..., 0] == 255) & (pa[..., 1] == 0) & (pa[..., 2] == 255)
alpha = np.where(outer, 0, 255).astype(np.uint8)
sq.putalpha(Image.fromarray(alpha, 'L'))

dens = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}
for d, k in dens.items():
    f = RES / f'mipmap-{d}'; f.mkdir(exist_ok=True)
    px = int(48 * k)
    sq.resize((px, px), Image.LANCZOS).save(f / 'ic_launcher.png', optimize=True)
    rd = place(grad(px, px), 0.56); mask = Image.new('L', (px * 4, px * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, px * 4 - 1, px * 4 - 1), fill=255)
    out = Image.new('RGBA', (px, px), (0, 0, 0, 0)); out.paste(rd, (0, 0), mask.resize((px, px), Image.LANCZOS))
    out.save(f / 'ic_launcher_round.png', optimize=True)
    fg = int(108 * k)                                   # 적응형 캔버스 = 108dp, 안전 지름 66dp
    place(Image.new('RGBA', (fg, fg), (0, 0, 0, 0)), 0.50).save(f / 'ic_launcher_foreground.png', optimize=True)
    grad(fg, fg).convert('RGB').save(f / 'ic_launcher_background.png', optimize=True)
    # 상태바 아이콘 — 24dp, 흰 실루엣
    sd = RES / f'drawable-{d}'; sd.mkdir(exist_ok=True)
    sp = int(24 * k); h = int(sp * 0.92)
    s = SYM.resize((round(h * SYM.width / SYM.height), h), Image.LANCZOS)
    al = np.asarray(s)[..., 3].astype(float); al = np.clip(al * 1.4, 0, 255).astype(np.uint8)
    white = Image.new('RGBA', s.size, (255, 255, 255, 0)); white.putalpha(Image.fromarray(al, 'L'))
    st = Image.new('RGBA', (sp, sp), (0, 0, 0, 0)); st.alpha_composite(white, ((sp - s.width) // 2, (sp - s.height) // 2))
    st.save(sd / 'ic_stat_pill.png', optimize=True)

(RES / 'mipmap-anydpi-v26').mkdir(exist_ok=True)
for name in ('ic_launcher.xml', 'ic_launcher_round.xml'):
    (RES / 'mipmap-anydpi-v26' / name).write_text('''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
''')
mid = (TOP + BOT) / 2
(RES / 'values/ic_launcher_background.xml').write_text(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#%02X%02X%02X</color>\n</resources>\n' % tuple(int(x) for x in mid))
old_vec = RES / 'drawable/ic_stat_pill.xml'
if old_vec.exists(): old_vec.unlink()                  # 예전 벡터(옛 초안 심볼)는 쓰지 않는다
for junk in (RES / 'drawable/ic_launcher_background.xml', RES / 'drawable-v24/ic_launcher_foreground.xml'):
    if junk.exists(): junk.unlink()

sizes = {'drawable': (480, 320), 'drawable-land-mdpi': (480, 320), 'drawable-land-hdpi': (800, 480), 'drawable-land-xhdpi': (1280, 720),
         'drawable-land-xxhdpi': (1600, 960), 'drawable-land-xxxhdpi': (1920, 1280), 'drawable-port-mdpi': (320, 480),
         'drawable-port-hdpi': (480, 800), 'drawable-port-xhdpi': (720, 1280), 'drawable-port-xxhdpi': (960, 1600), 'drawable-port-xxxhdpi': (1280, 1920)}
for d, (w, h) in sizes.items():
    f = RES / d; f.mkdir(exist_ok=True); place(grad(w, h), 0.30).convert('RGB').save(f / 'splash.png', optimize=True)
print('정본(art/icon-1024.png)에서 아이콘 5밀도 · 스플래시 11장 · 상태바 아이콘 갱신 · 배경색 #%02X%02X%02X' % tuple(int(x) for x in mid))
