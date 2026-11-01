# Day13 — main.py로 배우는 Supabase 회원가입·로그인 API

이 문서는 같은 폴더의 `main.py`를 Python 초보자 관점에서 읽기 위한 학습 자료입니다. 모듈의 역할 → Python 문법 → 실제 요청 처리 순서로 설명합니다.

> 현재 `main.py`의 1~77줄(설정·회원가입)과 78~122줄(로그인)을 기준으로 작성했습니다. 편집기의 줄 번호는 1부터 시작합니다. 과거의 URL 메서드 호출 오류와 `persist_ssession` 오타는 현재 수정된 상태입니다. 이 문서 갱신 과정에서 `main.py`는 수정하지 않았습니다.

| 코드 위치 | 학습 내용 | 문서 위치 |
|---|---|---|
| 1~23줄 | 모듈, 환경변수, 앱 생성 | 2~5절 |
| 25~40줄 | 회원가입 데이터 모델과 검증 오류 처리 | 6~9절 |
| 42~76줄 | 회원가입 요청, HTTP 통신, 예외 처리 | 10~15절 |
| 78~91줄 | 로그인 입력·출력 모델 | 20~21절 |
| 93~110줄 | 로그인 경로와 Supabase 인증 호출 | 22~23절 |
| 111~122줄 | 세션·사용자 추출, 캐시 설정, 토큰 반환 | 24~26절 |

## 1. 이 프로그램은 무엇을 하나요?

사용자가 보낸 이메일과 비밀번호를 검사한 뒤, Supabase Auth에 회원가입 또는 로그인을 요청하는 웹 API입니다. 회원가입은 안내 메시지를, 로그인은 토큰과 사용자 정보를 반환합니다.

**API**는 다른 프로그램이 정해진 주소와 형식으로 기능을 요청할 수 있게 만든 창구입니다. 여기서는 `POST /auth/signup`이 회원가입 창구입니다.

```text
사용자 화면 또는 API 테스트 도구
    │ 이메일과 비밀번호를 JSON으로 전송
    ▼
FastAPI 서버: POST /auth/signup
    │ Pydantic으로 입력값 검사
    │ Supabase Python 클라이언트로 회원가입 요청
    ▼
Supabase Auth
    │ 회원가입 처리 또는 오류 응답
    ▼
FastAPI 서버 → 사용자에게 안내 메시지 또는 오류 전달
```

여기에는 서로 다른 두 번의 통신이 있습니다. 사용자 프로그램이 **우리 FastAPI 서버**에 요청하고, 우리 서버가 다시 **Supabase 서버**에 요청합니다. HTTPX는 두 번째 통신에 사용됩니다.

현재는 `POST /auth/signup`과 `POST /auth/login`이 구현되어 있습니다. JWT를 검증해 메모 API를 보호하거나, 토큰 갱신·로그아웃을 처리하는 경로는 아직 없습니다.

## 2. import와 모듈부터 이해하기

**모듈**은 다른 코드에서 가져다 쓸 수 있도록 기능을 묶은 단위입니다. 여러 모듈을 묶은 패키지나 라이브러리도 보통 대화에서는 모듈이라고 부릅니다.

- `import os`: `os`를 가져옵니다. 사용할 때는 `os.getenv(...)`처럼 이름을 붙입니다.
- `from dotenv import load_dotenv`: `dotenv`에서 특정 기능을 가져옵니다. 이후 `load_dotenv(...)`로 바로 사용합니다.

| 가져온 도구 | 간단한 설명 | 이 파일에서 하는 일 |
|---|---|---|
| `os` | 운영체제 관련 기능을 제공하는 Python 기본 모듈 | 환경변수 읽기 |
| `dotenv` | `.env` 파일을 읽는 외부 라이브러리. 설치 이름은 `python-dotenv` | URL과 키를 환경변수로 불러오기 |
| `fastapi` | Python으로 웹 API를 만드는 프레임워크 | 주소 등록, 요청 수신, 응답 반환 |
| `pydantic` | 데이터 구조와 검증 규칙을 정의하는 라이브러리 | 이메일 형식, 비밀번호 길이 검사 |
| `supabase` | Supabase 서비스를 Python에서 호출하는 SDK | Auth 회원가입·로그인 요청 |
| `httpx` | 다른 서버와 HTTP/HTTPS 통신을 하는 라이브러리 | Supabase 통신에 사용할 연결과 타임아웃 관리 |

**프레임워크**는 프로그램의 실행 틀을 제공하는 도구입니다. 이 코드에서는 FastAPI가 요청을 받은 뒤 우리가 작성한 함수를 호출합니다. **SDK**는 특정 서비스의 API를 편하게 사용하도록 만든 도구 모음입니다.

## 3. 자주 등장하는 Python 표현

| 표현 | 의미 | 이 코드의 예 |
|---|---|---|
| 변수 | 값에 붙인 이름 | `supabase_key` |
| 함수 | 특정 작업을 수행하는 코드 묶음 | `signup(...)` |
| 인수 | 함수를 호출하면서 전달하는 값 | `load_dotenv(override=True)`의 `True` |
| 클래스 | 객체의 구조와 동작을 정의하는 틀 | `SignupRequest` |
| 객체 | 클래스로 만들어진 실제 값 | 검증된 요청 객체 `body` |
| 메서드 | 객체나 클래스에 속한 함수 | `body.password.get_secret_value()` |
| 속성 | 객체에 속한 값이나 기능 | `body.email`, `supabase.auth` |
| `return` | 함수 실행을 끝내고 결과를 돌려줌 | `return SignupResponse(...)` |
| `raise` | 예외를 발생시켜 정상 흐름을 중단 | `raise HTTPException(...)` |

