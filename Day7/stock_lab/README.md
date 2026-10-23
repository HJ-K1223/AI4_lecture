# 소소 상점 · 재고 조회 실험실

쇼핑몰에서 상품 3개의 재고를 확인하는 상황으로 동기·비동기를 비교하는 로컬 학습 앱입니다.
기존 Day7/main.py, Day7/probe.py와 독립적으로 실행합니다.
FastAPI, Uvicorn, asyncio, time, HTTPX를 사용합니다. 화면은 HTML/CSS/JavaScript이며 별도 프런트엔드 설치가 필요 없습니다.
실제 DB/외부 서비스 대신 조회마다 2초의 I/O 대기를 흉내냅니다.

## 1. 설치 및 실행 (Windows PowerShell)

Python 3.10 이상이 필요합니다. 먼저 현재 8000번 포트에서 실행 중인 기존 서버를 해당 터미널에서 Ctrl+C로 종료하세요.

```powershell
cd C:\AI4\Day7\stock_lab
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --port 8000 --workers 1
```

브라우저에서 **http://127.0.0.1:8000** 을 여세요. API 문서는 **http://127.0.0.1:8000/docs** 입니다.
서버 종료는 Ctrl+C입니다. Python 파일을 변경한 뒤에는 서버를 재시작하세요.
가상환경 활성화 명령 없이 실행하므로 PowerShell 실행 정책 변경이 필요 없습니다.

`python` 명령을 찾을 수 없다면 `py --version`을 확인하고 위의 가상환경 생성 명령만 `py -m venv .venv`로 실행하세요.
둘 다 실행되지 않으면 Python 설치 및 터미널 PATH 설정이 필요합니다.
기존 가상환경에서 원본 Python 경로를 찾지 못하는 경우에도 정상 설치된 Python으로 이 하위 폴더의 새 가상환경을 생성하세요.

8000번 포트를 다른 앱이 사용 중이라면 `--port 8001`로 실행하고 브라우저도 8001번으로 접속하세요.
이 경우 아래 probe에는 `--url http://127.0.0.1:8001`을 추가합니다.

## 2. 화면에서 실험하기

1. **동기 호출 · 서버 정지**를 선택하고 **상품 1개 조회**를 누릅니다.
2. 같은 방식으로 **상품 3개 함께 조회**를 누릅니다.
3. 비동기 조회와 스레드 위임에서도 같은 실험을 합니다.
4. **세 방식 차례로 비교**는 세 방식의 3개 요청 실험을 한 묶음씩 순서대로 실행합니다. 약 10초가 예상됩니다.
5. 전체 시간, /health 응답 시간, 서버 조회 구간, 스레드 ID, 비교 기록을 관찰합니다.

| 방식 | 1개 예상 | 3개 예상 | 조회가 실행되는 곳 |
|---|---:|---:|---|
| 동기 직접 호출 bad | 약 2초 | 약 6초 | 이벤트 루프 스레드, sleep이 스레드를 정지 |
| 비동기 조회 good | 약 2초 | 약 2초 | 이벤트 루프 스레드, await 중 다른 요청 진행 |
| 동기 스레드 위임 thread | 약 2초 | 약 2초 | 별도 스레드, 이벤트 루프는 다른 요청 진행 |

위 숫자는 **예상값**입니다. 화면과 probe가 표시하는 실측 결과를 우선하세요.
두 개 이상의 브라우저 탭이나 probe를 함께 실행하면 서로 영향을 줍니다. 비교는 한 클라이언트씩 진행하세요.
여러 worker를 사용하면 요청이 서로 다른 프로세스로 분산되어 실험 결과가 달라지므로 단일 worker를 유지하세요.

## 3. 다른 터미널에서 HTTPX로 확인하기

서버를 실행한 채 새 PowerShell 터미널에서:

```powershell
cd C:\AI4\Day7\stock_lab
.\.venv\Scripts\python.exe probe.py
.\.venv\Scripts\python.exe probe.py --mode bad --count 1
```

첫 명령은 bad → good → thread 순서로 각 3개를 asyncio.gather()로 함께 요청합니다.
둘째 명령은 bad 요청 한 개를 측정합니다. `--mode good`, `--mode thread`도 가능합니다.
시작 시각 차이(ms), HTTP 상태, 응답 시간, 서버 조회 구간, 스레드 정보를 출력합니다.

## 4. 코드를 읽는 순서

- **main.py / legacy_lookup**: `sleep(2)`로 현재 스레드를 멈추는 동기 보조 함수입니다.
- **main.py / async_lookup**: `await asyncio.sleep(2)`로 대기 중 제어권을 양보합니다.
- **main.py / stock**: 같은 데이터에 대해 세 호출 방식을 비교합니다.
  - bad: `legacy_lookup(product_id)`
  - good: `await async_lookup(product_id)`
  - thread: `await asyncio.to_thread(legacy_lookup, product_id)`
