# main5.py 목적 및 코드 해설

## 1. 목적

**SQLite를 대화 이력의 원본 저장소로 사용하고, Redis를 조회 결과의 임시 캐시로 사용하는 코드**다.

Redis에 데이터가 있으면 빠르게 가져오고(**HIT**), 없으면 SQLite에서 조회해 Redis에 다시 저장한다(**MISS**). 이런 방식을 **Cache Aside(캐시 어사이드)**라고 한다. 캐시를 삭제하거나 만료시켜도 SQLite 원본이 남아 있으므로 다음 조회에서 캐시를 복원할 수 있다.

실제 LLM API 호출이나 새 대화 입력 기능은 없으며, 초기 예제 대화를 조회하는 실습이다.

## 2. 전체 조회 흐름

```text
사용자의 history 명령
        ↓
Redis에서 사용자별 캐시 조회
        ├─ 있음(HIT) → JSON을 복원하고 결과 출력
        └─ 없음(MISS) → SQLite에서 최근 메시지 조회
                            ↓
                       Redis에 60초 동안 저장
                            ↓
                         결과 출력
```

현재 코드는 HIT 여부와 관계없이 먼저 SQLite 파일의 존재를 확인하고 연결한다. HIT일 때 생략되는 것은 대화 이력을 가져오는 SQL 조회다.

## 3. 저장 구조와 설정

| 구분 | 내용 |
|---|---|
| `DEMO_USERS` | 허용된 가상 사용자: `demo-a`(민수), `demo-b`(지연) |
| `CACHE_TTL = 60` | 캐시 생성 후 60초 동안 유지. HIT 조회로는 연장하지 않는다. |
| `MAX_MESSAGES = 6` | 원본 중 최근 6개 메시지만 조회하고 캐시한다. |
| SQLite | `messages` 테이블에 사용자별 대화 원본 저장 |
| Redis 키 | `lesson05:history:demo-a` 또는 `lesson05:history:demo-b` |
| Redis 자료형 | **String**: 메시지 목록 전체를 JSON 문자열 하나로 저장 |

Redis List를 사용하는 `main4.py`와 달리, 이 코드는 Python 목록을 JSON으로 변환해 `SET`으로 저장한다.

## 4. 함수별 해설

### `read_settings()` — 연결 설정 읽기

`load_dotenv()`로 불러온 환경변수에서 `REDIS_HOST`, `REDIS_PORT`, `SQLITE_PATH`를 읽는다. 필수 설정이 없으면 `ValueError`를 발생시키고, 포트는 정수로 변환한다. 별도의 포트 범위 검사는 없다.

### `initialize(conn)` — 원본 DB 초기화

`CREATE TABLE IF NOT EXISTS`로 테이블이 없을 때 생성한다.

