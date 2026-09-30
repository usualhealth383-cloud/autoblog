#!/usr/bin/env python3
"""문제 은행 추출 — 본책(book/·book2/ chapter.html)의 바로바로 체크·STEP 1~3·알짜 해설·자료 파헤치기·직접 해보기와
강의용 교재의 오해/진실·빈칸에서 앱이 쓸 문제를 만든다.

산출물: data/bank.json  (문항)  ·  data/labs.json (자료 탐구·집에서 실험)
문항 형식: {id, lessonId, concept, step('qc'|1|2|3|'auto'), type('ox'|'blank'|'mc'|'multi'|'essay'), stem, source, choices, answer, explain, wrong, figure, difficulty}
  answer: ox → 'O'/'X' · blank → 정답 문자열 · mc/multi → 1~5 · essay → 모범 답안(explain에)
사용: python3 tools/extract_bank.py
"""
import json, re, pathlib, random
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'data'
ROMAN = {'I': '1', 'II': '2', 'III': '3'}
MARKS = '①②③④⑤'

import sys as _sys; _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _extract_common import txt as _txt, defs_map, selfcontain, strip_tags, plain_text


def txt(node, keep_bold=True):
    return _txt(node, keep_bold)


def lesson_code(path):
    """book/chapter-09 → 1304, book/chapter-i02 → 1102, book/chapter-03 → 1203, book2/chapter-2203 → 2203"""
    if path.parent.name == 'sample-chapter': return '1201'   # 빅뱅 단원은 표본 장(sample-chapter)에 있다 — 예전엔 빠져 문항이 자동 생성뿐이었다
    d = path.parent.name.replace('chapter-', '')
    if path.parts[-3] == 'book2': return d
    if d.startswith('i'): return '11' + d[1:].zfill(2)
    n = int(d)
    return f'12{n:02d}' if n <= 5 else f'13{n-5:02d}'


