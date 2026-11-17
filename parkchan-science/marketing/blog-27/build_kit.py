#!/usr/bin/env python3
"""blog-27 — 고1 예비반 합친 글(첫 글 10-12 + 고1 예비반 11-16, 2026-11-17 현욱님 「원래 글 내용까지 잘 반영해 새 글」). 사진은 링크로 붙이지 않고 파일로 올린다.\n옛 설명: 원장님 글 다듬은 판(고1 예비반 수강 안내, 2026-11-16).\n원래 꼴: 강의 시간표 안내 글(2026-11-12 원장님 메모). 시간이 바뀌면 이 글만 고친다.\n원래 꼴: 두 번째 블로그 글: 통합과학이 중학교 과학·지금까지의 수능 과학과 무엇이 다른가(2026-11-05).
첫 글 수정판(blog-18) 기준을 따른다 — 개강일·보충자료·동영상·공통과학·'확실히' 없음, 시작 시각만, 좁은 줄 간격.
사용: python3 build_kit.py  → kit.html · post.txt · ../../../docs/marketing/blog-27/*.jpg"""
import re, html, base64, hashlib, io, json, pathlib
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent
PUB = HERE.parents[2] / 'docs' / 'marketing' / 'blog-27'
URL = 'https://usualhealth383-cloud.github.io/autoblog/marketing/blog-27/'
BLUE = '#2F5FC4'
TITLES = ['고1 예비반 안내 (현 중3) · 일요반 11월 22일 개강']
TAGS = (HERE.parent / 'blog-16' / 'tags.txt').read_text(encoding='utf-8').split()

POST = [('img', 'cover_go1_b', '고1 예비반(현 중3) 수강 안내'),
 ('p', '안녕하십니까.<br>대구 월성동 박찬 통합과학 학원 원장입니다.<br>고1 예비(현 중3) 학부모님께 통합과학 안내 말씀을 드립니다.'),
 ('q', '통합과학, 왜 중요할까요'),
 ('p', '고등학교 1학년에서 통합과학은 **국어, 영어, 수학과 같은 학점**으로 배우는 과목입니다.<br>그리고 고1로 끝나지 않고 ==고3 수능까지 함께하는 중요한 과목==입니다.'),
 ('img', '04_change', '고등학교 과학, 이렇게 바뀝니다 — 고1 모두 통합과학, 고교 내신 5등급제, 수능도 통합과학'),
 ('p', '· **교육과정** — 2022 개정에 따라 고1 학생은 모두 통합과학을 배웁니다.<br>· **내신** — 2025년 고1부터 5등급제로 바뀌었습니다.<br>· **수능** — 2028학년도부터 과학탐구는 통합과학 한 과목입니다. 지금 중3 학생들이 치를 수능도 현재 발표 기준으로 같은 체제입니다.'),
 ('p', '그래서 ==고1 첫 내신이 고등학교 3년의 출발점==입니다.<br>물론 고등학교에 올라가 열심히 하면 됩니다. 다만 시간 여유가 있는 지금, 통합과학 전체를 천천히 그리고 체계적으로 공부해 두면 고1 내신도, 고3 수능 준비도 훨씬 수월해집니다.'),
 ('p', '고등학교 통합과학은 중학교 과학과 겹치는 부분이 많습니다. 그래서 중학교 때 과학을 잘한 학생이 조금 더 쉽게 공부할 수 있는 것은 사실입니다.<br>거꾸로 말하면, ==중학교 때 과학이 부족했던 학생도 지금부터 제대로 공부하면 충분히 잘할 수 있다==는 뜻입니다.'),
 ('q', '원장이 직접 맡을 수 있는 반만'),
 ('p', '저희 학원은 여러 반, 많은 학생을 두는 학원이 아닙니다.<br>원장인 제가 직접 맡을 수 있는 반만 열어, **처음부터 끝까지 제가 직접 가르치고 상담합니다.**<br>학생 한 명 한 명의 공부를 꼼꼼히 점검하고, 수강생 모두가 통합과학에 자신감을 갖도록 끝까지 곁에서 함께하겠습니다.'),
 ('q', '이렇게 강의합니다'),
 ('p', '==①== **개념과 원리 중심, 이해 중심 강의**<br>처음 만나는 통합과학을 원리부터 이해하며 차근차근 따라올 수 있도록 가르칩니다.<br><br>==②== **사고력과 응용력을 기르는 문제 풀이**<br>자료를 해석하고, 처음 보는 상황에 개념을 적용하는 문제를 함께 풉니다.<br><br>==③== **EBS 강의와 같은 강의실 시스템**으로 학습 효과를 높입니다.<br><br>==④== **한 명 한 명 꼼꼼하게 챙기는 학생 관리**'),
 ('q', '강의 시간'),
 ('tbl', [('일요반 (새로 시작하는 반)', '**11월 22일(일) 개강** · 오후 1시 ~ 4시 · 처음부터'),
 ('기존 반 (화, 수, 금)', '오후 5시 30분 · 물질과 규칙성부터 이어서 (11월 12일(목) 기준)'),
 ('수요반 (겨울방학)', '오후 2시 ~ 5시 · 처음부터 · 개강일은 따로 안내해 드리겠습니다')], 0),
 ('q', '상담 안내'),
 ('c', '어느 반이 맞을지,<br>지금 학생에게 무엇이 필요한지<br>편하게 상담해 드리겠습니다.'),
 ('img', '07_visit_b', '박찬 통합과학 학원 오시는 길과 상담 전화'),
 ('c', '**오시는 길**<br>대구 달서구 조암로 25 그루타워 501호 (월성 CGV 옆)<br><br>**상담 문의 053-213-3577**<br>매일 오후 2시 ~ 오후 10시'),
 ('c', '처음 만나는 통합과학,<br>학생이 자신 있게 시작할 수 있도록<br>정성껏 가르치겠습니다.<br><br>감사합니다.')]

