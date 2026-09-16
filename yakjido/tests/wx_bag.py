import functools,http.server,socketserver,threading,pathlib,json
from playwright.sync_api import sync_playwright
DOCS=pathlib.Path('/home/user/autoblog/docs/yakjido')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a,**k):pass
srv=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Q,directory=str(DOCS)))
threading.Thread(target=srv.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
def fc(mx,mn,rh=50,code=0): return {"current":{"temperature_2m":(mx+mn)/2,"apparent_temperature":(mx+mn)/2,"relative_humidity_2m":rh,"weather_code":code},"daily":{"temperature_2m_max":[mx],"temperature_2m_min":[mn]}}
CASES=[('폭염+이뇨제+NSAID',['cls:bp.diur','ibuprofen'],fc(34,25),{"pm10":30,"pm2_5":10},'콩팥'),
       ('폭염+항콜린',['dimenhydrinate','cetirizine'],fc(34,25),{"pm10":30,"pm2_5":10},'항콜린'),
       ('영하+수면제',['diphenhydramine'],fc(3,-4),{"pm10":30,"pm2_5":10},'빙판'),
       ('일교차+혈압약',['cls:bp.arb'],fc(24,12),{"pm10":30,"pm2_5":10},'아침 혈압'),
       ('미세먼지+천식플래그',[],fc(20,12),{"pm10":120,"pm2_5":60},'흡입기'),
       ('빈 약통 무난',[],fc(22,16),{"pm10":20,"pm2_5":8},'무난')]
with sync_playwright() as p:
    br=p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=br.new_page(viewport={'width':390,'height':844}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    cur={}
    pg.route('**/*open-meteo.com/**',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(cur['fc'] if 'forecast' in r.request.url else {"current":cur['aq']})))
    pg.goto(url); pg.wait_for_timeout(500)
    ok=0
    for name,taking,f,aq,kw in CASES:
        cur['fc']=f; cur['aq']=aq
        me={'age':'senior','taking':taking,'pub':{}}
        if '천식' in name: me['asthma']=True
        pg.evaluate("(m)=>{localStorage.setItem('yakjido.hello.v1','1');localStorage.removeItem('yakjido.wx.v1');localStorage.setItem('yakjido.me.v1',JSON.stringify(m))}",me)
        pg.goto(url+'#/home'); pg.reload(); pg.wait_for_timeout(1100)
        tips=pg.evaluate("[...document.querySelectorAll('.wx-tip')].map(x=>x.innerText)")
        hit=any(kw in t for t in tips); ok+=hit
        print(('✓' if hit else '✗'),name,'|',' || '.join(t[:70] for t in tips))
    print(ok,'/',len(CASES),'errs',errs); br.close()