def parse_chapter(path):
    src = path.read_text(encoding='utf-8')
    code = lesson_code(path)
    markers = defs_map(src)
    soup = BeautifulSoup(src, 'html.parser')
    items, labs = [], []

    # ── 바로바로 체크: 개념 순서대로 ──
    for ci, qc in enumerate(soup.select('.quickcheck'), 1):
        ans_line = txt(qc.select_one('.qc-ans'), keep_bold=False).replace('정답', '', 1)
        answers = {int(m.group(1)): (m.group(2), (m.group(3) or '').strip(' ()'))
                   for m in re.finditer(r'(\d)\s*([OX])\s*(\([^)]*\))?', ans_line)}
        for li in qc.select('ol li'):
            no = li.select_one('.no'); n = int(txt(no, False)) if no else 0
            if no: no.extract()
            stem = re.sub(r'\(\s*O\s*,\s*X\s*\)\s*$', '', txt(li)).strip()
            a = answers.get(n)
            if not a: continue
            items.append({'id': f'{code}-c{ci}-{n}', 'lessonId': code, 'concept': int(ci), 'step': 'qc', 'type': 'ox', 'stem': stem,
                          'source': '', 'choices': [], 'answer': a[0], 'explain': a[1], 'wrong': '', 'figure': '', 'difficulty': '●○○'})

    # ── 정답표 · 해설 ──
    ans = {}
    tbl = None
    for t in soup.select('table.anstable'):          # 첫 칸 머리글이 '문항'인 표가 진짜 정답표
        th = t.select_one('tr th')
        if th and txt(th, False).startswith('문항'): tbl = t; break
    if tbl is None: tbl = soup.select_one('table.anstable')
    if tbl:
        rows = tbl.select('tr')
        nums = [txt(td, False) for td in rows[0].select('td')]
        vals = [txt(td, False) for td in rows[1].select('td')]
        ans = {int(n): v for n, v in zip(nums, vals) if n.isdigit()}
    sols = {}
    for sol in soup.select('.sol'):
        sno = sol.select_one('.sno'); n = int(txt(sno, False)) if sno and txt(sno, False).isdigit() else None
        if n is None: continue
        ps = [p for p in sol.find_all('p', recursive=False)]
        wb = sol.select_one('.wrongbox')
        sols[n] = {'explain': txt(ps[0]) if ps else '', 'wrong': txt(wb.select_one('p')) if wb and wb.select_one('p') else '',
                   'concept': txt(sol.select_one('.slink'), False)}
        sa = sol.select_one('.sans')                  # 해설 머리의 정답 — 정답표가 비었을 때의 보조
        if sa and txt(sa, False) and not ans.get(n): ans[n] = txt(sa, False)

    # ── STEP 1~3 ──
    step = None; qi = 0
    for el in soup.select('.step-head, .q'):
        if 'step-head' in el.get('class', []):
            step = 3 if 's3' in el['class'] else 2 if 's2' in el['class'] else 1; continue
        if step is None: continue
        qno = el.select_one('.qno'); n = int(txt(qno, False)) if qno and txt(qno, False).isdigit() else None
        if n is None: continue
        stem_el = el.select_one('.stem')
        diff = stem_el.select_one('.difficulty'); difficulty = txt(diff, False) if diff else ''
        tags = stem_el.select_one('.tags'); tag = txt(tags, False) if tags else ''
        for s in stem_el.select('.difficulty, .tags, .badge-data, .badge-essay'): s.extract()
        is_ox = bool(stem_el.select_one('.ox-answer'))
        for s in stem_el.select('.ox-answer'): s.extract()
        for s in stem_el.select('.blankline'): s.replace_with('＿＿＿')
        stem = txt(stem_el)
        bogi = el.select_one('.bogi-box')
        if bogi:
            bt = bogi.select_one('.bt');
            if bt: bt.extract()
            for br in bogi.find_all('br'): br.replace_with('\n')
            source = re.sub(r'[ \t]+', ' ', plain_text(bogi, '')).strip(); source = re.sub(r'\n\s*\n+', '\n', source)
        else: source = ''
        choices = [re.sub(r'^[①②③④⑤]\s*', '', txt(li)) for li in el.select('ul.choices li')]
        fig = el.select_one('figure svg'); figure = selfcontain(str(fig), markers, f'{code}q{n}') if fig else ''
        a = ans.get(n, ''); sol = sols.get(n, {})
        if is_ox: typ, answer = 'ox', a
        elif el.select_one('.essay-lines') or '서술' in a or a == '서술형': typ, answer = 'essay', ''
        elif choices and bogi: typ, answer = 'multi', (MARKS.index(a) + 1 if a in MARKS else None)
        elif choices: typ, answer = 'mc', (MARKS.index(a) + 1 if a in MARKS else None)
        else: typ, answer = 'blank', a
        m = re.search(r'개념\s*(\d)', tag) or re.search(r'개념\s*(\d)', sol.get('concept', ''))
        items.append({'id': f'{code}-q{n}', 'lessonId': code, 'concept': int(m.group(1)) if m else 0, 'step': step, 'type': typ,
                      'stem': stem, 'source': source, 'choices': choices, 'answer': answer,
                      'explain': sol.get('explain', ''), 'wrong': sol.get('wrong', ''), 'figure': figure,
                      'difficulty': difficulty or {1: '●○○', 2: '●●○', 3: '●●●'}[step]})
        qi += 1

    # ── 자료 파헤치기 · 직접 해보기 ──
    lab = soup.select_one('.lab')
    if lab:
        head = lab.select_one('.lab-head'); title = txt(head.select('span')[-1], False) if head and head.select('span') else ''
        body = lab.select_one('.lab-body')
        sections = {}; cur = None
        for ch in body.children:
            name = getattr(ch, 'name', None)
            if name == 'h4': cur = txt(ch, False); sections[cur] = []
            elif name and cur: sections[cur].append(ch)
        def sect(prefix):
            for k, v in sections.items():
                if k.startswith(prefix): return k, v
            return None, []
        _, data = sect('자료'); _, steps = sect('해석'); _, concl = sect('결론'); exp_k, exp = sect('직접')
        fig = body.select_one('figure svg')
        expoint = body.select_one('.expoint p')
        labs.append({'lessonId': code, 'title': title,
                     'data': ' '.join(txt(x) for x in data if getattr(x, 'name', None) == 'p'),
                     'figure': selfcontain(str(fig), markers, f'{code}lab') if fig else '',
                     'steps': [txt(li) for x in steps if getattr(x, 'name', None) == 'ol' for li in x.select('li')],
                     'conclusion': ' '.join(txt(x) for x in concl if getattr(x, 'name', None) == 'p'),
                     'exam': txt(expoint) if expoint else '',
                     'tryTitle': (exp_k or '').replace('직접 해보기', '').strip(' —-'),
                     'tryBody': ' '.join(txt(x) for x in exp if getattr(x, 'name', None) == 'p')})
    return items, labs


