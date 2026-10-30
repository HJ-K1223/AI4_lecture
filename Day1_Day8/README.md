# 작은 방명록 — Supabase PostgreSQL

2026-10-29: 로컬 코드를 SQLite에서 Supabase PostgreSQL로 변경했다.
alwaysdata의 운영 사이트에는 아직 업로드하지 않았다. 회원가입·JWT 인증은 아직 없다.

## 설정

`config.json`은 이 폴더에 두며 Git에서 제외한다. 실제 비밀번호는 문서에 기록하지 않는다.
필수 키는 `host`, `port`, `dbname`, `user`, `password`다.
앱은 `GUESTBOOK_CONFIG_PATH` 환경변수로 다른 설정 파일 경로도 지정할 수 있다.
상대 경로는 이 폴더 기준이다. `GUESTBOOK_DB_PATH`는 이제 사용하지 않는다.

Supabase SQL Editor에서 만든 `public.guestbook` 테이블이 필요하다.
열은 `id`(identity 기본 키), `name`(text), `message`(text),
`created_at`(timestamptz, 기본값 now())이다. 앱은 테이블을 자동 생성하지 않는다.
RLS 정책과 연결 계정 권한은 별도 관리한다. 관리자 DB 계정 연결에 사용자 JWT가 자동 적용되지는 않는다.

## 로컬 실행

Python 3.10 이상과 `requirements.txt`의 패키지가 필요하다.
현재 이 폴더의 `.venv`에 검증용 환경을 준비했다. C:\AI4에서 실행한다.

```powershell
.\Day1_Day8\.venv\Scripts\python.exe -m uvicorn main:app --app-dir Day1_Day8 --host 127.0.0.1 --port 8000 --workers 1
```

브라우저에서 http://127.0.0.1:8000 을 연다. 글 등록은 실제 Supabase에 저장된다.
TLS를 사용하며 연결 대기는 5초, SQL 실행은 10초, 잠금 대기는 5초로 제한한다.

읽기 전용 연결 확인(기본 config.json 사용):

```powershell
.\Day1_Day8\.venv\Scripts\python.exe Day1_Day8/check_connection.py
```

## 기능

이름 1~20자, 내용 1~500자, 최신순 10건씩 표시한다.
작성 시각은 PostgreSQL의 now()로 저장하고 화면에는 한국 시간으로 변환한다.
최대 1,000건이며 테이블 잠금을 잡은 트랜잭션에서 개수 검사와 등록을 수행한다.
이 제한은 앱의 저장 경로에 적용된다. SQL Editor 등에서 직접 INSERT하는 경우에는 적용되지 않는다.
입력 검사, HTML 이스케이프, 폼 크기 제한, DB 장애 시 503 응답을 유지한다.

## 검증

```powershell
.\Day1_Day8\.venv\Scripts\python.exe -m pytest Day1_Day8/test_guestbook.py -q -p no:cacheprovider
```

현재 테스트는 설정 오류, 한국 시간 표시, HTML 이스케이프, HTTP 입력 검사,
등록 리다이렉트, DB 오류 응답을 DB 대역으로 검증한다.
실제 PostgreSQL 저장·동시 등록·한도·재시작 보존은 별도 통합 검증이 필요하다.
기존 SQLite 전용 테스트는 현재 코드와 호환되지 않아 위 검증으로 교체했다.

## 이후 배포

기존 DEPLOYMENT.md와 DEPLOYMENT_HJK.md의 SQLite 설명은 이전 배포 기록이다.
다음 배포 때 기존 운영 코드·SQLite를 백업하고 변경한 코드와 requirements.txt를 업로드한다.
서버의 Linux 가상환경에 의존성을 설치하고 config.json을 안전한 위치에 별도로 배치한다.
필요하면 GUESTBOOK_CONFIG_PATH를 지정하고 Web > Sites에서 사이트를 재시작한다.
Windows .venv는 업로드하지 않는다. 기존 SQLite 글은 자동 이전되지 않는다.
