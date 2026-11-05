"""실행: uvicorn app.main:app --reload."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import PROJECT_ROOT, Settings, get_settings
from app.core.db import Database
from app.core.auth import LoginRequired
from app.core.security import SESSION_COOKIE, SESSION_MAX_AGE, SecurityMiddleware, login_url
from app.core.templates import render
from app.services.shop import ShopError
from app.routers.auth import router as auth_router
from app.routers.cart import router as cart_router
from app.routers.orders import router as orders_router
from app.routers.payments import router as payments_router
from app.routers.products import router as products_router
from app.routers.pages import router as pages_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        database = Database(settings)
        application.state.database = database
        try:
            yield
        finally:
            database.dispose()

    application = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.state.settings = settings
    application.state.templates = Jinja2Templates(directory=PROJECT_ROOT / "app" / "templates")
    application.state.templates.env.filters["won"] = lambda amount: f"{amount:,}원"
    application.add_middleware(SecurityMiddleware)
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret.get_secret_value(),
        session_cookie=SESSION_COOKIE,
        max_age=SESSION_MAX_AGE,
        same_site="lax",
        https_only=settings.cookie_secure,
        path="/",
    )
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    @application.exception_handler(LoginRequired)
    async def authentication_required(request: Request, error: LoginRequired):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": "로그인이 필요합니다."}, status_code=401)
        next_path = request.url.path + ("?" + request.url.query if request.url.query else "")
        return RedirectResponse(login_url(next_path), status_code=303)

    @application.exception_handler(SQLAlchemyError)
    async def database_unavailable(request: Request, error: SQLAlchemyError):
        detail = "일시적으로 요청을 처리할 수 없습니다. 잠시 후 다시 시도하세요."
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": detail}, status_code=503)
        return render(request, "error.html", member=getattr(request.state, "member", None), status_code=503, detail=detail)

    @application.exception_handler(ShopError)
    async def shop_error(request: Request, error: ShopError):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": error.detail, "code": error.code}, status_code=error.status_code)
        return render(request, "error.html", member=getattr(request.state, "member", None),
                      status_code=error.status_code, detail=error.detail)
    application.mount("/static", StaticFiles(directory=PROJECT_ROOT / "app" / "static"), name="static")
    application.include_router(pages_router)
    application.include_router(auth_router)
    application.include_router(products_router)
    application.include_router(cart_router)
    application.include_router(orders_router)
    application.include_router(payments_router)
    return application


app = create_app()
