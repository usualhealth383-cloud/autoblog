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

# 오프라인 검사용 — 브라우저 캐시를 못 쓰게(no-store) 하고, 검사 중에 «진짜로 꺼 버릴» 수 있는 서버.
# context.set_offline 은 서비스워커의 fetch 를 막지 못하고, 기본 서버는 브라우저가 휴리스틱 캐시로 메워 거짓 통과했다(2026-10-13 상용화 점검 5-01).
class _NoStore(_Quiet):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store'); super().end_headers()

def serve_nostore():
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(_NoStore, directory=str(DOCS)))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}/index.html'

CACHED_CORE_JS = "async()=>{ for (const k of await caches.keys()) { const ks = (await (await caches.open(k)).keys()).map(r=>r.url); if (ks.some(u=>/data\\/core\\.json/.test(u)) && ks.some(u=>/data\\/detail\\.json/.test(u))) return true; } return false; }"

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
    createChannel: async o => { (__LN.ch = __LN.ch || []).push(o); }, registerActionTypes: async o => { __LN.types = o; },
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
  for(const x of (D.supplements||[])) cands.push('supp:'+x.id);   /* 영양제도 내 약통에 담긴다 — 철분+제산제·와파린+코엔자임 Q10 규칙(10-13) */
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
    const fl=new Set([...(d.avoid||[]), ...(d.caution||[])].flatMap(a=>a.flags||[]));   /* 금기(avoid)든 주의(caution)든 «경고가 달려 있으면» 됨 — 소염제+항응고제는 주의(현욱님 10-13 「금기까지는 아니지, 의사 먼저 상의」) */
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

# Z6(2026-10-13 의사-피드백 §101) — 메디세이프처럼 알림을 잘, 어르신 약도. 단 「너무 자주 하면 안 된다 · 광고 알림 금지」(현욱님).
#   같은 시각 약은 한 장으로 묶기 · 30분 뒤 한 번만 · 하루 «시각 수 + 1»장 · 건너뛰기(놓침과 따로) · 10분 뒤 다시(앱·웹) ·
#   어르신 갈래(dose_senior) · 약 이름·알 수 글 · 저녁 정리(기본 꺼짐, 켠 분만) · 약 떨어짐 한 번 · 가족에게 알릴까요(앱 안에서만) · 알람 500개 한도
def alarm_z6(br, url, fails):
    zerr = []
    def page(me, t='2026-09-28T07:00:00', native=True):
        pz = br.new_page(viewport={'width': 390, 'height': 844}); pz.on('pageerror', lambda e: zerr.append(str(e)))
        pz.clock.install(time=t)
        if native: pz.add_init_script(CAP_MOCK)
        pz.add_init_script("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',%s)" % json.dumps(json.dumps(me)))
        pz.goto(url + '#/schedule?t=sc4'); pz.wait_for_selector('.app', timeout=15000); pz.wait_for_timeout(1500)
        return pz
    SR = {'age': 'senior', 'easy': True, 'taking': ['ibuprofen', 'acetaminophen'], 'sched': {'ibuprofen': ['08:00', '20:00'], 'acetaminophen': ['08:00']}, 'qty': {'acetaminophen': 2}, 'pub': {}}
    pz = page(SR)
    P = lambda: pz.evaluate("()=>__LN.pending")
    L = P(); dose = [x for x in L if x.get('actionTypeId') == 'dose']
    on = [x for x in L if x.get('title') == '약지도 · 약 드실 시간']; ag = [x for x in L if x.get('title') == '아직 안 드셨어요']
    if any(x.get('channelId') != 'dose_senior' for x in dose): fails.append('Z6 알림: 어르신 모드 복용 알림이 어르신 갈래(dose_senior)로 가지 않습니다')
    chs = pz.evaluate("()=>(__LN.ch||[]).map(c=>c.id+':'+c.visibility+':'+c.importance)")
    if 'dose_senior:1:5' not in chs or 'dose2:0:5' not in chs: fails.append(f'Z6 알림: 알림 갈래가 틀립니다 — {chs}')
    # 같은 시각 약은 한 장 — 08:00 은 두 약이 한 장, 7일 × 시각 2개 = 14
    if len(on) != 14: fails.append(f'Z6 알림: 같은 시각 약을 한 장으로 묶지 않았습니다 — 제시간 알림 {len(on)}개(14개여야)')
    m8 = [x for x in on if x['body'].startswith('아침 8시 약')]
    if not m8 or sorted(m8[0]['extra'].get('keys') or []) != ['acetaminophen@08:00', 'ibuprofen@08:00']: fails.append(f'Z6 알림: 08:00 알림이 두 약을 함께 담지 않습니다 — {m8[:1]}')
    if m8 and ('2알' not in m8[0]['body'] or '이부프로펜' not in m8[0]['body'] or '물 한 컵과 함께' not in m8[0]['body']): fails.append(f'Z6 알림: 어르신 알림 글이 「아침 8시 약 — 이름 알 수」·물 한 컵 꼴이 아닙니다 — {m8[0]["body"]}')
    e8 = [x for x in on if x['body'].startswith('저녁 8시 약')]
    if not e8 or '물 한 컵' in e8[0]['body']: fails.append(f'Z6 알림: 물 그림이 없는 약(이부프로펜만)에 「물 한 컵」이 붙었습니다 — {e8[:1]}')
    # 어르신도 더 자주가 아니다 — 다시 알림은 30분 뒤 한 번뿐
    mins = sorted({pz.evaluate("(a)=>new Date(a).getMinutes()", x['schedule']['at']) for x in ag})
    if mins != [30]: fails.append(f'Z6 알림: 다시 알림이 30분 뒤 한 번이 아닙니다 — 분 {mins}')
    perday = pz.evaluate("()=>{const c={};for(const x of __LN.pending){if(x.id>=900000||!x.schedule.at)continue;const d=new Date(x.schedule.at);const k=d.getMonth()+'-'+d.getDate();c[k]=(c[k]||0)+1;}return c;}")
    if max(perday.values()) > 3: fails.append(f'Z6 알림: 하루 알림이 «시각 수 + 1»(3장)을 넘습니다 — {perday}')
    if any(x.get('title') == '오늘 약 체크' for x in L): fails.append('Z6 알림: 저녁 하루 정리가 어르신에게도 기본으로 켜져 있습니다(기본 꺼짐)')
    # 광고·홍보성 알림 0 — 제목은 정해진 것만
    OK_T = {'약지도 · 약 드실 시간', '아직 안 드셨어요', '알림을 이어 가려면 약지도를 한 번 열어 주세요', '약이 5일분쯤 남았어요', '오늘 약 체크', '내일 진료가 있어요', '2시간 뒤 진료예요', '약지도 · 혈압 잴 시간'}
    bad = sorted({x.get('title') for x in L if x.get('title') not in OK_T})
    if bad: fails.append(f'Z6 알림: 정해지지 않은 알림 제목(광고·홍보 금지) — {bad}')
    # 저녁 정리 켜기 → 오늘 21:00 「체크하지 않은 약이 3번」, 08:00 「먹었어요」 → 1번, 20:00 건너뛰기 → 오늘 정리 사라짐
    pz.evaluate("()=>setEvening(true)"); pz.wait_for_timeout(500)
    ev = lambda: [x for x in P() if x.get('title') == '오늘 약 체크']
    e0 = [x for x in ev() if x['id'] == 590000]
    if not e0 or '3번' not in e0[0]['body'] or pz.evaluate("(a)=>new Date(a).getHours()", e0[0]['schedule']['at']) != 21: fails.append(f'Z6 알림: 저녁 9시 하루 정리가 틀립니다 — {e0}')
    pz.evaluate("()=>__LN.listeners.localNotificationActionPerformed({actionId:'took',notification:{extra:{key:'ibuprofen@08:00',keys:['ibuprofen@08:00','acetaminophen@08:00']}}})"); pz.wait_for_timeout(600)
    if sorted(pz.evaluate("()=>takenSet()")) != ['acetaminophen@08:00', 'ibuprofen@08:00']: fails.append('Z6 알림: 묶은 알림의 「먹었어요」가 두 약을 함께 체크하지 않습니다')
    e0 = [x for x in ev() if x['id'] == 590000]
    if not e0 or '1번' not in e0[0]['body']: fails.append(f'Z6 알림: 체크 뒤 저녁 정리 개수가 맞지 않습니다 — {e0}')
    pz.evaluate("()=>__LN.listeners.localNotificationActionPerformed({actionId:'skip',notification:{extra:{key:'ibuprofen@20:00',keys:['ibuprofen@20:00'],day:todayKey()}}})"); pz.wait_for_timeout(600)
    sk = pz.evaluate("()=>({s:(ME.skipped||{})[todayKey()]||[], t:takenSet(), st:dayStat(todayKey()).s, left:__LN.pending.filter(x=>x.schedule.at&&new Date(x.schedule.at).getDate()===28&&x.id<900000).map(x=>x.title)})")
    if sk['s'] != ['ibuprofen@20:00'] or 'ibuprofen@20:00' in sk['t']: fails.append(f'Z6 건너뛰기: 건너뛴 회차가 따로 적히지 않습니다 — {sk}')
    if sk['st'] != 'skip': fails.append(f'Z6 건너뛰기: 남은 회차를 다 건너뛴 날이 skip 이 아닙니다 — {sk["st"]}')
    if sk['left']: fails.append(f'Z6 건너뛰기: 건너뛴 뒤에도 오늘 알림이 남아 있습니다 — {sk["left"]}')
    # 「10분 뒤 다시」 — 어르신 갈래로 다시
    pz.evaluate("()=>__LN.listeners.localNotificationActionPerformed({actionId:'later',notification:{title:'약지도 · 약 드실 시간',body:'x',extra:{key:'ibuprofen@20:00',keys:['ibuprofen@20:00']}}})"); pz.wait_for_timeout(400)
    sn = [x for x in P() if x['id'] >= 900000 and x['id'] < 999990]
    if not sn or sn[0].get('channelId') != 'dose_senior' or (sn[0].get('extra') or {}).get('keys') != ['ibuprofen@20:00']: fails.append(f'Z6 알림: 「10분 뒤 다시」가 틀립니다 — {sn[:1]}')
    # 복용률 — 건너뛴 것은 먹은 것으로 세지 않고 따로
    a = pz.evaluate("()=>{const y=dayBefore(1);ME.days[y]={n:2,s:{'08:00':1,'20:00':1}};ME.taken[y]=['ibuprofen@08:00'];ME.skipped[y]=['ibuprofen@20:00'];return adherence(30);}")
    if a.get('took') != 1 or a.get('skip') != 1 or a.get('full') != 0: fails.append(f'Z6 건너뛰기: 복용률이 건너뛴 것을 먹은 것으로 셉니다 — {a}')
    pz.goto(url + '#/schedule?t=sc3'); pz.wait_for_timeout(500)
    pz.evaluate("()=>calPick(dayBefore(1))"); pz.wait_for_timeout(300)
    cd = pz.inner_text('#cal-day') if pz.query_selector('#cal-day') else ''
    if '건너뜀' not in cd: fails.append(f'Z6 건너뛰기: 달력에서 건너뛴 회차가 「건너뜀」으로 보이지 않습니다 — {cd[:120]}')
    if '건너뜀' not in pz.inner_text('.cal-key'): fails.append('Z6 건너뛰기: 달력 표에 「건너뜀」이 없습니다')
    # 저장 꼴 — skipped 는 「id@HH:MM」 배열만, evening 은 참/거짓
    sm = pz.evaluate("()=>sanitizeMe({skipped:{'2026-09-27':['ibuprofen@20:00','x<y@08:00',3,'ibuprofen@20:00'],'bad':['a@08:00']},evening:true,qty:{a:'2'}})")
    if sm.get('skipped') != {'2026-09-27': ['ibuprofen@20:00']} or sm.get('evening') is not True: fails.append(f'Z6 저장 꼴: skipped·evening 이 바로잡히지 않습니다 — {sm.get("skipped")} {sm.get("evening")}')
    # 약 떨어짐 — 하루 1번 약 6알 → 남을 날 6일 → 5일분 되는 내일 9시 한 번. 이미 5일분 안쪽(4알)이면 알림 없이 넣을 때 바로 말씀
    pz.evaluate("()=>{ME.stock={acetaminophen:{left:12,at:todayKey()}};saveMe();nativeArm();}"); pz.wait_for_timeout(500)
    rf = pz.evaluate("()=>__LN.pending.filter(x=>x.extra&&x.extra.stock).map(x=>x.title+'|'+x.body)")
    if len(rf) != 1 or '5일분쯤 남았어요 — 미리 처방·구입해 두세요' not in rf[0]: fails.append(f'Z6 약 떨어짐: 알림이 한 번이 아니거나 글이 틀립니다 — {rf}')
    pz.close()
    # 알람 한도 — 어르신 · 약 60개 × 하루 4번(같은 시각) / 약 60개 × 서로 다른 240개 시각 둘 다 500개 아래
    for nm, mk in [('60개 × 4번', "(ids)=>{const s={};ids.forEach(id=>s[id]=['08:00','13:00','19:00','22:00']);return s;}"),
                   ('60개 × 다른 시각 240개', "(ids)=>{const s={};ids.forEach((id,i)=>s[id]=[0,1,2,3].map(j=>{const m=(i*4+j)*5+300;return String(Math.floor(m/60)%24).padStart(2,'0')+':'+String(m%60).padStart(2,'0')}));return s;}")]:
        pz = page({'age': 'senior', 'easy': True, 'evening': True, 'pub': {}})
        n = pz.evaluate("async(mk)=>{const ids=D.drugs.slice(0,60).map(d=>d.id);ME.taking=ids;ME.sched=(eval(mk))(ids);ME.stock={};ids.forEach(id=>ME.stock[id]={left:40,at:todayKey()});ME.visits=[{id:'v1',at:'2026-10-01T10:30',where:'x'}];ME.vitalRemind={bp:['07:30','21:00']};saveMe();await nativeArm();"
                        "const c={};for(const x of __LN.pending){if(!x.schedule.at||x.id>=900000)continue;if(x.extra&&(x.extra.visit||x.extra.vitals))continue;const d=new Date(x.schedule.at);const k=d.getMonth()+'-'+d.getDate();c[k]=(c[k]||0)+1;}"
                        "return {n:__LN.pending.length, slots:new Set(Object.values(ME.sched).flat()).size, max:Math.max(...Object.values(c)), on:__LN.pending.filter(x=>x.title==='약지도 · 약 드실 시간').length};}", mk)
        if n['n'] > 500: fails.append(f'Z6 알람 한도({nm}): 휴대폰 알람 {n["n"]}개 — 500개를 넘습니다')
        if n['max'] > n['slots'] + 1: fails.append(f'Z6 알람 한도({nm}): 하루 {n["max"]}장 — 시각 수 + 1({n["slots"] + 1})을 넘습니다')
        if n['on'] < 1: fails.append(f'Z6 알람 한도({nm}): 제시간 알림이 없습니다')
        pz.close()
    # 일반 모드 — 비공개 갈래 dose2 그대로, 약 이름 없이 「아침 8시」
    pz = page({'taking': ['ibuprofen', 'acetaminophen'], 'sched': {'ibuprofen': ['08:00'], 'acetaminophen': ['08:00']}, 'pub': {}})
    L = P()
    if any(x.get('channelId') != 'dose2' for x in L if x.get('actionTypeId') == 'dose'): fails.append('Z6 알림: 일반 모드가 비공개 갈래(dose2)가 아닙니다')
    if any('이부프로펜' in x.get('body', '') or '타이레놀' in x.get('body', '') for x in L): fails.append('Z6 알림: 일반 모드 알림에 약 이름이 보입니다')
    if '광고 알림은 보내지 않아요' not in pz.evaluate("()=>document.querySelector('#sc4').textContent"): fails.append('Z6 알림: 알림 칸에 「광고 알림은 보내지 않아요」가 없습니다')
    pz.close()
    # 웹 — 묶은 알림 · 30분 뒤 한 번 · 10분 뒤 다시(창이 타이머) · 하루 상한
    pw = page(SR, '2026-09-28T07:58:00', native=False)
    pw.evaluate("()=>{window.__F=[];window.showNote=(t,b,k,d,p)=>__F.push(t+'|'+k);Object.defineProperty(Notification,'permission',{get:()=>'granted'});armNotifications();}")
    pw.clock.run_for(40 * 60000); pw.wait_for_timeout(200)
    F = pw.evaluate("()=>__F")
    if F != ['약지도 · 약 드실 시간|ibuprofen@08:00,acetaminophen@08:00', '아직 안 드셨어요|ibuprofen@08:00,acetaminophen@08:00']: fails.append(f'Z6 웹 알림: 08:00 묶은 알림·08:30 다시 알림이 틀립니다 — {F}')
    pw.evaluate("()=>{__F.length=0;webSnooze('ibuprofen@20:00',todayKey(),'약지도 · 약 드실 시간','x');}")
    pw.clock.run_for(11 * 60000); pw.wait_for_timeout(200)
    if pw.evaluate("()=>__F") != ['약지도 · 약 드실 시간|ibuprofen@20:00']: fails.append(f'Z6 웹 알림: 「10분 뒤 다시」가 10분 뒤 울리지 않습니다 — {pw.evaluate("()=>__F")}')
    sws = (DOCS / 'sw.js').read_text(encoding='utf-8')
    if "yakjido-later" not in sws or "action === 'later'" not in sws: fails.append('Z6 웹 알림: 서비스워커가 「10분 뒤 다시」를 처리하지 않습니다')
    pw.close()
    # 홈 — 어르신이 2시간 넘게 체크하지 않은 회차 → 「가족에게 알릴까요」(앱 안에서만) · 괜찮아요 · 먹었어요
    ph = page(SR, '2026-09-28T10:30:00')
    ph.goto(url + '#/home'); ph.wait_for_timeout(600)
    if not ph.query_selector('.dh-fam'): fails.append('Z6 가족: 2시간 넘게 체크 안 한 회차에 「가족에게 알리기」가 없습니다')
    else:
        ph.click('.dh-fam .x'); ph.wait_for_timeout(300)
        if ph.query_selector('.dh-fam'): fails.append('Z6 가족: 「괜찮아요」를 눌러도 다시 묻습니다')
    if any('가족' in (x.get('title', '') + x.get('body', '')) for x in ph.evaluate("()=>__LN.pending")): fails.append('Z6 가족: 가족 알림이 휴대폰 알림으로 걸렸습니다(앱 안에서만)')
    # 복용 시간 화면 — 지난 회차 건너뛰기 단추(접이 안)
    ph.goto(url + '#/schedule'); ph.wait_for_timeout(500)
    ph.evaluate("()=>document.querySelectorAll('details.why-more').forEach(d=>d.open=true)")
    b = ph.query_selector('.skip-l button')
    if not b: fails.append('Z6 건너뛰기: 복용 시간 화면에 지난 회차 「건너뛰기」 단추가 없습니다')
    else:
        b.click(); ph.wait_for_timeout(400)
        if not ph.evaluate("()=>((ME.skipped||{})[todayKey()]||[]).length") or not ph.query_selector('.dose-tick.skip'): fails.append('Z6 건너뛰기: 단추를 눌러도 건너뜀으로 적히지 않습니다')
    ph.close()
    if zerr: fails.append(f'Z6 알림: JS 오류 {zerr[:2]}')

