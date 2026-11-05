-- 데이터가 있는 테이블은 삭제하지 않습니다.
-- public에 있는 이 프로젝트의 지정 테이블만 대상으로 합니다.
BEGIN;

-- 비어 있는 테이블만 삭제합니다. 데이터가 하나라도 있으면 전체 중단합니다.
-- 식별자는 고정된 목록에서만 가져오고 format의 %I로 인용합니다.
DO $$
DECLARE
    shop_table text;
    has_rows boolean;
BEGIN
    FOREACH shop_table IN ARRAY ARRAY[
        'members', 'products', 'orders', 'order_items', 'payments', 'cart_merge_receipts'
    ] LOOP
        IF to_regclass(format('public.%I', shop_table)) IS NOT NULL THEN
            EXECUTE format('LOCK TABLE public.%I IN ACCESS EXCLUSIVE MODE', shop_table);
            EXECUTE format('SELECT EXISTS (SELECT 1 FROM public.%I)', shop_table) INTO has_rows;
            IF has_rows THEN
                RAISE EXCEPTION 'public.%에 데이터가 있습니다. 삭제 대신 이전 SQL을 사용하세요.', shop_table;
            END IF;
        END IF;
    END LOOP;
END;
$$;

-- 의존하는 테이블부터 제거합니다. CASCADE는 사용하지 않습니다.
DROP TABLE IF EXISTS public.cart_merge_receipts RESTRICT;
DROP TABLE IF EXISTS public.payments RESTRICT;
DROP TABLE IF EXISTS public.order_items RESTRICT;
DROP TABLE IF EXISTS public.orders RESTRICT;
DROP TABLE IF EXISTS public.products RESTRICT;
DROP TABLE IF EXISTS public.members RESTRICT;
DROP FUNCTION IF EXISTS public.set_shop_updated_at() RESTRICT;

COMMIT;
