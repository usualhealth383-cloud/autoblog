#!/usr/bin/env python3
"""blog-28 — 고1 예비반 합친 글(첫 글 10-12 + 고1 예비반 11-16, 2026-11-17 현욱님 「원래 글 내용까지 잘 반영해 새 글」). 사진은 링크로 붙이지 않고 파일로 올린다.\n옛 설명: 원장님 글 다듬은 판(고1 예비반 수강 안내, 2026-11-16).\n원래 꼴: 강의 시간표 안내 글(2026-11-12 원장님 메모). 시간이 바뀌면 이 글만 고친다.\n원래 꼴: 두 번째 블로그 글: 통합과학이 중학교 과학·지금까지의 수능 과학과 무엇이 다른가(2026-11-05).
첫 글 수정판(blog-18) 기준을 따른다 — 개강일·보충자료·동영상·공통과학·'확실히' 없음, 시작 시각만, 좁은 줄 간격.
사용: python3 build_kit.py  → kit.html · post.txt · ../../../docs/marketing/blog-28/*.jpg"""
import re, html, base64, hashlib, io, json, pathlib
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent
PUB = HERE.parents[2] / 'docs' / 'marketing' / 'blog-28'
URL = 'https://usualhealth383-cloud.github.io/autoblog/marketing/blog-28/'
BLUE = '#2F5FC4'
TITLES = ['박찬 통합과학 학원 반별 안내']
TAGS = (HERE.parent / 'blog-16' / 'tags.txt').read_text(encoding='utf-8').split()

POST = [('img', 'cover_classes_c', '반별 안내 — 세 반 한눈에 보기'),
 ('p', '안녕하십니까.<br>대구 월성동 박찬 통합과학 학원입니다.<br>저희 학원은 <b>세 반</b>을 원장이 직접 가르칩니다. 아이 학년에 맞는 반을 보시고, 자세한 내용은 반마다 붙은 안내 글에서 확인해 주십시오.'),
 ('q', '고1 예비반 (현 중3)'),
 ('p', '고1 내신부터 고3 수능까지 이어지는 통합과학을 ==처음부터 차근차근== 공부하는 반입니다.'),
 ('tbl', [('일요반 (새로 시작하는 반)', '**11월 22일(일) 개강** · 오후 1시 ~ 4시 · 처음부터'),
 ('화 · 수 · 금 (기존 반)', '오후 5시 30분 · 물질과 규칙성부터 이어서 (11월 12일(목) 기준)'),
 ('수요반 (겨울방학)', '오후 2시 ~ 5시 · 처음부터 · 개강일은 따로 안내해 드리겠습니다')], 0),
 ('c', '<a href="https://blog.naver.com/parkchan3577/224480077519">고1 예비반 자세히 보기 ›</a>'),
 ('q', '고3 수능 준비반 (현 고2)'),
 ('p', '2028학년도 ==첫 통합과학 수능==을 준비하는 반입니다. 이론 정리부터 시작합니다.'),
 ('tbl', [('토요반', '**12월 19일(토) 개강** · 오후 4시 ~ 7시'),
 ('일요반', '**12월 20일(일) 개강** · 오후 4시 ~ 7시')], None),
 ('c', '<a href="https://blog.naver.com/parkchan3577/224480078183">고3 수능 준비반 자세히 보기 ›</a>'),
 ('q', '중등부 특강반'),
 ('p', '==기본 개념과 원리==를 탄탄히 다지는 반입니다.'),
 ('tbl', [('목요반', '오후 2시 ~ 5시 · 겨울방학 개강'),
 ('토요반', '오후 1시 ~ 4시 · 겨울방학 개강')], None),
 ('c', '<a href="https://blog.naver.com/parkchan3577/224480078542">중등부 특강반 자세히 보기 ›</a>'),
 ('q', '강의 시간표'),
 ('img', 'timetable_sun', '박찬 통합과학 강의 시간표'),
 ('c', '어느 반이 맞을지,<br>지금 아이에게 무엇이 필요한지<br>편하게 상담해 드리겠습니다.'),
 ('c', '**상담 문의 053-213-3577**<br>매일 오후 2시 ~ 오후 10시<br>대구 달서구 조암로 25 그루타워 501호 (월성 CGV 옆)'),
 ('c', '감사합니다.')]

BANNED = ['중등부 통합과학', '고3 예비', '11월 21일', '토요반 (새로', '토요반이 새로', '무료', '선행', '1등급', '대구 최초', '반드시', '확실히', '꼭 좋은', '보충', '진도', '미리', '교재', '일주일']
def inline(s, mode):   # mode: rich | prev | txt
    if mode == 'txt':
        s = re.sub(r'<a href="([^"]+)">([^<]+)</a>', r'\2 \1', s)
        return re.sub(r'<[^>]+>', '', re.sub(r'\*\*|==', '', s.replace('<br>', '\n')))
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

HI_IMG={'cover_classes_c': 'blog-28/hi_1_반별안내_표지.png', 'timetable_sun': 'blog-28/hi_2_강의시간표.png'}
for _k,_p in HI_IMG.items():
    _im=Image.open(HERE.parent/_p).convert('RGB');_b=io.BytesIO();_im.save(_b,'JPEG',quality=92)
    imgs[_k]=(imgs[_k][0],'data:image/jpeg;base64,'+base64.b64encode(_b.getvalue()).decode())
