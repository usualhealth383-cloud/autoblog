#!/usr/bin/env python3
"""문제 은행 추출 — 본책(book/·book2/ chapter.html)의 바로바로 체크·STEP 1~3·알짜 해설·자료 파헤치기·직접 해보기와
강의용 교재의 오해/진실·빈칸에서 앱이 쓸 문제를 만든다.

산출물: data/bank.json  (문항)  ·  data/labs.json (자료 탐구·집에서 실험)
문항 형식: {id, lessonId, concept, step('qc'|1|2|3|'auto'), type('ox'|'blank'|'mc'|'multi'|'essay'), stem, source, choices, answer, explain, wrong, figure, difficulty}
  answer: ox → 'O'/'X' · blank → 정답 문자열 · mc/multi → 1~5 · essay → 모범 답안(explain에)
해설 공백 메우기(2026-10, 벤치마크 ★2) — 지어내지 않고 교재에 이미 있는 문장만 옮긴다(결정적·유료 API 없음)
  · 바로바로 체크 OX: qc-ans 괄호 → 없으면 알짜 정리 줄 → 그 쪽의 날개 노트 용어 → 그 쪽 본문 문장(글자 겹침이 충분할 때만)
  · 자동 OX(오해✗): '오해: … → 진실: …' · 자동 빈칸 4지선다: 답을 채운 원문 + 용어표 정의, 오답 보기마다 그 말이 원래 채우는 문장
사용: python3 tools/extract_bank.py [--out 폴더]   (--out: data/ 대신 그 폴더에 bank.json·labs.json 을 쓴다 — 시험용)
"""
import json, re, pathlib, random
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'data'
ROMAN = {'I': '1', 'II': '2', 'III': '3'}
MARKS = '①②③④⑤'

import sys as _sys; _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _extract_common import txt as _txt, defs_map, selfcontain, strip_tags, plain_text, supsub_uni


def mark_no(a):
    """'③' → 3. 빈칸·여러 글자는 None — ('' in MARKS 가 참이라 빈 정답이 ①로 읽히던 것)"""
    return MARKS.index(a) + 1 if len(a) == 1 and a in MARKS else None


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


# 근거 문장 고르기 — 한글·영숫자 두 글자 묶음(bigram)이 문항 문장과 얼마나 겹치는가. 흔한 어미는 뺀다
_STOP = {'이다', '한다', '된다', '있다', '없다', '는다', '에서', '으로', '하는', '되는', '에는', '이며', '하고'}
def _bigrams(t):
    t = re.sub(r'[^가-힣A-Za-z0-9]', '', re.sub(r'<[^>]+>', '', t))
    return {t[i:i + 2] for i in range(len(t) - 1)} - _STOP
def _overlap(stem, line):
    a = _bigrams(stem); s = len(a & _bigrams(line))
    return (s / len(a) if a else 0), s
EV_MIN, EV_SHARED = 0.4, 5          # 문항 bigram 의 40 % 이상, 5개 이상 겹쳐야 근거로 쓴다(낮추면 엉뚱한 줄이 붙는다 — 2026-10 점검)


def qc_evidence(stem, page, gist):
    """바로바로 체크 OX 의 해설 근거: 알짜 정리 줄(가산점) → 그 쪽 날개 노트 용어 → 그 쪽 본문 문장. 없으면 ''"""
    cands = [(g, 0.08, '알짜 정리: ' + g) for g in gist]
    if page is not None:
        for t in page.select('.wing .term'):
            b = t.find('b'); k = txt(b, False) if b else ''
            v = re.sub(r'^<b>.*?</b>\s*', '', txt(t)) if k else txt(t)
            cands.append((k + ' ' + v, 0, (f'<b>{k}</b>: ' if k else '') + v))
        for p in page.select('.main p'):
            if p.find_parent(class_='quickcheck') or p.find_parent(class_='gist'): continue
            for x in re.split(r'(?<=[.!?])\s+', txt(p)):
                bare = re.sub(r'<[^>]+>', '', x)
                if 8 <= len(bare) <= 160 and not TIPS.search(bare) and not re.search(r'(보자|볼까)[.!?]?$|\?$', bare): cands.append((x, 0, '교재: ' + x))   # '…담가 보자.' 같은 권유·물음은 근거가 아니다
    best, top = '', 0
    for line, bonus, out in cands:
        r, s = _overlap(stem, line)
        if r >= EV_MIN and s >= EV_SHARED and r + bonus > top: best, top = out, r + bonus
    return best


