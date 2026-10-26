"""TestClient로 방명록 CRUD와 오류·경계 입력을 검증합니다."""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
issued_ids = []


def expect_status(response, expected):
    print(response.request.method, response.request.url.path,
          "->", response.status_code)
    assert response.status_code == expected, response.text


def create_task(name, message):
    response = client.post("/tasks", json={"name": name, "message": message})
    expect_status(response, 201)
    task = response.json()
    assert task["name"] == name
    assert task["message"] == message
    assert isinstance(task["id"], int) and task["id"] >= 1
    assert task["id"] not in issued_ids, "발급했던 ID가 재사용되었습니다"
    if issued_ids:
        assert task["id"] > max(issued_ids), "ID가 증가하지 않았습니다"
    issued_ids.append(task["id"])
    print("issued ID:", task["id"])
    return task


def run_checks():
    # 초기 데이터의 ID도 발급 이력에 포함합니다.
    response = client.get("/tasks")
    expect_status(response, 200)
    initial_tasks = response.json()
    assert initial_tasks, "초기 데이터가 있어야 합니다. 새 Python 프로세스에서 실행하세요"
    for task in initial_tasks:
        assert isinstance(task["id"], int) and task["id"] >= 1
        assert len(task["name"]) >= 1 and len(task["message"]) >= 1
        assert task["id"] not in issued_ids
        issued_ids.append(task["id"])
        response = client.get(f"/tasks/{task['id']}")
        expect_status(response, 200)
        assert response.json() == task
    print("PASS: 초기 방명록 전체·개별 조회")

    first = create_task("첫 방문자", "반갑습니다")
    middle = create_task("김", "안")
    last = create_task("마지막 방문자", "잘 보고 갑니다")
    first_url = f"/tasks/{first['id']}"
    middle_url = f"/tasks/{middle['id']}"
    response = client.get(first_url)
    expect_status(response, 200)
    assert response.json() == first
    print("PASS: 정상 등록·조회, 이름과 메시지 한 글자 허용")

    response = client.put(first_url, json={"name": "전체 수정", "message": "둘 다 수정"})
    expect_status(response, 200)
    assert response.json() == {
        "id": first["id"], "name": "전체 수정", "message": "둘 다 수정",
    }

    response = client.patch(first_url, json={"name": "이름만 수정"})
    expect_status(response, 200)
    assert response.json() == {
        "id": first["id"], "name": "이름만 수정", "message": "둘 다 수정",
    }
    response = client.patch(first_url, json={"message": "메시지만 수정"})
    expect_status(response, 200)
    assert response.json() == {
        "id": first["id"], "name": "이름만 수정", "message": "메시지만 수정",
    }
    response = client.patch(first_url, json={"name": "가", "message": "나"})
    expect_status(response, 200)
    assert response.json() == {"id": first["id"], "name": "가", "message": "나"}
    before = response.json()
    response = client.patch(first_url, json={})
    expect_status(response, 200)
    assert response.json() == before
    print("PASS: PUT 전체 수정, PATCH 선택 수정·기존 값 보존, 빈 PATCH")

    # 누락·빈 문자열·null은 거절하고 목록 전체를 보존해야 합니다.
    before_list = client.get("/tasks").json()
    invalid_full_inputs = [
        {},
        {"name": "메시지 누락"},
        {"message": "이름 누락"},
        {"name": "", "message": "안녕하세요"},
        {"name": "방문자", "message": ""},
        {"name": None, "message": "안녕하세요"},
        {"name": "방문자", "message": None},
    ]
    for payload in invalid_full_inputs:
        response = client.post("/tasks", json=payload)
        expect_status(response, 422)
        assert client.get("/tasks").json() == before_list
        response = client.put(first_url, json=payload)
        expect_status(response, 422)
        assert client.get("/tasks").json() == before_list
    for payload in [
        {"name": ""}, {"message": ""}, {"name": None}, {"message": None},
        {"name": "변경되면 안 됨", "message": None},
    ]:
        response = client.patch(first_url, json=payload)
        expect_status(response, 422)
        assert client.get("/tasks").json() == before_list
    print("PASS: POST·PUT·PATCH 오류 입력 422, 기존 데이터 보존")

    response = client.delete(middle_url)
    expect_status(response, 204)
    assert response.content == b""
    expected_remaining = initial_tasks + [before, last]
    assert client.get("/tasks").json() == expected_remaining
    print("PASS: 요청 ID만 삭제, 다른 방명록 보존, 204 빈 응답")

    # 없는 번호를 임의로 정하지 않고, 방금 삭제한 ID로 검사합니다.
    for response in [
        client.get(middle_url),
        client.put(middle_url, json={"name": "방문자", "message": "없음"}),
        client.patch(middle_url, json={"message": "없음"}),
        client.delete(middle_url),
    ]:
        expect_status(response, 404)
        assert response.json() == {"detail": "Task not found"}
    assert client.get("/tasks").json() == expected_remaining
    print("PASS: 없는 ID에 GET·PUT·PATCH·DELETE 모두 404")

    last_url = f"/tasks/{last['id']}"
    response = client.get(last_url)
    expect_status(response, 200)
    assert response.json() == last
    response = client.put(last_url, json={"name": "위치 변경", "message": "PUT 확인"})
    expect_status(response, 200)
    assert response.json() == {
        "id": last["id"], "name": "위치 변경", "message": "PUT 확인",
    }
    response = client.patch(last_url, json={"message": "PATCH 확인"})
    expect_status(response, 200)
    assert response.json() == {
        "id": last["id"], "name": "위치 변경", "message": "PATCH 확인",
    }
    assert client.get(first_url).json() == before
    print("PASS: ID와 리스트 위치가 달라도 조회·수정 가능")

    response = client.delete(last_url)
    expect_status(response, 204)
    new_task = create_task("새 방문자", "최대 ID 삭제 후 등록")
    assert new_task["id"] > last["id"]
    print("PASS: 최대 ID 삭제 후 기존·삭제된 ID와 중복 없음")

    for task in client.get("/tasks").json():
        response = client.delete(f"/tasks/{task['id']}")
        expect_status(response, 204)
    response = client.get("/tasks")
    expect_status(response, 200)
    assert response.json() == []
    final_task = create_task("다시 방문", "전체 삭제 후 등록")
    response = client.get("/tasks")
    expect_status(response, 200)
    assert response.json() == [final_task]
    print("PASS: 전체 삭제 후에도 ID 재사용 없음")
    print("ALL PASS")


if __name__ == "__main__":
    run_checks()
