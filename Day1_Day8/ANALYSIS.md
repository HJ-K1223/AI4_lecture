# Day1~Day8 분석과 방명록 설계

검토일: 2026-10-23. 기존 학습 파일은 수정하지 않는다.

## 실제 자료에서 확인한 내용

| 자료 | 문법·알고리즘 | 방명록 적용 |
| --- | --- | --- |
| Day1/day1-1.py ~ day1-5.py | 변수, 형 변환, 비교·산술 연산, if/elif/else, 리스트, for/range, 중첩 반복, while/break, 난수 숫자 맞히기 | 문자열 길이와 빈 입력 검사, 목록 출력. 난수 게임은 앱에 불필요 |
| Day2/Morning, Afternoon | 논리·포함 연산, 단락 평가, dict 순회, 함수, 컴프리헨션, 짝수 누적, FizzBuzz, 정규식 금지어 마스킹 | 조건 검사, 입력 딕셔너리 처리, HTML 목록 결합. 금지어·분석 기능은 요구하지 않아 제외 |
| Day3/Morning | 클래스, 생성자, 인스턴스 상태, 상속·다형성, 추상 메서드, dataclass | 작은 앱이므로 상속 구조 없이 함수로 구성 |
| Day3/Afternoon | enumerate, split, dict 변환, try/except, 사용자 정의 예외, 주문·점수 전처리 | 폼 해석, 잘못된 입력과 DB 오류 처리 |
| Day4/Morning/day4-1.py | print(10+20)만 확인 | 이 파일만으로 추가 학습 내용 추정 불가 |
| Day5 | 폴더 없음 | 별도 FastAPI 실습 폴더를 보조 자료로 사용하되 Day5 자료로 단정하지 않음 |
| 05.FastAPI-uvicorn/labs, fastapi_win_vscode/labs | FastAPI 객체, 경로 데코레이터, 매개변수, HTTP 응답 | GET 목록·POST 등록 경로 |
| Day6/ch02~ch07 | BaseModel, 타입 힌트, Field 경계값, validator, 중첩 모델, 직렬화, CRUD와 상태 | 서버 입력 검증 원칙 적용. HTML 폼에는 간단한 함수 검사 사용 |
| Day7/01~03, stock_lab | async/await, asyncio, 순차·병렬 외부 요청, 블로킹 비교, 시간 측정 | 외부 API 없음. SQLite 작업은 동기 함수에서 수행하여 이벤트 루프의 블로킹을 피함 |
| Day8/lesson_01~08 | Swagger/OpenAPI, Path/Query, 본문 검증, 오류 상태, 응답 계약, 상태 시나리오, pytest/TestClient | 정상 등록, 경계값, 실패 시 상태 보존, 저장 지속성 등을 검증 |
| fastapi_calculator/main.py | HTMLResponse, html.escape, string.Template, 정적 CSS | 기존 HTML 중심 서버 렌더링 방식을 재사용 |

## 최소 설계 제안

- 기존 FastAPI·Uvicorn과 Python 표준 모듈만 사용한다. React, Vue, JavaScript, ORM, Jinja2, python-multipart는 추가하지 않는다.
- 화면 하나에 이름·내용 입력 폼과 최신순 목록을 배치한다. 브라우저 기본 POST 폼을 사용한다.
- sqlite3로 guestbook 테이블 하나만 사용한다. id, name, message, created_at 네 열이며 외래키·관계 테이블은 없다.
- SQL의 INTEGER PRIMARY KEY로 ID를 생성한다. 메모리 dict의 max()+1 대신 DB가 동시 요청의 ID를 관리한다.
- 이름 1~20자, 내용 1~500자, 요청 본문 16 KiB, 저장 최대 1,000건, 목록은 10건씩 제공한다. 한도 도달 시 기존 글을 지우지 않고 신규 등록을 거절한다.
- 사용자 입력은 SQL 매개변수로 저장하고 HTML escape로 출력한다. 등록 성공 뒤 303 이동하여 새로고침 재등록을 줄인다.
- 인증, 수정·삭제, 이미지 업로드, 외부 API, 실시간 통신은 기본 방명록 범위에 포함하지 않는다.

## 확인할 제약

사용자가 1번(FastAPI·Uvicorn 유지 + Python 기본 모듈) 구성을 승인하여 위 방식으로 구현했다. 서비스 배포는 이번 요청의 전제 조건이며, 계정 생성이나 실제 공개 배포를 의미하지 않는다. 현재 요청은 Day1_Day8 폴더에 코드와 문서를 작성하는 범위다.

무료 호스팅의 데이터 보존·사용량은 앱의 글 개수 제한만으로 보장할 수 없다. 실제 서비스의 무료 플랜과 영구 파일 저장 지원을 따로 확인해야 한다.
