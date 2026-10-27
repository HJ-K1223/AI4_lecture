# note-demo

이메일 회원과 게시판을 제공하는 Django 애플리케이션입니다. alwaysdata Free의 Python WSGI 사이트와 관리형 PostgreSQL에 배포하도록 구성했습니다.

문서 확인일: **2026-10-27 (Asia/Seoul)**. 실행·배포 안내는 아래 공식 자료를 확인해 작성했으며, **실제 alwaysdata 계정 배포와 자원 측정은 아직 수행하지 않았습니다.**

## 구현 기능

- 이메일 회원가입, 비밀번호 해시, 로그인·POST 로그아웃, DB 세션.
- 비밀번호 찾기 Mock: 이메일 발송·토큰·비밀번호 변경 없음.
- 제목만 표시하는 게시글 목록, 기본 10개 페이징, 상세·작성·본인 수정/삭제.
- 댓글 작성·조회·본인 삭제, 20개 페이징. 게시글 삭제 시 댓글 연쇄 삭제.
- 제목·본문·댓글 조회 시 금칙어 마스킹. 관리자 추가/삭제가 다음 조회에 반영됨.
- ADMIN 전용 금칙어 화면, 정규화 중복 방지, 최대 500개 제한.
- 서버 권한 검증, CSRF, 출력 이스케이프, 원문 편집 응답 캐시 방지.

처음 접속하면 로그인 화면이 나오며, 로그인 폼 아래에서 회원가입으로 이동할 수 있습니다. 게시글 목록·상세·댓글 조회는 로그인한 회원만 가능합니다. 로그인 후 게시판으로, 로그아웃 후 로그인 화면으로 이동합니다. 관리자는 타인 글을 수정·삭제할 수 없습니다. SNS 로그인, 실제 비밀번호 복구, 댓글 수정·대댓글, 업로드는 포함하지 않습니다.

## 실행 버전과 구조

실제 테스트: Python **3.13.9**, Django **5.2.18**, PostgreSQL **17.11**, WhiteNoise **6.12.0** (Windows x64). 모든 Python 파일은 이 프로젝트 아래에 있습니다. 의존성은 `requirements.txt`에 고정했습니다.

