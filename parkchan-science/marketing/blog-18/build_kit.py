#!/usr/bin/env python3
"""blog-18 — 첫 블로그 글(blog-16) 수정판 묶음. 개강일·'3월 입학 전 1·2를 확실히'·월별 진도 그림을 빼고
수업 시간·교재(완자 통합과학, EBS 개념완성 943제 문항편)·새 인사말을 넣었다(2026-11-04 원장님).
사용: python3 build_kit.py  → kit.html · post.txt · ../../../docs/marketing/blog-18/*.jpg"""
import re, html, base64, hashlib, io, json, pathlib
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent
PUB = HERE.parents[2] / 'docs' / 'marketing' / 'blog-18'
URL = 'https://usualhealth383-cloud.github.io/autoblog/marketing/blog-18/'
BLUE = '#2F5FC4'
TITLES = ['월성동 과학학원 | 현 중3 고1 예비반, 처음 만나는 통합과학을 차근차근 — 박찬 통합과학',
          '대구 과학학원 | 고1 예비반 수강생 모집 중, 개념부터 차근차근 — 월성동 박찬 통합과학']
TAGS = (HERE.parent / 'blog-16' / 'tags.txt').read_text(encoding='utf-8').split()

POST = [
 ('c', '안녕하십니까.<br>대구 월성동 박찬 통합과학 학원입니다.'),
 ('c', '현재 중학교 3학년 자녀를 두신<br>학부모님께 인사드립니다.'),
 ('c', '==고1 예비반== 수업을 안내드립니다.<br>처음 만나는 **통합과학**을 학생들이<br>원리부터 이해하며 차근차근 따라올 수 있도록<br>매 시간 정성을 다해 가르치겠습니다.'),
 ('c', '==한 학생 한 학생이 좋은 결과를 거둘 수 있도록==<br>==끝까지 곁에서 함께하겠습니다.=='),
 ('img', '01_greeting', '현 중3 학부모님께 — 고1 예비반, 처음 만나는 통합과학 차근차근 준비합니다 · 화금반 화·금 오후 5시 30분 · 수토반 수 오후 5시 30분, 토 오후 3시 30분 · 주 2회'),
 ('q', '처음 만나는 통합과학, 차근차근 준비합니다'),
 ('tbl', [('화금반', '화, 금 **오후 5시 30분**'),
          ('수토반', '수 **오후 5시 30분**, 토 **오후 3시 30분**'),
          ('수업', '주 2회'),
          ('대상', '고1 예비 (현 중3)'),
          ('교재', '완자 통합과학<br>EBS 개념완성 943제 문항편')], None),
 ('c', '개념은 **완자 통합과학**으로 차근차근 다지고,<br>**EBS 개념완성 943제 문항편**으로<br>다양한 문제를 풀어 봅니다.'),
 ('img', '02_book', '교재와 수업 — 개념은 완자 통합과학, 문제는 EBS 개념완성 943제 문항편'),
 ('q', '왜 예비반은 주 2회일까요'),
 ('p', '평소 강의를 해 보면, 시간의 여유가 많을수록 더 상세히 설명하고 더 많은 문제를 함께 풀 수 있었습니다.'),
 ('p', '주 1회 수업에도 나름의 장점이 있을 것입니다.<br>다만 저는 주 2회 수업으로 조금 더 여유로운 시간 속에서 **다양한 지식을 전하고 문제 풀이를 하며, 더 큰 학습 효과**를 거두고자 합니다.'),
 ('c', '그래서 시간의 여유가 있는<br>==고1 예비반 때만==<br>==일주일에 두 번== 수업합니다.'),
 ('c', '고등학교에 올라가면<br>고1 내신반과 고3 수능반은<br>일주일에 한 번밖에 하지 못합니다.'),
 ('img', '03_twice', '왜 예비반은 주 2회일까요 — 세 가지 이유'),
 ('q', '고등학교 과학, 이렇게 바뀝니다'),
 ('p', '· 교육과정 — 2022 개정에 따라 **고1 학생은 모두 통합과학**을 배웁니다.<br>· 내신 — 2025년 고1부터 **5등급제**로 바뀌었습니다.<br>· 수능 — **2028학년도부터 과학탐구는 통합과학 한 과목**입니다. 지금 중3 학생들이 치를 수능도 현재 발표 기준으로 같은 체제입니다.'),
 ('c', '==고1 첫 내신이==<br>==고등학교 3년의 출발점입니다.=='),
 ('img', '04_change', '고등학교 과학, 이렇게 바뀝니다'),
 ('q', '이렇게 강의합니다'),
 ('p', '==① 개념과 원리 위주의 이해 중심 강의==<br>중학교 때 과학 기초가 부족했거나 성적이 아쉬웠던 학생을 위해 **특별 보충 수업**을 준비해 두었습니다.<br>처음부터 차근차근 따라올 수 있도록 돕겠습니다.'),
 ('p', '==② 사고력 · 응용력 향상을 돕는 문제 풀이==<br>자료를 해석하고, 처음 보는 상황에 개념을 적용하는 문제를 함께 풉니다.'),
 ('p', '==③ 원장 직강==<br>처음부터 끝까지 제가 직접 가르치고 상담합니다.'),
 ('q', '일주일 무료 수강'),
 ('c', '먼저 **일주일 들어 보시고**<br>등록을 결정하셔도 됩니다.<br>수업이 아이에게 맞는지<br>직접 확인해 보십시오.'),
 ('c', '① 상담 전화 또는 내원<br>② 수강 예약<br>==③ 일주일 무료 수강==<br>④ 등록 결정'),
 ('img', '06_free', '일주일 무료 수강 후 등록 · 대구 달서구 조암로 25 그루빌딩 501호(월성 CGV 옆) · 053-213-3577'),
 ('q', '오시는 길'),
 ('c', '대구 달서구 조암로 25<br>**그루빌딩 501호** (월성 CGV 옆)'),
 ('c', '상담 문의 **053-213-3577**<br>상담 시간 매일 오후 2시 ~ 오후 10시'),
 ('c', '처음 만나는 통합과학,<br>아이가 자신 있게 시작할 수 있도록<br>정성껏 가르치겠습니다.<br>편하게 전화 주십시오.'),
 ('c', '감사합니다.'),
 ('fine', '남교입 제2019-115호 · 교습비(월) / 총 교습시간<br>중등부 21만 원 / 1,042분 · 26만 7,000원 / 1,303분<br>고등부 22만 원 / 912분 · 31만 7,000원 / 1,303분'),
]

