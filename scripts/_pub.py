"""저장된 한국-남아공 글을 Blogger에만 재발행(텔레그램/재생성 없음).
이미 호스팅된 이미지 URL 재사용."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")
from auto_blog import config, publishers  # noqa: E402

DIR = "20260624-1926-korea-southafrica"
out_dir = config.DATA_DIR / "posts" / DIR
blog = json.loads((out_dir / "blog.json").read_text(encoding="utf-8"))

REPO = "usualhealth383-cloud/autoblog"
base = f"https://raw.githubusercontent.com/{REPO}/main/public/{DIR}"
imgs = {int(p.stem[3:]): f"images/{p.name}" for p in sorted((out_dir / "images").glob("sec*.jpg"))}
image_urls = {str(i): f"{base}/sec{i}.jpg" for i in imgs}

record = {"article": blog, "images": imgs, "image_urls": image_urls,
          "status": "published", "dir": DIR}
print("글:", blog["title"], "|", sum(len(p) for s in blog["sections"] for p in s["paragraphs"]), "자",
      "| 이미지 URL:", len(image_urls))

from auto_blog.publishers import blogger  # noqa: E402
try:
    url = blogger.publish(record, out_dir)
    print("✅ 블로거(KR):", url)
except Exception as e:
    print("❌ KR 실패:", str(e)[:160])
    sys.exit(1)

# 영문본
try:
    from auto_blog import translator
    en = translator.translate_article(blog) if hasattr(translator, "translate_article") else None
except Exception:
    en = None
if en:
    try:
        eu = blogger.publish_article(en, record, out_dir)
        print("✅ 블로거(EN):", eu)
    except Exception as e:
        print("⚠ EN 실패:", str(e)[:120])
