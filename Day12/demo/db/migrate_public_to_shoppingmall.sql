-- 기존 public의 쇼핑몰 데이터를 보존하면서 위치를 옮깁니다.
-- schema.sql을 shoppingmall에 먼저 실행하지 마세요. 한 번만 실행합니다.
BEGIN;

CREATE SCHEMA IF NOT EXISTS shoppingmall;
REVOKE ALL ON SCHEMA shoppingmall FROM PUBLIC, anon, authenticated;

ALTER TABLE public.members SET SCHEMA shoppingmall;
ALTER TABLE public.products SET SCHEMA shoppingmall;
ALTER TABLE public.orders SET SCHEMA shoppingmall;
ALTER TABLE public.order_items SET SCHEMA shoppingmall;
ALTER TABLE public.payments SET SCHEMA shoppingmall;
ALTER FUNCTION public.set_shop_updated_at() SET SCHEMA shoppingmall;

-- 초기 6개 테이블 버전을 실행한 경우에만 기술용 테이블도 보존하여 옮깁니다.
DO $$
BEGIN
    IF to_regclass('public.cart_merge_receipts') IS NOT NULL THEN
        ALTER TABLE public.cart_merge_receipts SET SCHEMA shoppingmall;
        ALTER TABLE shoppingmall.cart_merge_receipts ENABLE ROW LEVEL SECURITY;
        REVOKE ALL ON TABLE shoppingmall.cart_merge_receipts FROM PUBLIC, anon, authenticated;
    END IF;
END;
$$;

ALTER TABLE shoppingmall.members ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoppingmall.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoppingmall.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoppingmall.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoppingmall.payments ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE shoppingmall.members, shoppingmall.products,
    shoppingmall.orders, shoppingmall.order_items, shoppingmall.payments
    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION shoppingmall.set_shop_updated_at() FROM PUBLIC;

COMMIT;
