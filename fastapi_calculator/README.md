# 두 숫자 계산기

두 값을 입력하면 덧셈·뺄셈·곱셈·나눗셈 결과를 한 화면에 표시하는 FastAPI 학습용 프로젝트입니다.

- 백엔드: Python / FastAPI / Uvicorn
- 프론트엔드: HTML / CSS
- JavaScript 없이 HTML 폼을 제출하고, 서버가 계산 결과를 포함한 HTML을 돌려줍니다.
- 저장 위치: `C:\AI4\fastapi_calculator`

## 1. 실행 방법 (Windows PowerShell)

Python 3.13에서 검증했습니다. 터미널에서 다음 명령을 순서대로 실행하세요.

```powershell
cd C:\AI4\fastapi_calculator
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

브라우저에서 http://127.0.0.1:8000 에 접속합니다.

가상환경의 Python 경로를 직접 사용하므로 활성화 명령을 실행할 필요가 없습니다. `python` 명령을 찾지 못하면 Python 설치와 PATH를 확인하거나 `py -m venv .venv`를 사용하세요.

- 종료: 서버를 실행한 터미널에서 `Ctrl+C`
- 코드 수정 자동 반영: `--reload`
- 8000 포트가 이미 사용 중인 경우: 마지막 명령에 `--port 8001`을 추가하고 http://127.0.0.1:8001 에 접속
- `main:app`: `main.py` 파일 안의 `app` 객체를 실행한다는 의미
- HTML 파일을 직접 여는 대신 반드시 FastAPI 주소로 접속하세요.

## 2. 사용 방법과 계산 규칙

1. 첫 번째 값과 두 번째 값을 입력합니다.
2. '계산하기'를 누릅니다. 입력 후 Enter로도 제출할 수 있습니다.
3. 같은 페이지에서 네 가지 결과를 확인합니다. 입력값은 유지됩니다.

예: 첫 번째 값 10, 두 번째 값 2 → 덧셈 12 / 뺄셈 8 / 곱셈 20 / 나눗셈 5

- 뺄셈: 첫 번째 값 - 두 번째 값
- 나눗셈: 첫 번째 값 / 두 번째 값
- 정수, 음수, 소수를 지원합니다.
- 허용 크기: 각 값이 -1,000,000,000,000 이상, 1,000,000,000,000 이하
- 소수점 아래 최대 12자리까지 입력할 수 있습니다.
- 쉼표와 지수 표기는 사용하지 않습니다. `1,000`, `1e3` 대신 `1000`을 입력하세요.
- 두 번째 값이 0이면 나눗셈 결과에 안내 문구를 표시하고 다른 계산은 정상적으로 제공합니다.
- 덧셈·뺄셈·곱셈은 입력 범위 안에서 Decimal로 정확하게 계산합니다.
- 나눗셈은 소수점 아래 12자리로 반올림합니다. 기본 반올림 방식은 ROUND_HALF_EVEN입니다.
- 결과의 불필요한 소수점 뒤 0은 제거합니다.
- 빈 값, 잘못된 숫자, 허용 범위를 벗어난 값은 브라우저 또는 서버에서 검사합니다.
- 서버에서 입력 오류를 발견하면 HTTP 422와 읽기 쉬운 오류 화면을 응답합니다.

## 3. 파일 구성

```text
fastapi_calculator/
├── main.py                # FastAPI 경로, 입력 검사, 계산, HTML 렌더링
├── templates/
│   └── index.html         # 입력 폼과 결과 표시 영역
├── static/
│   └── style.css          # 색상, 배치, 모바일 대응
├── test_main.py           # 자동 검증 테스트 8개
├── requirements.txt       # 앱 실행용 패키지와 검증한 버전
├── requirements-dev.txt   # 테스트용 추가 패키지
├── .gitignore
└── README.md
```

## 4. 요청이 처리되는 흐름

```text
브라우저: 숫자 10, 2 입력 후 버튼 클릭
    ↓ HTML form의 GET 요청
GET /calculate?first=10&second=2
    ↓ FastAPI가 first, second 문자열을 함수에 전달
parse_number(): 입력 형식·크기·소수 자릿수 검사 후 Decimal 변환
    ↓
calculate(): 사칙연산 수행
    ↓
render_page(): 결과를 HTML 템플릿에 삽입
    ↓ HTTP 200, HTML 응답
