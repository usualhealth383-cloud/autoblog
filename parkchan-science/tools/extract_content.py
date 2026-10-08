#!/usr/bin/env python3
"""강의용 교재(L-XXXX.html)에서 개념·문항을 뽑아 앱이 쓸 데이터로 만든다.

교재는 조판된 HTML이라 그대로는 배달할 수 없다. 개념 하나를 한 덩어리로 떼어 내고,
그림은 SVG 파일로 따로 저장해 앱에서 그대로 띄운다(다시 그리지 않는다).

사용: python3 tools/extract_content.py [출력폴더]     기본값 data/
산출물: data/concepts.json · data/quizzes.json · data/figures/<개념id>.svg
"""
import json, re, sys, pathlib
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 통합과학1(book/) 이 앞, 통합과학2(book2/) 가 뒤 — 앱의 '오늘의 개념' 순서다
SRCS = [(ROOT / 'book' / 'lecture-edition', 'L-1[0-9][0-9][0-9].html'),
        (ROOT / 'book2' / 'lecture-edition', 'L-2[0-9][0-9][0-9].html')]
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'data')
UNIT_OF = {'11': ('I', '과학의 기초'), '12': ('II', '물질과 규칙성'), '13': ('III', '시스템과 상호작용'),
           '21': ('I', '변화와 다양성'), '22': ('II', '환경과 에너지'), '23': ('III', '과학과 미래 사회')}
BOOK_OF = {'1': '통합과학 1', '2': '통합과학 2'}
MARKS = '①②③④⑤'

import sys as _sys; _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _extract_common import txt as _txt, defs_map, selfcontain, strip_tags, supsub_uni, plain_text


def txt(node, keep_bold=False):
    """조판 태그를 걷어 낸 문자열. keep_bold 면 <b>·첨자를 남기고 빈칸을 {{㉠}} 로(앱에서 강조·빈칸에 쓴다)."""
    return _txt(node, keep_bold, blanks=keep_bold)


def parse_keyline(line, count):
    """'정답 1 ③ (해설) 2 ② (… 3 × 10⁸ …) 3 서술형 모범 답안' 을 앞에서부터 차례로 읽는다.
    예전에는 ' 3 ' 을 아무 데서나 찾아 괄호 속 식(3 × 10⁸)에서 잘렸다(2026-10-01 점검: 해설 5개가 잘리거나 섞임)."""
    body = re.sub(r'^\s*정답\s*', '', line); out, pos = {}, 0
    for i in range(1, count + 1):
        m = re.compile(rf'\s*{i}\s+').match(body, pos)
        if not m: break
        pos = m.end(); mk = re.compile(r'([①②③④⑤])\s*').match(body, pos)
        if mk and body[mk.end():mk.end() + 1] == '(':            # ③ (해설) — 괄호 짝을 세어 끝을 찾는다
            depth, j = 0, mk.end()
            while j < len(body):
                if body[j] == '(': depth += 1
                elif body[j] == ')':
                    depth -= 1
                    if depth == 0: break
                j += 1
            out[i] = (mk.group(1), body[mk.end() + 1:j].strip()); pos = j + 1
        elif mk and ((i == count and not body[mk.end():].strip()) or (i < count and re.compile(rf'\s*{i + 1}\s').match(body, mk.end()))):
            out[i] = (mk.group(1), ''); pos = mk.end()
        else:                                                   # 서술형: 다음 번호(맨 끝이면 끝)까지
            if i == count: end = len(body)
            else:
                n = re.compile(rf'\s{i + 1}\s').search(body, pos); end = n.start() if n else len(body)
            m2 = mk.group(1) if mk else None
            out[i] = (m2, body[(mk.end() if mk else pos):end].strip()); pos = end
    return out


