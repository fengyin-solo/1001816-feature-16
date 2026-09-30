"""城市地下管网巡检养护平台 后端服务入口。

启动：uvicorn app.main:app --host 127.0.0.1 --port 8000
健康检查：GET /api/health
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.catalog import get_spec, label_of
from app.config import settings
from app.routers import ROUTERS
from app.security import resolve_identity
from app.store import store

app = FastAPI(title="城市地下管网巡检养护平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def scope_business_modules(request: Request, call_next):
    """业务模块账号访问他人台账时直接拦下并说明原因。

    值班管理员放行；访客（未声明身份）不在此拦截，避免裸打开台账页一片白板，
    但下钻接口仍要求明确身份。
    """
    if request.url.path.startswith("/api/"):
        parts = request.url.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api" and get_spec(parts[1]) is not None:
            identity = resolve_identity(
                request.headers.get("x-operator-role"),
                request.headers.get("x-operator-module"),
            )
            if identity.role == "module" and identity.module != parts[1]:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": (
                            f"业务模块账号只能查看本单位（{label_of(identity.module or '')}）经手的单子，"
                            f"「{label_of(parts[1])}」不在你的权限范围内"
                        )
                    },
                )
    return await call_next(request)


for module in ROUTERS:
    app.include_router(module.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    """健康检查：确认服务已经监听、示例数据已经就绪。"""
    return {"ok": True, "app": settings.app_name, "modules": len(store.module_names())}
