# Supabase: public에서 shoppingmall로 변경

스키마 이름은 공백 없는 **`shoppingmall`**입니다. 전체 테이블명은 `shoppingmall.members`처럼 사용합니다. 이 문서는 실행 안내이며, 에이전트가 원격 DB를 변경하지는 않았습니다.

## 어떤 파일을 실행하나요?

- **빈 테이블을 지우고 다시 만들려면 방법 A**: `drop_public_shop.sql` → `schema.sql`
- **기존 데이터를 유지하려면 방법 B (권장)**: `migrate_public_to_shoppingmall.sql`만 실행
- **아직 테이블을 만들지 않았다면**: `schema.sql`만 실행

A와 B는 대안입니다. 둘 다 실행하지 마세요. 작업 중에는 애플리케이션 쓰기 요청을 멈추고, 보관할 데이터가 있다면 먼저 백업하세요. `public` 스키마 자체는 다른 서비스에서도 사용할 수 있으므로 삭제하지 않습니다.

## 먼저 현재 위치 확인

Supabase 프로젝트의 **SQL Editor**에서 새 쿼리를 열고 아래 SQL을 실행합니다. 테이블 소유자 권한이 있는 역할(기본 프로젝트에서는 일반적으로 `postgres`)을 사용합니다.

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('public', 'shoppingmall')
  AND table_type = 'BASE TABLE'
  AND table_name IN (
    'members', 'products', 'orders', 'order_items', 'payments', 'cart_merge_receipts'
  )
ORDER BY table_schema, table_name;
```

이미 두 스키마에 같은 테이블이 모두 있다면 실행을 멈추고 어느 쪽 데이터가 기준인지 먼저 확인합니다. 이전 SQL은 기존 대상 테이블을 덮어쓰거나 데이터를 병합하지 않습니다.

## 방법 A — public의 빈 테이블 삭제 후 재생성

1. SQL Editor의 새 쿼리에 [drop_public_shop.sql](../db/drop_public_shop.sql) 전체 내용을 붙여 넣고 실행합니다.
2. 쇼핑몰 테이블과 갱신 트리거 함수만 제거됩니다. 데이터가 1행이라도 있으면 삭제를 중단하고, 트랜잭션 전체를 롤백합니다. 해당 데이터가 있다면 방법 B를 사용하세요.
3. 성공하면 다른 새 쿼리에 [schema.sql](../db/schema.sql) 전체 내용을 붙여 넣고 실행합니다.
4. `shoppingmall` 스키마와 5개 테이블·FK·인덱스·트리거·RLS가 생성됩니다.
5. 아래 완료 확인 SQL을 실행합니다.

삭제 SQL은 자식 테이블부터 지우고 `CASCADE`는 사용하지 않습니다. 다른 객체가 참조하면 실패하며, 그 의존성을 확인한 뒤 처리해야 합니다. 이 프로젝트의 이름과 같은 다른 용도의 테이블이 있다면 해당 SQL을 실행하지 마세요.

## 방법 B — 데이터 보존 이전

1. `shoppingmall`에 신규 생성용 `schema.sql`을 먼저 실행하지 마세요.
2. SQL Editor의 새 쿼리에 [migrate_public_to_shoppingmall.sql](../db/migrate_public_to_shoppingmall.sql) 전체 내용을 붙여 넣고 실행합니다.
3. 기존 행·ID를 유지하며 5개 테이블과 갱신 함수의 위치를 옮깁니다. 성공하면 해당 객체는 `public`에 남지 않습니다.
4. 초기 6개 테이블 버전의 `cart_merge_receipts`가 있으면 데이터 보호를 위해 함께 옮깁니다. 현재 최소 설계에서는 사용하지 않는 이전 버전 객체입니다. 없다면 건너뜁니다.
5. 아래 완료 확인 SQL을 실행합니다. **이전 성공 후 `schema.sql`을 다시 실행하지 않습니다.**

PostgreSQL의 `SET SCHEMA`는 테이블의 인덱스·제약조건도 함께 이동합니다. 기존 FK와 트리거의 객체 참조는 유지하며, 사용자 정의 갱신 함수는 별도로 이동하도록 작성했습니다. [PostgreSQL 공식 문서](https://www.postgresql.org/docs/current/sql-altertable.html)

이전 SQL은 기존 5개 테이블과 `public.set_shop_updated_at()` 함수가 모두 있는 상태를 전제로 합니다. 누락·대상 이름 충돌·권한 오류가 있으면 전체 이전을 취소합니다. 실패 후 SQL Editor에 트랜잭션 중단 오류가 계속 나오면 `ROLLBACK;`을 실행한 뒤 원인을 확인합니다.

## 완료 확인

처음의 위치 확인 SQL을 다시 실행합니다. 현재 버전의 경우 결과에 `shoppingmall` 테이블 5개가 있고, 해당 5개 테이블의 `public` 행은 없어야 합니다.

이어서 실제 데이터 수를 확인합니다.

```sql
SELECT 'members' AS table_name, count(*) AS row_count FROM shoppingmall.members
UNION ALL SELECT 'products', count(*) FROM shoppingmall.products
UNION ALL SELECT 'orders', count(*) FROM shoppingmall.orders
UNION ALL SELECT 'order_items', count(*) FROM shoppingmall.order_items
UNION ALL SELECT 'payments', count(*) FROM shoppingmall.payments;
```

방법 A라면 모두 0, 방법 B라면 이전 전 데이터 수와 일치해야 합니다. Supabase Table Editor에서 스키마 선택을 `shoppingmall`로 바꾸어 확인할 수도 있습니다. 목록이 갱신되지 않으면 화면을 새로고침하세요.

## 이후 FastAPI 연결

- DB 호스트·포트·DB 이름은 그대로입니다. PostgreSQL 스키마는 별도 데이터베이스가 아니므로 연결 URL의 DB 이름을 `shoppingmall`로 바꾸지 않습니다.
- 이후 SQLAlchemy 모델에 스키마를 `shoppingmall`로 명시하고 FK도 `shoppingmall.members.id`처럼 지정합니다. SQL에서도 전체 이름을 사용해 `search_path` 의존을 줄입니다.
- 서버는 해당 스키마에 접근 가능한 테이블 소유자 또는 서버 전용 DB 역할로 접속합니다. 별도 역할을 만들 경우 스키마 USAGE와 필요한 테이블 권한, RLS 적용 방식을 함께 설정해야 합니다.
- 현재 구조는 서버가 PostgreSQL에 직접 연결합니다. Supabase Data API의 **Exposed schemas에 shoppingmall을 추가할 필요가 없습니다.** 브라우저에 직접 노출하지 않고 익명·일반 인증 역할의 접근 권한을 회수합니다. 커스텀 스키마를 Data API에 노출하는 절차는 별도 설정입니다. [Supabase 공식 문서](https://supabase.com/docs/guides/api/using-custom-schemas)
- SQL의 `FROM PUBLIC`에서 대문자 `PUBLIC`은 모든 역할을 뜻하는 권한 대상입니다. 소문자 `public.` 스키마 참조와 달라서 변경하지 않았습니다.

실제 Supabase 적용은 사용자가 위 방법 중 하나를 선택해 수행합니다. 다음 지시까지 애플리케이션 구현은 진행하지 않습니다.
