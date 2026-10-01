#!/usr/bin/env python3
"""부록 '정답 한눈에 보기' 생성기 — 각 소단원 chapter.html 의 알짜 해설 정답표(table.anstable)를 읽어
back-matter/back.html 의 정답표를 다시 쓴다.

사용: python3 tools/make_answer_index.py book|book2 [--check]
  · 읽는 것: 소단원마다 table.anstable 의 모든 짝(문항 줄·정답 줄 — 1~12 / 13~24)과
             그 파일의 첫 쪽번호(<span class="num">N</span>) = 소단원 시작 쪽
  · 쓰는 것: back.html 의 <!-- ANSWER-INDEX:START --> ~ <!-- ANSWER-INDEX:END --> 사이
             (표지가 없으면 첫 실행으로 보고 옛 '정답 한눈에 보기' 머리·표 자리에 표지를 넣는다)
  · 대조: 만든 정답이 tools/extract_bank.py 의 parse_chapter 가 읽는 정답과 하나라도 다르면 멈춘다(assert)
  · --check: 파일을 고치지 않고, 지금 back.html 의 표가 생성 결과와 같은지만 본다(다르면 exit 1)
서술형(정답표의 '서술형')은 '서술'로 적는다.
"""
import html, pathlib, re, sys
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from extract_bank import parse_chapter, lesson_code, MARKS   # noqa: E402

START, END = '<!-- ANSWER-INDEX:START -->', '<!-- ANSWER-INDEX:END -->'
N_ITEMS, PER_ROW = 24, 12

# 단원 묶음 · 짧은 소단원 이름 (빌드 순서 = build.sh 의 render 순서)
BOOKS = {
    'book': [
        ('I. 과학의 기초', [
            ('chapter-i01', '01 시간과 공간'), ('chapter-i02', '02 기본량과 단위'),
            ('chapter-i03', '03 측정과 어림·표준'), ('chapter-i04', '04 정보와 디지털')]),
        ('II. 물질과 규칙성', [
            ('sample-chapter', '01 우주의 시작'), ('chapter-02', '02 별과 원소'),
            ('chapter-03', '03 주기성과 결합'), ('chapter-04', '04 지각·생명 물질'),
            ('chapter-05', '05 전기적 성질')]),
        ('III. 시스템과 상호작용', [
            ('chapter-06', '01 지구시스템'), ('chapter-07', '02 판구조론'),
            ('chapter-08', '03 중력과 운동'), ('chapter-09', '04 운동량·충격량'),
            ('chapter-10', '05 생명과 화학 반응'), ('chapter-11', '06 유전자와 단백질')]),
    ],
    'book2': [
        ('I. 변화와 다양성', [
            ('chapter-2101', '01 지질시대와 변천'), ('chapter-2102', '02 진화와 다양성'),
            ('chapter-2103', '03 산화와 환원'), ('chapter-2104', '04 산·염기와 중화'),
            ('chapter-2105', '05 에너지 출입')]),
        ('II. 환경과 에너지', [
            ('chapter-2201', '01 생태계의 구성'), ('chapter-2202', '02 생태계 평형'),
            ('chapter-2203', '03 온난화와 기후변화'), ('chapter-2204', '04 태양 에너지'),
            ('chapter-2205', '05 발전과 효율')]),
        ('III. 과학과 미래 사회', [
            ('chapter-2301', '01 감염병과 과학'), ('chapter-2302', '02 빅데이터와 AI'),
            ('chapter-2303', '03 과학기술과 윤리')]),
    ],
}

# 열 너비(mm) — 이름 | 범위 | 1~12열. 위 줄(1~12) 4~6번이 빈칸 단답이라 넓게, 아래 줄(13~24)은 기호·'서술'뿐
COLS = [38, 9.5] + [7.6] * 3 + [17.6] * 3 + [9.55] * 6


def cell_text(td):
    return re.sub(r'\s+', ' ', td.get_text(' ')).strip()


def read_chapter(path):
    """(정답 dict{번호: 문자열}, 시작 쪽) — anstable 의 문항·정답 줄 짝을 모두 읽는다"""
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    tbl = None
    for t in soup.select('table.anstable'):
        th = t.select_one('tr th')
        if th and cell_text(th).startswith('문항'): tbl = t; break
    assert tbl is not None, f'{path}: table.anstable(문항/정답) 없음'
    rows = tbl.select('tr')
    assert len(rows) % 2 == 0, f'{path}: 정답표 줄 수가 홀수({len(rows)})'
    ans = {}
    for i in range(0, len(rows), 2):
        h0, h1 = cell_text(rows[i].select_one('th')), cell_text(rows[i + 1].select_one('th'))
        assert h0.startswith('문항') and h1.startswith('정답'), f'{path}: {i // 2 + 1}번째 짝 머리글 {h0!r}/{h1!r}'
        nums = [cell_text(td) for td in rows[i].select('td')]
        vals = [cell_text(td) for td in rows[i + 1].select('td')]
        assert len(nums) == len(vals), f'{path}: 문항 {nums} / 정답 {vals} 칸 수 다름'
        for n, v in zip(nums, vals):
            assert n.isdigit() and int(n) not in ans and v, f'{path}: 문항 {n!r} 정답 {v!r}'
            ans[int(n)] = v
    assert sorted(ans) == list(range(1, N_ITEMS + 1)), f'{path}: 문항 번호 {sorted(ans)}'
    num = soup.select_one('span.num')
    assert num and cell_text(num).isdigit(), f'{path}: 첫 쪽번호 없음'
    return ans, int(cell_text(num))


