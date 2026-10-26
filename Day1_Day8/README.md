# 작은 방명록

Day1~Day8 학습 내용을 사용한 HTML 중심의 방명록입니다. 이름·내용 등록과 최신순 목록을 한 화면에서 제공합니다. 사용자 승인에 따라 기존 FastAPI·Uvicorn과 Python 기본 SQLite를 사용했습니다. 추가 라이브러리는 설치하지 않았습니다.

## 실행

Python 3.10 이상이 필요합니다. 현재 프로젝트의 기존 가상환경에서 PowerShell로 실행합니다.

```powershell
cd C:\AI4
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir Day1_Day8 --host 127.0.0.1 --port 8000 --workers 1
```

브라우저에서 http://127.0.0.1:8000 을 엽니다. 종료는 터미널에서 Ctrl+C입니다. 처음 시작할 때 `Day1_Day8/data/guestbook.db`가 자동 생성됩니다.

새 환경에서만 `python -m pip install -r requirements.txt`로 같은 두 라이브러리를 설치합니다. 기존 가상환경에는 재설치할 필요가 없습니다. 배포에서는 `requirements-dev.txt`를 설치하지 않습니다.

## 사용과 범위

이름(1~20자)과 내용(1~500자)을 입력하고 **글 남기기**를 누릅니다. 앞뒤 공백은 제거하며, 내용 안의 줄바꿈은 유지합니다. 최신 글부터 10개씩 표시합니다. 등록 후 이동한 화면을 새로고침하면 폼을 다시 전송하지 않습니다. 버튼을 여러 번 누르면 별도 글이 등록될 수 있습니다.

SQLite 파일에는 `guestbook` 테이블 하나만 있습니다. `id INTEGER PRIMARY KEY`, `name TEXT`, `message TEXT`, `created_at TEXT`로 구성하며 관계나 외래키는 없습니다. 생성 시간은 한국 시간(+09:00)으로 기록합니다.

저장 상한은 1,000건입니다. 가득 차면 기존 글을 보존하고 새 글을 409로 거절합니다. 요청 본문은 16 KiB까지만 받습니다. 인증·수정·삭제·업로드·검색 기능은 기본 범위에 포함하지 않았습니다. 공개 글만 입력해야 합니다.

## 파일 안내

| 파일 | 역할 |
| --- | --- |
| main.py | 폼 해석, 입력 검사, SQLite 저장·조회, HTML 응답 |
| templates/index.html | 단일 화면의 HTML |
| static/style.css | 모바일 대응을 포함한 작은 CSS |
| ANALYSIS.md | 실제 Day1~Day8 자료 분석과 기술 선택 |
| DEPLOYMENT.md | 무료 배포 가능 조건과 제약 |
| test_guestbook.py | HTTP 계약, 저장 지속성, 한도·오류 검증 |
| VERIFICATION.md | 실제 검증 결과와 확인하지 못한 범위 |

## 테스트

기존 가상환경의 pytest·httpx를 사용합니다. 테스트 데이터는 `Day1_Day8/.test_tmp`에 생성하며 실제 방명록 DB와 분리합니다. 남아 있는 테스트 폴더와 보고서는 배포 대상에서 제외할 수 있습니다.

```powershell
cd C:\AI4
.\.venv\Scripts\python.exe -m pytest Day1_Day8/test_guestbook.py -q --basetemp=Day1_Day8/.test_tmp -o cache_dir=Day1_Day8/.pytest_cache
```

## 학습 순서

1. `index.html`의 `form`, `name`, `method`, `action`을 확인합니다.
2. `main.py`의 `read_form` → `create_entry`에서 입력을 검사하는 흐름을 봅니다.
3. `save_entry`의 SQL 매개변수와 트랜잭션을 확인합니다.
4. `render_page`의 반복문, HTML 이스케이프, LIMIT/OFFSET을 읽습니다.
5. 테스트에서 정상 입력과 경계값, 오류 발생 전후의 DB 상태를 비교합니다.

`sqlite3`, URL 인코딩 폼 해석, SQL 트랜잭션·페이지 조회는 이번 앱에 새로 적용한 내용입니다. Pydantic·비동기 병렬 호출·상속을 모두 넣기보다, 작은 방명록에 필요한 부분만 사용했습니다.
