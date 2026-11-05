# 테이블 정의서

단계 1 수정 제안입니다. 모든 테이블의 전체 이름은 `shoppingmall.<테이블명>`입니다. 예: `shoppingmall.members`. FK도 동일한 스키마를 참조합니다. [ERD](erd.md)와 함께 읽으세요. 실행용 정의는 [schema.sql](../db/schema.sql)입니다.

## 표 읽는 방법

- PK: 기본키, FK: 외래키, UK: 중복 불가입니다.
- 필수는 NULL 불가를 뜻합니다. 기본값이 있으면 INSERT 시 생략할 수 있습니다.
- ID는 UUID, 금액은 KRW 정수, 일시는 시간대가 있는 timestamptz입니다.
- created_at은 생성 시각, updated_at은 수정 시각입니다. 수정 시각은 트리거가 자동 갱신합니다.

## 1. members — 회원

| 컬럼 | 자료형 | 필수 | 키·기본값 | 의미 |
| --- | --- | --- | --- | --- |
| id | uuid | 예 | PK, 자동 생성 | 회원 ID |
| email | varchar(254) | 예 | UK | 소문자·앞뒤 공백 제거한 로그인 이메일 |
| password_hash | text | 예 | — | Argon2 해시, 평문 저장 금지 |
| name | varchar(80) | 예 | 공백만 입력 불가 | 이름 |
| phone | varchar(30) | 아니오 | — | 연락처 |
| address | varchar(500) | 아니오 | — | 기본 배송주소 |
| status | varchar(10) | 예 | ACTIVE | ACTIVE / WITHDRAWN |
| auth_version | integer | 예 | 1, 양수 | 기존 인증을 무효화하는 버전 |
| created_at | timestamptz | 예 | now() | 가입 시각 |
| updated_at | timestamptz | 예 | now() | 수정 시각 |
| deleted_at | timestamptz | 아니오 | — | 탈퇴 시각 |

ACTIVE면 탈퇴 시각이 없어야 하고 WITHDRAWN이면 있어야 합니다. 탈퇴 시 이메일은 `withdrawn+<UUID>@invalid.local`, 이름은 `탈퇴회원`, 전화·주소는 NULL로 바꿉니다. 비밀번호는 임의값의 해시로 교체합니다. 로그아웃·비밀번호 변경·탈퇴 시 auth_version을 올리고 모든 요청에서 회원 상태·버전을 검사합니다. 따라서 로그아웃하면 다른 브라우저의 기존 로그인도 무효화합니다. 같은 이메일 재가입은 새 회원 ID로 처리합니다.

## 2. products — 상품

| 컬럼 | 자료형 | 필수 | 키·기본값 | 의미 |
| --- | --- | --- | --- | --- |
| id | uuid | 예 | PK, 자동 생성 | 상품 ID |
| sku | varchar(50) | 예 | UK | 상품 식별 코드 |
| name | varchar(150) | 예 | 공백만 입력 불가 | 현재 상품명 |
| description | text | 예 | 빈 문자열 | 상품 설명 |
| price | bigint | 예 | 0 이상 | 현재 판매가격 |
| stock | integer | 예 | 0, 음수 불가 | 현재 재고 |
| image_path | varchar(500) | 아니오 | — | 정적 상품 이미지 경로 |
| is_active | boolean | 예 | true | 판매 여부 |
| created_at | timestamptz | 예 | now() | 등록 시각 |
| updated_at | timestamptz | 예 | now() | 수정 시각 |

판매 종료 상품은 삭제 대신 is_active=false로 바꾸어 주문 이력의 참조를 유지합니다.

## 3. orders — 장바구니·주문

| 컬럼 | 자료형 | 필수 | 키·기본값 | 의미 |
| --- | --- | --- | --- | --- |
| id | uuid | 예 | PK, 자동 생성 | 장바구니부터 결제까지 유지되는 ID |
| member_id | uuid | 예 | FK → members.id | 소유 회원 |
| status | varchar(10) | 예 | CART | CART / PENDING / PAID / CANCELED |
| currency | varchar(3) | 예 | KRW만 허용 | 통화 |
| total_amount | bigint | 예 | 0, 음수 불가 | 상품 금액 합계 |
| recipient_name | varchar(80) | 아니오 | — | 주문 시 복사한 수령인 |
| recipient_phone | varchar(30) | 아니오 | — | 주문 시 복사한 전화 |
| shipping_address | varchar(500) | 아니오 | — | 주문 시 복사한 배송주소 |
| created_at | timestamptz | 예 | now() | 장바구니 생성 시각 |
| updated_at | timestamptz | 예 | now() | 수정 시각 |
| ordered_at | timestamptz | 아니오 | — | 주문 생성 시각 |
| paid_at | timestamptz | 아니오 | — | 결제 완료 시각 |
| canceled_at | timestamptz | 아니오 | — | 미결제 취소 시각 |

- 회원당 CART는 최대 1개입니다. PENDING 전환 후 새 상품을 담으면 새로운 CART를 만듭니다.
- CART에는 주문일이 없고 PENDING / PAID에는 주문일이 있습니다. 결제일은 PAID, 취소일은 CANCELED일 때만 있습니다.
- 장바구니 합계는 참고값입니다. 주문 생성 시 현재 가격으로 다시 계산하며 가격 변경이 있으면 사용자에게 재확인받습니다.
- DB는 배송정보 NULL을 허용하지만 주문 생성 시 서비스에서 필수 입력을 검사합니다. 주문 화면은 회원 정보를 기본값으로 표시하며 입력한 배송정보를 주문에만 저장합니다. 탈퇴 시 과거 배송정보도 삭제할 수 있어야 하므로 DB에서는 NULL을 허용합니다.

