from fastapi import FastAPI

app = FastAPI(title="Lesson 02")

@app.get("/method") # 라우터
def read_method():
    return {"method": "GET", "purpose": "read"}

# Swagger UI에서 POST 요청을 테스트할 수 있도록 status_code를 201로 설정
@app.post("/method", status_code=201)
def create_method():
    return {"method": "POST", "purpose": "create"}

# @app.put("/method", status_code=204)
# def replace_method():
#     return{"method":"PUT","purpose" : "replace"}