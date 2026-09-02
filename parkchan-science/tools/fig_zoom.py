#!/usr/bin/env python3
"""본책 챕터의 figure들을 고해상도로 잘라 한 장의 검수 시트로 저장.
사용: python3 tools/fig_zoom.py book2/chapter-2101/chapter.html /tmp/out.png"""
import sys, json, subprocess, pymupdf, pathlib
html = sys.argv[1]; out = sys.argv[2]
pdf = html.replace('.html', '.pdf')
here = pathlib.Path(__file__).parent
rects = json.loads(subprocess.run(['python3', str(here/'fig_rects.py'), html], capture_output=True, text=True).stdout)
d = pymupdf.open(pdf); MM = 72/25.4
src = []
for r in rects:
    clip = pymupdf.Rect(r['x']*MM-4, r['y']*MM-4, (r['x']+r['w'])*MM+4, (r['y']+r['hh'])*MM+6)
    src.append(d[r['p']-1].get_pixmap(dpi=175, clip=clip))
W = int(max(p.width for p in src)); H = sum(int(p.height)+8 for p in src)
sheet = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0,0,W,H), False); sheet.clear_with(235)
y = 0
for p in src:
    p.set_origin(0,y); sheet.copy(p, p.irect); y += int(p.height)+8
sheet.save(out)
print(f'{len(rects)}개 그림 → {out} ({sheet.width}x{sheet.height})')