def parse_chapter(path):
    src = path.read_text(encoding='utf-8')
    code = lesson_code(path)
    markers = defs_map(src)
    soup = BeautifulSoup(src, 'html.parser')
    items, labs = [], []
    gist = [txt(li) for li in soup.select('.gist li')]

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
            explain = a[1] or qc_evidence(stem, qc.find_parent(class_='page'), gist)   # 괄호 풀이가 없으면 교재의 근거 줄
            items.append({'id': f'{code}-c{ci}-{n}', 'lessonId': code, 'concept': int(ci), 'step': 'qc', 'type': 'ox', 'stem': stem,
                          'source': '', 'choices': [], 'answer': a[0], 'explain': explain, 'wrong': '', 'figure': '', 'difficulty': '●○○'})

    # ── 정답표 · 해설 ──
    ans = {}
    tbl = None
    for t in soup.select('table.anstable'):          # 첫 칸 머리글이 '문항'인 표가 진짜 정답표
        th = t.select_one('tr th')
        if th and txt(th, False).startswith('문항'): tbl = t; break
    if tbl is None: tbl = soup.select_one('table.anstable')
    if tbl:
        rows = tbl.select('tr')
        for i in range(0, len(rows) - 1, 2):          # 문항 줄·정답 줄이 짝 — 24문항은 두 짝(1~12 / 13~24)
            nums = [txt(td, False) for td in rows[i].select('td')]
            vals = [txt(td, False) for td in rows[i + 1].select('td')]
            ans.update({int(n): v for n, v in zip(nums, vals) if n.isdigit()})
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
        must = bool(stem_el.select_one('.must'))          # '중요' 표시 — 발문 글자에서는 뺀다
        for s in stem_el.select('.difficulty, .tags, .badge-data, .badge-essay, .must'): s.extract()
        is_ox = bool(stem_el.select_one('.ox-answer'))
        for s in stem_el.select('.ox-answer'): s.extract()
        for s in stem_el.select('.blankline'): s.replace_with('＿＿＿')
        # 그림 밖 자료(2026-10): 탐구 과정·조건 줄(.exp)과 표(.qtab·.exptab)를 대단원·모의고사와 같은 data(줄)·table(표)로.
        # 예전엔 .exp 가 발문 글자에 이어 붙고(표는 칸이 뭉개져 '원소산소탄소…'), 발문 밖 .exp 는 통째로 빠졌다(2103-q21 반응식)
        fig = el.select_one('figure svg')
        exps = el.select('.exp')
        tabs = [tb for tb in el.select('table.qtab, table.exptab') if not tb.find_parent('figure')]
        data = []
        for x in exps:
            xc = __import__('copy').copy(x)
            for f in xc.select('figure, table'): f.extract()      # 그림은 figure 로, 표는 table 로 따로
            data += block_lines(xc)
        table = [table_rows(tb) for tb in tabs]
        order = el.find_all(True)
        first = min((order.index(x) for x in exps + tabs), default=None)
        fig_after = fig is not None and first is not None and first < order.index(fig)
        for x in exps + tabs: x.extract()
        for f in stem_el.select('figure'): f.extract()         # 발문 안에 든 그림의 글자(svg text)가 발문에 섞이지 않게
        stem = txt(stem_el)
        bogi = el.select_one('.bogi-box')
        if bogi:
            bt = bogi.select_one('.bt');
            if bt: bt.extract()
            for br in bogi.find_all('br'): br.replace_with('\n')
            source = re.sub(r'[ \t]+', ' ', plain_text(bogi, '')).strip(); source = re.sub(r'\n\s*\n+', '\n', source)
        else: source = ''
        choices = [re.sub(r'^[①②③④⑤]\s*', '', txt(li)) for li in el.select('ul.choices li')]
        figure = selfcontain(str(fig), markers, f'{code}q{n}') if fig else ''
        a = ans.get(n, ''); sol = sols.get(n, {})
        if is_ox: typ, answer = 'ox', a
        elif el.select_one('.essay-lines') or '서술' in a or a == '서술형': typ, answer = 'essay', ''
        elif choices and bogi: typ, answer = 'multi', (mark_no(a))
        elif choices: typ, answer = 'mc', (mark_no(a))
        else: typ, answer = 'blank', a
        m = re.search(r'개념\s*(\d)', tag) or re.search(r'개념\s*(\d)', sol.get('concept', ''))
        items.append({'id': f'{code}-q{n}', 'lessonId': code, 'concept': int(m.group(1)) if m else 0, 'step': step, 'type': typ,
                      'stem': stem, 'source': source, 'choices': choices, 'answer': answer,
                      'explain': sol.get('explain', ''), 'wrong': sol.get('wrong', ''), 'figure': figure,
                      'difficulty': difficulty or {1: '●○○', 2: '●●○', 3: '●●●'}[step], **({'must': True} if must else {}),
                      **({'data': '\n'.join(data)} if data else {}), **({'table': table} if table else {}), **({'figAfter': True} if fig_after else {})})
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
    origin = {}                                 # 값 → (개념, 빈칸) — 오답 보기 해설: 그 말이 원래 채우는 문장
    for c in concepts:
        for k, v in c['blanks'].items():
            if 1 <= len(re.sub(r'<[^>]+>', '', v)) <= 12 and v not in [p[0] for p in pool]: pool.append((v, c['lessonId'], c['lessonId'][:2])); origin[v] = (c, k)
    bare_of = lambda t: re.sub(r'<[^>]+>', '', t).strip()

    def filled(c, k):
        """빈칸 k 가 든 원문 문장 — 모든 빈칸을 답으로 채우고 k 의 답은 굵게"""
        for t in [s['d'] for s in c['steps']] + c['body']:
            if '{{' + k + '}}' not in t: continue
            sent = next((x for x in re.split(r'(?<=[.!?])\s+', strip_tags(t)) if '{{' + k + '}}' in x), '')
            def fill(mm):
                val = c['blanks'].get(mm.group(1), '')
                if mm.group(1) != k: return val
                before = mm.string[:mm.start()]
                return val if before.count('<b>') > before.count('</b>') else f'<b>{bare_of(val)}</b>'   # 이미 굵은 자리면 겹쳐 굵게 하지 않는다
            return re.sub(r'\{\{([㉠㉡㉢])\}\}', fill, sent).strip()
        return ''

    def term_def(word, c):
        """용어표에서 그 말의 뜻 — 같은 개념 → 같은 소단원 → 전체. '라이다(LiDAR)'처럼 괄호가 붙은 용어도 찾는다"""
        same = [c] + [x for x in concepts if x['lessonId'] == c['lessonId'] and x is not c] + [x for x in concepts if x['lessonId'] != c['lessonId']]
        for x in same:
            for t in x.get('terms', []):
                k = bare_of(t['k'])
                if word and (k == word or re.sub(r'\s*\(.*?\)\s*', '', k) == word): return t['v']
        return ''
    rnd = random.Random(7)
    for c in concepts:
        code, no = c['lessonId'], int(c['no'])
        for i, m in enumerate(c['myths'], 1):
            x = strip_tags(m['x']).strip(); o = strip_tags(m['o']).strip()
            if x.endswith('.') and standalone(x):
                items.append({'id': f'{code}-m{no}-{i}x', 'lessonId': code, 'concept': no, 'step': 'auto', 'type': 'ox', 'stem': x,
                              'source': '', 'choices': [], 'answer': 'X', 'explain': f'오해: {x} → 진실: {o}', 'wrong': '', 'figure': '', 'difficulty': '●○○'})
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
                # 해설: 답을 채운 원문 + 용어표 정의(없으면 개념 포인트) · 오답 보기: 그 말의 뜻이나 그 말이 원래 채우는 문장
                d = term_def(bare, c)
                explain = filled(c, k) + (f' — <b>{bare}</b>: {d}' if d else (' ' + c['point'] if c['point'] else ''))
                wl = []
                for j, b in enumerate(ch):
                    if b == v: continue
                    oc = origin.get(b); bb = bare_of(b)
                    why = term_def(bb, oc[0] if oc else c) or (filled(*oc) if oc else '')
                    if why: wl.append(f'<b>{MARKS[j]}</b> {bb} — {why}')
                items.append({'id': f'{code}-b{no}-{k}', 'lessonId': code, 'concept': no, 'step': 'auto', 'type': 'mc', 'stem': '빈칸에 들어갈 말은? ' + stem,
                              'source': '', 'choices': ch, 'answer': ch.index(v) + 1, 'explain': explain.strip(), 'wrong': ' '.join(wl), 'figure': '', 'difficulty': '●○○'})
                break
    return items


