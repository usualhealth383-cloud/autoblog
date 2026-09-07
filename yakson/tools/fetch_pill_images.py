#!/usr/bin/env python3
"""낱알 사진을 로컬 썸네일로 내려받아 앱에 번들한다 (정부 서버 의존 제거, 오프라인 지원).

제작 PC(국내망)에서 실행:  python3 yakson/tools/fetch_pill_images.py [--all]
- 기본: content/productImages.json 에 매핑된 대표 제품 사진만(수십 장)
- --all: pills.json 의 일반의약품 전체(약 5,600장, 160px WebP ≈ 25 MB) — 저장소 용량을 생각해 선택
출력: docs/yakson/img/<id>.jpg|webp  · 앱은 같은 id 의 로컬 파일이 있으면 그것을 먼저 쓴다(build.py 가 매핑을 갱신).
출처 표시 의무: 식품의약품안전처·약학정보원.
"""
import json, pathlib, sys, urllib.request, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT.parent / 'docs' / 'yakson' / 'img'; IMG.mkdir(parents=True, exist_ok=True)
try:
    from PIL import Image
except ImportError:
    Image = None; print('PIL 이 없어 원본 JPG 를 그대로 저장합니다 (pip install pillow 권장)')

def fetch(url):
    iid = url.rstrip('/').split('/')[-1]
    dst = IMG / (iid + ('.webp' if Image else '.jpg'))
    if dst.exists(): return dst
    req = urllib.request.Request(url, headers={'User-Agent': 'yakson-build/1.0'})
    data = urllib.request.urlopen(req, timeout=30).read()
    if Image:
        import io
        im = Image.open(io.BytesIO(data)).convert('RGB'); im.thumbnail((320, 320)); im.save(dst, 'WEBP', quality=80)
    else:
        dst.write_bytes(data)
    time.sleep(0.2)
    return dst

targets = []
pm = ROOT / 'content' / 'productImages.json'
if pm.exists(): targets += [v['img'] for v in json.loads(pm.read_text(encoding='utf-8')).values()]
if '--all' in sys.argv:
    targets += [p['img'] for p in json.loads((ROOT.parent / 'docs' / 'yakson' / 'data' / 'pills.json').read_text(encoding='utf-8')) if p.get('img')]
ok = fail = 0
for u in dict.fromkeys(targets):
    try: fetch(u); ok += 1
    except Exception as e: fail += 1; print('실패', u, e)
print(f'저장 {ok} · 실패 {fail} → {IMG}')
