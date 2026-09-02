#!/usr/bin/env python3
"""강의용 그림을 본책으로 이식.
사용: python3 tools/port_figure.py <강의용파일> <그림번호> <본책파일> <본책그림번호> [width]
  - 강의용 SVG를 통째로 가져오되, 참조하는 defs(marker/gradient/symbol/clipPath)를 SVG 안에 인라인
  - 모든 id에 접두사를 붙여 본책 기존 id와 충돌 방지
  - width는 기본 468px(124mm), 높이는 viewBox 비율로 자동
"""
import sys, re, pathlib

def find_svg(text, caption_key):
    """캡션 키워드로 figure의 svg 범위를 찾는다"""
    i = text.index(caption_key)
    a = text.rindex('<svg', 0, i)
    b = text.index('</svg>', a) + 6
    return a, b, text[a:b]

def collect_defs(src_text, svg):
    """svg가 참조하는 url(#id)/href="#id" 정의를 원본 파일 전체에서 수집"""
    ids = set(re.findall(r'url\(#([A-Za-z0-9_\-]+)\)', svg)) | set(re.findall(r'href="#([A-Za-z0-9_\-]+)"', svg))
    have = set(re.findall(r'<(?:marker|linearGradient|radialGradient|symbol|clipPath|pattern|g|path|filter)[^>]*\bid="([A-Za-z0-9_\-]+)"', svg))
    need = ids - have
    blocks, resolved = [], set()
    frontier = set(need)
    while frontier:
        nid = frontier.pop()
        if nid in resolved: continue
        m = re.search(r'<(marker|linearGradient|radialGradient|symbol|clipPath|pattern|g|path|filter)\b[^>]*\bid="%s"' % re.escape(nid), src_text)
        if not m:
            print(f'  [경고] 정의를 못 찾음: #{nid}', file=sys.stderr); resolved.add(nid); continue
        tag, start = m.group(1), m.start()
        # 자기 닫힘 태그인지 확인
        head_end = src_text.index('>', start)
        if src_text[head_end-1] == '/':
            block = src_text[start:head_end+1]
        else:
            depth, j = 1, head_end+1
            while depth > 0:
                nxt_o = src_text.find('<'+tag, j); nxt_c = src_text.find('</'+tag, j)
                if nxt_c == -1: break
                if nxt_o != -1 and nxt_o < nxt_c: depth += 1; j = nxt_o + 1
                else: depth -= 1; j = nxt_c + 1
            block = src_text[start:src_text.index('>', j)+1]
        blocks.append(block); resolved.add(nid)
        for x in set(re.findall(r'url\(#([A-Za-z0-9_\-]+)\)', block)) | set(re.findall(r'href="#([A-Za-z0-9_\-]+)"', block)):
            if x not in resolved: frontier.add(x)
    return blocks

def main():
    lec_f, lec_key, bk_f, bk_key = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    width = int(sys.argv[5]) if len(sys.argv) > 5 else 468
    pref = 'p' + re.sub(r'\D', '', pathlib.Path(bk_f).parent.name)[-4:] + re.sub(r'\D','',lec_key)[:2] + '_'
    lec = pathlib.Path(lec_f).read_text(); bk = pathlib.Path(bk_f).read_text()
    _, _, svg = find_svg(lec, lec_key)
    defs = collect_defs(lec, svg)
    if defs:
        inject = '<defs>' + ''.join(defs) + '</defs>'
        m = re.search(r'<defs>', svg)
        svg = (svg[:m.end()] + inject.replace('<defs>','',1).replace('</defs>','',1) + svg[m.end():]) if m \
              else re.sub(r'(<svg[^>]*>)', r'\1' + inject, svg, count=1)
    # id 접두사
    all_ids = set(re.findall(r'\bid="([A-Za-z0-9_\-]+)"', svg))
    for i in sorted(all_ids, key=len, reverse=True):
        svg = svg.replace(f'id="{i}"', f'id="{pref}{i}"').replace(f'url(#{i})', f'url(#{pref}{i})').replace(f'href="#{i}"', f'href="#{pref}{i}"')
    # 크기 조정
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    vw, vh = float(vb.group(1)), float(vb.group(2))
    h = round(width * vh / vw)
    svg = re.sub(r'<svg width="[\d.]+" height="[\d.]+"', f'<svg width="{width}" height="{h}"', svg, count=1)
    a, b, old = find_svg(bk, bk_key)
    pathlib.Path(bk_f).write_text(bk[:a] + svg + bk[b:])
    print(f'이식 완료: {lec_f}[{lec_key}] → {bk_f}[{bk_key}]  {width}x{h}px, defs {len(defs)}개')

main()
