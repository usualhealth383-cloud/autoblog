"""Blogger 자동 발행 (공식 API v3).

최초 1회 OAuth 동의(브라우저 자동 열림) 후 토큰을 config/token.json 에 저장한다.
이미지는 외부 URL 이 필요하므로 로컬 생성 이미지를 base64 data URI 로 본문에 인라인한다.

사전 준비(사용자):
1) Google Cloud Console 에서 프로젝트 생성 → 'Blogger API v3' 사용 설정
2) OAuth 동의화면 구성(외부, 테스트 사용자에 본인 추가)
3) 사용자 인증 정보 → OAuth 클라이언트 ID(데스크톱 앱) → client_secret.json 다운로드
   → auto_blog/config/client_secret.json 에 저장
4) .env 의 BLOGGER_BLOG_ID 채우기
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

from .. import config, formatter

SCOPES = ["https://www.googleapis.com/auth/blogger"]
TOKEN_FILE = config.ROOT / "config" / "token.json"


def _service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            cs = config.ROOT / config.get("BLOGGER_CLIENT_SECRET_FILE",
                                          "config/client_secret.json")
            if not cs.exists():
                raise RuntimeError(f"client_secret.json 이 없습니다: {cs}")
            flow = InstalledAppFlow.from_client_secrets_file(str(cs), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.parent.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("blogger", "v3", credentials=creds)


def _data_uri(path: Path, max_width: int = 860, quality: int = 74) -> str:
    """이미지를 JPEG 로 압축·축소해 data URI 로. (Blogger 본문 용량 한도 회피)"""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width > max_width:
        im = im.resize((max_width, int(im.height * max_width / im.width)))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def _inlined_images(record: dict, post_dir: Path) -> dict[int, str]:
    """글의 이미지들을 압축 data URI 로 변환."""
    inlined: dict[int, str] = {}
    for k, rel in (record.get("images") or {}).items():
        p = post_dir / rel
        if p.exists():
            inlined[int(k)] = _data_uri(p)
    return inlined


def _insert(article: dict, inlined: dict[int, str]) -> str:
    blog_id = config.get("BLOGGER_BLOG_ID")
    if not blog_id:
        raise RuntimeError("BLOGGER_BLOG_ID 미설정")
    svc = _service()
    body = {
        "kind": "blogger#post",
        "blog": {"id": blog_id},
        "title": article.get("title", ""),
        "content": formatter.render_body(article, inlined),
        "labels": article.get("tags", []),
    }
    post = svc.posts().insert(blogId=blog_id, body=body, isDraft=False).execute()
    return post.get("url", "(URL 없음)")


def _images_for_publish(record: dict, post_dir: Path) -> dict[int, str]:
    """이미지가 공개 URL 로 올라가 있으면 URL 사용(가벼움+SEO), 아니면 base64 인라인."""
    urls = record.get("image_urls")
    if urls:
        return {int(k): v for k, v in urls.items()}
    return _inlined_images(record, post_dir)


def publish(record: dict, post_dir: Path) -> str:
    """한국어 원문 발행."""
    return _insert(record["article"], _images_for_publish(record, post_dir))


def publish_article(article: dict, record: dict, post_dir: Path) -> str:
    """임의 article(예: 영문 번역본)을 같은 이미지로 발행."""
    return _insert(article, _images_for_publish(record, post_dir))
