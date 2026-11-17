import html,pathlib,re
M=pathlib.Path('/home/user/autoblog/parkchan-science/marketing')
def kit(n):
    k=(M/f'blog-{n}/kit.html').read_text()
    r=re.search(r'<template id="rich">(.*?)</template>',k,re.S).group(1)
    import json
    U=json.load(open('hosted.json'))[n];it=iter(U)
    r=re.sub(r'src="data:image/[^"]+"',lambda m:'src="https://usualhealth383-cloud.github.io/autoblog/marketing/final-01/'+next(it)+'"',r)
    return r,(M/f'blog-{n}/post.txt').read_text(),(M/f'blog-{n}/titles.txt').read_text().strip()
PH={'22': [('1_강의시간표_사진1', '「강의 시간표를 정리해 드립니다.」 문장 바로 아래 빈 줄')], '27': [('2_고1예비반_사진1_표지', '맨 위 첫 줄(「안녕하십니까」 위 빈 줄)'), ('2_고1예비반_사진2_고등학교과학', '「…고3 수능까지 함께하는 중요한 과목입니다.」 아래 빈 줄'), ('2_고1예비반_사진3_오시는길', '「편하게 상담해 드리겠습니다.」 아래 빈 줄')], '25': [('3_고3수능준비반_사진1_표지', '맨 위 첫 줄')], '26': [('4_중등부특강반_사진1_표지', '맨 위 첫 줄')], '28': [('5_반별안내_사진1_표지', '맨 위 첫 줄'), ('5_반별안내_사진2_강의시간표', '소제목 「강의 시간표」 바로 아래 빈 줄')], '23': [('6_원장인사말_사진1_표지', '맨 위 첫 줄')]}
P=[('23','원장 인사말 — 새 글로 한 번 더 (카드 맨 앞으로)','학원 소개','새 글',['첫 화면 카드는 <b>최신 글부터</b> 놓입니다. 원장 인사말을 새 글로 올리면 맨 앞이 됩니다(지금 글은 공감 0 · 댓글 0).','① <b>글쓰기</b>(새 글) → 아래 제목 복사 · 본문 복사 → Ctrl+V','② 맨 위 표지를 한 번 눌러 <b>Delete</b> → 페이지 맨 위 「이 사진 복사」(원장 인사말) → <b>Ctrl+V</b> (카드에 뜨려면 네이버 사진이어야 함)','③ 발행 창에서 카테고리 <b>학원 소개</b>, <b>공지사항으로 등록</b>에 체크 → 발행','④ 예전 원장 인사말 글 → 수정 → 발행 창에서 <b>비공개</b> → 발행']),
('22','강의 시간표','학원 공지사항','수정',['고3 반 이름 「고3 수능 준비반 (현 고2)」','중등부: 「통합과학」 글자 빼고 「중등부 특강반」 · <b>목요반 오후 2시 ~ 5시 · 토요반 오후 1시 ~ 4시</b>','시간표 사진(고화질)을 넣음 — 지금 이 글엔 사진이 없음','고1 새 반은 일요반 11월 22일(일) 그대로']),
('27','고1 예비반','반별 안내 › 고1 예비반','수정',['강의 시간 「토요반 21일」 → <b>일요반 11월 22일(일)</b>','비공개로 돌린 첫 글 내용 합침(고등학교 과학 변화 · 문제 풀이 · 오시는 길 · 교습비)']),
('25','고3 수능 준비반','반별 안내 › 고3 예비반','수정',['「고3 예비」 → <b>고3 수능 준비반 (현 고2)</b> — 제목 · 첫 인사 · 본문 · 표지 그림','수업 토요반 12월 19일 · 일요반 12월 20일 오후 4시 ~ 7시 그대로']),
('26','중등부 특강반','반별 안내 › 중등부반','수정',['「통합과학」 글자 모두 뺌(표지 그림 · 본문 · 태그)','<b>목요반 오후 2시 ~ 5시 · 토요반 오후 1시 ~ 4시</b> (겨울방학 개강)']),
('28','반별 안내','반별 안내 (맨 위 칸)','수정',['고3 반 이름 · 중등부 특강반(통합과학 뺌 · 목 2시 ~ 5시 · 토 1시 ~ 4시) · 시간표 사진 · 표지 그림']),

('21','그래프 문제 글','통합과학 이야기','수정 (여유 있을 때)',['글은 그대로 · 사진 3장을 고화질로']),
('19','중학교 비교 글','통합과학 이야기','수정 (여유 있을 때)',['글은 그대로 · 사진 4장을 고화질로'])]
import base64
COVERS=[('원장 인사말','03_원장인사말_표지'),('반별 안내','10_반별안내_사진1_표지'),('고1 예비반','07_고1예비반_사진1_표지'),('고3 수능 준비반','04_고3예비반_표지'),('중등부 특강반','05_중등부_표지'),('강의 시간표','06_강의시간표'),('그래프 문제 글','08_그래프글_사진1'),('중학교 비교 글','09_중학교비교글_사진1')]
def b64(f): return 'data:image/png;base64,'+base64.b64encode(open(M/'hires'/(f+'.png'),'rb').read()).decode()
CV=''.join(f'<div class="cvr"><img src="{b64(f)}" alt="{t} 대표 사진"><div><b>{t}</b><button class="big" onclick="cpImg(this)">이 사진 복사</button></div></div>' for t,f in COVERS)
TT={'23':'원장 인사말','27':'고1 예비반','25':'고3 수능 준비반','26':'중등부 특강반','22':'강의 시간표','28':'반별 안내','21':'그래프 문제 글','19':'중학교 비교 글'}
TLIST=''.join(f'<div class="cp"><div class="cph"><b>{TT[n]}</b><button onclick="cpy(this)">복사</button></div><pre>{html.escape((M/f"blog-{n}/titles.txt").read_text().strip())}</pre></div>' for n in ['23','27','25','26','22','28','21','19'])
MAP='https://map.naver.com/p/search/%EB%B0%95%EC%B0%AC%ED%86%B5%ED%95%A9%EA%B3%BC%ED%95%99%ED%95%99%EC%9B%90'
B='https://usualhealth383-cloud.github.io/autoblog/marketing/home-04/'
W1='<a href="https://blog.naver.com/PostList.naver?blogId=parkchan3577&categoryNo=1" target="_self"><img src="'+B+'wa_e5abb204.png" width="170" height="330" alt="상담 문의 053-213-3577" border="0"></a>'
W2='<a href="'+MAP+'" target="_blank"><img src="'+B+'wb_7a1fbe2d.png" width="170" height="330" alt="오시는 길" border="0"></a>'
WIDGETS=f'<div class="cp"><div class="cph"><b>위젯 6 · 상담 문의</b><button onclick="cpy(this)">복사</button></div><pre>{html.escape(W1)}</pre></div><div class="cp"><div class="cph"><b>위젯 7 · 오시는 길</b><button onclick="cpy(this)">복사</button></div><pre>{html.escape(W2)}</pre></div>'
cards,tpl=[],[]
for i,(n,name,cat,act,chg) in enumerate(P,1):
    r,t,title=kit(n);tpl.append(f'<template id="r{n}">{r}</template>')
    if False:
        cards.append(f'<li class="st"><label class="ck"><input type="checkbox" data-k="g{n}"><span></span></label><div class="sb"><h3><em>{i}</em>{name} <small>(여유 있을 때)</small></h3><p class="where">블로그 글: {html.escape(title)}</p><ul class="chg">{chr(10).join(f"<li>{c}</li>" for c in chg)}</ul></div></li>');continue
    cards.append(f'''<li class="st"><label class="ck"><input type="checkbox" data-k="g{n}"><span></span></label><div class="sb">
<h3><em>{i}</em>{name}</h3><p class="where">블로그 글: {html.escape(title)} · 카테고리 {cat}</p>
<ul class="chg">{''.join(f"<li>{c}</li>" for c in chg)}</ul>
<div class="cp"><div class="cph"><b>제목</b><button onclick="cpy(this)">복사</button></div><pre>{html.escape(title)}</pre></div>
<button class="big" data-rich="r{n}" data-txt="t{n}">본문 복사 (사진 · 표 · 정렬 · 태그 포함)</button>

<details><summary>서식이 빠지면 — 글자만 복사</summary><textarea id="t{n}" readonly>{html.escape(t)}</textarea><button class="big alt" onclick="cpyT('t{n}')">글자만 복사</button></details></div></li>''')
H=f'''<title>박찬 블로그 글 최종본</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap">
<style>:root{{--bg:#F4F1EA;--card:#fff;--fg:#15213B;--sub:#5D6475;--bd:#E2DCCF;--pt:#1F5BC4;--soft:#EEF3FB;--ok:#2E8A66;--code:#F7F5F0}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#8FB4F2;--soft:#1F2C47;--ok:#5CC49A;--code:#161D2C;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#8FB4F2;--soft:#1F2C47;--ok:#5CC49A;--code:#161D2C;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:'Noto Sans KR',system-ui,sans-serif;word-break:keep-all;line-height:1.7;font-size:16px}}
.w{{max-width:820px;margin:0 auto;padding-inline:16px;padding-block:30px 90px;display:flex;flex-direction:column;gap:16px}}
h1{{font-size:25px;font-weight:900;letter-spacing:-.03em}} .lead{{color:var(--sub);font-size:15px}}
.how{{background:var(--card);border:2px solid var(--pt);border-radius:14px;padding:16px 18px;font-size:15px}} .how ol{{padding-left:20px;display:flex;flex-direction:column;gap:3px;margin-top:6px}}
.fix{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px 18px;font-size:14.5px}} .fix b{{color:var(--fg)}} .fix ul{{padding-left:18px;margin-top:6px;display:flex;flex-direction:column;gap:3px}}
ol.steps{{list-style:none;padding:0;display:flex;flex-direction:column;gap:12px}}
li.st{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px;display:grid;grid-template-columns:30px 1fr;gap:12px}} li.st.done{{opacity:.45}}
.sb{{min-width:0;display:flex;flex-direction:column;gap:10px}} h3{{font-size:18px;font-weight:900}} h3 em{{font-style:normal;color:var(--pt);margin-right:8px}}
.where{{font-size:13.5px;font-weight:700;color:var(--pt);background:var(--soft);border-radius:8px;padding:6px 10px}}
.chg{{padding-left:18px;font-size:14.5px;color:var(--sub);display:flex;flex-direction:column;gap:2px}} .chg b{{color:var(--fg)}}
.ck input{{display:none}} .ck span{{display:block;width:26px;height:26px;border-radius:8px;border:2px solid var(--bd);cursor:pointer}} .ck input:checked+span{{background:var(--ok);border-color:var(--ok);box-shadow:inset 0 0 0 4px var(--card)}}
.cp{{border:1px solid var(--bd);border-radius:10px;overflow:hidden}} .cph{{display:flex;justify-content:space-between;align-items:center;padding:7px 12px;background:var(--code)}}
.cph button{{font:inherit;font-size:13px;font-weight:700;padding:5px 14px;border-radius:8px;border:none;background:var(--pt);color:#fff;cursor:pointer}} .cp pre{{padding:9px 12px;white-space:pre-wrap;font-family:inherit;font-size:15px}}
button.big{{font:inherit;font-weight:900;font-size:16px;padding:14px;border-radius:12px;border:none;background:var(--pt);color:#fff;cursor:pointer;width:100%}} button.big.alt{{background:var(--soft);color:var(--fg);margin-top:8px}}
textarea{{width:100%;height:140px;font:inherit;font-size:13px;border:1px solid var(--bd);border-radius:8px;padding:8px;background:var(--code);color:var(--fg);margin-top:8px;box-sizing:border-box}}
details summary{{cursor:pointer;font-weight:700;font-size:14px;color:var(--sub)}}
.bar{{position:sticky;top:env(safe-area-inset-top,0px);background:var(--bg);padding:8px 0;z-index:2;font-size:14px;font-weight:700;color:var(--sub)}} .bar i{{font-style:normal;color:var(--ok)}}.ph{{background:var(--soft);border-radius:10px;padding:10px 14px;font-size:14.5px}} .ph ol{{padding-left:20px;margin-top:4px}} h3 small{{font-size:13px;color:var(--sub);font-weight:500}}.cvs{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}} .cvr{{display:flex;flex-direction:column;gap:6px;min-width:0}} .cvr img{{width:100%;aspect-ratio:1;object-fit:cover;object-position:top;border:1px solid var(--bd);border-radius:8px}} .cvr b{{font-size:14px}} .cvr .big{{font-size:14px;padding:10px}}</style>
<div class="w"><header><h1>박찬 블로그 글 최종본 — 복사해서 붙이기만</h1><p class="lead">원장님 글(A·B·C·D)과 오늘 확인하신 내용으로 8편을 모두 고쳤습니다. 디자인은 글을 다 고친 뒤 한꺼번에 바꿉니다(그림만 갈아 끼우면 되게 준비해 둠).</p></header>
<div class="fix"><b>이번에 바뀐 기준</b><ul><li>고1 예비반 새 반: <b>일요반 11월 22일(일)</b> 오후 1시 ~ 4시 · 기존 화 · 수 · 금 오후 5시 30분 · 겨울방학 수요반 오후 2시 ~ 5시 (주 몇 회인지는 쓰지 않음)</li>
<li>고3: <b>고3 수능 준비반 (현 고2)</b> · 토요반 12월 19일 · 일요반 12월 20일 오후 4시 ~ 7시</li><li>중등부: <b>중등부 특강반</b> — 「통합과학」 글자 없음 · <b>목요반 오후 2시 ~ 5시 · 토요반 오후 1시 ~ 4시</b> · 겨울방학 개강</li></ul></div>
<div class="how"><b>글마다 똑같이</b><ol><li>블로그에서 그 글 → <b>수정</b></li><li>제목 칸: 아래 <b>제목 복사</b> → 기존 제목 지우고 붙여 넣기</li><li>본문 아무 곳 → <b>Ctrl+A</b> → <b>Delete</b></li><li>아래 <b>본문 복사</b> → 본문 칸에 <b>Ctrl+V</b> — 사진(고화질) · 표 · 가운데/왼쪽 정렬 · 태그가 한 번에 들어갑니다</li><li>오른쪽 위 <b>발행</b> → 카테고리 확인 → <b>발행</b></li></ol><p class="lead" style="margin-top:6px">모든 문단에 정렬과 글자색을 하나하나 박아 두어, 지운 글의 서식(파란 글씨 · 가운데 정렬)이 남아 있어도 덮어씁니다.</p>
</div>
<section class="fix"><b>카드 제목 — 앞 글자만 봐도 무슨 글인지</b><p class="lead" style="margin:6px 0 10px">첫 화면 카드는 제목 앞 9 ~ 10자만 보입니다. 글마다 <b>수정 → 제목만 바꾸기 → 발행</b>(순서는 그대로 유지됩니다).</p><div style="display:flex;flex-direction:column;gap:8px">{TLIST}</div></section>
<section class="fix"><b>첫 화면 아래 빈칸 채우기 — 위젯 2개</b><p class="lead" style="margin:6px 0 10px">관리 → 꾸미기 설정 → <b>레이아웃·위젯 설정</b> → 오른쪽 아래 <b>위젯직접등록</b> → 위젯명 「상담 문의」, 코드 붙여 넣기 → 다음 → 등록. 「오시는 길」도 같게. 회색 판 맨 아래에 생긴 두 위젯을 <b>RSS/ATOM 오른쪽</b>(프로필 · 검색 · RSS 와 같은 줄)으로 끌어 놓고 → <b>적용</b>.</p><div style="display:flex;flex-direction:column;gap:8px">{WIDGETS}</div></section>
<section class="fix" id="cover"><b>첫 화면을 예쁘게 — 글마다 대표 사진 한 장 (Ctrl+V 한 번)</b>
<p class="lead" style="margin:6px 0 10px">첫 화면 큰 사진 · 사진 카드에는 네이버에 직접 들어간 사진만 나옵니다. 사진 버튼 · 파일 찾기 없이, 여기서 <b>이 사진 복사</b> → 글 수정 화면에서 맨 위 표지 사진을 눌러 <b>Delete</b> → 그 자리에 <b>Ctrl+V</b> → 발행. 그러면 네이버 사진(고화질)으로 바뀝니다. <b>원장 인사말 하나만 해도</b> 첫 화면이 「큰 사진 + 인사말」로 바뀝니다.</p>
<div class="cvs">{CV}</div></section>
<div class="bar">진행 <i id="cnt">0</i> / {len(P)}</div>
<ol class="steps">{''.join(cards)}</ol>
<div class="fix"><b>카테고리 이름 하나 (선택)</b><ul><li>관리 → 메뉴·글·동영상 관리 → 블로그 → 카테고리 관리 → <b>고3 예비반</b>을 눌러 이름을 <b>고3 수능 준비반</b>으로 → 확인</li></ul></div>
</div>
{''.join(tpl)}
<script>
function cpy(b){{const t=b.closest('.cp').querySelector('pre').textContent;navigator.clipboard.writeText(t).then(()=>{{b.textContent='복사됨';setTimeout(()=>b.textContent='복사',1500)}},()=>{{const r=document.createRange();r.selectNodeContents(b.closest('.cp').querySelector('pre'));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Ctrl+C'}})}}
async function cpImg(b){{const src=b.closest('.cvr').querySelector('img').src,old=b.textContent;try{{const bl=await (await fetch(src)).blob();await navigator.clipboard.write([new ClipboardItem({{'image/png':bl}})]);b.textContent='복사됨 · 표지 자리에 Ctrl+V'}}catch(e){{b.textContent='복사가 막혔어요 · 사진 위 오른쪽 클릭 → 이미지 복사'}}setTimeout(()=>b.textContent=old,2600)}}
function cpyT(id){{const t=document.getElementById(id);navigator.clipboard.writeText(t.value).catch(()=>{{t.focus();t.select()}})}}
document.querySelectorAll('button[data-rich]').forEach(btn=>btn.addEventListener('click',async e=>{{const b=e.currentTarget,h=document.getElementById(b.dataset.rich).innerHTML,old=b.textContent;let ok=false;
try{{await navigator.clipboard.write([new ClipboardItem({{'text/html':new Blob([h],{{type:'text/html'}}),'text/plain':new Blob([document.getElementById(b.dataset.txt).value],{{type:'text/plain'}})}})]);ok=true}}catch(_){{}}
if(!ok){{const d=document.createElement('div');d.style.cssText='position:absolute;left:-9999px;top:0;width:600px;background:#fff;color:#333';d.innerHTML=h;document.body.appendChild(d);try{{const s=getSelection(),r=document.createRange();r.selectNodeContents(d);s.removeAllRanges();s.addRange(r);ok=document.execCommand('copy');s.removeAllRanges()}}catch(_){{}}d.remove()}}
b.textContent=ok?'복사했습니다 · 본문 칸에 Ctrl+V':'복사가 막혔습니다 · 아래 「글자만 복사」를 써 주세요';setTimeout(()=>b.textContent=old,2600)}}));
const boxes=[...document.querySelectorAll('.ck input')];let S={{}};try{{S=JSON.parse(localStorage.getItem('pc-posts')||'{{}}')}}catch(e){{}}
function upd(){{let n=0;boxes.forEach(x=>{{x.closest('li').classList.toggle('done',x.checked);if(x.checked)n++}});document.getElementById('cnt').textContent=n}}
boxes.forEach(x=>{{x.checked=!!S[x.dataset.k];x.addEventListener('change',()=>{{S[x.dataset.k]=x.checked;try{{localStorage.setItem('pc-posts',JSON.stringify(S))}}catch(e){{}}upd()}})}});upd();
</script>'''
open('posts.html','w').write(H);print(len(H))