# Z7(실사용 검수 2차 audit2 — 2026-10-13) — 약국 카드·내 약통·아이 나이·내 몸 조건이 실제 제품으로 다시 깨지지 않게.
#   A1 「이 중 하나만」 묶음은 카드·보내기·메모에 하나만 · A2 내 약통은 «성분»으로 견줌(타이레놀 → 콜대원 겹침) ·
#   A3 낱알 검색으로 담은 판콜에이캡슐·펜잘의 성분 · 성분 모름이면 안심 문장 없음 · A4 아이 2개월·5개월·4세·14세 ·
#   A5 「아이 ○ kg 기준」 한 줄의 나이 규칙 · A6 열 「소아」 칸은 어린이 제품 · B5·B6 신장 + 마그밀, 항응고제 + 부루펜(§101 한 줄) ·
#   B8 응급 신호 체크 시 「두 가지」 칸·용량 숨김 · B10 기침 카드에 고르지 않은 파모티딘 없음
def z7_checks(br, url, fails):
    zerr = []
    pz = br.new_page(viewport={'width': 390, 'height': 844}); pz.on('pageerror', lambda e: zerr.append(str(e)))
    pz.add_init_script("localStorage.setItem('yakjido.hello.v1','1')")
    pz.goto(url + '#/home'); pz.wait_for_function("()=>typeof CORE!=='undefined' && CORE===2", timeout=20000)
    pz.evaluate("async()=>{ await pubIndex(); await pubPills(); await lexLoad(true); }")
    RESET = """()=>{ for (const k of Object.keys(FLAG_LABEL)) if (k!=='senior'&&k!=='child') ME[k]=false; ME.age='adult'; ME.child=null; ME.taking=[]; ME.pub={}; ME.prn={}; ME.allergy=[]; ME.allergyUnknown=false; for (const k in EITHER_PICK) delete EITHER_PICK[k]; for (const k in OPT_PICK) delete OPT_PICK[k]; saveMe(); }"""
    ADD = "n=>{ const i=(PUB.index||[]).findIndex(p=>pubNorm(p.n).startsWith(pubNorm(n))); if (i<0) return ''; addPubIx(i); return PUB.index[i].n; }"
    def go(h):
        pz.evaluate("h=>{ location.hash=h; route(); }", h); pz.wait_for_timeout(60)
    def txt(sel='#view'):
        return pz.evaluate("s=>[...document.querySelectorAll(s)].filter(e=>e.getClientRects().length).map(e=>e.innerText).join(' | ')", sel)
    # A1 — 감기·열 약국 카드: 묶음은 하나만, 카드 안 성분 겹침 0, 「또는」 바꾸기, 보내기·메모도 하나만
    pz.evaluate(RESET)
    a1 = pz.evaluate("""()=>{ const bad=[]; const keys=sid=>{ const s=byId(D.symptoms,sid); return showable(basketPicked(s,basket(s))).filter(x=>!x.have&&!x.again).map(x=>drugKeys(x.d)); };
      for (const sid of ['cold','fever','headache','msk','deworm']) { const ks=keys(sid).flat(); const dup=ks.filter((k,i)=>ks.indexOf(k)!==i); if (dup.length) bad.push(sid+' 카드 안 같은 성분: '+dup.join(',')); }
      const s=byId(D.symptoms,'cold'); const ids=showable(basketPicked(s,basket(s))).map(x=>x.d.id); if (ids.includes('acetaminophen') && ids.includes('coldaewon')) bad.push('감기 카드에 아세트아미노펜과 콜대원이 함께');
      const m=memoText(s); if (/아세트아미노펜 —/.test(m) && /\\n· 콜대원/.test(m)) bad.push('메모에 묶음 둘 다');
      const sd=sendItems({s:'cold'}).map(x=>x.id); if (sd.includes('acetaminophen') && sd.includes('coldaewon')) bad.push('보내기에 묶음 둘 다');
      location.hash='#/show/fever'; route(); const n1=document.querySelectorAll('.show-list li:not(.show-have) .n').length; if (n1!==1) bad.push('열 카드 번호 줄이 '+n1+'개');
      const sw=document.querySelector('.show-sw'); if (!sw) bad.push('열 카드에 「또는 … 바꾸기」 단추 없음'); else { sw.click(); const t=document.querySelector('.show-list').innerText; if (!/소아/.test(t)) bad.push('바꾸기를 눌러도 소아 칸으로 안 바뀜'); }
      location.hash='#/show/deworm'; route(); if (document.querySelectorAll('.show-list li .n:not([aria-hidden])').length!==1) bad.push('구충제 카드에 알벤다졸이 두 번 번호로');
      return bad; }""")
    if a1: fails.append(f'Z7 A1 묶음 하나만: {a1[:4]}')
    # A2 — 내 약통 타이레놀정500 → 감기 카드에 아세트아미노펜이 든 약을 표시 없이 1번으로 권하지 않는다
    pz.evaluate(RESET); tn = pz.evaluate(ADD, '타이레놀정500')
    a2 = pz.evaluate("""()=>{ const bad=[]; for (const sid of ['cold','fever','headache']) { const s=byId(D.symptoms,sid); for (const x of showable(basketPicked(s,basket(s)))) if (!x.have && !x.cab && drugKeys(x.d).includes('acetaminophen')) bad.push(sid+': '+x.d.id+' (아세트아미노펜) 표시 없이 권함'); }
      eitherSet('cold', 1); location.hash='#/show/cold'; route(); const t=document.querySelector('.show-list').innerText; if (/콜대원/.test(t) && !/같은 성분\\(아세트아미노펜\\)/.test(t)) bad.push('콜대원을 골랐는데 「드시는 타이레놀과 같은 성분」 표시 없음');
      location.hash='#/symptom/cold'; route(); if (!/아세트아미노펜/.test((document.querySelector('.dupbox')||{}).innerText||'')) bad.push('감기 화면 확인 상자에 아세트아미노펜 겹침 없음');
      return bad; }""")
    if not tn: fails.append('Z7 A2: 타이레놀정500을 e약은요에서 못 찾음')
    if a2: fails.append(f'Z7 A2 성분으로 견주기: {a2[:3]}')
    # A3 — 낱알 검색(#/pill) → 「내 약통에 담기」 → 같이 먹어도 되나요
    pz.evaluate(RESET)
    for nm in ['판콜에이캡슐', '펜잘']:
        go('#/pill'); pz.fill('#pq', nm); pz.wait_for_timeout(700)
        pz.evaluate("n=>{ const c=[...document.querySelectorAll('.pill-cw')].find(e=>e.querySelector('.pill-card b').innerText.replace(/\\s/g,'').startsWith(n)); c && c.querySelector('.pc-take').click(); }", nm)
        pz.wait_for_timeout(500)
    pz.evaluate(ADD, '타이레놀정500'); pz.evaluate("()=>pubIngrFill()")
    a3 = pz.evaluate("()=>Object.values(ME.pub).map(x=>({n:x.name, i:x.ingr}))")
    pc = [x for x in a3 if x['n'].startswith('판콜에이캡슐')]
    if not pc: fails.append(f'Z7 A3: 낱알 검색에서 판콜에이캡슐을 담지 못함 {a3}')
    elif '아세트아미노펜' not in pc[0]['i']: fails.append(f'Z7 A3: 판콜에이캡슐 성분이 비어 있음 — {pc[0]}')
    if not any(x['n'].startswith('펜잘') for x in a3): fails.append(f'Z7 A3: 낱알 검색에서 펜잘을 담지 못함 {a3}')
    go('#/together'); t = txt()
    if pc and '아세트아미노펜' in pc[0]['i'] and '아세트아미노펜' not in t: fails.append('Z7 A3: 판콜에이캡슐 + 타이레놀정500인데 아세트아미노펜 겹침이 안 뜸')
    pz.evaluate(RESET); pz.evaluate(ADD, '타이레놀정500')
    pz.evaluate("()=>{ ME.taking.push('pub:z7x'); ME.pub['pub:z7x']={name:'모르는감기캡슐',full:'모르는감기캡슐',ingr:'',rx:0,seq:'',drugId:''}; saveMe(); }")
    go('#/together'); t = txt('.ix-sum')
    if '걸리는 조합' in t or '성분을 몰라 겹침을 확인하지 못했어요' not in t: fails.append(f'Z7 A3: 성분 모름 약이 있는데 머리말이 분명하지 않음 — {t[:80]}')
    # A4·A5·A6 — 아이 나이(2개월·5개월·4세·14세·생년월일 없음)
    a4 = pz.evaluate("""()=>{ const bad=[]; const bd=m=>{ const d=new Date(); d.setMonth(d.getMonth()-m); d.setDate(d.getDate()-1); return d.toISOString().slice(0,10); };
      const kid=(m,w)=>{ ME.age='child'; ME.child={name:'',birth:m==null?'':bd(m),weight:w}; saveMe(); };
      const ids=sid=>{ const s=byId(D.symptoms,sid); return basket(s).map(x=>x.d); };
      kid(2,5); location.hash='#/symptom/fever'; route();
      if (!document.querySelector('.inf-stop') || document.querySelector('.answer .buy-item')) bad.push('2개월 열: 「진료가 먼저」 대신 약 목록');
      location.hash='#/show/fever'; route(); if (document.querySelector('.show-list li')) bad.push('2개월 열: 약국 카드에 약');
      location.hash='#/symptom/headache'; route(); if (!/3개월 미만/.test((document.querySelector('.answer .kid-line')||{}).innerText||'')) bad.push('2개월: 「아이 kg 기준」 줄에 3개월 미만 안내 없음');
      for (const sid of ['cold','fever','headache','allergy']) if (ids(sid).some(isNsaid)) bad.push('2개월 '+sid+': 소염진통제를 권함');
      kid(5,7); for (const sid of ['cold','fever','headache','msk']) if (ids(sid).some(isNsaid)) bad.push('5개월 '+sid+': 소염진통제(이부프로펜 등)를 권함');
      location.hash='#/symptom/fever'; route(); const k5=(document.querySelector('.answer .kid-line')||{}).innerText||''; if (!/이부프로펜 시럽은 생후 6개월부터/.test(k5)) bad.push('5개월: kg 줄에 이부프로펜 6개월 안내 없음 — '+k5.slice(0,60));
      kid(48,16); location.hash='#/symptom/fever'; route(); if (!/설명서 표/.test([...document.querySelectorAll('.answer .kid-over')].map(e=>e.innerText).join(''))) bad.push('4세 16 kg: 이부프로펜 설명서 표 넘음 경고 없음');
      for (const sid of ['cold','allergy','cough','constipation','diarrhea']) for (const x of basket(byId(D.symptoms,sid))) { if (/500 ?mg|정$|캡슐/.test(x.product||'') && !kidAdultOk(x.d)) bad.push('4세 '+sid+': 어른 제품 '+x.product); if (minAgeOf(x.d)!=null && minAgeOf(x.d)>48) bad.push('4세 '+sid+': '+x.d.id+'('+minAgeOf(x.d)+'개월부터)'); }
      kid(168,50); for (const sid of ['allergy','diarrhea','cold']) for (const x of basket(byId(D.symptoms,sid))) if ((x.why||[]).includes('child') && minAgeOf(x.d)!=null) bad.push('14세 '+sid+': 나이 기준이 있는데 「소아」로 막음 '+x.d.id);
      kid(null,5); location.hash='#/symptom/fever'; route(); if (!/생후 3개월 안팎/.test([...document.querySelectorAll('.answer .kid-over')].map(e=>e.innerText).join(''))) bad.push('생년월일 없음 5 kg: 「생후 3개월 안팎」 경고 없음');
      ME.age='adult'; ME.child=null; saveMe(); location.hash='#/symptom/fever'; route();
      const kidRow=[...document.querySelectorAll('.answer .buy-item')].find(b=>/소아/.test((b.querySelector('.role')||{}).innerText||''));
      if (!kidRow || /500 ?mg|세토펜정/.test(kidRow.innerText) || !/어린이/.test(kidRow.innerText)) bad.push('어른 모드 열 「소아」 칸: '+(kidRow?kidRow.innerText.replace(/\\n/g,' / '):'없음'));
      return bad; }""")
    if a4: fails.append(f'Z7 A4·A5·A6 아이 나이: {a4[:5]}')
    # B5·B6 — 내 몸 조건: 신장 + 마그밀(빨강), 항응고제 + 부루펜(§101 주의 한 줄 — 증상 화면·약국 카드·같이 먹어도 되나요)
    AC = '금기는 아니지만 위장관 출혈 가능성이 있어 주의해요. 처방한 의사와 먼저 상의하세요'
    pz.evaluate(RESET); pz.evaluate("()=>{ ME.kidney=true; saveMe(); }"); pz.evaluate(ADD, '마그밀정')
    go('#/together'); t = txt('.ix.stop')   # 병용 규칙(kidney-mg)이 말하든, 내 몸 조건 칸이 말하든 빨강이면 된다
    if '마그밀' not in t or '걸리는 조합은 나오지 않았어요' in txt(): fails.append('Z7 B5: 신장 질환 + 마그밀정인데 빨강(먹지 말 것) 판정이 없음')
    pz.evaluate(RESET); pz.evaluate("()=>{ ME.anticoag=true; saveMe(); }"); pz.evaluate(ADD, '부루펜정')
    go('#/together'); t = txt()
    if AC not in t: fails.append('Z7 B6: 항응고제 + 부루펜정인데 §101 주의 한 줄이 같이 먹어도 되나요에 없음')
    if '같이 드시면 안 돼' in t or '내 몸 조건과 맞지 않는' in t: fails.append('Z7 B6: 항응고제 + 부루펜이 «금기»처럼 나옴(§101 은 주의)')
    pz.evaluate("()=>{ ME.taking=[]; ME.pub={}; saveMe(); }")
    go('#/symptom/msk'); t = txt('.answer .buy')
    if AC not in t: fails.append('Z7 B6: 항응고제 조건에서 근육통 화면 소염제 칸에 주의 한 줄 없음')
    go('#/show/msk'); t = txt('.show-list')
    if AC not in t: fails.append('Z7 B6: 항응고제 조건에서 약국 카드 소염제 줄에 주의 한 줄 없음')
    # B8 — 응급 신호 체크 → 「두 가지(함께·번갈아)」 칸·아이 용량 줄도 숨김
    pz.evaluate(RESET); pz.evaluate("()=>{ ME.age='child'; ME.child={name:'',birth:'',weight:12}; saveMe(); }")
    go('#/symptom/fever')
    b8 = pz.evaluate("""()=>{ const v=s=>[...document.querySelectorAll(s)].some(e=>e.getClientRects().length>0); const before=v('.answer .med-tip');
      document.querySelector('.rf input[type=checkbox]').click();
      return {before, tip:v('.med-tip'), kid:v('.answer .kid-line')||v('.answer .kid-over'), doTwo:[...document.querySelectorAll('.care-do')].some(e=>/번갈아/.test(e.innerText))}; }""")
    if not b8['before']: fails.append('Z7 B8: 열 화면에 「두 가지 — 함께·번갈아」 접이가 없음(체크 전)')
    if b8['tip'] or b8['kid'] or b8['doTwo']: fails.append(f'Z7 B8: 응급 신호 체크 뒤에도 약 쓰는 법·용량이 보임 {b8}')
    # B10 — 고르지 않은 보조 칸(파모티딘)은 기침 약국 카드·보내기에 가지 않는다
    pz.evaluate(RESET); go('#/show/cough'); t = txt('.show-list')
    if '파모티딘' in t: fails.append('Z7 B10: 기침 약국 카드에 고르지 않은 파모티딘이 들어감(자료 cough.plan 「신물」 칸 optional — 내용 조 몫)')
    # 내용 조 X4 뒤 부모 요청 — ageAskMonths 한 줄(막지 않음) · 아이 모드 성인 칸 숨김 · 제품 용법(아스피린프로텍트) · 자료 확인 중 도장 · 검색 · 코 스프레이는 코막힘 겹침으로 세지 않음
    pz.evaluate(RESET)
    z = pz.evaluate("""async()=>{ const bad=[]; const bd=m=>{ const d=new Date(); d.setMonth(d.getMonth()-m); d.setDate(d.getDate()-1); return d.toISOString().slice(0,10); };
      ME.age='child'; ME.child={name:'',birth:bd(10),weight:9}; saveMe();
      const bk=basket(byId(D.symptoms,'fever')); const ap=bk.find(x=>x.d.id==='acetaminophen');
      if (bk.some(x=>/성인/.test(x.slot))) bad.push('아이 모드 열에 성인 칸');
      if (Number.isFinite(drug('acetaminophen').ageAskMonths) && !(ap && /의사·약사와 상의/.test(ap.cau||'') && !ap.blocked)) bad.push('10개월 아세트아미노펜: ageAskMonths 「상의」 한 줄 없음(또는 막음) '+JSON.stringify(ap&&{c:ap.cau,b:ap.blocked}));
      ME.age='adult'; ME.child=null; ME.taking=[]; ME.pub={}; const i=(PUB.index||[]).findIndex(p=>pubNorm(p.n).startsWith('아스피린프로텍트')); if (i>=0) { addPubIx(i); const it=takingItems()[0]; if (!/하루 1번/.test(it.simple||'') || /500 ?mg/.test(it.simple||'')) bad.push('아스피린프로텍트 용법이 제품 용법이 아님: '+it.simple); } else bad.push('아스피린프로텍트를 e약은요에서 못 찾음');
      await lexLoad(true); const u=(LEX.ing||[]).find(x=>x.unv && !(x.drug && drug(x.drug))); if (u) { location.hash='#/ingr/'+u.id; route(); if (!/자료 확인 중/.test((document.querySelector('.review-stamp')||{}).innerText||'')) bad.push('unv 성분 화면에 「자료 확인 중」 없음 '+u.id); }
      const s1=search('아이 기침')[0]||{}; if (!/기침/.test(s1.t||'')) bad.push('「아이 기침」 1번: '+s1.t);
      const ab=search('알레르기 비염')[0]||{}; if (ab.k!=='증상') bad.push('「알레르기 비염」 1번: '+ab.k+':'+ab.t);
      const rn=search('콧물약').map(h=>h.t), ci=rn.findIndex(t=>/코푸시럽\)/.test(t)), oi=rn.findIndex(t=>/클로르페니라민|세티리진|로라타딘/.test(t)); if (ci>=0 && (oi<0 || oi>ci)) bad.push('「콧물약」 처방 코푸시럽이 약국 항히스타민보다 앞: '+rn.slice(0,6));
      const mq=mqHits('콧물약').map(h=>h.t), mc=mq.findIndex(t=>/코푸시럽\)/.test(t)); if (mc===0) bad.push('내 약통 「콧물약」 1번이 처방 코푸시럽');
      if ((search('기침약').slice(0,4)).some(h=>/요실금/.test(h.t))) bad.push('「기침약」 상위에 요실금');
      for (const q of ['해열제','진통제']) if (!search(q).slice(0,5).some(h=>/아세트아미노펜/.test(h.t))) bad.push('「'+q+'」 상위 5개에 아세트아미노펜 없음');
      if (!/치통/.test((search('이 아파')[0]||{}).t||'')) bad.push('「이 아파」 1번이 치통 아님');
      if (planDup([{d:drug('xylometazoline'),slot:'코'},{d:drug('coldaewon'),slot:'종합'}]).some(t=>/코막힘/.test(t))) bad.push('코 스프레이 + 콜대원을 코막힘 겹침으로 셈(규칙 decongest-dup 과 다름)');
      ME.taking=[]; ME.pub={}; saveMe(); return bad; }""")
    if z: fails.append(f'Z7 부모 요청(ageAsk·성인 칸·제품 용법·자료 확인 중·검색·코 스프레이): {z[:4]}')
    pz.evaluate(RESET)
    if zerr: fails.append(f'Z7: JS 오류 {zerr[:2]}')
    pz.close()

