#!/usr/bin/env python3
"""오늘의 한 마디 — 분야별로 검증해 모은 글귀를 하나로 합친다.

· 선생님이 쓴 글(kind=teacher)은 뺀다(2026-09-30 원장 지시: 출처 있는 명언만).
· 같은 원문·같은 번역은 하나만 남긴다.
· 분야가 고르게 섞이도록(과학자 → 고전 → 작가 …) 나란히 펼치고, 같은 사람이 이틀 연속 나오지 않게 한다.
· 앱에는 보일 칸만 넣고, 검증 근거(verify)는 data/quotes-verification.json 에 따로 남긴다.

사용: python3 tools/build_quotes.py <모은 JSON 폴더>  또는  <파일.json …> [--drop "w018;존 우든"]
"""
import json, sys, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 and Path(sys.argv[1]).is_dir() else None
KIND = {'science': '과학자', 'classic': '고전', 'west': '서양 고전', 'korea': '우리 인물', 'writer': '작가·사상가', 'modern': '운동·예술'}
FIELDS = ('kind', 'kindName', 'ko', 'orig', 'who', 'role', 'src', 'url', 'note')

old = json.loads((ROOT / 'data/quotes.json').read_text(encoding='utf-8'))
DROPARG = sys.argv[sys.argv.index('--drop') + 1] if '--drop' in sys.argv else None
args = [a for a in sys.argv[1:] if not a.startswith('--') and a != DROPARG]
DROP = [x for x in (DROPARG.split(';') if DROPARG else []) if x]
items = []
if args and all(a.endswith('.json') for a in args):          # 파일을 직접 고르면 그것만(검증을 통과한 *.fixed.json 등)
    for a in args:
        items += json.loads(Path(a).read_text(encoding='utf-8'))
else:                                                        # 폴더를 주면 기존 글귀(선생님 글 제외) + 폴더의 모든 JSON
    items = [q for q in old['quotes'] if q.get('kind') != 'teacher']
    for f in sorted(SRC.glob('*.json')) if SRC else []:
        items += json.loads(f.read_text(encoding='utf-8'))
items = [q for q in items if q.get('kind') != 'teacher' and not any(d in (q.get('id', '') + '|' + q.get('who', '') + '|' + q.get('ko', '')) for d in DROP)]

norm = lambda t: re.sub(r'[\s\W_]+', '', unicodedata.normalize('NFKC', t or '')).lower()
seen, out, dropped = set(), [], []
for q in items:
    k1, k2 = norm(q.get('orig')), norm(q.get('ko'))
    if (k1 and k1 in seen) or k2 in seen:
        dropped.append(q['who'] + ' · ' + q['ko'][:24]); continue
    seen.update(x for x in (k1, k2) if x)
    q['kindName'] = KIND.get(q['kind'], q.get('kindName', ''))
    for k in ('ko', 'note', 'src', 'role', 'who'):
        assert q.get(k), f'빈 칸 {k}: {q}'
    assert len(q['ko']) <= 120 and len(q['note']) <= 70, q
    out.append(q)

# 한 사람에 쏠리지 않게: 한 사람당 최대 CAP 개(원문이 짧은 것부터 남긴다)
import random
CAP = int(sys.argv[sys.argv.index('--cap') + 1]) if '--cap' in sys.argv else 12
per = {}
pkey = lambda q: q['who'] + ('|' + q.get('role', '') if q['who'].startswith('작자') else '')   # '작자 미상'은 책마다 따로
for q in sorted(out, key=lambda q: len(q.get('ko', ''))): per.setdefault(pkey(q), []).append(q)
keep = {id(q) for v in per.values() for q in v[:CAP]}
capped = [pkey(q) for v in per.values() for q in v[CAP:]]
out = [q for q in out if id(q) in keep]
# 분야별로 나란히 펼치기: 분야 안은 고정 씨앗으로 섞고(같은 책이 몰리지 않게), 분야 안 순서(i/n)로 정렬하면 비율대로 고르게 섞인다
rnd = random.Random(20261101)
by = {}
for q in out: by.setdefault(q['kind'], []).append(q)
for v in by.values(): rnd.shuffle(v)
order = sorted(((i + 0.5) / len(v), k, q['ko']) + (q,) for k, v in by.items() for i, q in enumerate(v))
seq = [x[-1] for x in order]
# 같은 사람은 최소 WIN 일 간격(뒤쪽의 다른 사람과 자리 바꾸기)
WIN = 7
def clash(i, who): return any(seq[j]['who'] == who for j in range(max(0, i - WIN), i))
for i in range(1, len(seq)):
    if clash(i, seq[i]['who']):
        for j in range(i + 1, len(seq)):
            if not clash(i, seq[j]['who']):
                seq[i], seq[j] = seq[j], seq[i]; break

keep_ids = {q.get('id') for q in seq if q.get('id')}
n = 0
def nid():
    global n
    while True:
        n += 1; i = f'w{n:03d}'
        if i not in keep_ids: keep_ids.add(i); return i
app, audit = [], []
for q in seq:
    q.setdefault('id', None)
    if not q['id']: q['id'] = nid()
    app.append({k: q[k] for k in ('id',) + FIELDS if q.get(k)})
    audit.append({'id': q['id'], 'who': q['who'], 'src': q['src'], 'url': q.get('url', ''), 'verify': q.get('verify', '기존 검증(2026-09 이전)')})

(ROOT / 'data/quotes.json').write_text(json.dumps({'quotes': app, 'bridge': old['bridge']}, ensure_ascii=False, indent=1), encoding='utf-8')
(ROOT / 'data/quotes-verification.json').write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding='utf-8')
cnt = {}
for q in app: cnt[q['kindName']] = cnt.get(q['kindName'], 0) + 1
print(f'글귀 {len(app)}개', cnt, f'· 중복 제외 {len(dropped)}', dropped[:8], f'· 한 사람 {CAP}개 넘어 뺀 것 {len(capped)}', sorted(set(capped)))
