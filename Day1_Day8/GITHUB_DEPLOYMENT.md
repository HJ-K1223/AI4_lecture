# GitHub → alwaysdata 자동 배포 설정

확인일: 2026-10-23. 실제 로컬 설정에서 확인한 origin은 `https://github.com/HJ-K1223/AI4_lecture.git`, 현재 브랜치는 `main`이다. 원격 저장소 공개 여부, 로컬 커밋의 원격 반영 여부, GitHub Secrets는 확인하지 않았다.

PC의 Git 저장소는 이미 GitHub에 연결되어 있다. 이번 설정은 GitHub에 push한 방명록 코드를 alwaysdata로 전송하고 사이트를 재시작하는 연결을 추가한다.

## 전체 흐름

PC 코드 수정 → 필요한 파일 commit → main에 push → GitHub Actions → 파일 업로드 → 라이브러리 설치 확인 → alwaysdata API로 사이트 재시작 → 홈페이지 응답 확인.

새 Python 라이브러리나 프레임워크는 추가하지 않는다. 표준 Ubuntu runner의 SSH·tar·curl과 공식 actions/checkout을 사용한다. SQLite DB는 `/home/hjk/guestbook-data/guestbook.db`, 가상환경은 `/home/hjk/guestbook/.venv`에 유지한다. 전송 대상은 main.py, requirements.txt, templates, static뿐이다.

현재 준비한 `deploy/alwaysdata.yml`은 비활성 예시 파일이다. 저장소 루트의 `.github/workflows/alwaysdata.yml`로 복사해 GitHub에 push해야 실행된다. 자동 배포를 활성화하거나 GitHub에 push하는 작업은 아직 수행하지 않았다.

## 1. 기존 서버 확인

수동 배포한 사이트가 정상 실행되는 상태에서 설정한다. 서버에 `/home/hjk/guestbook/.venv/bin/python`이 있어야 한다. 없으면 `DEPLOYMENT_HJK.md` 4단계의 가상환경 설치를 먼저 완료한다. 관리자 Command·Working directory·DB 환경변수는 기존대로 둔다.

## 2. 배포 전용 SSH 키 준비