# Z10(현욱님 10-14 답 넷 + R1 앱 연결) — 아이 화상 응급 선 · 자일리톨 껌·경구수액 수유 · 철분 + 제산제(다른 항목만) · 코엔자임 Q10 + 와파린 ·
#   집 혈압 낮은 기준(90/60) · 설사 약국 카드에 스멕타이트 + 트리메부틴 함께(현욱님 10-14) · 테트라사이클린 카드 한 장
def z10_checks(br, url, fails):
    zerr = []
    pz = br.new_page(viewport={'width': 390, 'height': 844}); pz.on('pageerror', lambda e: zerr.append(str(e)))
    pz.add_init_script("localStorage.setItem('yakjido.hello.v1','1')")
    pz.goto(url + '#/home'); pz.wait_for_function("()=>typeof CORE!=='undefined' && CORE===2", timeout=20000)
    def go(h):
        pz.evaluate("h=>{ location.hash=h; route(); }", h); pz.wait_for_timeout(100)
    pz.evaluate("()=>{ ME.taking=[]; ME.vitals=[]; saveMe(); }")
    go('/symptom/burn')
    if '어른 손바닥 3개·아이 2개 넓이를 넘는 화상' not in pz.evaluate("()=>document.querySelector('#sp2')?.textContent||''"): fails.append('화상 병원 갈 때 — 응급 칸에 「어른 손바닥 3개·아이 2개」가 없습니다')
    for did, want in [('xylitol-gum', '보통 양은 괜찮은 편'), ('ors', '몸에 원래 있는 소금·포도당')]:
        go('/drug/' + did)
        try: pz.wait_for_selector('.lact', state='attached', timeout=8000)
        except Exception: pass
        t = pz.evaluate("()=>document.querySelector('.lact')?.textContent||''")
        if '수유 중 괜찮은 편' not in t or want not in t: fails.append(f'{did} 수유 칸이 「괜찮은 편」이 아닙니다: {t[:60]}')
    ix = lambda tk: pz.evaluate("t=>{ ME.taking=t; saveMe(); return ixRun().hits.map(h=>h.r.id); }", tk)
    if 'iron-antacid' in ix(['supp:iron']): fails.append('철분 영양제 하나만으로 「철분 + 제산제」 카드가 뜹니다')
    if 'iron-antacid' in ix(['supp:iron', 'supp:calcium']): fails.append('철분 + 칼슘 영양제에 「철분 + 제산제」 카드가 뜹니다(칼슘 카드가 따로 있음)')
    if 'iron-antacid' not in ix(['supp:iron', 'almagate']): fails.append('철분 영양제 + 알마게이트에 「철분 + 제산제」 카드가 없습니다')
    h = ix(['cls:blood.warf', 'supp:coq10'])
    if 'warfarin-coq10' not in h: fails.append('와파린 + 코엔자임 Q10 카드가 없습니다')
    elif pz.evaluate("()=>{ const r=ixRun().hits.find(h=>h.r.id==='warfarin-coq10').r; return r.lv==='info' && r.badge==='알아 두기' && /수치를 확인/.test(r.do); }") is not True: fails.append('와파린 + 코엔자임 Q10 카드가 「알아 두기」 info 가 아니거나 문장이 다릅니다')
    if 'warfarin-coq10' in ix(['supp:coq10']) or 'warfarin-coq10' in ix(['cls:blood.warf']): fails.append('와파린 + 코엔자임 Q10 카드가 한쪽만으로 뜹니다')
    h = ix(['cls:derm.tetra', 'almagate'])
    if 'tetra-mineral' not in h or 'sx-tetra' in h: fails.append(f'테트라사이클린 + 제산제 — 정식 규칙 한 장이어야 합니다: {h}')
    pz.evaluate("()=>{ ME.taking=[]; saveMe(); }")
    def bp(s_, d_):
        go('/vitals'); pz.evaluate("()=>{ VT.k='bp'; route(); }"); pz.fill('#vs', str(s_)); pz.fill('#vd', str(d_)); pz.click('button:has-text("적어 두기")'); pz.wait_for_timeout(150)
        return pz.evaluate("()=>{ const n=document.querySelector('.bp-lo'); return n ? n.textContent + (n.querySelector('.src-chip') ? '#src' : '') : ''; }")
    t = bp(85, 55)
    if '90/60보다 낮아요' not in t or '#src' not in t: fails.append(f'혈압 85/55 — 낮은 혈압 안내·출처가 없습니다: {t[:60]}')
    if pz.query_selector('.bp-lo a.call') or '119' in t: fails.append('낮은 혈압 안내에 119 가 붙습니다(조용한 안내여야)')
    if bp(110, 70): fails.append('혈압 110/70 에 낮은 혈압 안내가 뜹니다')
    ids = pz.evaluate("()=>{ const s=byId(D.symptoms,'diarrhea'); return showable(basketPicked(s,basket(s))).map(x=>x.d.id); }")
    if 'smectite' not in ids or 'trimebutine' not in ids: fails.append(f'설사 약국 카드에 스멕타이트·트리메부틴이 함께 있지 않습니다: {ids}')
    go('/show/diarrhea'); t = pz.evaluate("()=>document.querySelector('.show-list')?.innerText||''")
    if '트리메부틴' not in t and '포리부틴' not in t: fails.append('설사 「약국에서 보여드리기」에 트리메부틴이 없습니다')
    pz.evaluate("()=>{ ME.vitals=[]; VT.alert=null; saveMe(); }")
    if zerr: fails.append(f'Z10 검사 JS 오류: {zerr[:2]}')
    pz.close()

