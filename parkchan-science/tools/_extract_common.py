"""교재 추출 공통 — extract_content.py · extract_bank.py 가 같이 쓴다.

2026-10-01 점검에서 나온 것
· 글자 속 '<보기>'·'10⁻¹⁵ < 10⁻¹⁰' 같은 부등호가 태그로 오인돼 지워졌다 → 원문을 이스케이프된 채로 받아 태그만 걷고 마지막에 풀기
· 그림이 파일 상단(defs-only)·다른 그림의 <defs> 에 있는 기호(<g id="sy-owl">)·그라데이션을 참조하는데 마커만 옮겨 그림이 비었다
  → 파일 안의 모든 <defs> 에서 id 가 붙은 정의를 모아, 그림이 쓰는 것을 (그 정의가 다시 쓰는 것까지) 넣는다
"""
import html as _html, re

SUP_U = str.maketrans('0123456789+-−n', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻ⁿ'); SUB_U = str.maketrans('0123456789+-', '₀₁₂₃₄₅₆₇₈₉₊₋')
UNI_SS = '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ₀₁₂₃₄₅₆₇₈₉₊₋'
TAG = r'</?[a-zA-Z][^>]*>'          # 진짜 태그만(글자 '<보기>'·'< 10' 은 태그가 아니다)


def supsub_uni(h):
    """글자만 남길 칸(제목·용어·캡션)용: 첨자를 유니코드 첨자로"""
    h = re.sub(r'<sup\b[^>]*>(.*?)</sup>', lambda m: re.sub(TAG, '', m[1]).translate(SUP_U), h, flags=re.S)
    return re.sub(r'<sub\b[^>]*>(.*?)</sub>', lambda m: re.sub(TAG, '', m[1]).translate(SUB_U), h, flags=re.S)


def strip_tags(t):
    """<b>·<sup>·<sub> 만 남기고 태그를 걷는다(앱이 그대로 그린다)"""
    t = re.sub(r'<(sup|sub)\b[^>]*>', r'<\1>', t)
    return re.sub(r'<(?!/?(?:b|sup|sub)>)/?[a-zA-Z][^>]*>', '', t)


def plain_text(node, sep=' '):
    from bs4 import BeautifulSoup   # 추출할 때만 필요(점검 check_content.py 는 bs4 없이 돈다 — CI)
    return BeautifulSoup(supsub_uni(str(node)), 'html.parser').get_text(sep)


def txt(node, keep_bold=False, blanks=False):
    """조판 태그를 걷어 낸 문자열. keep_bold 면 <b>·<sup>·<sub> 를 남긴다. blanks 면 빈칸 <span class="blank">㉠</span> → {{㉠}}"""
    if node is None: return ''
    if keep_bold:
        h = node.decode_contents()                                  # 글자 속 < > & 는 &lt; &gt; &amp; 로 온다
        if blanks: h = re.sub(r'<span class="blank">(.*?)</span>', r'{{\1}}', h)
        h = re.sub(r'<b\b[^>]*>', '<b>', h)
        h = strip_tags(h)
        return re.sub(r'\s+', ' ', _html.unescape(h)).strip()
    t = re.sub(r'\s+', ' ', plain_text(node, ' '))
    return re.sub(r'\s+([' + UNI_SS + r']+)', r'\1', t).strip()


def defs_map(src):
    """파일 안 모든 <defs> 의 id 붙은 정의(마커·기호·그라데이션·패턴·클립) — id → 원문(대소문자 그대로)"""
    out = {}
    for d in re.finditer(r'<defs>(.*?)</defs>', src, re.S):
        body = d.group(1)
        for m in re.finditer(r'<(marker|g|symbol|linearGradient|radialGradient|pattern|clipPath|mask|path|filter)\b[^>]*\bid="([^"]+)"', body):
            tag, i = m.group(1), m.group(2)
            if i in out: continue
            end = _close(body, m.start(), tag)
            if end: out[i] = body[m.start():end]
    return out


def _close(s, start, tag):
    """start 에서 열린 <tag …> 의 짝이 되는 닫는 태그 끝 위치(자기 닫힘 포함). 같은 이름이 안에 겹쳐 있어도 센다"""
    head = re.compile(r'<' + tag + r'\b[^>]*?(/?)>'); m = head.match(s, start)
    if not m: return None
    if m.group(1) == '/': return m.end()
    depth, pos = 1, m.end(); pat = re.compile(r'<(/?)' + tag + r'\b[^>]*?(/?)>')
    while depth:
        n = pat.search(s, pos)
        if not n: return None
        if n.group(1): depth -= 1
        elif not n.group(2): depth += 1
        pos = n.end()
    return pos


def refs(svg):
    return set(re.findall(r'url\(#([^)]+)\)', svg)) | set(re.findall(r'href="#([^"]+)"', svg))


def selfcontain(svg, defs, cid):
    """그림 하나를 독립 문서로: 쓰는 정의를(정의가 다시 쓰는 것까지) <defs> 로 넣고, 모든 id 에 번호를 붙여
    앱 한 문서 안에서 다른 그림과 id 가 부딪히지 않게 한다."""
    have = set(re.findall(r'\bid="([^"]+)"', svg))
    need, seen, todo = [], set(), sorted(refs(svg) - have)
    while todo:
        i = todo.pop(0)
        if i in seen or i in have or i not in defs: continue
        seen.add(i); need.append(defs[i])
        todo += sorted(refs(defs[i]) - have - seen)
    if need:
        svg = re.sub(r'(<svg\b[^>]*>)', lambda m: m.group(1) + '<defs>' + ''.join(need) + '</defs>', svg, count=1)
    for i in sorted(set(re.findall(r'\bid="([^"]+)"', svg)), key=len, reverse=True):
        svg = svg.replace(f'id="{i}"', f'id="{i}-{cid}"').replace(f'url(#{i})', f'url(#{i}-{cid})').replace(f'href="#{i}"', f'href="#{i}-{cid}"')
    return svg


def dangling(svg):
    """그림 안에서 정의 없이 참조만 하는 id — 0 이어야 한다"""
    return sorted(refs(svg) - set(re.findall(r'\bid="([^"]+)"', svg)))
