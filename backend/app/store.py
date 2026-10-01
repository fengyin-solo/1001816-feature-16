"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。

口径约定：
- 概览卡片、模块台账、运营下钻都从这里同一份数据取数，保证数字说的是同一件事；
- 历史统计在留档时整份快照冻结（见 snapshots），之后口径调整不回写历史。
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

from app.accounts import Account
from app.modules import MODULES, ModuleMeta
from app.seed import SEED_ROWS

# 当前统计口径版本；历史快照保留留档当时的口径，不随后续修改联动
CURRENT_CALIBER = "2026-10"


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }
        # 历史留档：初始化一份按 2026-09 口径冻结的月度快照
        self._snapshots: list[dict[str, Any]] = [
            self._build_snapshot(
                snapshot_date="2026-09-30",
                caliber="2026-09",
                note="2026年9月月度运营留档（历史口径，仅作历史对比）",
            )
        ]

    def module_names(self) -> list[str]:
        return [meta.key for meta in MODULES if meta.key in self._tables]

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    # ---- 台账口径（概览卡片与运营下钻共用） ----

    def visible_modules(self, account: Account | None) -> list[ModuleMeta]:
        """账号可见的业务模块：值班管理员看全部，业务账号只看本单位。"""
        if account is None or account.is_admin:
            return list(MODULES)
        return [meta for meta in MODULES if account.can_access_module(meta.key)]

    def module_summary(self, meta: ModuleMeta) -> dict[str, object]:
        """单个模块的台账统计：今日新增=在库单数，待处理/异常按单据标记。"""
        rows = self.rows(meta.key)
        return {
            "key": meta.key,
            "name": meta.name,
            "created": len(rows),
            "pending": sum(1 for row in rows if row.get("pending")),
            "abnormal": sum(1 for row in rows if row.get("abnormal")),
        }

    def overview(self, account: Account | None = None) -> dict[str, object]:
        """运营概览：卡片数字与模块台账取自同一份统计。"""
        modules = [self.module_summary(meta) for meta in self.visible_modules(account)]
        cards = [
            {"key": "modules", "label": "业务模块", "value": len(modules)},
            {"key": "created", "label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"key": "pending", "label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"key": "abnormal", "label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"cards": cards, "modules": modules, "caliber": CURRENT_CALIBER}

    # ---- 运营下钻取数 ----

    def drill_rows(
        self,
        meta: ModuleMeta,
        *,
        kind: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """按卡片口径展开单个模块的单子，再叠加状态筛选。

        kind 与卡片一一对应：pending=待处理、abnormal=异常量、created=今日新增。
        """
        rows = self.rows(meta.key)
        if kind == "pending":
            rows = [row for row in rows if row.get("pending")]
        elif kind == "abnormal":
            rows = [row for row in rows if row.get("abnormal")]
        # created 不做标记过滤，即全部在库单
        if status:
            rows = [row for row in rows if row.get("status") == status]
        return [self._project_row(meta, row) for row in rows]

    def _project_row(self, meta: ModuleMeta, row: dict[str, Any]) -> dict[str, Any]:
        """把各模块异构台账投影成下钻列表统一结构，数字仍来自原单。"""
        return {
            "id": row.get("id"),
            "module": meta.key,
            "module_name": meta.name,
            "code": str(row.get(meta.code_field, "") or ""),
            "status": row.get("status"),
            "pending": bool(row.get("pending")),
            "abnormal": bool(row.get("abnormal")),
        }

    # ---- 历史留档 ----

    def _build_snapshot(
        self, *, snapshot_date: str, caliber: str, note: str = ""
    ) -> dict[str, Any]:
        modules = [self.module_summary(meta) for meta in MODULES]
        cards = [
            {"key": "modules", "label": "业务模块", "value": len(modules)},
            {"key": "created", "label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"key": "pending", "label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"key": "abnormal", "label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {
            "date": snapshot_date,
            "caliber": caliber,
            "note": note,
            "cards": cards,
            "modules": modules,
        }

    def snapshots(self) -> list[dict[str, Any]]:
        """历史统计按留档时间倒序返回，内容为冻结快照。"""
        return deepcopy(sorted(self._snapshots, key=lambda item: item["date"], reverse=True))

    def add_snapshot(self, note: str = "") -> dict[str, Any]:
        """按当前口径留一份档；历史快照不会被后续数据变动改写。"""
        snapshot = self._build_snapshot(
            snapshot_date=date.today().isoformat(),
            caliber=CURRENT_CALIBER,
            note=note,
        )
        self._snapshots.append(snapshot)
        return deepcopy(snapshot)


store = Store()
