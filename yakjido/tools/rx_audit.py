#!/usr/bin/env python3
"""약 사전의 '약국 구입 / 처방 필요' 표시를 식약처 공공데이터와 대조한다.

자료 세 가지 (모두 앱에 이미 들어 있다)
  - easy-index.json : e약은요 4,766건 — 사실상 일반의약품만 담긴 목록
  - pills.json      : 낱알식별 일반의약품 5,660건
  - pills-rx.json   : 낱알식별 전문의약품 19,034건
낱알식별은 알약만 담아 연고·점안·시럽·질정은 없다. 그래서 '자료 없음'이 곧 오류는 아니다.

판정
  약국만 있음  → 일반   |  처방만 있음 → 전문
  둘 다 있음   → 제품별 (같은 성분이라도 제형·함량에 따라 분류가 갈리는 약)

    python3 yakjido/tools/rx_audit.py            # 표를 찍고, 어긋나면 1 로 끝난다
"""
import json, glob, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(os.path.dirname(ROOT), 'docs', 'yakjido', 'data')
drugs = [x for f in sorted(glob.glob(os.path.join(ROOT, 'content', 'drugs*.json')))
         for x in json.load(open(f, encoding='utf-8'))]
idx = json.load(open(os.path.join(DATA, 'easy-index.json'), encoding='utf-8'))
otc = json.load(open(os.path.join(DATA, 'pills.json'), encoding='utf-8'))
rxp = json.load(open(os.path.join(DATA, 'pills-rx.json'), encoding='utf-8'))

# 앱이 스스로 '이 제품은 이 성분' 이라고 이어 둔 것 + 성분 이름 글자 맞추기
def keys(d):
    ks = set()
    base = re.split(r'[(（]', d['name'])[0].strip()
    base = re.sub(r'\s*(정|캡슐|겔|크림|연고|패치|파스|시럽|액|정제|질정)$', '', base)
    if len(base) >= 2: ks.add(base)
    for p in d.get('products', []):
        nm = re.split(r'[(（·]', p.get('name', ''))[0].strip()
        if len(nm) >= 3: ks.add(nm)
    return ks

def count(pool, ks, fields=('n', 'ingr')):
    return sum(1 for x in pool if any(k in ' '.join(str(x.get(f, '')) for f in fields) for k in ks))

def count_easy(it_list, ks, did):
    n = 0
    for it in it_list:
        hay = it['n'] + ' ' + ' '.join(it.get('i', []))
        if did in it.get('map', []) or any(k in hay for k in ks): n += 1
    return n

# 이름이 비슷한 다른 약이 잡히는 자리는 이유를 적고 넘긴다
EXCEPT = {'cough-syrup-rx': '약국의 코푸시럽에스가 이름으로 잡히지만 성분이 다른 약'}

rows = []
for d in drugs:
    ks = keys(d)
    if not ks: continue
    n_easy = count_easy(idx, ks, d['id'])
    n_otc = count(otc, ks)
    n_rx = count(rxp, ks)
    buyable, rxonly = (n_easy or n_otc), n_rx
    evid = '제품별' if buyable and rxonly else '일반' if buyable else '전문' if rxonly else '자료 없음'
    rows.append({'d': d, 'evid': evid, 'easy': n_easy, 'otc': n_otc, 'rx': n_rx})

def kind(r):
    if r['d']['id'] in EXCEPT: return None
    app, evid = r['d'].get('rx'), r['evid']
    app_otc = app in ('일반', '안전상비')
    if evid == '자료 없음': return None
    if app == '제품별': return None if evid == '제품별' else '살핌'
    if app_otc and evid == '전문': return '오류'
    if app == '전문' and evid == '일반': return '오류'
    if evid == '제품별': return '살핌'
    return None

err = [r for r in rows if kind(r) == '오류']
look = [r for r in rows if kind(r) == '살핌']
print('# 약국·처방 표시 대조\n')
print(f"대조 {len(rows)}개 · **어긋남 {len(err)}건** · 살펴볼 것 {len(look)}건\n")
for title, group in (('어긋남 — 고쳐야 함', err), ('살펴볼 것 — 일반·전문이 함께 있는 성분', look)):
    if not group: continue
    print(f'## {title}\n')
    print('| 약 | 앱 표시 | 자료 판정 | e약은요 | 일반 낱알 | 전문 낱알 |')
    print('|---|---|---|---|---|---|')
    for r in group:
        print(f"| {r['d']['name']} | {r['d']['rx']} | {r['evid']} | {r['easy']} | {r['otc']} | {r['rx']} |")
    print()
none = [r for r in rows if r['evid'] == '자료 없음']
print(f"## 자동 대조가 안 되는 제형 {len(none)}개\n")
print(', '.join(f"{r['d']['name'].split(' (')[0]}({r['d']['rx']})" for r in none))
sys.exit(1 if err else 0)
