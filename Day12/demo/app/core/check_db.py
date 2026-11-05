"""실행: python -m app.core.check_db. 비밀 연결정보는 출력하지 않습니다."""

from app.core.config import get_settings
from app.core.db import Database


def main() -> int:
    database = None
    try:
        database = Database(get_settings())
        database.check_schema()
    except Exception:
        print("DB 확인 실패: .env의 연결정보, TLS, shoppingmall 테이블과 권한을 확인하세요.")
        return 1
    finally:
        if database is not None:
            database.dispose()
    print("DB 확인 완료: shoppingmall의 필수 테이블 5개를 읽을 수 있습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