브라우저: CSS를 적용한 결과 화면 표시
```

조회 성격의 계산이고 저장 데이터를 변경하지 않으므로 GET을 사용했습니다. 입력값은 주소창에 나타납니다. POST와 JSON 방식은 이 예제의 필수 요소가 아닙니다.

| 경로 | 역할 |
|---|---|
| `GET /` | 빈 계산기 화면 |
| `GET /calculate?first=10&second=2` | 입력값 검사와 계산 결과 화면 |
| `GET /static/style.css` | CSS 제공 |
| `GET /docs` | FastAPI가 자동 생성한 API 문서 |

이 앱의 계산 경로는 JSON이 아닌 HTML을 반환합니다. `/docs`에서 호출해도 응답 본문은 HTML이며, 완성된 화면은 기본 주소에서 확인하세요.

## 5. Python 문법과 FastAPI 개념

| 코드 | 의미 |
|---|---|
| `FastAPI(...)` | API 앱 객체 생성 |
| `@app.get(...)` | GET 요청 경로를 바로 아래 함수에 연결 |
| `response_class=HTMLResponse` | 응답이 HTML이라는 것을 FastAPI에 알림 |
| `first: str = ""` | 문자열 매개변수이며 누락 시 빈 문자열 사용 |
| `Decimal(text)` | 문자열을 십진수 계산용 숫자로 변환 |
| `raise ValueError(...)` | 입력값 문제를 알리는 예외 발생 |
| `try` / `except` | 예외를 잡아 오류 화면으로 바꿈 |
| `with localcontext()` | 해당 블록 안에서만 Decimal 계산 설정 변경 |
| `list[tuple[str, str, str]]` | 문자열 3개로 구성된 튜플들의 리스트 |
| `for name, symbol, value in results` | 각 튜플의 세 값을 변수로 나누어 받음 |
| `Template.substitute(...)` | HTML의 `$first` 같은 표시 자리를 값으로 교체 |
| `escape(...)` | 사용자 입력이 HTML 태그나 속성으로 해석되지 않도록 변환 |
| `Path(__file__).resolve().parent` | 현재 Python 파일이 있는 폴더의 절대 경로 |

`pathlib.Path`는 파일 경로를 다루는 Python 기능입니다. FastAPI의 경로 검사용 `Path`와는 다릅니다.

Python이 계산을 담당하고 HTML은 화면 구조, CSS는 모양을 담당합니다. 별도의 템플릿 패키지와 폼 파싱 패키지는 필요 없습니다.

## 6. 검증 방법 및 결과

2026-10-20 검증 환경: Windows / Python 3.13.14 / FastAPI 0.150.0 / Uvicorn 0.54.0 / Pydantic 2.14.1 / HTTPX 0.28.1

기존 `C:\AI4\05.FastAPI-uvicorn\.venv` 환경을 이용해 실제 FastAPI TestClient 요청으로 테스트했습니다. 신규 가상환경의 패키지 설치는 별도로 실행하지 않았습니다.

**자동 테스트 8개 모두 통과했습니다.**

- 초기 화면과 CSS 응답
- 사칙연산 결과 및 결과 HTML
- 소수의 정확한 덧셈과 음수 계산
- 0으로 나눌 때 나머지 결과 유지
- 반복소수의 반올림
- 빈 값·문자·NaN·무한대·지수 표기·범위 초과 등 잘못된 입력
- 경계값과 매우 작은 나눗수
- 사용자 입력의 HTML 이스케이프

실제 Uvicorn 서버를 로컬 8765 포트에서 실행하고 브라우저로 다음도 확인했습니다.

- 10과 2를 입력해 버튼 제출 → 12, 8, 20, 5 표시
- 두 번째 값을 0으로 변경해 제출 → 나눗셈 안내 문구 및 다른 연산 결과 표시
- HTML과 CSS가 함께 제공되는 화면 확인

테스트 재실행:

```powershell
cd C:\AI4\fastapi_calculator
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest -v
```

검증 환경의 Starlette는 HTTPX 기반 TestClient에 대해 사용 중단 예정 경고를 표시합니다. 현재 테스트는 정상 통과했으며 앱 실행에는 HTTPX가 필요하지 않습니다.

자동 테스트는 명시한 입력과 동작을 검증합니다. 모든 브라우저 크기에서의 배치나 모든 환경의 동작까지 보장하는 것은 아닙니다.

## 7. 참고 문서

- [FastAPI HTML 응답](https://fastapi.tiangolo.com/advanced/custom-response/#html-response)
- [FastAPI 정적 파일 제공](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Python Decimal](https://docs.python.org/3/library/decimal.html)
- [Python string.Template](https://docs.python.org/3/library/string.html#template-strings)
