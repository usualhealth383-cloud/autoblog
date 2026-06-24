"""네이버 블로그용 복붙 초안 생성.

네이버는 공식 글쓰기 API 가 없고 자동발행이 약관 위반이므로, 사람이 복붙할 수 있는
HTML 초안 파일을 만든다. 네이버 스마트에디터는 HTML 붙여넣기를 일부 지원하므로
제목/본문을 그대로 옮기기 쉽게 구성한다.
"""
from __future__ import annotations

from pathlib import Path

from .. import formatter


def generate(record: dict, post_dir: Path) -> Path:
    article = record["article"]
    images = {int(k): v for k, v in (record.get("images") or {}).items()}
    title = article.get("title", "")
    body = formatter.render_body(article, images, ads=False)  # 네이버엔 구글 광고 코드 금지

    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"/>
<title>{title}</title></head>
<body style="max-width:720px;margin:20px auto;font-family:'Malgun Gothic',sans-serif">
<p style="background:#e7f5ff;padding:10px;border-radius:8px;color:#1971c2;font-size:13px">
📋 네이버 블로그 글쓰기 → 제목에 아래 제목을, 본문에 아래 내용을 복사해 붙여넣으세요.
이미지는 네이버 에디터에서 직접 업로드해야 합니다(images 폴더 참고).</p>
<h1>{title}</h1>
{body}
</body></html>"""
    dest = post_dir / "naver_draft.html"
    dest.write_text(html, encoding="utf-8")
    return dest
