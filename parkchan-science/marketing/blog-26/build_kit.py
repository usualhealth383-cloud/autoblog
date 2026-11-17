#!/usr/bin/env python3
"""blog-26 — 원장님 글 다듬은 판(중등부 특강반 안내, 2026-11-16).\n원래 꼴: 강의 시간표 안내 글(2026-11-12 원장님 메모). 시간이 바뀌면 이 글만 고친다.\n원래 꼴: 두 번째 블로그 글: 통합과학이 중학교 과학·지금까지의 수능 과학과 무엇이 다른가(2026-11-05).
첫 글 수정판(blog-18) 기준을 따른다 — 개강일·보충자료·동영상·공통과학·'확실히' 없음, 시작 시각만, 좁은 줄 간격.
사용: python3 build_kit.py  → kit.html · post.txt · ../../../docs/marketing/blog-26/*.jpg"""
import re, html, base64, hashlib, io, json, pathlib
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent
PUB = HERE.parents[2] / 'docs' / 'marketing' / 'blog-26'
URL = 'https://usualhealth383-cloud.github.io/autoblog/marketing/blog-26/'
BLUE = '#2F5FC4'
TITLES = ['중등부 특강반 안내 · 겨울방학 목 · 토']
TAGS = ['월성동과학학원', '대구과학학원', '달서구과학학원', '월성동학원', '중등부과학', '중등과학', '중학생과학', '겨울방학특강', '과학학원', '월배과학학원', '진천동과학학원', '상인동과학학원', '박찬통합과학학원']

POST = [('img', 'cover_middle_c', '중등부 특강반 안내'),
 ('c', '중등부 학부모님, 안녕하십니까.<br>박찬 통합과학 학원 원장입니다.'),
 ('c', '학생이 과학을 어려워하나요?<br>혹시 지루해하지는 않나요?'),
 ('c', '과학은 ==기본 개념과 원리부터 차근차근== 공부하면<br>이해가 잘 되고, 이해가 되면 재미가 생깁니다.<br>재미가 붙으면 실력도 자연스럽게 따라옵니다.'),
 ('c', '그렇게 공부할 수 있도록 제가 직접 가르치겠습니다.<br>소중한 겨울방학, 알차게 지도하겠습니다.'),
 ('q', '강의 시간 (겨울방학 개강)'),
 ('tbl', [('목요반', '오후 2시 ~ 5시'), ('토요반', '오후 1시 ~ 4시')], None),
 ('q', '강의 특징'),
 ('p', '==①== 기본 개념과 원리 중심 강의<br>==②== 이해 중심 강의<br>==③== EBS 강의와 같은 강의실 시스템으로 효과적인 수업'),
 ('c', '상담 문의 **053-213-3577**<br>매일 오후 2시 ~ 오후 10시'),
 ('c', '감사합니다.')]

BANNED = ['무료', '선행', '1등급', '대구 최초', '반드시', '확실히', '꼭 좋은', '중등부 통합과학', '고등학교', '고1', '수능', '일요반']
def inline(s, mode):   # mode: rich | prev | txt
    if mode == 'txt':
        return re.sub(r'\*\*|==', '', s).replace('<br>', '\n')
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    return re.sub(r'==(.+?)==', (r'<b>\1</b>' if mode == 'rich' else r'<b class="em">\1</b>'), s)

imgs, n = {}, 0
PUB.mkdir(parents=True, exist_ok=True)
for b in POST:
    if b[0] == 'img':
        im = Image.open(HERE / 'images' / f'{b[1]}.png').convert('RGB'); buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88, optimize=True)
        data = buf.getvalue(); (PUB / f'{b[1]}.jpg').write_bytes(data)
        imgs[b[1]] = (f'{URL}{b[1]}.jpg?v={hashlib.sha1(data).hexdigest()[:8]}', 'data:image/jpeg;base64,' + base64.b64encode(data).decode())
(PUB / 'manifest.json').write_text(json.dumps({k + '.png': v[0].split('/')[-1] for k, v in imgs.items()}, ensure_ascii=False, indent=1), encoding='utf-8')

HI_IMG={'cover_middle_c': 'hires/05_중등부_표지.png'}
for _k,_p in HI_IMG.items():
    _im=Image.open(HERE.parent/_p).convert('RGB');_b=io.BytesIO();_im.save(_b,'JPEG',quality=92)
    imgs[_k]=(imgs[_k][0],'data:image/jpeg;base64,'+base64.b64encode(_b.getvalue()).decode())