| 컬럼 | 역할 |
|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT`: 메시지 식별 번호 자동 생성 |
| `owner` | 메시지 소유자. 예: `demo-a` |
| `role` | `user` 또는 `assistant`만 허용 |
| `content` | 메시지 내용 |

테이블의 전체 행 수가 0일 때만 사용자 두 명의 예제 대화 총 4개를 추가한다. 기존 데이터가 있으면 초기 예제를 추가하지 않으며, 테이블을 비우거나 덮어쓰지도 않는다.

`with conn:`은 정상 종료 시 커밋하고 예외 발생 시 롤백하는 트랜잭션 문맥이다. 연결 종료는 바깥의 `closing(...)`이 담당한다.

### `read_source(conn, owner)` — SQLite 원본 조회

허용된 사용자인지 검사한 뒤, 해당 사용자의 메시지를 조회한다.

```sql
SELECT role, content FROM messages WHERE owner = ?
ORDER BY id DESC LIMIT ?
```

- `WHERE owner = ?`: 사용자별 데이터 구분
- `ORDER BY id DESC`: ID가 큰 메시지부터 조회
- `LIMIT ?`: 최대 6개 조회
- `?` 자리표시자: 값을 SQL 문자열에 직접 붙이지 않고 매개변수로 전달

조회 결과를 `role`, `content` 필드가 있는 딕셔너리 목록으로 반환한다. **현재 코드는 결과를 뒤집지 않으므로 최신 메시지가 먼저 표시된다.** 대화 순서대로 LLM에 전달하려면 최근 6개를 고른 뒤 오래된 메시지부터 정렬하는 처리가 필요하다.

### `decode_history(raw)` — 캐시 복원과 검증

`json.loads()`로 캐시 문자열을 Python 객체로 복원한다. 목록인지, 메시지가 최대 6개인지, 각 메시지의 역할과 내용이 올바른지 확인한다. 잘못된 캐시는 오류로 처리하며 자동 삭제하거나 원본에서 복원하지 않는다.

### `cache_key(owner)` — 캐시 키 생성

사용자 ID 앞에 `lesson05:history:`를 붙여 사용자별 캐시를 구분한다.

### `load_history(conn, client, owner)` — 캐시 우선 조회

1. Redis의 `GET`으로 캐시를 조회한다.
2. 값이 있으면 검증 후 메시지와 `HIT`를 반환한다.
3. 값이 없으면 SQLite의 `read_source()`를 호출한다.
4. 결과를 JSON 문자열로 만들어 `SET ... EX 60`에 해당하는 작업으로 저장한다.
5. 메시지와 `MISS`를 반환한다.

`raw is not None`으로 판단하므로 빈 목록을 저장한 문자열 `"[]"`도 HIT다. `ensure_ascii=False`는 JSON에 한글을 문자 그대로 저장한다.

### `show_history(messages, source)` — 결과 출력

조회 경로인 `HIT` 또는 `MISS`와 메시지 번호·역할·내용을 출력한다. 목록이 비어 있으면 대화 이력이 없다고 안내한다.

### `main()` — 명령 실행과 자원 관리

`argparse`로 명령과 사용자 ID를 받는다. `init`에는 사용자 ID를 넣지 않고, `history`와 `evict`에는 사용자 ID가 필요하다.

`closing(sqlite3.connect(...))`으로 SQLite 연결을 종료한다. `timeout=5`는 SQLite 잠금 대기 시간이다. Redis는 `with redis.Redis(...)`로 연결 자원을 정리하며 응답을 문자열로 받는다. 연결 및 소켓 작업 제한 시간은 각각 1초다.

## 5. 명령어 및 실행 예시

`C:\AI4\Day14` 폴더에서 실행하는 예시다. Python 환경에 `redis`, `python-dotenv` 패키지가 필요하며, Redis 서버가 실행 중이어야 캐시 조회와 삭제가 가능하다.

`.env` 설정 예시:

```dotenv
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
SQLITE_PATH=C:/AI4/Day14/chat_history.db
```

상대 DB 경로를 지정하면 Python 실행 시의 현재 작업 폴더를 기준으로 해석된다.

| 실행 명령 | 기능 |
|---|---|
| `python main5.py init` | 테이블 생성 및 빈 테이블에 예제 데이터 추가 |
| `python main5.py history demo-a` | 민수의 대화 이력 조회 및 캐시 활용 |
| `python main5.py history demo-b` | 지연의 대화 이력 조회 및 캐시 활용 |
| `python main5.py evict demo-a` | 민수의 Redis 캐시만 삭제. SQLite 원본은 유지 |

캐시 동작 확인 순서:

```powershell
python main5.py init
python main5.py evict demo-a
python main5.py history demo-a
python main5.py history demo-a
python main5.py evict demo-a
python main5.py history demo-a
```

위 순서에서 세 번의 `history` 결과는, 캐시 만료나 다른 변경이 없다면 **MISS → HIT → MISS**다. 캐시 저장 후 60초가 지나도 다음 조회는 MISS가 된다.

## 6. 현재 코드에서 알아둘 점

- `init`은 Redis 서버가 꺼져 있어도 가능하지만, 설정 검사 때문에 Redis 주소와 포트 환경변수는 필요하다.
- Redis 장애 시 SQLite로 우회하지 않고 조회를 중단한다. **캐시가 없는 상황(MISS)**과 **Redis 서버에 연결할 수 없는 상황**은 다르게 처리된다.
- SQLite 파일이 없으면 `history`, `evict` 모두 거절된다. 먼저 `init`을 실행해야 한다.
- SQLite 원본을 외부에서 수정해도 기존 캐시는 즉시 갱신되지 않는다. `evict`로 삭제하거나 TTL 만료를 기다려야 한다. `init`도 캐시를 삭제하지 않는다.
- 사용자 ID를 구분하지만 실제 로그인이나 세션 인증은 구현하지 않는다.
- 파일 중간의 `host, port, db_path = read_settings()`가 `main()` 호출 전에도 실행된다. 이 시점의 설정 오류는 맨 아래 `try/except` 바깥에서 발생하므로 사용자용 오류 안내 대신 traceback이 출력될 수 있다. `main()` 안에서도 같은 설정을 다시 읽는다.

## 7. main4.py와 비교

| 구분 | main4.py | main5.py |
|---|---|---|
| 주요 목적 | 세션별 대화 저장과 모의 응답 | 원본 DB와 Redis 캐시의 역할 분리 |
| 대화 보관 기준 | 세션 ID | 사용자 ID |
| 원본 저장소 | 별도 영구 원본 없음 | SQLite |
| Redis 자료형 | List | String(JSON 목록) |
| 캐시 삭제·만료 후 | Redis에서 해당 대화가 사라짐 | SQLite 원본에서 다시 조회 가능 |
| 응답 생성 | 규칙 기반 모의 응답 | 없음. 이력 조회만 수행 |
