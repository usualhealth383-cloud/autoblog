import base64,io,html
from PIL import Image
def d(p,w):
    im=Image.open(p).convert('RGB');im.thumbnail((w,9999));b=io.BytesIO();im.save(b,'JPEG',quality=85);return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
BASE='https://usualhealth383-cloud.github.io/autoblog/marketing/home-02/'
CAT='https://blog.naver.com/PostList.naver?blogId=parkchan3577&categoryNo='
BT=[(1,'학원 소개',1),(2,'반별 안내',6),(3,'강의 시간표',11),(4,'통합과학 이야기',12),(5,'상담 오시는 길',1)]
def code(n,t,c): return '<a href="'+CAT+str(c)+'" target="_self"><img src="'+BASE+'btn'+str(n)+'_e1.png" width="170" height="120" alt="'+t+'" border="0"></a>'
codes=''.join(f'<div class="cd"><div class="ch"><b>{n} · {t}</b><button onclick="cp(this)">코드 복사</button></div><pre>{html.escape(code(n,t,c))}</pre></div>' for n,t,c in BT)
pv,mc=d('out/pv.png',1200),d('out/mc.png',500)
def step(n,title,body,done=False):
    tag='<span class="dn">끝냄</span>' if done else ''
    return f'<li class="{"done" if done else ""}"><div class="sn">{n}</div><div class="sb"><h3>{title}{tag}</h3>{body}</div></li>'
