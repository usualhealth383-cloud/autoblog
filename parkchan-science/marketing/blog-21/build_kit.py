#!/usr/bin/env python3
"""blog-21 — 네 번째 글: 고등학교 과학 시험, 왜 그래프 문제가 많을까요. (blog-19 꼴)\n원래: 두 번째 블로그 글: 통합과학이 중학교 과학·지금까지의 수능 과학과 무엇이 다른가(2026-11-05).
첫 글 수정판(blog-18) 기준을 따른다 — 개강일·보충자료·동영상·공통과학·'확실히' 없음, 시작 시각만, 좁은 줄 간격.
사용: python3 build_kit.py  → kit.html · post.txt · ../../../docs/marketing/blog-21/*.jpg"""
import re, html, base64, hashlib, io, json, pathlib
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent
PUB = HERE.parents[2] / 'docs' / 'marketing' / 'blog-21'
URL = 'https://usualhealth383-cloud.github.io/autoblog/marketing/blog-21/'
BLUE = '#2F5FC4'
TITLES = ['월성동 과학학원 | 고등학교 과학 시험, 왜 그래프 문제가 많을까요 — 박찬 통합과학', '대구 과학학원 | 달걀 떨어뜨리기로 보는 고1 통합과학 그래프 문제 — 월성동 박찬 통합과학']
TAGS = (HERE.parent / 'blog-16' / 'tags.txt').read_text(encoding='utf-8').split()

POST = [
 ('c', '안녕하십니까.<br>대구 월성동 박찬 통합과학 학원입니다.'),
 ('c', '고등학교 과학 시험에는<br>그래프와 표가 많이 나옵니다.<br>2028학년도 수능 예시문항에도<br>자료를 해석하는 문제가 많이 담겼습니다.'),
 ('c', '==왜 그럴까요?==<br>예시 문제 하나로 함께 풀어 보겠습니다.'),
 ('img', 'c01_cover', '고등학교 과학 시험, 왜 그래프 문제가 많을까요 — 예시 문제 하나로 함께 풀어 봅니다'),
 ('q', '예시 문제, 달걀이 덜 깨지는 쪽은?'),
 ('c', '같은 달걀 두 개를 같은 높이에서 떨어뜨립니다.<br>하나는 딱딱한 바닥에, 하나는 푹신한 방석에 떨어집니다.<br>멈출 때 받는 힘을 시간에 따라 나타내면 이렇습니다.'),
 ('img', 'c02_graph', '예시 문제 — 딱딱한 바닥(A)과 푹신한 방석(B)에 떨어진 달걀이 받는 힘을 시간에 따라 나타낸 그래프, 두 모양의 넓이는 같음(가상의 자료)'),
 ('c', '정답은 **B, 푹신한 방석**입니다.<br>답은 쉽게 짐작할 수 있지만,<br>==왜 그런지를 그래프로 설명하는 것==이 고등학교 과학입니다.'),
 ('q', '이렇게 생각합니다'),
 ('img', 'c03_answer', '이렇게 생각합니다 — 넓이(충격량)가 같다, 시간이 다르다, 그래서 B가 덜 깨진다'),
 ('c', '그래프 아래의 넓이는 **충격량**입니다.<br>같은 달걀이 같은 높이에서 떨어져 멈추므로 넓이는 같고,<br>방석은 부딪히는 시간을 길게 늘려<br>가장 큰 힘을 작게 만듭니다.<br>자동차의 에어백도 같은 원리입니다.'),
 ('c', '이 문제 하나에<br>==그래프 읽기, 넓이의 뜻, 생활에 적용하기==가<br>모두 들어 있습니다.<br>그래서 수업마다 자료를 해석하는 연습을 함께 합니다.'),
 ('q', '고1 예비반 수강생 모집 중'),
 ('tbl', [('화금반', '화, 금 **오후 5시 30분**'),
          ('수토반', '수 **오후 5시 30분**, 토 **오후 3시 30분**'),
          ('수업', '주 2회'),
          ('대상', '고1 예비 (현 중3)'),
          ('교재', '완자 통합과학<br>EBS 개념완성 943제 문항편')], None),
 ('img', 'c04_class', '고1 예비반 수강생 모집 중 · 화금반 화·금 오후 5시 30분 · 수토반 수 오후 5시 30분, 토 오후 3시 30분 · 일주일 무료 수강 · 상담 053-213-3577'),
 ('c', '먼저 **일주일 들어 보시고**<br>등록을 결정하셔도 됩니다.'),
 ('c', '상담 문의 **053-213-3577**<br>상담 시간 매일 오후 2시 ~ 오후 10시<br>대구 달서구 조암로 25 그루빌딩 501호 (월성 CGV 옆)'),
 ('c', '감사합니다.'),
 ('fine', '남교입 제2019-115호 · 교습비(월) / 총 교습시간<br>중등부 21만 원 / 1,042분 · 26만 7,000원 / 1,303분<br>고등부 22만 원 / 912분 · 31만 7,000원 / 1,303분'),
]