def parse_lesson(path):
    src_text = path.read_text(encoding='utf-8')
    markers = defs_map(src_text)
    # 페이지 원문을 순서대로 들고 있다가, 그림은 여기서 원문 그대로 꺼낸다
    raw_pages = [seg for seg in re.split(r'(?=<div class="page lect")', src_text)
                 if seg.lstrip().startswith('<div class="page lect"')]
    soup = BeautifulSoup(src_text, 'html.parser')
    code = path.stem[2:]                       # L-2203 → 2203
    unit, unit_name = UNIT_OF[code[:2]]
    book = code[0]
    band = txt(soup.select_one('.tagband span'))          # "II. 환경과 에너지 · 03 지구온난화와 기후변화"
    lesson_name = re.split(r'\s·\s', band, maxsplit=1)[-1].strip()   # 단원·소단원 사이는 ' · '(띄어 씀) — 이름 속 '에너지·물질'의 ·에서 자르지 않는다
    lesson_name = re.sub(r'^\d+\s*', '', lesson_name)

    concepts, cur = [], None
    for pi, page in enumerate(soup.select('.page.lect')):
        if page.select_one('.qs-head') or page.select_one('.memo-area'):
            if cur:
                concepts.append(cur)
                cur = None
            continue
        lesson_tag = page.select_one('.a-lesson')
        if lesson_tag:                                     # A면 — 개념이 시작된다
            if cur:
                concepts.append(cur)
            title_el = page.select_one('.a-title')
            soft = title_el.select_one('.soft')
            subtitle = txt(soft).lstrip('— ').strip() if soft else ''
            if soft:
                soft.extract()
            cur = {
                'id': f"{code}-{txt(lesson_tag).replace('개념 ', '')}",
                'book': book, 'bookName': BOOK_OF[book],
                'unit': unit, 'unitName': unit_name,
                'lessonId': code, 'lessonName': lesson_name,
                'no': txt(lesson_tag).replace('개념 ', ''),
                'title': txt(title_el).rstrip('— ').strip(),
                'subtitle': subtitle,
                'steps': [], 'howto': [], 'body': [],
                'terms': [], 'myths': [], 'point': '', 'answers': '',
                'blanks': {}, 'warning': '',
                'figure': None,
            }
            for st in page.select('.a-step'):
                cur['steps'].append({
                    'n': txt(st.select_one('.n')),
                    't': txt(st.select_one('.t'), keep_bold=True),   # 제목에도 빈칸(㉠)이 있다(2303-01)
                    'd': txt(st.select_one('.d'), keep_bold=True)})
            fig = page.select_one('.a-fig')
            if fig and fig.find('svg'):
                cap = fig.select_one('figcaption')
                raw_svg = ''
                if pi < len(raw_pages):
                    m = re.search(r'<svg\b.*?</svg>', raw_pages[pi], re.S)
                    if m:
                        raw_svg = m.group()          # 원문 — 대소문자가 살아 있다
                cur['figure'] = {
                    'caption': txt(cap).split('|')[-1].strip() if cap else '',
                    'file': f"figures/{cur['id']}.svg",
                    '_svg': selfcontain(raw_svg or str(fig.find('svg')), markers, cur['id'])}
            for li in page.select('.howto li'):
                n = li.select_one('b.n')          # 번호는 앱이 다시 붙인다
                if n:
                    n.extract()
                cur['howto'].append(txt(li, keep_bold=True))

        if cur is None:
            continue
        for para in page.select('.a-script p'):
            cur['body'].append(txt(para, keep_bold=True))
        for tr in page.select('table.terms tr'):
            cur['terms'].append({'k': txt(tr.find('th')), 'v': txt(tr.find('td'))})
        for m in page.select('.myth .m'):
            why = ''
            w = m.select_one('span.w')               # '왜?' 표지 — 그 뒤 글은 이유(반박 텍스트의 설명)
            if w:
                box = soup.new_tag('span')
                for sib in list(w.next_siblings):
                    box.append(sib.extract())
                why = txt(box, keep_bold=True)
                br = w.find_previous_sibling('br')   # 진실과 이유 사이 줄바꿈
                if br:
                    br.extract()
                w.extract()
            raw = txt(m, keep_bold=True)
            parts = re.split(r'✓\s*진실', raw)
            if len(parts) == 2:
                cur['myths'].append({
                    'x': re.sub(r'^✗\s*오해\s*', '', parts[0]).strip(),
                    'o': parts[1].strip(),
                    'why': why})
        pt = page.select_one('.point p')
        if pt:
            cur['point'] = txt(pt, keep_bold=True)
        ans = page.select_one('.ans-line')
        if ans:
            line = txt(ans)
            cur['answers'] = line
            body, _, warn = line.partition(' — ')
            cur['blanks'] = {m.group(1): m.group(2).strip()
                             for m in re.finditer(r'([㉠㉡㉢])\s*(.+?)(?=\s*[㉠㉡㉢]|$)',
                                                  body.replace('정답 ', '', 1))}
            cur['warning'] = warn.strip()
    if cur:
        concepts.append(cur)

    # ── 확인 문제 쪽 ──
    quizzes = []
    qpage = soup.select_one('.page.lect:has(.qs-head)')
    if qpage:
        note = qpage.select_one('.qs-note p')
        keyline = txt(qpage.select_one('.ans-line'))
        qqs = qpage.select('.qq')
        keys = parse_keyline(txt(qpage.select_one('.ans-line'), keep_bold=True), len(qqs))
        for i, qq in enumerate(qqs, 1):
            stems = qq.select('.stem')
            qn = qq.select_one('.qn')
            if qn:
                qn.extract()
            tag = qq.select_one('.tag')
            if tag:
                tag.extract()
            q = {'lessonId': code, 'no': i,
                 'type': txt(tag) if tag else '',
                 'stem': txt(stems[0], keep_bold=True),
                 'source': txt(qq.select_one('.bogi'), keep_bold=True) if qq.select_one('.bogi') else '',
                 'ask': txt(stems[1], keep_bold=True) if len(stems) > 1 else '',
                 'choices': [txt(li, keep_bold=True).lstrip('①②③④⑤ ') for li in qq.select('ol.ch li')],
                 'essay': bool(qq.select_one('.write')),
                 'gradeNote': txt(note, keep_bold=True) if i == 3 and note else '',
                 'answerLine': keyline}
            mk, ex = keys.get(i, (None, ''))
            if q['essay']: mk, ex = None, (('' if not mk else mk + ' ') + ex).strip()   # 서술형 모범 답안이 ①로 시작해도 정답 ①이 아니다(1201 #3)
            q['answer'] = MARKS.index(mk) + 1 if mk else None
            q['explain'] = ex
            quizzes.append(q)
    return concepts, quizzes


def main():
    (OUT / 'figures').mkdir(parents=True, exist_ok=True)
    all_c, all_q = [], []
    paths = [p for src, pat in SRCS for p in sorted(src.glob(pat))]
    for path in paths:
        cs, qs = parse_lesson(path)
        for c in cs:
            if c['figure']:
                (OUT / c['figure']['file']).write_text(c['figure'].pop('_svg'), encoding='utf-8')
        all_c += cs
        all_q += qs
        print(f"{path.stem}: 개념 {len(cs)} · 문항 {len(qs)}")

    (OUT / 'concepts.json').write_text(
        json.dumps(all_c, ensure_ascii=False, indent=1), encoding='utf-8')
    (OUT / 'quizzes.json').write_text(
        json.dumps(all_q, ensure_ascii=False, indent=1), encoding='utf-8')
    figs = len(list((OUT / 'figures').glob('*.svg')))
    print(f"\n합계: 개념 {len(all_c)} · 문항 {len(all_q)} · 그림 {figs} → {OUT}")

    missing = [c['id'] for c in all_c if not c['body'] or not c['point']]
    if missing:
        print('본문·포인트가 빈 개념:', missing)


if __name__ == '__main__':
    main()