S=[
step(1,'스킨 · 1단 레이아웃 · 위젯 정리','<p>베이직 스킨, 1단 레이아웃, 서재·지도·블로그정보 빼기.</p>',True),
step(2,'바탕을 미색으로','<p><b>관리 → 꾸미기 설정 → 세부 디자인 설정</b> → 리모콘 <b>스킨배경 → 직접등록</b></p><ul><li>상단 영역: <b>2_스킨배경_상단</b></li><li>하단 영역(패턴): 컬러 <b>F6F2E9</b></li></ul>',True),
step(3,'간판을 새 그림으로 바꾸기','<p>같은 리모콘 <b>타이틀</b> → 디자인 → 직접등록 → 지금 그림을 지우고 <b>1_타이틀</b>(새 판) 등록 → 영역 높이 <b>300</b> · 블로그 제목 표시 <b>끔</b> → <b>적용</b></p>'),
step(4,'네이버 메뉴 글씨 진하게','<p>리모콘 <b>네이버 메뉴</b> → 디자인 <b>맨 아래(검정 글씨)</b> → <b>적용</b>. 오른쪽 위 \'이웃블로그 · 블로그 홈\'이 보이면 됩니다. 리모콘 <b>블로그 메뉴</b>도 흐리면 진한 글씨로.</p>'),
step(5,'단추 5개를 간판 아래로','<p><b>꾸미기 설정 → 레이아웃·위젯 설정</b>에서 회색 판을 이렇게 맞추고 <b>적용</b>.</p><pre class="lay">[네이버메뉴]\n[타이틀]\n[메뉴 형태]\n[학원 소개][반별 안내][강의 시간표][통합과학 이야기][상담]\n[글 영역]\n[검색][RSS][프로필영역][카테고리]</pre><p class="nt">단추 그림은 새 디자인으로 이미 바꿔 두었어요. 위젯을 다시 등록할 필요는 없어요. 아직 다섯 개를 다 등록하지 않았다면 맨 아래 코드를 쓰세요.</p>'),
step(6,'블로그 정보 · 프로필','<p><b>기본 설정 → 블로그 정보</b></p><ul><li>블로그명: <b>박찬 통합과학 학원</b></li><li>별명: <b>박찬 원장</b></li><li>소개글: <b>대구 월성동 통합과학 전문 학원 · 원장 직강 · 상담 053-213-3577 (매일 오후 2시 ~ 10시)</b></li><li>프로필 이미지: <b>3_프로필</b></li></ul>'),
step(7,'글 목록을 그림 카드로 (프롤로그)','<p><b>메뉴·글·동영상 관리 → 프롤로그</b></p><ul><li>형태: <b>이미지 강조</b></li><li>\'반별 안내\' 줄은 비어 보이니 <b>고1 예비반 · 고3 예비반 · 중등부반</b>으로 바꿔요(줄 추가)</li></ul>'),
step(8,'옛 글 제목 짧게','<ul><li>고1 예비반 수업을 안내드립니다</li><li>통합과학, 중학교 과학과 무엇이 다를까요</li><li>고등학교 과학 시험, 왜 그래프 문제가 많을까요</li><li>박찬 통합과학 학원 강의 시간표</li></ul><p class="nt">글 → 수정 → 제목만 바꾸고 다시 발행.</p>'),
step(9,'휴대폰 커버','<p>네이버 블로그 앱 → 내 블로그 → <b>홈편집</b> → 커버 스타일(그림이 위쪽을 크게 채우는 모양) → 커버 이미지 <b>4_모바일커버</b> → 소개글은 6단계와 같게 → <b>적용</b></p>'),
step(10,'마지막 점검 · 사진 두 장','<ul><li>PC: 간판 → 단추 5개 → 그림 카드 순서인가요?</li><li>단추 5개를 눌러 맞는 곳으로 가나요?</li><li>휴대폰: 커버 글씨와 블로그 이름이 겹치지 않나요?</li></ul>'),
]
H=f'''<title>박찬 블로그 최종 순서표</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap">
<style>:root{{--bg:#F4F1EA;--card:#fff;--fg:#15213B;--sub:#5D6475;--bd:#E2DCCF;--pt:#1F5BC4;--soft:#EEF3FB;--ok:#2E8A66;--code:#F7F5F0}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#8FB4F2;--soft:#1F2C47;--ok:#5CC49A;--code:#161D2C;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#8FB4F2;--soft:#1F2C47;--ok:#5CC49A;--code:#161D2C;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:'Noto Sans KR',system-ui,sans-serif;word-break:keep-all;line-height:1.7;font-size:16px}}
.w{{max-width:820px;margin:0 auto;padding-inline:16px;padding-block:32px 80px;display:flex;flex-direction:column;gap:20px}}
h1{{font-size:26px;font-weight:900;letter-spacing:-.03em;text-wrap:balance}} h1 em{{font-style:normal;color:var(--pt)}} .lead{{color:var(--sub);font-size:15px;margin-top:4px}}
.hero{{background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:16px;display:flex;flex-direction:column;gap:10px}} .hero img{{width:100%;border-radius:10px;border:1px solid var(--bd)}}
.hero p{{font-size:14px;color:var(--sub)}}
ol{{list-style:none;display:flex;flex-direction:column;gap:12px}}
li{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px 18px;display:grid;grid-template-columns:34px 1fr;gap:12px}}
li.done{{opacity:.6}} .sn{{width:30px;height:30px;border-radius:50%;background:var(--fg);color:var(--card);font-weight:900;font-size:14px;display:grid;place-items:center}}
li.done .sn{{background:var(--ok)}} .sb{{min-width:0}} h3{{font-size:17px;font-weight:900;letter-spacing:-.02em;display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
.dn{{font-size:12px;font-weight:700;color:var(--ok);border:1px solid var(--ok);border-radius:999px;padding:0 8px}}
.sb p,.sb ul{{font-size:15px;color:var(--sub);margin-top:4px}} .sb ul{{padding-left:18px}} .sb b{{color:var(--fg)}} .nt{{font-size:14px!important}}
pre.lay{{margin-top:8px;background:var(--code);border-radius:10px;padding:12px;font-size:12.5px;line-height:1.6;overflow-x:auto;font-family:ui-monospace,Menlo,monospace;color:var(--fg)}}
details{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:14px 18px}} summary{{cursor:pointer;font-weight:900}}
.cds{{display:flex;flex-direction:column;gap:10px;margin-top:12px}} .cd{{border:1px solid var(--bd);border-radius:10px;overflow:hidden}}
.ch{{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:var(--code);gap:8px}} .ch b{{font-size:14px}}
.ch button{{font:inherit;font-size:13px;font-weight:700;padding:5px 12px;border-radius:8px;border:none;background:var(--pt);color:#fff;cursor:pointer;flex:none}}
.cd pre{{font-size:12px;padding:10px 12px;white-space:pre-wrap;word-break:break-all;font-family:ui-monospace,Menlo,monospace;color:var(--sub)}}
.mc{{display:flex;gap:14px;align-items:center}} .mc img{{width:140px;border-radius:8px;border:1px solid var(--bd)}}
.bench{{font-size:14px;color:var(--sub);border-left:3px solid var(--pt);padding-left:12px}}</style>
<div class="w"><header><h1><em>박찬</em> 블로그 꾸미기 — 최종 순서표</h1><p class="lead">말씀하신 대로 덜어 냈어요. 영어 · 금색 · 무늬 · 반 이름 줄을 빼고, 학원 간판처럼 <b>파란 박찬 + 남색 통합과학학원</b> 두 색만 남겼어요. 그림은 <b>박찬_블로그꾸미기_최종.zip</b> 하나만 쓰시면 돼요.</p></header>
<div class="hero"><img src="{pv}" alt="완성 모습 PC 화면"><div class="mc"><img src="{mc}" alt="휴대폰 커버"><p>위: PC 첫 화면 완성 모습 · 왼쪽: 휴대폰 커버. 단추 5개는 번호와 이름만, 상담 단추만 남색으로 채웠어요.</p></div></div>
<ol>{''.join(S)}</ol>
<details><summary>위젯 코드 5개 (아직 등록 안 한 단추만)</summary><div class="cds">{codes}</div></details>
<p class="bench">큰 학원은 차분한 바탕에 이름 하나를 크게 세웁니다. 우리는 거기에 실제 학원 간판과 같은 두 색을 써서, 학원 앞에서 본 간판과 블로그가 같은 얼굴로 보이게 했어요.</p></div>
<script>function cp(b){{const t=b.closest('.cd').querySelector('pre').textContent;const ok=()=>{{b.textContent='복사됨';setTimeout(()=>b.textContent='코드 복사',1500)}};
try{{navigator.clipboard.writeText(t).then(ok,()=>sel(b))}}catch(e){{sel(b)}}}}
function sel(b){{const r=document.createRange();r.selectNodeContents(b.closest('.cd').querySelector('pre'));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='선택됨 · Ctrl+C'}}</script>'''
open('guide.html','w').write(H);print(len(H))
