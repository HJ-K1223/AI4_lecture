"""실제 HTTP 요청의 동시 시작 및 서버 조회 구간을 확인합니다."""

import argparse
import asyncio
from time import perf_counter

import httpx


async def compare(client, mode, count):
    start = perf_counter()
    print(f"\n[{mode}] 상품 {count}개 동시 요청", flush=True)

    async def request_one(product_id):
        sent = perf_counter()
        print(f"  시작 상품 {product_id}: +{(sent - start) * 1000:.1f}ms", flush=True)
        response = await client.get(f"/api/stock/{mode}/{product_id}")
        response.raise_for_status()
        data = response.json()
        print(f"  완료 상품 {product_id}: HTTP {response.status_code}, "
              f"{perf_counter() - sent:.3f}s, 조회 스레드={data['lookup_thread']}", flush=True)
        assert data["product"]["id"] == product_id
        return data

    async def health():
        await asyncio.sleep(0.3)
        sent = perf_counter()
        response = await client.get("/health")
        response.raise_for_status()
        return perf_counter() - sent

    # 세 코루틴을 한 번에 예약합니다. /health 작업도 같은 클라이언트 이벤트 루프에서 진행합니다.
    health_task = asyncio.create_task(health())
    try:
        data = await asyncio.gather(*(request_one(i) for i in range(1, count + 1)))
        total = perf_counter() - start
        health_time = await health_task
    finally:
        if not health_task.done():
            health_task.cancel()
        await asyncio.gather(health_task, return_exceptions=True)
    origin = min(item["lookup_started"] for item in data)
    for item in data:
        print(f"  서버 조회 구간 상품 {item['product']['id']}: "
              f"+{item['lookup_started'] - origin:.3f}s ~ "
              f"+{item['lookup_finished'] - origin:.3f}s; "
              f"엔드포인트 스레드={item['endpoint_thread']}")
    print(f"  상품 전체 완료 {total:.3f}s / health 응답 {health_time:.3f}s")


async def main(args):
    async with httpx.AsyncClient(base_url=args.url, timeout=20.0, trust_env=False) as client:
        for mode in (["bad", "good", "thread"] if args.mode == "all" else [args.mode]):
            await compare(client, mode, args.count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--mode", choices=["all", "bad", "good", "thread"], default="all")
    parser.add_argument("--count", type=int, choices=[1, 3], default=3)
    try:
        asyncio.run(main(parser.parse_args()))
    except httpx.HTTPError as error:
        parser.exit(1, f"요청 실패: {error}\n서버 주소와 실행 상태를 확인하세요.\n")
