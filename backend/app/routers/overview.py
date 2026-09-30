"""运营概览与卡片下钻接口。

- GET /api/overview：四块卡片 + 各模块数字，按值班身份限定可见范围
- GET /api/drill：某块卡片的单子明细，可在卡片口径上再按状态挑一类
- GET /api/drill/modules：「业务模块」卡片的下钻列表

越权（业务模块账号跨模块下钻/查看）一律 403 并说明原因。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.catalog import get_spec, label_of
from app.security import Identity, resolve_identity
from app.store import METRIC_LABELS, METRIC_PREDICATES, store

router = APIRouter(prefix="/api", tags=["运营概览"])

PAGE_SIZE_MAX = 200


def _denied(identity: Identity, module: str) -> HTTPException:
    if identity.role == "guest":
        return HTTPException(status_code=403, detail="当前未识别值班身份，不能下钻查看单据，请先切换为值班账号")
    return HTTPException(
        status_code=403,
        detail=f"业务模块账号只能查看本单位（{label_of(identity.module or '')}）经手的单子，"
        f"「{label_of(module)}」不在你的权限范围内",
    )


@router.get("/overview")
def overview(identity: Identity = Depends(resolve_identity)) -> dict[str, object]:
    """运营概览：管理员看全部模块，业务模块账号只汇总本单位经手的单子。"""
    module = None if identity.is_admin else identity.module
    payload = store.overview(module)
    payload["identity"] = {
        "role": identity.role,
        "module": identity.module,
        "module_label": label_of(identity.module) if identity.module else None,
    }
    return payload


@router.get("/drill/modules")
def drill_modules(identity: Identity = Depends(resolve_identity)) -> dict[str, object]:
    """「业务模块」卡片下钻：列出可见模块；模块账号只返回本单位这一行。"""
    if identity.role == "guest":
        raise _denied(identity, "")
    names = store.module_names() if identity.is_admin else [identity.module]  # type: ignore[list-item]
    return {
        "metric": "modules",
        "metric_label": "业务模块",
        "items": store.module_summary(names),
        "total": len(names),
    }


@router.get("/drill/{metric}")
def drill(
    metric: str,
    status: str | None = Query(default=None, description="在卡片口径上再按状态挑一类"),
    module: str | None = Query(default=None, description="值班管理员可指定单个业务模块"),
    page: int = 1,
    size: int = 20,
    identity: Identity = Depends(resolve_identity),
) -> dict[str, Any]:
    """卡片数字下钻：列出的单子与卡片使用同一口径，total 即那块数字（未挑状态时）。"""
    if metric not in METRIC_PREDICATES:
        raise HTTPException(status_code=404, detail=f"概览卡片「{metric}」不存在，可下钻：今日新增/待处理/出错")
    if identity.role == "guest":
        raise _denied(identity, module or "")
    if identity.role == "module":
        # 业务模块账号只能看本单位经手的单子；跨模块点击在这里拦下并说明原因。
        if module is not None and module != identity.module:
            raise _denied(identity, module)
        module = identity.module
    elif module is not None and get_spec(module) is None:
        raise HTTPException(status_code=404, detail=f"业务模块「{module}」不存在")

    if size > PAGE_SIZE_MAX:
        raise HTTPException(status_code=400, detail=f"每页最多 {PAGE_SIZE_MAX} 条，请缩小分页范围")

    names = store.module_names() if module is None else [module]
    if status is not None:
        allowed: set[str] = set()
        for name in names:
            spec = get_spec(name)
            if spec is not None:
                allowed.update(spec.statuses)
        if status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"状态「{status}」不属于所选模块的状态范围，可选：{'、'.join(sorted(allowed))}",
            )

    payload = store.drill(metric, names, status=status, module=module, page=page, size=size)
    payload["metric_label"] = METRIC_LABELS[metric]
    return payload
