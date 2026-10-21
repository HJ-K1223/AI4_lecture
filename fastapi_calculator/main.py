"""두 값을 받아 사칙연산을 수행하는 FastAPI 학습용 앱."""
from decimal import Decimal, InvalidOperation, localcontext
from html import escape
from pathlib import Path
import re
from string import Template

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
PAGE = Template((BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8"))
app = FastAPI(title="두 숫자 계산기")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def parse_number(text: str, label: str) -> Decimal:
    """숫자 형식, 크기, 소수 자릿수를 검사합니다."""
    text = text.strip()
    if not text:
        raise ValueError(f"{label}을 입력해 주세요.")
    if len(text) > 40 or not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", text):
        raise ValueError(f"{label}에는 올바른 숫자를 입력해 주세요. 예: -3, 0.5")
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"{label}의 숫자 형식을 확인해 주세요.") from None
    if abs(number) > Decimal("1000000000000"):
        raise ValueError(f"{label}은 -1조부터 1조 사이로 입력해 주세요.")
    if number.as_tuple().exponent < -12:
        raise ValueError(f"{label}은 소수점 아래 12자리까지 입력할 수 있어요.")
    return number


def format_number(number: Decimal) -> str:
    """지수 표기와 불필요한 소수점 뒤 0을 제거합니다."""
    if number == 0:
        return "0"
    text = format(number, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def calculate(first: Decimal, second: Decimal) -> list[tuple[str, str, str]]:
    """계산은 Python 서버에서 수행하며, 나눗셈은 소수 12자리로 반올림합니다."""
    with localcontext() as context:
        context.prec = 60
        division = "0으로 나눌 수 없어요."
        if second != 0:
            division = format_number((first / second).quantize(Decimal("0.000000000001")))
        return [
            ("덧셈", "+", format_number(first + second)),
            ("뺄셈", "−", format_number(first - second)),
            ("곱셈", "×", format_number(first * second)),
            ("나눗셈", "÷", division),
        ]


def render_page(first: str = "", second: str = "", error: str = "", results=None) -> str:
    """사용자 입력은 HTML 이스케이프 후 화면에 표시합니다."""
    cards = ""
    if results is not None:
        items = "".join(
            f'<article class="result-card"><span class="operation">{name} <b>{symbol}</b></span>'
            f'<strong>{escape(value)}</strong></article>'
            for name, symbol, value in results
        )
        cards = f'<section class="results" aria-label="계산 결과"><h2>계산 결과</h2><div class="grid">{items}</div></section>'
    return PAGE.substitute(
        first=escape(first, quote=True),
        second=escape(second, quote=True),
        error=f'<p class="error" role="alert">{escape(error)}</p>' if error else "",
        results=cards,
    )


@app.get("/", response_class=HTMLResponse)
def home():
    return render_page()


@app.get("/calculate", response_class=HTMLResponse)
def calculate_page(first: str = "", second: str = ""):
    # first, second는 /calculate?first=10&second=2에서 받는 쿼리 매개변수입니다.
    try:
        a = parse_number(first, "첫 번째 값")
        b = parse_number(second, "두 번째 값")
    except ValueError as error:
        return HTMLResponse(render_page(first, second, error=str(error)), status_code=422)
    return render_page(first, second, results=calculate(a, b))
