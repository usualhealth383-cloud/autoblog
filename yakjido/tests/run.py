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
  6. 병용 판정 시나리오 5건 (삼중고·와파린·전립선·치매약+방광약·혈압약 모름)
  7. 항콜린 이중 계산 0 (식약처 2.4만 제품 전수)
  8. 이름 검색 8건 (베시케어·하루날디·타이레놀·TY 500 …)
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

TAP_JS = """()=>[...document.querySelectorAll('#view button,#view a')].filter(e=>!(e.matches('a.link')&&e.closest('p,span,li'))).map(e=>{const b=e.getBoundingClientRect();return b.height>0&&b.height<44?((e.innerText||e.className)+'').slice(0,20)+':'+Math.round(b.height):null}).filter(Boolean)"""

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
        pg.goto(url); pg.wait_for_timeout(1200)
        pg.evaluate("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',taking:['cls:bp.arb'],pub:{}}))")
        routes = pg.evaluate("()=>['/home','/drugs','/tips','/me','/together','/kinds','/kinds/bp','/pill','/supp','/kids','/mix','/hello/1','/hello/3','/photo','/schedule','/about','/bag','/rxout','/senior']" +
                             ".concat(D.symptoms.map(s=>'/symptom/'+s.id)).concat(D.drugs.map(d=>'/drug/'+d.id)).concat(D.classes.map(c=>'/class/'+c.id)).concat(D.classes.map(c=>'/drugs?cat='+c.id))")
        # 1~3. 모든 화면
        for r in routes:
            pg.goto(url + '#' + r); pg.wait_for_timeout(350)
            o = pg.evaluate(OVERFLOW_JS)
            if o['ov']: fails.append(f'가로 넘침 {r}: {o["ov"]}')
            if o['clip']: fails.append(f'글자 잘림 {r}: {o["clip"]}')
            if o['len'] < 40: fails.append(f'빈 화면 {r}')
        if errs: fails.append(f'JS 오류 {len(errs)}: {errs[:3]}')
        # 4~5. 명암비·탭 타깃 (대표 화면, 두 테마)
        SC = ['/home', '/symptom/cold', '/symptom/drymouth', '/drug/ibuprofen', '/me', '/together', '/kinds', '/tips', '/drugs', '/hello/3']
        for theme in ['light', 'dark']:
            pg.emulate_media(color_scheme=theme); bad = []; tap = []
            for r in SC:
                pg.goto(url + '#' + r); pg.wait_for_timeout(500)
                bad += pg.evaluate(CONTRAST_JS); tap += pg.evaluate(TAP_JS)
            if bad: fails.append(f'명암비({theme}) {len(bad)}: {bad[:3]}')
            if tap: fails.append(f'44px 미만({theme}) {len(tap)}: {sorted(set(tap))[:5]}')
        pg.emulate_media(color_scheme='light')
        # 5b. 어르신 모드(글자 20px·큰 단추) — 넘침·잘림은 큰 글씨에서 먼저 터진다
        pg.evaluate("localStorage.setItem('yakjido.fs','20px');localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',easy:true,taking:['cls:bp.arb','ibuprofen'],pub:{}}))")
        for r in SC + ['/bag', '/schedule', '/symptom/cramp', '/symptom/sprain', '/drug/acetaminophen', '/kinds/bp']:
            pg.goto(url + '#' + r); pg.reload(); pg.wait_for_timeout(500)
            o = pg.evaluate(OVERFLOW_JS)
            if o['ov']: fails.append(f'어르신 모드 가로 넘침 {r}: {o["ov"]}')
            if o['clip']: fails.append(f'어르신 모드 글자 잘림 {r}: {o["clip"]}')
        pg.evaluate("localStorage.setItem('yakjido.fs','16px')")
        # 6. 병용 판정 시나리오 (이름 없이 종류로)
        CASES = [(['bp.arb', 'bp.diur'], '/symptom/arthritis', '콩팥'), (['blood.warf'], '/symptom/msk', '와파린'),
                 (['pros.alpha'], '/symptom/cold', '전립선'), (['dem.ache', 'blad.oab'], '/together', '치매약'), (['bp.any'], '/symptom/arthritis', '혈압약')]
        for picks, r, kw in CASES:
            pg.evaluate("(p)=>localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',taking:p.map(x=>'cls:'+x),pub:{}}))", picks)
            pg.goto(url + '#' + r); pg.reload(); pg.wait_for_timeout(700)
            txt = pg.evaluate("()=>[...document.querySelectorAll('.ixline,.ix-h b')].map(x=>x.innerText).join(' | ')")
            if kw not in txt: fails.append(f'병용 시나리오 {picks} → "{kw}" 없음: {txt[:80]}')
        # 9. 날씨 카드
        pg.goto(url + '#/home'); pg.reload(); pg.wait_for_timeout(1000)
        wx = pg.evaluate("()=>document.querySelector('.wx')?.innerText||''")
        for kw in ['일교차', '14℃', '미세먼지', '나쁨']:
            if kw not in wx: fails.append(f'날씨 카드에 "{kw}" 없음: {wx[:80]!r}')
        # 9b. 날씨를 못 받는 곳(아티팩트·오프라인)에서 요청이 반복되지 않는지 — 예전에 4초 170번 돌았다
        pg.unroute('**/api.open-meteo.com/**'); pg.unroute('**/air-quality-api.open-meteo.com/**')
        cnt = [0]
        pg.route('**/*open-meteo.com/**', lambda rt: (cnt.__setitem__(0, cnt[0] + 1), rt.abort()))
        pg.evaluate("localStorage.removeItem('yakjido.wx.v1')"); pg.goto(url + '#/home'); pg.reload(); pg.wait_for_timeout(3000)
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
        br.close()
    print(f'화면 {len(routes)}개 검사 완료')
    if fails:
        print('실패', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
    print('✓ 전부 통과 — JS 오류 0 · 넘침 0 · 잘림 0 · 명암비 AA · 44px · 어르신 모드 · 병용 5건 · 이중계산 0 · 검색 8건 · 구어 12건')

if __name__ == '__main__':
    main()