# ══════════ 대단원 마무리 · 실전 모의고사 (2026-10) ══════════
# 소단원 문항과 같은 필드 + step('unit'|'mock'|'recap') · lessons(이어지는 소단원들, 첫째가 lessonId) · book · unit · points(모의고사 배점)
# 모의고사는 exam: 'hakpyeong'(고1 학평형, M{권}-q{번호}) | 'suneung'(수능형, 제1회 MS-q{번호} · 제2회 MS2-q{번호}, book '1+2', area 행동 영역 · tags 융합/고난도)
# · round: 회차(1, 2 …) — 같은 exam·book 안에서 회차를 가른다(수능형은 두 회가 모두 book '1+2')
# 그림 밖 자료: data(탐구 과정·조건 줄, '\n' 으로 줄 나눔) · table(표: 줄마다 [['h'|'d', 글자], …]) · ask(그림·자료 뒤의 발문)
# 문제 은행 보통 풀이(bankPool)에는 나오지 않는다 — 앱의 '대단원 마무리'·'실전 모의고사'에서만
LESSON_SET = None
ROMAN_IDX = {'I': 1, 'II': 2, 'III': 3}


def lesson_refs(text, book, unit=None):
    """'→ I-03 (I-02 · I-04)'·'II-01 + II-03'·'▶ I-01 개념 2' → ['1103','1102','1104'] (적힌 순서, 중복 없이, 있는 소단원만)
    unit 을 주면 로마 숫자 없는 '01·03' 도 그 단원의 소단원으로 읽는다"""
    out = []
    for m in re.finditer(r'(?<![A-Za-z])(III|II|I)-(\d{2})(?!\d)', text):
        out.append(f'{book}{ROMAN[m.group(1)]}{m.group(2)}')
    if unit:
        bare = re.sub(r'(?<![A-Za-z])(III|II|I)-\d{2}', ' ', text)
        for m in re.finditer(r'(?<![\d.])(0\d)(?![\d.])', bare): out.append(f'{book}{ROMAN[unit]}{m.group(1)}')
    seen = []
    for l in out:
        if l not in seen and (LESSON_SET is None or l in LESSON_SET): seen.append(l)
    return seen


