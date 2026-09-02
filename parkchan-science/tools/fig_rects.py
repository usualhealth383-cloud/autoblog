"""각 .page 안 figure(svg 포함)의 페이지 내 위치(mm)를 측정해 JSON으로 출력"""
import subprocess, re, sys, pathlib, html as h, json
src = pathlib.Path(sys.argv[1]).resolve()
js = """
<script>
function run(){
  const MM=96/25.4, out=[];
  document.querySelectorAll('.page').forEach((pg,i)=>{
    const pr=pg.getBoundingClientRect();
    pg.querySelectorAll('figure, .a-fig').forEach(fg=>{
      const svg=fg.querySelector('svg'); if(!svg) return;
      const r=fg.getBoundingClientRect();
      const cap=fg.querySelector('figcaption');
      out.push({p:i+1,
        x:+((r.left-pr.left)/MM).toFixed(1), y:+((r.top-pr.top)/MM).toFixed(1),
        w:+(r.width/MM).toFixed(1), hh:+(r.height/MM).toFixed(1),
        sw:+(svg.getBoundingClientRect().width/MM).toFixed(1),
        cap: cap? cap.textContent.slice(0,60):''});
    });
  });
  const pre=document.createElement('pre'); pre.id='rep';
  pre.textContent='BEGIN'+JSON.stringify(out)+'END'; document.body.appendChild(pre);
}
if(document.readyState==='complete') run(); else window.addEventListener('load',()=>document.fonts?document.fonts.ready.then(run):run());
</script>
"""
txt = src.read_text(encoding='utf-8')
css = src.parent/'lecture.css'
if css.exists(): txt = txt.replace('<link rel="stylesheet" href="lecture.css">','<style>\n'+css.read_text()+'\n</style>')
tmp = src.parent/('_fr_'+src.name)
tmp.write_text(txt.replace('</body>', js+'</body>'), encoding='utf-8')
dom = subprocess.run(['/opt/pw-browsers/chromium','--headless=new','--no-sandbox','--disable-gpu','--virtual-time-budget=6000','--dump-dom',f'file://{tmp}'],capture_output=True,text=True,timeout=240).stdout
tmp.unlink()
m = re.search(r"<pre id=\"rep\">BEGIN(.*?)END</pre>", dom, re.S)
print(json.dumps(json.loads(h.unescape(m.group(1))), ensure_ascii=False))
