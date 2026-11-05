# Supabase Auth 연결 이메일 회원가입 API
# 2개의 계정으로 가입 - 로그인 - 메모 접근 - 갱신 - 로그아웃

# os는 환경변수 조회, python-dotenv는 .env 파일 로딩을 담당합니다.
import os
from dotenv import load_dotenv
# FastAPI는 API를 구성하고 Request/Response는 요청 정보와 응답 설정에 사용합니다.
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
# Pydantic은 입력·응답 구조와 이메일 형식, 비밀번호 길이 등의 검증 규칙을 정의합니다.
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr
# Supabase SDK는 인증 요청을 수행하며 Auth 예외는 인증 서비스 오류 처리에 사용합니다.
from supabase.client import ClientOptions, create_client, AuthApiError, AuthRetryableError
# HTTPX는 Supabase와의 HTTP 통신에 사용할 연결과 타임아웃을 관리합니다.
import httpx


# .env를 자동 탐색합니다. override=True는 .env 값으로 기존 환경변수를 덮어씁니다.
load_dotenv(override=True)


# getenv는 환경변수를 읽고 strip은 양쪽 공백, rstrip('/')는 끝의 슬래시를 제거합니다.
# 현재 변수가 아예 없으면 None.strip()에서 실패해 아래 누락 검사에 도달하지 못합니다.
supabase_url = os.getenv('SUPABASE_URL').strip().rstrip('/')
# publishable 키는 프로젝트 접근용이며 로그인 사용자의 JWT가 아닙니다. 실제 값은 출력하지 않습니다.
supabase_key = os.getenv('SUPABASE_PUBLISHABLE_KEY').strip()
# 공백 제거 후 설정이 비어 있으면 RuntimeError로 앱 시작을 중단합니다.
if not supabase_url or not supabase_key:
    raise RuntimeError('SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY missing')

# title은 Swagger의 제목입니다. 현재 회원가입과 로그인 경로를 등록합니다.
app = FastAPI(title="Supabase Auth - 회원가입")

# BaseModel을 상속해 요청 필드를 검증합니다. extra='forbid'는 추가 필드를 거부합니다.
class SignupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email : EmailStr  # 이메일 형식을 검사하며 실제 주소의 소유 여부는 확인하지 않습니다.
    # SecretStr은 출력에서 값을 가리며 암호화하지 않습니다. Field는 길이 조건을 지정합니다.
    password : SecretStr = Field(min_length = 8, max_length = 128) # 8~128자이며 상한은 개발자가 정한 정책입니다.

# 회원가입 성공 응답은 안내 메시지만 포함하며 토큰을 전달하지 않습니다.
class SignupResponse(BaseModel):
    message : str

# 입력 검증 실패 시 실행할 함수를 등록합니다. 회원가입·로그인 입력 오류에 공통 적용됩니다.
@app.exception_handler(RequestValidationError)
async def handler_validation_error(_request:Request, exc:RequestValidationError):
    # _request는 사용하지 않는 요청 객체입니다. exc.errors()는 검증 오류 목록을 반환합니다.
    # 위치(loc)와 종류(type)만 선택해 원본 입력값이 422 응답에 노출되지 않게 합니다.
    errors = [
        {'loc':error['loc'], 'type': error['type']}
        for error in exc.errors()
    ]
    # JSONResponse로 상태 코드와 JSON 본문을 지정합니다. 422는 요청 입력 검증 실패입니다.
    return JSONResponse(status_code = 422, content = {'detail':errors})

