"""매일 1회 실행 — 자동 생성 + 엄격검증 + 발행 + 텔레그램 보고.

승인 버튼 없이 바로 발행하므로 writer 의 엄격 게이트(write_article_safe)로 안전성을
최대한 확보한다. GitHub Actions cron 등에서 하루 한 번 호출하도록 설계됨.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auto_blog import config, pipeline, publishers, telegram_bot  # noqa: E402


def main():
    rec = pipeline.run_auto()
    post_dir = config.DATA_DIR / "posts" / rec["dir"]

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