# 자동 문항 품질(2026-10-01 점검) — 앞 문장 없이는 뜻이 안 서는 문장, 시험 요령 문장, 그림을 가리키는 문장은 문제로 내지 않는다
CONNECT = re.compile(r'^(그런데|그래서|하지만|그러나|따라서|그러므로|또|또한|즉|반면|이때|이것|이는|이를|이 |그 |그것|저 |여기|위의?|아래|앞의?|왼쪽|오른쪽|가운데|한 칸|둘 다|모두 )')
FIGREF = re.compile(r'그림\s*\d|표\s*\d|왼쪽|오른쪽|가운데는|위 그림|아래 그림|[㉠㉡㉢](?![}])')
TIPS = re.compile(r'선지|함정|단골|오답|출제|시험에|문제에서')
SUBJ = re.compile(r'^[^.]{0,28}?\S(은|는|이|가|에는|에서는)\s')      # 첫 문장 앞쪽에 주어(은·는·이·가)가 있어야 홀로 선다
def standalone(t):
    t = re.sub(r'<[^>]+>', '', t).strip()
    return len(t) >= 12 and not CONNECT.match(t) and not FIGREF.search(t) and not TIPS.search(t) and bool(SUBJ.match(t))
PRED_END = ('다', '게', '고', '며', '해', '져', '라', '서', '아', '어', '은')
def kind(v):
    v = re.sub(r'<[^>]+>', '', v)
    if re.search(r'\d', v): return 'num'
    if v.endswith(PRED_END) and len(v) <= 5: return 'pred'
    return 'noun'


def auto_from_lecture(concepts):
    """강의용 교재에서 자동 생성: 오해✗ 문장 → X, 진실✓ 문장 → O · 빈칸 ㉠㉡㉢ → 4지선다(같은 종류의 다른 빈칸 정답이 오답 보기)"""
    items = []
    pool = []                                   # (값, 소단원, 단원) — 같은 값은 한 번만
    for c in concepts:
        for v in c['blanks'].values():
            if 1 <= len(re.sub(r'<[^>]+>', '', v)) <= 12 and v not in [p[0] for p in pool]: pool.append((v, c['lessonId'], c['lessonId'][:2]))
    rnd = random.Random(7)
    for c in concepts:
        code, no = c['lessonId'], int(c['no'])
        for i, m in enumerate(c['myths'], 1):
            x = strip_tags(m['x']).strip(); o = strip_tags(m['o']).strip()
            if x.endswith('.') and standalone(x):
                items.append({'id': f'{code}-m{no}-{i}x', 'lessonId': code, 'concept': no, 'step': 'auto', 'type': 'ox', 'stem': x,
                              'source': '', 'choices': [], 'answer': 'X', 'explain': o, 'wrong': '', 'figure': '', 'difficulty': '●○○'})
            if False and o.endswith('.') and standalone(o):   # 진실(✓) 문장은 오해 없이 홀로 읽으면 뜻이 비는 것이 많아(2026-10-01 점검 77건+) 문제로 내지 않고 X 문항의 해설로만 쓴다
                items.append({'id': f'{code}-m{no}-{i}o', 'lessonId': code, 'concept': no, 'step': 'auto', 'type': 'ox', 'stem': o,
                              'source': '', 'choices': [], 'answer': 'O', 'explain': '교재 개념 카드의 설명 그대로입니다.', 'wrong': '', 'figure': '', 'difficulty': '●○○'})
        # 빈칸: 뼈대·본문에서 {{㉠}} 이 든 문장을 뽑아 4지선다로
        texts = [s['d'] for s in c['steps']] + c['body']
        for k, v in c['blanks'].items():
            for t in texts:
                if '{{' + k + '}}' not in t: continue
                sent = next((x for x in re.split(r'(?<=[.!?])\s+', strip_tags(t)) if '{{' + k + '}}' in x), None)
                if not sent: break
                # 묻는 빈칸만 비우고, 같은 문장의 다른 빈칸은 답으로 채운다(빈칸 둘인데 하나만 묻던 것)
                stem = re.sub(r'\{\{([㉠㉡㉢])\}\}', lambda mm: '＿＿＿' if mm.group(1) == k else c['blanks'].get(mm.group(1), '＿＿＿'), sent).strip()
                bare = re.sub(r'<[^>]+>', '', v)
                if bare in re.sub(r'<[^>]+>', '', stem).replace('＿＿＿', ''): break       # 답이 문장에 이미 있다(거저 주는 문제)
                if not standalone(stem.replace('＿＿＿', '빈칸')) : break
                kv = kind(v)
                plain_stem = re.sub(r'<[^>]+>', '', stem)
                def ok(b): bb = re.sub(r'<[^>]+>', '', b); return b != v and bb not in bare and bare not in bb and bb not in plain_stem and kind(b) == kv and abs(len(bb) - len(bare)) <= 4
                near = [p[0] for p in pool if ok(p[0]) and p[1] == code] + [p[0] for p in pool if ok(p[0]) and p[2] == code[:2] and p[1] != code] + [p[0] for p in pool if ok(p[0]) and p[2] != code[:2]]
                near = list(dict.fromkeys(near))
                if len(near) < 3: break
                ch = rnd.sample(near[:12], 3) + [v]; rnd.shuffle(ch)
                items.append({'id': f'{code}-b{no}-{k}', 'lessonId': code, 'concept': no, 'step': 'auto', 'type': 'mc', 'stem': '빈칸에 들어갈 말은? ' + stem,
                              'source': '', 'choices': ch, 'answer': ch.index(v) + 1, 'explain': c['point'], 'wrong': '', 'figure': '', 'difficulty': '●○○'})
                break
    return items


