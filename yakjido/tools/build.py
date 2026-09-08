#!/usr/bin/env python3
"""약지도 앱 빌드 — content/*.json 을 app-shell.html 에 심어 docs/yakjido/index.html 로 낸다.

사용:  python3 yakjido/tools/build.py
- content/ 의 모든 JSON 을 하나의 DATA 객체로 합친다(파일명 = 키).
- public/ 에 공공데이터(e약은요·낱알식별) 추출본이 있으면 함께 심는다.
- 배포본은 GitHub Pages(docs/yakjido/) 로 나간다. manifest·sw 는 같은 폴더에 둔다.
"""
import json, pathlib, re, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
shell = (ROOT / 'app-shell.html').read_text(encoding='utf-8')
data = {}
for p in sorted((ROOT / 'content').glob('*.json')):
    if p.name.startswith('_'): continue
    key = p.stem.split('.')[0]          # drugs.part2.json → drugs 에 합침
    v = json.loads(p.read_text(encoding='utf-8'))
    if key in data and isinstance(v, list): data[key].extend(v)
    elif key in data and isinstance(v, dict): data[key].update(v)
    else: data[key] = v
pub = ROOT.parent / 'docs' / 'yakjido' / 'data'   # 공공데이터는 import_public_data.py 가 여기에 직접 쓴다
if (pub / 'meta.json').exists():
    data['public'] = json.loads((pub / 'meta.json').read_text(encoding='utf-8'))  # 건수·출처만 인라인, 본문은 data/ 로 지연 로드
# 낱알 사진은 식약처 서버 주소를 그대로 쓴다(저장 안 함). docs/yakjido/img/ 에 파일이 있을 때만 그것을 우선.
imgdir = ROOT.parent / 'docs' / 'yakjido' / 'img'
for v in (data.get('productImages') or {}).values():
    iid = v['img'].rstrip('/').split('/')[-1]
    for ext in ('.webp', '.jpg'):
        if (imgdir / (iid + ext)).exists(): v['img'] = 'img/' + iid + ext; break
# ── 삽화(art/) ────────────────────────────────────────────────────────────
# yakjido/art/ 에 PNG 를 넣어 두기만 하면 배포본으로 복사되고, 앱은 있는 그림만 그린다.
# 파일이 없으면 D.art 목록에 안 들어가서 화면에 빈 자리도 안 생긴다.
ART_NAMES = ['hero-home', 'guide-1-where', 'guide-2-pharmacy', 'guide-3-take', 'photo-guide',
             'pill-search', 'schedule', 'supp-label', 'kids-dose', 'easy-mode',
             'me-safety', 'tips', 'empty-search']
artsrc = ROOT / 'art'
artdst = ROOT.parent / 'docs' / 'yakjido' / 'art'
MAXW = {'easy-mode': 300}                  # 88px 원형이라 작게, 나머지는 900px 이면 2배 화면까지 충분
found = []
if artsrc.exists():
    for name in ART_NAMES:
        f = next((artsrc / (name + e) for e in ('.webp', '.png', '.jpg') if (artsrc / (name + e)).exists()), None)
        if not f: continue
        artdst.mkdir(parents=True, exist_ok=True)
        try:
            from PIL import Image
            im = Image.open(f).convert('RGB'); cap = MAXW.get(name, 900); long = max(im.size)
            if long > cap:
                r = cap / long; im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
            im.save(artdst / (name + '.webp'), 'WEBP', quality=82, method=6)
        except Exception as e:
            (artdst / (name + f.suffix)).write_bytes(f.read_bytes()); print('그림 변환 실패, 원본 복사:', name, e)
        found.append(name)
for stale in (artdst.glob('*') if artdst.exists() else []):      # 지운 그림은 배포본에서도 지운다
    if stale.stem not in found: stale.unlink()
data['art'] = found

j = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
stamp = datetime.date.today().isoformat()
out = shell.replace('<!--DATA-->', j).replace('__BUILD__', stamp)
pages = ROOT.parent / 'docs' / 'yakjido'
pages.mkdir(parents=True, exist_ok=True)
(pages / 'index.html').write_text(out, encoding='utf-8')
# 서비스워커 캐시 이름을 빌드마다 갱신
sw = ROOT / 'sw.js'
if sw.exists():
    s = re.sub(r"const CACHE = '[^']*'", f"const CACHE = 'yakjido-{stamp}-{abs(hash(j)) % 10000}'", sw.read_text(encoding='utf-8'))
    (pages / 'sw.js').write_text(s, encoding='utf-8')
for name in ('manifest.webmanifest',):
    src = ROOT / name
    if src.exists():
        (pages / name).write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
for ic in (ROOT / 'icons').glob('*'):
    (pages / ic.name).write_bytes(ic.read_bytes())

# ── 앱 아이콘 ──────────────────────────────────────────────────────────────
# art/icon-1024.png 이 있으면 그것으로 각 크기의 아이콘을 다시 만든다(없으면 icons/ 의 기존 것 유지).
src_icon = None
for ext in ('.png', '.webp', '.jpg'):
    f = ROOT / 'art' / ('icon-1024' + ext)
    if f.exists(): src_icon = f; break
if src_icon:
    try:
        from PIL import Image
        im = Image.open(src_icon).convert('RGBA')
        if im.width != im.height:                       # 두 안이 나란히 들어온 경우 왼쪽(캡슐 안) 정사각형만 쓴다
            side = min(im.width, im.height); im = im.crop((0, 0, side, side))
        bg = Image.new('RGBA', im.size, (250, 248, 243, 255))
        bg.alpha_composite(im); im = bg.convert('RGB')
        for size, name in ((1024, 'icon-1024.png'), (512, 'icon-512.png'), (192, 'icon-192.png'), (180, 'icon-180.png')):
            im.resize((size, size), Image.LANCZOS).save(pages / name, 'PNG')
        im.resize((512, 512), Image.LANCZOS).save(pages / 'icon-maskable-512.png', 'PNG')
        print('앱 아이콘 재생성 ← art/' + src_icon.name)
    except Exception as e:
        print('아이콘 재생성 건너뜀:', e)

counts = {k: (len(v) if isinstance(v, (list, dict)) else 1) for k, v in data.items()}
print(f'배포본 → {pages}/index.html · {len(out)//1024} KB · {counts}')
print('삽화:', ', '.join(found) if found else '없음 (yakjido/art/ 에 PNG 를 넣으면 자동 반영)')
