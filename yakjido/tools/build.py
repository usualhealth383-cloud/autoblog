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
# 낱알 사진은 식약처 서버 주소를 그대로 쓴다(저장 안 함). 사진이 없으면 앱이 모양·색 자료로 그린다. docs/yakjido/img/ 에 파일이 있을 때만 그것을 우선.
imgdir = ROOT.parent / 'docs' / 'yakjido' / 'img'
for v in (data.get('productImages') or {}).values():
    iid = v['img'].rstrip('/').split('/')[-1]
    for ext in ('.webp', '.jpg'):
        if (imgdir / (iid + ext)).exists(): v['img'] = 'img/' + iid + ext; break
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

counts = {k: (len(v) if isinstance(v, (list, dict)) else 1) for k, v in data.items()}
print(f'배포본 → {pages}/index.html · {len(out)//1024} KB · {counts}')
