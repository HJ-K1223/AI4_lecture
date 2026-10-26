# 무료 배포 점검과 alwaysdata 배포 방법

확인일: 2026-10-23. 현재 공식 자료를 추가 검색하여 alwaysdata를 비영리 학습용 추천 대상으로 선정했습니다. 비교는 `HOSTING_COMPARISON.md`에 있습니다. 실제 호스팅 계정 생성이나 배포는 수행하지 않았습니다.

## 앱이 요구하는 조건

- Python 3.10 이상, FastAPI·Uvicorn 실행 지원, 프로세스 1개.
- SQLite 파일을 쓸 수 있는 로컬 디스크. 글을 계속 보존하려면 재시작·재배포 후에도 남는 저장 경로가 필요합니다.
- `GUESTBOOK_DB_PATH` 환경변수로 DB 파일 경로를 지정할 수 있습니다. 상대경로는 이 프로젝트 폴더 기준입니다. 기본값은 `data/guestbook.db`입니다.
- 호스팅의 사용량·결제 설정은 해당 계정에서 별도로 확인해야 합니다. 글 개수와 요청 크기 제한은 디스크·응답 크기를 줄이지만 트래픽·호스팅 요금을 보장하지 않습니다.

외부 API, 외부 DB, 이미지, CDN, 예약 작업, npm 빌드, JavaScript가 없습니다. 운영용 requirements에는 기존 두 패키지만 있으며 테스트 도구는 배포하지 않습니다. 데이터는 최대 1,000건, 글당 이름 20자·내용 500자, 목록은 페이지당 10건입니다.

## 추천: alwaysdata Free

