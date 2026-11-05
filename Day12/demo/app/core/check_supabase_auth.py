"""공유 환경설정으로 Auth API 접근을 읽기 전용 확인합니다."""

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings


def main() -> int:
    try:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_publishable_key:
            print("Auth 확인 실패: 프로젝트 또는 C:/AI4/.env의 Auth 설정이 필요합니다.")
            return 1
        url = str(settings.supabase_url).rstrip("/")
        if not url.startswith("https://"):
            print("Auth 확인 실패: HTTPS 프로젝트 주소가 필요합니다.")
            return 1
        request = Request(url + "/auth/v1/settings", headers={
            "apikey": settings.supabase_publishable_key.get_secret_value(),
            "Accept": "application/json",
        })
        with urlopen(request, timeout=10) as response:
            if response.status != 200:
                return 1
        print("Supabase Auth API 접근 확인 완료. 계정·세션·데이터는 변경하지 않았습니다.")
        return 0
    except HTTPError as error:
        print(f"Auth API 확인 실패: HTTP {error.code}. 주소·키·프로젝트 상태를 확인하세요.")
    except (URLError, TimeoutError):
        print("Auth API 확인 실패: 네트워크 연결을 확인하세요.")
    except Exception:
        print("Auth API 확인 실패: 환경설정을 확인하세요. 비밀값은 출력하지 않습니다.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