def lesson_refs_books(text, book):
    """'▶ 통합과학2 I-05 개념 1 + 통합과학1 III-05 개념 2' → ['2105', '1305'] — 수능형(두 권 전 범위) 해설용.
    '통합과학1'·'통합과학2'(또는 '통과1') 뒤의 참조는 그 권으로 읽고, 권 표시가 없으면 앞의 권(처음엔 book)을 이어 쓴다"""
    out, cur = [], book
    for m in re.finditer(r'(?:통합과학|통과)\s*([12])|(?<![A-Za-z])(III|II|I)-(\d{2})(?!\d)', text):
        if m.group(1): cur = m.group(1); continue
        out.append(f'{cur}{ROMAN[m.group(2)]}{m.group(3)}')
    seen = []
    for l in out:
        if l not in seen and (LESSON_SET is None or l in LESSON_SET): seen.append(l)
    return seen


def frag_txt(h):
    """HTML 조각 → txt(<b>·<sup>·<sub> 만 남김)"""
    return txt(BeautifulSoup(h, 'html.parser'))


def br_lines(node):
    """<br> 로 나눈 줄 — 줄마다 <b>·<sup>·<sub> 를 남긴다"""
    return [t for t in (frag_txt(p) for p in re.split(r'<br\s*/?>', node.decode_contents())) if t]


def block_lines(node, skip=('bt',)):
    """자료·보기 상자 → 줄 목록. 안에 줄 div(it·bl·dt·tg)가 있으면 그것을, 아니면 <br> 로 나눈다. 표는 따로(block_tables)"""
    divs = [d for d in node.find_all('div', recursive=False) if not set(d.get('class', [])) & set(skip)]
    if divs:
        out = []
        for d in divs:
            t = txt(d)
            if set(d.get('class', [])) & {'dt', 'tg'}: t = f'<b>{t}</b>'
            if t: out.append(t)
        return out
    n = __import__('copy').copy(node)
    for s in n.select('.' + ', .'.join(skip)): s.extract()
    for s in n.select('table'): s.extract()
    return br_lines(n)


def table_rows(tb):
    return [[['h' if c.name == 'th' else 'd', txt(c)] for c in tr.find_all(['th', 'td'], recursive=False)] for tr in tb.select('tr')]


def answer_table(soup):
    """정답표(문항/번호 · 정답 · 배점 줄) → {번호: (정답, 배점)}"""
    out = {}
    for tbl in soup.select('table.anstable, table.anst'):
        nums = []
        for tr in tbl.select('tr'):
            th = tr.find('th'); lab = txt(th, False) if th else ''
            vals = [txt(td, False) for td in tr.find_all('td')]
            if lab.startswith(('문항', '번호')): nums = vals
            elif lab.startswith('정답'):
                for n, v in zip(nums, vals):
                    if n.isdigit(): out.setdefault(int(n), ['', None])[0] = v
            elif lab.startswith('배점'):
                for n, v in zip(nums, vals):
                    if n.isdigit() and re.fullmatch(r'\d+(\.\d+)?', v): out.setdefault(int(n), ['', None])[1] = float(v)
    return out


def solutions(soup):
    """해설 → {번호: {explain, wrong, link}} — 대단원 마무리·모의고사 1회(.sno·.sans·.slink·.wrongbox·.rubric)와
    모의고사 2회(.n·.a·.rv, 본문 안 '<b>바로알기</b>') 두 짜임"""
    sols = {}
    for sol in soup.select('.sol'):
        sno = sol.select_one('.sno') or sol.select_one('b.n')
        n = txt(sno, False) if sno else ''
        if not n.isdigit(): continue
        n = int(n)
        link = ' '.join(txt(x, False) for x in sol.select('.slink, .rv'))
        if sol.select_one('.shead'):
            ps = sol.find_all('p', recursive=False)
            explain = ' '.join(txt(p) for p in ps)
            wb = sol.select_one('.wrongbox')
            wrong = ' '.join(txt(p) for p in wb.select('p')) if wb else ''
            rub = sol.select_one('table.rubric')
            if rub:                                    # 서술형: 채점 요소 + '이렇게 쓰면 0점'
                rows = [[txt(td) for td in tr.find_all('td')] for tr in rub.select('tr')]
                crit = ' '.join(f'{r[0]} ({r[1]})' for r in rows if len(r) >= 2)
                wt = txt(wb.select_one('.wt'), False) if wb and wb.select_one('.wt') else ''
                wrong = crit + (f' — {wt}: {wrong}' if wrong else '')
        else:
            n2 = __import__('copy').copy(sol)
            for s in n2.select('b.n, span.a, span.rv, span.bh, span.tg2, .analysis'): s.extract()
            h = txt(n2)
            parts = re.split(r'<b>\s*바로알기\s*</b>', h, maxsplit=1)
            explain = parts[0].strip(); wrong = parts[1].strip() if len(parts) > 1 else ''
        sols[n] = {'explain': explain, 'wrong': wrong, 'link': link,
                   'area': ' '.join(txt(x, False) for x in sol.select('span.bh')).lstrip('· ').strip(),
                   'tags': [txt(x, False) for x in sol.select('span.tg2')]}
    return sols


