#!/usr/bin/env python3
"""앱 아이콘 한 장(정사각 PNG)에서 PWA·안드로이드가 쓰는 크기를 전부 뽑는다.

원본은 절대 고치지 않는다 — 읽어서 줄이기만 한다.
maskable(안드로이드 적응형)은 바깥 20%가 잘려 나가므로, 심볼을 80% 안쪽으로 들여 놓는다.

사용: python3 tools/make_icons.py app/icons/05_딥틸_흰심볼_크게.png
산출: docs/parkchan/icon-{180,192,512,1024}.png · icon-maskable-512.png
      app-native/android/app/src/main/res/mipmap-*/ic_launcher*.png (폴더가 있을 때만)
"""
import sys, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'app/icons/05_딥틸_흰심볼_크게.png')
im = Image.open(src).convert('RGBA')
assert im.width == im.height, f'정사각이 아니다: {im.size}'
BG = im.getpixel((4, 4))                         # 모서리 색 = 배경색

def sq(size):
    return im.resize((size, size), Image.LANCZOS)

def maskable(size, safe=0.80):
    canvas = Image.new('RGBA', (size, size), BG)
    inner = int(size * safe)
    canvas.paste(sq(inner), ((size - inner) // 2, (size - inner) // 2))
    return canvas

pwa = ROOT.parent / 'docs' / 'parkchan'
for s in (180, 192, 512, 1024):
    sq(s).save(pwa / f'icon-{s}.png', optimize=True)
maskable(512).save(pwa / 'icon-maskable-512.png', optimize=True)
print(f'PWA 아이콘 5종 ← {src.name}  (배경 {BG[:3]})')

# 안드로이드 — 폴더가 있을 때만 (cap add android 뒤)
res = ROOT / 'app-native/android/app/src/main/res'
if res.exists():
    dens = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
    for d, s in dens.items():
        folder = res / f'mipmap-{d}'; folder.mkdir(exist_ok=True)
        sq(s).save(folder / 'ic_launcher.png', optimize=True)
        sq(s).save(folder / 'ic_launcher_round.png', optimize=True)
        # 적응형 전경(108dp 기준 = 아이콘의 2.25배 캔버스, 심볼은 가운데 66%)
        fg = int(s * 108 / 48)
        maskable(fg, safe=0.66).save(folder / 'ic_launcher_foreground.png', optimize=True)
    # 적응형 배경색
    vals = res / 'values'; vals.mkdir(exist_ok=True)
    (vals / 'ic_launcher_background.xml').write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        f'    <color name="ic_launcher_background">#{BG[0]:02X}{BG[1]:02X}{BG[2]:02X}</color>\n</resources>\n')
    print('안드로이드 mipmap 5밀도 갱신')

# 스플래시 — Capacitor 템플릿의 기본 로고를 브랜드로 바꾼다. 배경색 위에 심볼(원본 정사각)을 가운데.
if res.exists():
    sizes = {'drawable': (480, 320), 'drawable-land-mdpi': (480, 320), 'drawable-land-hdpi': (800, 480),
             'drawable-land-xhdpi': (1280, 720), 'drawable-land-xxhdpi': (1600, 960), 'drawable-land-xxxhdpi': (1920, 1280),
             'drawable-port-mdpi': (320, 480), 'drawable-port-hdpi': (480, 800), 'drawable-port-xhdpi': (720, 1280),
             'drawable-port-xxhdpi': (960, 1600), 'drawable-port-xxxhdpi': (1280, 1920)}
    for d, (w, h) in sizes.items():
        canvas = Image.new('RGB', (w, h), BG[:3])
        sym = int(min(w, h) * 0.42)              # 짧은 변의 42% — 로딩 화면에서 과하지 않게
        canvas.paste(sq(sym).convert('RGB'), ((w - sym) // 2, (h - sym) // 2))
        folder = res / d; folder.mkdir(exist_ok=True)
        canvas.save(folder / 'splash.png', optimize=True)
    print('스플래시 11장 갱신')
