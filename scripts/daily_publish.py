"""매일 1회 실행 — 자동 생성 + 엄격검증 + 발행 + 텔레그램 보고.

승인 버튼 없이 바로 발행하므로 writer 의 엄격 게이트(write_article_safe)로 안전성을
최대한 확보한다. GitHub Actions cron 등에서 하루 한 번 호출하도록 설계됨.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402

from auto_blog import config, pipeline, publishers, telegram_bot  # noqa: E402


def _host_images_on_github(rec: dict, post_dir):
    """생성된 이미지를 저장소 public/ 에 올리고 raw 공개 URL 을 만든다(가벼운 페이지+SEO).
    GitHub Actions 안(GITHUB_REPOSITORY 설정됨)에서만 동작. 아니면 빈 dict → base64 폴백."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    images = rec.get("images") or {}
    if not repo or not images:
        return {}
    public_dir = ROOT / "public" / rec["dir"]
    public_dir.mkdir(parents=True, exist_ok=True)
    base = f"https://raw.githubusercontent.com/{repo}/main/public/{rec['dir']}"
    urls = {}
    for idx, rel in images.items():
        src = post_dir / rel
        if src.exists():
            name = os.path.basename(rel)
            shutil.copy(src, public_dir / name)
            urls[str(idx)] = f"{base}/{name}"

    def run(*a):
        subprocess.run(a, cwd=str(ROOT), check=False)
    run("git", "config", "user.email", "actions@github.com")
    run("git", "config", "user.name", "github-actions")
    run("git", "add", "public")
    run("git", "commit", "-m", f"images: {rec['dir']}")
    run("git", "push", "origin", "HEAD:main")
    print(f"  이미지 {len(urls)}장 공개 URL 호스팅 완료")
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