def cross_check(path, ans):
    """parse_chapter(앱 문제 은행 추출기)가 읽는 정답과 하나하나 같아야 한다"""
    items, _ = parse_chapter(path)
    code = lesson_code(path)
    got = {int(it['id'].rsplit('-q', 1)[1]): it for it in items if re.fullmatch(rf'{code}-q\d+', it['id'])}
    assert sorted(got) == sorted(ans), f'{path}: parse_chapter 문항 {sorted(got)} ≠ 정답표 {sorted(ans)}'
    for n, v in ans.items():
        it = got[n]
        if it['type'] == 'essay':
            ok = v.startswith('서술')
        elif it['type'] in ('mc', 'multi'):
            ok = isinstance(it['answer'], int) and MARKS[it['answer'] - 1] == v
        else:                                              # ox · blank — 문자열 그대로
            ok = it['answer'] == v
        assert ok, f'{path} {n}번: 정답표 {v!r} ≠ parse_chapter {it["type"]}:{it["answer"]!r}'
    for n in (18, 19, 20):
        assert got[n]['type'] == 'essay', f'{path} {n}번이 서술형이 아니다({got[n]["type"]})'


def show(v):
    v = '서술' if v.startswith('서술') else v
    e = html.escape(v, quote=False)
    return f'<span class="w">{e}</span>' if len(v.replace(' ', '')) >= 5 else e


def build(book):
    bdir = ROOT / book
    units, n_lessons = [], 0
    for ui, (uname, lessons) in enumerate(BOOKS[book], 1):
        rows = []
        for li, (d, short) in enumerate(lessons):
            path = bdir / d / 'chapter.html'
            ans, page = read_chapter(path)
            cross_check(path, ans)
            rows.append((short, page, ans, li % 2 == 1))
            n_lessons += 1
        units.append((ui, uname, rows))

    colgroup = '<colgroup>' + ''.join(f'<col style="width:{w}mm;">' for w in COLS) + '</colgroup>'
    ncol = len(COLS)
    out = [START,
           f'  <div class="sol-head" style="margin-bottom:2.5mm;"><span class="stt">정답 한눈에 보기</span><span class="sub">전 {n_lessons}개 소단원 · 문항 1~{N_ITEMS} — 채점은 빠르게, 복습은 해설로!</span></div>',
           '']
    for ui, uname, rows in units:
        out.append(f'  <table class="ax ax-{ui} ax24">{colgroup}')
        # 단원 띠 = 위 줄 번호(1~12), 회색 머리 줄 = 아래 줄 번호(13~24)
        out.append(f'    <tr class="uhead"><th colspan="2">{uname}</th>'
                   + ''.join(f'<th class="n">{n}</th>' for n in range(1, PER_ROW + 1)) + '</tr>')
        out.append('    <tr class="axh"><th>소단원</th><th class="rg">번호</th>'
                   + ''.join(f'<th>{n}</th>' for n in range(PER_ROW + 1, N_ITEMS + 1)) + '</tr>')
        for short, page, ans, zebra in rows:
            z = ' z' if zebra else ''
            for half in (0, 1):
                lo = half * PER_ROW + 1
                cells = ''.join(f'<td class="a">{show(ans[n])}</td>' for n in range(lo, lo + PER_ROW))
                head = (f'<th class="lname" rowspan="2">{html.escape(short, quote=False)} <span class="pg">{page}쪽</span></th>'
                        if half == 0 else '')
                rg = f'<th class="rg">{lo}~{lo + PER_ROW - 1}</th>'
                out.append(f'    <tr class="{"p1" if half == 0 else "p2"}{z}">{head}{rg}{cells}</tr>')
        out.append('  </table>')
        out.append('')
    out.append('  ' + END)
    return '\n'.join(out), n_lessons


OLD = re.compile(r'[ \t]*<div class="sol-head"[^>]*><span class="stt">정답 한눈에 보기</span>.*?</table>(?:\s*<table class="ax.*?</table>)*', re.S)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 1 or args[0] not in BOOKS:
        sys.exit('사용: python3 tools/make_answer_index.py book|book2 [--check]')
    book = args[0]
    back = ROOT / book / 'back-matter' / 'back.html'
    src = back.read_text(encoding='utf-8')
    block, n = build(book)
    if START in src:
        i, j = src.index(START), src.index(END) + len(END)
        # 표지 앞의 들여쓰기는 그대로 둔다
        new = src[:i] + block + src[j:]
    else:                                                  # 첫 실행 — 옛 머리·표 자리에 표지째 넣는다
        m = OLD.search(src)
        assert m, f'{back}: 옛 정답표(정답 한눈에 보기)를 찾지 못함'
        new = src[:m.start()] + '  ' + block + src[m.end():]
    if '--check' in sys.argv:
        same = new == src
        print(f'{back.relative_to(ROOT)}: 정답표 {"최신" if same else "다름 — 다시 생성 필요"}')
        sys.exit(0 if same else 1)
    if new != src:
        back.write_text(new, encoding='utf-8')
    print(f'OK: {back.relative_to(ROOT)} — 소단원 {n}개 × {N_ITEMS}문항 (parse_chapter 대조 통과){"" if new != src else " · 바뀐 것 없음"}')


if __name__ == '__main__':
    main()
