"""샘플 상품 INSERT만 실행합니다. 기존 상품은 수정하지 않습니다."""

from app.core.config import PROJECT_ROOT, get_settings
from app.core.db import Database


def main() -> int:
    database = None
    try:
        database = Database(get_settings())
        if database.engine is None:
            raise RuntimeError("DB 설정 없음")
        statement = (PROJECT_ROOT / "db" / "seed.sql").read_text(encoding="utf-8-sig")
        with database.engine.begin() as connection:
            result = connection.exec_driver_sql(statement)
            count = result.rowcount
        print(f"샘플 상품 준비 완료: {count}개 추가. 기존 SKU의 가격·재고는 유지했습니다.")
    except Exception:
        print("샘플 상품 등록 실패: DB 연결·shoppingmall 스키마·권한을 확인하세요.")
        return 1
    finally:
        if database is not None:
            database.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
