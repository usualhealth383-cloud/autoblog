import base64,io,html
from PIL import Image
def d(p,w):
    im=Image.open(p).convert('RGB');im.thumbnail((w,9999));b=io.BytesIO();im.save(b,'JPEG',quality=85);return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
BASE='https://usualhealth383-cloud.github.io/autoblog/marketing/home-02/'
CAT='https://blog.naver.com/PostList.naver?blogId=parkchan3577&categoryNo='
BT=[(1,'학원 소개',1),(2,'반별 안내',6),(3,'강의 시간표',11),(4,'통합과학 이야기',12),(5,'상담 · 오시는 길',1)]
def code(n,t,c,v): return f'<a href="{CAT}{c}" target="_self"><img src="{BASE}btn{n}_e1.png" width="170" height="120" alt="{t}" border="0"></a>'
def codes(v):
    return ''.join(f'''<div class="cd"><div class="ch"><b>위젯 {n} · {t}</b><button onclick="cp(this)">코드 복사</button></div><pre>{html.escape(code(n,t,c,v))}</pre></div>''' for n,t,c in BT)
pa,ma=d('out/pv.png',1200),d('out/mc.png',540)
H=f'''<title>박찬 블로그 꾸미기 1안</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap">
<style>
:root{{--bg:#F4F2EC;--card:#FFFFFF;--fg:#1E2B47;--sub:#5A6377;--bd:#E4DFD3;--pt:#1F6FD1;--soft:#EEF3FB;--warn:#FFF6E5;--warnbd:#E9C98A;--code:#F7F6F2}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#7FB2FF;--soft:#1F2C47;--warn:#2E2717;--warnbd:#6B5626;--code:#161D2C;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141A28;--card:#1D2537;--fg:#E8ECF5;--sub:#A3ADC2;--bd:#2E3850;--pt:#7FB2FF;--soft:#1F2C47;--warn:#2E2717;--warnbd:#6B5626;--code:#161D2C;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:'Noto Sans KR',system-ui,sans-serif;word-break:keep-all;line-height:1.7;font-size:16px}}
.w{{max-width:860px;margin:0 auto;padding-inline:16px;padding-block:36px 80px;display:flex;flex-direction:column;gap:22px}}
h1{{font-size:28px;font-weight:900;letter-spacing:-.03em;line-height:1.35;text-wrap:balance}} h1 em{{font-style:normal;color:var(--pt)}}
.lead{{color:var(--sub);margin-top:6px}}
.sec{{background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:24px 22px;display:flex;flex-direction:column;gap:14px;min-width:0}}
.sec h2{{font-size:20px;font-weight:900;letter-spacing:-.02em;display:flex;gap:10px;align-items:center}}
.sec h2 .n{{flex:none;width:30px;height:30px;border-radius:50%;background:var(--fg);color:var(--card);font-size:15px;display:grid;place-items:center}}
.pick{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .pick figure{{min-width:0;display:flex;flex-direction:column;gap:8px}}
.pick img{{width:100%;border-radius:10px;border:1px solid var(--bd)}} figcaption{{font-size:14px;color:var(--sub)}} figcaption b{{color:var(--fg)}}
.rec{{background:var(--soft);border-radius:12px;padding:14px 16px;font-size:15px}}
ol.st{{display:flex;flex-direction:column;gap:14px;padding-left:0;list-style:none;counter-reset:s}}
ol.st>li{{counter-increment:s;display:grid;grid-template-columns:28px 1fr;gap:10px}}
ol.st>li::before{{content:counter(s);width:26px;height:26px;border-radius:8px;background:var(--soft);color:var(--pt);font-weight:900;font-size:14px;display:grid;place-items:center;margin-top:2px}}
ol.st>li>div{{min-width:0}} .path{{font-weight:700}} .path i{{font-style:normal;color:var(--sub);padding:0 4px}}
.st p,.st ul{{font-size:15px;color:var(--sub);margin-top:4px}} .st ul{{padding-left:18px}}
.warn{{background:var(--warn);border:1px solid var(--warnbd);border-radius:12px;padding:12px 16px;font-size:14.5px}}
.tabs{{display:flex;gap:8px}} .tabs button{{font:inherit;font-size:14px;font-weight:700;padding:7px 16px;border-radius:999px;border:1px solid var(--bd);background:var(--card);color:var(--sub);cursor:pointer}}
.tabs button.on{{background:var(--fg);color:var(--card);border-color:var(--fg)}}
.cd{{border:1px solid var(--bd);border-radius:12px;overflow:hidden}} .ch{{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:var(--code);gap:10px}}
.ch b{{font-size:15px}} .ch button{{font:inherit;font-size:13px;font-weight:700;padding:6px 14px;border-radius:8px;border:none;background:var(--pt);color:#fff;cursor:pointer;flex:none}}
pre{{font-size:12.5px;line-height:1.55;padding:12px 14px;white-space:pre-wrap;word-break:break-all;font-family:ui-monospace,Menlo,monospace;color:var(--sub)}}
.mob{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .mob img{{width:100%;border-radius:10px;border:1px solid var(--bd)}}
.chk li{{font-size:15px}} .src{{font-size:13px;color:var(--sub)}} .src a{{color:var(--sub)}}
.bench{{font-size:14px;color:var(--sub);border-left:3px solid var(--pt);padding-left:12px}}
@media (max-width:560px){{.pick,.mob{{grid-template-columns:1fr}} h1{{font-size:24px}}}}
</style>
<div class="w">
<header><h1><em>박찬</em> 블로그를 홈페이지처럼 — 따라 하기 순서표</h1>
<p class="lead">PC 화면 7단계와 휴대폰 화면 3단계로 나눴어요. 학부모님은 대부분 휴대폰으로 보시니 <b>휴대폰 3단계를 꼭</b> 해 주세요. 메뉴 이름은 네이버 화면에 따라 조금 다를 수 있어요.</p></header>

<section class="sec"><h2><span class="n">0</span>완성 모습 · 1안 잡지 표지</h2>
<img src="{pa}" alt="1안 PC 화면 미리보기" style="width:100%;border-radius:10px;border:1px solid var(--bd)">
<div class="rec"><b>지난 시안에서 보완한 것</b><br>· 간판 뒤에 원자 궤도와 파동을 아주 옅게 깔아 과학 학원인 게 은은하게 보여요.<br>· 한 줄 소개를 「물리 · 화학 · 생명 · 지구를 <b>원장이 직접</b> 하나로 이어 가르칩니다」로 바꿔, 통합과학이 무엇인지와 원장 직강을 한 문장에 담았어요.<br>· 금색 도장을 두 겹 테두리로 다듬었고, 전화번호는 명조 숫자로 바꿨어요.<br>· 단추를 종이 카드처럼 만들고 오른쪽 아래에 → 를 넣어 누를 수 있는 것처럼 보이게 했어요. 상담 단추만 남색으로 채웠어요.<br>· 프로필 그림도 같은 금색 도장으로 맞췄어요.</div></section>

<section class="sec"><h2><span class="n">1</span>준비물 — 보내 드린 그림 4장 (박찬_블로그꾸미기_1안.zip)</h2>
<ol class="st"><li><div><span class="path">1_타이틀</span><p>블로그 맨 위 큰 간판(966 × 300)</p></div></li>
<li><div><span class="path">2_스킨배경</span><p>화면 전체 바탕을 간판과 같은 미색으로 칠하는 띠 그림</p></div></li>
<li><div><span class="path">3_프로필</span><p>블로그 프로필 그림(금색 도장)</p></div></li>
<li><div><span class="path">4_모바일커버</span><p>휴대폰 블로그 첫 화면 커버</p></div></li></ol>
<p class="src">메뉴 단추 5개 그림은 인터넷 주소로 올려 두어서, 아래 위젯 코드만 붙여 넣으면 돼요.</p></section>

<section class="sec"><h2><span class="n">2</span>PC — 블로그 관리에서 7단계</h2>
<p class="src">PC에서 내 블로그 → 오른쪽 위 <b>관리</b> → 위쪽 탭 <b>꾸미기 설정</b>에서 시작해요.</p>
<ol class="st">
<li><div><span class="path">스킨 선택</span><p><b>베이직</b> 적용 — ✅ 하셨어요.</p></div></li>
<li><div><span class="path">레이아웃·위젯 설정 <i>›</i> 레이아웃</span><p><b>1단 레이아웃</b> — ✅ 하셨어요.</p></div></li>
<li><div><span class="path">같은 화면 <i>›</i> 위젯 끄기</span><p>서재·지도·블로그정보 빼기 — ✅ 하셨어요. 남은 카테고리·프로필영역·RSS·검색은 그대로 둬요.</p></div></li>
<li><div><span class="path">같은 화면 <i>›</i> 위젯직접등록 (5번)</span><p>오른쪽 아래 <b>위젯직접등록</b> → 위젯명에 단추 이름, 위젯코드에 아래 <b>3번 칸의 코드</b>를 붙여 넣고 <b>다음 → 등록</b>. 다섯 번 반복해요. 등록한 위젯은 목록 맨 아래에 생겨요. 회색 판에서 끌어서 <b>메뉴 형태 바로 아래, 글 영역 위</b>에 1 → 5 순서로 한 줄로 놓고 <b>적용</b>.</p></div></li>
<li><div><span class="path">세부 디자인 설정 <i>›</i> 리모콘 <i>›</i> 스킨배경 <i>›</i> 직접등록</span><p><b>2_스킨배경</b> 그림을 올리고 <b>바둑판(반복)</b>으로 채워요. 위쪽 검은 띠까지 미색으로 덮여요.</p></div></li>
<li><div><span class="path">같은 리모콘 <i>›</i> 타이틀 <i>›</i> 디자인 <i>›</i> 직접등록</span><p><b>1_타이틀</b> 그림을 올리고, 영역 높이를 <b>300</b>으로 맞춰요. <b>블로그 제목 글자는 끄기</b>(그림에 이미 이름이 있어요). 마지막에 오른쪽 아래 <b>적용</b>.</p></div></li>
<li><div><span class="path">기본 설정 <i>›</i> 블로그 정보</span><ul><li>블로그 이름: <b>박찬 통합과학 학원</b></li><li>블로그 프로필 이미지: <b>3_프로필</b></li><li>소개글: <b>대구 월성동 통합과학 전문 학원 · 상담 053-213-3577 (매일 오후 2시 ~ 10시)</b></li></ul></div></li>
</ol>
<div class="warn">프롤로그는 <b>메뉴·글 관리 › 프롤로그</b>에서 <b>이미지 강조</b>로 바꿔 주세요. 대표 그림이 크게 보여서 글자만 빽빽한 느낌이 사라져요.</div></section>

<section class="sec"><h2><span class="n">3</span>위젯 코드 5개 — 복사해서 붙여 넣기</h2>
<div style="display:flex;flex-direction:column;gap:10px">{codes('e')}</div>
<div class="warn">단추 그림은 <b>공개 주소에 올린 뒤에</b> 보여요. 올려 드린다고 알려 드리면 그때 붙여 넣어 주세요. '상담 · 오시는 길' 단추는 지금 학원 소개로 가요. 스마트플레이스 공유 주소(naver.me로 시작)를 주시면 그곳으로 바꿔 드릴게요.</div></section>

<section class="sec"><h2><span class="n">4</span>휴대폰 — 네이버 블로그 앱에서 3단계</h2>
<div class="mob"><img src="{ma}" alt="휴대폰 커버"></div>
<ol class="st">
<li><div><span class="path">내 블로그 <i>›</i> 홈편집</span><p>프로필 아래 <b>홈편집</b>을 눌러요.</p></div></li>
<li><div><span class="path">커버 스타일 <i>›</i> 커버 이미지</span><p>커버 모양 중 <b>그림이 화면 위쪽을 크게 채우는 것</b>을 고르고 <b>4_모바일커버</b>를 올려요. 아래쪽 비워 둔 자리에 블로그 이름이 얹혀요.</p></div></li>
<li><div><span class="path">소개 · 프로필</span><p>PC와 같은 소개글을 넣고 <b>적용</b>. 이름이 커버 글씨와 겹치면 화면을 찍어 보내 주세요. 바로 고쳐 드릴게요.</p></div></li>
</ol></section>

<section class="sec"><h2><span class="n">5</span>끝난 뒤 점검</h2>
<ul class="chk" style="padding-left:18px;display:flex;flex-direction:column;gap:6px">
<li>PC: 맨 위 간판 → 단추 5개 → 글 목록 순서로 보이나요?</li>
<li>단추 5개를 하나씩 눌러 맞는 카테고리로 가나요? ('반별 안내'를 누르면 중등부·고1·고3 글이 다 보이는지 꼭 확인)</li>
<li>휴대폰: 커버 그림이 잘리지 않고, 이름과 겹치지 않나요?</li>
<li>왼쪽·오른쪽에 서재·지도 같은 칸이 남아 있지 않나요?</li></ul>
<p class="bench">큰 학원들은 홈페이지형 스킨을 외주로 만들어요. 우리는 같은 틀을 직접 만들고, 간판·단추·커버·프로필·글 대표 그림을 한 색(미색 · 남색 · 금색)과 한 글꼴로 맞췄어요. 어디로 들어와도 같은 학원으로 보이는 게 차별점이에요.</p>
<p class="src">참고: <a href="https://www.qreativeuniverse.com/naver-homepage-style-blog-guide/">홈페이지형 블로그 만들기 안내</a> · <a href="https://www.i-boss.co.kr/ab-6141-23074">타이틀 966px, 위젯 가로 170px</a> · <a href="https://navercorp.com/media/pressReleasesDetail?seq=29381">네이버 모바일 홈편집 커버</a> · <a href="https://www.sdij.com">시대인재(차분한 바탕 + 강조색 하나)</a></p></section>
</div>
<script>
function tab(v,b){{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
document.getElementById('ta').hidden=v!=='a';document.getElementById('tb').hidden=v!=='b';document.getElementById('t'+v).style.display='flex';}}
function cp(b){{const t=b.closest('.cd').querySelector('pre').textContent;const ok=()=>{{b.textContent='복사됨';setTimeout(()=>b.textContent='코드 복사',1500)}};
try{{navigator.clipboard.writeText(t).then(ok,()=>sel(b))}}catch(e){{sel(b)}}}}
function sel(b){{const r=document.createRange();r.selectNodeContents(b.closest('.cd').querySelector('pre'));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='선택됨 · Ctrl+C'}}
</script>'''
open('guide.html','w').write(H);print(len(H))
