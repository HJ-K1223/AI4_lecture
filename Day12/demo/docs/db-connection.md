# Supabase 연결 확인 결과

2026-10-29, 사용자의 요청에 따라 로컬 `.env`를 사용해 실제 연결을 확인했습니다.

## 결과

- Supabase PostgreSQL TLS 연결 성공
- shoppingmall.members, products, orders, order_items, payments의 읽기 권한 확인
- 검사 쿼리는 SELECT 1과 각 테이블의 SELECT id ... LIMIT 0만 실행
- 실제 회원·상품 데이터는 가져오거나 출력하지 않음
- 데이터·스키마·권한 변경 없음
- `.env` 수정 없음, 비밀값 출력 없음
- 설정 검증 및 기존 기반 테스트 총 9개 통과

## 변경 파일

- `app/core/config.py`: DATABASE_URL에 더해 기존 host·port·dbname·user·password 설정을 지원합니다. 비밀번호는 메모리에서 안전하게 URL 인코딩하며 TLS를 요구합니다.
- `tests/test_foundation.py`: 예약문자가 포함된 비밀번호 처리와 불완전한 분리 설정 거부를 검증합니다.
- `.env.example`: 분리 설정 예시를 추가했습니다. 실제 비밀값은 없습니다.
- `README.md`, `docs/stage2.md`, `docs/plan.md`: 실제 연결 성공과 현재 진행 상태를 반영했습니다.

## 다시 확인하는 명령

프로젝트 폴더의 PowerShell에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m app.core.check_db
```

성공 메시지: `DB 확인 완료: shoppingmall의 필수 테이블 5개를 읽을 수 있습니다.`

현재 연결을 위해 사용자가 추가로 해야 할 설정은 없습니다. 이 최초 연결 검사는 읽기 전용입니다. 이후 진행한 가입·로그인·로그아웃 통합 검증은 [단계 3 결과](stage3.md)에 정리했습니다. 구매 트랜잭션은 이후 기능 구현 단계에서 확인합니다.
