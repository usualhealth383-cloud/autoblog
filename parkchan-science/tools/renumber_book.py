#!/usr/bin/env python3
"""본책 쪽 번호 다시 매기기 — 쪽을 더하거나 빼면 그 뒤 모든 폴리오·차례·'N쪽' 참조가 어긋난다.

빌드 순서(book/build.sh · book2/build.sh 의 render 줄)대로 파일을 읽어, 폴리오(<span class="num">)를 1부터 차례로 다시 매기고
옛 번호 → 새 번호 표로 본문 속 'N쪽' 참조와 차례(tr-pg)를 함께 고친다.
새로 넣은 쪽은 폴리오를 <span class="num">?</span> 로 두면 된다(옛 번호가 없으니 참조 대상이 아니다).

사용: python3 tools/renumber_book.py book [--dry]      (book2 도 같음)
바뀐 참조는 모두 문맥과 함께 찍는다 — 눈으로 확인할 것.
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FOLIO = re.compile(r'(<div class="folio">.*?<span class="num">)([^<]*)(</span>)', re.S)
PAGEREF = re.compile(r'(?<![\d.])(\d{1,3})(\s?쪽)')
TOCPG = re.compile(r'(<span class="tr-pg">)(\d+)(</span>)')


def order(book):
    sh = (ROOT / book / 'build.sh').read_text(encoding='utf-8')
    return [ROOT / book / m for m in re.findall(r'^render\s+(\S+\.html)\s', sh, re.M)]


def main():
    book = sys.argv[1]; dry = '--dry' in sys.argv
    files = order(book); texts = {f: f.read_text(encoding='utf-8') for f in files}
    n = 0; old2new = {}; plan = {}
    for f in files:
        news = []
        # 쪽마다 하나씩 센다(표지처럼 폴리오가 없는 쪽도 한 쪽) — 폴리오는 그 쪽의 번호를 받는다
        for seg in re.split(r'(?=<div class="page[ "])', texts[f])[1:]:
            n += 1
            for m in FOLIO.finditer(seg):
                news.append(n); o = m.group(2).strip()
                if o.isdigit():
                    if int(o) in old2new: print(f'! 옛 번호 {o} 가 두 번 나온다 ({f.relative_to(ROOT)})'); sys.exit(1)
                    old2new[int(o)] = n
        if len(news) != len(FOLIO.findall(texts[f])): print(f'! {f.relative_to(ROOT)}: 쪽 밖에 폴리오가 있다'); sys.exit(1)
        plan[f] = news
    lo, hi = (min(old2new), max(old2new)) if old2new else (0, 0)
    changed = 0
    for f in files:
        s = texts[f]; it = iter(plan[f])
        s = FOLIO.sub(lambda m: m.group(1) + str(next(it)) + m.group(3), s)
        def ref(m, node=''):
            nonlocal changed
            o = int(m.group(1))
            if not (lo <= o <= hi) or o not in old2new or old2new[o] == o: return m.group(0)
            ctx = m.string[max(0, m.start() - 28):m.end() + 8].replace('\n', ' ')
            print(f'  {f.parent.name}: {o}쪽 → {old2new[o]}쪽   …{ctx}…'); changed += 1
            return str(old2new[o]) + m.group(2)
        # 태그 안(속성·주석)은 건드리지 않는다 — 글자 부분만
        s = re.sub(r'>([^<]+)<', lambda t: '>' + PAGEREF.sub(ref, t.group(1)) + '<', s)
        s = TOCPG.sub(lambda m: m.group(1) + str(old2new.get(int(m.group(2)), int(m.group(2)))) + m.group(3), s)
        if s != texts[f] and not dry: f.write_text(s, encoding='utf-8')
    print(f'{book}: 폴리오 {n}쪽 · 본문 참조 {changed}곳 고침' + (' (시험 실행)' if dry else ''))


if __name__ == '__main__':
    main()