# Z9(실사용 검수 3차 — 2026-10-14) — B6 아주 높은 혈당(현욱님: 식사·증상으로 나눠, 증상이면 119) · B7 영양제 ↔ 내 약통 ·
#   B8 늦게 온 제품 목록이 계산기 칸을 지우지 않게 · C2 계산기 ** · C3 하루 최대 겹말 · C12 아이 처음 안내 · C13 당뇨 목표 · C14 탭 화살표
def z9_checks(br, url, fails):
    zerr = []
    pz = br.new_page(viewport={'width': 390, 'height': 844}); pz.on('pageerror', lambda e: zerr.append(str(e)))
    pz.add_init_script("localStorage.setItem('yakjido.hello.v1','1')")
    pz.goto(url + '#/home'); pz.wait_for_function("()=>typeof CORE!=='undefined' && CORE===2", timeout=20000)
    def go(h):
        pz.evaluate("h=>{ location.hash=h; route(); }", h); pz.wait_for_timeout(80)
    def txt():
        return pz.inner_text('#view')
    pz.evaluate("()=>{ ME.taking=[]; ME.vitals=[]; ME.diabetes=false; ME.kidney=false; saveMe(); }")
    # B6 — 300 이상: 식사·증상 칩 → 결과 한 줄
    def bg(v, w):
        go('/vitals'); pz.evaluate("w=>{ VT.k='bg'; VT.gw=w; route(); }", w); pz.fill('#vg', str(v)); pz.click('button:has-text("적어 두기")'); pz.wait_for_timeout(120)
    bg(320, '식후 2시간')
    t = txt()
    if '많이 높아요' not in t or '지금 이런 증상이 있나요?' not in t: fails.append('혈당 320(식후) 뒤에 「많이 높아요」·증상 묻기가 없습니다')
    if pz.query_selector('.bg-hi .bg-out'): fails.append('혈당 320 — 증상을 고르기 전에 119 결과가 먼저 뜹니다')
    pz.click('.bg-hi button:has-text("없음")'); pz.wait_for_timeout(100)
    if '다음 공복에 다시 재세요' not in pz.inner_text('.bg-hi'): fails.append('혈당 320 식후 + 증상 없음 → 「다시 재세요」가 아닙니다')
    pz.click('.bg-hi button:has-text("구토·복통")'); pz.wait_for_timeout(100)
    if '바로 진료' not in pz.inner_text('.bg-hi') or not pz.query_selector('.bg-hi a.call[href="tel:119"]'): fails.append('혈당 320 + 구토·복통 → 「바로 진료·119」 단추가 없습니다')
    if pz.evaluate("()=>(VT.bgs||[]).includes(4)"): fails.append('혈당 증상 칩 — 증상을 고르면 「없음」이 풀려야 합니다')
    bg(350, '공복'); pz.click('.bg-hi button:has-text("없음")'); pz.wait_for_timeout(100)
    if '오늘 안에 진료' not in pz.inner_text('.bg-hi'): fails.append('혈당 350 공복 + 증상 없음 → 「오늘 안에 진료」가 아닙니다')
    bg(400, '그 밖')
    if '언제 재셨어요?' not in pz.inner_text('.bg-hi'): fails.append('혈당 400 「그 밖」 — 식사를 묻지 않습니다')
    pz.click('.bg-hi button:has-text("없음")'); pz.wait_for_timeout(80)
    if pz.query_selector('.bg-hi .bg-out'): fails.append('혈당 400 「그 밖」 — 식사를 고르기 전에 결과가 나옵니다')
    pz.click('.bg-hi button:has-text("식사하고 몇 시간 안")'); pz.wait_for_timeout(80)
    if '다음 공복에 다시 재세요' not in pz.inner_text('.bg-hi'): fails.append('혈당 400 「그 밖」 → 식후 + 없음 → 「다시 재세요」가 아닙니다')
    if pz.evaluate("()=>JSON.stringify(ME).includes('bgs')"): fails.append('혈당 증상 칩이 내 기록(ME)에 저장됩니다 — 화면 기억만이어야 합니다')
    # C13 — 「목표 안」은 당뇨일 때만
    bg(110, '공복')
    if '목표' in pz.inner_text('.vt-list'): fails.append('당뇨가 아닌데 혈당 기록에 「목표」 표가 붙습니다')
    pz.evaluate("()=>{ ME.diabetes=true; saveMe(); route(); }"); pz.wait_for_timeout(80)
    if '목표 안' not in pz.inner_text('.vt-list'): fails.append('당뇨인데 공복 110 에 「목표 안」이 없습니다')
    pz.evaluate("()=>{ ME.diabetes=false; ME.vitals=[]; VT.alert=null; saveMe(); }")
    # B7 — 와파린 담고 오메가3 화면 → 배너, 영양제 담기 → 같이 먹어도 되나요
    pz.evaluate("()=>{ ME.taking=['cls:blood.warf']; saveMe(); }"); go('/supp/omega3')
    b = pz.inner_text('.supp-box') if pz.query_selector('.supp-box') else ''
    if '오메가3' not in b or '항응고' not in b: fails.append(f'와파린을 담았는데 오메가3 화면에 내 약통 경고가 없습니다: {b[:80]}')
    go('/supp/vitc')
    if pz.query_selector('.supp-box'): fails.append('와파린 + 비타민 C — 걸릴 것이 없는데 내 약통 경고가 뜹니다')
    go('/supp/omega3'); pz.click('button:has-text("내 약통에 담기")'); pz.wait_for_timeout(120)
    if 'supp:omega3' not in pz.evaluate("()=>ME.taking"): fails.append('영양제 화면 「내 약통에 담기」가 담지 못했습니다')
    if pz.evaluate("()=>!!(ME.prn||{})['supp:omega3']"): fails.append('영양제를 「필요할 때만」으로 담았습니다 — 매일 드시는 것이 기본')
    if 'sx-omega3' not in pz.evaluate("()=>ixRun().hits.map(h=>h.r.id)"): fails.append('같이 먹어도 되나요가 와파린 + 오메가3 를 판정하지 않습니다')
    go('/together')
    if '오메가' not in txt(): fails.append('같이 먹어도 되나요 화면에 담은 영양제가 없습니다')
    pz.evaluate("()=>{ ME.taking=['cls:thy.levo','supp:calcium']; saveMe(); }")
    if 'levo-mineral' not in pz.evaluate("()=>ixRun().hits.map(h=>h.r.id)"): fails.append('갑상선약 + 칼슘 영양제가 「시간을 띄우세요」로 걸리지 않습니다')
    go('/supp/iron')
    if '갑상선' not in (pz.inner_text('.supp-box') if pz.query_selector('.supp-box') else ''): fails.append('갑상선약을 담았는데 철분 화면에 시간 띄우기 안내가 없습니다')
    if pz.evaluate("()=>sanitizeMe(JSON.parse(JSON.stringify(ME))).taking.join(',')") != 'cls:thy.levo,supp:calcium': fails.append('영양제 id 가 기록 바로잡기(sanitizeMe)에서 빠집니다')
    for r in ['/schedule', '/bag', '/me?t=meds', '/home', '/show']:
        go(r)
        if '문제가 생겼어요' in txt(): fails.append(f'영양제를 담은 뒤 {r} 화면이 터집니다')
    pz.evaluate("()=>{ ME.taking=[]; saveMe(); }")
    # C2·C3 — 계산기 ** · 「하루 최대 약국…」 겹말 · 「—」
    go('/supp/zinc'); pz.evaluate("()=>document.querySelectorAll('details').forEach(d=>d.open=true)")
    if '**' in txt(): fails.append('아연 계산기에 ** 가 그대로 보입니다')
    go('/drug/ibuprofen')
    if '하루 최대 약국' in pz.inner_text('.dose-hero'): fails.append('이부프로펜 용량 칸 「하루 최대 약국…」 겹말')
    go('/drug/ciclopirox-shampoo')
    if pz.query_selector('.dose-hero') and pz.inner_text('.dose-hero').split('\n')[-1].strip().startswith('—'): fails.append('시클로피록스 용량 칸에 「—」 한 글자가 값처럼 보입니다')
    # C12 — 아이 처음 안내: 어른 조건 칩 없음 · 생년월일·몸무게 칸
    go('/hello/1'); pz.click('button.hello-big:has-text("아이가 먹을 약이에요")'); pz.wait_for_timeout(120)
    t = txt()
    if '임신' in t or '전립선' in t or '술을' in t: fails.append('아이 처음 안내 2단계에 임신·전립선·술 칩이 나옵니다')
    if not pz.query_selector('#k-birth') or not pz.query_selector('#k-w'): fails.append('아이 처음 안내에 생년월일·몸무게 칸이 없습니다')
    else:
        pz.fill('#k-w', '11.5'); pz.fill('#k-birth', '2024-03-01'); pz.click('.actions .btn'); pz.wait_for_timeout(100)
        c = pz.evaluate("()=>ME.child")
        if not c or c.get('weight') != 11.5 or c.get('birth') != '2024-03-01': fails.append(f'아이 처음 안내의 몸무게·생년월일이 저장되지 않습니다: {c}')
    pz.evaluate("()=>{ ME.age='adult'; ME.child=null; saveMe(); }")
    # C14 — 약 탭 ←/→
    go('/drug/acetaminophen'); pz.focus('.dtabs [role=tab]'); pz.keyboard.press('ArrowRight')
    if pz.evaluate("()=>[...document.querySelectorAll('.dtabs [role=tab]')].indexOf(document.activeElement)") != 1: fails.append('약 탭에서 → 키로 다음 탭에 가지 않습니다')
    pz.keyboard.press('Home')
    if pz.evaluate("()=>[...document.querySelectorAll('.dtabs [role=tab]')].indexOf(document.activeElement)") != 0: fails.append('약 탭에서 Home 키로 첫 탭에 가지 않습니다')
    if zerr: fails.append(f'Z9 검사 JS 오류: {zerr[:2]}')
    pz.close()
    # B8 — 제품 목록(easy-index)이 늦게 와도 계산기에 적은 값·펼친 칸이 남는다
    ctx = br.new_context(viewport={'width': 390, 'height': 844}, service_workers='block'); p2 = ctx.new_page(); e2 = []; p2.on('pageerror', lambda e: e2.append(str(e)))
    held = []
    p2.route('**/easy-index.json*', lambda rt: held.append(rt))   # 붙잡아 두었다가 다 적은 뒤에 보낸다(느린 휴대폰 흉내)
    p2.add_init_script("localStorage.setItem('yakjido.hello.v1','1')")
    p2.goto(url + '#/supp/iron'); p2.wait_for_function("()=>typeof CORE!=='undefined' && CORE===2 && !!document.querySelector('.pick-more')", timeout=20000)
    p2.evaluate("()=>{ document.querySelector('.pick-more').open = true; }")
    if p2.evaluate("()=>!!PUB.index"): fails.append('B8 검사 — 제품 목록이 이미 와 있어 늦게 오는 경우를 재현하지 못했습니다')
    p2.fill('#c-amt', '50'); p2.fill('#c-price', '9000'); p2.fill('#c-n', '60')
    before = p2.inner_text('#c-pct')
    for rt in held: rt.continue_()
    p2.wait_for_function("()=>!!PUB.index", timeout=20000); p2.wait_for_timeout(300)
    after = p2.evaluate("()=>[document.getElementById('c-amt').value, document.getElementById('c-n').value, document.getElementById('c-pct').innerText, document.querySelector('.pick-more').open]")
    if after[:2] != ['50', '60'] or after[2] != before or not after[3]: fails.append(f'제품 목록이 늦게 오면 계산기 칸이 지워집니다: 전 {before} → 뒤 {after}')
    if e2: fails.append(f'B8 검사 JS 오류: {e2[:2]}')
    ctx.close()

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
            # Z8 — 처음은 밝게(메디나눔 10-14): 휴대폰을 어둡게 해도 앱은 밝게 뜬다. 어두운 화면 검사는 앱 설정 「어둡게」를 켜고 본다(휴대폰도 어둡게)
            pg.emulate_media(color_scheme=theme); pg.evaluate("t=>setTheme(t)", theme); bad = []; tap = []
            for r in SC:
                pg.goto(url + '#' + r); pg.wait_for_timeout(500)
                bad += pg.evaluate(CONTRAST_JS); tap += pg.evaluate(TAP_JS)
                for u in pg.evaluate(UICON_JS): fails.append(f'조작 부품 대비({theme}) {r}: {u} — 3:1 이 필요합니다')
            # 4b. 약 화면은 탭 안(주의·부작용·수유·제품 칸)까지 — 첫 탭만 보던 검사가 「수유 자료 없음」 칩 4.0:1 을 놓쳤다(2026-10-07)
            for r in ['/drug/loxoprofen', '/drug/coldaewon', '/drug/ibuprofen', '/drug/antibiotic-eyedrop']:
                pg.goto(url + '#' + r); pg.wait_for_timeout(400)
                for tb in pg.evaluate("()=>[...document.querySelectorAll('.dtabs .tab')].map(b=>b.dataset.p)"):
                    pg.click(f'.dtabs .tab[data-p={tb}]'); pg.wait_for_timeout(150)
                    bad += [dict(x, at=r + ':' + tb) for x in pg.evaluate(CONTRAST_JS)]; tap += pg.evaluate(TAP_JS)
            if bad: fails.append(f'명암비({theme}) {len(bad)}: {bad[:3]}')
            if tap: fails.append(f'44px 미만({theme}) {len(tap)}: {sorted(set(tap))[:5]}')
        pg.emulate_media(color_scheme='light'); pg.evaluate("()=>{ try { localStorage.removeItem('yakjido.theme'); } catch (e) {} document.documentElement.dataset.theme = 'light'; }")
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
        if _mt['tabs'] != ['내 몸', '내 약통', '설정']: fails.append(f'내 정보 탭이 셋이 아닙니다: {_mt["tabs"]}')   # 3-20 이름 하나로 — 「먹는 약」 → 「내 약통」
        if _mt['chips'] != 12 or not _mt['on'] or not _mt['off']: fails.append(f'건강 상태 단추가 켜지고 꺼지지 않습니다: {_mt}')
        if '소변이 막힐 수' not in _mt['desc']: fails.append('건강 상태를 눌러도 「켜 둔 것」 설명이 안 붙습니다')
        if not _mt['stay']: fails.append('건강 상태를 누르면 화면이 맨 위로 튑니다')
        pg.goto(url + '#/me?t=meds'); ready(); pg.wait_for_timeout(300)
        if not pg.query_selector('#mq') or '복용 시간 알림' not in pg.inner_text('#view'): fails.append('내 정보 「내 약통」 탭에 약 담기·알림이 없습니다')
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
        # 5a-11b. Z8 — 처음은 밝게(휴대폰이 어둡게여도) · 세 가지(밝게·어둡게·기기 따라)를 이 기기에 기억 · 다시 열어도 그대로 · 어둡게여도 종이에는 밝게
        _pt = br.new_page(viewport={'width': 390, 'height': 844}, color_scheme='dark')
        _pt.add_init_script("localStorage.setItem('yakjido.hello.v1','1')"); _pt.goto(url + '#/me?t=set'); _pt.wait_for_timeout(1500)
        _bg = "()=>({th:document.documentElement.dataset.theme||'(없음)', bg:getComputedStyle(document.body).backgroundColor, seg:[...document.querySelectorAll('[aria-label=\"화면 밝기\"] button')].map(b=>b.textContent+(b.getAttribute('aria-pressed')==='true'?'*':''))})"
        _d0 = _pt.evaluate(_bg)
        if _d0['th'] != 'light' or _d0['bg'] != 'rgb(239, 235, 227)': fails.append(f'처음 화면이 밝게가 아닙니다(휴대폰 어둡게): {_d0}')
        if _d0['seg'] != ['밝게*', '어둡게', '기기 따라']: fails.append(f'화면 밝기 칸이 「밝게·어둡게·기기 따라」(밝게 골라짐)가 아닙니다: {_d0["seg"]}')
        for _k, _want in (('dark', ('dark', 'rgb(14, 18, 20)')), ('auto', ('(없음)', 'rgb(14, 18, 20)')), ('light', ('light', 'rgb(239, 235, 227)'))):
            _pt.click(f'[aria-label="화면 밝기"] button:nth-child({["light", "dark", "auto"].index(_k) + 1})'); _pt.reload(); _pt.wait_for_timeout(1200)
            _d = _pt.evaluate(_bg)
            if (_d['th'], _d['bg']) != _want: fails.append(f'화면 밝기 {_k} 를 고르고 다시 열면 {_d} (기대 {_want})')
        _pt.click('[aria-label="화면 밝기"] button:nth-child(2)'); _pt.emulate_media(media='print')
        _pr = _pt.evaluate("()=>[getComputedStyle(document.documentElement).getPropertyValue('--muted').trim(), getComputedStyle(document.documentElement).getPropertyValue('--card').trim()]")
        if _pr != ['#5B6770', '#FFFFFF']: fails.append(f'어둡게에서 종이로 뽑으면 밝은 색이 아닙니다: {_pr}')
        _pt.close()
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
        # 5a-6b. 현욱님 10-13(Z2-1 → A) — 65세+심장+항응고제: 막힌 소염제 칸은 맨 뒤 「이 조건에선 약사와 먼저 상의」 묶음,
        #        같은 증상에 아세트아미노펜 칸이 있으면 그 칸이 1번. 증상 화면과 약국 카드(#/show)가 같은 순서.
        _q5 = pg.evaluate("""()=>{
          const keep = JSON.stringify(ME), bad = [], NS = /이부프로펜|나프록센|덱시부프로펜/;
          ['diabetes','ulcer','kidney','liver','glaucoma','bph','asthma','alcohol','gout','pregnant'].forEach(f=>{ME[f]=false;});
          ME.age='senior'; ME.heart=true; ME.anticoag=true; ME.taking=[]; ME.pub={}; ME.allergy=[]; ME.allergyUnknown=false;
          for (const sid of ['headache','msk','cold']) {
            location.hash = '#/symptom/' + sid; route();
            const all = [...document.querySelectorAll('.answer .buy .buy-item')];
            const main = all.filter(e => !e.closest('.opt-fold,.consult-grp')).map(e => (e.querySelector('b')||{}).innerText||'');
            const grp = all.filter(e => e.closest('.consult-grp')).map(e => (e.querySelector('b')||{}).innerText||'');
            const head = (document.querySelector('.consult-grp .consult-h')||{}).innerText||'';
            if (!/아세트아미노펜/.test(main[0]||'')) bad.push(sid+': 첫 칸이 아세트아미노펜이 아님 — '+(main[0]||'없음'));
            if (main.some(t => NS.test(t))) bad.push(sid+': 막힌 소염제가 앞쪽 목록에 남음 — '+main.join(','));
            if (sid !== 'headache' && !(grp.some(t => NS.test(t)) && /이 조건에선 약사와 먼저 상의/.test(head))) bad.push(sid+': 소염제가 「이 조건에선 약사와 먼저 상의」 묶음에 없음 — '+grp.join(','));
            location.hash = '#/show/' + sid; route();
            const sh = [...document.querySelectorAll('.show-list li:not(.show-have) b')].map(b => b.innerText);
            if (!/아세트아미노펜/.test(sh[0]||'')) bad.push(sid+': 약국 카드 1번이 아세트아미노펜이 아님 — '+(sh[0]||'없음'));
          }
          ME = sanitizeMe(JSON.parse(keep)); saveMe(); location.hash = '#/home'; route();
          return bad;}""")
        if _q5: fails.append(f'막힌 약 순서(65세+심장+항응고제): {_q5[:3]}')
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
        for _f, _lim in (('pills.json', 37), ('pills-rx.json', 157), ('easy-index.json', 85)):   # pills 25→30→37(2026-10-13): 빈 성분을 품목기준코드(1,491건)·식약처 상세(749건)로 채우자 새로 드러난 12개(메클리진·판테틴 복합·생약 감기약 오제나·씨누스트·아이비엽 등) — 해석 퇴보 아님, 화면엔 「성분 모름」
            if _cov[_f]['none'] > _lim: fails.append(f'성분을 못 읽는 제품이 늘었습니다 {_f}: {_cov[_f]["none"]} (기준 {_lim}) — {_cov[_f]["bad"][:5]}')
        # 혈압·혈당 수첩 — 적기·7일 평균·기준(135/85) 안내·지우기(2026-09-29)
        pv = br.new_page(viewport={'width': 390, 'height': 844}); verr = []
        pv.on('pageerror', lambda e: verr.append(str(e)))
        pv.clock.install(time='2026-09-29T08:00:00')
        pv.add_init_script("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['cls:bp.arb'],pub:{}}))")
        pv.goto(url + '#/vitals'); pv.wait_for_selector('.app', timeout=15000); pv.wait_for_timeout(600)
        # 적던 숫자가 뒤에서 온 자료(낱알 목록·사전) 때문에 지워지면 안 된다 — 화면을 연 지 4초쯤 뒤 easy-index 가 오며
        # 화면을 새로 그려 「184 / 100」이 사라졌고, 그래서 아래 재측정 검사가 전체 실행에서만 가끔 실패했다(2026-10-13)
        pv.fill('#vs', '128'); pv.fill('#vd', '82')
        try: pv.wait_for_function("()=>!!PUB.index && !!LEX.ing && !LEX.loading", timeout=20000); pv.wait_for_timeout(400)
        except Exception: fails.append('혈압 수첩: 뒤에서 받는 낱알 목록이 20초 안에 오지 않았습니다')
        if pv.evaluate("()=>[document.getElementById('vs').value, document.getElementById('vd').value].join('/')") != '128/82': fails.append('혈압 수첩: 적던 숫자가 뒤에서 온 자료 때문에 지워졌습니다')
        pv.fill('#vs', ''); pv.fill('#vd', '')
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
        _n0 = pv.evaluate("()=>ME.vitals.length")
        pv.fill('#vs', '184'); pv.fill('#vd', '100'); pv.click('button:has-text("적어 두기")')
        try: pv.wait_for_function(f"()=>ME.vitals.length>{_n0}", timeout=3000)   # 적힌 뒤에 본다(무거울 때 250 ms 로는 모자랄 수 있음) — 안 적혔으면 아래에서 실패
        except Exception: pass
        pv.wait_for_timeout(250)
        if not pv.query_selector('.note.alert') or '오늘 안에 진료' not in pv.inner_text('.note.alert'):
            fails.append('혈압 수첩: 쉬고 다시 재도 높은데 안내가 없습니다 — ' + str(pv.evaluate("()=>[VT.alert, JSON.stringify(ME.vitals.slice(-3)), document.querySelector('.toast')?.textContent||'', document.getElementById('vs')?.value, new Date().toISOString()]")) + str(verr[:2]))
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
        pp.click('.prn-row button:has-text("지금 먹었어요")'); pp.wait_for_timeout(300)   # 앱 안 확인 창(5-11) — 휴대폰 영어 OK/Cancel 창 대신
        if pp.query_selector('.dlg'): dlg.append(pp.inner_text('.dlg p')); pp.click('.dlg [data-a=no]'); pp.wait_for_timeout(200)
        if not dlg or '4시간' not in dlg[0]: fails.append(f'필요할 때만: 간격 안에 또 누르면 물어봐야 합니다 — {dlg}')
        if '오늘 1번' not in pp.inner_text('.prn-row'): fails.append('필요할 때만: 취소했는데 적혔습니다')
        if pp.evaluate("()=>prnLeft('acetaminophen')") != 9: fails.append('필요할 때만: 남은 알 수가 1 줄지 않았습니다')
        pp.click('.prn-qty button:has-text("2알")'); pp.wait_for_timeout(200)
        pp.click('.prn-row button:has-text("지금 먹었어요")'); pp.wait_for_selector('.dlg [data-a=ok]', timeout=3000); pp.click('.dlg [data-a=ok]'); pp.wait_for_timeout(300)
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
        # Z4 #1(외부 검수 P0) — 「내 정보 → 내 약통 → 이름으로 담기 → 같이 먹어도 되나요」. 판콜에이가 단일 성분(구아이페네신)으로 담겨
        #   콜대원 콜드에스·타이레놀과의 아세트아미노펜 겹침을 놓치던 길을 그대로 밟는다. 제품은 모든 성분 그대로(ME.pub) 담겨야 한다
        pz = br.new_page(viewport={'width': 390, 'height': 844}); zerr = []
        pz.on('pageerror', lambda e: zerr.append(str(e)))
        pz.add_init_script("localStorage.setItem('yakjido.hello.v1','1')")
        def _z_add(names):
            pz.goto(url + '#/me'); pz.wait_for_selector('.metabs', timeout=15000)
            pz.evaluate("()=>{ME.taking=[];ME.pub={};ME.prn={};saveMe();route();}")
            pz.click('.metabs .tab[data-k=meds]'); pz.wait_for_selector('#mq', timeout=5000)
            for nm, want in names:
                pz.fill('#mq', nm)
                pz.wait_for_function("()=>typeof PUB!=='undefined' && PUB.index && PUB.index.length>0", timeout=20000)
                pz.wait_for_function("w=>[...document.querySelectorAll('.card.rows .row b')].some(b=>b.innerText.replace(/\\s/g,'').startsWith(w))", arg=want, timeout=8000)
                pz.evaluate("w=>[...document.querySelectorAll('.card.rows .row')].find(r=>r.querySelector('b').innerText.replace(/\\s/g,'').startsWith(w)).click()", want)
                pz.wait_for_timeout(400)
            pz.click('button.srow:has-text("같이 먹어도 되나요")'); pz.wait_for_selector('.ix-list', timeout=5000); pz.wait_for_timeout(300)
            return pz.evaluate("()=>({dupe:[...document.querySelectorAll('.ix.stop .ix-dg')].map(e=>e.innerText), taking:ME.taking.slice(), ingr:Object.values(ME.pub).map(x=>x.ingr)})")
        _z = _z_add([('콜대원 콜드에스', '콜대원콜드에스'), ('판콜에이', '판콜에이')])
        if any(not t.startswith('pub:') for t in _z['taking']): fails.append(f'Z4 #1: 제품 이름으로 담았는데 단일 성분으로 담겼습니다 — {_z["taking"]}')
        if not all('아세트아미노펜' in i for i in _z['ingr']): fails.append(f'Z4 #1: 복합제의 성분이 빠졌습니다 — {_z["ingr"]}')
        if not any('아세트아미노펜' in d for d in _z['dupe']): fails.append(f'Z4 #1: 콜대원 콜드에스 + 판콜에이인데 아세트아미노펜 겹침이 안 뜹니다 — {_z["dupe"]}')
        if not any('일부 성분이 같아요' in d for d in _z['dupe']): fails.append(f'Z4 #1: 「일부 성분이 같아요」 표시가 없습니다 — {_z["dupe"]}')
        _z = _z_add([('판콜에이', '판콜에이'), ('타이레놀정 500', '타이레놀정500')])
        if not any('아세트아미노펜' in d for d in _z['dupe']): fails.append(f'Z4 #1: 판콜에이 + 타이레놀정 500인데 아세트아미노펜 겹침이 안 뜹니다 — {_z["dupe"]}')
        _z = _z_add([('타이레놀정 500', '타이레놀정500'), ('타이레놀 8시간', '타이레놀8시간')])
        if not any('성분이 모두 같아요' in d and '아세트아미노펜' in d for d in _z['dupe']): fails.append(f'Z4 #1: 타이레놀정 500 + 타이레놀 8시간 이알서방정인데 「성분이 모두 같아요」가 없습니다 — {_z["dupe"]}')
        # 단일 성분 항목의 제품 칸에 적힌 복합제 이름(구아이페네신 → 「판콜에이」)으로 찾아도 단일 성분 화면으로 보내지 않는다
        if pz.evaluate("()=>search('판콜에이').some(h=>h.h==='/drug/guaifenesin')"): fails.append('Z4 #1: 「판콜에이」 검색이 구아이페네신으로 갑니다')
        if zerr: fails.append(f'Z4 #1: JS 오류 {zerr[:2]}')
        pz.close()
        # 설치한 안드로이드 앱 — 앱을 닫아도 울리도록 휴대폰 알람으로 거는지(2026-09-28)
        pn = br.new_page(viewport={'width': 390, 'height': 844}); nerr = []
        pn.on('pageerror', lambda e: nerr.append(str(e)))
        pn.clock.install(time='2026-09-28T10:00:00')
        pn.add_init_script(CAP_MOCK)
        pn.add_init_script("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['ibuprofen'],sched:{ibuprofen:['08:00','20:00']},pub:{}}))")
        pn.goto(url + '#/schedule?t=sc4'); pn.wait_for_selector('.app', timeout=15000); pn.wait_for_timeout(1500)   # 알림 방법은 탭 안(2026-09-30)
        L = pn.evaluate("()=>__LN.pending")
        # 2026-10-13 상용화 점검 1-03 — 매일 반복(on)은 둘째 날부터 도즈에서 늦게 울려, 앞으로 7일치를 한 번짜리(at)·allowWhileIdle 로 건다
        daily = [x for x in L if x.get('title') == '약지도 · 약 드실 시간']
        again = [x for x in L if x.get('title') == '아직 안 드셨어요']
        if any(x.get('schedule', {}).get('on') for x in daily + again): fails.append('앱 알람: 복용 알림이 아직 매일 반복(on)입니다 — 둘째 날부터 도즈에서 늦게 울립니다')
        if not all(x.get('schedule', {}).get('allowWhileIdle') for x in daily + again): fails.append('앱 알람: 복용 알림에 allowWhileIdle 이 없습니다')
        if len(daily) != 13: fails.append(f'앱 알람: 제시간 알림이 7일치 13개(오늘 08:00 은 지남)여야 합니다 — {len(daily)}')
        _hm = pn.evaluate("()=>[...new Set(__LN.pending.filter(x=>x.title==='약지도 · 약 드실 시간').map(x=>{const d=new Date(x.schedule.at);return d.getHours()+':'+d.getMinutes()}))].sort()")
        if _hm != ['20:0', '8:0']: fails.append(f'앱 알람: 제시간 알림 시각이 08:00·20:00 이 아닙니다 — {_hm}')
        if any(x.get('channelId') != 'dose2' or x.get('actionTypeId') != 'dose' for x in daily + again): fails.append('앱 알람: 복용 알림 채널(잠금 화면 비공개 dose2)·「먹었어요」 단추가 빠졌습니다')
        if any('이부프로펜' in (x.get('body') or '') for x in daily + again): fails.append('앱 알람: 잠금 화면에 약 이름이 보입니다(기본은 숨김)')
        if not any(x.get('title') == '알림을 이어 가려면 약지도를 한 번 열어 주세요' for x in L): fails.append('앱 알람: 마지막 날 「알림을 이어 가려면 약지도를 한 번 열어 주세요」 알림이 없습니다')
        if any(x.get('isExactNotification') for x in L): fails.append('앱 알람: 정확한 시각 권한이 없는데 정확 알람으로 걸어 설정 화면이 매번 뜹니다')
        # 현욱님 10-13 「너무 자주 하면 안 된다」 — 하루 «시각 수 + 1»장. 시각 2개(08·20)면 하루 3장: 제시간 2 + 다시 알림 1(이른 08:30).
        #   오늘은 08:00·08:30 이 이미 울려 20:00 한 장만, 내일부터 08:30 다시 알림만 — 마지막 날은 「약지도를 한 번 열어 주세요」가 그 자리를 쓴다 → 5개
        if len(again) != 5: fails.append(f'앱 알람: 「아직 안 드셨어요」가 하루 상한 안에서 5개(내일부터 08:30, 마지막 날 빼고)여야 합니다 — {len(again)}')
        _pd = pn.evaluate("()=>{const c={};for(const x of __LN.pending){if(!x.schedule||!x.schedule.at||x.id>=900000)continue;const d=new Date(x.schedule.at);const k=d.getMonth()+'-'+d.getDate();c[k]=(c[k]||0)+1;}return Math.max(0,...Object.values(c));}")
        if _pd > 3: fails.append(f'앱 알람: 하루 알림이 «시각 수 + 1»(3장)을 넘습니다 — {_pd}')
        if any(x.get('id') == 590000 or str(x.get('title')) == '오늘 약 체크' for x in L): fails.append('앱 알람: 저녁 하루 정리가 기본으로 켜져 있습니다(기본 꺼짐)')
        if not (pn.evaluate("()=>__LN.types && __LN.types.types[0].actions.map(a=>a.id).join()") == 'took,later,skip'): fails.append('앱 알람: 「먹었어요」·「10분 뒤 다시」·「건너뛰기」 단추가 없습니다')
        t = pn.inner_text('.app')
        if '휴대폰 알림' not in t or '앱이 열려 있을 때' in t: fails.append('앱 알람: 알림 방법 카드가 설치 앱용으로 바뀌지 않았습니다')
        if '정확한 시각에 울리기' not in t: fails.append('앱 알람: 정확한 시각 허용 단추가 없습니다')
        pn.click('#sc4 button:has-text("허용")'); pn.wait_for_timeout(600)
        if not all(x.get('isExactNotification') for x in pn.evaluate("()=>__LN.pending")): fails.append('앱 알람: 허용 뒤에도 정확 알람으로 다시 걸리지 않습니다')
        # 알림의 「먹었어요」 → 체크되고, 오늘 20:30 「아직 안 드셨어요」는 지워져야 한다
        pn.evaluate("()=>__LN.listeners.localNotificationActionPerformed({actionId:'took',notification:{extra:{key:'ibuprofen@20:00'}}})"); pn.wait_for_timeout(600)
        if 'ibuprofen@20:00' not in pn.evaluate("()=>takenSet()"): fails.append('앱 알람: 「먹었어요」가 체크로 이어지지 않습니다')
        if pn.evaluate("()=>__LN.pending.some(x=>x.schedule.at && new Date(x.schedule.at).getDate()===28 && new Date(x.schedule.at).getHours()===20)"):
            fails.append('앱 알람: 미리 먹었다고 누른 뒤에도 오늘 20시 알림(제시간·30분 뒤)이 남아 있습니다')
        _ag = pn.evaluate("()=>__LN.pending.filter(x=>x.title==='아직 안 드셨어요').length")
        if _ag != 5: fails.append(f'앱 알람: 먹었어요 뒤 「아직 안 드셨어요」가 5개여야 합니다 — {_ag}')
        # 알림의 날짜로 적는다 — 어제 알림의 「먹었어요」는 어제 칸에(5-16)
        pn.evaluate("()=>__LN.listeners.localNotificationActionPerformed({actionId:'took',notification:{extra:{key:'ibuprofen@08:00',day:dayBefore(1)}}})"); pn.wait_for_timeout(400)
        if pn.evaluate("()=>((ME.taken||{})[dayBefore(1)]||[]).includes('ibuprofen@08:00') && !takenSet().includes('ibuprofen@08:00')") is not True: fails.append('앱 알람: 어제 알림의 「먹었어요」가 어제 기록으로 가지 않습니다')
        pn.evaluate("()=>__LN.listeners.localNotificationActionPerformed({actionId:'later',notification:{title:'약지도 · 약 드실 시간',body:'x',extra:{key:'ibuprofen@08:00'}}})"); pn.wait_for_timeout(400)
        if not [x for x in pn.evaluate("()=>__LN.pending") if x['id'] >= 900000]: fails.append('앱 알람: 「10분 뒤 다시」가 걸리지 않습니다')
        if pn.evaluate("async()=>!!(navigator.serviceWorker && await navigator.serviceWorker.getRegistration())"): fails.append('앱 알람: 설치 앱에서 서비스워커가 등록됩니다')
        # 남은 알 수 14알·하루 2번 → 7일치 → 5일분 남는 날(9/30) 아침 9시 한 번만(한 번 받아 올 때마다 한 번 — Z6)
        pn.evaluate("()=>{ME.stock={ibuprofen:{left:14,at:todayKey()}};saveMe();nativeArm();}"); pn.wait_for_timeout(600)
        rf = pn.evaluate("()=>__LN.pending.filter(x=>x.extra&&x.extra.stock).map(x=>{const d=new Date(x.schedule.at);return (d.getMonth()+1)+'/'+d.getDate()+' '+d.getHours()+'시 '+x.title})")
        if sorted(rf) != ['9/30 9시 약이 5일분쯤 남았어요']: fails.append(f'앱 알람: 약 떨어지기 전 알림이 틀립니다 — {rf}')
        # 기록 모두 지우기 — 기록·알람이 다 사라지고, 글자 크기 같은 보기 설정은 남는다
        pn.evaluate("()=>localStorage.setItem('yakjido.fs','20px')")
        pn.evaluate("()=>{ wipeMe(); }"); pn.wait_for_selector('.dlg [data-a=ok]', timeout=3000); pn.click('.dlg [data-a=ok]'); pn.wait_for_timeout(600)   # 앱 안 확인 창(5-11)
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
        alarm_z6(br, url, fails)
        z7_checks(br, url, fails)
        z9_checks(br, url, fails)
        z10_checks(br, url, fails)
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
        # 6c-2. 조건을 켠 바구니도(한 가지·두 가지 조합 전부) 스스로 겹치지 않는지 — 위 조건에서 감기 거담제가 구아이페네신으로 바뀌어
        #       「이 중 하나만」 묶음의 콜대원과 겹치던 것을 잡는다(2026-10-13)
        pdup2 = pg.evaluate("""()=>{ const FL=['senior','ulcer','kidney','heart','anticoag','pregnant','liver','asthma','alcohol','glaucoma','bph','gout'];
          const cs=FL.map(a=>[a]); for(let i=0;i<FL.length;i++) for(let j=i+1;j<FL.length;j++) cs.push([FL[i],FL[j]]); const out=[];
          for(const fl of cs) for(const s of (D.symptoms||[])){ const m=planDup(basket(s,{flags:fl})); if(m.length) out.push(s.id+' ['+fl.join('+')+'] '+String(m[0]).slice(0,60)); }
          return out; }""")
        if pdup2: fails.append(f'조건을 켠 추천 바구니가 스스로 겹침 {len(pdup2)}건: {pdup2[:2]}')
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
        # 10c. 현욱님 10-13(Z2-2 → B) — 생년월일 없이 6 kg 미만이면 mL 결과 위에 접지 않은 경고 한 줄, 결과는 그대로. 10 kg 이면 없음
        _ky = pg.evaluate("""()=>{ const r = w => { ME.age='child'; ME.child={name:'',birth:'',weight:w}; route();
            const e = document.querySelector('.kid-young'), c = document.querySelector('.dose-card');
            return {on: !!e && e.getClientRects().length > 0 && !e.closest('details'), txt: e ? e.innerText : '', cards: document.querySelectorAll('.dose-card').length,
                    above: !!(e && c && (e.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING))}; };
          const a = r(5), b = r(10); ME.age='adult'; ME.child={}; saveMe(); return {a, b}; }""")
        if not (_ky['a']['on'] and '생후 3개월 안팎일 수 있어요' in _ky['a']['txt'] and _ky['a']['above'] and _ky['a']['cards'] == 2):
            fails.append(f'아이 5 kg·생년월일 없음: 「생후 3개월 안팎」 경고가 결과 위에 보이지 않습니다(또는 결과가 사라짐) {_ky["a"]}')
        if _ky['b']['on']: fails.append('아이 10 kg·생년월일 없음인데 「생후 3개월 안팎」 경고가 뜹니다')
        # 7. 항콜린 이중 계산 · 8. 이름 검색
        r7 = pg.evaluate("""async()=>{ await pubPills(); await pubPillsRx(); let n=0;
          for(const p of (PUB.rx||[]).concat(PUB.pills||[])){ const ks=ingFind((p.ingr||'')+' '+(p.n||'')).filter(e=>e.ach).map(e=>e.k); if(ks.length!==new Set(ks).size) n++; } return n; }""")
        # ↑ «같은 성분»이 두 번 잡히는 것만 이중 계산이다 — 클로르페니라민+벨라돈나처럼 항콜린 성분이 실제로 둘인 복합제는 둘로 세는 게 맞다
        #   (2026-10-13 낱알 1,491건의 빈 성분을 품목기준코드로 채운 뒤 그런 제품 10개가 처음 드러남)
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
        # 9b. 영양제 화면 — 질문 세 개(음식 → 효과 → 하루에 얼마나)가 위, 제형·계산기는 「제품 고를 때」 접힌 칸(2026-10-07)
        pg.evaluate("localStorage.setItem('yakjido.me.v1',JSON.stringify({...JSON.parse(localStorage.getItem('yakjido.me.v1')||'{}'),sw:{s:'f',a:3}}))")
        pg.goto(url + '#/supp/iron'); pg.reload(); ready(); pg.wait_for_timeout(900)
        _sv = pg.evaluate("""()=>{const v=document.getElementById('view');const hs=[...v.querySelectorAll('h2.sq-h')].map(h=>h.textContent.replace(/^\\d/,''));
          const forms=[...v.querySelectorAll('table.cmp')].map(t=>!!t.closest('details:not([open])'));const dn=v.querySelector('.dose2 .dn')?.textContent||'';
          const fd=v.querySelectorAll('.fds .fd').length;return {hs,forms,dn,fd}}""")
        if _sv['hs'][:3] != ['어떤 음식에 많아요?', '뭐에 좋아요?', '하루에 얼마나?']: fails.append(f'영양제 화면 질문 순서가 다릅니다: {_sv["hs"]}')
        if not _sv['forms'] or not all(_sv['forms']): fails.append('철분 제형 표가 「제품 고를 때」 접힌 칸 밖에 나와 있습니다')
        if not _sv['dn'].startswith('6') or _sv['fd'] < 5: fails.append(f'65~74세 여자 철분 하루 필요량(6 mg)·음식 칸이 아닙니다: {_sv}')
        _y0 = pg.evaluate("()=>{const b=[...document.querySelectorAll('.who-seg button')].find(x=>x.textContent==='남자');b.scrollIntoView();window.scrollBy(0,-100);return Math.round(scrollY)}")
        pg.click('.who-seg button:text-is("남자")'); pg.wait_for_timeout(400)
        _sm = pg.evaluate("()=>({dn:document.querySelector('.dose2 .dn')?.textContent||'',y:Math.round(scrollY)})")
        if not _sm['dn'].startswith('8'): fails.append(f'남자를 고르면 철분 필요량이 8 mg이어야 합니다: {_sm}')
        if abs(_sm['y'] - _y0) > 40: fails.append(f'누구 기준을 고르면 화면이 튑니다: {_y0}→{_sm["y"]}')
        pg.evaluate("()=>{document.querySelector('details.pick-more').open=true}")
        _base = pg.evaluate("()=>{const s=(D.supplements||[]).find(x=>x.id==='iron');return s&&s.calc&&(s.calc.typical||s.calc.base)||0}")   # 계산 기준은 자료에서(10-14 예방 15 mg 으로 바뀜 — 숫자를 박아 두지 않음)
        _base = _base if isinstance(_base, (int, float)) and _base > 0 else 15
        pg.fill('#c-amt', str(_base)); pg.wait_for_timeout(200)
        if pg.inner_text('#c-pct').strip() != '100%': fails.append(f'접힌 칸 안 함량 계산기가 듣지 않습니다(기준 {_base} mg): {pg.inner_text("#c-pct")}')
        for _r in ['/supp/coq10', '/supp/lutein', '/supp/multi']:
            pg.goto(url + '#' + _r); pg.reload(); ready(); pg.wait_for_timeout(600)
            _o = pg.evaluate(OVERFLOW_JS)
            if _o['clip'] or _o['ov'] or _o['len'] < 40: fails.append(f'영양제 화면 {_r}: 넘침·잘림·빈 화면 {_o["clip"][:1]}{_o["ov"][:1]}')
        # 9c. 인터넷 없이 — 서비스워커가 껍데기·core·detail 을 받아 둔 뒤 비행기 모드에서도 증상·약·영양제가 열려야 한다(2026-10-08 출시 점검)
        #     첫 방문 한 번 뒤 다시 열지 않고 곧장 비행기 모드 — 서버를 실제로 끄고(브라우저 캐시 없음) 본다.
        _osrv, _ourl = serve_nostore()
        _oc = br.new_context(viewport={'width': 390, 'height': 844}); _op = _oc.new_page(); _oerr = []; _op.on('pageerror', lambda e: _oerr.append(str(e)))
        _op.goto(_ourl + '#/home'); _op.wait_for_function('window.__READY__===true && DETAIL===2', timeout=15000)
        _op.evaluate("localStorage.setItem('yakjido.hello.v1','1')")
        try:
            _op.wait_for_function("navigator.serviceWorker.controller", timeout=15000)
            for _i in range(40):                       # 본문(core·detail)이 워커 캐시에 들어갈 때까지 — 안 들어가면 그 자체가 실패(wait_for_function 은 async 결과를 기다리지 않아 직접 묻는다)
                if _op.evaluate(CACHED_CORE_JS): break
                _op.wait_for_timeout(500)
            else: raise RuntimeError('core·detail 이 워커 캐시에 없음')
        except Exception: fails.append('서비스워커가 설치되지 않았거나 본문(core·detail)을 캐시에 넣지 않습니다 — 첫 방문 뒤 비행기 모드에서 본문이 안 뜹니다')
        _osrv.shutdown(); _osrv.server_close()      # 진짜로 끈다
        _oc.set_offline(True)
        _oc.route('**/*', lambda rt: rt.abort())    # 워커 밖으로 나가는 요청도 모두 막는다(워커 안의 fetch 는 서버가 꺼져 실패한다)
        for _r in ['/symptom/cold', '/drug/acetaminophen', '/supp/iron', '/schedule']:
            _op.goto(_ourl + '#' + _r); _op.reload()
            try: _op.wait_for_function('window.__READY__===true && DETAIL===2', timeout=10000)
            except Exception: fails.append(f'인터넷 없이 {_r}: 본문 자료가 안 뜹니다(서비스워커 캐시)'); continue
            _op.wait_for_timeout(600)
            _t = _op.inner_text('#view')
            if len(_t) < 200 or '불러오는 중' in _t: fails.append(f'인터넷 없이 {_r}: 화면이 비었거나 「불러오는 중」에 멈춥니다')
        if _oerr: fails.append(f'인터넷 없이 JS 오류: {_oerr[:2]}')
        _oc.close()
        # 9d. 한 화면이 그리다 터지면 흰 화면이 아니라 「문제가 생겼어요」 카드 + 홈으로 단추(2026-10-08)
        pg.goto(url + '#/home'); pg.reload(); ready(); pg.wait_for_timeout(500); _e9 = []
        pg.on('pageerror', lambda e: _e9.append(str(e)))
        pg.evaluate("()=>{ window.__vAboutKeep = vAbout; vAbout = () => { throw new Error('시험용 오류'); }; }")
        pg.goto(url + '#/about'); pg.wait_for_timeout(500)
        _t9 = pg.inner_text('#view')
        if '문제가 생겼어요' not in _t9 or '홈으로' not in _t9: fails.append('화면이 터졌을 때 안내 카드가 안 뜹니다')
        if _e9: fails.append(f'화면이 터졌을 때 오류가 밖으로 샙니다: {_e9[:1]}')
        pg.evaluate("()=>{ vAbout = window.__vAboutKeep; }"); pg.goto(url + '#/home'); pg.wait_for_timeout(200); pg.goto(url + '#/about'); pg.wait_for_timeout(400)   # 같은 주소로는 다시 그리지 않으니 홈을 거쳐 온다
        if '문제가 생겼어요' in pg.inner_text('#view'): fails.append('화면 오류 카드가 복구 뒤에도 남습니다')
        # 9e. 메디나눔 계정(2026-10-13) — 동의 전에는 서버·라이브러리에 한 번도 닿지 않고, 계정 칸은 동의 단추만 보인다.
        #     동의하면 그때 처음 로그인 칸 + 만 14세 확인이 나오고, 체크 전엔 「계정 만들기」가 막혀 있다.
        _ac = br.new_context(viewport={'width': 390, 'height': 844}); _ap = _ac.new_page(); _aerr = []; _hits = []
        _ap.on('pageerror', lambda e: _aerr.append(str(e)))
        _ap.route('**/*supabase.co/**', lambda rt: (_hits.append(rt.request.url), rt.abort()))
        _ap.route('**/cdn.jsdelivr.net/npm/@supabase/**', lambda rt: (_hits.append(rt.request.url), rt.abort()))
        _ap.goto(url + '#/home'); _ap.wait_for_function('window.__READY__===true && DETAIL===2', timeout=15000)
        _ap.evaluate("localStorage.setItem('yakjido.hello.v1','1')")
        _ap.goto(url + '#/me?t=set'); _ap.reload(); _ap.wait_for_function('window.__READY__===true', timeout=15000); _ap.wait_for_timeout(1500)
        if _ap.query_selector('#acct') and not _ap.evaluate('D.meta.account === true'): fails.append('공용 서버가 열리기 전(meta.account=false)인데 계정 칸이 보입니다')
        if not _ap.query_selector('#acct') and _ap.evaluate('D.meta.account === true'): fails.append('계정이 켜졌는데(meta.account=true) 계정 칸이 안 보입니다')
        _ap.evaluate("()=>{ D.meta.account = true; route(); }"); _ap.wait_for_timeout(400)   # 서버가 열린 뒤의 모습
        _box = _ap.inner_text('#acct') if _ap.query_selector('#acct') else ''
        if '동의하고 계속' not in _box: fails.append(f'계정 칸이 동의 단추로 시작하지 않습니다: {_box[:80]!r}')
        if _ap.query_selector('#srvEmail'): fails.append('동의 전인데 이메일 칸이 보입니다(되는 척 금지)')
        if _hits: fails.append(f'동의 전인데 서버·라이브러리에 요청이 갑니다: {_hits[:2]}')
        _ap.click('#acct button:has-text("동의하고 계속")'); _ap.wait_for_selector('.dlg [data-a=ok]', timeout=3000); _ap.click('.dlg [data-a=ok]'); _ap.wait_for_timeout(1500)
        if not _ap.query_selector('#srvEmail') or not _ap.query_selector('#srvAge'): fails.append('동의 뒤에 로그인 칸·만 14세 확인이 안 나옵니다')
        elif not _ap.is_disabled('#srvSignup'): fails.append('만 14세 확인 전인데 「계정 만들기」가 눌립니다')
        else:
            _ap.check('#srvAge')
            if _ap.is_disabled('#srvSignup'): fails.append('만 14세 확인 뒤에도 「계정 만들기」가 막혀 있습니다')
        if '이 휴대폰에만 저장돼요' not in _ap.inner_text('#view'): fails.append('로그인 전인데 저장 위치 문구가 「이 휴대폰에만」이 아닙니다')
        if _aerr: fails.append(f'계정 칸 JS 오류: {_aerr[:2]}')
        _ac.close()
        # 9f. 둘러보기(#/demo) — 외부 검수자가 링크 하나로 채워진 화면을 만지게(2026-10-13). 예시를 담고, 화면이 터지지 않고, 「예시 지우기」로 비워져야 한다.
        _dc = br.new_context(viewport={'width': 390, 'height': 844}); _dp = _dc.new_page(); _derr = []
        _dp.on('pageerror', lambda e: _derr.append(str(e)))
        _dp.goto(url + '#/demo'); _dp.wait_for_function('window.__READY__===true', timeout=15000); _dp.wait_for_timeout(1200)
        if '예시 기록을 담았어요' not in _dp.inner_text('#view'): fails.append('둘러보기(#/demo)가 예시를 담지 못했습니다')
        for _r in ['/home', '/schedule', '/together', '/vitals', '/visits', '/me?t=meds']:
            _dp.goto(url + '#' + _r); _dp.wait_for_timeout(500)
            if '문제가 생겼어요' in _dp.inner_text('#view'): fails.append(f'둘러보기 예시로 {_r} 화면이 터집니다')
        _dp.goto(url + '#/demo'); _dp.wait_for_timeout(400); _dp.click('button:has-text("예시 지우기")'); _dp.wait_for_timeout(400)
        if _dp.evaluate('(ME.taking || []).length'): fails.append('「예시 지우기」 뒤에도 예시 약이 남습니다')
        if _derr: fails.append(f'둘러보기 JS 오류: {_derr[:2]}')
        _dc.close()
        br.close()
    print(f'화면 {len(routes)}개 검사 완료')
    if fails:
        print('실패', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
    print('✓ 전부 통과 — JS 오류 0 · 넘침 0 · 잘림 0 · 명암비 AA · 조작 부품 3:1 · 44px · 단추 누르기 · 복용 간격 · 복약 달력 · 홈 오늘약 · 어르신 소염제 · 소아 한도 · 계열 경고 · 어근 오인 · 내 정보 칸 · 화면 밝기(처음 밝게·세 가지·인쇄 밝게) · 아이콘 전수 · 약 알림 · 어르신 모드 · 320px · 병용 8건 · 겹침 규칙 53 · 입력칸 이름표 · 성분 해석 123 · 죽은 규칙 0 · 약통 판정 4건 · 자기중복 3건 · 바구니 겹침 · 이중계산 0 · 검색 8건 · 구어 30건 · 문장 16건 · 새 약 검색 12건 · 하루 최대 표기 · 먹는/바르는 구분 · 영양제 질문 순서 · 인터넷 없이 · 화면 오류 카드 · 계정 동의 먼저 · 둘러보기 · 아주 높은 혈당(식사·증상) · 영양제 ↔ 내 약통 · 늦은 목록에도 입력 유지 · 아이 처음 안내')

if __name__ == '__main__':
    main()