def item_common(el, stem_sel):
    """문항 상자에서 그림·자료·표·보기·선지를 읽는다"""
    fig = el.find('svg')                                # 그림은 figure 안에, 모의고사 몇 문항은 자료 상자(.dta) 안에 있다
    data, table = [], []
    for x in el.select('.exp, .dta'): data += block_lines(x, ('bt',))
    for tb in el.select('table.qtab, table.xt'): table += [table_rows(tb)]
    bogi = el.select_one('.bogi-box, .bogi')
    source = '\n'.join(block_lines(bogi)) if bogi else ''
    choices = [re.sub(r'^[①②③④⑤]\s*', '', txt(li)) for li in el.select('ul.choices li, ul.ch li')]
    after = False
    if fig is not None:                                # 자료·표가 그림보다 앞에 있으면 앱도 그 차례로(figAfter)
        order = el.find_all(True); fi = order.index(fig)
        first = min((order.index(x) for x in el.select('.exp, .dta, table.qtab, table.xt')), default=None)
        after = first is not None and first < fi
    return fig, data, table, source, choices, after


def parse_summary(path, markers=None):
    """book/summary-2/summary.html → 대단원 마무리 16문항(마무리 12 · 고난도 4) + 핵심 정리 빈칸(되살리기)"""
    src = path.read_text(encoding='utf-8')
    book = '1' if path.parts[-3] == 'book' else '2'
    ui = int(path.parent.name.split('-')[1]); unit = ['I', 'II', 'III'][ui - 1]
    markers = defs_map(src); soup = BeautifulSoup(src, 'html.parser')
    ans = answer_table(soup); sols = solutions(soup)
    items, warn = [], []
    for el in soup.select('.q'):
        qno = el.select_one('.qno'); n = int(txt(qno, False)) if qno and txt(qno, False).isdigit() else None
        if n is None: continue
        stem_el = el.select_one('.stem')
        diff = stem_el.select_one('.difficulty'); difficulty = re.sub(r'\s*\[.*?\]\s*', '', txt(diff, False)) if diff else ''
        tags = stem_el.select_one('.tags'); tag = txt(tags, False) if tags else ''
        must = bool(stem_el.select_one('.must'))
        for s in stem_el.select('.difficulty, .tags, .badge-data, .badge-essay, .must'): s.extract()
        for s in stem_el.select('.blankline'): s.replace_with('＿＿＿')
        stem = txt(stem_el)
        fig, data, table, source, choices, after = item_common(el, '.stem')
        a = (ans.get(n) or ['', None])[0]; sol = sols.get(n, {})
        if el.select_one('.essay-lines') or '서술' in a: typ, answer = 'essay', ''
        elif choices and source: typ, answer = 'multi', (mark_no(a))
        elif choices: typ, answer = 'mc', (mark_no(a))
        else: warn.append(f'{path.parent.name} {n}: 유형을 모름'); continue
        lessons = lesson_refs(sol.get('link', '') + ' ' + tag.split('|')[-1], book)
        if not lessons: warn.append(f'{path.parent.name} {n}: 소단원 연결 없음')
        cid = f'U{book}{ui}q{n}'
        it = {'id': f'U{book}-{ui}-q{n}', 'lessonId': lessons[0] if lessons else f'{book}{ui}01', 'lessons': lessons, 'book': book, 'unit': unit,
              'concept': 0, 'step': 'unit', 'type': typ, 'stem': stem, 'source': source, 'choices': choices, 'answer': answer,
              'explain': sol.get('explain', ''), 'wrong': sol.get('wrong', ''), 'figure': selfcontain(str(fig), markers, cid) if fig else '',
              'difficulty': difficulty or ('●●●' if n > 12 else '●●○')}
        if data: it['data'] = '\n'.join(data)
        if table: it['table'] = table
        if after: it['figAfter'] = True
        if must: it['must'] = True
        items.append(it)
    recap, rw = parse_recap(soup, book, ui, unit)
    return items, recap, warn + rw


SEN = '\u2063'                                         # 채운 답 뒤 표시(띄어쓰기 손질용, 남지 않는다)
PARTICLE = re.compile(SEN + r'\s+((?:의|을|를|은|는|이|가|에|에서|로|으로|와|과|해|도|만)(?=[\s,.)·]|$))')