def main():
    concepts = json.loads((OUT / 'concepts.json').read_text(encoding='utf-8'))
    items, labs = [], []
    for path in sorted(list((ROOT / 'book').glob('chapter-*/chapter.html')) + [ROOT / 'book' / 'sample-chapter' / 'chapter.html'] + list((ROOT / 'book2').glob('chapter-*/chapter.html'))):
        its, lbs = parse_chapter(path); items += its; labs += lbs
        print(f'{path.parent.name} → {lesson_code(path)}: 문항 {len(its)} · 탐구 {len(lbs)}')
    auto = auto_from_lecture(concepts); items += auto
    # 개념 번호는 그 소단원의 개념 수를 넘지 않게(바로바로 체크가 개념보다 많은 장이 있다 — 없는 개념 카드로 가던 것)
    nmax = {}
    for c in concepts: nmax[c['lessonId']] = max(nmax.get(c['lessonId'], 0), int(c['no']))
    for it in items:
        if it['concept'] and it['lessonId'] in nmax: it['concept'] = min(int(it['concept']), nmax[it['lessonId']])
    # 같은 OX 문장이 바로바로 체크와 자동(오해/진실)에 두 번 — 본책 것을 남긴다
    key = lambda t: re.sub(r'[\W_]+', '', re.sub(r'<[^>]+>', '', t))
    seen, keep = set(), []
    for it in items:
        k = (it['type'], key(it['stem'])) if it['type'] == 'ox' else None
        if k and k in seen: continue
        if k: seen.add(k)
        keep.append(it)
    print(f'  같은 OX 문장 중복 {len(items) - len(keep)}개 뺌'); items = keep
    # 개념 번호 없는 STEP 문항은 소단원 전체(0)로 둔다
    bad = [i['id'] for i in items if i['type'] in ('mc', 'multi') and not i['answer']]
    dropped = [i for i in items if i['type'] != 'essay' and not str(i.get('answer', '')).strip()]
    if dropped:
        print(f"  ! 정답이 없어 제외한 문항 {len(dropped)}개: " + ', '.join(d['id'] for d in dropped[:8]))
        items = [i for i in items if i not in dropped]
    (OUT / 'bank.json').write_text(json.dumps(items, ensure_ascii=False, indent=0), encoding='utf-8')
    (OUT / 'labs.json').write_text(json.dumps(labs, ensure_ascii=False, indent=0), encoding='utf-8')
    from collections import Counter
    na = sum(1 for i in items if i['step'] == 'auto')
    print(f'\n합계 문항 {len(items)} (본책 {len(items) - na} · 자동 {na}) · 탐구 {len(labs)} · 유형 {dict(Counter(i["type"] for i in items))}')
    if bad: print('정답 못 읽은 문항:', bad)


if __name__ == '__main__':
    main()