BANNED = ['개강', '내일', '시작되었', '동영상', '보충자료', '2시간', '7시 30분', '공통과학', '네 단계', '3월 입학 전', '확실히', '11월 3일', '11월 4일', '2027년 2월', '선행', '진도', '미리', '1등급', '완성']
def inline(s, mode):   # mode: rich | prev | txt
    if mode == 'txt':
        return re.sub(r'\*\*|==', '', s).replace('<br>', '\n')
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    return re.sub(r'==(.+?)==', (rf'<b style="color:{BLUE}">\1</b>' if mode == 'rich' else r'<b class="em">\1</b>'), s)

imgs, n = {}, 0
PUB.mkdir(parents=True, exist_ok=True)
for b in POST:
    if b[0] == 'img':
        im = Image.open(HERE / 'images' / f'{b[1]}.png').convert('RGB'); buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88, optimize=True)
        data = buf.getvalue(); (PUB / f'{b[1]}.jpg').write_bytes(data)
        imgs[b[1]] = (f'{URL}{b[1]}.jpg?v={hashlib.sha1(data).hexdigest()[:8]}', 'data:image/jpeg;base64,' + base64.b64encode(data).decode())
(PUB / 'manifest.json').write_text(json.dumps({k + '.png': v[0].split('/')[-1] for k, v in imgs.items()}, ensure_ascii=False, indent=1), encoding='utf-8')

C = 'margin:0;line-height:1.9;'
TD = 'border:1px solid #D9CFBD;padding:8px 10px;vertical-align:top;'
def rich(data_uri):
    out, k = [], 0
    for b in POST:
        t = b[0]
        if t in ('c', 'p'): out.append(f'<p style="{C}{"text-align:center;" if t == "c" else ""}">{inline(b[1], "rich")}</p>\n<p><br></p>')
        elif t == 'q': out.append(f'<p><br></p><p style="margin:0;text-align:center;font-size:19px;font-weight:700;line-height:1.6;color:#24406F;border-top:1px solid #3B6AD0;border-bottom:1px solid #3B6AD0;padding:14px 0">{b[1]}</p>')   # 줄 간격은 앞에 빈 줄 하나만(2026-11-04 현욱님 「항상 공간이 넓다」)
        elif t == 'img':
            src = imgs[b[1]][1 if data_uri else 0]
            out.append(f'<p style="margin:0;text-align:center"><img src="{src}" alt="{html.escape(b[2])}" width="1080" style="width:100%;max-width:100%;height:auto"></p>')
        elif t == 'tbl':
            rows = ''.join(f'<tr><td style="{TD}background:{"#FFF2C2" if i == b[2] else "#FFFFFF"};font-weight:700;{"color:"+BLUE+";" if i == b[2] else ""}">{l}</td><td style="{TD}background:{"#FFF2C2" if i == b[2] else "#FFFFFF"};{"font-weight:700;" if i == b[2] else ""}">{inline(v, "rich")}</td></tr>' for i, (l, v) in enumerate(b[1]))
            out.append(f'<table style="border-collapse:collapse;width:100%;margin:0 0 18px;font-size:15px;line-height:1.6">{rows}</table>\n<p><br></p>')
        elif t == 'fine': out.append(f'<p style="margin:0;font-size:13px;line-height:1.6;color:#9A9A9A;text-align:center">{b[1]}</p>')
    return '\n'.join(out)

def txt():
    out, k = [], 0
    for b in POST:
        t = b[0]
        if t in ('c', 'p'): out.append(inline(b[1], 'txt'))
        elif t == 'q': out.append(f'【소제목 · 인용구】 {b[1]}')
        elif t == 'img': k += 1; out.append(f'【사진 {k} · {b[1]}.png】')
        elif t == 'tbl': out.append('\n'.join(f'{l.replace("<br>", " · ")}: {inline(v, "txt").replace(chr(10), " · ")}' for l, v in b[1]))
        elif t == 'fine': out.append('\n'.join('【작은 글씨】' + x for x in b[1].split('<br>')))
    return '\n\n'.join(out)

def prev():
    out, k = [], 0
    for b in POST:
        t = b[0]
        if t in ('c', 'p'): cl = ' class="c"' if t == 'c' else ''; out.append(f'<p{cl}>{inline(b[1], "prev")}</p>')
        elif t == 'q': out.append(f'<blockquote>{b[1]}</blockquote>')
        elif t == 'img': k += 1; out.append(f'<figure><img src="images/{b[1]}.png" alt="{html.escape(b[2])}"><figcaption>사진 {k} · {b[1]}.png</figcaption></figure>')
        elif t == 'tbl': out.append('<div class="tw"><table>' + ''.join(('<tr class="now">' if i == b[2] else '<tr>') + f'<td>{l}</td><td>{inline(v, "prev")}</td></tr>' for i, (l, v) in enumerate(b[1])) + '</table></div>')
        elif t == 'fine': out.append(f'<p class="fine">{b[1]}</p>')
    return '\n'.join(out)

