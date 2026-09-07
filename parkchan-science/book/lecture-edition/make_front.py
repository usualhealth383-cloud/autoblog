#!/usr/bin/env python3
"""통합과학1 강의용 — 쪽 번호 재계산 + 앞부속(L-front.html) 생성.

각 L-파일의 <body style="--pg-start:N"> 을 순서대로 다시 매기고,
차례는 파일 안의 tagband·a-title 을 읽어 만든다(아직 없는 소단원은 제목만 넣는다).
사용: python3 make_front.py     → L-front.html 갱신 + 모든 L-*.html 의 pg-start 갱신
"""
import re, pathlib, html
HERE = pathlib.Path(__file__).resolve().parent
UNITS = [('I', '과학의 기초', ['1101','1102','1103','1104'], 'sum1',
          "--lb:#C1521E; --lb-dark:#B4560E; --lb-mid:#D98A5B; --lb-soft:#EBC4AB; --lb-light:#FBEFE7; --lb-pale:#FBF3ED; --lb-line:#F6DFCE;"),
         ('II', '물질과 규칙성', ['1201','1202','1203','1204','1205'], 'sum2', ''),
         ('III', '시스템과 상호작용', ['1301','1302','1303','1304','1305','1306'], 'sum3',
          "--lb:#4053B8; --lb-dark:#2E3E96; --lb-mid:#7280D4; --lb-soft:#C0C9EE; --lb-light:#ECEFFA; --lb-pale:#F2F4FC; --lb-line:#D9DFF5;")]
LESSON_NAMES = {'1101':'자연을 재는 눈 — 시간과 공간','1102':'기본량과 단위','1103':'측정과 어림, 측정 표준','1104':'정보와 신호, 디지털 문명',
  '1201':'우주의 시작과 원소의 탄생','1202':'별에서 만들어지는 원소','1203':'원소의 주기성과 화학 결합','1204':'지각과 생명체를 이루는 물질의 규칙성','1205':'물질의 전기적 성질과 신소재',
  '1301':'지구시스템과 에너지·물질 순환','1302':'판구조론과 지권의 변화','1303':'중력과 운동','1304':'운동량과 충격량','1305':'생명 시스템과 화학 반응','1306':'유전자에서 단백질까지'}

def pages(p): return len(re.findall(r'class="page lect', p.read_text(encoding='utf-8')))
def set_start(p, n):
    s = p.read_text(encoding='utf-8'); s2 = re.sub(r'--pg-start:\d+;', f'--pg-start:{n};', s, count=1)
    if s2 != s: p.write_text(s2, encoding='utf-8')
def titles(p):
    s = p.read_text(encoding='utf-8')
    out = []
    for m in re.finditer(r'<div class="a-title">(.*?)</div>', s, re.S):
        t = re.sub(r'<span class="soft">(.*?)</span>', r'\1', m.group(1))
        out.append(re.sub(r'\s+', ' ', t).strip())
    return out

# ── 쪽 번호: 앞부속 5쪽(1~5) 뒤부터 ──
pg = 5; info = {}
for unit, uname, codes, sumc, _ in UNITS:
    for c in codes:
        f = HERE / f'L-{c}.html'
        if f.exists():
            set_start(f, pg); info[c] = (pg + 1, titles(f)); pg += pages(f)
        else:
            info[c] = (None, [])
    f = HERE / f'L-{sumc}.html'
    if f.exists():
        set_start(f, pg); info[sumc] = pg + 1; pg += pages(f)
    else:
        info[sumc] = None

