#!/usr/bin/env python3
"""약지도 통합 검사 — 한 번 돌리면 화면 전부를 실제 브라우저로 훑는다.

사용:  python3 yakjido/tests/run.py            (docs/yakjido 를 임시 서버로 띄워서 검사)
       python3 yakjido/tests/run.py --url http://localhost:8765/index.html

무엇을 보나
  1. 모든 화면(증상 52·약 102·분류·병용·종류·팁·내 정보·온보딩)에서 JS 오류 0
  2. 가로 넘침 0 (details 가 닫힌 본문과 가로 스크롤 영역은 제외)
  3. 글자 잘림 0 (scrollWidth > clientWidth 인 말단 요소)
  4. 명암비 — 밝은/어두운 테마 모두 WCAG AA (본문 4.5, 큰 글씨 3.0)
  5. 탭 타깃 44px 미만 0 (문장 속 인라인 링크는 WCAG 2.5.8 예외)
  5b. 어르신 모드(글자 20px) 16화면에서 넘침·잘림 0
  5c. 좁은 화면(320px) × 20px 글씨 17화면에서 넘침·잘림 0
  6.  병용 판정 시나리오 8건 (삼중고·와파린·전립선·치매약+방광약·혈압약 모름·안압·천식·스테로이드)
  6a. 병명이 아니라 «드시는 약»으로 걸려야 할 규칙 4건
  6b. 한 통이 자기 자신과 겹쳤다고 세지 않는지 3건
  6c. 우리가 권하는 바구니가 스스로 겹치지 않는지 (증상 56개 전수)
  7.  항콜린 이중 계산 0 (식약처 2.4만 제품 전수)
  8. 이름 검색 8건 · 구어 12건 · 문장 16건 (베시케어·하루날디·타이레놀·TY 500 …)
  8c. 구어·띄어쓰기 오타 12건 (「타이 레놀」·「머리아파」·「소화제」 — 어르신이 실제로 치는 말)
  9. 홈 날씨 카드 — Open-Meteo 응답을 모의로 넣어 일교차·미세먼지 문구가 뜨는지

Playwright 와 Chromium 이 필요하다. 실패는 마지막에 모아서 보여 주고 종료 코드 1.
"""
import argparse, http.server, json, os, socketserver, sys, threading, pathlib, functools

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs' / 'yakjido'
CHROME = os.environ.get('CHROME', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass          # 접속 기록으로 결과를 가리지 않는다

def serve():
    handler = functools.partial(_Quiet, directory=str(DOCS))
    srv = socketserver.TCPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{srv.server_address[1]}/index.html'

OVERFLOW_JS = """()=>{const sw=document.documentElement.clientWidth;const ov=[],clip=[];
 for(const e of document.querySelectorAll('#view *')){
   if(e.closest('details:not([open]) .bd')||e.closest('.scroll-x,.tabs,.quick,.today-row,.pill-grid'))continue;
   const b=e.getBoundingClientRect(); if(b.width&&(b.right>sw+1||b.left<-1))ov.push(e.tagName+'.'+e.className);
   if(e.scrollWidth>e.clientWidth+2&&getComputedStyle(e).overflowX==='visible'&&e.children.length===0&&e.textContent.trim())clip.push(e.tagName+'|'+e.textContent.trim().slice(0,20));}
 return {ov:ov.slice(0,3),clip:clip.slice(0,3),len:(document.getElementById('view')||{}).innerText.length||0};}"""

CONTRAST_JS = """()=>{
 const lum=c=>{const [r,g,b]=c.match(/\\d+(\\.\\d+)?/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*r+.7152*g+.0722*b};
 const bg=e=>{while(e){const c=getComputedStyle(e).backgroundColor;if(c&&!/rgba\\(0, 0, 0, 0\\)|transparent/.test(c))return c;e=e.parentElement}return 'rgb(255,255,255)'};
 const out=[];
 for(const e of document.querySelectorAll('#view *')){
   if(e.closest('details:not([open]) .bd'))continue;
   const t=[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent.trim()).join('');if(!t)continue;
   const st=getComputedStyle(e);if(st.visibility==='hidden'||st.display==='none'||+st.opacity===0)continue;
   const L1=lum(st.color),L2=lum(bg(e));const r=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
   const size=parseFloat(st.fontSize),bold=parseInt(st.fontWeight)>=700;const need=(size>=24||(size>=18.66&&bold))?3:4.5;
   if(r<need)out.push({t:t.slice(0,24),r:+r.toFixed(2),need,cls:(''+e.className).slice(0,18)});}
 return out;}"""

# 글자 말고 «조작 부품»의 대비 — WCAG 1.4.11(3:1).
# 스위치가 꺼져 있을 때 막대가 안 보였고(1.29:1), 나이 고르는 칸은 고른 쪽이
# 흰 조각뿐이라 어느 쪽인지 알기 어려웠다(1.13:1). 어르신 앱에서는 특히 문제다.
UICON_JS = """()=>{
 const lum=c=>{const m=c.match(/\\d+(\\.\\d+)?/g);if(!m)return 1;const [r,g,b]=m.slice(0,3).map(Number).map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*r+.7152*g+.0722*b};
 const bg=e=>{while(e){const c=getComputedStyle(e).backgroundColor;if(c&&!/rgba\\(0, 0, 0, 0\\)|transparent/.test(c))return c;e=e.parentElement}return 'rgb(255,255,255)'};
 const cr=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
 const out=[];
 for(const e of document.querySelectorAll('button.sw, .seg button.on')){
   const st=getComputedStyle(e);
   const who=e.classList.contains('sw')?'스위치':'고른 칸';
   const ps=getComputedStyle(e,'::before');
   const bw=parseFloat(st.borderTopWidth)||0, pw=parseFloat(ps.borderTopWidth)||0;
   const cand=[ps.backgroundColor, ps.boxShadow, st.boxShadow, bw?st.borderTopColor:'', pw?ps.borderTopColor:'', st.backgroundColor].join(' ');
   const cols=[...cand.matchAll(/rgba?\\([^)]+\\)/g)].map(m=>m[0]).filter(c=>!/, 0\\)$/.test(c));
   const base=bg(e.parentElement);
   const best=cols.reduce((a,c)=>Math.max(a,cr(c,base)),0);
   if(best<3)out.push(who+' '+best.toFixed(2)+':1');}
 return [...new Set(out)];}"""

# 약 알림이 실제로 만들어지는지.
# 화면에는 「알림 켜짐」이라고 떠 있는데, 시간이 돼도 알림이 안 왔다. 타이머 안에서
# 없는 변수(id)를 써서 터지고 있었고, try/catch 가 그것을 조용히 삼키고 있었다.
NOTI_JS = """()=>{
  const fired=[], errs=[];
  const RT=window.setTimeout, RN=window.Notification;
  window.setTimeout=(fn)=>{ try{ fn(); }catch(e){ errs.push(''+e); } return 0; };
  const F=function(t,o){ fired.push(t+'|'+((o&&o.tag)||'')); };
  F.permission='granted'; window.Notification=F;
  try{
    ME.taking=['ibuprofen'];
    ME.sched={ibuprofen:['23:59']};
    armNotifications();
  }catch(e){ errs.push('armNotifications: '+e); }
  finally{ window.setTimeout=RT; window.Notification=RN; }
  return {fired, errs};
}"""

TAP_JS = """()=>[...document.querySelectorAll('#view button,#view a')].filter(e=>!((e.matches('a.link')||e.matches('a.call-in'))&&e.closest('p,span,li,div'))).map(e=>{const b=e.getBoundingClientRect();return b.height>0&&b.height<44?((e.innerText||e.className)+'').slice(0,20)+':'+Math.round(b.height):null}).filter(Boolean)"""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--url'); a = ap.parse_args()
    # 0. 자료 고리(브라우저 없이 1초) — 끊긴 출처·약 id·팁 링크가 있으면 여기서 멈춘다
    import subprocess
    r0 = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name('data.py'))], capture_output=True, text=True)
    print(r0.stdout.strip())
    if r0.returncode: sys.exit(1)
    url = a.url or serve()
    from playwright.sync_api import sync_playwright
    fails = []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME)
        pg = br.new_page(viewport={'width': 390, 'height': 844})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
        # 날씨는 바깥 서비스라 모의 응답으로 — 홈이 '데이터 있는 상태'로 검사된다(일교차 큼·미세먼지 나쁨)
        FC = json.dumps({"current": {"temperature_2m": 19.4, "apparent_temperature": 18.1, "relative_humidity_2m": 31, "weather_code": 1}, "daily": {"temperature_2m_max": [27.8], "temperature_2m_min": [14.2]}})
        AQ = json.dumps({"current": {"pm10": 92.0, "pm2_5": 41.0}})
        pg.route('**/api.open-meteo.com/**', lambda rt: rt.fulfill(status=200, content_type='application/json', body=FC))
        pg.route('**/air-quality-api.open-meteo.com/**', lambda rt: rt.fulfill(status=200, content_type='application/json', body=AQ))
        def ready(ms=8000):
            # 본문 자료(data/core.json)는 첫 화면이 뜬 뒤에 받는다 — 다 받을 때까지 기다린다
            try: pg.wait_for_function('window.__READY__===true', timeout=ms)
            except Exception: fails.append('본문 자료(core.json)를 못 받았습니다 — ' + pg.url)
        pg.goto(url); ready(); pg.wait_for_timeout(1200)
        pg.evaluate("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',taking:['cls:bp.arb'],pub:{}}))")
        routes = pg.evaluate("()=>['/home','/drugs','/tips','/me','/together','/kinds','/kinds/bp','/pill','/supp','/kids','/mix','/hello/1','/hello/3','/photo','/schedule','/about','/bag','/rxout','/senior','/myths']" +
                             ".concat(D.symptoms.map(s=>'/symptom/'+s.id)).concat(D.drugs.map(d=>'/drug/'+d.id)).concat(D.classes.map(c=>'/class/'+c.id)).concat(D.classes.map(c=>'/drugs?cat='+c.id)).concat((D.myths||[]).map(m=>'/myths?open='+m.id))")
        # 1~3. 모든 화면
        for r in routes:
            pg.goto(url + '#' + r); pg.wait_for_timeout(350)
            o = pg.evaluate(OVERFLOW_JS)
            if o['ov']: fails.append(f'가로 넘침 {r}: {o["ov"]}')
            if o['clip']: fails.append(f'글자 잘림 {r}: {o["clip"]}')
            if o['len'] < 40: fails.append(f'빈 화면 {r}')
            # 1b. 굵게 표시(**)가 글자 그대로 보이면 안 된다 — esc() 로 그린 칸을 잡아낸다.
            #     약의 «간단히» 한 줄 7곳이 실제로 그랬다.
            md = pg.evaluate("()=>{const t=(document.getElementById('app')||document.body).innerText;const m=t.match(/\\*\\*[^*\\n]{1,40}\\*\\*/g);return m?m.slice(0,2):[]}")
            if md: fails.append(f'굵게 표시가 글자로 보임 {r}: {md}')
        if errs: fails.append(f'JS 오류 {len(errs)}: {errs[:3]}')
        # 4~5. 명암비·탭 타깃 (대표 화면, 두 테마)
        SC = ['/home', '/symptom/cold', '/symptom/drymouth', '/drug/ibuprofen', '/me', '/together', '/kinds', '/tips', '/drugs', '/hello/3']
        for theme in ['light', 'dark']:
            pg.emulate_media(color_scheme=theme); bad = []; tap = []
            for r in SC:
                pg.goto(url + '#' + r); pg.wait_for_timeout(500)
                bad += pg.evaluate(CONTRAST_JS); tap += pg.evaluate(TAP_JS)
                for u in pg.evaluate(UICON_JS): fails.append(f'조작 부품 대비({theme}) {r}: {u} — 3:1 이 필요합니다')
            if bad: fails.append(f'명암비({theme}) {len(bad)}: {bad[:3]}')
            if tap: fails.append(f'44px 미만({theme}) {len(tap)}: {sorted(set(tap))[:5]}')
        pg.emulate_media(color_scheme='light')
        # 5a-1. 단추를 전부 눌러 본다 — 화면만 그려 보는 검사로는 «눌렀을 때 터지는 것»을 못 잡는다.
        #        되돌리기 어려운 단추(삭제·내보내기·인쇄·공유)는 건드리지 않는다.
        _CLICK = ['/home', '/kinds', '/supp', '/tips', '/myths', '/me', '/schedule',
                  '/symptom/msk', '/symptom/gout', '/symptom/cold', '/drug/acetaminophen', '/supp/mg', '/kids']
        pg.on('dialog', lambda d: d.dismiss())
        for r in _CLICK:
            pg.goto(url + '#' + r); ready(); pg.wait_for_timeout(250)
            n = pg.evaluate("()=>document.querySelectorAll('#view button, #view summary').length")
            for i in range(min(n, 40)):
                errs.clear()
                pg.evaluate("""(i)=>{const e=document.querySelectorAll('#view button, #view summary')[i];
                   if(!e) return; if(/삭제|지우|초기화|비우|내보내|다운|인쇄|공유|보내기/.test((e.innerText||'').trim())) return; e.click();}""", i)
                pg.wait_for_timeout(45)
                if errs: fails.append(f'단추를 누르니 터집니다 {r} [{i}]: {errs[0][:110]}')
                if pg.evaluate("()=>location.hash") != '#' + r:
                    pg.goto(url + '#' + r); ready(); pg.wait_for_timeout(120)
        errs.clear()

        # 5a. 약 알림 — 시간이 돼도 안 오던 것(타이머 안에서 조용히 터지고 있었다)
        pg.goto(url + '#/schedule'); ready(); pg.wait_for_timeout(300)
        _n = pg.evaluate(NOTI_JS)
        if _n['errs']: fails.append(f'약 알림이 터집니다: {_n["errs"][:2]}')
        if not _n['fired']: fails.append('약 알림이 하나도 만들어지지 않습니다 — 시간이 돼도 안 옵니다')
        # 5b. 어르신 모드(글자 20px·큰 단추) — 넘침·잘림은 큰 글씨에서 먼저 터진다
        pg.evaluate("localStorage.setItem('yakjido.fs','20px');localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',easy:true,taking:['cls:bp.arb','ibuprofen'],pub:{}}))")
        for r in SC + ['/bag', '/schedule', '/symptom/cramp', '/symptom/sprain', '/drug/acetaminophen', '/kinds/bp']:
            pg.goto(url + '#' + r); pg.reload(); ready(); pg.wait_for_timeout(500)
            o = pg.evaluate(OVERFLOW_JS)
            if o['ov']: fails.append(f'어르신 모드 가로 넘침 {r}: {o["ov"]}')
            if o['clip']: fails.append(f'어르신 모드 글자 잘림 {r}: {o["clip"]}')
        # 5c. 좁은 화면(320px) × 가장 큰 글씨 — 오래된 안드로이드 폰과 «화면 확대»를 켜신 분의 자리.
        #     낱알 검색칸과 소아 화면 단추가 실제로 화면을 넘고 있었다.
        pg.set_viewport_size({'width': 320, 'height': 640})
        for r in SC + ['/pill', '/kids', '/kinds', '/bag', '/schedule', '/symptom/fever', '/symptom/motion']:
            pg.goto(url + '#' + r); pg.reload(); ready(); pg.wait_for_timeout(420)
            o = pg.evaluate(OVERFLOW_JS)
            if o['ov']: fails.append(f'좁은 화면 가로 넘침 {r}: {o["ov"][:2]}')
            if o['clip']: fails.append(f'좁은 화면 글자 잘림 {r}: {o["clip"][:2]}')
        pg.set_viewport_size({'width': 390, 'height': 844})
        pg.evaluate("localStorage.setItem('yakjido.fs','16px')")
        # 6. 병용 판정 시나리오 (이름 없이 종류로)
        CASES = [(['bp.arb', 'bp.diur'], '/symptom/arthritis', '콩팥'), (['blood.warf'], '/symptom/msk', '와파린'),
                 (['pros.alpha'], '/symptom/cold', '전립선'), (['dem.ache', 'blad.oab'], '/together', '치매약'), (['bp.any'], '/symptom/arthritis', '혈압약')]
        CASES += [(['eye.glau'], '/symptom/cold', '안압'), (['resp.luka'], '/symptom/msk', '천식'),
                  (['ster.pred'], '/symptom/msk', '스테로이드')]
        for picks, r, kw in CASES:
            pg.evaluate("(p)=>localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',taking:p.map(x=>'cls:'+x),pub:{}}))", picks)
            pg.goto(url + '#' + r); pg.reload(); ready(); pg.wait_for_timeout(700)
            txt = pg.evaluate("()=>[...document.querySelectorAll('.ixline,.ix-h b')].map(x=>x.innerText).join(' | ')")
            if kw not in txt: fails.append(f'병용 시나리오 {picks} → "{kw}" 없음: {txt[:80]}')
        # 5d. 입력칸에는 이름표가 있어야 한다 — 자리표시 글자만으로는 화면낭독기가 못 읽는다.
        #     모든 화면 위에 떠 있는 검색칸이 그 상태였다.
        nolab = []
        for r in SC + ['/pill', '/me', '/supp/vitd', '/kids', '/about']:
            pg.goto(url + '#' + r); pg.wait_for_timeout(320)
            nolab += [f'{r}:{x}' for x in pg.evaluate("()=>[...document.querySelectorAll('#view input,#view select,#view textarea')].filter(e=>e.type!=='hidden'&&!e.getAttribute('aria-label')&&!(e.labels&&e.labels.length)).map(e=>e.id||e.name||e.placeholder||e.tagName)")]
        if nolab: fails.append(f'이름표 없는 입력칸 {len(nolab)}: {nolab[:4]}')
        # 6-0. 약 123개가 «성분»으로 풀려야 한다. 안 풀리면 그 약은 병용 판정·항콜린 계산에서
        #      통째로 빠진다 — 실제로 33개가 그 상태였고 화면에는 아무 표시가 없었다.
        nores = pg.evaluate("()=>(D.drugs||[]).filter(d=>!ingOf({d}).ings.length).map(d=>d.id)")
        if nores: fails.append(f'성분으로 안 풀리는 약 {len(nores)}개: {nores[:6]}')
        # 6-0b. 규칙이 쓰는 계열 태그는 «어떤 성분이나 약 종류»에든 있어야 한다. 없으면 죽은 규칙이다.
        dead = pg.evaluate("()=>{const tags=new Set();for(const e of (D.ingredients?.ing||[])) for(const c of (e.cls||[])) tags.add(c);for(const g of (D.ingredients?.quick||[])) for(const s of (g.subs||[])) for(const c of (s.cls||[])) tags.add(c);const out=[];for(const r of (D.interactions?.rules||[])){const used=[];for(const grp of (r.need||[])) for(const t of grp) if(!String(t).startsWith('k:')) used.push(t);if(r.count) used.push(r.count.tag);const miss=used.filter(t=>!tags.has(t));if(miss.length) out.push(r.id+':'+miss.join(','));}return out;}")
        if dead: fails.append(f'어떤 성분에도 없는 태그를 쓰는 규칙(죽은 규칙): {dead}')
        # 6a. 병명 대신 «드시는 약»으로도 걸려야 한다 — 어르신은 «녹내장»·«천식»이라는 말보다 «넣는 안약»을 아신다.
        #     전에는 이 경고들이 내 정보의 병명 체크에만 달려 있어, 약통만 채운 분께는 아예 뜨지 않았다.
        MEDCASE = [(['cls:bp.arb', 'coldaewon'], 'decongest-bp'), (['cls:eye.glau', 'dimenhydrinate'], 'anticho-glaucoma-med'),
                   (['cls:resp.luka', 'ibuprofen'], 'nsaid-asthma-med'), (['cls:ster.pred', 'ibuprofen'], 'steroid-nsaid')]
        for taking, rid in MEDCASE:
            pg.evaluate("(t)=>localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',taking:t,pub:{}}))", taking)
            pg.goto(url + '#/together'); pg.reload(); ready(); pg.wait_for_timeout(600)
            ids = pg.evaluate("()=>ixRun().hits.map(h=>h.r.id)")
            if rid not in ids: fails.append(f'약통으로 걸려야 할 규칙이 안 뜸 {taking} → {rid} (뜬 것: {ids})')
        # 6b. 한 통이 «자기 자신과» 겹쳤다고 세면 안 된다 — 복합제는 약 이름과 속 성분이 둘 다 잡힌다.
        #     신신플렉스(클로르족사존+에텐자미드) 한 통만 들고 있을 때 '졸음이 겹쳤다'가 뜨면 버그다.
        SELF = [(['relax-combo'], 'sed-load'), (['cold-combo'], 'sed-load'), (['antihist-1g'], 'ach-load')]
        for picks, rid in SELF:
            pg.evaluate("(p)=>localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',taking:p,pub:{}}))", picks)
            pg.goto(url + '#/together'); pg.reload(); ready(); pg.wait_for_timeout(700)
            ids = pg.evaluate("()=>ixRun().hits.map(h=>h.r.id)")
            if rid in ids: fails.append(f'한 통이 자기 자신과 겹침 {picks} → {rid} 떴음')
        # 6c. 우리가 권하는 바구니가 «스스로» 겹치지 않는지 — 약통을 등록하지 않은 분께도 보여야 한다.
        #     감기 화면이 타이레놀과 콜대원(아세트아미노펜 함유)을 나란히 권하던 것을 이 검사가 잡는다.
        pg.evaluate("()=>localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',taking:[],pub:{}}))")
        pg.goto(url + '#/home'); pg.reload(); ready(); pg.wait_for_timeout(700)
        pdup = pg.evaluate("()=>Object.fromEntries((D.symptoms||[]).map(s=>[s.id,planDup(basket(s))]).filter(x=>x[1].length))")
        KNOWN = {'msk', 'headache', 'arthritis'}      # 에텐자미드(근이완 복합제) — 본문에 설명을 달아 둔 자리
        for sid, msgs in pdup.items():
            if sid not in KNOWN: fails.append(f'추천 바구니가 스스로 겹침 {sid}: {msgs[0][:70]}')
            elif '소염' not in msgs[0]: fails.append(f'{sid} 겹침 내용이 바뀜: {msgs[0][:70]}')
        for sid in KNOWN:
            if sid not in pdup: fails.append(f'{sid} 소염 성분 겹침 경고가 사라짐 — 규칙이 죽었는지 확인')
        # 9. 날씨 카드
        pg.goto(url + '#/home'); pg.reload(); ready(); pg.wait_for_timeout(1000)
        wx = pg.evaluate("()=>document.querySelector('.wx')?.innerText||''")
        for kw in ['일교차', '14℃', '미세먼지', '나쁨']:
            if kw not in wx: fails.append(f'날씨 카드에 "{kw}" 없음: {wx[:80]!r}')
        # 9b. 날씨를 못 받는 곳(아티팩트·오프라인)에서 요청이 반복되지 않는지 — 예전에 4초 170번 돌았다
        pg.unroute('**/api.open-meteo.com/**'); pg.unroute('**/air-quality-api.open-meteo.com/**')
        cnt = [0]
        pg.route('**/*open-meteo.com/**', lambda rt: (cnt.__setitem__(0, cnt[0] + 1), rt.abort()))
        pg.evaluate("localStorage.removeItem('yakjido.wx.v1')"); pg.goto(url + '#/home'); pg.reload(); ready(); pg.wait_for_timeout(3000)
        if cnt[0] > 6: fails.append(f'날씨 실패 시 요청 반복 {cnt[0]}회/3초 (6회 이하여야)')
        wx = pg.evaluate("()=>document.querySelector('.wx')?.innerText||''")
        if '못 받았어요' not in wx: fails.append(f'날씨 실패 문구 없음: {wx[:60]!r}')
        pg.unroute('**/*open-meteo.com/**')
        pg.route('**/api.open-meteo.com/**', lambda rt: rt.fulfill(status=200, content_type='application/json', body=FC))
        pg.route('**/air-quality-api.open-meteo.com/**', lambda rt: rt.fulfill(status=200, content_type='application/json', body=AQ))
        # 10. 소아 용량 계산 — 아세트아미노펜 10~15 mg/kg(하루 75, 두 돌 전 60), 이부프로펜 5~10 mg/kg(하루 40), 상한
        #     15 kg 이부프로펜의 하루 500 mg 은 허가사항의 '30 kg 미만 하루 500 mg' 한도가 걸린 값이다(몸무게로만 곱하면 600).
        kd = pg.evaluate("()=>[[15,36],[8,5],[40,150],[10,20]].map(([w,m])=>['apap','ibu'].map(k=>{const r=kidDose(k,w,m);return [r.lo,r.hi,r.day]}))")
        want = [[[150, 225, 1125], [75, 150, 500]], [[80, 120, 480], [40, 80, 320]], [[400, 600, 3000], [200, 400, 1600]], [[100, 150, 600], [50, 100, 400]]]
        if kd != want: fails.append(f'소아 용량 계산 불일치: {kd} ≠ {want}')
        # 10b. 몸무게로 걸린 허가 한도 — 부루펜 30 kg 미만 하루 500 mg, 맥시부펜 30 kg 이하 하루 300 mg
        kc = pg.evaluate("()=>[['ibu',29],['ibu',30],['dexibu',30],['dexibu',31]].map(([k,w])=>{const r=kidDose(k,w,48);return [r.day, !!r.kidCap]})")
        wantc = [[500, True], [1200, False], [300, True], [868, False]]
        if kc != wantc: fails.append(f'소아 몸무게 한도 불일치: {kc} ≠ {wantc}')
        # 7. 항콜린 이중 계산 · 8. 이름 검색
        r7 = pg.evaluate("""async()=>{ await pubPills(); await pubPillsRx(); let n=0;
          for(const p of (PUB.rx||[]).concat(PUB.pills||[])){ if(ingFind((p.ingr||'')+' '+(p.n||'')).filter(e=>e.ach).length>1) n++; } return n; }""")
        if r7: fails.append(f'항콜린 이중 계산 제품 {r7}건')
        Q = {'베시케어': '베시케어', '하루날디': '하루날디', '타이레놀': '타이레놀', 'TY 500': '타이레놀', '크레스토': '크레스토', '플라빅스': '플라빅스', '베시케어 5mg': '베시케어', '트윈스타': '트윈스타'}
        r8 = pg.evaluate("(Q)=>Object.fromEntries(Object.keys(Q).map(q=>[q,(pillSearch({txt:q,sh:'',c:'',ln:''},true)[0]||[0,{n:''}])[1].n]))", Q)
        for q, want in Q.items():
            if want not in r8.get(q, ''): fails.append(f'검색 "{q}" → {r8.get(q)!r} (기대: {want})')
        # 8b. 통합 검색 순위 — 제품 이름은 제품이, 증상 이름은 증상이 먼저(사전 로드 뒤)
        r8b = pg.evaluate("async()=>{ await lexLoad(true); return Object.fromEntries(['인사돌','타이레놀','감기','변비','오메가3'].map(q=>[q,(search(q)[0]||{}).k])); }")
        for q, want in {'인사돌': '제품', '타이레놀': '제품', '감기': '증상', '변비': '증상', '오메가3': '영양제'}.items():
            if r8b.get(q) != want: fails.append(f'검색 순위 "{q}" 첫 결과 {r8b.get(q)!r} (기대: {want})')
        # 8c. 어르신이 실제로 치는 말 — 띄어쓰기 오타와 구어. 하나라도 0건이면 검색이 죽은 것이다
        SAY = ['타이 레놀', '이부 프로펜', '머리아파', '배아파', '목아파', '잠이안와', '소화제', '감기약', '무좀약', '변비약', '어지러워', '속쓰려']
        r8c = pg.evaluate("(L)=>Object.fromEntries(L.map(q=>[q,search(q).length]))", SAY)
        zero = [q for q, n in r8c.items() if not n]
        if zero: fails.append(f'구어 검색 0건: {zero}')
        # 8d. 문장으로 치시는 분 — 「어깨 아파」·「아이 해열제」·「변비가 있어요」가 전부 0건이었다.
        #     결과 «개수»만이 아니라 «맨 위에 무엇이 오는지»까지 본다.
        SAY2 = {'목이 아파요': '인후통', '어깨 아파': '어깨', '무릎 통증': '관절', '벌레 물림': '벌레',
                '아이 해열제': '열', '변비가 있어요': '변비', '입이 말라요': '마름', '귀가 먹먹해요': '귀',
                '다리에 쥐가 나요': '쥐', '잠이 안 와요': '잠', '손발이 저려요': '저리', '이가 아파요': '치통',
                '발목을 삐었어요': '삠', '눈이 뻑뻑해요': '눈', '소변이 잘 안 나와요': '소변', '기침이 나요': '기침'}
        r8d = pg.evaluate("async(Q)=>{ await lexLoad(true); return Object.fromEntries(Object.keys(Q).map(q=>[q,(search(q)[0]||{t:''}).t])); }", SAY2)
        for q, want in SAY2.items():
            if want not in (r8d.get(q) or ''): fails.append(f'문장 검색 "{q}" 첫 결과 {r8d.get(q)!r} (기대: {want} 포함)')
        br.close()
    print(f'화면 {len(routes)}개 검사 완료')
    if fails:
        print('실패', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
    print('✓ 전부 통과 — JS 오류 0 · 넘침 0 · 잘림 0 · 명암비 AA · 조작 부품 3:1 · 44px · 단추 누르기 · 약 알림 · 어르신 모드 · 320px · 병용 8건 · 입력칸 이름표 · 성분 해석 123 · 죽은 규칙 0 · 약통 판정 4건 · 자기중복 3건 · 바구니 겹침 · 이중계산 0 · 검색 8건 · 구어 12건 · 문장 16건')

if __name__ == '__main__':
    main()
