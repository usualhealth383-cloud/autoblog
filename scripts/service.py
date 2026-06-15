"""오토블로그 상시 서비스.

하나의 프로세스가:
  1) 텔레그램 버튼(승인/반려)을 계속 수신하고
  2) 매일 PUBLISH_HOUR(기본 06:00)에 글을 자동 생성해 텔레그램으로 검토 요청을 보낸다.

PC가 켜져 있는 동안 계속 돌아야 한다(작업 스케줄러로 자동 시작 권장).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auto_blog import config, pipeline, telegram_bot  # noqa: E402


def generate_and_notify():
    """글 자동 생성(트렌드→안전주제→근거→작성→검증→이미지) 후 텔레그램 검토 요청."""
    rec = pipeline.run(generate_images=True)
    if not rec:
        # 발행할 안전한 주제가 없으면 알림만
        for cid in telegram_bot._load_chats():
            import requests
            requests.post(f"{telegram_bot.API}/sendMessage",
                          data={"chat_id": cid,
                                "text": "ℹ️ 오늘은 적합한 안전 주제가 없어 글 생성을 건너뜁니다."},
                          timeout=30)
        return
    post_dir = config.DATA_DIR / "posts" / rec["dir"]
    telegram_bot.send_for_approval(rec, post_dir)
    print(f"  검토 요청 전송 완료: {rec['article'].get('title')}")


if __name__ == "__main__":
    hour = config.PUBLISH_HOUR
    print(f"=== 오토블로그 서비스 시작 (매일 {hour:02d}:00 자동 생성) ===")
    telegram_bot.run_bot(daily_job=generate_and_notify, daily_hour=hour)