현재 [공식 무료 플랜 사양](https://help.alwaysdata.com/en/docs/admin-billing/billing/public-cloud-prices/)은 디스크 1 GB, RAM 256 MB, CPU 1/4이며, 비영리 용도와 계정의 alwaysdata.net 주소로 제한됩니다. 계정 디스크에는 코드·가상환경·로그·DB 등이 함께 들어갑니다.

이 앱의 FastAPI·Uvicorn·SQLite 구성을 유지할 수 있습니다. 새 라이브러리나 프레임워크를 추가하지 않습니다. 다음 절차는 공식 ASGI·User program 설정을 우리 앱에 맞게 적용한 안내이며 해당 계정에서 실행 검증하지 않았습니다.

### 1. 계정 및 Python 준비

[alwaysdata](https://www.alwaysdata.com/)에서 Free 계정을 만듭니다. 유료 플랜의 30일 체험과 Free를 구분합니다. 아래 모든 `ACCOUNT`는 실제 계정 이름으로 바꿉니다. SSH 사용자 이름이 다르면 관리자 화면에 표시된 사용자 이름을 사용합니다.

관리자 `Environment > Python`에서 기존 로컬 검증과 같은 Python 3.13을 선택합니다. [Python 공식 설정 안내](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/)에 따라 기본 실행 명령은 `python`을 사용합니다.

`Remote access > SSH/SFTP`에서 접속 정보와 SSH 호스트 지문을 확인합니다. PowerShell에서 접속합니다. [SSH 공식 안내](https://help.alwaysdata.com/en/docs/web-hosting/remote-access/ssh/)

```powershell
ssh ACCOUNT@ssh-ACCOUNT.alwaysdata.net
```

접속한 서버에서 코드 폴더와 DB 폴더를 만듭니다.

```sh
mkdir -p /home/ACCOUNT/guestbook /home/ACCOUNT/guestbook-data
exit
```

### 2. 필요한 파일만 업로드

Windows PowerShell에서 실행합니다. scp가 없으면 관리자에서 안내하는 SFTP 접속 방식으로 같은 파일을 올릴 수 있습니다.

```powershell
cd C:\AI4
scp .\Day1_Day8\main.py .\Day1_Day8\requirements.txt ACCOUNT@ssh-ACCOUNT.alwaysdata.net:/home/ACCOUNT/guestbook/
scp -r .\Day1_Day8\templates .\Day1_Day8\static ACCOUNT@ssh-ACCOUNT.alwaysdata.net:/home/ACCOUNT/guestbook/
```

`.venv`, `.test_tmp`, `.smoke_tmp`, 테스트 DB, 실제 개인 DB는 위 명령에 포함되지 않습니다. Windows 가상환경은 Linux 서버로 복사하지 않고 서버에서 새로 만듭니다.

### 3. 서버 가상환경 설정

다시 SSH로 접속한 후 아래 Linux 명령을 실행합니다.

```sh
cd /home/ACCOUNT/guestbook
python --version
python -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python -m pip check
```

Python 버전이 선택한 3.13인지 확인합니다. 설치 대상은 기존 FastAPI·Uvicorn과 필수 의존성뿐입니다. 설치 실패 시 오류를 확인하고, 임의로 라이브러리나 고정 버전을 바꾸지 않습니다. `--no-cache-dir`은 계정 디스크에 pip 캐시가 쌓이는 것을 줄입니다.

### 4. 웹 사이트 등록

관리자 `Web > Sites`에서 기본 사이트를 수정하거나 `Add a site`를 선택합니다. 같은 주소를 중복 등록하지 않습니다. ASGI는 **User program** 유형으로 등록합니다. [공식 ASGI 안내](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/), [User program 필드 안내](https://help.alwaysdata.com/en/docs/web-hosting/sites/http-servers/user-program/).

| 항목 | 값 |
| --- | --- |
| Name | 작은 방명록 |
| Addresses | `ACCOUNT.alwaysdata.net` (관리자가 제공한 실제 기본 주소) |
| Type | `User program` |
| Working directory | `/home/ACCOUNT/guestbook` |
| Environment | `GUESTBOOK_DB_PATH=/home/ACCOUNT/guestbook-data/guestbook.db` |

Command에는 다음 한 줄을 입력합니다.

```sh
/home/ACCOUNT/guestbook/.venv/bin/python -m uvicorn main:app --host $IP --port $PORT --workers 1
```

`$IP`와 `$PORT`는 문자 그대로 두며 플랫폼이 제공하는 값을 사용합니다. 공식 문서는 지정된 IPv6 주소와 포트에서 실행하도록 안내합니다. 임의로 127.0.0.1이나 8000으로 바꾸지 않습니다. 운영 명령에 `--reload`는 넣지 않습니다.

별도 `Advanced > Services` 등록은 필요하지 않습니다. 이 기능은 무료 플랜에서 사용할 수 없는 별도 서비스 기능입니다. HTML과 CSS는 우리 FastAPI 앱에서 제공하므로 별도 정적 파일 매핑도 필요 없습니다.

### 5. 배포 확인

저장 후 제공된 HTTPS 주소를 엽니다. 글 한 개를 등록하고 다음 사항을 확인합니다.

1. 이름·내용이 목록에 나타나고 한글·줄바꿈이 표시되는지 확인합니다.
2. `https://ACCOUNT.alwaysdata.net/static/style.css`가 정상 응답하는지 확인합니다.
3. 사이트를 관리자에서 재시작한 뒤 같은 글이 남아 있는지 확인합니다.
4. SSH에서 `/home/ACCOUNT/guestbook-data/guestbook.db` 생성과 계정 디스크 사용량을 확인합니다.

실패하면 관리자 사이트 로그 또는 `/home/ACCOUNT/admin/logs/sites/`를 확인합니다. 이 절차의 재시작 후 글 보존 확인을 통과해야 실제 배포 완료로 판단합니다. [사이트·로그 안내](https://help.alwaysdata.com/en/docs/web-hosting/sites/add-a-site/).

### 6. 이후 코드 갱신

수정한 `main.py`, `templates`, `static`만 같은 위치에 업로드하고 사이트를 재시작합니다. DB는 코드 폴더 바깥에 있으므로 코드 업로드 대상으로 삼지 않습니다. requirements가 바뀌었다면 승인된 변경인지 확인하고 가상환경에서 설치합니다.

무료 플랜의 파일 백업은 매일 생성되고 3일간 보관된다고 [공식 문서](https://help.alwaysdata.com/en/docs/web-hosting/backups/)에 안내되어 있습니다. 중요한 방명록은 사이트를 잠시 정지하여 쓰기가 없는 상태에서 DB 파일을 별도로 내려받는 방식으로도 보관할 수 있습니다.

## 대안: Render 무료 플랜 — 데이터 소실을 허용하는 실습용

[Render 공식 무료 플랜 문서](https://render.com/docs/free)에 따르면 무료 웹 서비스는 영구 디스크를 지원하지 않으며 재배포·재시작·유휴 정지 시 로컬 SQLite 파일 변경이 사라집니다. 따라서 지속적으로 글을 보존하는 방명록의 배포 대상으로는 부적합합니다. 데이터 소실을 허용한 수업 시연에서만 아래 설정을 사용할 수 있습니다.

| 설정 | 값 |
| --- | --- |
| 서비스 | Web Service / Free |
| Root Directory | Day1_Day8 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1` |

연결한 저장소의 `Day1_Day8` 폴더를 배포합니다. 개인 DB 파일과 테스트 산출물은 업로드하지 않습니다. 무료 플랜 여부와 결제·초과 사용 설정을 확인하고 유료 디스크나 유료 서비스로 자동 변경하지 않습니다. 무료 유휴 종료와 사용량 제한은 서비스 공식 문서와 계정 화면이 기준입니다.

## PythonAnywhere: 배포 전 계정별 확인이 필요한 후보

[무료 계정 문서](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)에는 웹 앱 1개와 512 MiB 디스크가 기재되어 있습니다. 다만 [ASGI 공식 안내](https://help.pythonanywhere.com/pages/ASGICommandLine)는 FastAPI 배포를 실험 기능으로 설명하며 장기 가격이 확정되지 않았다고 명시합니다. 일반 무료 웹 앱 지원만으로 FastAPI가 계속 무료라고 단정할 수 없습니다.

이곳을 선택한다면 해당 계정의 무료 ASGI 지원·SQLite 파일 보존·만료/갱신 조건을 확인한 뒤 진행해야 합니다. 별도 배포 CLI 설치가 필요하다면 사용자의 추가 승인 대상으로 남깁니다. 이번 앱에는 배포 CLI를 추가하지 않았습니다.

## 무료 범위의 한계

이번 추가 조사에서는 alwaysdata의 계정 파일공간과 ASGI 웹 사이트 지원을 확인했습니다. 다만 무료 플랜의 유지 조건이 미래에도 동일하다는 보장은 없으며 실제 계정의 가입·사용 조건이 우선합니다. 비영리 조건에 맞는 학습용 배포에 추천하며 실제 보존 여부는 위 재시작 시험으로 확인합니다. 외부 DB·다른 프레임워크·새 라이브러리를 쓰는 변경은 먼저 사용자와 확인합니다.

무료 플랜이라도 무제한 접근을 보장하지 않습니다. 이 앱은 소규모 학습용이며 로그인·도배 방지·관리자 기능이 없습니다. 공개 운영에 그런 기능이 필요해지면 범위와 기술을 먼저 협의합니다.
