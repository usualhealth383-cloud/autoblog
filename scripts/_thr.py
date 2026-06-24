import sys
sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")
from auto_blog import config
from auto_blog.publishers import threads_upload as th

tok = config.get("THREADS_TOKEN")
uid = config.get("THREADS_USER_ID")
print("THREADS_TOKEN:", (tok[:10] + "…(" + str(len(tok)) + "자)") if tok else "없음")
print("THREADS_USER_ID:", uid or "없음")
print("configured():", th.configured())
if th.configured():
    print("check():", th.check())