def parse_recap(soup, book, ui, unit):
    """핵심 정리 '빈칸으로 다시 쓰기' → 빈칸(blank) 되살리기 문항. 정답 수와 빈칸 수가 맞고 모든 빈칸이 문장 안에 있을 때만 낸다"""
    import copy
    page = next((p for p in soup.select('.page') if p.select_one('.rc-grid')), None)
    if page is None: return [], [f'{book}-{unit}: 핵심 정리 쪽 없음']
    ae = page.select_one('.rc-ans .ra') or page.select_one('.rc-ans')
    at = re.sub(r'^\s*정답\s*', '', txt(ae)) if ae else ''
    blanks = page.select('span.blk, span.bl')
    num = lambda sp: txt(sp.find(['b', 'i']) or sp, False)
    nums = [int(num(s)) for s in blanks if num(s).isdigit()]
    N = len(nums)
    if not N or sorted(nums) != list(range(1, N + 1)): return [], [f'{book}-{unit}: 빈칸 번호가 1~N 이 아님 {nums}']
    answers, pos = {}, 0
    for k in range(1, N + 1):
        m = re.compile(rf'(?:^|(?<=\s)){k}\s').search(at, pos)
        if not m: return [], [f'{book}-{unit}: 빈칸 정답 {k} 를 못 찾음']
        if k > 1: answers[k - 1] = at[start:m.start()].strip()
        start, pos = m.end(), m.end()
    answers[N] = at[start:].strip()
    if any(not v or len(re.sub(r'<[^>]+>', '', v)) > 30 for v in answers.values()): return [], [f'{book}-{unit}: 빈칸 정답이 비었거나 너무 김']
    uni = lambda h: re.sub(r'<[^>]+>', '', supsub_uni(h)).strip()
    items = []
    for sp in blanks:
        k = int(num(sp)); box = sp.find_parent(class_=['rc-box', 'rc'])
        hno = box.select_one('.rc-h .no, .rc-h .rc-no') if box else None; ht = box.select_one('.rc-h .t, .rc-h .rc-t') if box else None
        box_no = txt(hno, False) if hno else ''; title = txt(ht, False) if ht else ''
        cont = sp.find_parent(['td', 'th', 'p', 'li']) or sp.find_parent(class_='rc-line')
        if cont is None: return [], [f'{book}-{unit}: 빈칸 {k} 의 문장을 못 찾음']
        def filled(node):
            c = copy.copy(node)
            for b in c.select('span.blk, span.bl'):
                bk = int(num(b)); b.replace_with('＿＿＿' if bk == k else BeautifulSoup(answers[bk] + SEN, 'html.parser'))
            return c
        lead = ''
        if cont.name in ('td', 'th'):
            tr = cont.find_parent('tr'); tbl = cont.find_parent('table'); rows = tbl.find_all('tr')
            cells = tr.find_all(['th', 'td'], recursive=False); ci = cells.index(cont)
            head = rows[0] if rows and not rows[0].find('td') else None
            if tr is head:                             # 머리 줄의 빈칸 — 머리 줄 전체 + 바로 아래 칸
                ctx = ' · '.join(t for t in (txt(filled(c)) for c in cells) if t)
                below = rows[1].find_all(['th', 'td'], recursive=False) if len(rows) > 1 else []
                if ci < len(below) and txt(below[ci]): ctx += f' ({txt(filled(cells[ci]))}: {txt(filled(below[ci]))})'
            else:
                rh = next((c for c in reversed(cells[:ci]) if c.name == 'th'), None)   # 같은 줄에서 바로 앞의 머리 칸
                hc = head.find_all(['th', 'td'], recursive=False) if head is not None else []
                ch = hc[ci] if ci < len(hc) else None
                lab = ' · '.join(t for t in (txt(rh, False) if rh else '', txt(ch, False) if ch is not None else '') if t)
                lead = txt(rh, False) if rh else ''
                ctx = (f'{lab}: ' if lab else '') + txt(filled(cont))
                if head is None and len([c for c in cells if c.name == 'td']) >= 2 and [c.name for c in cells].count('th') == 1:     # 머리 줄 없는 여러 칸 표 — 같은 칸의 다른 줄을 곁들인다
                    for r in rows:
                        if r is tr: continue
                        rc = r.find_all(['th', 'td'], recursive=False)
                        if ci < len(rc) and rc[0].name == 'th' and txt(rc[ci]): ctx += f' ({txt(rc[0], False)}: {txt(filled(rc[ci]))})'
        else:
            ls = br_lines(filled(cont)); at_ = next((i for i, s in enumerate(ls) if '＿＿＿' in s), None)
            if at_ is None: return [], [f'{book}-{unit}: 빈칸 {k} 의 줄을 못 찾음']
            ctx = ls[at_]
            if ctx.startswith('→') and at_: ctx = ls[at_ - 1] + ' ' + ctx      # '→ 자연선택 → …' 처럼 앞 줄에 이어지는 줄
            m = re.match(r'^<b>([\dI·\-]+)</b>\s*', ctx)
            if m: lead = m.group(1); ctx = ctx[m.end():]
        # 소단원: 상자 번호(01) — '잇기'·'01~04' 상자는 그 줄의 머리(01 ⇄ 02 · 01·I-02)
        if re.fullmatch(r'0\d', box_no): lessons = lesson_refs(box_no, book, unit)
        else: lessons = lesson_refs(lead, book, unit) or lesson_refs(box_no.split('~')[0], book, unit)
        if not lessons: lessons = [f'{book}{ui}01']
        a = answers[k]
        tidy = lambda t: PARTICLE.sub(r'\1', t).replace(SEN, '')     # 교재의 빈칸 상자 뒤 띄어쓰기('집단 의') — 답을 채우면 붙인다
        expl = tidy(ctx.replace('＿＿＿', f'<b>{a}</b>{SEN}')); ctx = tidy(ctx)
        stem = (f'[{title}] ' if title else '') + ctx
        items.append({'id': f'U{book}-{ui}-b{k}', 'lessonId': lessons[0], 'lessons': lessons, 'book': book, 'unit': unit, 'concept': 0,
                      'step': 'recap', 'type': 'blank', 'stem': stem, 'source': '', 'choices': [], 'answer': uni(a),
                      'explain': expl, 'wrong': '', 'figure': '', 'difficulty': '●○○'})
    items.sort(key=lambda x: int(x['id'].split('-b')[1]))
    return items, []


