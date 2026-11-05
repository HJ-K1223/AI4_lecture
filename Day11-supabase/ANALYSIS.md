# Day1~Day8 분석과 구현 연결

소스 파일을 읽어 핵심 문법과 기존 의존성을 확인했습니다. 학습용 파일에는 의도적인 오류 예제가 있으므로 전체 수업 코드를 일괄 실행하거나 수정하지 않았습니다. Day5 폴더는 현재 저장소에 없습니다.

| 수업 | 확인한 내용과 대표 파일 | 방명록에 적용 |
| --- | --- | --- |
| Day1 | `day1_practice.py`: 변수, 문자열, if, for/while, 리스트, 함수, 예외 처리. `day1_modules`: 모듈 분리 | 함수 분리, 글 목록 반복 출력, 문자열 작성 |
| Day2 | 오전 조건·반복·컴프리헨션, 오후 `main.py`의 누적 계산·반환·assert, `day2-3.py`의 문자열 정리 | 입력 정리, 길이와 글 수 조건 검사, 목록 누적 |
| Day3 | 오전 클래스·생성자·상속·추상화, 오후 주문 계산 함수의 타입·범위 검사와 예외 | Pydantic 모델로 입력 정의, 검증 실패 처리. 불필요한 상속 구조는 추가하지 않음 |
| Day4 | `day4-1.py`: random, 리스트와 인덱스, 범위를 벗어난 접근 오류 예제 | 목록 범위와 페이지 번호 경계 처리. 난수는 필요 없어 사용하지 않음 |
| Day5 | 폴더 없음 | 분석에서 제외 |
| Day6 | BaseModel, Field, validator, 직렬화, FastAPI. `ch08_project`: 모델·라우트·저장소 CRUD | FastAPI 라우트, Pydantic 입력 모델, 422 검증. 메모리 저장은 요청한 SQLite로 교체 |
| Day7 | FastAPI, async/await, httpx, 외부 요청 순차·병렬 처리, 정적 화면 예제 | 요청 본문 수신에 async 사용. 외부 API 호출·비동기 병렬 처리는 필요 없어 추가하지 않음 |
| Day8 | 요청 파라미터, 입력 검증, HTTPException과 오류 상태, 응답 계약, TestClient·pytest 시나리오 | 성공 303, 잘못된 폼 422, 용량 초과 409/413, 저장소 장애 503과 상태 기반 테스트 |

## 기술 선택

외부 라이브러리는 수업에 있는 `fastapi`, `pydantic`, `uvicorn`만 실행 의존성으로 선언했습니다. 테스트는 기존 `pytest`, `httpx`를 사용합니다. 새 외부 라이브러리나 별도 알고리즘 패키지는 도입하지 않았습니다.

`sqlite3`는 요청에 명시된 Python 내장 DB입니다. 그 밖의 `html.escape`, `urllib.parse`, `pathlib`, `datetime`, `contextlib`, `os`는 기본 입출력·문자열·파일·날짜 처리를 위한 표준 라이브러리입니다. 템플릿 엔진 대신 고정 HTML의 자리표시자를 한 번만 치환하고 모든 사용자 입력을 이스케이프합니다.

단순한 조건·반복, `COUNT`, 기본 키 역순 정렬, `LIMIT/OFFSET`만으로 목록과 페이지 이동을 구성했습니다. 관계형 모델, ORM, 검색 엔진, 캐시, 인증 프레임워크는 필요하지 않습니다. DB 작업은 FastAPI의 기존 스레드 실행 기능으로 수행합니다.

## 저장 구조

```sql
CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 30),
    message TEXT NOT NULL CHECK(length(message) BETWEEN 1 AND 1000),
    created_at TEXT NOT NULL
);
```

테이블은 하나이며 릴레이션이 없습니다. `AUTOINCREMENT`를 사용하지 않아 SQLite의 별도 순번 테이블도 생성하지 않습니다. 글 수 검사와 삽입은 같은 쓰기 트랜잭션으로 실행합니다. 영구 보존은 DB 파일이 위치한 호스팅 디스크의 수명에 달려 있으며, 무료 배포 조건은 README에 명시했습니다.
