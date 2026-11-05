from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Browser input example")


@app.get("/", response_class=HTMLResponse)
def home():
    # The input name 'some' becomes the query parameter /how?some=7.
    return """
    <!doctype html>
    <html lang="ko">
    <head><meta charset="utf-8"><title>숫자 판별</title></head>
    <body>
        <h1>숫자를 입력하세요</h1>
        <form action="/how" method="get">
            <label>정수: <input type="number" name="some" step="1" required></label>
            <button type="submit">결과 보기</button>
        </form>
    </body>
    </html>
    """


@app.get("/how", response_class=HTMLResponse)
def how(some: int):
    # FastAPI reads 'some' from the URL and validates it as an integer.
    if some >= 5:
        message = "큰 수를 입력하셨습니다."
    else:
        message = "작은 수를 입력하셨습니다."
    return f"""
    <!doctype html>
    <html lang="ko">
    <head><meta charset="utf-8"><title>판별 결과</title></head>
    <body>
        <h1>판별 결과</h1>
        <p>입력값: {some}</p>
        <p>{message}</p>
        <a href="/">다시 입력하기</a>
    </body>
    </html>
    """
'@ | Set-Content -LiteralPath $examplePath -Encoding UTF8