BANNED = ['시작되었', '동영상', '보충자료', '2시간', '7시 30분', '공통과학', '네 단계', '3월 입학 전', '확실히', '11월 3일', '11월 4일', '2027년 2월', '선행', '진도', '미리', '1등급', '완성']
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
        elif t == 'q': out.append(f'<p><br></p><p style="margin:0;text-align:center;font-size:19px;font-weight:700;line-height:1.6;color:#24406F;border-top:1px solid #3B6AD0;border-bottom:1px solid #3B6AD0;padding:14px 0">{b[1]}</p><p><br></p>')
        elif t == 'img':
            src = imgs[b[1]][1 if data_uri else 0]
            out.append(f'<p style="margin:0;text-align:center"><img src="{src}" alt="{html.escape(b[2])}" width="1080" style="width:100%;max-width:100%;height:auto"></p><p><br></p>')
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
head = old[:old.index('<div class="wrap">')].replace('<title>박찬 통합과학 블로그 글</title>', '<title>박찬 통합과학 첫 글 수정판</title>')
script = old[old.index('<script>'):]
nimg = sum(1 for b in POST if b[0] == 'img')
titles = ''.join(f'<div class="row"><span class="k">{"AB"[i]}</span><span class="t">{html.escape(t)}</span><button class="cp" data-text="{html.escape(t)}">복사</button></div>' for i, t in enumerate(TITLES))
tags = ''.join(f'<span>{t}</span>' for t in TAGS)
page = f'''{head}<div class="wrap">
<section class="box"><h1>박찬 통합과학 · 첫 글 수정판</h1><p class="sub">개강일 · '3월 입학 전 확실히' · 월별 진도 그림을 빼고 수업 시간 · 교재 · 새 인사말을 넣은 판 · 합니다체 · 사진 {nimg}장</p></section>
<section class="box"><h2>① 제목 — 하나 고르기</h2>{titles}</section>
<section class="box"><h2>② 본문 — 통째로 복사</h2><button class="cp big" id="richBtn">본문 통째로 복사 — 사진 · 표 · 굵게 · 색 포함</button>
<p class="note">네이버가 일부 서식을 빼면 '글자만 복사'(사진 자리 표시가 들어 있음)를 쓰십시오.</p>
<details style="margin-top:10px"><summary style="font-size:14px;color:var(--muted);cursor:pointer">글자만 복사 (서식 없음)</summary><textarea id="bodyTxt" readonly style="margin-top:8px">{html.escape(body)}</textarea><button class="cp big" data-copy="bodyTxt">글자만 복사</button></details>
<button class="cp big" id="richBtn2" style="background:var(--soft);color:var(--ink);border:1px solid var(--line)">사진이 안 들어가면 — 사진을 글 안에 담아 복사</button></section>
<section class="box"><h2>③ 태그 — 하나씩 입력 후 Enter</h2><div class="tags">{tags}</div><button class="cp big" data-copy="tagTxt">태그 복사(띄어쓰기로 구분)</button><textarea id="tagTxt" readonly style="display:none">{" ".join(TAGS)}</textarea></section>
<section class="box"><h2>④ 네이버에서 고치는 법</h2><ol class="how">
<li>블로그의 첫 글을 열어 <b>수정</b>을 누르고, 본문을 모두 지운 뒤 ②를 붙여 넣기</li>
<li>또는 새 글로 올리고 옛 글은 비공개로 두기</li>
<li>붙인 뒤 <b>사진 1</b>을 눌러 <b>대표</b>로 지정</li>
<li>사진이 빠져 있으면 아래 미리보기 사진을 길게 눌러(PC는 오른쪽 클릭) 저장한 뒤 그 자리에 올리기</li>
<li>제목도 ①로 바꾸기 — 옛 제목의 '3월 입학 전 … 확실히'가 남지 않게</li></ol></section>
<section class="box"><h2>미리보기</h2><article class="post">{prev()}</article></section>
</div>
<template id="rich">{rich(False)}</template><template id="rich2">{rich(True)}</template>
{script}'''
(HERE / 'kit.html').write_text(page, encoding='utf-8')
(HERE / 'post.txt').write_text(body + '\n', encoding='utf-8')
(HERE / 'titles.txt').write_text('\n'.join(TITLES) + '\n', encoding='utf-8')
(HERE / 'tags.txt').write_text('\n'.join(TAGS) + '\n', encoding='utf-8')
print('kit.html', len(page), 'B · 사진', nimg)