2026-10-27 공식 지원표에서 Django 5.2 LTS는 2028년 4월까지 연장 지원 대상이며 해당 계열의 최신 패치는 5.2.18입니다. 이 프로젝트는 최신 메이저 대신 지원 중인 LTS를 선택했습니다. 이후에는 보안 패치를 확인해 고정 버전을 갱신하고 재검증하세요. [Django 지원표](https://www.djangoproject.com/download/), [5.2.18 릴리스 노트](https://docs.djangoproject.com/en/5.2/releases/5.2.18/)

```text
config/settings/       공통·로컬·운영 설정
config/wsgi.py         alwaysdata WSGI 진입점
accounts/             커스텀 회원·인증·create_admin 명령
board/                게시글·댓글·43개 자동 테스트
moderation/           규칙·Unicode 마스킹·seed 로더
templates/, static/   서버 렌더링 화면·CSS
seeds/                명시적으로 로드하는 초기 규칙
tools/smoke_wsgi.py   읽기 전용 운영 WSGI 점검
docs/                 출처·배포·검증 기록
```

도메인 ERD는 [설계 문서](ai_agent_design_prompt.md)에 있습니다. 실제 회원 모델에는 인증 지원용 `is_active`·`last_login`이 추가됩니다. 비밀번호 필드의 DB 컬럼은 `password_hash`, 금칙어 등록자 FK의 실제 DB 컬럼은 Django 관례에 따라 `created_by_id`입니다. DB 세션 및 프레임워크 지원 테이블도 생성됩니다. FK의 실제 CASCADE/SET NULL/RESTRICT는 별도 마이그레이션으로 구성했습니다.

## 로컬 실행 — Windows CMD (명령 프롬프트)

### 1. Python과 PostgreSQL 준비

Python 3.13 계열의 지원 중인 패치 버전과 PostgreSQL 17을 설치하세요. 이미 있다면 아래 버전을 확인합니다. [Python 공식 다운로드](https://www.python.org/downloads/), [PostgreSQL Windows 다운로드](https://www.postgresql.org/download/windows/)

```cmd
py -3.13 --version
psql --version
cd /d C:\AI4\Day10\demo
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

위 명령은 Windows CMD에서 실행합니다. `cd /d`는 드라이브까지 함께 이동합니다. 가상환경을 활성화하지 않고 위처럼 Python의 경로를 직접 사용해도 됩니다. 활성화를 원하면 `.venv\Scripts\activate.bat`를 실행하고 이후 `python` 명령을 사용하세요. `psql`이 PATH에 없으면 설치 폴더의 `bin\psql.exe` 경로를 큰따옴표로 감싸 실행하세요. 기존 `.env`가 있다면 복사로 덮어쓰지 말고 필요한 값만 수정하세요.

### 2. 로컬 DB 생성

`psql`을 인식하지 못하면 PostgreSQL 실행 파일 폴더가 PATH에 없거나 PostgreSQL이 설치되지 않은 상태입니다. 일반 설치 경로가 있다면 CMD에서 `"C:\Program Files\PostgreSQL\17\bin\psql.exe" --version`처럼 실행하세요. 버전 폴더는 실제 설치값으로 바꿉니다. 현재 CMD에서만 PATH를 추가하려면 `set "PATH=C:\Program Files\PostgreSQL\17\bin;%PATH%"`를 사용합니다.

이 프로젝트에는 이전 검증에 사용한 `.runtime\postgres\pgsql\bin\psql.exe`도 있습니다. 일반 설치본과 별개이며, 검증용 서버는 작업 종료 시 중지했습니다. 아래는 해당 임시 DB에 접속하는 **선택적인 CMD 절차**입니다.

```cmd
cd /d C:\AI4\Day10\demo
.runtime\postgres\pgsql\bin\pg_ctl.exe -D .runtime\pgdata -l .runtime\postgres.log -o "-h 127.0.0.1 -p 55432" -w start
.runtime\postgres\pgsql\bin\psql.exe -h 127.0.0.1 -p 55432 -U note_test -d note_demo
```

임시 DB는 로컬 검증 전용입니다. 일반 설치본의 `postgres` 사용자·5432 포트와 다르게 `note_test` 사용자·55432 포트를 사용합니다. 이 DB로 앱을 실행한다면 `.env`의 `DB_USER=note_test`, `DB_PORT=55432`, `DB_HOST=127.0.0.1`, `DB_NAME=note_demo`를 맞춥니다. 초기 검증 설정은 비밀번호 없는 로컬 trust 인증이므로 운영에 사용하지 않습니다. 종료할 때는 `.runtime\postgres\pgsql\bin\pg_ctl.exe -D .runtime\pgdata -m fast stop`을 실행합니다.

로컬 PostgreSQL 관리자 세션에서 실행합니다. 역할/DB 이름은 예시이며 기존 것이 있다면 재생성하지 않습니다.

```cmd
psql -U postgres -d postgres
```

```sql
CREATE ROLE note_demo LOGIN;
\password note_demo
CREATE DATABASE note_demo OWNER note_demo ENCODING 'UTF8';
\q
```

`\password`는 비밀번호를 숨김 입력받습니다. `.env`에서 DB 비밀번호를 동일하게 설정합니다. 비밀번호를 명령행 인수에 넣지 마세요.

### 3. 환경변수 설정

CMD에서 `notepad .env`로 파일을 열어 편집합니다. `DJANGO_SECRET_KEY`에는 직접 생성한 무작위 값을 넣습니다.

```cmd
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY='직접_생성한_무작위_값'
DB_NAME=note_demo
DB_USER=note_demo
DB_PASSWORD='앞에서_설정한_DB_비밀번호'
DB_HOST=127.0.0.1
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
TRUST_PROXY_HTTPS=false
```

특수문자나 `#`가 있는 비밀 값은 따옴표로 감쌉니다. 셸에 이미 설정한 환경변수가 `.env`보다 우선합니다. 로컬과 운영 비밀키/DB는 분리하세요. `.env`는 Git 제외 대상입니다.

### 4. DB 적용·관리자·seed·실행

```cmd
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_admin --email admin@example.com --nickname 관리자
.\.venv\Scripts\python.exe manage.py load_banned_terms seeds/banned_terms.json
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```

[로컬 홈페이지](http://127.0.0.1:8000/)에 접속합니다. 비로그인 상태에서는 로그인 화면이 먼저 나오고, 폼 아래의 회원가입 링크로 신규 가입할 수 있습니다. 관리자는 숨김 입력한 비밀번호로 로그인하며, 금칙어 화면은 `/moderation/terms/`입니다. 일반 회원은 회원가입 화면에서 생성합니다. 기존 계정을 관리자 생성 명령으로 자동 승격하지 않습니다.

seed는 공개 사전 항목을 확인해 독립 선정한 **데모 키워드 2개**이며 완성된 운영용 금칙어 목록이 아닙니다. [출처와 이용 조건·한계](docs/seed_sources.md)를 확인하세요. 이 명령은 명시적으로 실행할 때만 동작하며, 삭제한 규칙도 재실행하면 다시 등록될 수 있습니다.

## 자동 테스트

### 로그인 화면 변경 후 기존 환경에서 할 일

이번 변경으로 `.env`, DB 사용자/포트, 기존 데이터, 패키지를 바꿀 필요는 없으며 추가 마이그레이션도 없습니다. 실행 중인 개발 서버의 CMD 창에서 **Ctrl+C**를 눌러 종료합니다. 현재처럼 프로젝트의 임시 PostgreSQL(55432)을 사용하는 경우에는 **DB 서버를 먼저 시작**해야 합니다. `(.venv)` 상태에서 아래 순서로 실행하세요.

```cmd
cd /d C:\AI4\Day10\demo
.runtime\postgres\pgsql\bin\pg_ctl.exe -D .runtime\pgdata status
.runtime\postgres\pgsql\bin\pg_ctl.exe -D .runtime\pgdata -l .runtime\postgres.log -o "-h 127.0.0.1 -p 55432" -w start
python manage.py collectstatic --noinput
python manage.py runserver
```

`status`가 서버 실행 중이라고 표시하면 바로 다음 `start` 명령은 건너뜁니다. 일반 설치본 PostgreSQL 서비스를 사용하는 경우에도 위 임시 DB 명령 대신 해당 서비스의 실행 상태를 확인합니다. `psql`은 DB에 접속하는 도구이므로 `psql`을 여는 것만으로 꺼진 DB 서버가 시작되지는 않습니다.

그다음 `http://127.0.0.1:8000/`에서 **Ctrl+F5**로 새로고침하세요. 이미 로그인한 세션이라면 게시판으로 이동하므로, 로그아웃하거나 시크릿 창에서 첫 로그인 화면을 확인합니다. 새로 가입하거나 DB를 초기화할 필요는 없습니다.

### 테스트 실행 절차

테스트는 PostgreSQL의 별도 `test_note_demo` DB를 생성하고 삭제합니다. **로컬 전용 DB 사용자에만** 테스트 DB 생성 권한을 부여하고, 운영 DB/운영 자격증명으로 실행하지 마세요. 로컬 관리자 세션의 예:

```sql
ALTER ROLE note_demo CREATEDB;
```

```cmd
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

테스트에서는 DEBUG가 꺼지므로 manifest를 생성하는 `collectstatic`이 먼저 필요합니다. 43개 테스트에 가입·인증·권한 우회·페이지 경계·댓글·마스킹·seed·CSRF·XSS·직접 SQL 삭제 관계가 포함됩니다. [실제 검증 결과](docs/verification.md)를 참고하세요.

테스트용 `.runtime/`에는 이 작업에서 준비한 임시 Python/PostgreSQL과 로그가 있습니다. **배포하지 마세요.** 일반 개발 환경은 위 `.venv` 절차로 구성합니다.

## alwaysdata 배포

### 기존 guestbook과 함께 배포하는 경우

현재 `hjk.alwaysdata.net/`은 기존 guestbook에서 사용합니다. 기존 Web 사이트·SSH 사용자·전역 Python 설정을 변경하지 않고 새 WSGI 사이트의 주소를 `hjk.alwaysdata.net/note-demo/`로 별도 등록하는 구성으로 준비합니다. 플랫폼 등록 화면에서 해당 경로가 허용되는지 확인하고, 거부되면 기존 루트 주소로 바꾸지 말고 오류를 확인합니다.

- 새 앱 폴더: `/home/hjk/apps/note-demo`, 새 venv: `/home/hjk/venvs/note-demo`.
- 서버 `.env`에 `APP_URL_PREFIX=/note-demo`를 추가합니다. `ALLOWED_HOSTS=hjk.alwaysdata.net`, `CSRF_TRUSTED_ORIGINS=https://hjk.alwaysdata.net`에는 경로를 붙이지 않습니다.
- 링크·로그인 이동·정적 URL은 `/note-demo/`를 유지합니다. WSGI에서 플랫폼이 경로를 제거해 전달하는 경우와 전체 경로를 전달하는 경우를 모두 처리합니다.
- 새 앱 쿠키는 별도 이름 `note_demo_sessionid`/`note_demo_csrftoken`과 `/note-demo/` 경로로 분리합니다. 같은 호스트 내 경로 분리는 별도 도메인과 같은 보안 격리를 제공하는 것은 아닙니다.
- HSTS는 호스트 전체에 영향을 주므로 이 경로 배포에서는 앱의 HSTS 응답을 끕니다. HTTPS 이동과 Secure 쿠키는 유지하며 `check --deploy`의 `security.W004`는 이 선택에 따른 경고입니다. 기존 사이트의 HTTPS/HSTS 설정은 변경하지 않습니다.
- 업데이트 ZIP에는 실제 `.env`, DB, venv가 없으므로 새 앱 폴더에서만 압축을 풀어 코드만 갱신합니다. `collectstatic` 후 새 WSGI 사이트만 재시작합니다. 관리자/seed 초기화는 반복하지 않습니다.
- 경로 예시를 제외한 아래 일반 배포 설명은 호스트 루트 배포의 기본값입니다. 현재 hjk 계정에서는 이 절의 경로 배포 설정을 우선 적용합니다.

### 1. 계정과 배포 파일

Free 플랜은 공식 문서 기준 디스크 1 GB, RAM 256 MB, CPU 1/4, 백업 3일이며 파일·메일·DB가 용량을 공유합니다. 비영리 용도와 계정의 `alwaysdata.net` 웹 주소 제한을 확인하세요. 실제 계정 한도가 우선합니다. [공식 플랜 조건](https://help.alwaysdata.com/en/docs/admin-billing/billing/public-cloud-prices/)

아래 `<account>`는 **실제 계정명으로 교체**합니다. 그대로 복사 실행하지 마세요. 관리 화면에서 SSH와 Python 3.13을 준비합니다.

전송 대상은 `manage.py`, `requirements.txt`, `config/`, `accounts/`, `board/`, `moderation/`, `templates/`, `static/`, `seeds/`와 필요한 문서입니다. `.runtime/`, 로컬 `.venv/`, `.git/`, `__pycache__/`, 로그·DB 덤프·로컬 `.env`·로컬 `staticfiles/`는 제외합니다. SFTP로 `/home/<account>/apps/note-demo`에 업로드하세요.

### 2. 서버 가상환경

Windows 로컬 작업은 CMD로 진행하고, SSH로 접속한 뒤에는 Linux 서버의 셸을 사용합니다. 다음은 **alwaysdata SSH의 Bash 명령**입니다. 관리 화면 `Environment > Python`에서 선택한 버전과 WSGI 사이트 버전을 일치시킵니다. 공식 안내대로 `python`을 사용합니다. [Python/venv/WSGI 안내](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/)

```bash
cd /home/<account>/apps/note-demo
python --version
python -m venv /home/<account>/venvs/note-demo
source /home/<account>/venvs/note-demo/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
```

플랫폼 관리 uWSGI를 사용하므로 Gunicorn/uWSGI를 별도 설치하거나 `runserver`를 배포 서버로 실행하지 않습니다. 서버 venv는 Linux에서 새로 생성합니다.

### 3. 관리형 PostgreSQL과 운영 환경

관리 화면 `Databases > PostgreSQL`에서 DB/사용자를 생성하고 실제 접속 정보를 기록합니다. 일반 호스트 형식은 `postgresql-<account>.alwaysdata.net`, 포트는 `5432`입니다. `localhost`로 고정하지 않습니다. 테이블 생성과 마이그레이션이 가능한 앱 전용 권한을 부여하세요. [공식 PostgreSQL 연결 안내](https://help.alwaysdata.com/en/docs/web-hosting/databases/postgresql/)

서버 프로젝트 루트에 **운영용 `.env`를 새로 생성**하고 아래 값을 편집합니다. 빈 템플릿은 `.env.production.example`을 참고하세요. `chmod 600 .env`로 보호하고 외부 공개 디렉터리에 두지 않습니다.

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY='운영_전용_50자_이상_무작위_키'
DB_NAME=<관리화면_DB명>
DB_USER=<관리화면_DB사용자>
DB_PASSWORD='실제_DB_비밀번호'
DB_HOST=postgresql-<account>.alwaysdata.net
DB_PORT=5432
ALLOWED_HOSTS=<account>.alwaysdata.net
CSRF_TRUSTED_ORIGINS=https://<account>.alwaysdata.net
TRUST_PROXY_HTTPS=true
```

비밀키는 활성화한 서버 venv에서 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`로 생성할 수 있습니다.

이 프로젝트는 `manage.py`와 공통 설정에서 `.env`를 읽습니다. 같은 파일을 WSGI와 SSH 명령이 함께 사용합니다. 관리 화면의 사이트 환경변수에도 같은 이름을 넣을 경우 **환경변수가 파일보다 우선**하므로 값이 어긋나지 않게 하세요. WSGI 사이트에는 최소 `DJANGO_SETTINGS_MODULE=config.settings.production`을 명시합니다.

`TRUST_PROXY_HTTPS=true`는 alwaysdata의 신뢰하는 프록시 뒤에서만 사용합니다. 해당 플랫폼은 HTTPS 요청도 HTTP로 전달하고 `X-Forwarded-Proto`를 추가하므로 앱은 이를 HTTPS 판정에 사용합니다. 다른 프록시로 옮길 때는 헤더 덮어쓰기/신뢰 경계를 다시 확인하세요. [공식 HTTP 스택](https://help.alwaysdata.com/en/docs/web-hosting/sites/http-stack/)

### 4. 스키마와 정적 파일 준비

```bash
python manage.py migrate --noinput
python manage.py create_admin --email 관리자이메일 --nickname 관리자
python manage.py load_banned_terms seeds/banned_terms.json
python manage.py collectstatic --noinput
python manage.py check --deploy
```

관리자/seed 명령은 초기 배포 시 수동으로 실행합니다. 이후 갱신 때 자동 재실행하지 마세요. 사용자 DB가 있는 재배포는 먼저 백업하고 파괴적인 초기화를 하지 않습니다.

정적 파일은 `staticfiles/`로 수집되며 WhiteNoise 미들웨어가 해시된 CSS를 제공합니다. 추가 Static 사이트나 Nginx가 필요하지 않습니다. [WhiteNoise Django 안내](https://whitenoise.readthedocs.io/en/stable/django.html), [Django 정적 배포 안내](https://docs.djangoproject.com/en/5.2/howto/static-files/deployment/)

운영 점검에서 `security.W005`·`security.W021` 두 경고는 남습니다. 계정 주소의 모든 하위 도메인을 통제한다고 가정하지 않아 HSTS 하위 도메인 일괄 적용과 preload를 끈 의도적 설정입니다. 경고를 숨기지 않으며, 다른 경고가 생기면 배포 전에 해결하세요. [Django 배포 점검](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

### 5. WSGI 사이트 등록과 재시작

`Web > Sites > Add a site`에서 아래처럼 등록합니다. [공식 사이트 등록 안내](https://help.alwaysdata.com/en/docs/web-hosting/sites/add-a-site/)

| 설정 | 값 |
| --- | --- |
| 주소 | <account>.alwaysdata.net |
| 유형 | Python WSGI |
| Application path | /home/<account>/apps/note-demo/config/wsgi.py |
| Working directory | /home/<account>/apps/note-demo |
| Virtualenv | /home/<account>/venvs/note-demo |
| Python | CLI/venv와 동일한 3.13 |
| 환경변수 | DJANGO_SETTINGS_MODULE=config.settings.production |

인증서 상태를 확인하고 관리 화면에서 사이트를 재시작합니다. HTTPS URL에서 첫 진입 로그인 화면→하단 회원가입→가입 완료 후 로그인→게시판·글·댓글→관리자 금칙어→로그아웃 후 로그인 화면 순서로 확인합니다. CSS 응답, 비로그인 수정 차단, 재시작 후 데이터 유지, HTTPS 리다이렉트 루프가 없는지도 확인하세요.

플랫폼 오류 로그는 `/home/<account>/admin/logs/uwsgi/<site-id>.log`입니다. 사이트 ID와 관리 화면 Logs를 기준으로 확인합니다. 앱 로그는 콘솔에 기록하며 별도 무제한 로그 파일을 만들지 않습니다. [공식 Python 로그 안내](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/)

실제 운영 배포를 대신하지 않는 읽기 전용 WSGI 점검은 로컬의 운영 설정+테스트 DB로 `python tools/smoke_wsgi.py`를 실행할 수 있습니다. 이 도구는 HTTPS 프록시 헤더를 모의하며 실제 인증서·외부 네트워크·계정 메모리 검증은 하지 않습니다.

### 6. 운영 정리와 백업

예약 작업이 가능하면 다음처럼 프로젝트 디렉터리에서 만료 세션을 정기적으로 정리합니다. 일정은 계정의 실제 기능을 확인하여 설정하고, 미설정 시 수동 실행합니다.

```bash
cd /home/<account>/apps/note-demo
/home/<account>/venvs/note-demo/bin/python manage.py clearsessions
```

개인화된 페이지가 있으므로 플랫폼 HTTP 캐시를 임의로 활성화하지 않습니다. 디스크·메모리 사용량은 관리 화면에서 측정하고, 작은 seed와 텍스트 데이터만 운영합니다. 업로드·대형 라이브러리·백그라운드 워커는 포함하지 않습니다.

업데이트 전에는 앱 코드/고정 의존성과 DB 백업을 계정 외부의 접근 제한된 위치에 보관합니다. 예를 들어 **로컬 PC에서** 서버와 같은 메이저 버전 이상의 `pg_dump`로 백업할 수 있습니다.

```bash
pg_dump -h postgresql-<account>.alwaysdata.net -p 5432 -U <db-user> -W -d <db-name> -Fc -f note-demo.dump
```

외부 DB 연결 정책이 다르면 SSH에서 덤프 후 SFTP로 내려받고 서버에 덤프를 누적하지 마세요. 복구는 새 빈 DB에 먼저 검증하고, 운영 복원 시에는 쓰기를 중지한 뒤 대상 DB를 명시해 진행합니다.

```bash
pg_restore -h <restore-host> -U <restore-user> -W -d <new-empty-db> --no-owner --no-acl note-demo.dump
```

코드 롤백만으로 DB 마이그레이션이 되돌아가지 않습니다. DB 복원은 백업 이후 데이터를 잃을 수 있으므로 복원 시점을 확인하세요. 테스트에서는 별도 로컬 DB에 덤프/복원을 실제 검증했습니다.

## 자주 발생하는 문제

| 증상 | 확인할 항목 |
| --- | --- |
| Python이 없거나 기존 venv가 실행되지 않음 | Python 설치/기본 인터프리터 경로 확인 후 새 .venv 생성 |
| connection timeout expired / DB 연결 실패 | 임시 DB라면 pg_ctl status로 실행 상태 확인 후 55432로 시작. DB 서버를 켠 뒤 Django도 재시작. 호스트/포트/DB명/암호와 환경변수 우선순위 확인 |
| 테스트 DB 생성 권한 오류 | 로컬 테스트 사용자 CREATEDB 권한. 운영 권한으로 해결하지 않기 |
| Missing staticfiles manifest entry / CSS 404 | 올바른 환경에서 collectstatic 후 WSGI 재시작 |
| 운영 HTTPS 무한 리다이렉트 | 실제 alwaysdata 프록시와 TRUST_PROXY_HTTPS, 전달 헤더 확인 |
| DisallowedHost / CSRF 403 | 실제 호스트와 https 출처, 폼 CSRF 토큰, Secure 쿠키 확인 |
| 관리 명령이 로컬 설정으로 실행됨 | .env의 DJANGO_SETTINGS_MODULE과 셸/사이트 환경변수 충돌 확인 |
| 관리자 로그인 후 Django /admin/이 없음 | 전용 화면 /moderation/terms/ 사용. Django admin 미설치 |

[구현 계획과 진행 상태](implementation_plan.md), [검증 기록](docs/verification.md), [배포 요약](docs/deploy_alwaysdata.md)을 함께 참고하세요.

