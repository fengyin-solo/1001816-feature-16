"""运营下钻业务规则：把卡片数字按同一口径展开成单子清单。

关键约束：
- 下钻取数与概览卡片共用 store 的同一份台账，卡片是几，展开就列出几条；
- 跨模块（不传 module）只有值班管理员能看，业务账号只允许看本单位模块；
- 某模块数据源拉取失败时不中断整页，失败模块单独列出，前端可从失败处重试。
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.accounts import Account, ensure_module_access
from app.modules import MODULES, ModuleMeta, get_module
from app.store import store

# 卡片 key -> 取数口径
CARD_KINDS = ("created", "pending", "abnormal")
# 跨模块下钻时支持的筛选项（待处理 / 出错）；单模块下钻用该模块自己的状态序列
CROSS_STATUSES: dict[str, str] = {
    "__pending__": "待处理",
    "__abnormal__": "出错",
}


class DrillService:
    def query(
        self,
        account: Account,
        *,
        kind: str,
        module: str | None = None,
        status: str | None = None,
        fail_modules: set[str] | None = None,
    ) -> dict[str, Any]:
        if kind not in CARD_KINDS:
            raise HTTPException(status_code=400, detail="下钻口径不存在：仅支持今日新增、待处理、异常量卡片")

        fail_modules = fail_modules or set()

        if module is not None:
            meta = get_module(module)
            if meta is None:
                raise HTTPException(status_code=404, detail=f"业务模块「{module}」不存在")
            # 越权访问在这里拦下，由路由层把原因原样回给前端
            ensure_module_access(account, meta.key)
            if status and status not in meta.statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"状态「{status}」不属于{meta.name}的可选状态",
                )
            metas = [meta]
            cross = False
        else:
            # 不传 module 即跨模块下钻，仅值班管理员
            if not account.is_admin:
                own = account.module_key or ""
                own_name = get_module(own).name if get_module(own) else "本单位"
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"越权访问：{account.label}只能下钻{own_name}的单子，"
                        "跨模块下钻仅限值班管理员"
                    ),
                )
            metas = list(MODULES)
            cross = True
            if status:
                # 跨模块只按“待处理/出错”一类挑，具体业务状态需要先选定模块
                if status not in CROSS_STATUSES:
                    raise HTTPException(
                        status_code=400,
                        detail="跨模块下钻只能按「待处理」或「出错」筛选，查看具体状态请先选定业务模块",
                    )

        items: list[dict[str, Any]] = []
        module_counts: list[dict[str, Any]] = []
        failed: list[dict[str, str]] = []
        for meta in metas:
            summary = store.module_summary(meta)
            if meta.key in fail_modules:
                # 这一模块没拉到：整页不白板，记下失败原因并保留其他模块的数据
                failed.append({"module": meta.key, "name": meta.name,
                               "message": f"{meta.name}台账暂时拉取不到，请稍后从该模块重新拉取"})
                module_counts.append({"key": meta.key, "name": meta.name, "count": 0,
                                      "expected": int(summary[kind]), "failed": True})
                continue
            rows = self._rows_for(meta, kind=kind, status=status)
            items.extend(rows)
            module_counts.append({"key": meta.key, "name": meta.name,
                                  "count": len(rows), "expected": int(summary[kind]),
                                  "failed": False})

        # 卡片数字（同一口径下，与运营页那块数字说的是同一件事）
        if failed and cross:
            card_value: int | None = None  # 有模块没拉到时，跨模块合计不可信
        else:
            card_value = sum(item["expected"] for item in module_counts if not item["failed"]) \
                if cross else (module_counts[0]["expected"] if module_counts else 0)

        return {
            "kind": kind,
            "module": module,
            "cross_module": cross,
            "status": status,
            "status_label": CROSS_STATUSES.get(status, status),
            "card_value": card_value,
            "total": len(items),
            "items": items,
            "module_counts": module_counts,
            "failed_modules": failed,
            "statuses": self.status_options(metas[0]) if module and not cross else None,
        }

    def _rows_for(self, meta: ModuleMeta, *, kind: str, status: str | None) -> list[dict[str, Any]]:
        if not status:
            return store.drill_rows(meta, kind=kind)
        if status == "__pending__":
            return [row for row in store.drill_rows(meta, kind=kind) if row["pending"]]
        if status == "__abnormal__":
            return [row for row in store.drill_rows(meta, kind=kind) if row["abnormal"]]
        return store.drill_rows(meta, kind=kind, status=status)

    def status_options(self, meta: ModuleMeta) -> list[str]:
        return list(meta.statuses)


drill_service = DrillService()
