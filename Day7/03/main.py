from fastapi import FastAPI, HTTPException
import httpx
import os

app = FastAPI()
BASE_URL = "http://127.0.0.1:9000"

@app.get('/health')
async def health():
    return {'status':'ok'}

import asyncio
from time import perf_counter

async def fetch(client, item_id):
     response = await client.get(f'/items/{item_id}')
     response.raise_for_status # 400 or 500번대 에러가 나면 멈추게 하기 위함
     return response.json()

async def fetch_case(client, case_id):
     response = await client.get(f'/cases/{case_id}')
     response.raise_for_status # 400 or 500번대 에러가 나면 멈추게 하기 위함
     return response.json()

@app.get('/summary') # 비동기 순차 실행
async def summary():
    start = perf_counter()
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=3, trust_env=False) as client:
        items = []
        for item_id in [1, 2, 3]:
            items.append(await fetch(client, item_id))
    return {'items': items, 'elapsed': round(perf_counter() - start, 3)}

@app.get('/labels') # 비동기 병렬 실행
async def labels():
    ids = [1, 2, 3]
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=3, trust_env=False) as client:
        tasks = [fetch(client, item_id) for item_id in ids]
        completed = []
        for task in asyncio.as_completed(tasks):
            completed.append(await task)
    return [{'requested_id': item_id, 'data': data}
            for item_id, data in zip(ids, completed)]

@app.get('/case_summary') # 비동기 순차 실행
async def summary():
    start = perf_counter()
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=3, trust_env=False) as client:
        cases = []
        for case_id in [1, 2, 3]:
            cases.append(await fetch_case(client, case_id))
    return {'cases': cases, 'elapsed': round(perf_counter() - start, 3)}