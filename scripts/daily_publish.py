"""매일 1회 실행 — 자동 생성 + 엄격검증 + 발행 + 텔레그램 보고.

승인 버튼 없이 바로 발행하므로 writer 의 엄격 게이트(write_article_safe)로 안전성을
최대한 확보한다. GitHub Actions cron 등에서 하루 한 번 호출하도록 설계됨.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import base64 as _b64  # noqa: E402
import os  # noqa: E402

import requests  # noqa: E402

from auto_blog import config, pipeline, publishers, telegram_bot  # noqa: E402


def _host_images_on_github(rec: dict, post_dir):
    """생성 이미지를 GitHub Contents API 로 직접 업로드해 raw 공개 URL 을 만든다.

    git push 가 아니라 API 라서 동시 커밋이 있어도 서버가 순서를 처리 → 푸시 거부(race)가
    구조적으로 발생하지 않는다. Actions 밖이거나 일부라도 실패하면 빈 dict → base64 폴백
    (이미지가 절대 깨지지 않게)."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    images = rec.get("images") or {}
    if not repo or not token or not images:
        return {}
    urls = {}
    for idx, rel in images.items():
        src = post_dir / rel
        if not src.exists():
            continue
        path = f"public/{rec['dir']}/{os.path.basename(rel)}"
        try:
            r = requests.put(
                f"https://api.github.com/repos/{repo}/contents/{path}",
                headers={"Authorization": f"token {token}",
                         "Accept": "application/vnd.github+json"},
                json={"message": f"image: {path}",
                      "content": _b64.b64encode(src.read_bytes()).decode(),
                      "branch": "main"},
                timeout=60)
        except requests.RequestException as e:
            print(f"  [경고] 이미지 업로드 오류: {e}")
            r = None
        if r is not None and r.status_code in (200, 201):
            urls[str(idx)] = f"https://raw.githubusercontent.com/{repo}/main/{path}"
        else:
            code = r.status_code if r is not None else "ERR"
            print(f"  [경고] 이미지 업로드 실패({code}) → base64 폴백")
    # 전부 성공해야 URL 사용(일부 실패면 일관성 위해 base64 폴백)
    if len(urls) != len(images):
        return {}
    print(f"  이미지 {len(urls)}장 공개 URL 호스팅 완료(API, 충돌 불가)")
    return urls


def main():
    rec = pipeline.run_auto()
    post_dir = config.DATA_DIR / "posts" / rec["dir"]

    # 이미지를 공개 URL 로 호스팅(가능하면) → 본문이 가벼워지고 구글 이미지검색 노출
    rec["image_urls"] = _host_images_on_github(rec, post_dir)

    print("⑥ 발행 중…")
    results = publishers.publish(rec, post_dir)
    rec["status"] = "published"
    rec["publish_results"] = results
    import json
    (post_dir / "article.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in results.items():
        print(f"  {k}: {v}")

    print("⑦ 텔레그램 보고…")
    telegram_bot.send_report(rec, results)
    print("완료 ✅")


if __name__ == "__main__":
    main()
