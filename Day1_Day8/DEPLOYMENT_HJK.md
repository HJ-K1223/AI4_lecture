# alwaysdata 방명록 배포 매뉴얼 — hjk 계정

작성일: 2026-10-23. 이 대화에서 확인한 실제 경로와 오류 해결 내용을 정리했다. 실제 사이트의 최종 정상 동작은 아직 확인하지 않았다.

## 현재까지 확인한 상태

- 서버 계정: `hjk`
- SSH 서버: `ssh-hjk.alwaysdata.net`
- 접속 주소: `https://hjk.alwaysdata.net/`
- 로컬 코드: `C:\AI4\Day1_Day8`
- 서버 코드: `/home/hjk/guestbook`
- `main.py`, `templates/index.html`, `static/style.css` 업로드 확인.
- 사이트 설정의 주소·명령·작업 폴더·DB 환경변수는 화면에서 확인.
- 마지막으로 확인한 원인: 서버에 `.venv/bin/python`이 없어서 앱 실행 실패.
- 가상환경 생성·라이브러리 설치를 안내했으나 실행 성공 결과는 아직 전달받지 못함.

이미 업로드했다면 1~3단계를 다시 할 필요 없이 4단계부터 진행한다.

## 1. SSH 계정 확인

alwaysdata 관리자 `Remote access > SSH/SFTP`에서 다음을 확인한다.

| 항목 | 설정 |
| --- | --- |
| Name | `hjk` |
| Shell | `bash` |
| Enable password-based login | 체크 |
| Password | 이 SSH 계정에 지정한 비밀번호 |

Name이 실제로 다른 경우 명령의 `hjk@` 부분만 실제 SSH 사용자 이름으로 바꾼다. 서버 주소와 `/home/hjk/` 경로는 계정 기준으로 유지한다. 로그인 비밀번호는 SSH 계정 비밀번호이며 관리자 로그인 비밀번호와 같다고 가정하지 않는다. 기존 비밀번호를 유지하는 수정 화면에서는 비밀번호를 비워 둘 수 있다.

현재 SSH 홈 디렉터리는 조회 결과 `/home/hjk/guestbook`이다. 정상 존재하므로 바꿀 필요 없다. 처음 설정할 때는 홈 디렉터리를 `/home/hjk/`로 두어도 되며, 아래 명령은 절대경로를 사용한다.

## 2. Windows PowerShell 열기

시작 메뉴에서 Windows PowerShell을 연다. 프롬프트가 `PS C:\...>`인지 확인한다. 로컬 Git Bash의 `Playdata@DESKTOP... /c/AI4`는 원격 서버 화면이 아니다.

이 문서의 명령은 모두 Windows PowerShell에 입력한다. 따옴표 안의 Linux 명령은 SSH를 통해 서버에서 실행된다. 매번 서버에서 작업한 후 로컬 프롬프트로 돌아오는 것이 정상이다. 비밀번호는 입력 중 글자나 별표가 표시되지 않는다.

첫 접속 시 SSH 호스트 지문은 관리자 SSH/SFTP 화면의 값과 비교한다.

## 3. 폴더 생성과 업로드 — 신규 배포 때만

서버 폴더 생성:

```powershell
C:\Windows\System32\OpenSSH\ssh.exe hjk@ssh-hjk.alwaysdata.net "mkdir -p /home/hjk/guestbook /home/hjk/guestbook-data"
```

로컬 작업 폴더 이동:

```powershell
cd C:\AI4
```

코드와 requirements 업로드:

```powershell
C:\Windows\System32\OpenSSH\scp.exe .\Day1_Day8\main.py .\Day1_Day8\requirements.txt hjk@ssh-hjk.alwaysdata.net:/home/hjk/guestbook/
```

HTML·CSS 폴더 업로드:

```powershell
C:\Windows\System32\OpenSSH\scp.exe -r .\Day1_Day8\templates .\Day1_Day8\static hjk@ssh-hjk.alwaysdata.net:/home/hjk/guestbook/
```

결과 확인:

```powershell
C:\Windows\System32\OpenSSH\ssh.exe hjk@ssh-hjk.alwaysdata.net "ls -R /home/hjk/guestbook"
```

필요한 구조:

```text
/home/hjk/guestbook/
├── main.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    └── style.css
```

Windows의 `.venv`, 테스트 폴더, 테스트 DB는 업로드하지 않는다.

## 4. 서버 가상환경 생성과 라이브러리 설치

관리자 `Environment > Python`에서 Python 3.13을 선택하고 저장한다. 이후 PowerShell에서 다음 한 줄을 실행한다.

```powershell
C:\Windows\System32\OpenSSH\ssh.exe hjk@ssh-hjk.alwaysdata.net "cd /home/hjk/guestbook && python --version && python -m venv .venv && .venv/bin/python -m pip install --no-cache-dir -r requirements.txt && mkdir -p /home/hjk/guestbook-data && .venv/bin/python -m pip check"
```

Python 3.13인지 확인한다. 명령의 `&&`는 앞 단계가 성공했을 때만 다음 단계를 실행하게 한다. 마지막 `No broken requirements found.`는 설치된 패키지의 의존성 검사 통과를 의미하며, 사이트 정상 실행까지 보장하는 것은 아니다.

