# 무료 호스팅 비교와 추천

조사 기준일: 2026-10-23(한국 시간). 각 서비스의 공식 문서를 직접 확인했다. 일반적인 무료 플랜과 FastAPI·로컬 SQLite를 함께 사용할 수 있는지를 구분했다. 계정을 만들거나 실제 배포하지는 않았다.

## 비교표

| 서비스 | 현재 무료 범위·조건 | 장점 | 단점·SQLite 제약 | 이 방명록에 대한 판단 |
| --- | --- | --- | --- | --- |
| alwaysdata | Free: 디스크 1 GB, RAM 256 MB, CPU 1/4. 비영리 용도 및 계정의 alwaysdata.net 주소로 제한 | ASGI 웹 앱을 User program으로 실행 가능. 계정 파일공간과 SSH 제공. 외부 DB 없이 구성 가능 | 초기 SSH·가상환경 설정 필요. 작은 메모리와 계정 전체 디스크 한도. 별도 Advanced > Services 기능은 유료 | **학습·비영리 방명록에 가장 적합**. 계정 파일공간에 SQLite를 두는 구성 권장 |
| PythonAnywhere | 무료 계정: 디스크 512 MiB, 웹 앱 1개/worker 1개, 웹 앱 1개월 만료 조건 | Python 중심 환경, SQLite 사용 가능 | ASGI는 실험 기능이고 장기 가격 미확정. 일반 무료 웹 앱 조건을 FastAPI에 그대로 적용하면 안 됨 | 차선 후보. 무료 ASGI 사용 가능 여부·갱신 조건을 계정에서 확인해야 함 |
| Render | 무료 웹 서비스, 월 750시간을 workspace에서 공유 | 무료 웹 앱 배포와 관리형 HTTPS 지원 | 15분 무접속 시 정지. 재시작·재배포·정지 시 로컬 SQLite 데이터 소실. 무료 영구 디스크 없음 | 데이터 초기화를 허용한 시연용 |
| Koyeb | 조직당 무료 instance 1개: RAM 512 MB, CPU 0.1, SSD 2 GB | 작은 웹 앱 실행에 충분한 무료 계산 자원 | 무료 instance에 영구 Volume 연결 불가. 1시간 무접속 시 scale-to-zero. SSD 용량 표기는 데이터 보존 보장이 아님 | SQLite 지속 저장이 필요한 방명록에는 비추천 |
| Hugging Face Spaces | 정적 Space는 무료. 현재 신규 Docker/Gradio Space 생성은 유료 플랜 필요(개인 무료 ZeroGPU Gradio 예외는 별도) | 정적 페이지·ML 데모 공유 기능 | 현재 앱에 필요한 Docker 방식은 신규 무료 계정의 일반 무료 배포 대상이 아님. 기본 로컬 디스크도 비영구 | 현재 조건에서 제외 |

서비스별 근거: [alwaysdata 무료 사양·조건](https://help.alwaysdata.com/en/docs/admin-billing/billing/public-cloud-prices/), [alwaysdata ASGI 구성](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/), [PythonAnywhere 무료 계정](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/), [PythonAnywhere SQLite](https://help.pythonanywhere.com/pages/KindsOfDatabases), [PythonAnywhere ASGI](https://help.pythonanywhere.com/pages/ASGICommandLine), [Render 무료 플랜](https://render.com/docs/free), [Koyeb instance](https://www.koyeb.com/docs/reference/instances), [Koyeb Volume 제한](https://www.koyeb.com/docs/reference/volumes), [Hugging Face 현재 Space 생성 조건](https://huggingface.co/docs/hub/en/spaces-overview).

## 추천 이유와 한계

**현재 앱을 비영리 학습 목적으로 배포한다면 alwaysdata를 추천한다.** 이는 공식 문서의 무료 사양·파일 호스팅·ASGI 실행 지원을 현재 코드의 요구사항에 대조한 판단이다. SQLite의 실제 동작·재시작 후 보존은 해당 계정에 배포한 뒤 최종 확인해야 한다.

현재 앱은 서버 렌더링 HTML, 단일 SQLite 파일, Uvicorn worker 1개만 필요하다. 따라서 Docker, 외부 DB, 새 프레임워크, 별도 배포 CLI를 도입하지 않아도 된다. 코드 수정 없이 DB 경로와 실행 명령을 설정하면 된다. 256 MB RAM이 충분할 가능성은 높지만, 이는 현재 앱 구조에 따른 예상이며 호스팅에서 부하 시험한 결과는 아니다.

계정 파일공간은 프로세스의 임시 컨테이너 디스크와 다른 방식으로 제공되며, 파일 백업도 제공된다. [alwaysdata 백업 문서](https://help.alwaysdata.com/en/docs/web-hosting/backups/)는 매일 파일 등을 백업하고 무료 플랜에서 3일간 보관한다고 안내한다. 백업은 최근 글 전체의 무손실 보장을 의미하지 않는다.

무료 플랜의 Advanced > Services 금지와 Web > Sites의 User program 웹 사이트는 구분한다. 방명록은 후자로 등록한다. [웹 사이트 실행 방식](https://help.alwaysdata.com/en/docs/web-hosting/sites/http-servers/user-program/), [유료 Services 기능](https://help.alwaysdata.com/en/docs/web-hosting/services/).

기존 DEPLOYMENT.md의 “지속 보존할 무료 후보를 확정하지 못했다”는 내용은 이번 추가 조사로 갱신했다. 배포 절차는 [DEPLOYMENT.md](DEPLOYMENT.md)에 기록했다. 영리·상업적 운영을 계획한다면 alwaysdata Free 추천 조건이 달라진다.