- **probe.py / compare**: `asyncio.gather()`로 요청을 함께 진행합니다.
- **static/app.js / experiment**: 브라우저에서는 fetch 호출을 모두 시작한 뒤 Promise.allSettled()로 기다립니다.

일반 `def` 보조 함수가 자동으로 스레드 풀로 이동하지는 않습니다.
이 앱의 세 엔드포인트 분기는 모두 같은 `async def stock` 안에서 실행되며, thread 방식에서만 명시적으로 조회를 별도 스레드에 맡깁니다.
FastAPI가 일반 `def` 엔드포인트를 스레드 풀에 위임하는 동작과 구분하세요.

## 5. 화면 수치를 해석하는 방법

- **전체 완료 시간**: 첫 상품 요청을 시작한 때부터 모든 상품 응답 본문을 받은 때까지의 브라우저 측 시간입니다. /health 완료 대기는 포함하지 않습니다.
- **응답 대기 시간**: 각 fetch 호출부터 응답 본문 수신까지입니다. 네트워크와 서버 진입 전 대기도 포함됩니다.
- **서버 조회 구간**: 서버 perf_counter()의 조회 시작·종료 기록입니다. 첫 조회 시작을 0으로 표시합니다. 세 방식의 시각적 비교를 위해 축은 최소 6초입니다.
- 서버와 브라우저 시계는 서로 빼지 않습니다. 서버 기록끼리, 클라이언트 기록끼리 비교합니다.
- **/health 응답 시간**: 상품 요청을 시작한 약 0.3초 뒤 보내는 가벼운 요청의 응답 대기 시간입니다. bad에서 길어지고 good/thread에서 짧아지는지 관찰하세요. 전송·도착 순서에 따라 달라질 수 있습니다.
- **스레드**: good은 여러 요청이 같은 스레드 ID여도 대기가 겹칠 수 있습니다. thread는 조회 스레드 ID가 엔드포인트 스레드와 다릅니다.
- bad 요청 각각의 응답 시각이 반드시 2초·4초·6초로 나뉘지는 않습니다. 전송과 이벤트 루프 일정에 따라 여러 응답이 늦게 함께 도착할 수도 있습니다. 서버 조회 구간과 전체 시간을 함께 확인하세요.
- HTTP 200은 응답 성공을 뜻하며, 서버가 다른 요청도 원활하게 처리했다는 증거는 아닙니다.
- 실험 중 화면 타이머가 움직이는 것은 브라우저 JavaScript가 서버와 별도로 실행되기 때문입니다.
- 비교 기록은 메모리에만 보관하고 새로고침 시 초기화됩니다. 재고 확인만 하며 주문이나 재고 차감은 없습니다.

## 6. 카페 비유와 실제 서비스 적용

bad는 직원이 한 잔의 준비를 기다리며 다음 주문까지 멈추는 상황입니다.
good은 음료 준비를 기다리는 동안 다음 주문을 받는 상황입니다.
thread는 기존 방식으로 일하는 보조 직원에게 준비를 맡기는 상황입니다.

실제 서비스에서는 `asyncio.sleep` 자리에 비동기 라이브러리의 조회를 넣습니다.
예를 들어 비동기 HTTP 조회에는 HTTPX AsyncClient의 `await client.get(...)`을 사용할 수 있습니다.
동기 함수를 단순히 `async def`로 감싸거나 앞에 await만 붙여서는 비동기가 되지 않습니다.
to_thread는 이 예제처럼 기다림이 긴 동기 I/O를 위임하는 방향이며 CPU 계산을 무조건 빠르게 만드는 방법은 아닙니다.

공식 설명: [FastAPI의 보조 함수와 스레드](https://fastapi.tiangolo.com/async/#other-utility-functions), [Python asyncio.to_thread](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread).

## 작성 환경의 검증 상태

JavaScript 문법, HTML ID 중복 및 JavaScript가 참조하는 고정 ID의 존재를 확인했습니다.
모의 HTTP 응답을 사용해 상품 요청 3개가 응답을 받기 전에 모두 시작되는지, 결과·타임라인·비교 기록이 표시되는지, 실행 후 버튼이 다시 활성화되는지도 확인했습니다.
이 검사는 실제 FastAPI 요청이나 브라우저 화면의 시각적 검증은 아닙니다.

작성 환경에서는 Python 명령이 없고 기존 가상환경의 원본 Python 경로도 유효하지 않아 서버 및 probe를 실행하지 못했습니다.
따라서 위 예상 시간을 실제 측정값으로 제시하지 않습니다. 설치 후 위 명령으로 HTTP 실측을 확인하세요.
