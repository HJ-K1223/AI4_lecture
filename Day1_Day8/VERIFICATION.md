# 검증 결과

실행일: 2026-10-23. 기존 학습 파일을 변경하지 않고 `Day1_Day8`만 작성했다.

## 환경

- Windows / Python 3.13.14
- FastAPI 0.150.0 / Uvicorn 0.54.0
- 기존 pytest 9.1.1 / httpx 0.28.1
- 패키지 추가 설치 없음

## 자동 검증

실행 명령:

```powershell
.\.venv\Scripts\python.exe -m pytest Day1_Day8/test_guestbook.py -q --basetemp=Day1_Day8/.test_tmp -o cache_dir=Day1_Day8/.pytest_cache
```

**25 passed, 1 warning in 1.25s**

빈 화면, CSS 응답, 단일 테이블·외래키 없음, 정상 등록과 303 이동, 새 앱 시작 후 저장 보존, 빈 입력·공백·길이·널 문자, 한글·이모지 최대 길이, HTML 이스케이프와 SQL 매개변수 저장, 최신순·페이지 이동, 잘못된 페이지, 중복·누락·초과 필드와 잘못된 UTF-8, Content-Length 없는 요청을 포함한 본문 상한, 용량 초과 시 기존 데이터 보존, 동시 저장 시 개수 제한, DB 장애의 503 응답을 검증했다.

경고 1건은 기존 Starlette TestClient가 httpx 사용의 향후 지원 중단을 알린 것이다. 현재 검사는 통과했으며 새 테스트 라이브러리는 추가하지 않았다.

## 실제 서버 확인

Uvicorn을 `127.0.0.1:8765`에서 실행하고 별도 테스트 DB(`.smoke_tmp/guestbook.db`)를 사용했다. 실제 HTTP로 루트 페이지 200, 폼 등록 후 이동한 페이지 200, 등록한 글 표시, CSS 200을 확인했다. 원문 결과는 `SMOKE_RESULT.txt`에 기록했다. 확인 후 서버를 종료했다. 사용자가 처음 실행하는 기본 `data/guestbook.db`에는 테스트 글을 넣지 않았다.

## 검증 한계

연결된 브라우저가 없어 실제 브라우저의 화면 배치·모바일 레이아웃·클릭 조작은 확인하지 못했다. HTML 응답과 CSS 제공은 검증했지만 시각적 검증을 대체하지 않는다. 무료 호스팅 계정에서 실제 배포·요금·파일 보존은 검증하지 않았다. 관련 조건과 공식 출처는 `DEPLOYMENT.md`를 참고한다.
