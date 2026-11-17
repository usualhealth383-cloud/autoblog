import base64,io,html,pathlib,re
from PIL import Image
R=pathlib.Path('/home/user/autoblog');M=R/'parkchan-science/marketing'
def d(p,w=1080):
    im=Image.open(p).convert('RGB');im.thumbnail((w,9999));b=io.BytesIO();im.save(b,'JPEG',quality=88);return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
def img(p,name,w=1080):
    return f'<figure class="im"><img src="{d(p,w)}" alt="{name}"><figcaption>{name}</figcaption></figure>'
def cp(label,text):
    return f'<div class="cp"><div class="cph"><b>{label}</b><button onclick="cpy(this)">복사</button></div><pre>{html.escape(text)}</pre></div>'
uid=[0]
def st(title,where,body):
    uid[0]+=1;i=uid[0]
    return f'<li class="st"><label class="ck"><input type="checkbox" data-k="f{i}"><span></span></label><div class="sb"><h3><em>{i}</em>{title}</h3><p class="where">{where}</p>{body}</div></li>'
kit=(M/'blog-27/kit.html').read_text()
rich=re.search(r'<template id="rich">(.*?)</template>',kit,re.S).group(1)
plain=(M/'blog-27/post.txt').read_text()
DONE=['간판(파란 박찬 + 남색 통합과학학원)','미색 바탕 · 1단 레이아웃','단추 5개(학원 소개 · 반별 안내 · 강의 시간표 · 통합과학 이야기 · 상담)','위 메뉴 줄(학원 소개 · 반별 안내 · 학원 공지사항 · 통합과학 이야기)','블로그 이름 · 프로필(남색) · 소개글','옛 첫 글 비공개','글 제목 7개 · 카테고리','휴대폰: 맨 위 공지(강의 시간표) · 소개']
TODO=['PC 첫 화면 그림 카드 자리에 「등록된 사진이 없습니다」 — 글 사진이 링크로 붙어 있어 네이버가 사진으로 보지 않음 (2부로 해결)','휴대폰 첫 화면: 커버 그림의 큰 글씨 위에 네이버가 블로그 이름·버튼을 겹쳐 올려 글자끼리 겹침 (1부 2번)','휴대폰 인기글·전체글도 사진 없이 글자만 (2부로 해결)','고1 예비반 글: 강의 시간이 토요반 21일 — 강의 시간표 글(일요반 22일)과 다름 (2부 5번)','강의 시간표 글: 중등부 표에 「토요반」, 사진 없음 (2부 4번)']
HOW='''<div class="how"><b>사진 바꾸는 법 (모든 글 같음)</b><ol>
<li>블로그에서 그 글을 엽니다 → 글 위쪽(또는 아래쪽) <b>수정</b>.</li>
<li>글쓰기 화면에서 바꿀 사진을 <b>한 번 누릅니다</b> → 키보드 <b>Delete</b> (사진이 지워집니다).</li>
<li>커서가 그 자리(빈 줄)에 있는 채로 화면 <b>맨 위 도구 막대의 「사진」</b> 버튼 → 내 PC → 아래에서 저장해 둔 그림 선택 → <b>열기</b>.</li>
<li>사진이 여러 장인 글은 2~3을 순서대로 반복합니다.</li>
<li>오른쪽 위 초록 <b>발행</b> → 뜬 창에서 카테고리 확인 → 창 아래 <b>발행</b>. 처음 올린 사진이 대표 사진(첫 화면 카드)이 됩니다.</li></ol>
<p>그림 저장: 이 페이지의 그림 위에서 <b>오른쪽 클릭 → 「이미지를 다른 이름으로 저장」</b>. 파일 이름은 아무거나 괜찮습니다.</p></div>'''
A=[
st('첫 화면 그림 카드 줄 수','관리 → 메뉴·글·동영상 관리 → 프롤로그','''<ol class="in"><li>형태: <b>이미지 강조</b> 그대로 (글 강조로 바꾸지 않습니다 — 글자가 먼저 나오고 메인목록이 3줄부터라 맞지 않음).</li>
<li>오른쪽 칸을 아래처럼 맞춥니다. 카테고리는 <b>변경</b>(밑줄 글씨)을 눌러 고르고, 줄 수는 <b>노출수</b> 칸(▾)에서 고릅니다.</li></ol>
<div style="overflow-x:auto"><table class="tb"><tr><th>줄</th><th>사용설정</th><th>카테고리</th><th>노출수</th></tr><tr><td>① 메인 이미지목록</td><td>필수</td><td>전체보기</td><td><b>2줄</b></td></tr><tr><td>② 글목록</td><td>✔ 체크</td><td>학원 공지사항</td><td>1줄</td></tr><tr><td>③ 글목록</td><td>☐ 체크 안 함</td><td>(상관없음)</td><td>–</td></tr></table></div>
<ol class="in" start="3"><li>맨 아래 초록 <b>확인</b>.</li></ol><p class="nt">이렇게 해도 2부(사진 다시 올리기)를 하기 전에는 「등록된 사진이 없습니다」가 그대로 보입니다. 정상입니다.</p>'''),
st('휴대폰 커버를 글자 없는 그림으로','관리 → 기본 설정 → 블로그 정보 → 「모바일앱 커버 이미지」','''<p class="nt">휴대폰에서는 네이버가 커버 위에 블로그 이름·프로필·이웃추가 버튼을 겹쳐 올립니다. 그래서 커버 그림에 큰 글씨가 있으면 글자끼리 겹쳐 지저분합니다(제가 휴대폰 화면으로 확인). 이름은 네이버가 얹어 주니 커버는 글자 없는 남색 그림으로 바꿉니다.</p>
<ol class="in"><li>아래 그림을 저장합니다.</li><li>「모바일앱 커버 이미지」 오른쪽 <b>삭제</b> → <b>등록</b> → 저장한 그림 선택.</li><li>페이지 맨 아래 <b>확인</b>.</li></ol>'''+img(M/'homepage-04/올릴그림/4_모바일커버_글자없음.png','휴대폰 커버 (글자 없는 남색)',600)),
]
B=[
st('원장 인사말 — 표지 사진 1장','글: 박찬 통합과학 원장이 학부모님께 드리는 글 (학원 소개)','<p>위 「사진 바꾸는 법」대로, 맨 위 표지 사진을 아래 그림으로 바꿉니다.</p>'+img(M/'blog-23/images/cover_greeting_b.png','원장 인사말 표지',700)),
st('고3 예비반 — 표지 사진 1장','글: 2028 수능 통합과학, 고2 겨울부터 함께 — 고3 예비반 (반별 안내 › 고3 예비반)','<p>맨 위 표지 사진을 아래 그림으로 바꿉니다.</p>'+img(M/'blog-25/images/cover_go3_b.png','고3 예비반 표지',700)),
st('중등부 특강반 — 표지 사진 1장','글: 중학교 과학을 단단하게, 겨울방학 중등부 특강반 (반별 안내 › 중등부반)','<p>맨 위 표지 사진을 아래 그림으로 바꿉니다.</p>'+img(M/'blog-26/images/cover_middle_b.png','중등부 특강반 표지',700)),
st('강의 시간표 — 표 한 칸 고치고 사진 넣기','글: 박찬 통합과학 학원 강의 시간표 (학원 공지사항)','''<ol class="in"><li>글 → <b>수정</b>.</li>
<li>「중등부 통합과학 특강반」 아래 표에서 두 번째 줄 왼쪽 칸의 <b>토요반</b>을 지우고 <b>일요반</b>이라고 씁니다. (같은 글의 문장 「목요반과 일요반」과 중등부 글이 모두 일요반입니다.)</li>
<li>맨 위 「반별 강의 시간을 한눈에 보실 수 있도록 강의 시간표를 정리해 드립니다.」 문장 <b>바로 아래 빈 줄</b>을 누르고 → 도구 막대 <b>사진</b> → 아래 시간표 그림을 올립니다. (이 글은 지금 사진이 한 장도 없습니다.)</li>
<li><b>발행</b> → <b>발행</b>.</li></ol>'''+img(R/'parkchan-science/marketing/repair-01/t04.png','강의 시간표 (고1 새 반 일요반 11월 22일)',900)),
st('고1 예비반 — 본문 통째로 바꾸기 (첫 글 내용 합친 판)','글: 처음 만나는 통합과학, 차근차근 함께 — 고1 예비반 (반별 안내 › 고1 예비반)','''<p class="nt">비공개로 돌린 첫 글의 내용(고등학교 과학이 바뀌는 세 가지 · 문제 풀이 강의 · 직접 가르치고 상담 · 오시는 길 · 맺음말 · 교습비)을 이 글에 합쳤고, 강의 시간을 강의 시간표 글대로 <b>일요반 11월 22일(일)</b>로 맞췄습니다. 첫 글의 「특별 보충 수업」은 원장님이 정하지 않은 내용이라 뺐습니다.</p>
<ol class="in"><li>글 → <b>수정</b>.</li><li>본문 아무 곳이나 누르고 <b>Ctrl+A</b>(전체 선택) → <b>Delete</b>. 제목은 그대로 둡니다.</li>
<li>아래 <b>「본문 복사」</b> 버튼 → 본문 칸에 <b>Ctrl+V</b>. 표·굵은 글씨·파란 글씨·태그 줄까지 들어갑니다.</li>
<li>본문에 노란 칸 <b>【사진 1 자리】 【사진 2 자리】 【사진 3 자리】</b>가 있습니다. 노란 칸 글자를 지우고, 그 줄에서 <b>사진</b> 버튼으로 아래 그림 1·2·3을 차례로 올립니다.</li>
<li>맨 아래 교습비 세 줄은 작은 회색 글씨로 들어갑니다. 그대로 둡니다.</li>
<li><b>발행</b> → 카테고리 「고1 예비반」 확인 → <b>발행</b>.</li></ol>
<button class="big" id="richBtn">본문 복사 (서식 포함)</button>
<details><summary>붙여 넣었는데 서식이 빠지면 — 글자만 복사</summary><textarea id="bodyTxt" readonly>'''+html.escape(plain)+'''</textarea><button class="big alt" onclick="cpyT()">글자만 복사</button></details>'''
+img(M/'blog-27/images/cover_go1_b.png','사진 1 · 표지',700)+img(M/'blog-27/images/04_change.png','사진 2 · 고등학교 과학, 이렇게 바뀝니다',700)+img(M/'blog-27/images/07_visit_b.png','사진 3 · 오시는 길',700)),
st('그래프 문제 글 — 사진 3장','글: 고등학교 과학 시험, 왜 그래프 문제가 많을까요? (통합과학 이야기)','<p>글 속 사진 3장을 위에서부터 차례로 아래 1·2·3으로 바꿉니다. (지금도 보이지만 링크라 첫 화면 카드에 안 잡힙니다.)</p>'+''.join(img(M/f'blog-21/images/{n}.png',f'사진 {i}',600) for i,n in enumerate(['c01_cover','c02_graph_b','c03_answer_b'],1))),
st('중학교 비교 글 — 사진 4장','글: 통합과학, 중학교 과학과 무엇이 다를까요? (통합과학 이야기)','<p>글 속 사진 4장을 위에서부터 차례로 아래 1·2·3·4로 바꿉니다.</p>'+''.join(img(M/f'blog-19/images/{n}.png',f'사진 {i}',600) for i,n in enumerate(['a01_cover','a02_question','a03_suneung','a04_study'],1))),
]
H=f'''<title>박찬 블로그 마무리</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap">
<style>:root{{--bg:#F4F1EA;--card:#fff;--fg:#15213B;--sub:#5D6475;--bd:#E2DCCF;--pt:#1F5BC4;--soft:#EEF3FB;--ok:#2E8A66;--bad:#B4462F;--code:#F7F5F0}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#8FB4F2;--soft:#1F2C47;--ok:#5CC49A;--bad:#E8846E;--code:#161D2C;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#8FB4F2;--soft:#1F2C47;--ok:#5CC49A;--bad:#E8846E;--code:#161D2C;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:'Noto Sans KR',system-ui,sans-serif;word-break:keep-all;line-height:1.7;font-size:16px}}
.w{{max-width:860px;margin:0 auto;padding-inline:16px;padding-block:30px 90px;display:flex;flex-direction:column;gap:18px}}
h1{{font-size:26px;font-weight:900;letter-spacing:-.03em}} .lead{{color:var(--sub);font-size:15px}}
h2{{font-size:21px;font-weight:900;margin-top:14px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}} h2 small{{font-size:14px;color:var(--sub);font-weight:500}}
.state{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px;display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.state h3{{font-size:15px;font-weight:900;margin-bottom:6px}} .state ul{{padding-left:18px;font-size:14.5px;display:flex;flex-direction:column;gap:3px}} .state>div{{min-width:0}}
.ok h3{{color:var(--ok)}} .no h3{{color:var(--bad)}}
ol.steps{{list-style:none;padding:0;display:flex;flex-direction:column;gap:12px}}
li.st{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px;display:grid;grid-template-columns:30px 1fr;gap:12px}} li.st.done{{opacity:.5}}
.sb{{min-width:0;display:flex;flex-direction:column;gap:10px}} h3 em{{font-style:normal;color:var(--pt);margin-right:8px}}
li.st h3{{font-size:17.5px;font-weight:900;letter-spacing:-.02em}} .where{{font-size:13.5px;font-weight:700;color:var(--pt);background:var(--soft);border-radius:8px;padding:6px 10px;width:fit-content;max-width:100%}}
.ck input{{display:none}} .ck span{{display:block;width:26px;height:26px;border-radius:8px;border:2px solid var(--bd);cursor:pointer}} .ck input:checked+span{{background:var(--ok);border-color:var(--ok);box-shadow:inset 0 0 0 4px var(--card)}}
ol.in{{padding-left:20px;font-size:15px;display:flex;flex-direction:column;gap:5px}} .nt{{font-size:14px;color:var(--sub)}} .sb>p{{font-size:15px}}
.tb{{border-collapse:collapse;font-size:13.5px;width:100%;min-width:300px}} .tb th,.tb td{{border:1px solid var(--bd);padding:7px 9px;text-align:left}} .tb th{{background:var(--code)}}
.how{{background:var(--card);border:2px solid var(--pt);border-radius:14px;padding:18px;font-size:15px}} .how ol{{padding-left:20px;margin:8px 0;display:flex;flex-direction:column;gap:4px}} .how p{{font-size:14px;color:var(--sub)}}
.cp{{border:1px solid var(--bd);border-radius:10px;overflow:hidden}} .cph{{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:var(--code)}}
.cph button{{font:inherit;font-size:13px;font-weight:700;padding:5px 14px;border-radius:8px;border:none;background:var(--pt);color:#fff;cursor:pointer}} .cp pre{{padding:10px 12px;white-space:pre-wrap;font-family:inherit;font-size:14.5px}}
button.big{{font:inherit;font-weight:900;font-size:16px;padding:14px;border-radius:12px;border:none;background:var(--pt);color:#fff;cursor:pointer;width:100%}} button.big.alt{{background:var(--soft);color:var(--fg);margin-top:8px}}
textarea{{width:100%;height:160px;font:inherit;font-size:13px;border:1px solid var(--bd);border-radius:8px;padding:8px;background:var(--code);color:var(--fg);margin-top:8px;box-sizing:border-box}}
figure.im{{display:flex;flex-direction:column;gap:4px}} figure.im img{{width:100%;max-width:420px;border:1px solid var(--bd);border-radius:8px}} figcaption{{font-size:13.5px;font-weight:700}}
details summary{{cursor:pointer;font-weight:700;font-size:14px;color:var(--pt)}}
.bar{{position:sticky;top:env(safe-area-inset-top,0px);background:var(--bg);padding:8px 0;z-index:2;font-size:14px;font-weight:700;color:var(--sub)}} .bar i{{font-style:normal;color:var(--ok)}}
@media (max-width:600px){{.state{{grid-template-columns:1fr}}}}</style>
<div class="w"><header><h1>박찬 블로그 마무리 — 이 한 장만 보세요</h1><p class="lead">이전에 보낸 순서표·사진 묶음·안내는 모두 잊으셔도 됩니다. 이 페이지에 필요한 글·사진·순서가 다 있습니다. 위에서부터 하고, 끝낸 칸은 왼쪽 네모를 누르세요. 모두 PC에서 합니다.</p></header>
<section class="state"><div class="ok"><h3>✔ 끝난 것 (11월 17일 제가 블로그를 직접 열어 확인)</h3><ul>{''.join(f"<li>{x}</li>" for x in DONE)}</ul></div><div class="no"><h3>✘ 남은 문제</h3><ul>{''.join(f"<li>{x}</li>" for x in TODO)}</ul></div></section>
<div class="bar">진행 <i id="cnt">0</i> / {uid[0]}</div>
<h2>1부 · 설정 2가지 <small>5분</small></h2><ol class="steps">{''.join(A)}</ol>
<h2>2부 · 글 7개 고치기 <small>글마다 1~5분 · 위 1~5번이 중요, 6·7번은 여유 있을 때</small></h2>{HOW}<ol class="steps">{''.join(B)}</ol>
<p class="lead">끝나면 「끝」이라고만 보내 주세요. PC와 휴대폰 화면을 제가 직접 열어 확인하고 결과를 알려 드립니다.</p></div>
<template id="rich">{rich}</template>
<script>
function cpy(b){{const t=b.closest('.cp').querySelector('pre').textContent;navigator.clipboard.writeText(t).then(()=>{{b.textContent='복사됨';setTimeout(()=>b.textContent='복사',1500)}},()=>{{const r=document.createRange();r.selectNodeContents(b.closest('.cp').querySelector('pre'));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Ctrl+C'}})}}
function cpyT(){{const t=document.getElementById('bodyTxt');navigator.clipboard.writeText(t.value).catch(()=>{{t.focus();t.select()}})}}
document.getElementById('richBtn').addEventListener('click',async e=>{{const b=e.currentTarget,h=document.getElementById('rich').innerHTML,old=b.textContent;let ok=false;
try{{await navigator.clipboard.write([new ClipboardItem({{'text/html':new Blob([h],{{type:'text/html'}}),'text/plain':new Blob([document.getElementById('bodyTxt').value],{{type:'text/plain'}})}})]);ok=true}}catch(_){{}}
if(!ok){{const d=document.createElement('div');d.style.cssText='position:absolute;left:-9999px;top:0;width:600px;background:#fff;color:#333';d.innerHTML=h;document.body.appendChild(d);try{{const s=getSelection(),r=document.createRange();r.selectNodeContents(d);s.removeAllRanges();s.addRange(r);ok=document.execCommand('copy');s.removeAllRanges()}}catch(_){{}}d.remove()}}
b.textContent=ok?'복사했습니다 · 네이버 본문에 Ctrl+V':'복사가 막혔습니다 · 아래 「글자만 복사」를 써 주세요';setTimeout(()=>b.textContent=old,2600)}});
const boxes=[...document.querySelectorAll('.ck input')];let S={{}};try{{S=JSON.parse(localStorage.getItem('pc-final')||'{{}}')}}catch(e){{}}
function upd(){{let n=0;boxes.forEach(x=>{{x.closest('li').classList.toggle('done',x.checked);if(x.checked)n++}});document.getElementById('cnt').textContent=n}}
boxes.forEach(x=>{{x.checked=!!S[x.dataset.k];x.addEventListener('change',()=>{{S[x.dataset.k]=x.checked;try{{localStorage.setItem('pc-final',JSON.stringify(S))}}catch(e){{}}upd()}})}});upd();
</script>'''
open('setup.html','w').write(H);print(len(H),uid[0])
