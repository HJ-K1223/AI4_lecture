# 작은 방명록

이름과 글을 남기고 최신 글부터 읽는 학습용 방명록입니다. 화면은 HTML과 CSS만 사용하며 JavaScript, 프런트엔드 프레임워크, 외부 폰트, 이미지, 유료 API를 사용하지 않습니다. 실행에 필요한 외부 라이브러리는 기존 수업의 FastAPI, Pydantic, Uvicorn으로 한정했습니다.

## 실행

저장소 루트(`C:\AI4`)에서 기존 가상환경을 사용합니다.

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --app-dir Day1-Day8 --reload
```

브라우저에서 <http://127.0.0.1:8000>을 엽니다. `/health`는 저장소 연결 상태를 확인합니다.

새 환경에서는 Python 3.11 이상에서 다음과 같이 설치합니다. 버전은 Day8 수업의 requirements와 같습니다.

```powershell
python -m pip install -r Day1-Day8/requirements.txt
python -m uvicorn main:app --app-dir Day1-Day8 --reload
```

기본 DB는 `Day1-Day8/data/guestbook.db`이며 앱 시작 시 자동 생성됩니다. 다른 위치를 지정하려면 실행 전에 `GUESTBOOK_DB_PATH` 환경변수를 설정합니다. 로컬에서는 같은 DB 경로로 재시작하면 글이 유지됩니다. DB 파일은 Git에 포함하지 않습니다.

## 서버 중지

서버를 실행한 터미널에서 **`Ctrl+C`**를 누릅니다. `--reload`로 실행한 경우에도 같은 방법으로 중지합니다. 종료 로그가 출력되고 명령 입력 프롬프트가 돌아오면 중지된 것입니다.

실행한 터미널에 접근할 수 없다면 `(.venv)`가 활성화된 Windows 명령 프롬프트(cmd) 터미널에서 포트를 사용하는 프로세스를 확인합니다. `(.venv)`는 가상환경 표시이며, 아래는 PowerShell 전용 명령이 아닌 Windows 기본 명령입니다. 기본 실행 포트는 `8000`이며, 다른 포트로 실행했다면 해당 번호로 바꿉니다.

```bat
netstat -ano | findstr LISTENING | findstr /C:":8000 "
```

출력된 행의 마지막 열이 PID(프로세스 번호)입니다. 아래 `12345`는 예시이므로 실제 번호로 바꿉니다.

```bat
tasklist /FI "PID eq 12345"
```

`tasklist`는 프로세스 이름을 보여줍니다. `python.exe`라는 이름만으로는 방명록 서버인지 알 수 없으므로, 실행한 포트와 PID가 방명록 Uvicorn 서버에 해당하는지 확인한 뒤 중지합니다. `/T`는 자식 프로세스도 함께 종료하고, `/F`는 강제 종료하므로 실행 터미널에 접근할 수 있을 때는 위의 `Ctrl+C`를 우선 사용합니다.

```bat
taskkill /PID 12345 /T /F
```

서버를 중지해도 로컬 SQLite 파일과 저장된 글은 유지됩니다.

## 기능과 범위

- 이름: 앞뒤 공백 제거 후 1~30자, 내용: 1~1,000자. 공백뿐인 입력은 거부합니다.
- 글은 최신순으로 20개씩 표시합니다. 전체 글은 최대 1,000개이며 한도 도달 시 기존 글을 보존하고 새 글은 거부합니다.
- SQLite `entries` 테이블 하나만 사용합니다. 필드는 `id`, `name`, `message`, `created_at`이며 관계 및 외래 키가 없습니다. 시간은 UTC로 표시합니다.
- SQL 값 바인딩과 HTML 이스케이프로 입력을 처리합니다. 요청 본문은 최대 16 KiB입니다.
- HTML 폼을 표준 라이브러리 `urllib.parse`로 읽어 별도 폼 파싱·템플릿 라이브러리를 추가하지 않았습니다.
- 익명 공개 작성·읽기만 제공합니다. 수정, 삭제, 로그인, 첨부, 관리자 화면은 이번 범위에 포함하지 않습니다. 중복 클릭 자체를 막는 기능은 없지만 저장 후 303 리다이렉트로 새로고침 재전송을 방지합니다.
- 쓰기 권한은 모든 방문자에게 열려 있습니다. 자동 도배 방지나 운영자 관리 기능은 구현하지 않았으므로 공개 운영 전 용도에 맞게 검토해야 합니다. 기능 확장이나 라이브러리 추가는 사용자와 협의합니다.

## 검증

기존 가상환경에 pytest와 httpx가 있어 추가 설치 없이 검증할 수 있습니다.

```powershell
.venv\Scripts\python.exe -m pytest Day1-Day8/test_guestbook.py -q
```

새 환경의 테스트 의존성은 `requirements-dev.txt`에 있습니다. 테스트는 임시 DB를 사용하며 실제 방명록 데이터를 수정하지 않습니다. 저장·재시작, 단일 테이블, 입력 경계, 페이지 이동, HTML/SQL 입력 처리, 용량 제한, 저장소 장애 응답을 확인합니다.

## Render 첫 배포 가이드

확인일: **2026-10-23**. Render를 처음 방문하는 사용자를 위한 GitHub 연결 방식의 무료 배포 안내입니다. [Render 공개 홈페이지](https://render.com/)와 공식 문서를 확인했습니다. 가입 화면은 JavaScript가 필요하고 연결된 브라우저가 없어, 로그인 후 화면을 직접 조작하거나 실제 배포를 수행하지는 않았습니다. 아래 화면명은 공식 문서 기준입니다.

배포 흐름은 **GitHub에 코드 올리기 → Render 가입 → 저장소 연결 → Free Web Service 생성 → 접속 확인**입니다. 별도 DB 서비스나 Docker 설정 없이 기존 FastAPI와 Python 내장 SQLite를 사용합니다.

**SQLite 보존 조건:** Render Free에서는 실행 중 생성한 DB 파일이 절전·재시작·재배포 시 사라집니다. 이 가이드는 테스트 글이 초기화될 수 있는 무료 시연 배포용입니다. 영구 디스크는 유료 서비스에서만 연결할 수 있으며, DB 경로를 바꾸는 것만으로 무료 저장 공간이 영구화되지는 않습니다. [공식 무료 제한](https://render.com/docs/free#local-files-lost-on-redeploy)

### 1. GitHub에 배포할 코드 올리기

현재 Render에서 선택한 배포 저장소는 [skn29teacher/guestbook](https://github.com/skn29teacher/guestbook), 브랜치는 `main`입니다. 이 저장소의 최상위에 `main.py`, `requirements.txt`, `templates/index.html`이 있는 것을 확인했습니다. 따라서 Render의 Root Directory는 비워 둡니다.

Render는 GitHub에 올라간 코드로 배포합니다. 아래 명령은 이후 코드를 수정해서 `guestbook` 저장소에 다시 올릴 때 사용하는 **로컬 Windows cmd의 `(.venv)` 터미널** 명령입니다. 로컬 원격 주소가 `guestbook`으로 연결된 작업 폴더에서 실행합니다.

```bat
git remote -v
git status --short
git add .
git diff --cached --name-only
```

출력에서 커밋할 파일을 확인합니다. `.venv`, `data/guestbook.db`, `*.db`가 보인다면 커밋하기 전에 `.gitignore`에 제외 규칙을 추가해야 합니다. 다른 작업의 파일이 이미 스테이징되어 있다면 함께 커밋되지 않도록 목록을 먼저 정리합니다. 이어서 실행합니다.

```bat
git commit -m "Add guestbook app and Render deployment guide"
git push origin main
```

GitHub 웹사이트에서 해당 저장소의 `main` 브랜치를 열어 다음 파일이 보이는지 확인합니다. 이 가이드를 작성하면서 위 커밋·푸시 명령을 대신 실행하지는 않았습니다.

```text
main.py
requirements.txt
templates/
  index.html
