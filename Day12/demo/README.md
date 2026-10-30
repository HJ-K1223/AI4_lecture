# 소담상점 — FastAPI 쇼핑몰

현재 **단계 4: 인증·상품 조회·장바구니·주문·모의 결제**까지 구현했습니다. 상품 목록은 실제 Supabase의 shoppingmall.products를 조회합니다. 회원 수정·탈퇴·구매내역은 다음 단계입니다.

가정: 화면의 임시 상점 이름은 `소담상점`이며 APP_NAME으로 변경할 수 있습니다.

## 현재 환경에서 실행

프로젝트 폴더 `C:\AI4\Day12\demo`를 VS Code로 열고 PowerShell 터미널에서 실행합니다. 프로젝트의 `.venv`는 Python 3.12로 생성하고 의존성을 설치해 두었습니다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8012
```

브라우저에서 [상품 화면](http://127.0.0.1:8012/products)을 엽니다. 종료는 서버 터미널에서 Ctrl+C입니다.

이 환경에서는 8000 포트 바인딩이 WinError 10013으로 거부되어 8012 포트를 사용합니다. 현재 .env의 APP_BASE_URL도 8012입니다. 다른 포트로 실행한다면 APP_BASE_URL을 반드시 같은 주소로 맞추세요. CSRF 검증에 사용합니다. 기본 8000 포트를 사용할 수 있는 환경에서는 APP_BASE_URL을 http://127.0.0.1:8000으로 설정하고 가상환경 활성화 후 표준 명령을 사용합니다.

```powershell
uvicorn app.main:app --reload
```

VS Code는 `.vscode/settings.json`에 지정한 프로젝트 인터프리터를 선택합니다. 처음 열 때 Python 확장 기능이 설치되어 있어야 하며, 필요하면 명령 팔레트에서 **Python: Select Interpreter**로 `.venv\Scripts\python.exe`를 선택합니다.

## 새 환경에서 설치

Python 3.11 이상을 설치한 환경에서 프로젝트 폴더를 열고 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

설치 후 .env.example을 .env로 복사하고 아래 로컬 설정 도구로 세션 비밀값을 생성합니다. 기존 .env는 덮어쓰지 않습니다.

```powershell
.\.venv\Scripts\python.exe -m app.core.setup_local
```

도구는 누락된 설정만 보완하며 DB 정보를 변경하지 않습니다. .env.example을 복사한 경우 APP_BASE_URL을 실행할 포트로 맞추고, 로컬 HTTP에서는 COOKIE_SECURE=false를 명시적으로 설정하세요. 운영은 반드시 Secure 쿠키를 사용합니다. SESSION_SECRET은 모든 환경에서 필수이며 생성값은 .env에만 저장합니다.

로그인·회원가입 폼은 DB 연결정보 없이 볼 수 있지만 실제 상품 조회·가입·로그인·구매에는 DB가 필요합니다. DB 미설정 상품 화면은 안내와 함께 503을 반환합니다. Node.js·npm·번들러·CSS 프레임워크는 사용하지 않습니다.

## 환경변수와 Supabase 연결

1. `.env`가 없다면 `.env.example`을 복사해 만듭니다. 기존 `.env`는 덮어쓰지 마세요.
2. `.env`에 Supabase **Connect**에서 받은 정보를 입력합니다. DATABASE_URL 또는 분리된 `host`, `port`, `dbname`, `user`, `password`를 지원합니다. `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`도 지원합니다. URL은 `postgresql+psycopg://` 형식을 권장하며 비밀번호의 예약문자는 URL 인코딩합니다. 분리 설정의 비밀번호는 원문을 사용하며 코드가 인코딩합니다. 둘 다 있으면 DATABASE_URL이 우선합니다. 연결정보를 채팅·Git·프론트 코드에 넣지 않습니다.
3. APP_BASE_URL을 실제 실행 주소로 맞춥니다. 8012 포트 사용 시 `http://127.0.0.1:8012`입니다.
4. [스키마 이전 안내](docs/schema-migration.md)에 따라 `shoppingmall` 스키마가 준비되어 있는지 확인합니다. 서버는 스키마를 자동 생성·삭제하지 않습니다.
5. 아래 읽기 전용 검증 명령을 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m app.core.check_db
```

성공 시 `shoppingmall`의 5개 테이블에 연결하고 읽을 수 있다는 메시지가 표시됩니다. 실패 시 URL·TLS·테이블·역할 권한을 확인하세요. 원래 예외나 연결 URL은 출력하지 않습니다. 이 검사는 INSERT·결제·행 잠금의 성공까지 검증하지는 않습니다.

Supabase 직접 연결이 네트워크에서 지원되지 않으면 프로젝트 Connect에 표시된 세션 풀러 연결 주소를 사용합니다. [Supabase 연결 공식 안내](https://supabase.com/docs/guides/database/connecting-to-postgres)

서버는 TLS 연결을 사용하고 `sslmode=disable`을 거부합니다. 기본 `require`는 암호화를 요구하는 설정이며 인증서 검증을 강화하려면 올바른 CA 설정과 함께 `verify-full`을 사용합니다. URL의 데이터베이스 이름은 기존 `postgres` 등 실제 DB 이름을 유지하고, `shoppingmall`로 바꾸지 않습니다.

## 샘플 상품

현재 Supabase에 샘플 상품 12개를 등록했습니다. 새 DB에서 실행하려면 스키마를 준비한 후 다음 명령을 사용합니다.

```powershell
.\.venv\Scripts\python.exe -m app.core.seed_db
```

또는 SQL Editor에서 [db/seed.sql](db/seed.sql)을 실행합니다. 같은 SKU는 건너뛰므로 기존 상품의 가격·재고를 초기화하지 않습니다. 로컬 SVG 상품 이미지도 함께 제공합니다.

## 운영 설정

운영에서는 APP_ENV=production, HTTPS인 APP_BASE_URL, 실제 호스트의 ALLOWED_HOSTS, DB 연결정보(URL 또는 분리 설정), 32자 이상의 임의 SESSION_SECRET, COOKIE_SECURE=true가 필요합니다. 누락되거나 안전하지 않은 설정은 시작 시 거부합니다. 인증 쿠키는 HttpOnly·Secure·SameSite=Lax이며 만료는 발급 후 2시간입니다. SESSION_SECRET은 재시작·여러 워커에서도 같은 환경변수를 사용합니다. alwaysdata의 구체적인 실행·프록시 설정은 단계 6에서 작성합니다.

## 검증

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

자동 테스트 **35개**가 통과했습니다. 기본 설정·인증에 더해 공개 목록·페이지네이션·장바구니·가격 변경 재확인·주문 스냅샷·소유권·중복 결제·품절·전체 롤백을 검증합니다. 기본 테스트는 메모리 DB를 사용합니다. [최초 DB 연결 결과](docs/db-connection.md)도 참고하세요.

실제 Supabase 인증 검증을 다시 실행하려면 다음 명령을 사용합니다. 원격 DB에 일시적으로 회원을 생성하지만 외부 트랜잭션을 커밋하지 않고 롤백합니다.

```powershell
.\.venv\Scripts\python.exe -m tests.check_auth_db
```

구매·PostgreSQL 동시성 검증은 다음 명령으로 실행합니다. 구매 테스트는 롤백하고, 동시성 검증은 별도로 만든 회원·상품·주문만 잠시 커밋하여 두 연결에서 사용한 뒤 정확한 UUID로 정리합니다. 기존 업무 데이터는 대상으로 삼지 않습니다.

```powershell
.\.venv\Scripts\python.exe -m tests.check_shop_db
```

실제 Supabase에서 마지막 재고 경쟁, 같은 키·다른 키의 같은 주문 동시 결제에도 성공·차감이 한 번만 발생함을 확인했습니다.

## 인증 수동 확인

1. [회원가입](http://127.0.0.1:8012/register)에서 이메일·이름·12~128자 비밀번호를 입력합니다. 가입 후 로그인 화면으로 이동합니다.
2. [복귀 경로가 있는 로그인](http://127.0.0.1:8012/login?next=%2Fproducts%3Fquantity%3D2)에서 로그인하면 `/products?quantity=2`로 즉시 이동하고 메뉴에 로그아웃이 나타납니다.
3. 로그아웃 버튼을 누르면 상품 목록으로 돌아가며 로그인 메뉴가 나타납니다. GET `/logout`은 허용하지 않습니다.
4. `/login?next=https://example.com` 또는 `/login?next=//example.com`으로 접속하고 로그인해도 내부 `/products`로 이동해야 합니다.

