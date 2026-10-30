# 검증 결과

검증일: 2026-10-23

- 기존 `.venv`의 FastAPI 0.115.12, Pydantic 2.11.5, Uvicorn 0.34.2, httpx 0.28.1, pytest 8.3.5 사용. 추가 패키지 설치 없음.
- `python -m pytest Day1-Day8/test_guestbook.py -q --tb=short`: **15 passed**.
- 첫 테스트 시도는 Windows 임시 폴더 접근 권한으로 실패했고, 샌드박스 밖 재실행에서 전체 통과했습니다.
- 기존 Starlette/AnyIO 조합에서 사용 중단 예고 경고 1건이 있으나 기능 테스트 실패는 없습니다. 기존 수업 버전을 유지했습니다.
- Uvicorn을 실제 실행해 `GET /` 200, HTML 폼 포함, `GET /health` 200 및 `{"status":"ok"}` 확인.
- 브라우저 연결 목록이 비어 있어 화면의 시각적 확인과 브라우저를 통한 직접 제출은 수행하지 못했습니다. 폼 제출 및 리다이렉트는 TestClient로 검증했습니다.
- 호스팅 계정 연결·외부 배포는 수행하지 않았습니다. 무료 배포 설정과 SQLite 데이터 소실 조건은 README에 기록했습니다.

테스트 데이터는 임시 DB에만 작성했으며 기본 방명록에는 예시 글을 넣지 않았습니다.
