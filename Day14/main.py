import os
import time
import uuid

import redis
from dotenv import load_dotenv

load_dotenv()

host = os.getenv('REDIS_HOST')
port_text = os.getenv('REDIS_PORT')
port = int(port_text)

key = f'Day14:message:{uuid.uuid4().hex}' # 매번 실행할때마다 다른 키를 생성
with redis.Redis(
    host = host,
    port = port,
    decode_responses = True, # bytes 대신 str로 반환
    socket_connect_timeout = 2, # 연결 설정 2초 제한
    socket_timeout = 2 # 읽기, 쓰기 제한 2초
)as client:
    print(f'PING : {client.ping()}')
    client.set(key, "Redis 연결 성공")
    print(f'저장 후 GET : {client.get(key)}')
    print(f'TTL : {client.ttl(key)}')

    client.set(key, "잠시 보관할 메시지", ex=2) # 2초 후 만료
    print(f'저장 후 GET : {client.get(key)}')
    print(f'TTL : {client.ttl(key)}')

    time.sleep(3)
    print(f'만료 후 GET : {client.get(key)}')
    print(f'TTL : {client.ttl(key)}')

    client.set(key, "삭제할 메시지", ex=30) # ex=30은 비정상 종료시 잔여키를 줄이는 목적
    print(f'DELETE 개수 : {client.delete(key)}')
    print(f'삭제 후 GET : {client.get(key)}')
