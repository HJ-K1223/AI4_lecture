# main3.py 코드 해설

## 목적

Redis에 세션을 저장하여 **세션 생성 → 사용자 확인 → 만료 또는 로그아웃** 과정을 실습하는 코드다. 실제 로그인 인증 대신 가상의 사용자 두 명을 사용한다.

## 저장 구조

| 항목 | 내용 |
|---|---|
| Redis 자료형 | String |
| 키 | `lesson03:session:{세션 ID}` |
| 값 | `demo-a` 또는 `demo-b` |
| 만료 시간 | 생성 후 60초. 조회해도 연장되지 않는다. |

세션 ID는 사용자 ID 자체가 아니라, 서버에 저장된 사용자 정보를 찾는 임의의 식별자다.

## 코드 흐름

1. **모듈과 상수 준비**: `argparse`는 명령줄 인자를 처리하고, `secrets`는 추측하기 어려운 세션 ID를 만든다. `DEMO_USERS`에는 사용자 ID와 이름을 저장한다.
2. **명령 입력**: `command`에는 `create`, `get`, `logout` 중 하나를 받는다. `value`에는 생성할 때 사용자 ID, 나머지 작업에서는 세션 ID를 받는다.
3. **설정 읽기와 검증**: 현재 작업 폴더의 `.env`에서 `REDIS_HOST`, `REDIS_PORT`를 읽는다. 기존 환경변수가 우선하며, 주소의 누락과 포트 범위(1~65535)를 검사한다.
4. **Redis 연결**: `decode_responses=True`로 응답을 문자열로 받고, 연결 및 소켓 작업의 제한 시간을 각각 2초로 설정한다. `with` 블록이 끝나면 연결 자원을 정리한다.
5. **명령에 따른 처리**: 아래 표와 같이 세션을 저장·조회·삭제한다.
6. **오류 처리**: 입력·설정 오류와 Redis 오류를 구분해 출력하고 종료 코드 `1`로 끝낸다. 명령줄 형식 오류는 `argparse`가 처리한다.

## 명령별 핵심 코드

| 명령 | 핵심 처리 | 의미 |
|---|---|---|
| `create` | `"sid_" + secrets.token_urlsafe(32)` | 32바이트 난수를 이용해 세션 ID 생성. `sid_`는 CLI 옵션으로 오인되는 것을 방지한다. |
| `create` | `client.set(key, args.value, ex=SESSION_TTL)` | 사용자 ID 저장과 60초 만료 설정을 함께 수행한다. |
| `get` | `client.get(key)` | 세션 ID로 사용자 ID를 찾는다. 없거나 만료되었으면 접근을 거절한다. |
| `get` | `client.ttl(key)` | 세션의 남은 유효 시간을 확인한다. |
| `logout` | `client.delete(key)` | 서버의 세션을 삭제한다. 삭제한 키 수를 출력한다. |

## 실행 예시

`C:\AI4\Day14` 폴더에서 실행하고, 해당 폴더의 `.env`에는 다음 설정을 준비한다. Python 환경에는 `redis`, `python-dotenv` 패키지가 필요하다.

```dotenv
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```

```powershell
python main3.py create demo-a
python main3.py get <발급받은_세션_ID>
python main3.py logout <발급받은_세션_ID>
```

`<발급받은_세션_ID>`는 꺾쇠까지 포함해 실제 출력된 `sid_...` 값으로 바꾼다. 생성 후 60초가 지나거나 로그아웃한 뒤에는 조회가 거절된다.

## 알아둘 점

- 비밀번호 확인이나 실제 회원 DB 조회는 없는 세션 관리 실습이다.
- 세션 ID는 `uuid`가 아니라 `secrets`로 생성한다.
- `GET`과 `TTL`은 별도 요청이므로 그 사이에 만료되면 TTL이 `-2`일 수도 있다.
- 세션은 Hash가 아닌 String으로 저장한다. 사용자 이름은 Redis가 아니라 `DEMO_USERS`에서 찾는다.