def parse_mock(path):
    """book/mock-exam/exam.html → 실전 모의고사 25문항(배점 합 50) — 학평형(exam 'hakpyeong', id M{권}-q{번호}, round 1)
    book2/mock-exam-suneung/exam.html → 수능형 제1회(exam 'suneung', id MS-q{번호}, 통합과학 1·2 전 범위 — book '1+2', round 1)
    book2/mock-exam-suneung-2/exam.html → 수능형 제2회(id MS2-q{번호}, round 2) — 폴더 이름 끝의 '-N' 이 회차"""
    from bs4 import Comment
    src = path.read_text(encoding='utf-8')
    book = '1' if path.parts[-3] == 'book' else '2'
    sn = path.parent.name.startswith('mock-exam-suneung')
    rm = re.search(r'-(\d+)$', path.parent.name); rnd = int(rm.group(1)) if rm else 1
    tag = (f'수능형 제{rnd}회' if sn else f'{book}권 제{rnd}회')
    markers = defs_map(src); soup = BeautifulSoup(src, 'html.parser')
    ans = answer_table(soup); sols = solutions(soup)
    items, warn = [], []
    for el in soup.select('.qq'):
        qn = el.select_one('b.qn'); n = re.sub(r'\D', '', txt(qn, False)) if qn else ''
        if not n: continue
        n = int(n)
        com = el.find_previous(string=lambda t: isinstance(t, Comment) and re.match(rf'\s*{n}\.\s', t))
        pts_el = el.select_one('.pts'); pts_txt = txt(pts_el, False) if pts_el else ''
        for s in el.select('b.qn, .pts'): s.extract()
        stems = [txt(p) for p in el.select('p.stem')]
        fig, data, table, source, choices, after = item_common(el, 'p.stem')
        a, p = ans.get(n) or ['', None]
        if p is None:
            m = re.search(r'([\d.]+)\s*점', pts_txt); p = float(m.group(1)) if m else None
        sol = sols.get(n, {})
        refs = sol.get('link', '') + ' ' + (str(com) if com else '')
        lessons = lesson_refs_books(refs, book) if sn else lesson_refs(refs, book)
        if not lessons: warn.append(f'모의고사 {tag} {n}: 소단원 연결 없음')
        typ = 'multi' if source else 'mc'
        qid = (f'MS-q{n}' if rnd == 1 else f'MS{rnd}-q{n}') if sn else (f'M{book}-q{n}' if rnd == 1 else f'M{book}r{rnd}-q{n}')
        it = {'id': qid, 'lessonId': lessons[0] if lessons else f'{book}101', 'lessons': lessons, 'book': '1+2' if sn else book,
              'unit': next((k for k, v in ROMAN.items() if lessons and lessons[0][1] == v), ''),
              'concept': 0, 'step': 'mock', 'type': typ, 'stem': stems[0] if stems else '', 'source': source, 'choices': choices,
              'answer': mark_no(a), 'explain': sol.get('explain', ''), 'wrong': sol.get('wrong', ''),
              'figure': selfcontain(str(fig), markers, (f'MS{n}' if rnd == 1 else f'MS{rnd}n{n}') if sn else (f'M{book}q{n}' if rnd == 1 else f'M{book}r{rnd}q{n}')) if fig else '', 'difficulty': '', 'points': p,
              'exam': 'suneung' if sn else 'hakpyeong', 'round': rnd}
        if sn:
            if sol.get('area'): it['area'] = sol['area']           # 행동 영역(평가원 8가지)
            if sol.get('tags'): it['tags'] = sol['tags']           # '융합' · '고난도'
        if mark_no(a) is None: warn.append(f'모의고사 {qid}: 정답표에 정답 없음')
        if p not in (1.5, 2.0, 2.5): warn.append(f'모의고사 {qid}: 배점 {p}')
        mp = re.search(r'([\d.]+)\s*점', pts_txt)
        if mp and p is not None and float(mp.group(1)) != p: warn.append(f'모의고사 {qid}: 문제지 배점 {pts_txt} ≠ 정답표 {p:g}')   # 글자 포함 비교는 '2' ⊂ '[2.5점]' 을 놓쳤다
        if len(stems) > 1: it['ask'] = ' '.join(stems[1:])
        if data: it['data'] = '\n'.join(data)
        if table: it['table'] = table
        if after: it['figAfter'] = True
        items.append(it)
    tot = sum(i['points'] or 0 for i in items)
    if len(items) != 25 or abs(tot - 50) > 1e-9: warn.append(f'모의고사 {tag}: {len(items)}문항 · 배점 합 {tot}')
    nums = sorted(int(i['id'].split('-q')[1]) for i in items)
    if nums != list(range(1, len(items) + 1)): warn.append(f'모의고사 {tag}: 문항 번호 {nums}')
    miss = [n for n in nums if n not in sols]
    if miss: warn.append(f'모의고사 {tag}: 해설 없는 문항 {miss}')
    empty = [i['id'] for i in items if not i['explain'] and not i['wrong']]
    if empty: warn.append(f'모의고사 {tag}: 해설이 빈 문항 {empty}')
    extra = sorted(set(sols) - set(nums)) + sorted(k for k in ans if k not in nums)
    if extra: warn.append(f'모의고사 {tag}: 문제지에 없는 번호의 정답·해설 {extra}')
    if sn:
        noarea = [i['id'] for i in items if not i.get('area')]
        if noarea: warn.append(f'모의고사 {tag}: 행동 영역 없는 해설 {noarea}')
    return items, warn


