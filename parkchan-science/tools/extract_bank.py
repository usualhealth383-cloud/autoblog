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


def txt(node, keep_bold=True):
    if node is None: return ''
    if keep_bold:
        html = ''.join(str(c) for c in node.contents)
        html = re.sub(r'<b\b[^>]*>', '<b>', html)
        html = re.sub(r'<(?!/?b>)[^>]+>', '', html)
        return re.sub(r'\s+', ' ', html).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').strip()
    return re.sub(r'\s+', ' ', node.get_text(' ')).strip()


def lesson_code(path):
    """book/chapter-09 → 1304, book/chapter-i02 → 1102, book/chapter-03 → 1203, book2/chapter-2203 → 2203"""
    d = path.parent.name.replace('chapter-', '')
    if path.parts[-3] == 'book2': return d
    if d.startswith('i'): return '11' + d[1:].zfill(2)
    n = int(d)
    return f'12{n:02d}' if n <= 5 else f'13{n-5:02d}'


def selfcontain(svg, markers, cid):
    used = set(re.findall(r'url\(#([^)]+)\)', svg)) | set(re.findall(r'href="#([^"]+)"', svg))
    need = [markers[i] for i in used if i in markers]
    if need:
        svg = re.sub(r'(<svg\b[^>]*>)', lambda m: m.group(1) + '<defs>' + ''.join(need) + '</defs>', svg, count=1)
    for i in sorted(set(re.findall(r'\bid="([^"]+)"', svg)), key=len, reverse=True):
        svg = svg.replace(f'id="{i}"', f'id="{i}-{cid}"').replace(f'url(#{i})', f'url(#{i}-{cid})').replace(f'href="#{i}"', f'href="#{i}-{cid}"')
    return svg


def parse_chapter(path):
    src = path.read_text(encoding='utf-8')
    code = lesson_code(path)
    markers = {m.group(1): m.group(0) for m in re.finditer(r'<marker id="([^"]+)".*?</marker>', src, re.S)}
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
    tbl = soup.select_one('table.anstable')
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
            source = re.sub(r'[ \t]+', ' ', bogi.get_text('')).strip(); source = re.sub(r'\n\s*\n+', '\n', source)
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


def auto_from_lecture(concepts):
    """강의용 교재에서 자동 생성: 오해✗ 문장 → X, 진실✓ 문장 → O · 빈칸 ㉠㉡㉢ → 4지선다(다른 개념의 정답이 오답 보기)"""
    items = []
    all_blanks = [v for c in concepts for v in c['blanks'].values() if 2 <= len(v) <= 12]
    rnd = random.Random(7)
    for c in concepts:
        code, no = c['lessonId'], int(c['no'])
        for i, m in enumerate(c['myths'], 1):
            x = re.sub(r'<[^>]+>', '', m['x']).strip(); o = re.sub(r'<[^>]+>', '', m['o']).strip()
            if x.endswith('.') and len(x) > 8:
                items.append({'id': f'{code}-m{no}-{i}x', 'lessonId': code, 'concept': no, 'step': 'auto', 'type': 'ox', 'stem': x,
                              'source': '', 'choices': [], 'answer': 'X', 'explain': o, 'wrong': '', 'figure': '', 'difficulty': '●○○'})
            if o.endswith('.') and len(o) > 8 and not re.search(r'반대다|틀렸다|아니다\.$', o):
                items.append({'id': f'{code}-m{no}-{i}o', 'lessonId': code, 'concept': no, 'step': 'auto', 'type': 'ox', 'stem': o,
                              'source': '', 'choices': [], 'answer': 'O', 'explain': '', 'wrong': '', 'figure': '', 'difficulty': '●○○'})
        # 빈칸: 뼈대·본문에서 {{㉠}} 이 든 문장을 뽑아 4지선다로
        texts = [s['d'] for s in c['steps']] + c['body']
        for k, v in c['blanks'].items():
            for t in texts:
                if '{{' + k + '}}' in t:
                    sent = next((x for x in re.split(r'(?<=[.!?])\s+', re.sub(r'<[^>]+>', '', t)) if '{{' + k + '}}' in x), None)
                    if not sent: break
                    stem = re.sub(r'\{\{[㉠㉡㉢]\}\}', '＿＿＿', sent).strip()
                    others = [b for b in all_blanks if b != v and abs(len(b) - len(v)) <= 4]
                    if len(others) < 3 or not (1 <= len(v) <= 12): break
                    ch = rnd.sample(others, 3) + [v]; rnd.shuffle(ch)
                    items.append({'id': f'{code}-b{no}-{k}', 'lessonId': code, 'concept': no, 'step': 'auto', 'type': 'mc', 'stem': '빈칸에 들어갈 말은? ' + stem,
                                  'source': '', 'choices': ch, 'answer': ch.index(v) + 1, 'explain': c['point'], 'wrong': '', 'figure': '', 'difficulty': '●○○'})
                    break
    return items


def main():
    concepts = json.loads((OUT / 'concepts.json').read_text(encoding='utf-8'))
    items, labs = [], []
    for path in sorted(list((ROOT / 'book').glob('chapter-*/chapter.html')) + list((ROOT / 'book2').glob('chapter-*/chapter.html'))):
        its, lbs = parse_chapter(path); items += its; labs += lbs
        print(f'{path.parent.name} → {lesson_code(path)}: 문항 {len(its)} · 탐구 {len(lbs)}')
    auto = auto_from_lecture(concepts); items += auto
    # 개념 번호 없는 STEP 문항은 소단원 전체(0)로 둔다
    bad = [i['id'] for i in items if i['type'] in ('mc', 'multi') and not i['answer']]
    (OUT / 'bank.json').write_text(json.dumps(items, ensure_ascii=False, indent=0), encoding='utf-8')
    (OUT / 'labs.json').write_text(json.dumps(labs, ensure_ascii=False, indent=0), encoding='utf-8')
    from collections import Counter
    print(f'\n합계 문항 {len(items)} (본책 {len(items)-len(auto)} · 자동 {len(auto)}) · 탐구 {len(labs)} · 유형 {dict(Counter(i["type"] for i in items))}')
    if bad: print('정답 못 읽은 문항:', bad)


if __name__ == '__main__':
    main()