body = txt()
hits = [w for w in BANNED if w in (body + ''.join(TITLES)).replace('개념완성', '')]   # 책 이름 'EBS 개념완성'은 허용
assert not hits, f'쓰지 않기로 한 말: {hits}'
old = (HERE.parent / 'blog-16' / 'kit.html').read_text(encoding='utf-8')
head = old[:old.index('<div class="wrap">')].replace('<title>박찬 통합과학 블로그 글</title>', '<title>박찬 통합과학 네 번째 글</title>')
script = old[old.index('<script>'):]
nimg = sum(1 for b in POST if b[0] == 'img')
titles = ''.join(f'<div class="row"><span class="k">{"AB"[i]}</span><span class="t">{html.escape(t)}</span><button class="cp" data-text="{html.escape(t)}">복사</button></div>' for i, t in enumerate(TITLES))
tags = ''.join(f'<button class="cp tg" data-text="{t}">{t}</button>' for t in TAGS)
head = head.replace('</style>', '.tags button.tg{font-size:14px;min-height:40px;padding:0 12px;background:var(--soft);color:var(--navy);font-weight:700}.tags button.tg.done{opacity:.4}\n</style>', 1)
page = f'''{head}<div class="wrap">
<section class="box"><h1>박찬 통합과학 · 네 번째 글</h1><p class="sub">고등학교 과학 시험, 왜 그래프 문제가 많을까요 · 합니다체 · 사진 {nimg}장</p></section>
<section class="box"><h2>① 제목 — 하나 고르기</h2>{titles}</section>
<section class="box"><h2>② 본문 — 통째로 복사</h2><button class="cp big" id="richBtn">본문 통째로 복사 — 사진 · 표 · 굵게 · 색 포함</button>
<p class="note">네이버가 일부 서식을 빼면 '글자만 복사'(사진 자리 표시가 들어 있음)를 쓰십시오.</p>
<details style="margin-top:10px"><summary style="font-size:14px;color:var(--muted);cursor:pointer">글자만 복사 (서식 없음)</summary><textarea id="bodyTxt" readonly style="margin-top:8px">{html.escape(body)}</textarea><button class="cp big" data-copy="bodyTxt">글자만 복사</button></details>
<button class="cp big" id="richBtn2" style="background:var(--soft);color:var(--ink);border:1px solid var(--line)">사진이 안 들어가면 — 사진을 글 안에 담아 복사</button></section>
<section class="box"><h2>③ 태그 — 하나씩 눌러 붙여 넣기</h2><p class="note" style="margin:0 0 10px">네이버 태그 칸은 여러 개를 한 번에 붙이면 하나로 뭉칩니다. 아래 태그를 하나 누르면 복사됩니다 → 태그 칸에 붙여 넣고 <b>Enter</b> → 다음 태그를 누르기. 누른 태그는 흐리게 바뀝니다.</p><div class="tags">{tags}</div>
<details style="margin-top:12px"><summary style="font-size:14px;color:var(--muted);cursor:pointer">쉼표로 한 번에 붙여 보기 (네이버가 나눠 줄 수도 있음)</summary><button class="cp big" data-copy="tagTxt">쉼표로 구분해 복사</button><textarea id="tagTxt" readonly style="display:none">{", ".join(TAGS)}</textarea></details></section>
<section class="box"><h2>④ 네이버에서 고치는 법</h2><ol class="how">
<li><b>새 글</b>을 열고 제목 칸에 ①, 본문 칸에 ②를 붙여 넣기</li>
<li>붙인 뒤 <b>사진 1</b>을 눌러 <b>대표</b>로 지정</li>
<li>사진이 빠져 있으면 아래 미리보기 사진을 길게 눌러(PC는 오른쪽 클릭) 저장한 뒤 그 자리에 올리기</li>
</ol></section>
<section class="box"><h2>미리보기</h2><article class="post">{prev()}</article></section>
</div>
<template id="rich">{rich(False)}</template><template id="rich2">{rich(True)}</template>
{script}<script>document.addEventListener('click',e=>{{const b=e.target.closest('button.tg');if(b)setTimeout(()=>b.classList.add('done'),50)}});</script>'''
(HERE / 'kit.html').write_text(page, encoding='utf-8')
(HERE / 'post.txt').write_text(body + '\n', encoding='utf-8')
(HERE / 'titles.txt').write_text('\n'.join(TITLES) + '\n', encoding='utf-8')
(HERE / 'tags.txt').write_text('\n'.join(TAGS) + '\n', encoding='utf-8')
print('kit.html', len(page), 'B · 사진', nimg)