# ── 앞부속 ──
H = []
H.append('''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>박찬 과학 통합과학 1 — 앞부속</title>
<link rel="stylesheet" href="lecture.css">
</head>
<body data-unit="I" style="--pg-start:0;">

<div class="page lect" style="padding:14mm 19mm 18mm;">
  <div class="cover">
    <div class="kicker">고등학교 통합과학</div>
    <div class="rule"></div>
    <div class="t">박찬 과학<br><span class="n">통합과학 1</span></div>
    <div class="s">개념 하나에 두 쪽<br>수업의 흐름을 그대로 옮긴 교재</div>
    <div class="foot">과학의 기초 · 물질과 규칙성 · 시스템과 상호작용</div>
  </div>
  <div class="folio"><span></span><span></span></div>
</div>

<div class="page lect">
  <div class="tagband"><span>이 책의 구성</span><span>통합과학 1</span></div>
  <div class="guide-h">
    <div class="en">HOW TO USE</div>
    <div class="t">이 책의 구성</div>
    <div class="s">한 개념을 <b>두 쪽</b>에 나누어 담았다. 왼쪽 면에서 뼈대와 그림을 잡고, 오른쪽 면에서 내용을 넓힌 뒤
      스스로 정리한다. 소단원이 끝나면 배운 것을 문제로 확인하고, 단원이 끝나면 전체를 한 쪽에 모아 본다.</div>
  </div>

  <div class="gcards">
    <div class="gcard"><div class="n">1</div><div class="b">
      <div class="t">왼쪽 면 — 뼈대와 그림</div>
      <div class="d">개념의 흐름을 <b>세 걸음</b>으로 먼저 잡는다. 이어지는 큰 그림에는 <b>그림 읽는 법</b>이 붙어 있어,
        고유명사나 그래프를 처음 보는 학생도 무엇을 보아야 하는지 알 수 있다.</div></div></div>
    <div class="gcard"><div class="n">2</div><div class="b">
      <div class="t">오른쪽 면 — 넓히고 정리하기</div>
      <div class="d">본문을 이어 읽고 <b>용어 정리</b>와 <b>오해 ✗ / 진실 ✓</b>로 헷갈리는 지점을 바로잡은 뒤,
        <b>포인트</b>에서 그 개념의 한 줄을 확인한다.</div></div></div>
    <div class="gcard"><div class="n">3</div><div class="b">
      <div class="t">빈칸 ㉠ ㉡ ㉢ 과 정답</div>
      <div class="d">개념마다 빈칸이 <b>세 개</b> 있다. 수업 중에 채우고, 오른쪽 면 <b>맨 아래에 거꾸로 인쇄된 정답</b>으로
        바로 확인한다. 책을 돌리지 않으면 눈에 들어오지 않으므로 미리 보게 되지 않는다.</div></div></div>
    <div class="gcard"><div class="n">4</div><div class="b">
      <div class="t">배운 것 확인하기</div>
      <div class="d">소단원 끝에 <b>세 문항</b>이 있다. 자주 틀리는 오개념 하나, 자료를 읽는 문항 하나,
        문장으로 쓰는 서술형 하나다. <b>채점 포인트</b>에 무엇이 들어가야 정답인지 적어 두었다.</div></div></div>
    <div class="gcard"><div class="n">5</div><div class="b">
      <div class="t">메모 쪽</div>
      <div class="d">확인 문제 뒤에 <b>필기 한 쪽</b>이 있다. 선생님이 칠판에 덧붙인 말, 스스로 떠오른 질문,
        헷갈렸던 지점과 다시 볼 쪽수를 그 소단원 바로 옆에 적어 둔다.</div></div></div>
    <div class="gcard"><div class="n">6</div><div class="b">
      <div class="t">단원 한눈에 정리</div>
      <div class="d">단원이 끝나면 소단원들을 한 쪽에 모으고, 단원 전체를 관통하는 흐름을 한 줄로 잇는다.
        시험 전에 이 쪽부터 펴면 된다.</div></div></div>
  </div>

  <div class="folio"><span>박찬 과학 | 통합과학 1</span><span class="num"></span></div>
</div>
''')
first = True
for unit, uname, codes, sumc, pal in UNITS:
    style = f' style="{pal}"' if pal else ''
    H.append(f'<div class="page lect"{style}>\n  <div class="tagband"><span>차례</span><span>통합과학 1</span></div>\n')
    if first:
        H.append('  <div class="toc-h">\n    <div class="en">CONTENTS</div>\n    <div class="t">차례</div>\n  </div>\n'); first = False
    H.append(f'  <div class="toc-unit"><span class="no">{unit}</span><span class="nm">{uname}</span><span class="line"></span></div>\n')
    for i, c in enumerate(codes, 1):
        p, ts = info[c]
        H.append(f'  <div class="toc-l">\n    <div class="lh"><span class="lno">{i:02d}</span><span class="lt">{LESSON_NAMES[c]}</span><span class="dots"></span><span class="lpg">{p if p else ""}</span></div>\n')
        if ts:
            H.append('    <ul>\n' + ''.join(f'      <li><span class="cn">{k:02d}</span><span class="ct">{t}</span></li>\n' for k, t in enumerate(ts, 1)) + '    </ul>\n')
        H.append('  </div>\n')
    sp = info[sumc]
    H.append(f'  <div class="toc-l" style="margin-bottom:0;">\n    <div class="lh"><span class="lno">마무리</span><span class="lt">{unit}단원 한눈에 정리</span><span class="dots"></span><span class="lpg">{sp if sp else ""}</span></div>\n  </div>\n')
    H.append('\n  <div class="folio"><span>박찬 과학 | 통합과학 1</span><span class="num"></span></div>\n</div>\n\n')
H.append('</body>\n</html>\n')
(HERE / 'L-front.html').write_text(''.join(H), encoding='utf-8')
print('L-front.html 생성 · 마지막 쪽', pg)
for k, v in info.items(): print(' ', k, v if not isinstance(v, tuple) else (v[0], len(v[1])))
