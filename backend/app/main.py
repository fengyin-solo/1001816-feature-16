"""城市地下管网巡检养护平台 后端服务入口。

启动：uvicorn app.main:app --host 127.0.0.1 --port 8000
健康检查：GET /api/health
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, Header, Query
from fastapi.middleware.cors import CORSMiddleware

from app.accounts import Account, require_module_account
from app.config import settings
from app.modules import MODULES
from app.routers import ROUTERS
from app.store import store

app = FastAPI(title="城市地下管网巡检养护平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_MODULE_PREFIXES = {f"/api/{meta.key}" for meta in MODULES}


def _module_guard(module_key: str):
    """生成该业务模块的账号守卫：先登录，再核对账号是否属于这个模块。"""

    def _guard(
        x_account_id: str | None = Header(default=None),
        account_id: str | None = Query(default=None),
    ) -> Account:
        return require_module_account(module_key, x_account_id, account_id)

    return _guard


# 概览/下钻路由自带账号依赖；其余每个业务模块路由按模块归属统一守卫，
# 这样业务账号只能进本单位模块的接口，无需改动 18 个路由文件。
for module in ROUTERS:
    if module.router.prefix in _MODULE_PREFIXES:
        module_key = module.router.prefix.removeprefix("/api/")
        # 注意：守卫要在 include_router 时通过 dependencies 传入；
        # 路由装饰器在注册阶段就读取依赖，事后改 router.dependencies 不会生效。
        app.include_router(module.router, dependencies=[Depends(_module_guard(module_key))])
    else:
        app.include_router(module.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    """健康检查：确认服务已经监听、示例数据已经就绪。"""
    return {"ok": True, "app": settings.app_name, "modules": len(store.module_names())}
