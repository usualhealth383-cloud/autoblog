#!/usr/bin/env python3
"""오늘의 한 마디 — 분야별로 검증해 모은 글귀를 하나로 합친다.

· 선생님이 쓴 글(kind=teacher)은 뺀다(2026-09-30 원장 지시: 출처 있는 명언만).
· 같은 원문·같은 번역은 하나만 남긴다.
· 분야가 고르게 섞이도록(과학자 → 고전 → 작가 …) 나란히 펼치고, 같은 사람이 이틀 연속 나오지 않게 한다.
· 앱에는 보일 칸만 넣고, 검증 근거(verify)는 data/quotes-verification.json 에 따로 남긴다.

사용: python3 tools/build_quotes.py <모은 JSON 폴더>
"""
import json, sys, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else None
KIND = {'science': '과학자', 'classic': '고전', 'west': '서양 고전', 'korea': '우리 인물', 'writer': '작가·사상가', 'modern': '운동·예술'}
FIELDS = ('kind', 'kindName', 'ko', 'orig', 'who', 'role', 'src', 'url', 'note')

old = json.loads((ROOT / 'data/quotes.json').read_text(encoding='utf-8'))
items = [q for q in old['quotes'] if q.get('kind') != 'teacher']
for f in sorted(SRC.glob('*.json')) if SRC else []:
    items += json.loads(f.read_text(encoding='utf-8'))

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

# 분야별로 나란히 펼치기: 각 분야 안에서의 순서(i/n)로 정렬하면 비율대로 고르게 섞인다
by = {}
for q in out: by.setdefault(q['kind'], []).append(q)
order = sorted(((i + 0.5) / len(v), k, q) for k, v in by.items() for i, q in enumerate(v))
seq = [q for _, _, q in order]
# 같은 사람 연속 피하기(뒤의 다른 사람과 자리 바꾸기)
for i in range(1, len(seq)):
    if seq[i]['who'] == seq[i-1]['who']:
        for j in range(i + 1, len(seq)):
            if seq[j]['who'] != seq[i-1]['who'] and (j + 1 >= len(seq) or seq[j+1]['who'] != seq[i]['who']):
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
print(f'글귀 {len(app)}개', cnt, f'· 중복 제외 {len(dropped)}', dropped[:8])
