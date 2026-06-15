"""설정 로더 — .env 와 환경변수를 읽어 한곳에서 제공."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv 미설치 환경에서도 import 자체는 깨지지 않게
    def load_dotenv(*_args, **_kwargs):  # type: ignore
        return False

# 회사/보안 프록시가 TLS 를 가로채는 환경에서도 HTTPS 가 되도록
# OS(윈도우) 인증서 저장소를 파이썬 SSL 에 연결한다. 없으면 조용히 통과.
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# 프로젝트 루트 = .../auto_blog
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"          # 산출물(글/이미지/로그)
DATA_DIR.mkdir(exist_ok=True)

load_dotenv(ROOT / ".env")


def get(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def get_bool(key: str, default: bool = False) -> bool:
    val = get(key, str(default)).lower()
    return val in ("1", "true", "yes", "on")


def get_int(key: str, default: int) -> int:
    try:
        return int(get(key, str(default)))
    except ValueError:
        return default


# 자주 쓰는 값
TARGET_GEO = get("TARGET_GEO", "KR")
PUBLISH_HOUR = get_int("PUBLISH_HOUR", 6)
TRANSLATE_TO_ENGLISH = get_bool("TRANSLATE_TO_ENGLISH", True)

OPENAI_API_KEY = get("OPENAI_API_KEY")
GEMINI_API_KEY = get("GEMINI_API_KEY")
ANTHROPIC_API_KEY = get("ANTHROPIC_API_KEY")


def missing_keys(*names: str) -> list[str]:
    """주어진 키 중 비어 있는 것 목록을 돌려준다(사전 점검용)."""
    return [n for n in names if not get(n)]