def unit_mock():
    """대단원 마무리 6 + 모의고사(학평형 2 · 수능형 2) — (문항, 경고)"""
    items, warns = [], []
    for b in ('book', 'book2'):
        for k in (1, 2, 3):
            p = ROOT / b / f'summary-{k}' / 'summary.html'
            if not p.exists(): warns.append(f'{p} 없음'); continue
            its, rc, w = parse_summary(p); items += its + rc; warns += w
            print(f'{b}/summary-{k}: 마무리 {len(its)} · 핵심 정리 빈칸 {len(rc)}' + (f' · ! {"; ".join(w)}' if w else ''))
            if len(its) != 16: warns.append(f'{b}/summary-{k}: 문항 {len(its)} (16 이어야)')
        for d in ('mock-exam', 'mock-exam-suneung', 'mock-exam-suneung-2'):   # 학평형 · 수능형 제1·2회(book2 에만)
            p = ROOT / b / d / 'exam.html'
            if p.exists():
                its, w = parse_mock(p); items += its; warns += w
                print(f'{b}/{d}: {len(its)}문항 · 배점 합 {sum(i["points"] or 0 for i in its):g}' + (f' · ! {"; ".join(w)}' if w else ''))
    return items, warns


def main():
    global LESSON_SET
    out = OUT
    if '--out' in _sys.argv[1:-1]:
        out = pathlib.Path(_sys.argv[_sys.argv.index('--out') + 1]).resolve(); out.mkdir(parents=True, exist_ok=True)
    concepts = json.loads((OUT / 'concepts.json').read_text(encoding='utf-8'))
    LESSON_SET = {c['lessonId'] for c in concepts}
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
    um, um_warn = unit_mock(); items += um
    # 개념 번호 없는 STEP 문항은 소단원 전체(0)로 둔다
    bad = [i['id'] for i in items if i['type'] in ('mc', 'multi') and not i['answer']]
    dropped = [i for i in items if i['type'] != 'essay' and not str(i.get('answer', '')).strip()]
    if dropped:
        print(f"  ! 정답이 없어 제외한 문항 {len(dropped)}개: " + ', '.join(d['id'] for d in dropped[:8]))
        items = [i for i in items if i not in dropped]
    (out / 'bank.json').write_text(json.dumps(items, ensure_ascii=False, indent=0), encoding='utf-8')
    (out / 'labs.json').write_text(json.dumps(labs, ensure_ascii=False, indent=0), encoding='utf-8')
    if out != OUT: print(f'  → {out} 에 썼습니다(data/ 는 그대로)')
    from collections import Counter
    na = sum(1 for i in items if i['step'] == 'auto')
    print(f'\n합계 문항 {len(items)} (본책 {len(items) - na} · 자동 {na}) · 탐구 {len(labs)} · 유형 {dict(Counter(i["type"] for i in items))}')
    if bad: print('정답 못 읽은 문항:', bad)
    st = Counter(str(i['step']) for i in items)
    ex = Counter(i.get('exam') for i in items if i['step'] == 'mock')
    rd = Counter((i.get('exam'), i.get('round')) for i in items if i['step'] == 'mock')
    print(f"대단원 마무리 {st['unit']} · 핵심 정리 빈칸 {st['recap']} · 모의고사 {st['mock']} (학평형 {ex['hakpyeong']} · 수능형 {ex['suneung']} = " + ' · '.join(f'제{r}회 {k}' for (e, r), k in sorted(rd.items()) if e == 'suneung') + ") (문제 은행 보통 풀이에는 나오지 않음)")
    for w in um_warn: print('  !', w)


if __name__ == '__main__':
    main()
