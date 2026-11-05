# FastAPI에서 Supabase PostgreSQL과 Redis의 응답 확인
import os
import psycopg
from redis import Redis, RedisError

# .env http json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field

# 환경변수
load_dotenv(override=True)
DB_URL = os.getenv("SUPABASE_DB_URL")
REDIS_URL = os.getenv("REDIS_URL")

# 환경변수 값 체크
if not DB_URL:
    raise RuntimeError("SUPABASE_DB_URL 설정 확인 필요")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL 설정 확인 필요")

# Backend FastAPI
app = FastAPI()

# API 동작 확인
@app.get("/health")
def health():
    checks = {'supabase': 'down', 'redis': 'down'}
    try:
        with psycopg.connect(
            DB_URL,
            connect_timeout = 5,
            sslmode = "require",
        ) as conn:
            with conn.cursor() as cur: # SQL 실행과 결과
                cur.execute("SELECT 1 as ok") # ok 열에 1 반환
                row =cur.fetchone() # 기본 반환형은 튜플
                if row == (1,):
                    checks['supabase'] = 'up'
    except psycopg.Error:
        pass

    try:
        with Redis.from_url(
            REDIS_URL,
            socket_connect_timeout = 3,
            socket_timeout = 3,
        ) as client:
            if client.ping():
                checks['redis'] = 'up'
    except (RedisError, ValueError):
        pass

    ready = all( value == 'up'for value in checks.values() ) # 튜플
    return JSONResponse(
        status_code = 200 if ready else 503,
        content = {'ready':ready, 'check':checks}
    )

# python -m uvicorn Day15.main1:app --host 127.0.0.1 --port 8000 --reload

# Pydantic 타입 검사
class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title : str = Field(min_length=1, max_length=100)

class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content : str = Field(min_length=1, max_length=1000)

from psycopg.rows import dict_row # 컬럼을 딕셔너리 행으로 받는다
def connect_db():
    # 호출한 쪽의 with 블록에서 정상:commit / 예외:rollback / 연결종료 담당
    return psycopg.connect(
        DB_URL,
        connect_timeout = 5,
        sslmode = 'require', # 원격 db에 암호를 요구
        row_factory = dict_row # 기본 튜플 대신 {컬럼:값} 형태로 읽음
    )

# 데이터베이스 생성
def init_db():
    with connect_db() as conn:
        conn.execute("create schema if not exists kdt_hybrid")
        conn.execute('''
            create table if not exists kdt_hybrid.conversation(
            id uuid primary key,
            title varchar(100) not null check(length(trim(title))>0),
            created_at timestamptz not null default current_timestamp
            )
        ''')
        conn.execute('''
            create table if not exists kdt_hybrid.messages(
            id bigint generated always as identity primary key,
            conversation_id uuid not null
                references kdt_hybrid.conversation(id),
            content varchar(1000) not null check(length(trim(content))>0),
            created_at timestamptz not null default current_timestamp
            )
        ''')
    print('테이블 준비 완료')

# 예외 발생 시 http 응답을 정함
@app.exception_handler(psycopg.Error)
def database_error(_request,_exc):
    # FastAPI가 전달하는 요청/예외는 여기서 출력하지 않음
    # 모든 오류를 잡지 않는다
    return JSONResponse(
        status_code = 503, # 서비스 이용 불가 (내부 오류)
        content = {'detail':'db 처리에 실패했습니다. 연결 정보와 테이블 상태를 확인하세요.'}

    )

# 글 등록
@app.post("/conversation", status_code = 201)
def create_convesation(body:ConversationCreate):
    conversation_id = uuid4() # conv0001
    with connect_db() as conn:
        row = conn.execute('''
            insert into kdt_hybrid.conversation(id,title)
            values(%s, %s) returning id, title,created_at
        ''',
        (conversation_id,body.title),
        ).fetchone() # returning이 돌려준 행 하나를 읽음
        return row

# 글 조회 -> 전체 데이터 반환 구조이므로 소량 데이터일때만 사용 및 테스트
# 대량의 데이터를 잘못 조회 시 DB가 죽고 Lock이 걸림 -> 조회는 가능하지만 다른 작업 불가
@app.get('/conversation')
def list_conversation():
    with connect_db() as conn:
        row = conn.execute('''
            select id, title, created_at from kdt_hybrid.conversation
            order by created_at, id
        ''').fetchall()
        return row

# 메시지 생성
@app.post('/conversation/{conversation_id}/messages',status_code=201)
def create_messages(conversation_id:UUID, body:MessageCreate):
    with connect_db() as conn:
        found = conn.execute('''
            select id from kdt_hybrid.conversation where id = %s 
        ''',
        (conversation_id,)).fetchone()
        if found is None:
            raise HTTPException(status_code=404, detail="대화방을 찾을 수 없습니다.")
        row = conn.execute('''
            insert into kdt_hybrid.messages(conversation_id, content)
            values(%s, %s) returning id, conversation_id, created_at
        ''',
        (conversation_id, body.content),
        ).fetchone()
        return row

@app.get('/conversation/{conversation_id}/messages')
def list_messages(conversation_id:UUID):
    with connect_db() as conn:
        rows = conn.execute('''
            select id, conversation_id, content, created_at
            from kdt_hybrid.messages where conversation_id = %s
            order by id
        ''',
        (conversation_id,)).fetchall()
        return rows