BANNED = ['11월 21일', '토요반 (새로', '토요반이 새로', '무료', '선행', '1등급', '대구 최초', '반드시', '확실히', '꼭 좋은', '보충', '진도', '미리', '교재', '일주일']
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

HI_IMG={'cover_go1_b': 'hires/07_고1예비반_사진1_표지.png', '04_change': 'hires/07_고1예비반_사진2_고등학교과학.png', '07_visit_b': 'hires/07_고1예비반_사진3_오시는길.png'}
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
            k += 1
            if data_uri:
                out.append(f'<p style="margin:0;text-align:center"><img src="{imgs[b[1]][1]}" alt="{html.escape(b[2])}" width="1080" style="width:100%;max-width:100%;height:auto"></p>')
            else:
                out.append(f'<p style="margin:0;text-align:center;background:#FFF2C2;color:#8A5A00;font-weight:700;padding:14px 0">【사진 {k} 자리 — 여기에 사진 {k} 파일을 올려 주세요】</p>')
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
        elif t == 'img': k += 1; out.append(f'<figure><img src="{imgs[b[1]][1]}" alt="{html.escape(b[2])}"><figcaption>사진 {k} · {b[1]}.png</figcaption></figure>')
        elif t == 'tbl': out.append('<div class="tw"><table>' + ''.join(('<tr class="now">' if i == b[2] else '<tr>') + f'<td>{l}</td><td>{inline(v, "prev")}</td></tr>' for i, (l, v) in enumerate(b[1])) + '</table></div>')
        elif t == 'fine': out.append(f'<p class="fine">{b[1]}</p>')
    return '\n'.join(out)

