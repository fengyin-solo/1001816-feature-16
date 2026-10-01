"""运营概览与下钻接口：卡片数字、模块台账、历史留档与卡片下钻取数。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.accounts import Account, require_account, require_admin
from app.schemas import ActionResult
from app.services.drill import drill_service
from app.store import store

router = APIRouter(prefix="/api", tags=["运营概览"])


@router.get("/accounts")
def list_accounts() -> dict[str, object]:
    """可选值班账号：一个值班管理员 + 各业务模块本单位账号（供前端切换身份）。"""
    from app.accounts import ACCOUNT_OPTIONS

    return {
        "items": [
            {"id": acc.id, "label": acc.label, "role": acc.role, "module": acc.module_key}
            for acc in ACCOUNT_OPTIONS
        ]
    }


@router.get("/overview")
def overview(account: Account = Depends(require_account)) -> dict[str, object]:
    """运营概览：卡片与模块行取自同一份台账；业务账号只汇总本单位模块。"""
    return store.overview(account)


@router.get("/drill")
def drill_entries(
    kind: str = Query(description="卡片口径：created/pending/abnormal"),
    account: Account = Depends(require_account),
    module: str | None = Query(default=None, description="限定单个业务模块；不传即跨模块（仅管理员）"),
    status: str | None = Query(default=None, description="单模块按业务状态挑，跨模块仅支持 __pending__/__abnormal__"),
    fail: str | None = Query(default=None, description="演示用：模拟这些模块台账拉取失败（逗号分隔）"),
) -> dict[str, Any]:
    """把一块卡片数字按同一口径展开成单子；失败模块单列说明，不拖垮整页。"""
    fail_modules = {item.strip() for item in fail.split(",") if item.strip()} if fail else set()
    return drill_service.query(
        account,
        kind=kind,
        module=module,
        status=status,
        fail_modules=fail_modules,
    )


@router.get("/overview/snapshots")
def list_snapshots(account: Account = Depends(require_admin)) -> dict[str, object]:
    """历史统计留档：按留档当时口径冻结，仅值班管理员可调阅。"""
    return {"items": store.snapshots()}


@router.post("/overview/snapshots", response_model=ActionResult)
def create_snapshot(account: Account = Depends(require_admin)) -> ActionResult:
    """按当前口径补一份留档；不影响已有历史快照。"""
    snapshot = store.add_snapshot(note="值班手动留档")
    return ActionResult(ok=True, message="已按当前口径留档，历史统计仍按当时口径保留", entry=snapshot)
