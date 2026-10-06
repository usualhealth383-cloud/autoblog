#!/usr/bin/env python3
"""교재 데이터 점검 — 추출하면서 뜻이 바뀌는 것(지수·아래 첨자가 사라짐 등)을 막는다.

· 원본(book*/)의 <sup>·<sub> 수와 앱 데이터(data/)에 남은 첨자 수(태그 + 유니코드 첨자)가 크게 다르면 실패
· '10−10 m'·'10-15'처럼 첨자가 사라진 흔적(10 뒤에 바로 음수·지수 숫자)이 데이터 글자에 있으면 실패
사용: python3 tools/check_content.py        (추출 뒤, 빌드 전에)
"""
import json, re, glob, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
UNI = '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ₀₁₂₃₄₅₆₇₈₉₊₋'
bad = []
data = {f: json.loads((ROOT / 'data' / f'{f}.json').read_text(encoding='utf-8')) for f in ('concepts', 'quizzes', 'bank', 'labs')}
def strings(x):
    if isinstance(x, str): yield x
    elif isinstance(x, list):
        for y in x: yield from strings(y)
    elif isinstance(x, dict):
        for k, y in x.items():
            if k not in ('figure', 'svg', 'id', 'lessonId'): yield from strings(y)
for f, items in data.items():
    for it in items:
        for t in strings(it):
            txt = re.sub(r'<su[pb]>.*?</su[pb]>', '', t)
            for m in re.finditer(r'(?<![\d.])10\s?[−-]\d{1,2}(?![\d.,])\s*(m|초|s|kg|g|배|J|W|L)\b', txt):
                bad.append(f'{f} {it.get("id") or it.get("lessonId")}: 첨자가 사라진 듯한 "{m[0]}" · {txt[max(0, m.start()-12):m.end()+8]}')
# 원본 대비 첨자 수(대략) — 문항·개념에 쓰인 원본 파일만
src = sum(len(re.findall(r'<su[pb]\b', open(p, encoding='utf-8').read())) for p in glob.glob(str(ROOT / 'book*' / 'lecture-edition' / 'L-*.html')))
got = sum(json.dumps(v, ensure_ascii=False).count('<sup>') + json.dumps(v, ensure_ascii=False).count('<sub>') + sum(json.dumps(v, ensure_ascii=False).count(c) for c in UNI) for k, v in data.items() if k in ('concepts', 'quizzes'))
print(f'강의용 교재 원본 첨자 {src}개 · 개념·확인 문제 데이터 첨자 {got}자')
if src and got < src * 0.8: bad.append(f'개념·확인 문제의 첨자가 원본보다 너무 적음({got} < {src}×0.8) — 추출기가 <sup>·<sub> 를 걷고 있지 않은지')
# 그림: 정의 없이 참조만 하는 기호·그라데이션(그리면 빈칸) — 0 이어야 한다
sys.path.insert(0, str(ROOT / 'tools')); from _extract_common import dangling
for f in sorted((ROOT / 'data' / 'figures').glob('*.svg')):
    d = dangling(f.read_text(encoding='utf-8'))
    if d: bad.append(f'그림 {f.name}: 정의 없는 참조 {d[:4]}')
for k in ('bank', 'labs'):
    for it in data[k]:
        if it.get('figure') and dangling(it['figure']): bad.append(f'{k} {it.get("id") or it.get("lessonId")}: 그림 정의 없는 참조 {dangling(it["figure"])[:4]}')
# '<보기>' 같은 글자가 태그로 오인돼 지워진 흔적
for it in data['bank']:
    if it['type'] == 'multi' and re.search(r'옳은 것만을\s+에서', it['stem']): bad.append(f'bank {it["id"]}: "<보기>" 가 지워진 듯함')
