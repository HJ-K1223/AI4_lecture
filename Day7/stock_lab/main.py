"""쇼핑몰 재고 조회로 배우는 동기 / 비동기. 단일 worker로 실행하세요."""

import asyncio
import logging
import threading
from pathlib import Path
from time import perf_counter, sleep
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DELAY_SECONDS = 2.0
PRODUCTS = {
    1: {"id": 1, "name": "데일리 머그", "price": 18000, "stock": 24},
    2: {"id": 2, "name": "포켓 노트", "price": 8500, "stock": 12},
    3: {"id": 3, "name": "캔버스 백", "price": 24000, "stock": 7},
}
app = FastAPI(title="재고 조회 실험실", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
logger = logging.getLogger("uvicorn.error")


def thread_info():
    return {"name": threading.current_thread().name, "id": threading.get_ident()}


def legacy_lookup(product_id: int):
    """기존 동기 재고 라이브러리의 I/O 대기를 흉내냅니다. 실제 DB 연결은 아닙니다."""
    started = perf_counter()
    worker = thread_info()
    logger.info("lookup start product=%s thread=%s", product_id, worker)
    sleep(DELAY_SECONDS)  # 이 함수를 호출한 스레드를 멈춥니다.
    finished = perf_counter()
    logger.info("lookup end product=%s thread=%s", product_id, worker)
    return {"product": PRODUCTS[product_id], "lookup_started": started,
            "lookup_finished": finished, "lookup_thread": worker}


async def async_lookup(product_id: int):
    """비동기 재고 라이브러리의 I/O 대기를 흉내냅니다."""
    started = perf_counter()
    worker = thread_info()
    logger.info("lookup start product=%s thread=%s", product_id, worker)
    await asyncio.sleep(DELAY_SECONDS)  # 대기 중 이벤트 루프에 제어권을 양보합니다.
    finished = perf_counter()
    logger.info("lookup end product=%s thread=%s", product_id, worker)
    return {"product": PRODUCTS[product_id], "lookup_started": started,
            "lookup_finished": finished, "lookup_thread": worker}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health():
    """다른 요청을 처리할 여유가 있는지 확인하는 가벼운 API."""
    return {"status": "ok", "thread": thread_info()}


@app.get("/api/stock/{mode}/{product_id}")
async def stock(mode: Literal["bad", "good", "thread"], product_id: int):
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="없는 상품입니다.")
    endpoint_thread = thread_info()
    if mode == "bad":
        result = legacy_lookup(product_id)  # 이벤트 루프 스레드에서 직접 실행 → 정지
    elif mode == "good":
        result = await async_lookup(product_id)  # 같은 스레드지만 대기 중 양보
    else:
        result = await asyncio.to_thread(legacy_lookup, product_id)  # 별도 스레드
    return {"mode": mode, "endpoint_thread": endpoint_thread,
            "delay_seconds": DELAY_SECONDS, **result}