body = txt()
hits = [w for w in BANNED if w in (body + ''.join(TITLES)).replace('개념완성', '')]   # 책 이름 'EBS 개념완성'은 허용
assert not hits, f'쓰지 않기로 한 말: {hits}'
old = (HERE.parent / 'blog-16' / 'kit.html').read_text(encoding='utf-8')
head = old[:old.index('<div class="wrap">')].replace('<title>박찬 통합과학 블로그 글</title>', '<title>박찬 고1 예비반 합친 글</title>')
script = old[old.index('<script>'):]
nimg = sum(1 for b in POST if b[0] == 'img')
titles = ''.join(f'<div class="row"><span class="k">{"AB"[i]}</span><span class="t">{html.escape(t)}</span><button class="cp" data-text="{html.escape(t)}">복사</button></div>' for i, t in enumerate(TITLES))
tags = ''.join(f'<button class="cp tg" data-text="{t}">{t}</button>' for t in TAGS)
head = head.replace('</style>', '.tags button.tg{font-size:14px;min-height:40px;padding:0 12px;background:var(--soft);color:var(--navy);font-weight:700}.tags button.tg.done{opacity:.4}\n</style>', 1)
page = f'''{head}<div class="wrap">
<section class="box"><h1>고1 예비반 — 두 글을 하나로</h1><p class="sub">첫 글(10월 12일)과 고1 예비반 글(11월 16일)을 합친 판 · 사진 {nimg}장 · 좋아요 받은 첫 글의 내용(고등학교 과학 변화 · 문제 풀이 · 오시는 길 · 교습비)을 모두 옮겼습니다</p></section>
<section class="box" style="border-color:#E0A800"><h2>⚠ 바뀐 점</h2><ol class="how"><li>첫 글에서 옮긴 것: 고등학교 과학이 바뀌는 세 가지(그림 포함) · 문제 풀이 강의 · 처음부터 끝까지 직접 가르치고 상담 · 상담 안내 · 오시는 길(그림 포함) · 맺음말 · 교습비</li><li>뺀 것: 첫 글의 '특별 보충 수업'(원장님이 아직 정하지 않은 내용)</li><li>새 반은 블로그에 올라간 강의 시간표 글대로 <b>일요반 11월 22일(일)</b></li></ol></section>
<section class="box"><h2>① 제목</h2>{titles}</section>
<section class="box"><h2>② 본문 — 통째로 복사</h2><button class="cp big" id="richBtn">본문 통째로 복사 — 사진 · 표 · 굵게 · 색 포함</button>
<p class="note">네이버가 일부 서식을 빼면 '글자만 복사'(사진 자리 표시가 들어 있음)를 쓰십시오.</p>
<details style="margin-top:10px"><summary style="font-size:14px;color:var(--muted);cursor:pointer">글자만 복사 (서식 없음)</summary><textarea id="bodyTxt" readonly style="margin-top:8px">{html.escape(body)}</textarea><button class="cp big" data-copy="bodyTxt">글자만 복사</button></details>
</section>
<section class="box"><h2>③ 태그 — 따로 할 일 없음</h2><p class="note" style="margin:0 0 10px">②로 본문을 붙여 넣으면 맨 끝 파란 줄(#태그)이 같이 들어가고, 네이버가 그 줄을 태그로 등록합니다. 붙인 뒤 맨 아래 태그 칸에 태그가 들어왔는지만 보십시오. 안 들어왔으면 아래 태그를 하나씩 눌러 넣으십시오.</p><div class="tags">{tags}</div></section>
<section class="box"><h2>④ 네이버에서 하는 법 — 지금 고1 예비반 글을 고쳐 씁니다</h2><ol class="how">
<li>블로그의 <b>'처음 만나는 통합과학, 차근차근 함께 — 고1 예비반'</b> 글 → <b>수정</b> (새 글을 따로 쓰면 같은 글이 두 개가 됩니다)</li>
<li>본문을 전부 선택(Ctrl+A)해 지우고 ②를 붙여 넣기</li>
<li>노란 <b>【사진 N 자리】</b>를 하나씩 지우고, 그 자리에서 위쪽 <b>사진</b> 버튼으로 보내 드린 파일을 올리기 — 1 표지 · 2 고등학교 과학 변화 · 3 오시는 길</li>
<li>사진 1을 <b>대표</b>로 지정 → 카테고리 <b>반별 안내 › 고1 예비반</b> → 발행</li>
<li>맨 아래 교습비 세 줄은 작은 회색 글씨로 들어갑니다</li>
</ol><p class="note">사진을 링크로 붙이면 네이버가 사진으로 받지 않아 첫 화면 그림 카드에 안 뜹니다. 꼭 파일로 올려 주세요.</p></section>
<section class="box"><h2>미리보기</h2><article class="post">{prev()}</article></section>
</div>
<button id="richBtn2" hidden></button><template id="rich">{rich(True)}</template><template id="rich2">{rich(True)}</template>
{script}<script>document.addEventListener('click',e=>{{const b=e.target.closest('button.tg');if(b)setTimeout(()=>b.classList.add('done'),50)}});</script>'''
(HERE / 'kit.html').write_text(page, encoding='utf-8')
(HERE / 'post.txt').write_text(body + '\n', encoding='utf-8')
(HERE / 'titles.txt').write_text('\n'.join(TITLES) + '\n', encoding='utf-8')
(HERE / 'tags.txt').write_text('\n'.join(TAGS) + '\n', encoding='utf-8')
print('kit.html', len(page), 'B · 사진', nimg)
