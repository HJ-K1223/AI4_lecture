"""Supabase 연결과 테이블을 읽기 전용으로 확인한다. 비밀 값은 출력하지 않는다."""
import sys

import psycopg

from main import BASE_DIR, load_database_config, connect


def main() -> int:
    try:
        settings = load_database_config(BASE_DIR / "config.json")
        with connect(settings) as connection:
            connection.execute("SET TRANSACTION READ ONLY")
            connection.execute("SELECT id, name, message, created_at FROM guestbook LIMIT 0")
        print("Supabase 연결 및 guestbook 열 조회 성공 (읽기 전용)")
        return 0
    except RuntimeError:
        print("설정 파일의 경로와 필수 항목을 확인해 주세요.")
    except psycopg.Error as error:
        print(f"DB 연결 또는 테이블 확인 실패 ({type(error).__name__}). 연결 설정과 네트워크를 확인해 주세요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
