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
  5b. 어르신 모드(글자 22px — 가장 큰 단계) 16화면에서 넘침·잘림 0
  5c. 좁은 화면(320px) × 22px 글씨 17화면에서 넘침·잘림 0
  6.  병용 판정 시나리오 8건 (삼중고·와파린·전립선·치매약+방광약·혈압약 모름·안압·천식·스테로이드)
  6a. 병명이 아니라 «드시는 약»으로 걸려야 할 규칙 4건
  6b. 한 통이 자기 자신과 겹쳤다고 세지 않는지 3건
  6c. 우리가 권하는 바구니가 스스로 겹치지 않는지 (증상 56개 전수)
  7.  항콜린 이중 계산 0 (식약처 2.4만 제품 전수)
  8. 이름 검색 8건 · 구어 30건 · 문장 16건 (베시케어·하루날디·타이레놀·TY 500 …)
  8c. 구어·띄어쓰기·처방약 이름 30건 (「타이 레놀」·「머리아파」·「소화제」 — 어르신이 실제로 치는 말)
  9. 홈 날씨 카드 — Open-Meteo 응답을 모의로 넣어 일교차·미세먼지 문구가 뜨는지

Playwright 와 Chromium 이 필요하다. 실패는 마지막에 모아서 보여 주고 종료 코드 1.
"""
import argparse, http.server, json, os, socketserver, sys, threading, pathlib, functools

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs' / 'yakjido'
CHROME = os.environ.get('CHROME', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
# 제작PC 등 다른 컴퓨터: 그 경로가 없으면 Playwright 기본 브라우저(`python -m playwright install chromium`)를 쓴다
if not os.path.exists(CHROME): CHROME = None
LAUNCH = {'executable_path': CHROME} if CHROME else {}

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass          # 접속 기록으로 결과를 가리지 않는다

def serve():
    handler = functools.partial(_Quiet, directory=str(DOCS))
    srv = socketserver.TCPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{srv.server_address[1]}/index.html'

OVERFLOW_JS = """()=>{const sw=document.documentElement.clientWidth;const ov=[],clip=[];
 for(const e of document.querySelectorAll('#view *')){
   if(e.closest('details:not([open]) .bd')||e.closest('.scroll-x,.tabs,.quick,.today-row,.pill-grid,.gjump'))continue;
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
 /* 아이콘도 본다 — 이 앱에서 아이콘은 장식이 아니라 «무슨 증상인지»를 말하는 그림이다 */
 for(const sv of document.querySelectorAll('#view svg.i')){
   const r=cr(getComputedStyle(sv).color, bg(sv.parentElement));
   if(r<3) out.push('아이콘('+((sv.parentElement.className+'')||'').slice(0,14)+') '+r.toFixed(2)+':1');}
 return [...new Set(out)];}"""

# 약 알림이 실제로 만들어지는지.
# 화면에는 「알림 켜짐」이라고 떠 있는데, 시간이 돼도 알림이 안 왔다. 타이머 안에서
# 없는 변수(id)를 써서 터지고 있었고, try/catch 가 그것을 조용히 삼키고 있었다.
# 설치한 안드로이드 앱(Capacitor) 흉내 — 휴대폰 알람 장치를 가짜로 두고, 앱이 무엇을 거는지 본다
CAP_MOCK = """
window.__LN = {pending:[], listeners:{}, perm:'granted', exact:'denied', types:null};
window.Capacitor = { isNativePlatform: () => true, Plugins: {
  LocalNotifications: {
    createChannel: async () => {}, registerActionTypes: async o => { __LN.types = o; },
    addListener: (n, f) => { __LN.listeners[n] = f; return { remove(){} }; },
    checkPermissions: async () => ({ display: __LN.perm }), requestPermissions: async () => ({ display: __LN.perm }),
    checkExactNotificationSetting: async () => ({ exact_alarm: __LN.exact }),
    changeExactNotificationSetting: async () => ({ exact_alarm: (__LN.exact = 'granted') }),
    getPending: async () => ({ notifications: __LN.pending.slice() }),
    cancel: async o => { const ids = o.notifications.map(x => x.id); __LN.pending = __LN.pending.filter(p => !ids.includes(p.id)); },
    schedule: async o => { for (const n of o.notifications) { __LN.pending = __LN.pending.filter(p => p.id !== n.id); __LN.pending.push(JSON.parse(JSON.stringify(n))); } return { notifications: o.notifications.map(n => ({ id: n.id })) }; }
  },
  App: { addListener: () => ({ remove(){} }), exitApp(){} },
  StatusBar: { setStyle(){}, setBackgroundColor(){} }, SplashScreen: { hide(){} }
} };
"""

NOTI_JS = """()=>{
  const fired=[], errs=[];
  const RT=window.setTimeout, RN=window.Notification;
  window.setTimeout=(fn)=>{ try{ fn(); }catch(e){ errs.push(''+e); } return 0; };
  const F=function(t,o){ fired.push(t+'|'+((o&&o.tag)||'')); };
  F.permission='granted'; window.Notification=F;
  /* 2026-09-23 — 알림은 이제 showNote(서비스워커)로 띄운다. 그 입구를 가로채 센다 */
  const RS=window.showNote; window.showNote=(t,b,k)=>{ fired.push(t+'|'+k); };
  try{
    ME.taking=['ibuprofen'];
    ME.sched={ibuprofen:['23:59']};
    armNotifications();
  }catch(e){ errs.push('armNotifications: '+e); }
  finally{ window.setTimeout=RT; window.Notification=RN; window.showNote=RS; }
  return {fired, errs};
}"""

# 겹침 규칙 52개가 «실제로» 뜨는지 전수로 본다.
# 자료가 이어져 있는지(죽은 규칙)만 보던 것으로는 부족했다 — 아세트아미노펜 중복 규칙은
# 고리가 멀쩡한데도 세는 방식 때문에 한 번도 뜨지 않았고, 리튬·디곡신·메트로니다졸은
# 사용자가 그 약을 담을 길 자체가 없어 영영 뜰 수 없었다(2026-09-22).
RULES_JS = """()=>{
  const rules=(D.interactions&&D.interactions.rules)||[];
  const cands=[];
  for(const d of (D.drugs||[])) cands.push(d.id);
  for(const g of (D.ingredients.quick||[])) for(const x of (g.subs||[])) cands.push('cls:'+x.id);
  const info={};
  for(const id of cands){ ME.taking=[id]; ME.pub={};
    const c=new Set(), k=new Set();
    ixItems([]).forEach(it=>it.ings.forEach(e=>{(e.cls||[]).forEach(x=>c.add(x)); if(e.k)k.add(e.k);}));
    info[id]={c,k}; }
  const hit=(id,g)=>g.some(t=>t.startsWith('k:')?info[id].k.has(t.slice(2)):info[id].c.has(t));
  const F=['heart','diabetes','ulcer','kidney','liver','anticoag','glaucoma','bph','asthma','alcohol','gout','pregnant','senior'];
  const bad=[];
  for(const r of rules){
    let pick=[],ok=true;
    if(r.count){ const c=cands.filter(id=>info[id].c.has(r.count.tag));
      if(c.length<r.count.n) ok=false; else pick=c.slice(0,r.count.n); }
    else { const used=new Set();
      for(const g of (r.need||[])){ const id=cands.find(x=>!used.has(x)&&hit(x,g)); if(!id){ok=false;break;} used.add(id); pick.push(id); } }
    if(!ok){ bad.push(r.id+' — 이 약을 담을 길이 없습니다'); continue; }
    F.forEach(f=>{ME[f]=false;}); if(r.flags) r.flags.forEach(f=>{ME[f]=true;});
    ME.taking=pick; ME.pub={};
    const sc=ixRun([]);
    if(!sc.hits.some(h=>h.r.id===r.id)){
      const over=sc.hits.filter(h=>(h.r.over||[]).includes(r.id)).map(h=>h.r.id);
      if(!over.length) bad.push(r.id+' — '+pick.join('+')+' 를 담아도 안 뜹니다');
    }
  }
  F.forEach(f=>{ME[f]=false;}); ME.taking=[]; ME.pub={}; saveMe();
  return bad;}"""

# 아이콘이 «서로 같은 그림»이 되는 사고를 막는다.
# 허리(back)와 장 경련(gutpain)이 24px 에서 사실상 같은 그림이었고,
# 감기(sneeze)·기침(cough)은 뿜는 표시가 «뒤통수»에 붙어 있었다(2026-09-22).
# 사람 눈을 대신할 수는 없지만, «둘이 똑같다»는 기계가 잡을 수 있다.
ICONDUP_JS = """async()=>{
  const names = Object.keys(I).filter(k=>typeof I[k]==='string' && I[k].indexOf('<svg')===0);
  const N=24, bits={};
  for (const k of names){
    const svg = I[k].replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"')
                    .replace('class="i"', 'fill="none" stroke="#000" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"');
    const img = new Image();
    const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    await new Promise((res,rej)=>{ img.onload=res; img.onerror=()=>res(); img.src=url; });
    const c=document.createElement('canvas'); c.width=N; c.height=N;
    const g=c.getContext('2d'); g.clearRect(0,0,N,N);
    try{ g.drawImage(img,0,0,N,N); }catch(e){}
    const d=g.getImageData(0,0,N,N).data; const b=[];
    for(let i=0;i<N*N;i++) b.push(d[i*4+3]>60?1:0);
    bits[k]=b;
  }
  const ink = k => bits[k].reduce((a,b)=>a+b,0);
  const same=[];
  for(let i=0;i<names.length;i++) for(let j=i+1;j<names.length;j++){
    const a=names[i], b=names[j];
    if(ink(a)<12 || ink(b)<12) continue;
    let eq=0; for(let t=0;t<N*N;t++) if(bits[a][t]===bits[b][t]) eq++;
    const r=eq/(N*N);
    if(r<0.965) continue;
    /* 일부러 그대로 두는 짝 — 세계 공통 기호라 바꾸면 오히려 못 읽는다.
       숫자를 느슨하게 푸는 대신, 예외를 눈에 보이게 적어 둔다. */
    const KEEP = ['clock|info'];
    if (KEEP.includes([a,b].sort().join('|'))) continue;
    same.push(a+'≈'+b+' '+Math.round(r*1000)/10+'%');
  }
  const blank = names.filter(k=>ink(k)<12);
  return {same, blank};
}"""

# 계열이 같으면 «피해야 할 몸 상태»도 같아야 한다.
# 이부프로펜에는 「심부전·신부전」이 달려 있는데 나프록센에는 없었고, 어느 소염제에도
# 「와파린」이 없었다. 그래서 와파린 드시는 어르신께 앱이 «같이 드시면 안 된다»고
# 경고하면서 동시에 그 소염제를 사라고 권하고 있었다(2026-09-22).
# 여기 적은 짝은 «성분 계열 → 그 계열이면 무조건 달려야 하는 몸 상태»다.
CLASSFLAG_JS = """pairs=>{
  const out=[];
  const KEEP = { 'celecoxib': ['ulcer', 'asthma'],   /* 위를 덜 건드리라고 만든 약 · 천식은 현욱님 답으로 안 단다(2026-09-23) */
                 'xylometazoline': ['bph', 'diabetes', 'glaucoma'],  /* 코에 뿌리는 약이라 전신 흡수가 적다 */
                 'benzoyl-peroxide': ['kidney'],                     /* 바르는 여드름약이다 */
                 'cough-syrup-rx': ['diabetes'],                     /* 처방 시럽 — 성분이 제품마다 다르다 */
                 'eye-decongestant': ['bph', 'heart', 'diabetes'],  /* 눈에 넣는 약 — 허가사항도 심장·당뇨는 «상의»(caution)로만 둔다 */
                 'allergy-eyedrop': ['glaucoma', 'bph'] };           /* 케토티펜 «안약» — 허가사항에 녹내장·전립선 금기가 없다(먹는 1세대 항히스타민과 다름) */
  for (const d of (D.drugs||[])) {
    ME.taking=[d.id]; ME.pub={};
    const cls=new Set(); ixItems([]).forEach(it=>it.ings.forEach(e=>(e.cls||[]).forEach(c=>cls.add(c))));
    const fl=new Set((d.avoid||[]).flatMap(a=>a.flags||[]));
    for (const [c,f] of pairs)
      if (cls.has(c) && !fl.has(f) && !(KEEP[d.id]||[]).includes(f)) out.push(d.id+' 에 '+f+' 가 없습니다('+c+' 계열)');
  }
  ME.taking=[]; ME.pub={}; saveMe();
  return out;}"""
CLASSFLAG_PAIRS = [['nsaid', 'anticoag'], ['nsaid', 'asthma'], ['nsaid', 'ulcer'],
                   ['anti1', 'glaucoma'], ['anti1', 'bph'],
                   ['decongest', 'bph'], ['decongest', 'heart'], ['decongest', 'diabetes'],
                   ['antacid', 'kidney'], ['ginkgo', 'anticoag'], ['h2', 'kidney'],
                   ['macrolide', 'heart'], ['quinolone', 'child']]

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
        br = p.chromium.launch(**LAUNCH)
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
            try: pg.wait_for_function('window.__READY__===true && (typeof DETAIL==="undefined" || DETAIL===2)', timeout=ms)   # 약 화면 칸(detail.json)까지
            except Exception: fails.append('본문 자료(core.json)를 못 받았습니다 — ' + pg.url)
        pg.goto(url); ready(); pg.wait_for_timeout(1200)
        pg.evaluate("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',taking:['cls:bp.arb'],pub:{}}))")
        routes = pg.evaluate("()=>['/home','/drugs','/tips','/me','/together','/kinds','/kinds/bp','/pill','/supp','/kids','/mix','/hello/1','/hello/3','/photo','/schedule','/about','/bag','/rxout','/senior','/myths','/askdoc','/askdoc?open=gout','/vitals','/visits','/me?t=meds','/me?t=set','/drugs?cat=all','/drugs?cat=nsaid','/senior?w=rx','/supp?t=label','/supp?t=stack','/tips?g=5','/myths?g=3','/schedule?t=sc2','/schedule?t=sc4','/pub/0','/pub/5']" +
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
        _CLICK = ['/home', '/kinds', '/supp', '/tips', '/myths', '/askdoc', '/me', '/schedule',
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

        # 5a-2. 고른 시간이 약의 최소 간격보다 촘촘하면 알려 줘야 한다
        pg.goto(url + '#/schedule'); ready(); pg.wait_for_timeout(250)
        _w = pg.evaluate("""()=>{
          PANE.schedule='sc1'; ME.taking=['naproxen']; ME.sched={naproxen:['08:00','13:00']}; route();
          const a=document.getElementById('view').innerText.includes('시간이 너무 촘촘해요');
          ME.sched={naproxen:['08:00','19:00']}; route();
          const b=document.getElementById('view').innerText.includes('시간이 너무 촘촘해요');
          ME.taking=[]; ME.sched={}; saveMe();
          return {tight:a, ok:b};}""")
        if not _w['tight']: fails.append('시간 간격이 촘촘한데 알려 주지 않습니다(나프록센 08:00+13:00)')
        if _w['ok']: fails.append('간격이 충분한데도 촘촘하다고 합니다(나프록센 08:00+19:00)')

        # 5a-3. 지난 기록 달력 — 35칸이 «정사각»으로 서고, 복용률 문장이 자연빈도로 나와야 한다.
        #       .today 라는 이름이 앱 안에 이미 있어서 달력 칸이 카드 여백을 물려받아 터진 적이 있다(2026-09-22).
        _c = pg.evaluate("""()=>{
          const day=n=>{const d=new Date();d.setDate(d.getDate()-n);
            return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')};
          ME.taking=['acetaminophen']; ME.sched={acetaminophen:['08:00','19:00']};
          ME.taken={}; ME.days={};
          for(let n=1;n<=10;n++){ ME.days[day(n)]=2; ME.taken[day(n)]= n%3 ? ['acetaminophen@08:00','acetaminophen@19:00'] : []; }
          PANE.schedule='sc3'; route();   /* 달력은 「지난 기록」 탭(2026-09-30) */
          const cells=[...document.querySelectorAll('.cal-d')];
          const bad=cells.map(c=>{const b=c.getBoundingClientRect();
            return Math.abs(b.width-b.height)>1.5 ? Math.round(b.width)+'x'+Math.round(b.height) : null}).filter(Boolean);
          const txt=document.getElementById('view').innerText;
          const pct=/[0-9]+ ?%/.test(txt.split('지난 기록')[1]||'');
          ME.taking=[]; ME.sched={}; ME.taken={}; ME.days={}; saveMe(); PANE.schedule='sc1';
          return {n:cells.length, bad:bad.slice(0,3), says:txt.includes('빠짐없이 드셨어요'), pct};}""")
        if _c['n'] != 35: fails.append(f'복약 달력 칸이 35개가 아닙니다: {_c["n"]}개')
        if _c['bad']: fails.append(f'복약 달력 칸이 정사각이 아닙니다: {_c["bad"]}')
        if not _c['says']: fails.append('복약 달력에 «며칠 중 며칠» 문장이 없습니다')
        if _c['pct']: fails.append('복약률을 %로 적고 있습니다 — 자연빈도(며칠 중 며칠)로 적어야 합니다')
        # 5a-7. 소아 용량 — 「N회 · M mg」이 곱셈을 부추기면 안 된다.
        #       덱시부프로펜 12 kg 에서 「4회 · 300 mg」이 떠서, 1회 84 mg × 4 = 336 mg 으로
        #       허가 한도를 넘기게 읽혔다(2026-09-22). 몸무게를 훑어 전부 본다.
        pg.goto(url + '#/kids'); ready(); pg.wait_for_timeout(400)
        _k = pg.evaluate("""()=>{
          const bad=[];
          for (const w of [6,8,10,12,15,18,20,24,28,30,35,40,50]) {
            ME.age='child'; ME.child={name:'',birth:'2016-03-01',weight:w}; route();
            for (const c of document.querySelectorAll('.dose-card')) {
              const nm=(c.querySelector('.eyebrow')||{}).innerText||'';
              const mg=(c.querySelector('.dose-meta div:nth-child(1) b')||{}).innerText||'';
              const cap=(c.querySelector('.dose-meta div:nth-child(3) b')||{}).innerText||'';
              const hi=+((mg.match(/~\s*([0-9.]+)/)||[])[1]||0);
              const day=+((cap.match(/([0-9,]+)\s*mg/)||[])[1]||'0').replace(/,/g,'');
              const n=+((cap.match(/^([0-9]+)회/)||[])[1]||0);
              if (n && hi && day && n*hi > day + 0.5) bad.push(w+'kg '+nm.slice(0,8)+' '+cap+' (1회 '+hi+'×'+n+'='+(n*hi)+')');
            }
          }
          ME.age='adult'; ME.child={}; saveMe();
          return bad;}""")
        if _k: fails.append(f'소아 하루 한도가 곱하면 넘습니다: {_k[:3]}')
        # 5a-10. 규칙이 쓰는 몸 상태는 «내 정보»에서 켤 수 있어야 한다.
        #        당뇨는 약 경고에 쓰이는데 정작 켤 칸이 없었다(2026-09-22).
        pg.goto(url + '#/me'); ready(); pg.wait_for_timeout(500)
        _fl = pg.evaluate("""()=>{
          const txt = document.getElementById('view').innerText;
          /* 칸의 문구는 조금씩 다르다 — 핵심 낱말로 본다 */
          const need = {pregnant:'임신', ulcer:'위궤양', kidney:'신장', liver:'간 질환', heart:'심장',
                        asthma:'천식', anticoag:'항응고', glaucoma:'녹내장', bph:'전립선', gout:'통풍', diabetes:'당뇨'};
          return Object.keys(need).filter(k => !txt.includes(need[k]));}""")
        if _fl: fails.append(f'내 정보에서 켤 수 없는 몸 상태가 있습니다: {_fl}')
        # 5a-10b. ClinicScore 문법(2026-09-29 현욱님) — 내 정보는 탭 셋, 건강 상태는 누르는 단추.
        #         누르면 그 자리에서 켜지고(맨 위로 튀지 않고) 「켜 둔 것」에 설명이 붙어야 한다.
        _mt = pg.evaluate("""()=>{
          ['heart','diabetes','ulcer','kidney','liver','anticoag','glaucoma','bph','asthma','alcohol','gout','pregnant'].forEach(f=>{ME[f]=false;}); saveMe(); route();
          const tabs=[...document.querySelectorAll('.metabs .tab')].map(b=>b.innerText.trim().replace(/\\s*\\d+$/,''));
          window.scrollTo(0,400); const y=window.scrollY;
          const chip=[...document.querySelectorAll('.chip-m')].find(b=>b.innerText.includes('전립선비대')); chip.click();
          const on=ME.bph===true, desc=(document.querySelector('.cond-on')||{}).innerText||'', stay=window.scrollY===y;
          [...document.querySelectorAll('.chip-m')].find(b=>b.innerText.includes('전립선비대')).click();
          const off=ME.bph===false && !document.querySelector('.cond-on');
          return {tabs, on, desc, stay, off, chips:document.querySelectorAll('.chip-m').length};}""")
        if _mt['tabs'] != ['내 몸', '먹는 약', '설정']: fails.append(f'내 정보 탭이 셋이 아닙니다: {_mt["tabs"]}')
        if _mt['chips'] != 12 or not _mt['on'] or not _mt['off']: fails.append(f'건강 상태 단추가 켜지고 꺼지지 않습니다: {_mt}')
        if '소변이 막힐 수' not in _mt['desc']: fails.append('건강 상태를 눌러도 「켜 둔 것」 설명이 안 붙습니다')
        if not _mt['stay']: fails.append('건강 상태를 누르면 화면이 맨 위로 튑니다')
        pg.goto(url + '#/me?t=meds'); ready(); pg.wait_for_timeout(300)
        if not pg.query_selector('#mq') or '복용 시간 알림' not in pg.inner_text('#view'): fails.append('내 정보 「먹는 약」 탭에 약 담기·알림이 없습니다')
        pg.goto(url + '#/me?t=set'); ready(); pg.wait_for_timeout(300)
        _st = pg.inner_text('#view')
        for kw in ('글자 크기', '화면 밝기', '휴대폰을 바꾸실 때', '개인정보처리방침'):
            if kw not in _st: fails.append(f'내 정보 「설정」 탭에 {kw} 없음')
        # 홈 — 탭을 누르면 그 묶음만. 전체 = 검수 끝난 증상 전부, 검수 대기는 따로
        pg.goto(url + '#/home'); ready(); pg.wait_for_timeout(300)
        _hm = pg.evaluate("""()=>{
          const n=()=>document.querySelectorAll('#hlist .srow').length, S=D.symptoms||[];
          const tab=k=>{ const b=[...document.querySelectorAll('.htabs .tab')].find(x=>x.dataset.k===k); b.click(); return n(); };
          const r={top:tab('top'), pain:tab('g:통증'), all:tab('all'), wait:tab('wait'),
            wantPain:S.filter(s=>s.group==='통증'&&s.reviewed!==false).length, wantAll:S.filter(s=>s.reviewed!==false).length, wantWait:S.filter(s=>s.reviewed===false).length,
            oneOn:document.querySelectorAll('.htabs .tab.on').length};
          tab('top'); return r;}""")
        if _hm['top'] != 12: fails.append(f'홈 「자주 찾는」이 12가지가 아닙니다: {_hm["top"]}')
        if _hm['pain'] != _hm['wantPain'] or _hm['all'] != _hm['wantAll'] or _hm['wait'] != _hm['wantWait']: fails.append(f'홈 탭 목록 수가 어긋납니다: {_hm}')
        if _hm['oneOn'] != 1: fails.append('홈 탭에서 고른 것이 하나가 아닙니다')
        # 5a-10c. 증상·약 상세도 탭(2026-09-30 현욱님 「증상상세 약 상세도 잘 정리하자」) — 탭마다 내용이 있고 넘침·잘림이 없어야 한다
        for _r in ['/symptom/cold', '/symptom/bph', '/symptom/fever', '/drug/ibuprofen', '/drug/acetaminophen']:
            pg.goto(url + '#' + _r); ready(); pg.wait_for_timeout(350)
            _tabs = pg.evaluate("()=>[...document.querySelectorAll('.stabs .tab,.dtabs .tab')].map(b=>b.dataset.p)")
            if len(_tabs) < 3: fails.append(f'{_r}: 탭이 없습니다 ({_tabs})')
            for _k in _tabs:
                pg.click(f'.tab[data-p="{_k}"]'); pg.wait_for_timeout(120)
                _pv = pg.evaluate("(k)=>{const p=document.getElementById(k);return p&&getComputedStyle(p).display!=='none'?p.innerText.trim().length:-1}", _k)
                if _pv < 20: fails.append(f'{_r} 탭 {_k}: 누르면 보이는 내용이 없습니다({_pv})')
                o = pg.evaluate(OVERFLOW_JS)
                if o['ov'] or o['clip']: fails.append(f'{_r} 탭 {_k}: 넘침·잘림 {o["ov"][:1]}{o["clip"][:1]}')
        # 탭 칸(.pane) 안에 다른 칸이 들어가 있으면 그 탭을 골라야만 보인다 — 복용 알림에서 한 번 그랬다(2026-09-30)
        pg.goto(url + '#/schedule'); ready(); pg.wait_for_timeout(250)
        _nest = pg.evaluate("""()=>{ ME.taking=['ibuprofen','acetaminophen']; ME.prn={acetaminophen:true}; ME.sched={ibuprofen:['08:00']}; route();
          const out=[]; for (const r of ['/schedule','/symptom/cold','/drug/ibuprofen']) { location.hash='#'+r; route();
            document.querySelectorAll('.pane .pane').forEach(p=>out.push(r+' #'+p.id));
            if (r==='/schedule' && getComputedStyle(document.querySelector('.prn-row')).display==='none') out.push('필요할 때 드신 약이 숨음'); }
          ME.taking=[]; ME.prn={}; ME.sched={}; saveMe(); return out; }""")
        if _nest: fails.append(f'탭 칸이 다른 칸 안에 들어가 있습니다: {_nest[:4]}')
        pg.goto(url + '#/symptom/cold'); ready(); pg.wait_for_timeout(300)
        if pg.evaluate("()=>{openCare();return getComputedStyle(document.getElementById('sp2')).display!=='none'&&document.querySelector('.tab[data-p=sp2]').classList.contains('on')}") is not True:
            fails.append('증상 화면: 「이럴 땐 병원으로」를 눌러도 병원 탭이 열리지 않습니다')
        # 약학정보원 사진(2026-09-30 현욱님 「그냥 쓰자」) — 짝 자료가 있으면 그 사진·그 제품 페이지로, 없으면 식약처 사진·검색 화면
        pg.goto(url + '#/pill'); ready(); pg.wait_for_timeout(300)
        _kp = pg.evaluate("""async()=>{ await pubPills(); const p=(PUB.pills||[]).find(x=>x.img); if(!p) return {skip:true};
          const before=pillImg(p); KPIC={[p.seq]:['2013062800004','201306280000401.jpg']};
          const after=pillImg(p); location.hash='#/pillinfo/'+p.seq; route();
          const a=[...document.querySelectorAll('a.plink')].find(x=>/health\.kr/.test(x.href));
          const r={before, after, link:a&&a.href}; KPIC={}; return r; }""")
        if not _kp.get('skip'):
            if 'nedrug' not in (_kp['before'] or ''): fails.append(f'약학정보원 짝이 없을 때 식약처 사진을 안 씁니다: {_kp["before"]}')
            if _kp['after'] != 'https://common.health.kr/shared/images/sb_photo/big3/201306280000401.jpg': fails.append(f'약학정보원 사진 주소가 틀립니다: {_kp["after"]}')
            if 'result_drug.asp?drug_cd=2013062800004' not in (_kp['link'] or ''): fails.append(f'약학정보원 제품 페이지 링크가 없습니다: {_kp["link"]}')
        # 식약처 제품 화면(e약은요) — 탭(약사 안내·허가 내용·성분 해설) 칸마다 내용이 있고 날것 코드(${)가 보이면 안 된다(2026-09-30)
        pg.goto(url + '#/pub/0'); ready(); pg.wait_for_timeout(1500)
        _pb = pg.evaluate("""()=>['pb1','pb2','pb3'].filter(k=>document.getElementById(k)).map(k=>{const t=document.getElementById(k).textContent; return [k, t.trim().length, t.includes('${')];})""")
        if not _pb: fails.append('식약처 제품 화면에 탭 칸이 없습니다')
        for _k, _n, _raw in _pb:
            if _n < 20: fails.append(f'식약처 제품 화면 {_k} 칸이 비었습니다')
            if _raw: fails.append(f'식약처 제품 화면 {_k} 칸에 날것 코드가 보입니다')
        # 5a-11. 화면 밝기 — 휴대폰 설정만 따르지 말고 앱에서도 고를 수 있어야 한다
        _th = pg.evaluate("""()=>{
          const before = themeNow();
          setTheme('light'); const a = document.documentElement.dataset.theme;
          setTheme('dark');  const b = document.documentElement.dataset.theme;
          setTheme('auto');  const c = document.documentElement.dataset.theme || '(없음)';
          setTheme(before);
          return {a, b, c};}""")
        if _th['a'] != 'light' or _th['b'] != 'dark' or _th['c'] != '(없음)':
            fails.append(f'화면 밝기 고르기가 듣지 않습니다: {_th}')
        # 5a-9. 성분 이름 읽기 — «두 글자 어근»이 엉뚱한 약을 물면 안 된다.
        #       「산화마그네슘」에서 염을 떼다 남은 「산화」가 여드름 겔(과산화벤조일)을
        #       제산제로 만들고 있었다. 겹침 경고가 통째로 틀어지는 자리다(2026-09-22).
        _ig = pg.evaluate("""cases=>cases.map(([t,want])=>{
          const got=ingFind(t).map(e=>e.k).sort();
          const ok = want.length ? want.every(w=>got.includes(w)) : got.length===0;
          return ok ? null : t+' → ['+got.join(',')+'] (바라던 것: '+(want.join(',')||'없음')+')';
        }).filter(Boolean)""", [
            ['과산화벤조일', ['benzoyl-peroxide']], ['산화아연연고', []], ['이산화티탄', []],
            ['산화마그네슘', ['antacid']], ['수산화마그네슘', ['antacid']], ['마그밀', ['magnesium-lax']],
            ['이부프로펜나트륨', ['ibuprofen']], ['나프록센나트륨', ['naproxen']],
            ['탄산리튬', ['lithium']], ['리시노프릴', ['acei']], ['알프라졸람', ['bzd']], ['은행잎', ['ginkgo']],
            # 「니코틴산아미드」는 비타민 B3 — 종합비타민 489개가 금연 보조제로 읽히면 안 된다(2026-09-23). 비타민으로 읽는 것은 맞다(2026-09-29)
            ['니코틴산아미드', ['vitamin-b']], ['니코틴산벤질', []], ['니코틴', ['nicotine']], ['니코틴폴라크리렉스', ['nicotine']],
            ['니코틴타르타르산염수화물', ['nicotine']], ['미녹시딜', ['minoxidil']],
            ['살리실산', ['salicylic-acid']], ['브롬페니라민말레산염', ['brompheniramine']], ['d-클로르페니라민말레산염', ['chlorpheniramine']], ['페니라민말레산염', ['pheniramine']], ['살리실산 락트산', ['salicylic-acid']], ['살리실산글리콜', ['glycol-salicylate']], ['클로닉신리시네이트', ['clonixin']], ['돔페리돈', ['domperidone']], ['스코폴리아엑스', ['scopolia']], ['니자티딘', ['nizatidine']], ['폴마콕시브', ['polmacoxib']], ['케토코나졸', ['azole-top']], ['에코나졸질산염', ['azole-top']], ['플루코나졸', ['azole']], ['이트라코나졸고체분산체', ['azole']], ['옥시코돈염산염', ['opioid-strong']], ['트리플루살', ['triflusal']], ['네비보롤염산염', ['betablock']], ['아세틸살리실산', ['aspirin']],
        ])
        _ig += pg.evaluate("""L=>L.map(([t,bad])=>{ const d=drugByIngr(t); return d&&d.id===bad ? t+' → '+bad : null; }).filter(Boolean)""", [
            ['니코틴산아미드', 'nicotine-patch'], ['니코틴산아미드 리보플라빈', 'nicotine-patch'], ['니코틴산벤질', 'nicotine-patch'],
            ['살리실산글리콜', 'salicylic-corn'], ['살리실산메틸', 'salicylic-corn'], ['아세틸살리실산', 'salicylic-corn'], ['살리실산', 'methyl-salicylate'], ['포비돈', 'povidone-iodine'], ['페퍼민트맛|오렌지맛|모과맛', 'peppermint-oil'],
        ])
        _ig += pg.evaluate("""L=>L.map(([t,want])=>{ const d=drugByIngr(t); return (d&&d.id)===want ? null : t+' → '+(d&&d.id)+' (바라던 것: '+want+')'; }).filter(Boolean)""", [
            ['오메프라졸', 'omeprazole'], ['니코틴', 'nicotine-patch'], ['미녹시딜', 'minoxidil'], ['포비돈요오드', 'povidone-iodine'],
        ])
        _ig += pg.evaluate("""L=>L.map(([t,p,want])=>{ const d=drugByIngr(t,p); return (d&&d.id||null)===want ? null : p.n+' → '+(d&&d.id)+' (바라던 것: '+want+')'; }).filter(Boolean)""", [
            ['트리암시놀론', {'n': '트리코탈정(트리암시놀론)', 'rx': 1}, None],
            ['트리암시놀론아세토니드', {'n': '아프타치정(트리암시놀론아세토니드)', 'rx': 0}, 'triamcinolone'],
            ['플루르비프로펜', {'n': '스트렙실트로키', 'rx': 0}, 'flurbiprofen'],
        ])
        # 공공 제품 전부(약 1만 개) — 「제품 → 약 화면」 연결이 성분 해석과 어긋나는 곳이 없어야 한다.
        # 포비돈 인공눈물이 소독약으로, 맛 이름이 페퍼민트 캡슐로 가던 것을 이 검사로 찾았다(2026-09-23).
        _ig += pg.evaluate("""async()=>{await pubPills(); try{await pubPillsRx()}catch(e){} const idx=await pubIndex();
          const rows=[...(PUB.pills||[]),...(PUB.rx||[]),...idx.map(r=>({n:r.n,ingr:(r.i||[]).join(' '),rx:0}))]; const bad=new Set();
          for(const x of rows){ if(!x.ingr) continue; const d=drugByIngr(x.ingr,x); if(!d) continue; const di=ingIndex().byDrug[d.id];
            if(di && (di.aka||[]).length && !ingFind(x.ingr).includes(di)) bad.add(x.n.slice(0,24)+' → '+d.id); }
          return [...bad];}""")
        if _ig: fails.append(f'성분 이름을 잘못 읽습니다: {_ig[:4]}')
        # 5a-8. 계열↔몸 상태 짝 — 같은 계열인데 한 약에만 경고가 달린 곳을 잡는다
        pg.goto(url + '#/home'); ready(); pg.wait_for_timeout(250)
        _cf = pg.evaluate(CLASSFLAG_JS, CLASSFLAG_PAIRS)
        if _cf: fails.append(f'계열은 같은데 피할 몸 상태가 빠졌습니다({len(_cf)}건): {_cf[:4]}')
        # 5a-6. 65세 이상으로 켜면 «소염제»에도 주의가 붙어야 한다.
        #       전에는 항콜린 점수만 보아, 「어르신 주의」가 종합감기약 한 줄에만 붙고
        #       정작 소염제에는 아무 표시가 없었다(2026-09-22).
        pg.goto(url + '#/symptom/cold'); ready(); pg.wait_for_timeout(400)
        _s = pg.evaluate("""()=>{
          /* 앞 검사가 켜 둔 몸 상태가 남아 있으면 「약사와 상의」 배지가 먼저 붙는다 — 비우고 본다 */
          ['heart','diabetes','ulcer','kidney','liver','anticoag','glaucoma','bph','asthma','alcohol','gout','pregnant'].forEach(f=>{ME[f]=false;});
          const has = a => { ME.age=a; ME.taking=[]; ME.pub={}; route();
            return [...document.querySelectorAll('.buy-item')]
              .some(e=>/이부프로펜|나프록센|덱시부프로펜/.test(e.innerText) && /어르신 주의/.test(e.innerText)); };
          const senior = has('senior'), adult = has('adult');
          ME.age='adult'; saveMe();
          return {senior, adult};}""")
        if not _s['senior']: fails.append('65세 이상인데 소염제에 「어르신 주의」가 안 붙습니다')
        if _s['adult']: fails.append('성인인데도 소염제에 「어르신 주의」가 붙습니다')
        # 5a-4. 홈 「오늘 약」 한 장 — 약이 없으면 안 뜨고, 있으면 지금 드실 것을 보여 줘야 한다
        pg.goto(url + '#/home'); ready(); pg.wait_for_timeout(250)
        _h = pg.evaluate("""()=>{
          ME.taking=[]; ME.sched={}; ME.taken={}; route();
          const none = !document.querySelector('.dh');
          /* 앞 검사(단추 전부 누르기)가 아세트아미노펜을 담았다 빼면서 «필요할 때만»으로 표시해 둘 수 있다 — 비우고 본다 */
          ME.prn={}; ME.taking=['acetaminophen']; ME.sched={acetaminophen:['00:01']}; ME.taken={}; route();
          const card = document.querySelector('.dh');
          const due = !!(card && card.querySelector('.dh-tick'));
          if (due) card.querySelector('.dh-tick').click();
          const ok = !!document.querySelector('.dh-b.ok');
          ME.taking=[]; ME.sched={}; ME.taken={}; ME.days={}; saveMe();
          return {none, has:!!card, due, ok};}""")
        if not _h['none']: fails.append('담아 둔 약이 없는데 홈에 「오늘 약」이 뜹니다')
        if not _h['has']: fails.append('약을 담고 시간을 골랐는데 홈에 「오늘 약」이 없습니다')
        if not _h['due']: fails.append('드실 시간이 지났는데 홈에서 「드셨어요」를 누를 수 없습니다')
        if not _h['ok']: fails.append('홈에서 「드셨어요」를 눌러도 다 드신 것으로 바뀌지 않습니다')
        # 5a-5. 아이콘 전수 — 서로 같은 그림이거나 비어 있으면 잡는다
        pg.goto(url + '#/home'); ready(); pg.wait_for_timeout(300)
        _i = pg.evaluate(ICONDUP_JS)
        if _i['blank']: fails.append(f'아이콘이 비어 있습니다: {_i["blank"][:4]}')
        if _i['same']: fails.append(f'아이콘 둘이 24px 에서 같은 그림입니다: {_i["same"][:4]}')
        # 5a. 약 알림 — 시간이 돼도 안 오던 것(타이머 안에서 조용히 터지고 있었다)
        pg.goto(url + '#/schedule'); ready(); pg.wait_for_timeout(300)
        _n = pg.evaluate(NOTI_JS)
        if _n['errs']: fails.append(f'약 알림이 터집니다: {_n["errs"][:2]}')
        if not _n['fired']: fails.append('약 알림이 하나도 만들어지지 않습니다 — 시간이 돼도 안 옵니다')
        # 5b. 어르신 모드(글자 20px·큰 단추) — 넘침·잘림은 큰 글씨에서 먼저 터진다
        pg.evaluate("localStorage.setItem('yakjido.fs','22px');localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',easy:true,taking:['cls:bp.arb','ibuprofen'],pub:{}}))")
        for r in SC + ['/bag', '/schedule', '/symptom/cramp', '/symptom/sprain', '/drug/acetaminophen', '/kinds/bp', '/vitals', '/visits', '/me?t=meds', '/me?t=set']:
            pg.goto(url + '#' + r); pg.reload(); ready(); pg.wait_for_timeout(500)
            o = pg.evaluate(OVERFLOW_JS)
            if o['ov']: fails.append(f'어르신 모드 가로 넘침 {r}: {o["ov"]}')
            if o['clip']: fails.append(f'어르신 모드 글자 잘림 {r}: {o["clip"]}')
        # 5c. 좁은 화면(320px) × 가장 큰 글씨 — 오래된 안드로이드 폰과 «화면 확대»를 켜신 분의 자리.
        #     낱알 검색칸과 소아 화면 단추가 실제로 화면을 넘고 있었다.
        pg.set_viewport_size({'width': 320, 'height': 640})
        for r in SC + ['/pill', '/kids', '/kinds', '/bag', '/schedule', '/symptom/fever', '/symptom/motion', '/vitals', '/visits', '/me?t=meds', '/me?t=set']:
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
        # 6b. 겹침 규칙 52개 전수 — 조건을 만족하는 약을 담으면 실제로 떠야 한다
        pg.evaluate("localStorage.removeItem('yakjido.me.v1')")
        pg.goto(url + '#/together'); pg.reload(); ready(); pg.wait_for_timeout(500)
        for b in pg.evaluate(RULES_JS): fails.append(f'겹침 규칙 {b}')
        pg.evaluate("localStorage.removeItem('yakjido.me.v1')")
        # 알림의 「먹었어요」 → #/schedule?tick= 으로 들어오면 그 복용이 체크돼야 한다(2026-09-23)
        pg.evaluate("localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['ibuprofen'],sched:{ibuprofen:['08:00']},pub:{}}))")
        pg.goto(url + '#/schedule?tick=ibuprofen%4008%3A00'); pg.reload(); ready(); pg.wait_for_timeout(400)
        if 'ibuprofen@08:00' not in pg.evaluate("()=>takenSet()"): fails.append('알림의 「먹었어요」가 복용 체크로 이어지지 않습니다')
        pg.evaluate("localStorage.removeItem('yakjido.me.v1')")
        # 성분 읽기 전수 — 식약처 2.9만 제품에서 «하나도 못 읽는 제품»이 다시 늘면 잡는다(2026-09-29 기준선)
        import importlib.util as _iu
        _sp = _iu.spec_from_file_location('ing_audit', str(ROOT / 'yakjido' / 'tools' / 'ing_audit.py')); _ia = _iu.module_from_spec(_sp); _sp.loader.exec_module(_ia)
        pg.goto(url + '#/home'); ready(); pg.wait_for_timeout(600)
        _cov = pg.evaluate(_ia.JS, ['pills.json', 'pills-rx.json', 'easy-index.json'])
        for _f, _lim in (('pills.json', 25), ('pills-rx.json', 157), ('easy-index.json', 85)):
            if _cov[_f]['none'] > _lim: fails.append(f'성분을 못 읽는 제품이 늘었습니다 {_f}: {_cov[_f]["none"]} (기준 {_lim}) — {_cov[_f]["bad"][:5]}')
        # 혈압·혈당 수첩 — 적기·7일 평균·기준(135/85) 안내·지우기(2026-09-29)
        pv = br.new_page(viewport={'width': 390, 'height': 844}); verr = []
        pv.on('pageerror', lambda e: verr.append(str(e)))
        pv.clock.install(time='2026-09-29T08:00:00')
        pv.add_init_script("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['cls:bp.arb'],pub:{}}))")
        pv.goto(url + '#/vitals'); pv.wait_for_selector('.app', timeout=15000); pv.wait_for_timeout(600)
        for sv, dv in ((142, 88), (138, 86), (140, 90)):
            pv.fill('#vs', str(sv)); pv.fill('#vd', str(dv)); pv.click('button:has-text("적어 두기")'); pv.wait_for_timeout(250)
        vt = pv.inner_text('.app')
        if '140/88' not in vt.replace('\n', '').replace(' ', '') and '140' not in pv.inner_text('.vt-big'): fails.append(f'혈압 수첩: 7일 평균이 틀립니다 — {pv.inner_text(".vt-big")[:60]}')
        if '가정혈압 기준(135/85)보다 높은 편' not in vt or '다음 진료 때 보여 주세요' not in vt: fails.append('혈압 수첩: 높은 평균 안내가 없습니다(혈압약 드시는 분)')
        if not pv.query_selector('svg.vz polyline'): fails.append('혈압 수첩: 2주 흐름 그림이 없습니다')
        pv.fill('#vs', '80'); pv.fill('#vd', '120'); pv.click('button:has-text("적어 두기")'); pv.wait_for_timeout(250)
        if len(pv.evaluate("()=>ME.vitals")) != 3: fails.append('혈압 수첩: 아래가 위보다 큰 값을 받아들였습니다')
        pv.click('.vt-x'); pv.wait_for_timeout(250)
        if len(pv.evaluate("()=>ME.vitals")) != 2: fails.append('혈압 수첩: 지우기가 안 됩니다')
        pv.click('.seg button:has-text("혈당")'); pv.wait_for_timeout(250); pv.fill('#vg', '112'); pv.click('button:has-text("적어 두기")'); pv.wait_for_timeout(250)
        if not any(x.get('k') == 'bg' and x.get('v') == 112 for x in pv.evaluate("()=>ME.vitals")): fails.append('혈압 수첩: 혈당이 적히지 않습니다')
        # 아주 높은 혈압 — 첫 번째는 «바르게 재고 5분 쉬고 다시», 쉬고 다시 재도 높으면 119·오늘 진료(현욱님 2026-09-29)
        pv.click('.seg button:has-text("혈압")'); pv.wait_for_timeout(200)
        pv.fill('#vs', '186'); pv.fill('#vd', '104'); pv.click('button:has-text("적어 두기")'); pv.wait_for_timeout(250)
        if '먼저 바르게 쟀는지' not in pv.inner_text('.app'): fails.append('혈압 수첩: 180 이상 첫 값에 «바르게 재기» 안내가 없습니다')
        if '119' in pv.inner_text('.note.alert') if pv.query_selector('.note.alert') else False: fails.append('혈압 수첩: 첫 값부터 119 안내가 뜹니다')
        pv.fill('#vs', '184'); pv.fill('#vd', '100'); pv.click('button:has-text("적어 두기")'); pv.wait_for_timeout(250)
        if not pv.query_selector('.note.alert') or '오늘 안에 진료' not in pv.inner_text('.note.alert'): fails.append('혈압 수첩: 쉬고 다시 재도 높은데 안내가 없습니다')
        pv.click('.seg button:has-text("혈당")'); pv.wait_for_timeout(200); pv.fill('#vg', '62'); pv.click('button:has-text("적어 두기")'); pv.wait_for_timeout(250)
        if not pv.query_selector('.note.alert') or '저혈당' not in pv.inner_text('.note.alert'): fails.append('혈압 수첩: 70 미만인데 저혈당 안내가 없습니다')
        if '저혈당' not in pv.inner_text('.vt-list'): fails.append('혈압 수첩: 혈당 목록에 저혈당 표시가 없습니다')
        # 진료 예약 적기 → 목록·홈 «내일 진료»·진료실 한 장
        pv.goto(url + '#/visits'); pv.wait_for_timeout(600)
        pv.fill('#vdate', '2026-09-30'); pv.fill('#vtime', '10:30'); pv.fill('#vwhere', '동네 내과'); pv.click('button:has-text("적어 두기")'); pv.wait_for_timeout(300)
        if '9월 30일' not in pv.inner_text('.vt-list'): fails.append('진료 예약: 적은 예약이 목록에 없습니다')
        pv.goto(url + '#/home'); pv.wait_for_timeout(800)
        if '내일 진료' not in pv.inner_text('.util'): fails.append('진료 예약: 홈에 «내일 진료»가 없습니다')
        pv.goto(url + '#/bag'); pv.wait_for_timeout(800)
        if '다음 진료' not in pv.inner_text('.app'): fails.append('진료 예약: 진료실 한 장에 다음 진료가 없습니다')
        if '집에서 잰 숫자' not in pv.inner_text('.app') or '혈압 최근 2주 평균' not in pv.inner_text('.app'): fails.append('혈압 수첩: 진료실 한 장(내 약 목록)에 집에서 잰 숫자가 없습니다')
        if verr: fails.append(f'혈압 수첩: JS 오류 {verr[:2]}')
        pv.close()
        # 필요할 때만 드시는 약 — 드신 때를 적고, 허가 간격·하루 상한으로 막아 드리는지(2026-09-29)
        pp = br.new_page(viewport={'width': 390, 'height': 844}); perr = []; dlg = []
        pp.on('pageerror', lambda e: perr.append(str(e)))
        pp.clock.install(time='2026-09-29T10:00:00')
        pp.add_init_script("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['acetaminophen','ibuprofen'],prn:{acetaminophen:true},stock:{acetaminophen:{left:10,at:'2026-09-29'}},pub:{}}))")
        pp.goto(url + '#/schedule'); pp.wait_for_selector('.app', timeout=15000); pp.wait_for_timeout(800)
        if pp.evaluate("()=>schedOf('acetaminophen', takingItems().find(x=>x.id==='acetaminophen')).length"): fails.append('필요할 때만: 시간 알림이 남아 있습니다')
        if '필요할 때 드신 약' not in pp.inner_text('.app'): fails.append('필요할 때만: 「필요할 때 드신 약」 칸이 없습니다')
        pp.click('.prn-row button:has-text("지금 먹었어요")'); pp.wait_for_timeout(300)
        row = pp.inner_text('.prn-row')
        if '오늘 1번' not in row or '14:00부터' not in row: fails.append(f'필요할 때만: 1번째 뒤 표시가 틀립니다 — {row[:120]}')
        pp.once('dialog', lambda d: (dlg.append(d.message), d.dismiss()))
        pp.click('.prn-row button:has-text("지금 먹었어요")'); pp.wait_for_timeout(300)
        if not dlg or '4시간' not in dlg[0]: fails.append(f'필요할 때만: 간격 안에 또 누르면 물어봐야 합니다 — {dlg}')
        if '오늘 1번' not in pp.inner_text('.prn-row'): fails.append('필요할 때만: 취소했는데 적혔습니다')
        if pp.evaluate("()=>prnLeft('acetaminophen')") != 9: fails.append('필요할 때만: 남은 알 수가 1 줄지 않았습니다')
        pp.click('.prn-qty button:has-text("2알")'); pp.wait_for_timeout(200)
        pp.once('dialog', lambda d: d.accept()); pp.click('.prn-row button:has-text("지금 먹었어요")'); pp.wait_for_timeout(300)
        _pl = pp.evaluate("()=>prnLeft('acetaminophen')")
        if _pl != 7: fails.append(f'필요할 때만: 2알을 골랐는데 남은 알 수가 맞지 않습니다 — {_pl}')
        pp.click('.prn-undo'); pp.wait_for_timeout(200)
        if '필요할 때 드신 약: ' not in pp.evaluate("()=>careReport()"): fails.append('필요할 때만: 보호자 보고에 빠졌습니다')
        pp.click('.prn-undo'); pp.wait_for_timeout(300)
        if pp.evaluate("()=>prnState(takingItems().find(x=>x.id==='acetaminophen')).count") != 0: fails.append('필요할 때만: 지우기가 안 됩니다')
        # 담자마자 «필요할 때만» — 진통제는 그렇게, 혈압약 종류는 아니게
        pp.evaluate("()=>{ME.taking=[];ME.prn={};saveMe();toggleTaking('ibuprofen');toggleTaking('famotidine');}"); pp.wait_for_timeout(300)
        ap = pp.evaluate("()=>({ibu:isPrn('ibuprofen'), fam:isPrn('famotidine')})")
        if not ap['ibu']: fails.append('필요할 때만: 이부프로펜을 담았는데 «필요할 때만»이 아닙니다')
        # 항콜린 아닌 진경제는 녹내장 «금지» 경고에서 빠진다 — 부틸스코폴라민은 그대로(2026-09-29 현욱님)
        _gl = pp.evaluate("()=>{ME.glaucoma=true; const r={}; for(const id of ['peppermint-oil']){ME.taking=[id];ME.pub={};r[id]=ixRun([]).hits.some(h=>h.r.id==='anticho-glaucoma');} ME.taking=['pub:1'];ME.pub={'pub:1':{name:'부스코판',full:'부스코판정(부틸스코폴라민브롬화물)',ingr:'부틸스코폴라민브롬화물',rx:0,seq:'1',drugId:''}}; r.busco=ixRun([]).hits.some(h=>h.r.id==='anticho-glaucoma'); ME.glaucoma=false; return r;}")
        if _gl.get('peppermint-oil'): fails.append('페퍼민트오일에 녹내장 금지 경고가 아직 뜹니다')
        if not _gl.get('busco'): fails.append('부틸스코폴라민에 녹내장 금지 경고가 사라졌습니다')
        if perr: fails.append(f'필요할 때만: JS 오류 {perr[:2]}')
        pp.close()
        # 설치한 안드로이드 앱 — 앱을 닫아도 울리도록 휴대폰 알람으로 거는지(2026-09-28)
        pn = br.new_page(viewport={'width': 390, 'height': 844}); nerr = []
        pn.on('pageerror', lambda e: nerr.append(str(e)))
        pn.clock.install(time='2026-09-28T10:00:00')
        pn.add_init_script(CAP_MOCK)
        pn.add_init_script("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['ibuprofen'],sched:{ibuprofen:['08:00','20:00']},pub:{}}))")
        pn.goto(url + '#/schedule?t=sc4'); pn.wait_for_selector('.app', timeout=15000); pn.wait_for_timeout(1500)   # 알림 방법은 탭 안(2026-09-30)
        L = pn.evaluate("()=>__LN.pending")
        daily = [x for x in L if x.get('schedule', {}).get('on')]
        again = [x for x in L if x.get('schedule', {}).get('at')]
        if sorted((x['schedule']['on']['hour'], x['schedule']['on']['minute']) for x in daily) != [(8, 0), (20, 0)]:
            fails.append(f'앱 알람: 매일 반복 알림이 08:00·20:00 둘이어야 합니다 — {[x.get("schedule") for x in daily]}')
        if any(x.get('channelId') != 'dose' or x.get('actionTypeId') != 'dose' for x in L): fails.append('앱 알람: 복용 알림 채널·「먹었어요」 단추가 빠졌습니다')
        if any(x.get('isExactNotification') for x in L): fails.append('앱 알람: 정확한 시각 권한이 없는데 정확 알람으로 걸어 설정 화면이 매번 뜹니다')
        if len(again) != 13: fails.append(f'앱 알람: 「아직 안 드셨어요」가 7일치 13개(오늘 08:30 은 지남)여야 합니다 — {len(again)}')
        if not (pn.evaluate("()=>__LN.types && __LN.types.types[0].actions.map(a=>a.id).join()") == 'took,later'): fails.append('앱 알람: 「먹었어요」·「10분 뒤 다시」 단추가 없습니다')
        t = pn.inner_text('.app')
        if '휴대폰 알림' not in t or '앱이 열려 있을 때' in t: fails.append('앱 알람: 알림 방법 카드가 설치 앱용으로 바뀌지 않았습니다')
        if '정확한 시각에 울리기' not in t: fails.append('앱 알람: 정확한 시각 허용 단추가 없습니다')
        pn.click('#sc4 button:has-text("허용")'); pn.wait_for_timeout(600)
        if not all(x.get('isExactNotification') for x in pn.evaluate("()=>__LN.pending")): fails.append('앱 알람: 허용 뒤에도 정확 알람으로 다시 걸리지 않습니다')
        # 알림의 「먹었어요」 → 체크되고, 오늘 20:30 「아직 안 드셨어요」는 지워져야 한다
        pn.evaluate("()=>__LN.listeners.localNotificationActionPerformed({actionId:'took',notification:{extra:{key:'ibuprofen@20:00'}}})"); pn.wait_for_timeout(600)
        if 'ibuprofen@20:00' not in pn.evaluate("()=>takenSet()"): fails.append('앱 알람: 「먹었어요」가 체크로 이어지지 않습니다')
        if pn.evaluate("()=>__LN.pending.some(x=>x.schedule.at && new Date(x.schedule.at).getDate()===28 && new Date(x.schedule.at).getHours()===20)"):
            fails.append('앱 알람: 먹었다고 누른 뒤에도 오늘 「아직 안 드셨어요」가 남아 있습니다')
        if len([x for x in pn.evaluate("()=>__LN.pending") if x['schedule'].get('at')]) != 12: fails.append('앱 알람: 먹었어요 뒤 「아직 안 드셨어요」가 12개여야 합니다')
        pn.evaluate("()=>__LN.listeners.localNotificationActionPerformed({actionId:'later',notification:{title:'약지도 · 약 드실 시간',body:'x',extra:{key:'ibuprofen@08:00'}}})"); pn.wait_for_timeout(400)
        if not [x for x in pn.evaluate("()=>__LN.pending") if x['id'] >= 900000]: fails.append('앱 알람: 「10분 뒤 다시」가 걸리지 않습니다')
        if pn.evaluate("async()=>!!(navigator.serviceWorker && await navigator.serviceWorker.getRegistration())"): fails.append('앱 알람: 설치 앱에서 서비스워커가 등록됩니다')
        # 남은 알 수 10알·하루 2번 → 5일치 → 3일치 되는 날(9/30)·오늘 치만 남는 날(10/2) 아침 9시
        pn.evaluate("()=>{ME.stock={ibuprofen:{left:10,at:todayKey()}};saveMe();nativeArm();}"); pn.wait_for_timeout(600)
        rf = pn.evaluate("()=>__LN.pending.filter(x=>x.extra&&x.extra.stock).map(x=>{const d=new Date(x.schedule.at);return (d.getMonth()+1)+'/'+d.getDate()+' '+d.getHours()+'시 '+x.title})")
        if sorted(rf) != ['10/2 9시 약이 오늘 치만 남았어요', '9/30 9시 약이 3일치 남았어요']: fails.append(f'앱 알람: 약 떨어지기 전 알림이 틀립니다 — {rf}')
        # 기록 모두 지우기 — 기록·알람이 다 사라지고, 글자 크기 같은 보기 설정은 남는다
        pn.once('dialog', lambda dg: dg.accept())
        pn.evaluate("()=>localStorage.setItem('yakjido.fs','20px')")
        pn.evaluate("()=>wipeMe()"); pn.wait_for_timeout(600)
        w = pn.evaluate("()=>({t:(ME.taking||[]).length, p:__LN.pending.length, ls:localStorage.getItem('yakjido.me.v1'), fs:localStorage.getItem('yakjido.fs')})")
        if w['t'] or w['p'] or w['ls'] or w['fs'] != '20px': fails.append(f'기록 모두 지우기가 제대로 안 됩니다 — {w}')
        # 진료 예약 — 전날 19시·2시간 전
        pn.evaluate("()=>{ME.visits=[{id:'v1',at:'2026-10-02T10:30',where:'동네 내과'}];saveMe();nativeArm();}"); pn.wait_for_timeout(500)
        vv = pn.evaluate("()=>__LN.pending.filter(x=>x.extra&&x.extra.visit).map(x=>{const d=new Date(x.schedule.at);return (d.getMonth()+1)+'/'+d.getDate()+' '+d.getHours()+':'+d.getMinutes()}).sort()")
        if vv != ['10/1 19:0', '10/2 8:30']: fails.append(f'앱 알람: 진료 예약 알림이 틀립니다 — {vv}')
        # 혈압 재기 알림 — 켜면 매일 7:30·21:00 두 개
        pn.evaluate("()=>{ME.vitalRemind={bp:['07:30','21:00']};saveMe();nativeArm();}"); pn.wait_for_timeout(500)
        vr = pn.evaluate("()=>__LN.pending.filter(x=>x.extra&&x.extra.vitals).map(x=>x.schedule.on.hour+':'+x.schedule.on.minute).sort()")
        if vr != ['21:0', '7:30']: fails.append(f'앱 알람: 혈압 재기 알림이 틀립니다 — {vr}')
        if nerr: fails.append(f'앱 알람: JS 오류 {nerr[:2]}')
        pn.close()
        # 6b-2. 성분표에 없던 공공 제품 — 클로닉신(먹는 소염제 26개 제품)·돔페리돈이 약통에서 실제로 걸려야 한다(2026-09-23)
        _pb = {'노리스정 + 와파린': ({'taking':['pub:1','cls:blood.warf'],'pub':{'pub:1':{'name':'노리스정','full':'노리스정(클로닉신리시네이트)','ingr':'클로닉신리시네이트','rx':0,'seq':'1','drugId':''}}}, 'warfarin-nsaid'),
               '노리스정 + 이부프로펜': ({'taking':['pub:1','ibuprofen'],'pub':{'pub:1':{'name':'노리스정','full':'노리스정','ingr':'클로닉신리시네이트','rx':0,'seq':'1','drugId':''}}}, 'nsaid-dup'),
               '멕시롱 + 플루코나졸': ({'taking':['pub:1','pub:2'],'pub':{'pub:1':{'name':'멕시롱액','full':'멕시롱액(돔페리돈)','ingr':'돔페리돈','rx':0,'seq':'1','drugId':''},'pub:2':{'name':'디푸루칸','full':'디푸루칸캡슐(플루코나졸)','ingr':'플루코나졸','rx':1,'seq':'2','drugId':''}}}, 'domperidone-cyp3a4')}
        # 바르는·붙이는 제품은 먹는 약 계열로 읽으면 안 된다 — 그런데 키미테(스코폴라민 패치)는 몸으로 들어가는 약이라 그대로(2026-09-23)
        _pn = {'디클로페낙 파스 + 이부프로펜': ({'taking':['pub:1','ibuprofen'],'pub':{'pub:1':{'name':'게보핏파스','full':'게보핏스트롱카타플라스마(디클로페낙나트륨)','ingr':'디클로페낙나트륨','rx':0,'seq':'1','drugId':''}}}, 'nsaid-dup'),
               '디펜히드라민 크림 + 녹내장': ({'glaucoma':True,'taking':['pub:1'],'pub':{'pub:1':{'name':'가두벌크림','full':'가두벌크림','ingr':'디펜히드라민염산염 리도카인','rx':0,'seq':'1','drugId':''}}}, 'anticho-glaucoma'),
               '프레드니솔론 크림 + 이부프로펜': ({'taking':['pub:1','ibuprofen'],'pub':{'pub:1':{'name':'더마스톤지크림','full':'더마스톤지크림','ingr':'프레드니솔론아세테이트','rx':0,'seq':'1','drugId':''}}}, 'steroid-nsaid')}
        for _nm, (_me, _rid) in _pn.items():
            pg.evaluate("(me)=>localStorage.setItem('yakjido.me.v1',JSON.stringify(me))", _me); pg.reload(); ready(); pg.wait_for_timeout(300)
            if _rid in pg.evaluate("()=>ixRun().hits.map(h=>h.r.id)"): fails.append(f'바르는 약을 먹는 약으로 읽음: {_nm} → {_rid}')
        _pb['키미테 패치 + 녹내장'] = ({'glaucoma':True,'taking':['pub:1'],'pub':{'pub:1':{'name':'키미테패취','full':'키미테패취(스코폴라민)','ingr':'스코폴라민','rx':0,'seq':'1','drugId':''}}}, 'anticho-glaucoma')
        for _nm, (_me, _rid) in _pb.items():
            pg.evaluate("(me)=>localStorage.setItem('yakjido.me.v1',JSON.stringify(me))", _me); pg.reload(); ready(); pg.wait_for_timeout(300)
            if _rid not in pg.evaluate("()=>ixRun().hits.map(h=>h.r.id)"): fails.append(f'약통 판정 누락: {_nm} → {_rid}')
        pg.evaluate("localStorage.removeItem('yakjido.me.v1')")

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
        # 에텐자미드(근이완 복합제)는 소염 효과가 거의 없어 겹침으로 세지 않는다(현욱님 답, 2026-09-23) — 이제 겹치는 바구니는 0이어야 한다
        for sid, msgs in pdup.items():
            fails.append(f'추천 바구니가 스스로 겹침 {sid}: {msgs[0][:70]}')
        # 규칙이 죽지 않았는지 — 진짜 소염제 두 가지(이부프로펜+나프록센)는 여전히 잡혀야 하고, 이부프로펜+신신플렉스는 잡히면 안 된다
        _pd = pg.evaluate("""()=>[planDup([{d:drug('ibuprofen'),slot:'가'},{d:drug('naproxen'),slot:'나'}]).length, planDup([{d:drug('ibuprofen'),slot:'가'},{d:drug('relax-combo'),slot:'나'}]).length]""")
        if _pd[0] == 0: fails.append('소염제 두 가지(이부프로펜+나프록센) 겹침 경고가 사라짐 — 규칙이 죽었는지 확인')
        if _pd[1] != 0: fails.append('이부프로펜+신신플렉스에 겹침 경고가 뜸 — 현욱님 답과 어긋남')
        # 9. 날씨 카드
        pg.goto(url + '#/home'); pg.reload(); ready(); pg.wait_for_timeout(1000)
        wx = pg.evaluate("()=>document.querySelector('.wx')?.innerText||''")
        for kw in ['일교차', '14℃', '미세먼지', '나쁨']:
            if kw not in wx: fails.append(f'날씨 카드에 "{kw}" 없음: {wx[:80]!r}')
        # 9a. 기상청 모델이 값을 모두 비워(null) 보낼 때 — 0℃·일교차 「—」가 뜨던 것(2026-09-30 실측). 기본 모델로 넘어가야 한다
        pg.unroute('**/api.open-meteo.com/**')
        _NULL = json.dumps({'current': {'temperature_2m': None, 'apparent_temperature': None, 'relative_humidity_2m': None, 'weather_code': None}, 'daily': {'temperature_2m_max': [None], 'temperature_2m_min': [None]}})
        pg.route('**/api.open-meteo.com/**', lambda rt: rt.fulfill(status=200, content_type='application/json', body=_NULL if 'kma_seamless' in rt.request.url else FC))
        pg.evaluate("localStorage.removeItem('yakjido.wx.v1')"); pg.goto(url + '#/home'); pg.reload(); ready(); pg.wait_for_timeout(1500)
        wx = pg.evaluate("()=>document.querySelector('.wx')?.innerText||''")
        if '0℃' in wx.split('\n')[0][:4] or '일교차 —' in wx or '14℃' not in wx: fails.append(f'기상청 모델이 빈 값을 보낼 때 날씨가 틀립니다: {wx[:80]!r}')
        pg.unroute('**/api.open-meteo.com/**')
        pg.route('**/api.open-meteo.com/**', lambda rt: rt.fulfill(status=200, content_type='application/json', body=FC))
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
        #     우리집 소아과 계산기와 같은 식이다(현욱님 지시 2026-09-23) — 몸무게로 걸린 별도 한도는 두지 않는다.
        kd = pg.evaluate("()=>[[15,36],[8,5],[40,150],[10,20]].map(([w,m])=>['apap','ibu'].map(k=>{const r=kidDose(k,w,m);return [r.lo,r.hi,r.day]}))")
        want = [[[150, 225, 1125], [75, 150, 600]], [[80, 120, 480], [40, 80, 320]], [[400, 600, 3000], [200, 400, 1600]], [[100, 150, 600], [50, 100, 400]]]
        if kd != want: fails.append(f'소아 용량 계산 불일치: {kd} ≠ {want}')
        # 10b. 우리집 소아과와 같은 답인지 — 그 앱의 doseRange 를 그대로 옮긴 식과 몸무게 4~70 kg 전부 비교.
        #      그리고 「하루 1번」 같은 횟수 문장·맥시부펜 계산 카드가 다시 생기면 안 된다.
        pg.goto(url + '#/kids'); ready(); pg.wait_for_timeout(400)
        kc = pg.evaluate("""()=>{const DR={apap:{pk:[10,15],day:75,capDose:1000,capDay:4000},ibu:{pk:[5,10],day:40,capDose:400,capDay:2400}};
          const bad=[]; for(let w=4;w<=70;w+=0.5) for(const m of [12,48]) for(const k of ['apap','ibu']){ const D=DR[k];
            const perKg=(k==='apap'&&m<24)?60:D.day; const lo=Math.round(Math.min(w*D.pk[0],D.capDose)), hi=Math.round(Math.min(w*D.pk[1],D.capDose)), day=Math.round(Math.min(w*perKg,D.capDay));
            const r=kidDose(k,w,m); if(r.lo!==lo||r.hi!==hi||r.day!==day) bad.push(k+' '+w+'kg '+[r.lo,r.hi,r.day]+' ≠ '+[lo,hi,day]); }
          ME.age='child'; ME.child={name:'',birth:'2016-03-01',weight:28}; route();
          const txt=document.getElementById('view').innerText; ME.age='adult'; ME.child={}; saveMe();
          if(/씩이면\s*\d+번|번까지예요/.test(txt)) bad.push('횟수 문장이 남아 있음');
          if(document.querySelectorAll('.dose-card').length!==2) bad.push('용량 카드가 2장이 아님');
          if(!txt.includes('맥시부펜은 덱시부프로펜')) bad.push('맥시부펜 안내 없음');
          return bad;}""")
        if kc: fails.append(f'소아 계산이 우리집 소아과와 다릅니다: {kc[:3]}')
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
        # 붙여 쓴 말과 «처방약 이름»을 더 넣는다 — 낱말 맞추기가 띄어쓰기 있을 때만 돌아가서
        # 「허리아파요」가 0건이었고, 검색이 «빠른 묶음»을 안 봐서 「와파린」도 0건이었다(2026-09-23).
        SAY = ['타이 레놀', '이부 프로펜', '머리아파', '배아파', '목아파', '잠이안와', '소화제', '감기약', '무좀약', '변비약', '어지러워', '속쓰려',
               '허리아파요', '열나요', '어깨아파요', '기침나요', '무릎아파', '코가막혀요', '변비가있어요', '손이저려요', '잠못자요', '귀울림',
               '와파린', '혈압약', '당뇨약', '갑상선약', '콜레스테롤약', '전립선약', '디곡신', '메트포르민']
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
        # 8e. 자체 비판 3차(2026-09-30) — 새 약 화면을 사람들이 부르는 말로 찾을 수 있어야 하고, 엉뚱한 것이 끼면 안 된다.
        #     「안약」에 티눈이, 「멍빼는약」에 수면유도제가 떠 있었고 「빨간눈」·「간장약」은 0건이었다.
        SAY3 = {'안약': ('안약', '티눈'), '빨간눈': ('충혈', None), '간장약': ('우르소데옥시콜산', None), '간영양제': ('우르소데옥시콜산', None),
                '눈가려움': ('알레르기 안약', None), '각질': ('요소', None), '멍빼는약': ('멍', '독시라민'), '피임약': ('피임', None),
                '조루': ('리도카인', None), '흉터': ('흉터', None), '발톱무좀': ('네일라카', None), '우루사': ('우루사', None)}
        r8e = pg.evaluate("async(Q)=>{ await lexLoad(true); return Object.fromEntries(Q.map(q=>[q,search(q).slice(0,5).map(x=>x.t)])); }", list(SAY3))
        for q, (want, bad) in SAY3.items():
            got = r8e.get(q) or []
            if not any(want in t for t in got): fails.append(f'검색 "{q}" 상위 5개에 {want!r} 없음: {got}')
            if bad and any(bad in t for t in got): fails.append(f'검색 "{q}" 에 엉뚱한 {bad!r}: {got}')
        # 8f. 「하루 최대」는 숫자일 때만 — 「하루 최대 처방에 따름」이 65개 약에 떠 있었다
        r8f = pg.evaluate("""()=>(D.drugs||[]).filter(d=>d.dose).map(d=>{ const mx=d.dose.max||''; const rule=/세요|따르|달라져|줄이/.test(mx);
            const t=maxLine(mx,rule).replace(/<[^>]+>/g,''); return (/하루 최대 하루/.test(t) || /^하루 최대 [^\d약]/.test(t) || /^하루 최대 [\d.,~\s]+(일|주|개월|달|시간|년)/.test(t) || /하루 최대 [^·]*\/일/.test(t)) ? d.id+': '+t : null; }).filter(Boolean)""")
        if r8f: fails.append(f'「하루 최대」가 어색하게 붙은 약 {len(r8f)}개: {r8f[:4]}')
        # 8g. 안약·크림에 «먹는 약»이라고 쓰지 않는다
        r8g = pg.evaluate("()=>['eye-decongestant','allergy-eyedrop','urea-cream','scar-gel','artificial-tears','naftifine','ciclopirox-nail'].filter(id=>isOral(drug(id))).concat(['ibuprofen','udca','oral-contraceptive','tranexamic-melasma','diosmin'].filter(id=>!isOral(drug(id))).map(x=>'!'+x))")
        if r8g: fails.append(f'먹는 약/바르는 약 구분이 틀림: {r8g}')
        # 8h. 부작용 빈도의 「이렇게 하세요」 — 먹는 약 발진에 「그 자리는 쉬게」를 붙이지 않는다(2026-10-04)
        r8h = pg.evaluate("()=>{const t=id=>{const d=document.createElement('div');d.innerHTML=sideFreqHtml(drug(id));return [...d.querySelectorAll('.sf-tip')].map(x=>x.textContent).join('|')};const o=['cetirizine','domperidone','carbocisteine','antibiotic-eyedrop'].filter(id=>/그 자리/.test(t(id)));const s=['terbinafine','benzoyl-peroxide'].filter(id=>!/그 자리/.test(t(id))).map(x=>'!'+x);return o.concat(s)}")
        if r8h: fails.append(f'부작용 팁이 약 모양과 안 맞음: {r8h}')
        # 9a. 바깥 사진이 «뜬» 상태 — 샌드박스에선 식약처 사진이 안 떠서 사진 칸 규칙이 숨어 있었다(2026-10-06 글자가 44px 칸에 갇힘)
        import io as _io
        from PIL import Image as _Im
        _b = _io.BytesIO(); _Im.new('RGB', (140, 76), (200, 220, 230)).save(_b, 'PNG'); _PNG = _b.getvalue()
        _fake = lambda rt: rt.fulfill(status=200, content_type='image/png', body=_PNG) if rt.request.resource_type == 'image' and 'localhost' not in rt.request.url and '127.0.0.1' not in rt.request.url else rt.continue_()
        pg.route('**/*', _fake)
        for _r in ['/symptom/headache', '/symptom/cold', '/symptom/heartburn']:
            pg.goto(url + '#' + _r); pg.reload(); ready(); pg.wait_for_timeout(1500)
            _w = pg.evaluate("()=>[...document.querySelectorAll('.answer .buy>.buy-item.has-img .bi-t')].map(e=>Math.round(e.getBoundingClientRect().width))")
            if any(x < 120 for x in _w): fails.append(f'사진이 뜨면 약 카드 글자가 좁아집니다 {_r}: {_w}')
        for _r in ['/drug/gnalen', '/drug/topical-steroid']:
            pg.goto(url + '#' + _r); pg.reload(); ready(); pg.wait_for_timeout(800)
            pg.click('button.tab[data-p=p3]'); pg.wait_for_timeout(400)
            _o = pg.evaluate(OVERFLOW_JS)
            if _o['clip'] or _o['ov']: fails.append(f'사진이 뜨면 제품 칸 글자가 잘립니다 {_r}: {_o["clip"][:2]}{_o["ov"][:2]}')
        pg.unroute('**/*', _fake)
        br.close()
    print(f'화면 {len(routes)}개 검사 완료')
    if fails:
        print('실패', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
    print('✓ 전부 통과 — JS 오류 0 · 넘침 0 · 잘림 0 · 명암비 AA · 조작 부품 3:1 · 44px · 단추 누르기 · 복용 간격 · 복약 달력 · 홈 오늘약 · 어르신 소염제 · 소아 한도 · 계열 경고 · 어근 오인 · 내 정보 칸 · 화면 밝기 · 아이콘 전수 · 약 알림 · 어르신 모드 · 320px · 병용 8건 · 겹침 규칙 53 · 입력칸 이름표 · 성분 해석 123 · 죽은 규칙 0 · 약통 판정 4건 · 자기중복 3건 · 바구니 겹침 · 이중계산 0 · 검색 8건 · 구어 30건 · 문장 16건 · 새 약 검색 12건 · 하루 최대 표기 · 먹는/바르는 구분')

if __name__ == '__main__':
    main()
