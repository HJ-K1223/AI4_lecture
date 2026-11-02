from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Lesson 01")

@app.get("/")
def root():
    return {"message": "Hello FastAPI"}

@app.get("/sports")
def sports():
    return{"sports":["Soccer","Bakketball","Tennis","Baseball"]}