`email: EmailStr`의 콜론은 **타입 힌트**입니다. 이 값에 어떤 종류의 데이터가 와야 하는지 표시합니다. Python 자체가 모든 타입 힌트를 자동 검사하는 것은 아니지만, FastAPI와 Pydantic은 이를 읽고 실제 검증에 사용합니다.

## 4. 환경변수와 load_dotenv

### 환경변수란?

프로그램이 실행될 때 외부에서 읽을 수 있는 이름과 값의 쌍입니다. 서버 주소나 API 키 같은 설정을 코드와 분리할 때 사용합니다.

`.env`는 이런 설정을 적는 텍스트 파일입니다. 예를 들어 `SUPABASE_URL=https://example.supabase.co`처럼 작성합니다. `.env` 파일이 존재한다고 Python이 저절로 읽는 것은 아닙니다.

### load_dotenv(override=True)

`load_dotenv()`가 `.env`의 설정을 현재 Python 프로세스의 환경변수에 넣습니다. 인수를 생략하면 라이브러리의 탐색 규칙에 따라 `.env`를 찾습니다.

`override=True`는 같은 이름의 환경변수가 이미 있어도 `.env`에 적힌 값으로 덮어쓰라는 의미입니다. 기본값인 `False`는 기존 값을 유지합니다. 운영체제 설정 자체를 영구적으로 바꾸는 동작은 아닙니다. [python-dotenv 공식 문서](https://github.com/theskumar/python-dotenv#variable-expansion)

### os.getenv(...)

`os.getenv('SUPABASE_URL')`은 해당 이름의 환경변수 값을 읽습니다. 값이 없고 별도 기본값도 지정하지 않았다면 `None`을 반환합니다. `None`은 문자열이 아니라 ‘값이 없음’을 나타내는 Python 값입니다.

### strip(), rstrip(), rsplit()의 차이

| 메서드 | 동작 | 예시 결과 |
|---|---|---|
| `.strip()` | 문자열 양쪽의 공백 제거 | `' abc '.strip()` → `'abc'` |
| `.rstrip('/')` | 문자열 오른쪽 끝의 `/` 제거 | `'https://a.co/'.rstrip('/')` → `'https://a.co'` |
| `.rsplit('/')` | 오른쪽 기준으로 문자열 분리. 반환값은 리스트 | `'a/b'.rsplit('/')` → `['a', 'b']` |

`rsplit`에 분리 횟수를 지정하지 않으면 모든 구분자를 기준으로 나눕니다. URL은 `https://`에도 슬래시가 들어 있으므로 URL 끝의 슬래시만 지우려는 용도로 적절하지 않습니다.

현재 코드는 `os.getenv('SUPABASE_URL').strip().rstrip('/')`입니다. 환경변수를 문자열로 읽은 뒤 공백과 끝의 슬래시를 제거합니다. 이전의 `.strip.rsplit(...)` 오류는 수정되었습니다. 메서드를 실행하려면 `.strip()`처럼 괄호가 필요하고, URL 문자열을 유지하려면 분리 결과인 리스트를 반환하는 `rsplit()`과 구분해야 합니다.

다만 환경변수가 아예 없으면 `os.getenv()`가 `None`을 반환하므로 현재 코드는 `.strip()`에서 실패합니다. 다음은 이 경우까지 고려한 보완 예시이며, 원본에는 적용하지 않았습니다.

```python
supabase_url = (os.getenv('SUPABASE_URL') or '').strip().rstrip('/')
supabase_key = (os.getenv('SUPABASE_PUBLISHABLE_KEY') or '').strip()
```

`or ''`는 읽은 값이 `None`이나 빈 문자열이면 대신 빈 문자열을 사용하게 합니다. 그래서 환경변수가 없어도 `.strip()`을 호출할 수 있습니다.

### if not ... / RuntimeError

`if not supabase_url or not supabase_key:`는 URL과 키 중 하나라도 비어 있는지 확인합니다. `not`은 참과 거짓을 뒤집고, `or`는 둘 중 하나가 참이면 참입니다.

`raise RuntimeError(...)`는 설정 오류를 알리고 앱 시작을 중단합니다. 필요한 설정이 없는데도 서버를 정상적으로 시작한 것처럼 보이지 않게 하려는 목적입니다. 현재는 설정이 빈 문자열이거나 공백뿐이면 이 검사가 처리하지만, 환경변수가 아예 없으면 앞의 `.strip()`에서 실패해 이 검사에 도달하지 못합니다.

## 5. FastAPI 앱 생성

`app = FastAPI(title="Supabase Auth - 회원가입")`는 API 요청을 처리할 앱 객체를 만듭니다. 이후 `app`에 주소와 오류 처리 함수를 등록합니다.

`title`은 자동 생성되는 API 문서 등에 표시할 제목입니다. 이것이 회원가입 주소를 정하는 것은 아닙니다. 주소는 뒤의 `@app.post(...)`에서 지정합니다.

## 6. SignupRequest: 입력값의 설계도

`class SignupRequest(BaseModel):`는 Pydantic의 `BaseModel` 기능을 물려받는 클래스를 정의합니다. 이를 **상속**이라고 합니다. 직접 검증 기능을 전부 만들지 않고 Pydantic 기능을 사용하려는 것입니다.

이 모델은 회원가입 요청에 필요한 필드와 규칙을 선언합니다.

### model_config = ConfigDict(extra='forbid')

모델의 동작 방식을 정하는 설정입니다. `extra='forbid'`는 선언하지 않은 추가 필드를 거부합니다. 예를 들어 `email`, `password` 외에 `role`을 보내면 검증 오류가 됩니다.

### email: EmailStr

`EmailStr`은 이메일 형식을 검증하는 타입입니다. 이메일처럼 보이는 형식인지 검사하지만, 실제 사서함이 존재하거나 요청한 사람이 그 주소의 주인인지를 확인하지는 않습니다. 주소 소유 확인은 이메일 인증 단계의 역할입니다.

### password: SecretStr = Field(...)

`SecretStr`은 비밀번호 같은 값을 일반 출력이나 객체 표현에서 가려주는 타입입니다. 실제 비밀번호를 해시하거나 암호화하는 기능은 아닙니다.

`Field(min_length=8, max_length=128)`는 필드에 추가 검증 조건을 지정합니다. 이 코드에서는 비밀번호를 8~128자로 제한합니다. 숫자나 특수문자가 반드시 있어야 한다는 조건은 여기에는 없습니다. Supabase 서버에 별도 비밀번호 정책이 있다면 그 정책도 통과해야 합니다.

`128`은 개발자가 선택한 상한이며 모든 서비스에 공통인 필수 규칙은 아닙니다. [Pydantic SecretStr 공식 문서](https://docs.pydantic.dev/latest/api/types/#pydantic.types.SecretStr)

### 실제 요청은 어떻게 바뀌나요?

```json
{
  "email": "student@example.com",
  "password": "study1234"
}
```

JSON은 프로그램 사이에서 데이터를 주고받는 텍스트 형식입니다. FastAPI는 위 JSON을 읽어 `SignupRequest`로 검증합니다. 통과하면 함수에서 `body.email`, `body.password`로 접근할 수 있습니다.

검증에 실패하면 `signup()` 본문은 실행되지 않고 요청 검증 오류 처리로 넘어갑니다.

## 7. SignupResponse: 성공 응답의 설계도

`class SignupResponse(BaseModel):` 아래의 `message: str`은 응답에 문자열 메시지가 필요하다는 뜻입니다.

입력 모델과 출력 모델은 쓰는 방향이 다릅니다. `SignupRequest`는 사용자가 보낸 데이터를 검사하고, `SignupResponse`는 서버가 돌려줄 데이터의 구조를 정의합니다.

## 8. 데코레이터(@)란?

함수 위에 붙은 `@...` 문법을 **데코레이터**라고 합니다. 이 코드에서는 FastAPI에 ‘아래 함수를 언제 사용할지’를 등록하는 역할을 합니다.

- `@app.exception_handler(RequestValidationError)`: 요청 검증 오류가 나면 아래 함수를 사용합니다.
- `@app.post('/auth/signup', ...)`: 해당 주소로 POST 요청이 들어오면 아래 함수를 사용합니다.

이 등록은 앱을 읽어 들일 때 일어납니다. 함수 본문은 실제 요청이나 오류가 발생했을 때 실행됩니다.

## 9. handler_validation_error(): 잘못된 입력 처리

이 함수는 FastAPI가 요청 데이터를 검증하다 `RequestValidationError`를 발생시켰을 때 호출됩니다. [FastAPI 오류 처리 공식 문서](https://fastapi.tiangolo.com/tutorial/handling-errors/)

### 함수의 매개변수

`async def handler_validation_error(_request: Request, exc: RequestValidationError):`

- `async def`: 비동기 함수 정의입니다. 비동기 함수는 `await`를 사용해 통신 등의 완료를 기다리는 동안 다른 작업이 진행되게 할 수 있습니다. 이 함수에는 직접 `await`하는 작업은 없습니다.
- `_request`: 현재 HTTP 요청 객체입니다. 앞의 `_`는 이 함수에서 사용하지 않는 매개변수라는 관례적 표시입니다.
- `exc`: 발생한 검증 오류 객체입니다. `exception`을 줄여 쓴 이름입니다.

매개변수는 함수가 전달받을 값에 붙이는 이름입니다. 여기서는 FastAPI가 요청과 예외 객체를 전달합니다.

### exc.errors()와 리스트 컴프리헨션

`exc.errors()`는 개별 검증 오류 정보를 담은 리스트를 반환합니다. 원본의 `errors = [...]`는 그 리스트에서 필요한 항목만 골라 새 리스트를 만드는 **리스트 컴프리헨션**입니다.

다음은 원본 표현을 일반 반복문으로 풀어 쓴 설명용 예시입니다.

```python
errors = []
for error in exc.errors():
    errors.append({'loc': error['loc'], 'type': error['type']})
```

`[]`는 리스트이고, `{...}`는 키와 값으로 이루어진 딕셔너리입니다. `append()`는 리스트 끝에 항목을 추가합니다.

- `loc`: 어느 위치의 값이 잘못됐는지 나타냅니다. 예: 요청 본문의 `email`.
- `type`: 어떤 종류의 오류인지 나타냅니다. 예: 필수값 누락, 길이 부족.

원래 오류 정보 전체를 응답하지 않고 이 두 항목만 선택하므로 비밀번호 같은 입력값이 검증 오류 응답에 포함되는 것을 줄일 수 있습니다. 프로그램 전체의 로그나 다른 출력까지 자동으로 보호하는 것은 아닙니다.

### JSONResponse(...)

`JSONResponse(status_code=422, content={'detail': errors})`는 상태 코드와 JSON 본문을 직접 지정하는 응답 객체입니다.

예를 들어 필수 이메일을 빠뜨리면 다음 형태로 응답합니다.

```json
{
  "detail": [
    {"loc": ["body", "email"], "type": "missing"}
  ]
}
```

`422`는 요청 데이터가 API가 요구한 조건을 충족하지 못했다는 의미로 사용합니다.

## 10. signup(): 회원가입 요청 처리

### @app.post('/auth/signup', response_model=SignupResponse)

`POST`는 서버에 데이터를 보내 처리를 요청할 때 사용하는 HTTP 메서드입니다. `/auth/signup`은 서버 안에서의 경로입니다. 예를 들어 서버가 `http://localhost:8000`에서 실행 중이라면 전체 주소는 `http://localhost:8000/auth/signup`입니다.

`response_model=SignupResponse`는 정상 반환 데이터를 해당 모델에 맞게 검증하고 JSON으로 변환하도록 지정합니다.

`def signup(body: SignupRequest):`는 검증된 요청 객체를 `body`라는 이름으로 받습니다. 이 코드는 동기 Supabase/HTTPX 클라이언트를 사용하므로 동기 함수 `def`로 작성되어 있습니다. FastAPI는 일반 `def`로 등록한 경로 함수를 스레드 풀에서 실행합니다.

### try / except

`try` 안에는 오류가 날 수 있는 작업을 적고, `except`에는 지정한 종류의 오류가 났을 때 처리할 내용을 적습니다. 모든 오류를 잡는 것은 아닙니다. 해당 `except`와 일치하지 않는 오류는 그대로 밖으로 전달됩니다.

## 11. HTTPX와 with 구문

### httpx.Client(timeout=10.0)

`httpx.Client`는 HTTP 요청을 보낼 수 있는 클라이언트 객체입니다. 연결을 재사용하는 기능과 공통 설정을 제공합니다. 이 코드에서는 `http_client.get(...)`을 직접 호출하지 않고 Supabase SDK에 전달합니다. SDK가 내부 통신에 사용합니다.

`timeout=10.0`은 연결, 읽기, 쓰기, 연결 풀 대기 등에 적용할 타임아웃을 설정합니다. ‘회원가입 전체가 무조건 10초 안에 끝난다’는 뜻은 아닙니다. [HTTPX 타임아웃 공식 문서](https://www.python-httpx.org/advanced/timeouts/)

### with ... as http_client

`with`는 사용이 끝난 자원을 정리하도록 하는 문법입니다. 여기서는 생성한 클라이언트를 `http_client`라는 이름으로 사용하고, 블록을 빠져나갈 때 연결 자원을 닫습니다. 중간에 예외가 발생해도 정리 작업이 수행됩니다.

요청마다 별도 클라이언트를 만드는 현재 구조에서는 사용자 요청 간 같은 Supabase 클라이언트를 공유하지 않습니다. 연결 재사용 범위도 이 클라이언트가 살아 있는 동안으로 한정됩니다. [HTTPX 클라이언트 공식 문서](https://www.python-httpx.org/advanced/clients/)

## 12. create_client()와 ClientOptions

`create_client(...)`는 Supabase 기능에 접근할 클라이언트 객체를 생성합니다. 실제 회원가입은 뒤의 `sign_up()` 호출에서 요청합니다.

| 인수 | 의미 |
|---|---|
| `supabase_url` | 어느 Supabase 프로젝트에 연결할지 지정 |
| `supabase_key` | 프로젝트 접근에 사용할 API 키 지정 |
| `options` | 클라이언트의 추가 동작 설정 |

`supabase_url=supabase_url`에서 왼쪽은 함수가 받는 매개변수 이름이고, 오른쪽은 앞서 만든 변수의 값입니다. 이름이 같아도 역할은 다릅니다. [Supabase 클라이언트 초기화 공식 문서](https://supabase.com/docs/reference/python/initializing)

`ClientOptions(...)`는 설정을 담는 객체입니다.

| 옵션 | 의도 |
|---|---|
| `persist_session=False` | Auth 클라이언트의 세션 저장 기능 끄기 |
| `auto_refresh_token=False` | 클라이언트의 자동 토큰 갱신 기능 끄기 |
| `httpx_client=http_client` | 앞에서 만든 HTTPX 클라이언트 사용 |

현재 회원가입과 로그인 모두 올바른 옵션명인 `persist_session=False`를 사용합니다. 이전의 `persist_ssession` 오타는 수정되어 있으므로 현재 코드의 오류로 보지 않아도 됩니다.

세션 저장을 끈다고 Supabase 서버의 사용자 계정이나 세션을 삭제하는 것은 아닙니다. 자동 갱신을 끈다고 토큰의 만료 시간이 사라지는 것도 아닙니다. 클라이언트의 저장/갱신 동작에 관한 옵션입니다. [Supabase Auth 개요](https://supabase.com/docs/reference/python/auth-api)

## 13. supabase.auth.sign_up(): 실제 회원가입

`supabase.auth`는 클라이언트 중 인증 기능을 담당하는 객체이고, 그 객체의 `sign_up()` 메서드가 이메일 회원가입을 요청합니다.

이 메서드에는 `email`, `password`를 담은 딕셔너리를 전달합니다.

- `str(body.email)`: 이메일 값을 문자열로 표현합니다.
- `body.password.get_secret_value()`: `SecretStr`에 담긴 실제 비밀번호를 꺼냅니다.

화면에 가려서 표시되는 값 자체를 보내면 올바른 비밀번호가 전달되지 않으므로, API 요청에는 실제 값을 꺼내 사용해야 합니다.

이 코드는 사용자 테이블에 직접 SQL을 실행하지 않습니다. Supabase Auth에 회원가입을 맡깁니다. Supabase의 이메일 확인 설정이 켜져 있으면 확인 메일 절차가 필요하며, 가입 요청 성공과 로그인 완료는 구분해야 합니다. [Supabase sign_up 공식 문서](https://supabase.com/docs/reference/python/auth-signup)

회원가입 함수는 `sign_up()`의 반환값을 변수에 저장하지 않습니다. 따라서 **회원가입 응답에는 JWT가 없습니다.** 뒤의 로그인 함수는 JWT를 응답하므로 두 함수를 구분해야 합니다.

## 14. 회원가입 예외를 HTTP 응답으로 바꾸기

이 절의 `try/except`는 `signup()` 안에만 있습니다. 다른 함수인 `login()`의 오류까지 처리해 주는 것은 아닙니다.

### AuthApiError as err

`except AuthApiError as err:`는 Supabase Auth API 오류를 잡고 그 객체를 `err`라는 이름으로 사용한다는 뜻입니다. `err.status`를 읽어 오류 상태에 따라 응답을 정합니다.

| 조건 | 우리 API의 응답 | 이 코드의 의도 |
|---|---|---|
| Supabase 상태가 `429` | `429` | 요청이 너무 많으므로 잠시 후 재시도 |
| Supabase 상태가 `500` 이상 또는 `401` | `503` | 인증 서비스 상태나 연결 설정 확인 |
| 그 외의 Auth API 오류 | `400` | 입력값이나 Auth 설정 확인 |
| `AuthRetryableError` 또는 `httpx.HTTPError` | `503` | 일시적 인증 오류나 통신 장애 안내 |

여기서 `401`을 `503`으로 바꾸는 것은 **이 프로그램이 선택한 처리 방식**입니다. 모든 API에서 반드시 이렇게 해야 하는 규칙은 아닙니다. 분류는 SDK가 실제로 발생시킨 예외 종류에 따라 적용됩니다.

`except (AuthRetryableError, httpx.HTTPError):`의 괄호는 여러 예외 종류 중 하나에 해당하면 처리한다는 의미입니다. 이름에 `Retryable`이 있어도 이 코드가 자동으로 재시도하는 것은 아닙니다.

### HTTPException과 JSONResponse의 차이

`raise HTTPException(400, '입력과 auth 설정을 확인하세요')`는 함수의 정상 처리를 중단하고 FastAPI가 오류 응답을 만들게 합니다. 보통 본문은 `{"detail": "입력과 auth 설정을 확인하세요"}` 형태입니다.

반면 앞의 `return JSONResponse(...)`는 응답 객체를 직접 만들어 반환합니다. 두 방식 모두 HTTP 응답을 만들지만, 하나는 예외를 발생시키고 다른 하나는 값을 반환한다는 차이가 있습니다.

## 15. 성공 응답 반환

`return SignupResponse(message='...')`는 모델 객체를 만들어 함수 결과로 돌려줍니다. FastAPI는 이를 JSON으로 변환합니다. 이 경로에 별도 성공 상태 코드를 지정하지 않았으므로 기본 `200`을 사용합니다.

```json
{
  "message": "가입 요청 처리 완료! 이메일 확인 설정이 켜져있다면 받은 메일을 확인하세요"
}
```

이 응답은 함수가 예외 없이 가입 요청 처리를 마쳤다는 안내입니다. 응답에 액세스 토큰이 포함되어 있지는 않습니다.

## 16. 앱 시작 시점과 요청 시점 구분하기

이 구분을 이해하면 코드를 훨씬 쉽게 읽을 수 있습니다.

1. **앱을 읽어 들일 때**: 모듈 import → `.env` 로드 → 설정값 읽기와 검사 → 앱 생성 → 모델 정의 → 핸들러와 API 경로 등록.
2. **회원가입 요청이 올 때**: 입력 검증 → `signup()` 호출 → HTTPX/Supabase 클라이언트 생성 → `sign_up()` 통신 → 자원 정리 → 응답 반환.
3. **입력 검증에 실패할 때**: `signup()` 대신 `handler_validation_error()`로 오류 응답 생성.

4. **로그인 요청이 올 때**: 입력 검증 → `login()` 호출 → 클라이언트 생성 → `sign_in_with_password()` 통신 → 자원 정리 → 토큰과 사용자 정보를 응답. 로그인 입력 검증에 실패해도 같은 `handler_validation_error()`가 동작합니다.

현재 환경변수가 없다면 1번에서 실패할 수 있고, 잘못된 로그인 정보에 대한 Supabase 예외는 4번에서 발생합니다. 앱 시작 오류와 요청 처리 중 오류는 발생 시점이 다릅니다.

## 17. 함수와 메서드 빠른 찾아보기

| 이름 | 한 문장 설명 |
|---|---|
| `load_dotenv()` | `.env`의 설정을 환경변수로 읽음 |
| `os.getenv()` | 이름에 해당하는 환경변수 값을 가져옴 |
| `.strip()` / `.rstrip()` | 문자열 양쪽 공백 / 오른쪽의 지정 문자를 제거 |
| `FastAPI()` | API 앱 객체 생성 |
| `ConfigDict()` | Pydantic 모델 설정 구성 |
| `Field()` | 필드 검증 조건과 부가 정보 지정 |
| `app.exception_handler()` | 특정 예외를 처리할 함수 등록 |
| `handler_validation_error()` | 이 파일에서 정의한 요청 검증 오류 처리 함수 |
| `exc.errors()` | 검증 오류 목록 반환 |
| `JSONResponse()` | JSON 본문과 상태 코드를 지정한 응답 생성 |
| `app.post()` | POST 요청을 처리할 경로 함수 등록 |
| `signup()` | 이 파일에서 정의한 회원가입 처리 함수 |
| `httpx.Client()` | HTTP 통신 클라이언트 생성 |
| `ClientOptions()` | Supabase 클라이언트 설정 객체 생성 |
| `create_client()` | Supabase 클라이언트 생성 |
| `str()` | 값을 문자열로 표현 |
| `.get_secret_value()` | SecretStr의 실제 값 반환 |
| `.sign_up()` | Supabase Auth에 회원가입 요청 |
| `HTTPException()` | FastAPI가 처리할 HTTP 오류 객체 생성 |
| `SignupResponse()` | 정의한 모델로 성공 응답 데이터 생성 |
| `.sign_in_with_password()` | 이메일·비밀번호로 Supabase Auth에 로그인 요청 |
| `login()` | 로그인 결과에서 토큰과 사용자 정보를 반환하는 함수 |
| `LoginResponse()` | 로그인 성공 응답 데이터 생성 |

`FastAPI()`, `JSONResponse()` 같은 표현은 정확히는 클래스를 호출해 객체를 생성하는 형태입니다. 초반에는 ‘괄호 안에 설정을 넣어 사용할 객체를 만든다’고 이해해도 충분합니다.

## 18. JWT 학습과 연결하기

**인증(Authentication)**은 사용자가 누구인지 확인하는 것이고, **인가(Authorization)**는 그 사용자에게 특정 작업을 허용할지 판단하는 것입니다.

회원가입은 계정 생성 단계이고 현재 로그인 함수는 세션을 받아 토큰을 사용자에게 전달하는 단계까지 구현합니다. 이후 액세스 토큰을 보호된 API에 전달하고 서버가 검증하는 기능을 추가하게 됩니다. Supabase의 세션은 JWT 형식의 액세스 토큰과 리프레시 토큰으로 표현됩니다. 리프레시 토큰도 JWT라고 생각하면 안 됩니다. [Supabase 세션 공식 문서](https://supabase.com/docs/guides/auth/sessions)

현재 파일에는 요청의 `Authorization` 헤더를 읽거나 JWT를 검증하는 부분이 없습니다. 따라서 이 파일만으로 API 접근 보호가 구현된 것은 아닙니다.

## 19. 이해했는지 확인하기

1. HTTPX는 사용자의 입력값을 검사하는 도구일까요, 다른 서버와 통신하는 도구일까요?
2. 비밀번호가 3글자라면 `sign_up()`까지 실행될까요?
3. `SecretStr`은 비밀번호를 해시할까요?
4. `with` 블록 안에서 오류가 나도 HTTP 클라이언트는 정리될까요?
5. 가입 요청 성공 메시지를 받으면 반드시 JWT도 받은 걸까요?

**답:** ① 통신 도구입니다. ② 요청 검증에서 거부되어 실행되지 않습니다. ③ 출력에서 값을 가려주는 타입이며 해시하지 않습니다. ④ 정리됩니다. ⑤ 이 코드의 응답에는 JWT가 없습니다.

## 20. LoginRequest: 로그인 입력 검증 — 78~81줄

로그인 요청에 필요한 이메일과 비밀번호의 형식을 정의합니다. 회원가입과 마찬가지로 Pydantic의 `BaseModel`을 상속합니다.

| 코드 | 의미 |
|---|---|
| `ConfigDict(extra='forbid')` | 선언하지 않은 추가 필드를 받으면 거부 |
| `email: EmailStr` | 이메일 형식 검사 |
| `password: SecretStr = Field(min_length=1)` | 비밀번호 값을 출력에서 가리고, 최소 1자 요구 |

회원가입은 비밀번호를 새로 정하므로 8~128자로 제한합니다. 로그인은 이미 가입된 계정의 비밀번호를 확인하므로 여기서는 비어 있지 않은지만 검사합니다. **1글자면 로그인된다는 뜻이 아닙니다.** 입력 검증을 통과한 뒤 Supabase에서 실제 비밀번호가 일치하는지 확인합니다.

예를 들어 이메일 형식이 잘못됐거나 비밀번호가 빈 문자열이면 로그인 함수 실행 전에 `422`로 응답합니다. 형식이 올바르지만 비밀번호가 틀렸다면 Supabase 인증 단계에서 실패합니다.

## 21. LoginResponse: 로그인 응답 구조 — 83~91줄

로그인에 성공했을 때 사용자에게 돌려줄 데이터의 설계도입니다.

| 필드 | 타입 | 의미 |
|---|---|---|
| `access_token` | `str` | API 접근 시 신원 확인에 사용하는 JWT 액세스 토큰 |
| `refresh_token` | `str` | 새 액세스 토큰을 발급받을 때 사용하는 갱신 토큰 |
| `token_type` | `str` | 토큰 사용 방식. 보통 `bearer` |
| `expires_in` | `int` | 발급 시점 기준 액세스 토큰의 유효 기간(초) |
| `expires_at` | `int \| None` | 만료 시각. 값이 있으면 Unix 타임스탬프(초) |
| `user_id` | `str` | Supabase가 부여한 사용자 식별자 |
| `email` | `str \| None` | 사용자 이메일 주소 |

`str`은 문자열, `int`는 정수입니다. `int | None`은 ‘정수 또는 값 없음’을 허용한다는 뜻입니다. `str | None`도 같은 방식으로 읽습니다.

이 코드에서는 `expires_at: int | None`처럼 기본값을 지정하지 않았으므로 응답을 만들 때 필드는 제공해야 하며, 그 값으로 `None`을 넣을 수 있다는 의미입니다.

**액세스 토큰과 갱신 토큰의 구분:** 보호된 API 호출에는 액세스 토큰을 사용하고, 액세스 토큰을 새로 얻는 절차에는 갱신 토큰을 사용합니다. 현재 코드는 두 토큰을 반환하지만 갱신용 API는 아직 구현하지 않았습니다. `expires_in`도 읽을 때마다 감소하는 실시간 카운터는 아닙니다.

## 22. 로그인 주소 등록과 Response — 93~94줄

`@app.post('/auth/login', response_model=LoginResponse)`는 이 함수를 로그인 POST 요청에 연결합니다.

- `/auth/login`: 로그인 요청을 받을 경로입니다.
- `response_model=LoginResponse`: 성공 응답을 앞에서 정의한 모델로 검증하고 JSON으로 변환하며, Swagger에도 응답 구조를 표시합니다.

`def login(body: LoginRequest, response: Response):`에는 두 매개변수가 있습니다.

| 매개변수 | 전달하는 주체 | 용도 |
|---|---|---|
| `body` | FastAPI가 요청 JSON을 검증해 전달 | 이메일과 비밀번호 읽기 |
| `response` | FastAPI가 응답 객체를 전달 | 응답 헤더 등의 설정 변경 |

`Response`는 파일 위쪽의 `from fastapi import ... Response`에서 가져옵니다. 사용자가 Swagger 요청 JSON에 `response`라는 항목을 넣는 것이 아닙니다.

`Request`와 `Response`도 구분해야 합니다. `Request`는 서버가 받은 요청을 살펴보는 객체이고, 여기서의 `Response`는 서버가 보낼 응답의 설정을 바꾸는 데 사용하는 객체입니다.

## 23. HTTP 클라이언트와 로그인 요청 — 95~110줄

회원가입 함수와 같은 방식으로 HTTPX와 Supabase 클라이언트를 생성합니다.

1. `httpx.Client(timeout=10.0)`으로 HTTP 통신 설정을 만듭니다.
2. `with ... as http_client`로 사용이 끝나면 연결 자원이 정리되게 합니다.
3. `create_client()`에 프로젝트 URL, 키, 추가 옵션을 전달합니다.
4. `sign_in_with_password()`로 이메일과 비밀번호를 Supabase Auth에 보냅니다.

`persist_session=False`는 클라이언트의 세션 저장 기능을, `auto_refresh_token=False`는 자동 토큰 갱신 기능을 끕니다. 로그인 시 세션을 발급받을 수 없게 만드는 설정은 아닙니다.

### sign_in_with_password()는 무엇인가요?

Supabase Auth가 계정의 이메일과 비밀번호를 확인하도록 요청하는 메서드입니다. 회원가입의 `sign_up()`이 새 계정 생성을 요청한다면, 이 메서드는 기존 계정의 로그인을 요청합니다.

전달하는 딕셔너리의 `email`에는 `str(body.email)`을, `password`에는 `body.password.get_secret_value()`를 넣습니다. 후자는 `SecretStr`에 가려져 있는 실제 비밀번호를 꺼내는 메서드입니다.

이메일 인증이 필요한 설정이라면 가입 후 받은 확인 메일의 인증 절차도 완료해야 합니다. 관리자가 직접 가입 요청을 승인하는 절차와는 다릅니다. [Supabase 로그인 공식 문서](https://supabase.com/docs/reference/python/auth-signinwithpassword)

## 24. 세션과 사용자 정보 — 111~112줄

로그인 응답에서 세션 정보와 사용자 정보를 각각 꺼내 사용합니다.

- **`session`**: 액세스 토큰, 갱신 토큰, 만료 정보처럼 로그인 상태를 이용하는 데 필요한 정보입니다.
- **`user`**: 사용자 ID, 이메일처럼 계정 자체에 관한 정보입니다.

`session.access_token`은 세션의 액세스 토큰 속성을 읽고, `user.id`는 사용자의 ID 속성을 읽는 표현입니다. 속성은 객체 안에 이름을 붙여 보관한 정보라고 이해하면 됩니다.

이 줄들은 `with` 블록 밖에 있습니다. `with`를 벗어나면 HTTP 연결은 정리되지만, 이미 받은 데이터까지 삭제되지는 않으므로 응답을 구성할 수 있습니다. Python의 `with` 자체는 함수처럼 별도의 지역 변수 범위를 만들지 않습니다.

## 25. Cache-Control: no-store — 113줄

`response.headers['Cache-Control'] = 'no-store'`는 HTTP 응답 헤더에 저장 금지 지시를 추가합니다.

**헤더**는 JSON 본문과 별도로 전달되는 부가 정보입니다. `Cache-Control`은 브라우저나 중간 캐시가 응답을 저장하는 방식을 지시하는 헤더이고, `no-store`는 이 응답을 저장하지 말라는 뜻입니다.

로그인 응답에는 인증에 사용할 수 있는 토큰이 포함되므로 이런 설정을 사용합니다. 다만 프런트엔드 코드가 토큰을 변수나 별도 저장소에 직접 보관하는 것까지 이 헤더가 막아주는 것은 아닙니다.

여기서는 `response` 객체 자체를 반환하지 않아도, FastAPI가 설정한 헤더를 최종 응답에 반영합니다. 응답 본문은 다음 줄의 `LoginResponse(...)`로 만듭니다. [FastAPI 응답 헤더 공식 문서](https://fastapi.tiangolo.com/advanced/response-headers/)

## 26. 로그인 응답 만들기 — 114~122줄

`return LoginResponse(...)`는 세션과 사용자 객체에서 꺼낸 값을 응답 모델에 넣고 반환합니다.

예를 들어 `access_token=session.access_token`에서 왼쪽은 **응답 필드 이름**, 오른쪽은 **세션 객체에서 읽은 값**입니다. 두 이름이 같아도 역할은 다릅니다. `user_id=user.id`는 사용자 객체의 `id`를 우리 API의 `user_id`라는 이름으로 전달합니다.

FastAPI가 이 모델을 JSON으로 변환하며, 별도 성공 상태 코드를 지정하지 않았으므로 성공 시 기본 `200`으로 응답합니다.

```json
{
  "access_token": "<액세스 토큰>",
  "refresh_token": "<갱신 토큰>",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": null,
  "user_id": "<사용자 ID>",
  "email": "student@example.com"
}
```

위 값은 구조 이해를 위한 예시입니다. 실제 토큰, 만료 시간과 사용자 정보는 로그인 응답에 따라 달라집니다.

## 27. 회원가입과 로그인의 전체 흐름 비교

| 구분 | 회원가입 | 로그인 |
|---|---|---|
| 주소 | `POST /auth/signup` | `POST /auth/login` |
| 입력 모델 | `SignupRequest` | 처음 정의한 `LoginRequest` |
| 비밀번호 입력 조건 | 8~128자 | 최소 1자 |
| Supabase 메서드 | `sign_up()` | `sign_in_with_password()` |
| 성공 응답 | 안내 메시지 | 토큰·만료 정보·사용자 정보 |
| Supabase/통신 오류 처리 | 함수 안에 `try/except` 있음 | 현재 함수에는 없음 |

```text
회원가입 요청
  → Supabase 계정 생성 요청
  → 이메일 확인이 필요한 설정이면 확인 메일의 링크 클릭
  → 같은 이메일과 비밀번호로 로그인 요청
  → 토큰과 사용자 정보 수신
  → 이후 보호된 API 요청에 액세스 토큰 사용
```

현재 구현은 토큰을 받는 단계까지입니다. 다른 API가 `Authorization: Bearer <access_token>`을 읽고 토큰을 검증하는 기능은 따로 구현해야 합니다.

## 28. 현재 코드의 주의점과 추가 복습

아래는 실제 구현의 한계이며, 이 문서 갱신에서는 코드를 수정하지 않았습니다.

- **환경변수 누락:** URL이나 키가 아예 없으면 `.strip()`에서 먼저 실패할 수 있습니다.
- **로그인 예외 처리 없음:** 잘못된 로그인 정보나 네트워크 오류가 나면, 현재는 직접 안내 응답으로 변환하지 않아 500으로 이어질 수 있습니다. 회원가입의 `try/except`는 로그인에 적용되지 않습니다.
- **세션·사용자 존재 확인 없음:** 두 객체를 바로 사용하므로 `None`인 경우를 다루는 방어 처리는 없습니다.
- **122줄 이후 같은 클래스 이름 재사용:** 현재 파일 아래에는 `LoginRequest`를 토큰 필드들로 다시 정의한 부분이 있습니다. 처음 등록한 로그인 경로의 입력 모델이 이 때문에 즉시 바뀌는 것은 아니지만, 이후 `LoginRequest`라는 이름은 새 클래스를 가리키므로 혼동과 잘못된 참조를 유발할 수 있습니다. 이 문서의 로그인 해설은 78줄의 첫 정의를 기준으로 합니다.

**추가 복습**

1. 로그인 입력 검증이 통과하면 비밀번호도 맞다는 뜻일까요?
2. `persist_session=False`이면 로그인 응답에 토큰이 없을까요?
3. 갱신 토큰을 보호된 API의 액세스 토큰 대신 사용할까요?
4. 로그인 오류도 회원가입 함수의 `except`가 처리할까요?

**답:** ① 아닙니다. 실제 일치 여부는 Supabase가 확인합니다. ② 아닙니다. 클라이언트의 세션 저장 기능을 끄는 설정입니다. ③ 아닙니다. 두 토큰의 용도가 다릅니다. ④ 아닙니다. 함수별 예외 처리는 별개입니다.
