"""나이 기준 대조표 — 우리가 적은 소아 나이 ↔ 식약처 허가 용법.

약 상세의 「어린이」 칸이 «라벨 확인»으로만 적혀 있던 자리를 찾아낸다.
어르신이 손주에게 어른 알약을 쪼개 먹이는 일이 가장 흔한 사고이고,
그때 필요한 답은 «상자를 보세요»가 아니라 «이 약은 만 몇 세부터»다.

근거는 식약처 e약은요의 용법용량 원문(docs/yakjido/data/easy-*.json)이다.
주의사항(c)이 아니라 용법용량(u)만 쓴다 — 주의사항에는 «수두에 걸린 15세 미만»처럼
조건이 붙은 문장이 섞여 있어 나이 기준으로 읽으면 틀린다.

    python3 tools/age_audit.py        # 나이-대조표.md 를 다시 만든다
"""
import json, glob, re, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT.parent / 'docs' / 'yakjido' / 'data'
OVER = re.compile(r'(?:만)?([0-9]{1,2})세(?:이상|부터)')

def load_drugs():
    out = []
    for f in [ROOT / 'content' / 'drugs.json'] + sorted((ROOT / 'content').glob('drugs.part*.json')):
        L = json.loads(f.read_text(encoding='utf-8'))
        out += (L if isinstance(L, list) else L['drugs'])
    return out

def main():
    idx = json.loads((DATA / 'easy-index.json').read_text(encoding='utf-8'))
    shards = {}
    def rec(i):
        sh = i // 200
        if sh not in shards: shards[sh] = json.loads((DATA / f'easy-{sh}.json').read_text(encoding='utf-8'))
        return shards[sh][i % 200]
    byname = {}
    for i, r in enumerate(idx): byname.setdefault(re.sub(r'\s+', '', r['n']), i)
    key = lambda n: re.sub(r'\s+', '', (n or '').split('·')[0].replace('등', '').strip())

    rows = []
    for d in load_drugs():
        if d.get('rx') == '전문': continue
        ours = ' '.join(str(d.get(k) or '') for k in ('children',)) + ' ' + str((d.get('dose') or {}).get('child') or '')
        vague = not re.search(r'[0-9]{1,2}\s*세|개월|돌', ours)
        for p in (d.get('products') or [])[:1]:
            k = key(p.get('name')); i = byname.get(k)
            if i is None:
                cand = [j for nm, j in byname.items() if len(k) >= 6 and nm.startswith(k[:6])]
                i = cand[0] if len(cand) == 1 else None
            if i is None: continue
            u = (rec(i).get('u') or '').replace(' ', '')
            a = {int(m.group(1)) for m in OVER.finditer(u)}
            if not a: continue
            rows.append((d['id'], d.get('name', ''), idx[i]['n'], min(a), ours.strip()[:70], vague))
    rows.sort(key=lambda r: (not r[5], r[0]))
    out = ['# 나이 대조표 — 우리가 적은 소아 나이 ↔ 식약처 허가 용법', '',
           f'자동 생성: `python3 tools/age_audit.py` · 약 {len(rows)}개', '',
           '「우리가 적은 것」에 나이·개월·돌이 하나도 없으면 **비어 있음**으로 표시한다.', '',
           '| 약 | 허가 용법의 제품 | 허가상 가장 어린 나이 | 우리가 적은 것 | |',
           '|---|---|---|---|---|']
    for i, n, pn, a, ours, vague in rows:
        out.append(f'| `{i}` {n} | {pn[:24]} | 만 {a}세 | {ours or "—"} | {"**비어 있음**" if vague else "있음"} |')
    (ROOT / '나이-대조표.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'나이-대조표.md · {len(rows)}개 · 비어 있음 {sum(1 for r in rows if r[5])}개')

if __name__ == '__main__':
    main()
