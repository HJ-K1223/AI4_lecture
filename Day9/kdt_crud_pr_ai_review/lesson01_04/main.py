"""FastAPI 방명록: 이름과 메시지를 등록·조회·수정·삭제합니다."""
from threading import Lock

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="간단한 방명록 API")
tasks = [{"id": 1, "name": "홍길동", "message": "안녕하세요"}]

# 시작할 때 한 번만 초기 데이터의 최대 ID를 확인합니다.
last_issued_id = 0
for task in tasks:
    if task["id"] > last_issued_id:
        last_issued_id = task["id"]
create_lock = Lock()


class TaskCreate(BaseModel):
    name: str = Field(min_length=1)
    message: str = Field(min_length=1)


class TaskPut(BaseModel):
    # ID는 서버가 관리하므로 수정 요청의 필드에 포함하지 않습니다.
    name: str = Field(min_length=1)
    message: str = Field(min_length=1)


class TaskPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    message: str | None = Field(default=None, min_length=1)


def find_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.get("/tasks")
def list_tasks():
    return tasks


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    global last_issued_id

    # 삭제해도 카운터는 줄이지 않습니다. 등록 요청은 하나씩 처리합니다.
    with create_lock:
        last_issued_id += 1
        task = {
            "id": last_issued_id,
            "name": payload.name,
            "message": payload.message,
        }
        tasks.append(task)
    return task


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    return find_task(task_id)


@app.put("/tasks/{task_id}")
def replace_task(task_id: int, payload: TaskPut):
    task = find_task(task_id)
    task.update(payload.model_dump())
    return task


@app.patch("/tasks/{task_id}")
def patch_task(task_id: int, payload: TaskPatch):
    task = find_task(task_id)
    changes = payload.model_dump(exclude_unset=True)

    # 생략은 허용하지만, 명시적인 null로 기존 값을 지우는 것은 거절합니다.
    for field, value in changes.items():
        if value is None:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null")

    task.update(changes)
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail="Task not found")
