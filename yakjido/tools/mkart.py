import re, json, base64, pathlib, sys
ROOT = pathlib.Path('/home/user/autoblog/docs/yakjido')
OUT  = pathlib.Path('/tmp/claude-0/-home-user-autoblog/cf2f6625-dcb1-56a6-b544-ead87bbf0fa1/scratchpad/artifact/yakson.html')
s = (ROOT/'index.html').read_text()
# 1) strip the outer document wrapper (Artifact adds its own)
s = re.sub(r'^<!doctype html>\s*|^<html[^>]*>\s*|</html>\s*$', '', s, flags=re.I|re.M)
s = re.sub(r'</?(head|body)[^>]*>\s*', '', s, flags=re.I)
# 2) drop PWA-only bits (no manifest / icons / service worker on the artifact host)
s = re.sub(r'^\s*<link rel="(manifest|apple-touch-icon|icon)"[^>]*>\s*$\n?', '', s, flags=re.M)
# 아티팩트 CSP 는 Google Fonts 외 스타일시트를 막는다 — jsdelivr 의 Pretendard 링크는 빼고 Noto Sans KR 로 간다
s = re.sub(r'^\s*<link rel="preconnect" href="https://cdn.jsdelivr.net"[^>]*>\s*$\n?', '', s, flags=re.M)
s = re.sub(r'^\s*<link rel="stylesheet" href="https://cdn.jsdelivr.net[^"]*">\s*$\n?', '', s, flags=re.M)
# 서비스워커 등록 블록 전체를 뺀다(아티팩트에는 워커가 없다). 여러 줄이라 중괄호를 세어 자른다.
i = s.find("if ('serviceWorker' in navigator")
if i >= 0:
    j = s.index('{', i); depth = 0; k = j
    while k < len(s):
        if s[k] == '{': depth += 1
        elif s[k] == '}':
            depth -= 1
            if depth == 0: break
        k += 1
    s = s[:i] + s[k+1:]
# 3) inline the illustrations as data URIs
art = {}
for f in sorted((ROOT/'art').glob('*.webp')):
    art[f.stem] = 'data:image/webp;base64,' + base64.b64encode(f.read_bytes()).decode()
# 미리보기(아티팩트)에서는 파일 내려받기가 막혀 있어 달력 파일 버튼을 안내 문구로 바꾼다 — 설치한 앱에서는 그대로 동작
s = s.replace("onclick=\"downloadIcs()\">${I.clock} 받기</button>", "onclick=\"toast('달력 파일은 설치한 약지도 앱에서 받을 수 있어요')\">${I.clock} 앱에서</button>")
s = s.replace('<img src="art/${n}.webp"', '<img src="${ART_DATA[n] || ("art/" + n + ".webp")}"')
# 아티팩트는 파일 하나라 서버가 없다 — 본문 자료(core.json)도 같이 심는다
# 첫 화면 머리의 앱 표시(34px) — 아티팩트 호스트에는 icon-192.png 파일이 없어 깨진 그림이 나왔다(2026-09-23 현욱님 캡처)
import io
from PIL import Image
_im = Image.open(ROOT/'icon-192.png').convert('RGBA').resize((68, 68), Image.LANCZOS)
_b = io.BytesIO(); _im.save(_b, 'PNG', optimize=True)
brandmark = 'data:image/png;base64,' + base64.b64encode(_b.getvalue()).decode()
inject = ('<script>const ART_DATA = ' + json.dumps(art) + ';\n'
          "window.__BRANDMARK__ = " + json.dumps(brandmark) + ';\n'
          "window.__CORE__ = " + (ROOT/'data/core.json').read_text() + ';\n'
          "window.__PILLS__ = " + (ROOT/'data/pills.json').read_text() + ';\n'
          "window.__EASY__ = "  + (ROOT/'data/easy-index.json').read_text() + ';\n'
          "window.__LEX__ = {ing:" + (ROOT/'data/lexicon.json').read_text()
          + ",brand:" + (ROOT/'data/brands.json').read_text()
          + ",qa:" + (ROOT/'data/qa.json').read_text()
          + ",nut:" + (ROOT/'data/nutrients.json').read_text()
          + ",mix:" + (ROOT/'data/mixes.json').read_text() + '};</script>\n')
i = s.index('<div class="app">')
s = s[:i] + inject + s[i:]
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(s)
print('wrote', OUT, round(len(s.encode())/1e6, 2), 'MB · art', len(art))
assert "'icon-192.png'" not in s.split('window.__BRANDMARK__')[0] or 'window.__BRANDMARK__ = "data:' in s, '앱 표시 그림이 파일 경로로 남았습니다'
for bad in ['serviceWorker.register', 'rel="manifest"', '<!doctype', '<body']:
    if bad in s: print('!! still present:', bad)
