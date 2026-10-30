-- 단계 1 제안: Supabase SQL Editor에서 신규 테이블 생성 시 실행합니다.
-- 기존 테이블을 삭제하거나 덮어쓰지 않습니다. 재실행용 마이그레이션은 아닙니다.
BEGIN;

CREATE SCHEMA IF NOT EXISTS shoppingmall;
REVOKE ALL ON SCHEMA shoppingmall FROM PUBLIC, anon, authenticated;

CREATE TABLE shoppingmall.members (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email varchar(254) NOT NULL UNIQUE,
    password_hash text NOT NULL,
    name varchar(80) NOT NULL,
    phone varchar(30),
    address varchar(500),
    status varchar(10) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'WITHDRAWN')),
    auth_version integer NOT NULL DEFAULT 1 CHECK (auth_version > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT members_email_normalized CHECK (email = lower(btrim(email))),
    CONSTRAINT members_name_nonempty CHECK (length(btrim(name)) > 0),
    CONSTRAINT members_deleted_state CHECK (
        (status = 'ACTIVE' AND deleted_at IS NULL) OR
        (status = 'WITHDRAWN' AND deleted_at IS NOT NULL)
    )
);

CREATE TABLE shoppingmall.products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sku varchar(50) NOT NULL UNIQUE,
    name varchar(150) NOT NULL CHECK (length(btrim(name)) > 0),
    description text NOT NULL DEFAULT '',
    price bigint NOT NULL CHECK (price >= 0),
    stock integer NOT NULL DEFAULT 0 CHECK (stock >= 0),
    image_path varchar(500),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE shoppingmall.orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id uuid NOT NULL REFERENCES shoppingmall.members(id) ON DELETE RESTRICT,
    status varchar(10) NOT NULL DEFAULT 'CART'
        CHECK (status IN ('CART', 'PENDING', 'PAID', 'CANCELED')),
    currency varchar(3) NOT NULL DEFAULT 'KRW' CHECK (currency = 'KRW'),
    total_amount bigint NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    recipient_name varchar(80),
    recipient_phone varchar(30),
    shipping_address varchar(500),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    ordered_at timestamptz,
    paid_at timestamptz,
    canceled_at timestamptz,
    CONSTRAINT orders_ordered_state CHECK (
        (status = 'CART' AND ordered_at IS NULL) OR
        (status IN ('PENDING', 'PAID') AND ordered_at IS NOT NULL) OR
        status = 'CANCELED'
    ),
    CONSTRAINT orders_paid_state CHECK ((status = 'PAID') = (paid_at IS NOT NULL)),
    CONSTRAINT orders_canceled_state CHECK (
        (status = 'CANCELED') = (canceled_at IS NOT NULL)
    )
);

-- 회원별 활성 장바구니는 최대 하나입니다. 동시 생성도 DB에서 차단합니다.
CREATE UNIQUE INDEX orders_one_cart_per_member
    ON shoppingmall.orders(member_id) WHERE status = 'CART';
CREATE INDEX orders_member_history_idx
    ON shoppingmall.orders(member_id, ordered_at DESC, id DESC) WHERE status <> 'CART';

-- 주문과 상품의 N:M 관계를 해소하고, 주문 시점의 상품명과 가격을 보존합니다.
CREATE TABLE shoppingmall.order_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid NOT NULL REFERENCES shoppingmall.orders(id) ON DELETE RESTRICT,
    product_id uuid NOT NULL REFERENCES shoppingmall.products(id) ON DELETE RESTRICT,
    product_name varchar(150) NOT NULL CHECK (length(btrim(product_name)) > 0),
    unit_price bigint NOT NULL CHECK (unit_price >= 0),
    quantity integer NOT NULL CHECK (quantity BETWEEN 1 AND 99),
    line_total bigint GENERATED ALWAYS AS (unit_price * quantity) STORED,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (order_id, product_id)
);
CREATE INDEX order_items_product_idx ON shoppingmall.order_items(product_id);

-- 결제 시도는 주문당 여러 번 가능하지만 성공은 최대 한 번만 허용합니다.
CREATE TABLE shoppingmall.payments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid NOT NULL REFERENCES shoppingmall.orders(id) ON DELETE RESTRICT,
    provider varchar(30) NOT NULL DEFAULT 'MOCK',
    method varchar(30) NOT NULL DEFAULT 'MOCK_CARD',
    status varchar(10) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'SUCCEEDED', 'FAILED')),
    amount bigint NOT NULL CHECK (amount >= 0),
    currency varchar(3) NOT NULL DEFAULT 'KRW' CHECK (currency = 'KRW'),
    idempotency_key uuid NOT NULL UNIQUE,
    transaction_id varchar(150),
    failure_code varchar(50),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    paid_at timestamptz,
    CONSTRAINT payments_transaction_unique UNIQUE (provider, transaction_id),
    CONSTRAINT payments_success_state CHECK (
        (status = 'SUCCEEDED' AND paid_at IS NOT NULL AND transaction_id IS NOT NULL) OR
        (status <> 'SUCCEEDED' AND paid_at IS NULL)
    )
);
CREATE UNIQUE INDEX payments_one_success_per_order
    ON shoppingmall.payments(order_id) WHERE status = 'SUCCEEDED';
CREATE INDEX payments_order_created_idx ON shoppingmall.payments(order_id, created_at DESC);
CREATE INDEX products_catalog_idx
    ON shoppingmall.products(created_at DESC, id DESC) WHERE is_active;

CREATE FUNCTION shoppingmall.set_shop_updated_at()
RETURNS trigger LANGUAGE plpgsql SET search_path = '' AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER members_updated_at BEFORE UPDATE ON shoppingmall.members
    FOR EACH ROW EXECUTE FUNCTION shoppingmall.set_shop_updated_at();
CREATE TRIGGER products_updated_at BEFORE UPDATE ON shoppingmall.products
    FOR EACH ROW EXECUTE FUNCTION shoppingmall.set_shop_updated_at();
CREATE TRIGGER orders_updated_at BEFORE UPDATE ON shoppingmall.orders
    FOR EACH ROW EXECUTE FUNCTION shoppingmall.set_shop_updated_at();
CREATE TRIGGER order_items_updated_at BEFORE UPDATE ON shoppingmall.order_items
    FOR EACH ROW EXECUTE FUNCTION shoppingmall.set_shop_updated_at();
CREATE TRIGGER payments_updated_at BEFORE UPDATE ON shoppingmall.payments
    FOR EACH ROW EXECUTE FUNCTION shoppingmall.set_shop_updated_at();

-- 브라우저의 Supabase Data API 직접 접근은 허용하지 않습니다.
-- 서버의 DATABASE_URL은 테이블 소유자 또는 적절한 서버 전용 역할을 사용합니다.
ALTER TABLE shoppingmall.members ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoppingmall.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoppingmall.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoppingmall.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoppingmall.payments ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE shoppingmall.members, shoppingmall.products, shoppingmall.orders,
    shoppingmall.order_items, shoppingmall.payments
    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION shoppingmall.set_shop_updated_at() FROM PUBLIC;

COMMIT;