현재 앱에서 승인된 FastAPI·Uvicorn과 필수 의존성만 설치한다. 별도 DB 서비스나 새 라이브러리는 필요 없다.

## 5. 관리자 웹 사이트 설정

`Web > Sites`에서 **주소가 `hjk.alwaysdata.net`인 기존 사이트**를 수정한다. 기본 환영 페이지를 제공하던 사이트가 있다면 그 사이트의 유형을 바꾼다. 같은 주소의 사이트를 중복 생성하지 않는다.

| 항목 | 값 |
| --- | --- |
| Addresses | `hjk.alwaysdata.net` |
| Type | `User program` |
| Working directory | `/home/hjk/guestbook` |
| Environment | `GUESTBOOK_DB_PATH=/home/hjk/guestbook-data/guestbook.db` |

주소에 `https://`나 `/guestbook`을 붙이지 않는다. 주소 입력에 빈 추가 행이 있다면 빈 행만 제거한다. 작업 폴더 왼쪽에 `/home/hjk/`가 고정 표시되면 오른쪽 칸에는 `guestbook`만 입력한다.

Command:

```sh
/home/hjk/guestbook/.venv/bin/python -m uvicorn main:app --host $IP --port $PORT --workers 1
```

`$IP`와 `$PORT`는 문자 그대로 입력한다. 플랫폼이 제공하는 주소·포트를 사용한다. `--reload`는 넣지 않는다. 별도 `Advanced > Services`에 등록하지 않는다.

저장 후 목록에서 유형이 User program으로 반영됐는지 확인하고 사이트를 재시작한다.

## 6. 접속과 완료 확인

브라우저에서 **https://hjk.alwaysdata.net/** 를 연다. 필요하면 Ctrl+F5 또는 시크릿 창으로 확인한다.

배포 완료 기준:

1. 작은 방명록 화면과 CSS가 표시된다.
2. 이름·내용을 등록하면 목록에 표시된다.
3. 관리자에서 사이트를 재시작해도 글이 남아 있다.

DB는 첫 앱 시작 때 `/home/hjk/guestbook-data/guestbook.db`에 자동 생성된다.

## 7. 오류별 확인

| 증상 | 의미·대응 |
| --- | --- |
| `Permission denied` | SSH Name과 비밀번호 확인. `SSH_USER`라는 예시 문자열을 그대로 쓰지 않음 |
| `poll: No error` 후 연결 종료 | 원인 단정 불가. Git Bash 대신 새 Windows PowerShell에서 이 문서의 원격 명령 방식 사용 |
| `/home/hjk`가 없다고 나옴 | 먼저 명령 실행 위치 확인. 로컬 Git Bash에서 Linux 서버 경로를 조회했을 수 있음 |
| `.venv/bin/python` 없음 | 4단계 실행. 이번 대화에서 확인한 실제 실행 실패 원인 |
| `No module named uvicorn/fastapi` | 서버 가상환경에 requirements 설치 여부 확인 |
| alwaysdata 기본 환영 페이지 | Web > Sites의 주소·유형·저장 상태와 브라우저 캐시 확인 |
| `Connection to upstream failed` 또는 502/503 | 앱 시작 실패, 지정 IP·포트 미사용 등 가능. 해당 사이트 로그 확인 |

경로·패키지 확인 명령:

```powershell
C:\Windows\System32\OpenSSH\ssh.exe hjk@ssh-hjk.alwaysdata.net "cd /home/hjk/guestbook && ls -l main.py .venv/bin/python templates/index.html static/style.css && .venv/bin/python -m pip show fastapi uvicorn"
```

로그는 관리자 Web > Sites의 해당 사이트 Logs 또는 `/home/hjk/admin/logs/sites/`에서 확인한다. 필요 시 오류 마지막 부분을 공유하되 비밀번호는 공유하지 않는다.

## 8. 코드 수정 후 재업로드

3단계의 코드·HTML·CSS 업로드 명령을 다시 실행하고 관리자에서 사이트를 재시작한다. `.venv`와 `/home/hjk/guestbook-data`는 덮어쓰지 않는다. requirements를 변경한 경우에만 승인된 변경을 서버 가상환경에 설치한다.

## 무료 플랜 조건과 공식 자료

조사 당시 alwaysdata Free는 비영리 용도·제공 기본 도메인 제한이 있다. 가입·운영 시 계정의 실제 조건이 우선한다. 비교 분석은 `HOSTING_COMPARISON.md`에 있다.

- [무료 플랜 사양](https://help.alwaysdata.com/en/docs/admin-billing/billing/public-cloud-prices/)
- [SSH 접속](https://help.alwaysdata.com/en/docs/web-hosting/remote-access/ssh/)
- [Python과 ASGI 설정](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/)
- [User program 설정](https://help.alwaysdata.com/en/docs/web-hosting/sites/http-servers/user-program/)
- [사이트 주소와 로그](https://help.alwaysdata.com/en/docs/web-hosting/sites/add-a-site/)