C = 'margin:0;line-height:1.9;color:#333333;'
TD = 'border:1px solid #D9CFBD;padding:8px 10px;vertical-align:top;color:#333333;text-align:left;'
HASH = ' '.join('#' + t for t in TAGS)
def rich(data_uri):
    out, k = [], 0
    for b in POST:
        t = b[0]
        if t in ('c', 'p'): out.append(f'<p style="{C}{"text-align:center;" if t == "c" else "text-align:left;"}">{inline(b[1], "rich")}</p>\n<p><br></p>')
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
    out.append(f'<p style="margin:22px 0 0;line-height:1.9;color:#333333;text-align:left;">{HASH}</p>')
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
head = old[:old.index('<div class="wrap">')].replace('<title>박찬 통합과학 블로그 글</title>', '<title>박찬 반별 안내 글</title>')
script = old[old.index('<script>'):]
nimg = sum(1 for b in POST if b[0] == 'img')
titles = ''.join(f'<div class="row"><span class="k">{"AB"[i]}</span><span class="t">{html.escape(t)}</span><button class="cp" data-text="{html.escape(t)}">복사</button></div>' for i, t in enumerate(TITLES))
tags = ''.join(f'<button class="cp tg" data-text="{t}">{t}</button>' for t in TAGS)
head = head.replace('</style>', '.tags button.tg{font-size:14px;min-height:40px;padding:0 12px;background:var(--soft);color:var(--navy);font-weight:700}.tags button.tg.done{opacity:.4}\n</style>', 1)
page = f'''{head}<div class="wrap">
<section class="box"><h1>반별 안내 — 세 반 한눈에</h1><p class="sub">상위 카테고리 「반별 안내」에 직접 올리는 글 · 메뉴와 단추 02를 누르면 「작성된 글이 없습니다」 대신 이 글이 뜹니다 · 사진 {nimg}장</p></section>
<section class="box" style="border-color:#E0A800"><h2>⚠ 이 글이 필요한 까닭</h2><ol class="how"><li>세 반 글은 하위 카테고리(고1 예비반 · 고3 예비반 · 중등부반)에 있어서, 위 메뉴 「반별 안내」나 단추 02를 누르면 「작성된 글이 없습니다」가 뜹니다(직접 확인).</li><li>이 글을 <b>상위 「반별 안내」</b>에 올리면 그 자리에 세 반 요약 · 시간 · 각 반 글로 가는 링크 · 시간표가 뜹니다.</li><li>요일 · 시간은 블로그에 올라간 강의 시간표 글과 같습니다(고1 새 반 일요반 11월 22일).</li></ol></section>
<section class="box"><h2>① 제목</h2>{titles}</section>
<section class="box"><h2>② 본문 — 통째로 복사</h2><button class="cp big" id="richBtn">본문 통째로 복사 — 사진 · 표 · 굵게 · 색 포함</button>
<p class="note">네이버가 일부 서식을 빼면 '글자만 복사'(사진 자리 표시가 들어 있음)를 쓰십시오.</p>
<details style="margin-top:10px"><summary style="font-size:14px;color:var(--muted);cursor:pointer">글자만 복사 (서식 없음)</summary><textarea id="bodyTxt" readonly style="margin-top:8px">{html.escape(body)}</textarea><button class="cp big" data-copy="bodyTxt">글자만 복사</button></details>
</section>
<section class="box"><h2>③ 태그 — 따로 할 일 없음</h2><p class="note" style="margin:0 0 10px">②로 본문을 붙여 넣으면 맨 끝 파란 줄(#태그)이 같이 들어가고, 네이버가 그 줄을 태그로 등록합니다. 붙인 뒤 맨 아래 태그 칸에 태그가 들어왔는지만 보십시오. 안 들어왔으면 아래 태그를 하나씩 눌러 넣으십시오.</p><div class="tags">{tags}</div></section>
<section class="box"><h2>④ 네이버에서 하는 법 — 새 글로 씁니다</h2><ol class="how">
<li>블로그 <b>글쓰기</b> → 제목 칸에 ①을 복사해 붙여 넣기</li>
<li>본문 칸에 ②의 <b>본문 통째로 복사</b> → Ctrl+V</li>
<li>노란 <b>【사진 1 자리】</b>, <b>【사진 2 자리】</b>를 지우고 그 줄에서 <b>사진</b> 버튼 → 함께 보낸 zip의 <b>1_반별안내_표지.png</b>, <b>2_강의시간표.png</b></li>
<li>파란 「자세히 보기 ›」 글씨가 링크로 들어갔는지 한 번 눌러 확인(안 되면 그 글씨를 드래그 → 도구 막대 <b>링크</b> → 아래 주소 붙여 넣기)</li>
<li>오른쪽 위 <b>발행</b> → 카테고리를 <b>반별 안내</b>(하위 말고 위 칸) → <b>발행</b></li></ol>
<p class="note">링크 주소 — 고1: https://blog.naver.com/parkchan3577/224480077519 · 고3: https://blog.naver.com/parkchan3577/224480078183 · 중등부: https://blog.naver.com/parkchan3577/224480078542</p></section>
<section class="box"><h2>미리보기</h2><article class="post">{prev()}</article></section>
</div>
<button id="richBtn2" hidden></button><template id="rich">{rich(True)}</template><template id="rich2">{rich(True)}</template>
{script}<script>document.addEventListener('click',e=>{{const b=e.target.closest('button.tg');if(b)setTimeout(()=>b.classList.add('done'),50)}});</script>'''
(HERE / 'kit.html').write_text(page, encoding='utf-8')
(HERE / 'post.txt').write_text(body + '\n', encoding='utf-8')
(HERE / 'titles.txt').write_text('\n'.join(TITLES) + '\n', encoding='utf-8')
(HERE / 'tags.txt').write_text('\n'.join(TAGS) + '\n', encoding='utf-8')
print('kit.html', len(page), 'B · 사진', nimg)