# 경로와 성공 응답 모델을 등록합니다. 실제 POST 요청 시 함수 본문이 실행됩니다.
@app.post('/auth/signup', response_model = SignupResponse)
# body는 요청 JSON을 검증한 객체입니다. 동기 경로 함수는 FastAPI의 스레드 풀에서 실행됩니다.
def signup(body:SignupRequest):
    # 인증·통신 예외를 아래 except에서 HTTP 오류로 변환합니다. 로그인 오류까지 잡지는 않습니다.
    try:
        # timeout은 통신 단계별 10초 설정이며, with 종료 시 연결 자원을 닫습니다.
        with httpx.Client(timeout = 10.0) as http_client:
            # 요청별 Supabase 클라이언트를 생성합니다. 사용자별 전역 세션을 공유하지 않습니다.
            supabase = create_client(
                supabase_url = supabase_url,
                supabase_key = supabase_key,
                options = ClientOptions(
                    persist_session = False,  # SDK의 세션 저장 기능을 끕니다. 기본 True입니다.
                    auto_refresh_token=False,  # 자동 토큰 갱신을 끕니다. 기본 True입니다.
                    httpx_client = http_client  # 위에서 만든 HTTPX 클라이언트를 통신에 사용합니다.
                )
            )
            # Auth에 계정 생성을 요청합니다. 직접 DB에 INSERT하지 않으며 반환값은 사용하지 않습니다.
            supabase.auth.sign_up(
                {
                    'email':str(body.email),
                    'password':body.password.get_secret_value()  # 전송할 실제 비밀번호를 꺼냅니다.
                }
            )
    # Supabase Auth가 반환한 API 오류를 클라이언트용 HTTP 오류로 변환합니다.
    except AuthApiError as err:
        # 429는 요청 횟수 제한에 걸린 경우입니다.
        if err.status == 429:
            raise HTTPException(429, '요청이 많습니다. 잠시 후 다시 시도하세요')
        # 5xx와 401은 서비스·설정 문제로 간주해 503으로 변환하는 이 코드의 정책입니다.
        if err.status >= 500 or err.status == 401:
            raise HTTPException(503, '인증 서비스 상태 또는 연결 설정 확인')
        # 나머지는 400으로 전달합니다. HTTPException의 인자는 상태 코드와 detail 문구입니다.
        raise HTTPException(400, '입력과 auth 설정을 확인하세요')
    except (AuthRetryableError, httpx.HTTPError):
        # 일시적인 인증 오류나 연결 실패·타임아웃 등을 처리합니다. 자동 재시도하지는 않습니다.
        raise HTTPException(503, '인증 서비스 연결 불가. 잠시 후 다시 시도하세요')
    # 예외 없이 끝나면 기본 200으로 안내 메시지를 반환합니다.
    # 이메일 확인이 필요한 설정에서는 받은 메일의 링크로 주소 소유 확인을 완료해야 합니다.
    return SignupResponse(message = '가입 요청 처리 완료! 이메일 확인 설정이 켜져있다면 받은 메일을 확인하세요')

# 로그인 요청도 추가 필드를 거부합니다. 실제 이메일·비밀번호 일치 여부는 Supabase가 확인합니다.
class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email : EmailStr
    password : SecretStr=Field(min_length=1)  # 기존 비밀번호를 확인하므로 빈 문자열만 거부합니다.

# 로그인 성공 응답 모델입니다. 토큰과 함께 숫자형 만료 정보 및 사용자 정보를 반환합니다.
class LoginResponse(BaseModel):
    # 토큰은 호출자가 사용할 수 있게 str로 반환합니다. SecretStr이면 JSON에서도 가려집니다.
    access_token : str  # 보호된 API 호출 시 전달할 JWT 액세스 토큰입니다.
    refresh_token : str  # 새 액세스 토큰 발급에 쓰는 별도 토큰이며 액세스 JWT와 다릅니다.
    token_type : str  # 보통 bearer이며 Authorization 헤더에서 사용할 방식을 나타냅니다.
    expires_in : int  # 발급 시 기준 유효 기간(초)입니다. 실시간으로 감소하는 값은 아닙니다.
    expires_at : int | None  # 만료 시각(Unix timestamp, 초)이며 None도 허용합니다.
    user_id : str  # Supabase가 부여한 사용자 식별자입니다.
    email : str | None  # 이메일 문자열 또는 None을 허용합니다.

# 로그인 경로를 등록하고 성공 응답 JSON을 검증하며 Swagger에 구조를 표시합니다.
@app.post('/auth/login', response_model = LoginResponse)
# Response는 FastAPI가 전달합니다. 요청 JSON 필드가 아니라 응답 헤더 설정용 객체입니다.
def login(body : LoginRequest, response : Response):
    # 현재 로그인에는 try/except가 없어 인증·통신 예외가 처리되지 않은 오류로 전달됩니다.
    # with를 벗어나면 HTTP 연결 자원이 정리됩니다.
    with httpx.Client(timeout = 10.0) as http_client:
            supabase = create_client(
                supabase_url = supabase_url,
                supabase_key = supabase_key,
                options = ClientOptions(
                    persist_session = False,
                    auto_refresh_token=False,
                    httpx_client = http_client
                )
            )
            # 회원가입과 같은 프로젝트에 연결해 이메일·비밀번호로 로그인을 요청합니다.
            result = supabase.auth.sign_in_with_password(
                {
                    'email':str(body.email),
                    'password':body.password.get_secret_value()
                }
            )
    # session은 토큰·만료 정보, user는 계정 정보를 담습니다. 현재 None 여부 검사는 없습니다.
    # HTTP 연결이 닫혀도 이미 받은 응답 데이터는 사용할 수 있습니다.
    session = result.session
    user = result.user
    # 인증 토큰이 담긴 응답을 브라우저나 중간 캐시에 저장하지 않도록 지시합니다.
    response.headers['Cache-Control'] = 'no-store'
    # 필요한 필드만 모델로 반환합니다. FastAPI가 JSON으로 변환하고 기본 200으로 응답합니다.
    return LoginResponse(
        access_token = session.access_token,
        refresh_token = session.refresh_token,
        token_type = session.token_type,
        expires_in = session.expires_in,
        expires_at = session.expires_at,
        user_id = user.id,
        email = user.email
    )

# Bearer JWT로 현재 사용자 확인은 후속 학습 내용입니다. 이 파일에는 검증 경로가 없습니다.
