"""Blogger 최초 1회 인증 + 연결 확인.

실행하면 브라우저에 구글 로그인/동의 창이 뜬다. 본인 계정으로 허용하면
config/token.json 에 토큰이 저장되고, 이후로는 자동 발행 시 다시 묻지 않는다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auto_blog import config  # noqa: E402
from auto_blog.publishers import blogger  # noqa: E402


def main():
    blog_id = config.get("BLOGGER_BLOG_ID")
    if not blog_id:
        print("❌ .env 의 BLOGGER_BLOG_ID 가 비어 있습니다.")
        return
    print("브라우저에서 구글 로그인/동의 창이 곧 열립니다…")
    print("→ 본인 계정 선택 → '계속' → 권한 허용 을 눌러주세요.\n")
    svc = blogger._service()  # 최초 1회 OAuth (브라우저 동의)
    blog = svc.blogs().get(blogId=blog_id).execute()
    print("\n✅ 인증 성공!")
    print(f"   블로그 이름: {blog.get('name')}")
    print(f"   주소: {blog.get('url')}")
    print(f"   현재 글 수: {blog.get('posts', {}).get('totalItems', 0)}")
    print("\n토큰이 저장됐습니다. 이제 대시보드에서 '승인'만 누르면 자동 게시됩니다.")


if __name__ == "__main__":
    main()