# 개념 덧붙임(data/concept_extras.json — 손으로 만든 원본, 추출기가 덮어쓰지 않음): '왜?' 정교화 질문 + 계산형 예제 → 따라 풀기
# · 키 = 실제 개념 id · why 는 개념마다 1개(q·a·src) · a 는 그 개념의 src 문단/용어 글과 겹쳐야 한다(새 사실 금지)
# · example 과 follow 는 짝으로 · 첨자는 <sup>·<sub> 태그로(유니코드 첨자·'H2O'·'10−6' 흔적 금지)
_ex_p = ROOT / 'data' / 'concept_extras.json'
if not _ex_p.exists(): bad.append('data/concept_extras.json 이 없음')
else:
    extras = json.loads(_ex_p.read_text(encoding='utf-8')); cmap = {c['id']: c for c in data['concepts']}
    _plain = lambda s: re.sub(r'<[^>]+>', '', s)
    _sub = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻₀₁₂₃₄₅₆₇₈₉₊₋', '0123456789+−0123456789+−')
    _norm = lambda s: re.sub(r'[\s·,.\'"‘’“”()\-—–~:;!?/]', '', _plain(s).translate(_sub))
    def _src(c, src):
        out = []
        for p in src.split('+'):
            m = re.fullmatch(r'(body|steps|terms)\[(\d+)\]|point', p.strip())
            if not m: return None
            if p.strip() == 'point': t = c['point']
            else:
                arr = c[m[1]]; i = int(m[2])
                if i >= len(arr): return None
                t = arr[i]['d'] if m[1] == 'steps' else (arr[i]['k'] + ' ' + arr[i]['v'] if m[1] == 'terms' else arr[i])
            for k, v in c['blanks'].items(): t = t.replace('{{%s}}' % k, v)
            out.append(t)
        return ' '.join(out)
    def _strs(x):
        if isinstance(x, str): yield x
        elif isinstance(x, list):
            for y in x: yield from _strs(y)
        elif isinstance(x, dict):
            for y in x.values(): yield from _strs(y)
    n_why = n_ex = 0
    for cid, x in extras.items():
        if cid not in cmap: bad.append(f'extras {cid}: 없는 개념 id'); continue
        w = x.get('why') or {}
        if not all(isinstance(w.get(k), str) and w[k].strip() for k in ('q', 'a', 'src')): bad.append(f'extras {cid}: why 의 q·a·src 가 비어 있음')
        else:
            n_why += 1
            if not re.search(r'(왜|어떻게)[^?]*\?$', w['q']): bad.append(f'extras {cid}: why.q 가 "왜/어떻게 …?" 꼴이 아님')
            if not 20 <= len(_plain(w['a'])) <= 60: bad.append(f'extras {cid}: why.a 길이 {len(_plain(w["a"]))}자(20~60)')
            st = _src(cmap[cid], w['src'])
            if st is None: bad.append(f'extras {cid}: why.src "{w["src"]}" 를 찾을 수 없음(body[i]·steps[i]·terms[i]·point, + 로 잇기)')
            else:
                a = re.sub(r'(이)?기때문이다|때문이다|기때문', '', _norm(w['a'])); s = _norm(st)
                bg = [a[i:i + 2] for i in range(len(a) - 1)]
                cov = sum(b in s for b in bg) / max(1, len(bg))
                if cov < 0.7: bad.append(f'extras {cid}: why.a 가 근거({w["src"]}) 글과 {cov:.0%}만 겹침 — 본문 문장으로 답한다')
        ex, fo = x.get('example'), x.get('follow')
        if bool(ex) != bool(fo): bad.append(f'extras {cid}: example 과 follow 는 짝으로 둔다')
        if ex:
            n_ex += 1
            if not (isinstance(ex.get('title'), str) and ex['title'].strip() and isinstance(ex.get('answer'), str) and ex['answer'].strip()): bad.append(f'extras {cid}: example.title·answer 가 비어 있음')
            if not (isinstance(ex.get('steps'), list) and 2 <= len(ex['steps']) <= 4 and all(isinstance(s, str) and s.strip() for s in ex['steps'])): bad.append(f'extras {cid}: example.steps 는 2~4줄')
        if fo and not all(isinstance(fo.get(k), str) and fo[k].strip() for k in ('q', 'answer', 'explain')): bad.append(f'extras {cid}: follow 의 q·answer·explain 이 비어 있음')
        for t in _strs(x):
            if t.count('<sup>') != t.count('</sup>') or t.count('<sub>') != t.count('</sub>'): bad.append(f'extras {cid}: 첨자 태그 짝이 안 맞음 · {t[:40]}')
            if re.search('[' + UNI + ']', t): bad.append(f'extras {cid}: 유니코드 첨자 대신 <sup>·<sub> 를 쓴다 · {t[:40]}')
            bare = re.sub(r'<(su[pb])>.*?</\1>', '', t)
            if re.search(r'(?<![\d.])10\s?[−-]\d', bare) or re.search(r'(?<![A-Za-z0-9])(?:[A-Z][a-z]?)+\d+(?![\d.,:])', _plain(bare)): bad.append(f'extras {cid}: 첨자가 사라진 듯함 · {_plain(bare)[:50]}')
            if re.search(r'\d(?:%|℃|J|N|kg|K|W)(?![A-Za-z])', _plain(t)): bad.append(f'extras {cid}: 숫자와 단위 사이 빈칸(교재처럼 "5 %"·"100 J") · {_plain(t)[:40]}')
    if n_why != len(cmap): bad.append(f'extras: why 가 {n_why}개 — 개념 {len(cmap)}개 모두에 하나씩')
    print(f'개념 덧붙임 why {n_why}개 · 예제→따라 풀기 {n_ex}개')
for b in bad[:30]: print('✗', b)
print('교재 데이터 점검', '통과' if not bad else f'실패 {len(bad)}건'); sys.exit(1 if bad else 0)
