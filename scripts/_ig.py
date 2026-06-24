import sys
sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")
from auto_blog import config
from auto_blog.publishers import instagram_upload as ig

tok = config.get("IG_TOKEN")
print("IG_TOKEN:", (tok[:6] + "…(" + str(len(tok)) + "자)") if tok else "없음")
print("IG_USER_ID:", config.get("IG_USER_ID") or "없음")
print("configured():", ig.configured())
if ig.configured():
    print("check():", ig.check())