C = 'margin:0;line-height:1.9;color:#333333;'
TD = 'border:1px solid #D9CFBD;padding:8px 10px;vertical-align:top;color:#333333;text-align:justify;'
HASH = ' '.join('#' + t for t in TAGS)
def rich(data_uri):
    out, k = [], 0
    for b in POST:
        t = b[0]
        if t in ('c', 'p'): out.append(f'<p style="{C}{"text-align:center;" if t == "c" else "text-align:justify;"}">{inline(b[1], "rich")}</p>\n<p><br></p>')
        elif t == 'q': out.append(f'<p><br></p><p style="margin:0;text-align:center;font-size:19px;font-weight:700;line-height:1.6;color:#24406F;border-top:1px solid #3B6AD0;border-bottom:1px solid #3B6AD0;padding:14px 0">{b[1]}</p>')   # 줄 간격은 앞에 빈 줄 하나만(2026-11-04 현욱님 「항상 공간이 넓다」)
        elif t == 'img':
            src = imgs[b[1]][1 if data_uri else 0]
            out.append(f'<p style="margin:0;text-align:center"><img src="{src}" alt="{html.escape(b[2])}" width="1080" style="width:100%;max-width:100%;height:auto"></p>')
        elif t == 'tbl':
            rows = ''.join(f'<tr><td style="{TD}background:{"#FFF2C2" if i == b[2] else "#FFFFFF"};font-weight:700;{"color:"+BLUE+";" if i == b[2] else ""}">{l}</td><td style="{TD}background:{"#FFF2C2" if i == b[2] else "#FFFFFF"};{"font-weight:700;" if i == b[2] else ""}">{inline(v, "rich")}</td></tr>' for i, (l, v) in enumerate(b[1]))
            out.append(f'<table style="border-collapse:collapse;width:100%;margin:0 0 18px;font-size:15px;line-height:1.6">{rows}</table>\n<p><br></p>')
        elif t == 'fine': out.append(f'<p style="margin:0;font-size:13px;line-height:1.6;color:#9A9A9A;text-align:center">{b[1]}</p>')
    out.append(f'<p style="margin:22px 0 0;line-height:1.9;color:#333333;text-align:justify;">{HASH}</p>')
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
    out.append(HASH)
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
head = old[:old.index('<div class="wrap">')].replace('<title>박찬 통합과학 블로그 글</title>', '<title>박찬 통합과학 중등부 특강반 안내</title>')
script = old[old.index('<script>'):]
nimg = sum(1 for b in POST if b[0] == 'img')
titles = ''.join(f'<div class="row"><span class="k">{"AB"[i]}</span><span class="t">{html.escape(t)}</span><button class="cp" data-text="{html.escape(t)}">복사</button></div>' for i, t in enumerate(TITLES))
tags = ''.join(f'<button class="cp tg" data-text="{t}">{t}</button>' for t in TAGS)
head = head.replace('</style>', '.tags button.tg{font-size:14px;min-height:40px;padding:0 12px;background:var(--soft);color:var(--navy);font-weight:700}.tags button.tg.done{opacity:.4}\n</style>', 1)
page = f'''{head}<div class="wrap">
<section class="box"><h1>박찬 통합과학 · 중등부 특강반 안내</h1><p class="sub">원장님 글 다듬은 판 · 중등부 특강반 수강 안내 · 사진 {nimg}장</p></section>
<section class="box" style="border-color:#E0A800"><h2>⚠ 올리기 전 확인</h2><ol class="how"><li>강의 시간은 강의 시간표(11월 12일 기준)에 맞췄습니다</li></ol></section>
<section class="box"><h2>① 제목</h2>{titles}</section>
<section class="box"><h2>② 본문 — 통째로 복사</h2><button class="cp big" id="richBtn">본문 통째로 복사 — 사진 · 표 · 굵게 · 색 포함</button>
<p class="note">네이버가 일부 서식을 빼면 '글자만 복사'(사진 자리 표시가 들어 있음)를 쓰십시오.</p>
<details style="margin-top:10px"><summary style="font-size:14px;color:var(--muted);cursor:pointer">글자만 복사 (서식 없음)</summary><textarea id="bodyTxt" readonly style="margin-top:8px">{html.escape(body)}</textarea><button class="cp big" data-copy="bodyTxt">글자만 복사</button></details>
<button class="cp big" id="richBtn2" style="background:var(--soft);color:var(--ink);border:1px solid var(--line)">사진이 안 들어가면 — 사진을 글 안에 담아 복사</button></section>
<section class="box"><h2>③ 태그 — 따로 할 일 없음</h2><p class="note" style="margin:0 0 10px">②로 본문을 붙여 넣으면 맨 끝 파란 줄(#태그)이 같이 들어가고, 네이버가 그 줄을 태그로 등록합니다. 붙인 뒤 맨 아래 태그 칸에 태그가 들어왔는지만 보십시오. 안 들어왔으면 아래 태그를 하나씩 눌러 넣으십시오.</p><div class="tags">{tags}</div></section>
<section class="box"><h2>④ 네이버에서 고치는 법</h2><ol class="how">
<li><b>새 글</b>을 열고 제목 칸에 ①, 본문 칸에 ②를 붙여 넣기</li>
<li>붙인 뒤 <b>사진 1</b>을 눌러 <b>대표</b>로 지정</li>
<li>사진이 빠져 있으면 아래 미리보기 사진을 길게 눌러(PC는 오른쪽 클릭) 저장한 뒤 그 자리에 올리기</li>
</ol></section>
<section class="box"><h2>미리보기</h2><article class="post">{prev()}</article></section>
</div>
<template id="rich">{rich(True)}</template><template id="rich2">{rich(True)}</template>
{script}<script>document.addEventListener('click',e=>{{const b=e.target.closest('button.tg');if(b)setTimeout(()=>b.classList.add('done'),50)}});</script>'''
(HERE / 'kit.html').write_text(page, encoding='utf-8')
(HERE / 'post.txt').write_text(body + '\n', encoding='utf-8')
(HERE / 'titles.txt').write_text('\n'.join(TITLES) + '\n', encoding='utf-8')
(HERE / 'tags.txt').write_text('\n'.join(TAGS) + '\n', encoding='utf-8')
print('kit.html', len(page), 'B · 사진', nimg)
