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

# ── 첫 화면 자료와 나머지를 나눈다 ────────────────────────────────────────
# 첫 화면(어디가 불편하세요 · 증상 타일 · 검색)에 필요한 것은 «이름·갈래·아이콘·
# 한 줄 설명»뿐이다. 나머지 본문(계획·복용법·출처 …)은 data/core.json 으로 빼서
# 화면이 뜬 뒤에 받는다. 받아 오면 같은 객체에 그대로 덧씌우므로(Object.assign)
# 화면 함수는 하나도 바꾸지 않아도 된다.
SLIM = {
    'symptoms':    ['id', 'group', 'icon', 'name', 'short', 'tags', 'reviewed'],
    'drugs':       ['id', 'name', 'en', 'class', 'rx', 'tagline', 'simple', 'tags'],
    'supplements': ['id', 'name', 'en', 'tags', 'brands', 'evidence'],
    'classes':     ['id', 'name', 'short', 'icon'],
}
CORE_KEYS = ['sources', 'ingredients', 'interactions', 'kids', 'productImages', 'suppRules', 'myths']
inline, core = {}, {}
for k, v in data.items():
    if k in SLIM:
        fs = SLIM[k]
        inline[k] = [{f: o[f] for f in fs if f in o} for o in v]
        rest = [{f: o[f] for f in o if f not in fs or f == 'id'} for o in v]
        core[k] = [o for o in rest if len(o) > 1]
    elif k in CORE_KEYS:
        core[k] = v
    else:
        inline[k] = v                       # meta · art · public · tips 는 작아서 그대로 둔다

jc = json.dumps(core, ensure_ascii=False, separators=(',', ':'))
j = json.dumps(inline, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
stamp = datetime.date.today().isoformat()
out = shell.replace('<!--DATA-->', j).replace('__BUILD__', stamp)
pages = ROOT.parent / 'docs' / 'yakjido'
pages.mkdir(parents=True, exist_ok=True)
(pages / 'index.html').write_text(out, encoding='utf-8')
(pages / 'data').mkdir(parents=True, exist_ok=True)
(pages / 'data' / 'core.json').write_text(jc, encoding='utf-8')
print(f'첫 화면 {len(out)/1024:.0f} KB · 본문 data/core.json {len(jc)/1024:.0f} KB')
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
# 원본이 SVG 면 크기마다 «다시 그린다» — 키우고 줄여도 테두리가 뭉개지지 않는다.
src_icon = None
svg_icon = ROOT / 'art' / 'icon.svg'
if svg_icon.exists():
    try:
        import cairosvg, io as _io
        cairosvg.svg2png(url=str(svg_icon), write_to=str(ROOT / 'art' / 'icon-1024.png'), output_width=1024, output_height=1024)
    except Exception as e:
        print('아이콘 SVG 굽기 건너뜀:', e)
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
        sizes = ((1024, 'icon-1024.png'), (512, 'icon-512.png'), (192, 'icon-192.png'), (180, 'icon-180.png'))
        mask_svg = ROOT / 'art' / 'icon-maskable.svg'
        if svg_icon.exists():
            import cairosvg
            for size, name in sizes:
                cairosvg.svg2png(url=str(svg_icon), write_to=str(pages / name), output_width=size, output_height=size)
            # 마스크용은 안드로이드가 동그랗게 잘라낸다 — 그림을 줄여 둔 판을 따로 쓴다
            cairosvg.svg2png(url=str(mask_svg if mask_svg.exists() else svg_icon), write_to=str(pages / 'icon-maskable-512.png'), output_width=512, output_height=512)
        else:
            for size, name in sizes:
                im.resize((size, size), Image.LANCZOS).save(pages / name, 'PNG')
            im.resize((512, 512), Image.LANCZOS).save(pages / 'icon-maskable-512.png', 'PNG')
        print('앱 아이콘 재생성 ← art/' + src_icon.name)
    except Exception as e:
        print('아이콘 재생성 건너뜀:', e)

counts = {k: (len(v) if isinstance(v, (list, dict)) else 1) for k, v in data.items()}
print(f'배포본 → {pages}/index.html · {len(out)//1024} KB · {counts}')
print('삽화:', ', '.join(found) if found else '없음 (yakjido/art/ 에 PNG 를 넣으면 자동 반영)')