가입은 실제 Supabase에 계정을 생성합니다. 테스트 계정이 남는 것을 원하지 않으면 기본 자동 테스트나 아래 메모리 DB 브라우저 검증을 사용하세요. 로그아웃은 별도 세션 테이블 없이 기존 쿠키 재사용을 막기 위해 해당 회원의 다른 브라우저 로그인도 무효화합니다.

### API 401 → 로그인 → 원래 화면 복귀

공통 JavaScript의 독립 검증은 아래 메모리 DB 서버를 사용할 수 있습니다. 샘플 상품 12개가 포함되며 가입·구매·재고 변경도 메모리에만 남습니다. Supabase에 접속하지 않습니다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn tests.preview_auth:app --port 8013
```

1. [검증 화면](http://127.0.0.1:8013/auth-test/fetch?quantity=2)에서 **인증 API 호출** 버튼을 누릅니다.
2. `/api/auth/me`의 401 응답 후 원래 URL이 담긴 `/login?next=...`로 이동하는지 확인합니다.
3. 회원가입 링크에서 테스트 계정을 만들고 로그인합니다. 가입·로그인 사이에도 next가 유지됩니다.
4. `/auth-test/fetch?quantity=2`로 복귀하는지 확인합니다. 서버를 끄면 이 테스트 회원은 사라집니다.

검증용 `/auth-test/fetch`는 tests.preview_auth에만 존재합니다. 실제 앱에는 테스트 경로를 추가하지 않았습니다.

## 비회원 → 결제 선택 → 로그인 → 이전 화면 복귀 수동 테스트

실제 앱은 8012, 위 메모리 DB 서버는 8013입니다. 연습용 구매에는 8013을 사용할 수 있습니다. 실제 앱에서 구매하면 Supabase에 주문·결제 기록이 남고 재고가 차감됩니다. 모든 결제는 모의 결제이며 실제 청구는 없습니다.

1. 로그아웃 상태에서 `/products`를 열고 상품 상세로 이동합니다. 목록·상세는 로그인 없이 표시되어야 합니다.
2. 수량을 2개로 선택하고 **결제 선택**을 누릅니다.
3. `/login?next=...`로 이동하며 next에 `/checkout?product_id=...&quantity=2`가 포함되는지 확인합니다.
4. 계정이 없으면 회원가입 링크로 이동해 가입합니다. 로그인 화면으로 돌아온 뒤에도 next가 유지되어야 합니다.
5. 로그인하면 같은 상품·수량 2개의 **선택 상품 확인** 화면으로 즉시 돌아와야 합니다. 자동으로 장바구니에 담거나 결제하지 않아야 합니다.
6. **장바구니에 담고 계속**을 눌러 장바구니에서 상품·수량·합계를 확인합니다. 수량 변경·삭제 후 다시 담기도 확인합니다.
7. 받는 분·연락처·배송주소를 입력하고 **주문 생성 · 결제 확인**을 누릅니다. 최종 주문 상품·합계·배송정보가 표시되어야 합니다.
8. **결제하기**를 누르면 모의 결제 완료 메시지와 함께 `/products`로 이동해야 합니다. 결제한 수량만큼 재고가 줄어야 합니다.
9. 이전 결제 확인 URL을 다시 열면 이미 결제 완료 상태가 표시되고 추가 결제 버튼이 없어야 합니다.

로그인 상태에서도 1~2와 5~9를 반복합니다. 세션이 유효하면 로그인 화면을 거치지 않아야 합니다. 장바구니의 배송정보 변경은 회원 기본정보를 수정하지 않습니다.

### 열린 장바구니에서 세션 종료 후 API 복귀

1. 로그인 후 상품을 담고 A 탭에 `/cart`를 열어 둡니다.
2. 같은 브라우저의 B 탭에서 `/products`를 열고 로그아웃합니다.
3. A 탭에서 수량 변경을 누릅니다. 변경 API의 401 응답을 공통 JS가 처리해 `/login?next=%2Fcart`로 이동해야 합니다.
4. 로그인하면 `/cart`로 복귀합니다. 실패했던 수량 변경은 자동 재실행하지 않으며 사용자가 다시 확인하고 실행합니다.

[단계 2 결과](docs/stage2.md), [단계 3 결과](docs/stage3.md), [단계 4 결과](docs/stage4.md)에 변경 파일·화면 캡처·검증 범위를 정리했습니다.

## 문서

- [설계와 단계 안내](docs/plan.md)
- [ERD](docs/erd.md) / [Mermaid 원문](docs/erd.mmd)
- [테이블 정의](docs/table-definition.md)
- [구매 흐름 그래프](docs/purchase-simulation.md) / [Mermaid 원문](docs/purchase-simulation.mmd)
- [구현된 구매 흐름 Mermaid](docs/purchase-flow.mmd)
- [스키마 이전](docs/schema-migration.md)