## 4. order_items — 주문상품

| 컬럼 | 자료형 | 필수 | 키·기본값 | 의미 |
| --- | --- | --- | --- | --- |
| id | uuid | 예 | PK, 자동 생성 | 항목 ID |
| order_id | uuid | 예 | FK → orders.id | 소속 장바구니·주문 |
| product_id | uuid | 예 | FK → products.id | 선택 상품 |
| product_name | varchar(150) | 예 | 공백만 입력 불가 | 주문 당시 상품명 |
| unit_price | bigint | 예 | 0 이상 | 주문 당시 단가 |
| quantity | integer | 예 | 1~99 | 수량 |
| line_total | bigint | 예 | 자동 계산 | unit_price × quantity, 직접 입력 불가 |
| created_at | timestamptz | 예 | now() | 항목 생성 시각 |
| updated_at | timestamptz | 예 | now() | 수정 시각 |

(order_id, product_id)는 중복 불가입니다. 같은 상품을 다시 담으면 수량을 변경합니다. PENDING 전환 시 이름·단가를 확정하고 이후 수정하지 않습니다. 수량 0 대신 항목을 삭제합니다.

## 5. payments — 결제 시도

| 컬럼 | 자료형 | 필수 | 키·기본값 | 의미 |
| --- | --- | --- | --- | --- |
| id | uuid | 예 | PK, 자동 생성 | 결제 시도 ID |
| order_id | uuid | 예 | FK → orders.id | 결제 대상 주문 |
| provider | varchar(30) | 예 | MOCK | 결제 제공자, 향후 PG 식별용 |
| method | varchar(30) | 예 | MOCK_CARD | 결제수단 |
| status | varchar(10) | 예 | PENDING | PENDING / SUCCEEDED / FAILED |
| amount | bigint | 예 | 0 이상 | 결제 금액 |
| currency | varchar(3) | 예 | KRW만 허용 | 통화 |
| idempotency_key | uuid | 예 | UK | 동일 요청을 식별하는 재시도 키 |
| transaction_id | varchar(150) | 아니오 | provider와 묶어 UK | 모의 거래ID, 성공 시 필수 |
| failure_code | varchar(50) | 아니오 | — | 실패 사유 코드 |
| created_at | timestamptz | 예 | now() | 결제 시도 시각 |
| updated_at | timestamptz | 예 | now() | 수정 시각 |
| paid_at | timestamptz | 아니오 | — | 성공한 결제 시각 |

주문당 SUCCEEDED는 최대 1개입니다. 성공에는 거래ID와 결제일이 있어야 하고 다른 상태에는 결제일이 없습니다. 같은 요청 재전송은 회원·주문·금액·수단을 대조하여 기존 결과를 반환합니다. 실패 후 사용자가 새로 시도하면 새 키·새 행을 만듭니다. 카드번호는 받거나 저장하지 않습니다.

## 인덱스와 무결성

| 대상 | 정의 | 목적 |
| --- | --- | --- |
| 각 테이블 PK·UK | 자동 인덱스 | ID 조회·중복 방지 |
| orders | member_id, CART일 때 UNIQUE | 회원당 장바구니 1개 |
| orders | member_id, ordered_at DESC, id DESC / CART 제외 | 구매내역 조회 |
| order_items | order_id + product_id UNIQUE | 중복 상품 방지·주문별 조회 |
| order_items | product_id | 상품 FK 탐색 |
| products | created_at DESC, id DESC / 활성 상품 | 상품 목록 페이지네이션 |
| payments | order_id, SUCCEEDED일 때 UNIQUE | 중복 성공 방지 |
| payments | order_id, created_at DESC | 결제 이력 조회 |

모든 FK는 ON DELETE RESTRICT로 이력을 참조하는 행의 삭제를 막습니다. Supabase RLS를 활성화하고 anon·authenticated의 테이블 접근 권한을 회수합니다. 브라우저는 FastAPI만 호출합니다.

## 서비스에서 보장할 규칙

SQL 제약조건만으로 모든 기능이 완성되지는 않습니다. 다음은 이후 구현에서 검증합니다.

- 로그인 회원의 주문만 조회·변경합니다. 서버 DB 연결이 RLS를 우회해도 소유권 검사를 생략하지 않습니다.
- 주문 합계 = 항목 합계, 결제 금액 = 주문 합계를 검증합니다. 클라이언트 금액은 신뢰하지 않습니다.
- CART에서만 항목을 수정하고 빈 장바구니는 주문으로 전환하지 않습니다.
- 결제 성공 시 재고·결제·주문을 단일 트랜잭션으로 변경합니다. 도중 오류면 전체 롤백합니다.
- 탈퇴 시 미결제 건을 취소하고 개인정보를 지우되 구매·결제 기록은 보존합니다. 실제 운영 개인정보 보존 기간은 별도 확정합니다.
- 실제 PG 전환에는 웹훅 검증·재고 예약·보상 처리가 추가로 필요합니다. 외부 PG 호출을 긴 DB 트랜잭션에 넣지 않습니다.

