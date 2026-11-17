import html,pathlib,re
M=pathlib.Path('/home/user/autoblog/parkchan-science/marketing')
def kit(n):
    k=(M/f'blog-{n}/kit.html').read_text()
    r=re.search(r'<template id="rich">(.*?)</template>',k,re.S).group(1)
    r=re.sub(r'<p[^>]*>\s*<img[^>]*>\s*</p>','<p><br></p>',r)
    return r,(M/f'blog-{n}/post.txt').read_text(),(M/f'blog-{n}/titles.txt').read_text().strip()
PH={'22': [('1_강의시간표_사진1', '「강의 시간표를 정리해 드립니다.」 문장 바로 아래 빈 줄')], '27': [('2_고1예비반_사진1_표지', '맨 위 첫 줄(「안녕하십니까」 위 빈 줄)'), ('2_고1예비반_사진2_고등학교과학', '「…고3 수능까지 함께하는 중요한 과목입니다.」 아래 빈 줄'), ('2_고1예비반_사진3_오시는길', '「편하게 상담해 드리겠습니다.」 아래 빈 줄')], '25': [('3_고3수능준비반_사진1_표지', '맨 위 첫 줄')], '26': [('4_중등부특강반_사진1_표지', '맨 위 첫 줄')], '28': [('5_반별안내_사진1_표지', '맨 위 첫 줄'), ('5_반별안내_사진2_강의시간표', '소제목 「강의 시간표」 바로 아래 빈 줄')], '23': [('6_원장인사말_사진1_표지', '맨 위 첫 줄')]}
P=[('22','강의 시간표','학원 공지사항','수정',['고3 반 이름 「고3 수능 준비반 (현 고2)」','중등부: 「통합과학」 글자 빼고 「중등부 특강반」 · <b>목요반 오후 2시 ~ 5시 · 토요반 오후 1시 ~ 4시</b>','시간표 사진(고화질)을 넣음 — 지금 이 글엔 사진이 없음','고1 새 반은 일요반 11월 22일(일) 그대로']),
('27','고1 예비반','반별 안내 › 고1 예비반','수정',['강의 시간 「토요반 21일」 → <b>일요반 11월 22일(일)</b>','비공개로 돌린 첫 글 내용 합침(고등학교 과학 변화 · 문제 풀이 · 오시는 길 · 교습비)']),
('25','고3 수능 준비반','반별 안내 › 고3 예비반','수정',['「고3 예비」 → <b>고3 수능 준비반 (현 고2)</b> — 제목 · 첫 인사 · 본문 · 표지 그림','수업 토요반 12월 19일 · 일요반 12월 20일 오후 4시 ~ 7시 그대로']),
('26','중등부 특강반','반별 안내 › 중등부반','수정',['「통합과학」 글자 모두 뺌(표지 그림 · 본문 · 태그)','<b>목요반 오후 2시 ~ 5시 · 토요반 오후 1시 ~ 4시</b> (겨울방학 개강)']),
('28','반별 안내','반별 안내 (맨 위 칸)','수정',['고3 반 이름 · 중등부 특강반(통합과학 뺌 · 목 2시 ~ 5시 · 토 1시 ~ 4시) · 시간표 사진 · 표지 그림']),
('23','원장 인사말','학원 소개','수정',['맨 끝 「중등부반 … 통합과학에 자신감」 → 「중등부 특강반 … 과학에 자신감」']),
('21','그래프 문제 글','통합과학 이야기','사진만',['글은 그대로 두고 사진 3장만 바꿉니다: 글 → 수정 → 사진을 하나씩 눌러 Delete → 그 자리에서 사진 버튼 → zip의 7_그래프글_사진1·2·3 (위에서부터 순서대로) → 발행']),
('19','중학교 비교 글','통합과학 이야기','사진만',['글은 그대로 두고 사진 4장만 바꿉니다: 글 → 수정 → 사진을 하나씩 눌러 Delete → 그 자리에서 사진 버튼 → zip의 8_중학교비교글_사진1~4 (위에서부터 순서대로) → 발행'])]
cards,tpl=[],[]
for i,(n,name,cat,act,chg) in enumerate(P,1):
    r,t,title=kit(n);tpl.append(f'<template id="r{n}">{r}</template>')
    if act=='사진만':
        cards.append(f'<li class="st"><label class="ck"><input type="checkbox" data-k="g{n}"><span></span></label><div class="sb"><h3><em>{i}</em>{name} <small>(여유 있을 때)</small></h3><p class="where">블로그 글: {html.escape(title)}</p><ul class="chg">{chr(10).join(f"<li>{c}</li>" for c in chg)}</ul></div></li>');continue
    cards.append(f'''<li class="st"><label class="ck"><input type="checkbox" data-k="g{n}"><span></span></label><div class="sb">
<h3><em>{i}</em>{name}</h3><p class="where">블로그 글: {html.escape(title)} · 카테고리 {cat}</p>
<ul class="chg">{''.join(f"<li>{c}</li>" for c in chg)}</ul>
<div class="cp"><div class="cph"><b>제목</b><button onclick="cpy(this)">복사</button></div><pre>{html.escape(title)}</pre></div>
<button class="big" data-rich="r{n}" data-txt="t{n}">본문 복사 (표 · 서식 · 태그 포함)</button>
<div class="ph"><b>붙여 넣은 뒤 사진 올리기</b> — 그 자리를 누르고 도구 막대 <b>사진</b> → zip 파일 선택<ol>{''.join(f"<li><b>{f}.png</b> → {w}</li>" for f,w in PH.get(n,[]))}</ol></div>
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
.bar{{position:sticky;top:env(safe-area-inset-top,0px);background:var(--bg);padding:8px 0;z-index:2;font-size:14px;font-weight:700;color:var(--sub)}} .bar i{{font-style:normal;color:var(--ok)}}.ph{{background:var(--soft);border-radius:10px;padding:10px 14px;font-size:14.5px}} .ph ol{{padding-left:20px;margin-top:4px}} h3 small{{font-size:13px;color:var(--sub);font-weight:500}}</style>
<div class="w"><header><h1>박찬 블로그 글 최종본 — 복사해서 붙이기만</h1><p class="lead">원장님 글(A·B·C·D)과 오늘 확인하신 내용으로 8편을 모두 고쳤습니다. 디자인은 글을 다 고친 뒤 한꺼번에 바꿉니다(그림만 갈아 끼우면 되게 준비해 둠).</p></header>
<div class="fix"><b>이번에 바뀐 기준</b><ul><li>고1 예비반 새 반: <b>일요반 11월 22일(일)</b> 오후 1시 ~ 4시 · 기존 화 · 수 · 금 오후 5시 30분 · 겨울방학 수요반 오후 2시 ~ 5시 (주 몇 회인지는 쓰지 않음)</li>
<li>고3: <b>고3 수능 준비반 (현 고2)</b> · 토요반 12월 19일 · 일요반 12월 20일 오후 4시 ~ 7시</li><li>중등부: <b>중등부 특강반</b> — 「통합과학」 글자 없음 · <b>목요반 오후 2시 ~ 5시 · 토요반 오후 1시 ~ 4시</b> · 겨울방학 개강</li></ul></div>
<div class="how"><b>글마다 똑같이</b><ol><li>블로그에서 그 글 → <b>수정</b></li><li>제목 칸: 아래 <b>제목 복사</b> → 기존 제목 지우고 붙여 넣기</li><li>본문 아무 곳 → <b>Ctrl+A</b> → <b>Delete</b></li><li>아래 <b>본문 복사</b> → 본문 칸에 <b>Ctrl+V</b> (사진은 빼고 붙습니다 — 네이버가 붙여 넣은 사진을 「허용되지 않은 양식」으로 지우기 때문)</li><li>칸 안 <b>「붙여 넣은 뒤 사진 올리기」</b>에 적힌 자리에 zip 사진을 올립니다 (직접 올린 사진이 가장 선명합니다)</li><li>오른쪽 위 <b>발행</b> → 카테고리 확인 → <b>발행</b></li></ol><p class="lead" style="margin-top:6px">글자가 통째로 파랗게 들어오면(지운 글의 글자색이 남아서 생김): 본문 <b>Ctrl+A</b> → 도구 막대 <b>글자색</b> → <b>검정</b>. 이번 판은 글자색을 박아 두어 다시 생기지 않게 했습니다.</p>
<p class="lead" style="margin-top:6px">사진은 함께 보낸 <b>박찬_글최종본_사진.zip</b> 하나만 쓰세요. 파일 앞 번호 = 아래 칸 번호입니다. 이전 zip은 쓰지 마세요.</p></div>
<div class="bar">진행 <i id="cnt">0</i> / {len(P)}</div>
<ol class="steps">{''.join(cards)}</ol>
<div class="fix"><b>카테고리 이름 하나 (선택)</b><ul><li>관리 → 메뉴·글·동영상 관리 → 블로그 → 카테고리 관리 → <b>고3 예비반</b>을 눌러 이름을 <b>고3 수능 준비반</b>으로 → 확인</li></ul></div>
</div>
{''.join(tpl)}
<script>
function cpy(b){{const t=b.closest('.cp').querySelector('pre').textContent;navigator.clipboard.writeText(t).then(()=>{{b.textContent='복사됨';setTimeout(()=>b.textContent='복사',1500)}},()=>{{const r=document.createRange();r.selectNodeContents(b.closest('.cp').querySelector('pre'));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Ctrl+C'}})}}
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
