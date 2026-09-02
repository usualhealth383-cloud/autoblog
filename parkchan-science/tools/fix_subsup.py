#!/usr/bin/env python3
"""화학식 첨자·폰트 폴백 정리
1) 유니코드 첨자(₂₃₄ ⁺⁻)를 본문 폰트 그대로 쓰는 마크업으로 교체
   - HTML 문맥: <sub>/<sup>  (CSS는 add_css()가 넣는다)
   - SVG <text> 문맥: <tspan dy="…em" font-size="68%">…</tspan> + 복원 tspan
2) 'PC Pen' / 'PC Serif' 단독 지정에 한글·한자 폴백을 붙여 중국어·라틴 폰트로 떨어지지 않게 한다.
사용: python3 tools/fix_subsup.py <파일…>
"""
import re, sys, pathlib

SUB = {'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9'}
SUP = {'⁺':'+','⁻':'−','⁰':'0','¹':'1','²':'2','³':'3','⁴':'4'}
RUN = re.compile('([' + ''.join(SUB) + ']+)|([' + ''.join(SUP) + ']+)')
DY_SUB, DY_SUP, SZ = 0.14, -0.34, '68%'

CSS_RULE = """
  /* 화학식 첨자 — 본문 폰트를 그대로 축소해 자형이 어긋나지 않게 한다 */
  sub,sup{ font-size:0.68em; line-height:0; font-weight:inherit; }
  sub{ vertical-align:-0.14em; } sup{ vertical-align:0.34em; }
"""

def html_conv(t):
    def rep(m):
        if m.group(1): return '<sub>' + ''.join(SUB[c] for c in m.group(1)) + '</sub>'
        return '<sup>' + ''.join(SUP[c] for c in m.group(2)) + '</sup>'
    return RUN.sub(rep, t)

def svg_text_inner(inner):
    m = RUN.search(inner)
    if not m: return inner
    is_sub = bool(m.group(1))
    plain = ''.join((SUB if is_sub else SUP)[c] for c in m.group())
    dy = DY_SUB if is_sub else DY_SUP
    rest = svg_text_inner(inner[m.end():])
    piece = f'<tspan dy="{dy}em" font-size="{SZ}">{plain}</tspan>'
    if rest.strip():
        piece += f'<tspan dy="{-dy}em">{rest}</tspan>'
    else:
        piece += rest
    return inner[:m.start()] + piece

def svg_conv(seg):
    def rep(m):
        head, inner = m.group(1), m.group(2)
        return head + svg_text_inner(inner) + '</text>'
    return re.sub(r'(<text\b[^>]*>)(.*?)</text>', rep, seg, flags=re.S)

def fonts(s):
    # @font-face 안의 font-family 는 '이름 정의'이므로 폴백을 붙이면 폰트가 통째로 깨진다 — 잠시 봉인
    seals = []
    def seal(m):
        seals.append(m.group()); return f'\x00FF{len(seals)-1}\x00'
    s = re.sub(r'@font-face\s*\{[^}]*\}', seal, s)
    s = re.sub(r"font-family:\s*'PC Pen'(?!\s*,)", "font-family:'PC Pen','PC Sans',sans-serif", s)
    s = re.sub(r"font-family:\s*'PC Serif'(?!\s*,)", "font-family:'PC Serif','PC Sans',serif", s)
    s = re.sub(r'font-family="PC Pen"', 'font-family="PC Pen, PC Sans, sans-serif"', s)
    s = re.sub(r'font-family="PC Serif"', 'font-family="PC Serif, PC Sans, serif"', s)
    s = re.sub(r'\x00FF(\d+)\x00', lambda m: seals[int(m.group(1))], s)
    return s

def add_css(s):
    if 'sub,sup{' in s: return s
    i = s.find('</style>')
    return s if i < 0 else s[:i] + CSS_RULE + s[i:]

def convert(path):
    p = pathlib.Path(path); s0 = p.read_text(encoding='utf-8')
    out, pos = [], 0
    for m in re.finditer(r'<svg\b.*?</svg>', s0, re.S):
        out.append(html_conv(s0[pos:m.start()])); out.append(svg_conv(m.group())); pos = m.end()
    out.append(html_conv(s0[pos:]))
    s = fonts(add_css(''.join(out)))
    if s != s0:
        p.write_text(s, encoding='utf-8'); print('수정:', path)
    else:
        print('변화 없음:', path)

for a in sys.argv[1:]: convert(a)