Windows PowerShell에서 실행한다. 같은 이름의 키가 이미 있으면 덮어쓰지 않는다.

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.ssh" | Out-Null
C:\Windows\System32\OpenSSH\ssh-keygen.exe -t ed25519 -C "github-actions-guestbook" -f "$env:USERPROFILE\.ssh\alwaysdata_guestbook"
```

자동 배포용으로 passphrase 질문에는 Enter를 두 번 눌러 빈 값으로 생성한다. 이 전용 키는 비밀번호 없이 동작하므로 개인 키를 저장소나 채팅에 올리지 않는다. 이 안내서는 키를 대신 생성하거나 읽지 않는다.

생성한 공개 키를 복사한다.

```powershell
Get-Content "$env:USERPROFILE\.ssh\alwaysdata_guestbook.pub" | Set-Clipboard
```

alwaysdata 관리자 `Remote access > SSH/SFTP` → `hjk` 사용자의 SSH Keys(열쇠 아이콘) → Add a SSH Key에 공개 키를 등록한다. 기존 비밀번호 로그인은 유지해도 된다.

키 접속 확인:

```powershell
C:\Windows\System32\OpenSSH\ssh.exe -i "$env:USERPROFILE\.ssh\alwaysdata_guestbook" -o BatchMode=yes hjk@ssh-hjk.alwaysdata.net "pwd"
```

## 3. SSH 호스트 정보 준비

이미 접속해 저장된 서버 키를 사용한다. 기존 접속 시 관리자에서 안내한 SSH 지문과 비교한 값이어야 한다.

```powershell
C:\Windows\System32\OpenSSH\ssh-keygen.exe -F ssh-hjk.alwaysdata.net -f "$env:USERPROFILE\.ssh\known_hosts" | Where-Object { $_ -and $_ -notmatch '^#' } | Set-Clipboard
```

복사한 내용을 다음 단계의 `AD_KNOWN_HOSTS`에 넣는다. 결과가 없으면 기존 SSH 접속에서 호스트 키 확인·등록을 먼저 완료한다. 서버 지문이 바뀌면 관리자에서 확인한 뒤 이 Secret을 갱신한다. 호스트 검사를 끄는 방식은 사용하지 않는다.

## 4. alwaysdata API 토큰과 사이트 ID 준비

프로필의 API/Access tokens 메뉴에서 자동 배포용 토큰을 만들고, 가능한 권한 설정에서 해당 계정·사이트 재시작에 필요한 범위로 제한한다. Web > Sites에서 `hjk.alwaysdata.net` 사이트의 숫자 ID를 확인한다. 편집 페이지 URL의 사이트 ID로도 확인할 수 있다. 계정 ID나 포트 8100과 혼동하지 않는다.

이 토큰은 파일 업로드에 쓰는 SSH 키와 별개이며 사이트 재시작 API에 사용한다. 개인 키와 API 토큰은 채팅에 보내지 않고 GitHub Secrets에 직접 등록한다.

## 5. GitHub Secrets 등록

`HJ-K1223/AI4_lecture` 저장소 → Settings → Secrets and variables → Actions → New repository secret에서 다음 네 항목을 만든다.

| Name | Value |
| --- | --- |
| AD_SSH_PRIVATE_KEY | `alwaysdata_guestbook` 개인 키 전체 내용. `.pub` 파일이 아님 |
| AD_KNOWN_HOSTS | 3단계에서 복사한 호스트 키 행 |
| AD_API_TOKEN | alwaysdata에서 생성한 토큰 |
| AD_SITE_ID | 방명록 사이트의 숫자 ID |

개인 키를 Secret에 붙여 넣기 위해 로컬에서 클립보드로 복사할 수 있다.

```powershell
Get-Content -Raw "$env:USERPROFILE\.ssh\alwaysdata_guestbook" | Set-Clipboard
```

등록 후 클립보드를 비운다.

```powershell
Set-Clipboard -Value ""
```

## 6. 워크플로 활성화

다음은 Windows PowerShell 명령이다. 기존 workflow 파일이 있다면 덮어쓰기 전에 내용을 비교한다.

```powershell
cd C:\AI4
New-Item -ItemType Directory -Force .github\workflows | Out-Null
Copy-Item Day1_Day8\deploy\alwaysdata.yml .github\workflows\alwaysdata.yml
git status --short
git add .github/workflows/alwaysdata.yml Day1_Day8/main.py Day1_Day8/requirements.txt Day1_Day8/templates/index.html Day1_Day8/static/style.css
git diff --cached --stat
```

스테이징 목록에 배포할 코드만 있는지 확인한다. 원래 다른 작업을 스테이징했다면 먼저 분리한다. `.venv`, DB, 비밀번호·키는 포함하지 않는다. 확인 후 실행한다.

```powershell
git commit -m "Set up guestbook deployment to alwaysdata"
git push origin main
```

push 후 GitHub Actions 탭에서 `Deploy guestbook to alwaysdata` 실행을 확인한다. 파일 업로드·사이트 재시작·홈페이지 확인이 모두 성공해야 첫 연동이 완료된다. 필요하면 Actions의 Run workflow로 main 배포를 다시 실행할 수 있다.

## 7. 이후 변경 반영

예: UI만 수정한 경우

```powershell
cd C:\AI4
git add Day1_Day8/templates/index.html Day1_Day8/static/style.css
git diff --cached --stat
git commit -m "Update guestbook UI"
git push origin main
```

방명록 실행 파일·HTML·CSS·requirements 또는 활성 workflow 변경에만 자동 배포한다. 다른 수업 코드와 문서만 바꾸면 배포하지 않는다. 문서 변경에도 배포가 필요하면 Run workflow를 사용한다.

배포 시 현재 파일에 덮어쓰므로 잠깐의 불일치와 사이트 재시작 중 짧은 접속 중단이 있을 수 있다. 자동 롤백은 없다. DB는 전송·삭제 대상이 아니다. 삭제한 정적 파일을 서버에서 자동 정리하는 기능은 없으며 불필요한 파일은 별도로 검토해 정리한다.

## 실패 시

- SSH 인증 실패: 공개 키가 hjk 사용자에 등록됐는지, Secret이 개인 키 전체인지 확인.
- 호스트 검사 실패: 관리자의 SSH 지문과 AD_KNOWN_HOSTS 확인.
- `.venv/bin/python` 오류: 수동 배포 매뉴얼의 서버 가상환경 생성 단계 실행.
- API 401/403: API 토큰·권한·계정 확인. 404: 사이트 ID 확인.
- 홈페이지 검사 실패: 관리자 사이트 로그 확인. 검사는 HTTP 성공과 제목 문자열만 확인하므로 글 등록·재시작 후 저장 보존도 직접 확인.

이 예시의 YAML·원격 명령은 공식 문서에 맞춰 작성했지만 실제 Secrets와 계정으로 GitHub Actions를 실행 검증하지 않았다.

## 무료 범위와 공식 출처

GitHub 공식 가격표는 Free 계정에 월 2,000 CI/CD분을 제공하고 공개 저장소의 표준 runner 실행은 무료라고 안내한다. private 저장소는 계정의 사용량·결제 설정을 확인한다. 예시는 표준 Ubuntu runner, 변경 경로 제한, 실행당 10분 제한을 사용하고 artifact/cache 업로드를 추가하지 않는다. 월 총사용량을 이 설정만으로 보장하지는 않는다.

- [GitHub Actions Secrets 설정](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [GitHub 요금](https://github.com/pricing)
- [공식 checkout action](https://github.com/actions/checkout)
- [alwaysdata SSH 공개 키 등록](https://help.alwaysdata.com/en/docs/web-hosting/remote-access/ssh/use-keys/)
- [alwaysdata API 재시작 예시](https://help.alwaysdata.com/en/docs/development/api/)
- [alwaysdata API 토큰](https://help.alwaysdata.com/en/docs/admin-billing/profile/tokens/)
