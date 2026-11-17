import base64,io,html,pathlib
from PIL import Image
R=pathlib.Path('/home/user/autoblog')
def d(p,w=1080):
    im=Image.open(p).convert('RGB');im.thumbnail((w,9999));b=io.BytesIO();im.save(b,'JPEG',quality=88);return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
M=R/'parkchan-science/marketing'
def img(p,name,w=1080,cls=''):
    return f'<figure class="im {cls}"><img src="{d(p,w)}" alt="{name}"><figcaption>{name} <span>· 오른쪽 클릭 → 이미지를 다른 이름으로 저장</span></figcaption></figure>'
def cp(label,text):
    return f'<div class="cp"><div class="cph"><b>{label}</b><button onclick="cpy(this)">복사</button></div><pre>{html.escape(text)}</pre></div>'
uid=[0]
def st(title,body,where=''):
    uid[0]+=1;i=uid[0]
    w=f'<p class="where">{where}</p>' if where else ''
    return f'<li class="st" id="s{i}"><label class="ck"><input type="checkbox" data-k="s{i}"><span></span></label><div class="sb"><h3>{title}</h3>{w}{body}</div></li>'
INTRO='''과학이 어렵게 느껴지는 아이도 '아, 이래서 그렇구나' 하는 순간을 만납니다. 그 순간까지 원장이 곁에서 직접 가르치겠습니다.

대구 월성동(월성 CGV 옆) 통합과학 전문 학원
고1 예비 · 고1 내신 · 고3 수능 · 중등부 특강
상담 053-213-3577'''
A=[
st('간판 아래 메뉴 줄에 「통합과학 이야기」 넣기','''<ol class="in"><li>아래쪽 <b>상단 메뉴 지정</b>의 <b>왼쪽 상자(블로그 카테고리)</b>에서 맨 아래 <b>통합과학 이야기</b>를 한 번 누릅니다.</li>
<li>두 상자 사이 <b>선택 ›</b> 버튼을 누릅니다.</li><li>오른쪽 상자(선택한 메뉴)가 <b>학원 소개 · 반별 안내 · 학원 공지사항 · 통합과학 이야기</b> 네 줄이면 됩니다.</li>
<li>위쪽 표의 <b>대표메뉴는 프롤로그 그대로</b>(대표메뉴는 프롤로그·블로그만 고를 수 있습니다).</li><li>맨 아래 초록 <b>확인</b>.</li></ol>''','관리 → 메뉴·글·동영상 관리 → 메뉴 관리 → 상단메뉴 설정'),
st('첫 화면(프롤로그)을 「원장 인사말이 크게 뜨는 대문」으로','''<ol class="in"><li>형태에서 맨 위 <b>글 강조</b> 동그라미를 누릅니다 (지금은 이미지 강조).</li>
<li>글 강조 오른쪽 세 줄을 아래 표대로 맞춥니다. 카테고리는 <b>변경</b>(밑줄 글씨)을 눌러 고르고, 줄 수는 오른쪽 <b>노출수</b> 칸에서 고릅니다.</li></ol>
<table class="tb"><tr><th>줄</th><th>사용</th><th>카테고리</th><th>노출수</th></tr>
<tr><td>① 메인목록</td><td>필수</td><td><b>학원 소개</b></td><td><b>1줄</b></td></tr>
<tr><td>② 이미지목록</td><td>✔ 체크</td><td><b>전체보기</b></td><td><b>2줄</b></td></tr>
<tr><td>③ 글목록</td><td>✔ 체크</td><td>학원 공지사항</td><td>1줄</td></tr></table>
<ol class="in" start="3"><li>맨 아래 초록 <b>확인</b>.</li></ol>
<p class="nt">① 학원 소개에는 원장 인사말 한 편만 있어서(첫 글은 비공개 확인함) 그 글이 사진과 함께 크게 뜹니다. ② 반별 안내로 두면 「등록된 사진이 없습니다」가 떠서 전체보기로 바꿉니다. 사진 카드는 <b>2부의 사진 올리기</b>를 해야 채워집니다.</p>''','관리 → 메뉴·글·동영상 관리 → 프롤로그 (또는 상단메뉴 설정 화면의 「프롤로그 관리 ›」)'),
st('블로그 정보 — 이름 · 별명 · 소개글','''<p class="nt">아래를 복사해 각 칸에 붙여 넣고 맨 아래 <b>확인</b>. (소개글은 넣으셨으면 건너뛰기)</p>'''+cp('블로그명','박찬 통합과학 학원')+cp('별명','박찬 원장')+cp('소개글',INTRO),'관리 → 기본 설정 → 블로그 정보'),
st('휴대폰 커버','''<ol class="in"><li>아래 그림을 저장합니다.</li><li>같은 화면(블로그 정보) 아래쪽 <b>모바일앱 커버 이미지 → 등록</b>으로 올리고 <b>확인</b>.</li></ol>'''+img(M/'homepage-04/올릴그림/4_모바일커버_남색.png','모바일 커버',700,'sm'),'관리 → 기본 설정 → 블로그 정보 (아래쪽)'),
st('오른쪽 위 네이버 메뉴 글씨','<p>오른쪽 위 「이웃블로그 · 블로그 홈」 글씨가 흐리면: 리모콘 <b>네이버 메뉴</b> → 디자인 <b>맨 아래(검정)</b> → <b>적용</b>. 지금 화면은 또렷해서 했으면 건너뛰기.</p>','관리 → 꾸미기 설정 → 세부 디자인 설정 → 리모콘'),
]
POSTSTEP='''<ol class="in"><li>그 글 열기 → <b>수정</b></li><li>맨 위 표지 사진을 눌러 <b>Delete</b></li><li>그 자리에서 맨 위 도구 막대 <b>사진</b> 버튼 → 아래에서 저장한 그림 올리기</li><li>사진을 눌러 <b>대표</b> → 오른쪽 위 <b>발행</b> → <b>발행</b></li></ol>'''
B=[
st('원장 인사말 글 — 표지 사진 다시 올리기','<p class="nt">링크로 붙은 사진이라 네이버가 사진으로 안 봅니다 → 첫 화면에 안 뜸.</p>'+POSTSTEP+img(M/'blog-23/images/cover_greeting_b.png','원장 인사말 표지',800,'sm'),'글: 박찬 통합과학 원장이 학부모님께 드리는 글'),
st('고3 예비반 글 — 표지 사진','글 수정 순서는 위와 같습니다.'+img(M/'blog-25/images/cover_go3_b.png','고3 예비반 표지',800,'sm'),'글: 2028 수능 통합과학, 고2 겨울부터 함께 — 고3 예비반'),
st('중등부 특강반 글 — 표지 사진','글 수정 순서는 위와 같습니다.'+img(M/'blog-26/images/cover_middle_b.png','중등부 표지',800,'sm'),'글: 중학교 과학을 단단하게, 겨울방학 중등부 특강반'),
st('강의 시간표 글 — 표 한 칸 고치고 사진 넣기','''<ol class="in"><li>글 → <b>수정</b></li><li>중등부 표에서 <b>토요반</b> 줄을 <b>일요반</b>으로 (같은 글 문장과 중등부 글이 모두 「목요반 · 일요반」입니다)</li>
<li>첫 인사 문단 아래에 아래 시간표 그림을 <b>사진</b> 버튼으로 올리고 <b>대표</b> → 발행</li></ol>'''+img(R/'parkchan-science/marketing/repair-01/t04.png','강의 시간표 (일요반 11월 22일)',900,'sm'),'글: 박찬 통합과학 학원 강의 시간표'),
st('고1 예비반 글 — 두 글 합친 판으로 고쳐 쓰기','<p>따로 만든 묶음에서 본문을 복사해 붙이고, 노란 사진 자리에 그림 3장을 올립니다.</p><p><a href="https://claude.ai/artifact/6Gb7WKWj8exkjaV3xtx5AT">고1 예비반 합친 글 묶음 열기 ›</a></p>','글: 처음 만나는 통합과학, 차근차근 함께 — 고1 예비반'),
st('(여유 있을 때) 그래프 · 중학교 비교 글 사진','<p>지금도 사진이 보이지만 링크라서 첫 화면 카드에 안 잡힙니다. 같은 방법으로 바꾸면 카드가 늘어납니다.</p><details><summary>그림 보기 (7장)</summary>'+''.join(img(M/f'blog-21/images/{n}.png',f'그래프 글 {i}',700,'sm') for i,n in enumerate(['c01_cover','c02_graph_b','c03_answer_b'],1))+''.join(img(M/f'blog-19/images/{n}.png',f'중학교 비교 글 {i}',700,'sm') for i,n in enumerate(['a01_cover','a02_question','a03_suneung','a04_study'],1))+'</details>','글: 고등학교 과학 시험, 왜 그래프 문제가 많을까요 / 통합과학, 중학교 과학과 무엇이 다를까요'),
]
H=f'''<title>박찬 블로그 마무리</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap">
<style>:root{{--bg:#F4F1EA;--card:#fff;--fg:#15213B;--sub:#5D6475;--bd:#E2DCCF;--pt:#1F5BC4;--soft:#EEF3FB;--ok:#2E8A66;--code:#F7F5F0;--y:#FFF6DB}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#8FB4F2;--soft:#1F2C47;--ok:#5CC49A;--code:#161D2C;--y:#2E2717;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#8FB4F2;--soft:#1F2C47;--ok:#5CC49A;--code:#161D2C;--y:#2E2717;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:'Noto Sans KR',system-ui,sans-serif;word-break:keep-all;line-height:1.7;font-size:16px}}
.w{{max-width:860px;margin:0 auto;padding-inline:16px;padding-block:30px 90px;display:flex;flex-direction:column;gap:18px}}
h1{{font-size:26px;font-weight:900;letter-spacing:-.03em}} .lead{{color:var(--sub);font-size:15px}}
h2{{font-size:20px;font-weight:900;margin-top:10px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}} h2 small{{font-size:14px;color:var(--sub);font-weight:500}}
ol.steps{{list-style:none;padding:0;display:flex;flex-direction:column;gap:12px}}
li.st{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px;display:grid;grid-template-columns:30px 1fr;gap:12px}}
li.st.done{{opacity:.55}} .sb{{min-width:0;display:flex;flex-direction:column;gap:8px}}
h3{{font-size:17px;font-weight:900;letter-spacing:-.02em}} .where{{font-size:13.5px;font-weight:700;color:var(--pt);background:var(--soft);border-radius:8px;padding:6px 10px;width:fit-content}}
.ck input{{display:none}} .ck span{{display:block;width:26px;height:26px;border-radius:8px;border:2px solid var(--bd);cursor:pointer}}
.ck input:checked+span{{background:var(--ok);border-color:var(--ok);box-shadow:inset 0 0 0 4px var(--card)}}
ol.in{{padding-left:20px;font-size:15px;display:flex;flex-direction:column;gap:4px}} .nt{{font-size:14px;color:var(--sub)}} .sb p{{font-size:15px}}
.tb{{border-collapse:collapse;font-size:14.5px;width:100%}} .tb th,.tb td{{border:1px solid var(--bd);padding:7px 9px;text-align:left}} .tb th{{background:var(--code);font-weight:700}}
.cp{{border:1px solid var(--bd);border-radius:10px;overflow:hidden}} .cph{{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:var(--code)}}
.cph button{{font:inherit;font-size:13px;font-weight:700;padding:5px 14px;border-radius:8px;border:none;background:var(--pt);color:#fff;cursor:pointer}}
.cp pre{{padding:10px 12px;white-space:pre-wrap;font-family:inherit;font-size:14.5px}}
figure.im{{display:flex;flex-direction:column;gap:4px}} figure.im img{{width:100%;border:1px solid var(--bd);border-radius:8px}} figure.im.sm img{{max-width:360px}}
figcaption{{font-size:13px;font-weight:700}} figcaption span{{font-weight:500;color:var(--sub)}}
details summary{{cursor:pointer;font-weight:700;font-size:14px;color:var(--pt)}} details[open]{{display:flex;flex-direction:column;gap:10px}}
.bar{{position:sticky;top:env(safe-area-inset-top,0px);background:var(--bg);padding:8px 0;z-index:2;font-size:14px;font-weight:700;color:var(--sub)}}
.bar i{{font-style:normal;color:var(--ok)}}
a{{color:var(--pt);font-weight:700}}</style>
<div class="w"><header><h1>박찬 블로그 마무리 — 한 장 순서표</h1><p class="lead">여기 있는 것만 위에서부터 하시면 끝납니다. 붙여 넣을 글은 <b>복사</b> 버튼, 그림은 <b>오른쪽 클릭 → 이미지를 다른 이름으로 저장</b>. 끝낸 칸은 왼쪽 네모를 누르면 흐려집니다(이 브라우저에 기억).</p></header>
<div class="bar">진행 <i id="cnt">0</i> / {uid[0]}</div>
<h2>1부 · 메뉴와 화면 설정 <small>지금 할 것 · PC</small></h2><ol class="steps">{''.join(A)}</ol>
<h2>2부 · 글 고치기 <small>마지막에 모아서</small></h2><ol class="steps">{''.join(B)}</ol>
<p class="lead">다 하셨으면 「끝」이라고만 말씀해 주세요. 블로그는 제가 직접 열어 확인합니다.</p></div>
<script>
function cpy(b){{const t=b.closest('.cp').querySelector('pre').textContent;const ok=()=>{{b.textContent='복사됨';setTimeout(()=>b.textContent='복사',1500)}};
try{{navigator.clipboard.writeText(t).then(ok,()=>sel(b))}}catch(e){{sel(b)}}}}
function sel(b){{const r=document.createRange();r.selectNodeContents(b.closest('.cp').querySelector('pre'));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Ctrl+C'}}
const boxes=[...document.querySelectorAll('.ck input')];let S={{}};try{{S=JSON.parse(localStorage.getItem('pc-setup')||'{{}}')}}catch(e){{}}
function upd(){{let n=0;boxes.forEach(x=>{{x.closest('li').classList.toggle('done',x.checked);if(x.checked)n++}});document.getElementById('cnt').textContent=n}}
boxes.forEach(x=>{{x.checked=!!S[x.dataset.k];x.addEventListener('change',()=>{{S[x.dataset.k]=x.checked;try{{localStorage.setItem('pc-setup',JSON.stringify(S))}}catch(e){{}}upd()}})}});upd();
</script>'''
open('setup.html','w').write(H);print(len(H))
