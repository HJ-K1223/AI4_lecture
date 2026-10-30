"""로컬 개발용 세션 설정을 보완합니다. 기존 DB 비밀값은 변경·출력하지 않습니다."""

from pathlib import Path
import os
from secrets import token_urlsafe
from urllib.parse import urlsplit

from dotenv import dotenv_values, set_key


def main() -> int:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    values = dotenv_values(env_path) if env_path.exists() else {}
    if os.environ.get("APP_ENV", values.get("APP_ENV", "development")) != "development":
        print("운영 환경에서는 로컬 설정 도구를 실행하지 않습니다.")
        return 1
    updates = {}
    if not values.get("SESSION_SECRET"):
        updates["SESSION_SECRET"] = token_urlsafe(48)
    if not values.get("APP_BASE_URL"):
        updates["APP_BASE_URL"] = "http://127.0.0.1:8012"
    origin = urlsplit(updates.get("APP_BASE_URL", values.get("APP_BASE_URL", "")))
    if not values.get("COOKIE_SECURE") and origin.scheme == "http" and origin.hostname in ("127.0.0.1", "localhost", "::1"):
        updates["COOKIE_SECURE"] = "false"
    for key, value in updates.items():
        set_key(str(env_path), key, value, quote_mode="always", encoding="utf-8")
    print("로컬 설정 확인 완료. 기존 DB 정보는 유지했으며 비밀값은 출력하지 않습니다.")
    print("추가·설정한 키: " + (", ".join(updates) if updates else "없음"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
