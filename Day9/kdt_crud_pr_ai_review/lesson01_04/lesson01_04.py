from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

'''
Create : POST status 201
Read : GET
Update PUT / PATCH
Delete DELETE

초기데이터 list[dict]
id : int(1이상), name : str (1글자 이상), message : str (1글자 이상)
'''
app = FastAPI()
tasks = [{'id':1,'name':'홍길동','message':'안녕하세요'}]

class TaskPut(BaseModel):
    id : int = Field(ge=1)
    name: str = Field(min_length=1)
    message : str = Field(min_length=1)

@app.get('/tasks')
def list_tasks():
    return tasks

@app.post('/tasks/{task_id}')
def create_tasks():
    