```

`git push`에서 권한 오류가 나면 로컬 원격 주소와 해당 GitHub 저장소에 쓰기 권한이 있는 계정인지 확인합니다.

### 2. Render 처음 방문 및 가입

1. 브라우저에서 <https://render.com/>을 엽니다.
2. **Get started**를 눌러 가입 화면으로 이동합니다. [대시보드](https://dashboard.render.com/)로 바로 접속해도 됩니다.
3. GitHub 계정으로 가입·로그인하는 방식을 선택하면 이후 저장소 연결이 편리합니다. 안내되는 계정 확인 절차를 완료합니다.
4. 처음 생성되는 작업 공간을 사용합니다. 작업 공간은 서비스를 모아 관리하는 곳이며, 이름은 본인이 알아보기 쉽게 정하면 됩니다.

공식 첫 배포 가이드는 결제 없이 무료 리소스로 진행할 수 있다고 안내합니다. 무료 작업 공간을 사용하더라도 **각 서비스의 실행 요금제를 별도로 Free로 선택**해야 합니다. 유료 작업 공간이나 유료 실행 요금제를 선택할 필요는 없습니다. [첫 배포 안내](https://render.com/docs/your-first-deploy), [요금제 구분](https://render.com/docs/free#create-a-free-instance)

### 3. GitHub 저장소 연결

1. Render 대시보드 오른쪽 위 **+ New → Web Service**를 선택합니다. 이 앱은 Python 서버가 실행되는 Web Service입니다.
2. 코드 가져오기 방식에서 **Git Provider**를 선택하고 GitHub를 연결합니다.
3. GitHub의 Render 앱 권한 화면이 열리면 배포할 저장소를 포함하도록 설정합니다. 저장소를 선택할 수 있다면 `guestbook`을 선택합니다.
4. Render 저장소 목록에서 해당 저장소를 찾아 **Connect**를 누릅니다.

연결 메뉴를 별도로 찾아야 하면 **Account Settings → Account Security → Git Deployment Credentials → Add credential → GitHub**를 사용합니다. 저장소가 보이지 않으면 [Render GitHub 앱 설정](https://github.com/apps/render/installations/new)의 **Repository access**에 저장소가 포함되어 있는지 확인합니다. [공식 연결·문제 해결](https://render.com/docs/git-provider)

### 4. 생성 화면에 입력할 값

아래 표는 현재 화면에 연결된 `skn29teacher/guestbook` 저장소를 배포하는 값입니다. 자동으로 입력된 명령이 있어도 표와 대조하세요.

| 화면 항목 | 입력·선택할 값 | 설명 |
| --- | --- | --- |
| Name | 예: `ai4-guestbook` | 서비스 이름. 중복이면 다른 이름 사용 |
| Language / Runtime | `Python 3` | Python 실행 환경 |
| Branch | `main` | 코드가 올라간 브랜치 |
| Region | `Singapore` 권장 | 한국 방문자를 고려한 선택. 생성 후 지역 변경은 새 서비스 생성 필요 |
| Root Directory | **비워 둠** | `main.py`와 `requirements.txt`가 저장소 최상위에 있음 |
| Build Command | `python -m pip install -r requirements.txt` | 실행에 필요한 패키지 설치 |
| Start Command | `python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1` | FastAPI 서버 시작 |
| Compute / Instance Type | **`Free`** | 무료 실행 요금제 |
| Health Check Path | `/health` | DB 접근까지 확인하는 앱 상태 경로 |

Root Directory는 공백 그대로 둡니다. 위 Start Command의 **`$PORT`는 그대로 입력**합니다. Render의 Linux 서버가 제공하는 값이며, 이 명령은 로컬 Windows cmd에 입력하는 명령이 아닙니다. `--app-dir`와 `--reload`도 붙이지 않습니다. [Web Service 설정·포트](https://render.com/docs/web-services), [FastAPI 배포 예시](https://render.com/docs/deploy-fastapi), [지역 안내](https://render.com/docs/regions)

### 5. Python 버전과 상태 확인 경로 설정

생성 화면의 **Environment Variables**에서 다음 값을 추가합니다. 화면에 없다면 **Advanced** 영역을 확인합니다.

| Key | Value |
| --- | --- |
| `PYTHON_VERSION` | `3.13.12` |

현재 로컬 `.venv`에서 Python 3.13.12와 프로젝트의 고정 패키지 버전이 함께 실행되는 것을 확인했습니다. Render 신규 서비스의 현재 기본 Python은 3.14 계열이며, 현재 고정된 Pydantic 2.11.5의 첫 배포에 그대로 적용하지 않도록 위 버전을 명시합니다. 환경변수 방식은 `3.13`이 아닌 **전체 버전 `3.13.12`**를 요구합니다. [Render Python 버전 설정](https://render.com/docs/python-version), [Pydantic의 Python 3.14 지원 도입](https://pydantic.dev/articles/pydantic-v2-12-release)

SQLite는 기본 경로에 자동 생성되므로 `DATABASE_URL`이나 별도 DB 계정을 추가할 필요가 없습니다. `GUESTBOOK_DB_PATH`도 이번 무료 배포에서는 비워둡니다.

Health Check Path가 생성 화면에 보이지 않으면 배포 후 **Settings → Health Checks → Edit**에서 `/health`를 입력하고 **Save Changes**를 누릅니다. [공식 상태 확인 설정](https://render.com/docs/health-checks)

### 6. 배포 시작 및 성공 확인

1. **Free**, 비어 있는 Root Directory, 명령어, `PYTHON_VERSION`을 다시 확인합니다.
2. 화면 맨 아래 **Deploy** 또는 **Create Web Service**를 누릅니다. 공식 문서에 두 버튼명이 사용되며, 가입 후 실제 화면의 생성 버튼을 사용합니다.
3. 생성된 서비스의 **Deploys** 페이지에서 로그를 확인합니다. 패키지 설치 후 Uvicorn 서버가 시작되어야 합니다.
4. 상태가 **Live**가 되면 서비스 페이지에 표시된 `https://서비스주소.onrender.com` 링크를 엽니다. 실제 주소는 화면의 링크를 사용합니다.

