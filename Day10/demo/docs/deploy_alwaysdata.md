# alwaysdata 배포 요약

최종 확인일: 2026-10-27. 실제 배포는 아직 수행하지 않았습니다.

상세 명령과 최신 공식 출처는 [README 배포 안내](../README.md#alwaysdata-배포)를 기준으로 합니다.

1. Free 계정의 실제 한도, SSH, Python 3.13, PostgreSQL 접속 정보를 확인합니다.
2. 실행 코드/requirements/템플릿/정적 소스만 업로드하고 .runtime·로컬 venv·비밀 파일·덤프는 제외합니다.
3. 서버에서 venv를 생성하고 고정 의존성을 설치합니다.
4. 운영 .env를 새로 작성하고 chmod 600으로 보호합니다. 사이트와 SSH 명령의 환경을 일치시킵니다.
5. 기존 DB 갱신 전 백업 후 migrate, 초기 관리자/seed는 수동 실행, collectstatic과 check --deploy를 수행합니다.
6. Python WSGI에 config/wsgi.py·작업 폴더·venv·Python 버전을 등록하고 재시작합니다.
7. HTTPS, CSS, 인증, 권한, 마스킹, 재시작 후 영속성 및 메모리/디스크를 확인합니다.
8. clearsessions 예약/수동 절차와 외부 백업·복구 절차를 유지합니다.

사이트 경로는 /home/<account>/apps/note-demo, venv는 /home/<account>/venvs/note-demo를 계획값으로 사용합니다. 실제 계정명으로 교체하세요. 승인된 구현 계획의 P9(외부 실제 배포)는 계정 접근과 배포 실행 지시 후 수행할 작업으로 남아 있습니다.

