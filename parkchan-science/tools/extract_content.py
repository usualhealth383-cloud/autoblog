#!/usr/bin/env python3
"""강의용 교재(L-XXXX.html)에서 개념·문항을 뽑아 앱이 쓸 데이터로 만든다.

교재는 조판된 HTML이라 그대로는 배달할 수 없다. 개념 하나를 한 덩어리로 떼어 내고,
그림은 SVG 파일로 따로 저장해 앱에서 그대로 띄운다(다시 그리지 않는다).

사용: python3 tools/extract_content.py [출력폴더]     기본값 data/
산출물: data/concepts.json · data/quizzes.json · data/figures/<개념id>.svg
"""
import json, re, sys, pathlib
from bs4 import BeautifulSoup

SRC = pathlib.Path(__file__).resolve().parent.parent / 'book2' / 'lecture-edition'
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                   pathlib.Path(__file__).resolve().parent.parent / 'data')
UNIT_OF = {'21': ('I', '변화와 다양성'), '22': ('II', '환경과 에너지'),
           '23': ('III', '과학과 미래 사회')}
MARKS = '①②③④⑤'


def txt(node, keep_bold=False):
    """조판 태그를 걷어 낸 문자열. keep_bold 면 <b> 만 남긴다(앱에서 강조에 쓴다)."""
    if node is None:
        return ''
    if keep_bold:
        html = ''.join(str(c) for c in node.contents)
        html = re.sub(r'<span class="blank">(.*?)</span>', r'{{\1}}', html)
        html = re.sub(r'<b\b[^>]*>', '<b>', html)
        html = re.sub(r'<(?!/?b>)[^>]+>', '', html)
        return re.sub(r'\s+', ' ', html).strip()
    return re.sub(r'\s+', ' ', node.get_text(' ')).strip()


def parse_lesson(path):
    src_text = path.read_text(encoding='utf-8')
    # 페이지 원문을 순서대로 들고 있다가, 그림은 여기서 원문 그대로 꺼낸다
    raw_pages = [seg for seg in re.split(r'(?=<div class="page lect")', src_text)
                 if seg.lstrip().startswith('<div class="page lect"')]
    soup = BeautifulSoup(src_text, 'html.parser')
    code = path.stem[2:]                       # L-2203 → 2203
    unit, unit_name = UNIT_OF[code[:2]]
    band = txt(soup.select_one('.tagband span'))          # "II. 환경과 에너지 · 03 지구온난화와 기후변화"
    lesson_name = band.split('·')[-1].strip()
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
                    't': txt(st.select_one('.t')),
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
                    '_svg': raw_svg or str(fig.find('svg'))}
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
            raw = txt(m, keep_bold=True)
            parts = re.split(r'✓\s*진실', raw)
            if len(parts) == 2:
                cur['myths'].append({
                    'x': re.sub(r'^✗\s*오해\s*', '', parts[0]).strip(),
                    'o': parts[1].strip()})
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
        for i, qq in enumerate(qpage.select('.qq'), 1):
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
            m = re.search(rf'\b{i} ([①②③④⑤])', keyline)
            q['answer'] = MARKS.index(m.group(1)) + 1 if m else None
            body = keyline.replace('정답 ', '', 1)
            seg = re.search(rf'(?:^|\s){i} (.+?)(?=\s{i+1} |$)', body)
            q['explain'] = re.sub(r'^[①②③④⑤]\s*', '', seg.group(1)).strip(' ()') if seg else ''
            quizzes.append(q)
    return concepts, quizzes


def main():
    (OUT / 'figures').mkdir(parents=True, exist_ok=True)
    all_c, all_q = [], []
    for path in sorted(SRC.glob('L-2[0-9][0-9][0-9].html')):
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