정상 시작 로그에는 다음과 같은 메시지가 나타납니다. 실제 포트 숫자는 Render가 정합니다.

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:...
```

서비스 주소 뒤에 `/health`를 붙여 접속하면 다음 응답이 나와야 합니다.

```json
{"status":"ok"}
```

방명록 화면에서 이름과 테스트 글을 입력하고, 등록 후 목록에 표시되는지와 새로고침 후에도 보이는지 확인합니다. 로컬 방명록 글은 서버로 복사하지 않았으므로 처음에는 빈 목록이 정상입니다. [배포 상태·공개 주소 확인](https://render.com/docs/your-first-deploy#5-monitor-your-deploy)

### 7. 수정한 코드 다시 배포하기

로컬에서 파일을 수정한 뒤, 1단계처럼 변경 내용을 확인하고 `git add`, `git commit`, `git push origin main`을 실행합니다. GitHub 연결 방식은 기본적으로 연결된 브랜치에 push할 때 자동 재배포합니다.

수동으로 최신 코드를 배포하려면 서비스의 **Deploys → Manual Deploy → Deploy latest commit**을 선택합니다. **Restart service**는 현재 배포를 재시작하는 기능입니다. 두 작업 모두 무료 서버의 SQLite 글이 초기화될 수 있습니다. [자동·수동 배포 안내](https://render.com/docs/deploys)

서비스를 만든 뒤 Python 버전을 수정했다면 **Environment**에서 값을 저장할 때 **Save, rebuild, and deploy**를 선택해 새 Python 버전으로 다시 빌드합니다. [환경변수 저장 방법](https://render.com/docs/configure-environment-variables)

### 8. Render 서버 중지·재개와 무료 사용량

Render 서버는 로컬 터미널을 닫거나 `Ctrl+C`를 눌러도 계속 실행됩니다. 중지하려면 대시보드 서비스 목록에서 해당 서비스 옆의 체크박스를 선택하고 표시되는 메뉴의 **Suspend**를 사용합니다. 다시 실행하려면 같은 방식으로 **Resume**을 사용합니다. [공식 중지·재개 안내](https://render.com/changelog/suspend-and-resume-services-in-bulk-from-the-render-dashboard)

무료 서버는 15분 동안 요청이 없으면 절전하며, 다음 방문 시 다시 켜지는 데 약 1분이 걸릴 수 있습니다. 실행 시간은 워크스페이스 전체가 월 750시간을 나눠 사용하며, 소진하면 다음 달까지 무료 서버가 중지됩니다. **Billing → Monthly Included Usage**에서 실행 시간·트래픽·빌드 사용량을 확인합니다. 결제 수단이 등록된 경우에는 **외부 전송량·빌드 시간의 포함량 초과분**에 추가 요금이 발생할 수 있습니다. 결제 수단이 없으면 해당 한도에 따라 서비스 또는 새 빌드가 제한됩니다. [무료 동작·사용량 조건](https://render.com/docs/free)

### 처음 배포할 때 자주 만나는 문제

| 증상 | 확인할 내용 |
| --- | --- |
| 저장소가 목록에 없음 | GitHub 계정과 Render 앱의 Repository access 확인 |
| `requirements.txt`를 찾을 수 없음 | GitHub 저장소 최상위에 파일이 있는지, Root Directory가 비어 있는지 확인 |
| `Could not import module "main"` | GitHub 저장소 최상위의 `main.py`와 비어 있는 Root Directory 확인 |
| Pydantic·`pydantic-core`·`maturin` 설치 실패 | 로그의 Python 버전을 확인하고 `PYTHON_VERSION=3.13.12`로 전체 재빌드 |
| 열린 포트를 찾지 못함 | Start Command의 `--host 0.0.0.0 --port $PORT` 확인 |
| `templates/index.html` 관련 오류 | GitHub에도 `templates/index.html`이 같은 구조와 대소문자로 올라갔는지 확인 |
| `/health`가 503 응답 | SQLite 접근 실패를 의미. DB 경로·쓰기 권한·서비스 로그 확인 |
| 첫 방문에 로딩 화면이 오래 표시됨 | 절전 복귀일 수 있으므로 잠시 기다린 뒤 재접속 |
| `/docs`가 404 응답 | 현재 앱은 API 문서 화면을 끈 상태. `/`와 `/health`로 확인 |
| 나중에 방문하니 글이 사라짐 | Free 서버의 임시 파일시스템에 따른 동작. 영구 보존 설정으로 오해하지 않기 |

실패 시 **Deploys**의 해당 배포 로그에서 마지막 오류부터 확인합니다. [Python 배포 문제 해결](https://render.com/docs/troubleshooting-python-deploys), [일반 배포 문제 해결](https://render.com/docs/troubleshooting-deploys)

## 파일 안내

`main.py`는 입력 모델·DB·라우트, `templates/index.html`은 화면, `test_guestbook.py`는 검증, `ANALYSIS.md`는 기존 수업과 구현의 연결을 설명합니다. 원래 요청 파일인 `Codex.md`는 그대로 보존했습니다.
