"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。

概览卡片与下钻列表共用本文件里的谓词（created/pending/abnormal、status），
卡片数字就是下钻列表的 total，不会出现两处口径不一致。
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from app.catalog import get_spec, label_of
from app.seed import SEED_ROWS

# 概览四块卡片的口径：key 同时是下钻路由使用的 metric。
# 历史统计沿用这三个既有标记，新增过滤只在同一谓词上叠加 status。
METRIC_PREDICATES: dict[str, Callable[[dict[str, Any]], bool]] = {
    "created": lambda row: True,
    "pending": lambda row: bool(row.get("pending")),
    "abnormal": lambda row: bool(row.get("abnormal")),
}
METRIC_LABELS: dict[str, str] = {
    "created": "今日新增",
    "pending": "待处理",
    "abnormal": "出错",
}
CARD_ORDER: tuple[str, ...] = ("created", "pending", "abnormal")


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def scoped_modules(self, module: str | None) -> list[str]:
        """值班管理员看全部模块；业务模块账号只看本单位模块。"""
        if module is None:
            return self.module_names()
        return [module] if get_spec(module) is not None else []

    def overview(self, module: str | None = None) -> dict[str, object]:
        """运营概览：把各业务模块的待处理量汇总成看板卡片。

        module=None 为值班管理员的全量口径；传入模块标识时只汇总该模块
        （业务模块账号只能看到本单位经手的单子）。
        """
        names = self.scoped_modules(module)
        modules: list[dict[str, object]] = []
        for name in names:
            rows = self.rows(name)
            modules.append({
                "key": name,
                "name": label_of(name),
                "created": len(rows),
                "pending": sum(1 for row in rows if row.get("pending")),
                "abnormal": sum(1 for row in rows if row.get("abnormal")),
            })
        cards = [
            {"label": "业务模块", "value": len(modules), "metric": "modules"},
            *(
                {
                    "label": METRIC_LABELS[metric],
                    "value": sum(int(item[metric]) for item in modules),
                    "metric": metric,
                }
                for metric in CARD_ORDER
            ),
        ]
        return {"cards": cards, "modules": modules}

    def status_facets(
        self,
        metric: str,
        names: Iterable[str],
    ) -> list[dict[str, object]]:
        """在卡片口径之上按状态分面，供下钻页挑选状态。"""
        base = METRIC_PREDICATES[metric]
        counts: dict[str, int] = {}
        for name in names:
            spec = get_spec(name)
            statuses = spec.statuses if spec else ()
            for status in statuses:
                counts.setdefault(status, 0)
            for row in self.rows(name):
                if not base(row):
                    continue
                status = str(row.get("status") or "")
                counts.setdefault(status, 0)
                counts[status] += 1
        return [
            {"status": status, "count": count}
            for status, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]

    def drill(
        self,
        metric: str,
        names: list[str],
        *,
        status: str | None = None,
        module: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, object]:
        """卡片数字的下钻明细：同一谓词过滤，可再按状态挑一类。

        names 是身份可见的模块集合；module 是在其中进一步指定的单个模块
        （业务模块账号只能传本单位模块，越权由路由层提前拦下）。
        """
        if module is not None:
            if module not in names:
                raise PermissionError(module)
            target_names = [module]
        else:
            target_names = names

        base = METRIC_PREDICATES[metric]
        cross_module = len(target_names) > 1
        items: list[dict[str, Any]] = []
        matched = 0
        for name in target_names:
            spec = get_spec(name)
            for row in self.rows(name):
                if not base(row):
                    continue
                if status is not None and str(row.get("status") or "") != status:
                    continue
                matched += 1
                if spec is not None and not cross_module:
                    # 单模块台账与卡片取同一份数据、同一套列。
                    items.append(dict(row))
                else:
                    columns = spec.columns if spec else ()
                    items.append({
                        "id": row.get("id"),
                        "module": name,
                        "业务模块": label_of(name),
                        "单号": row.get(columns[0]) if columns else row.get("id"),
                        "业务名称": row.get(columns[1]) if len(columns) > 1 else "",
                        "状态": row.get("status"),
                        "待处理": "是" if row.get("pending") else "否",
                        "异常": "是" if row.get("abnormal") else "否",
                    })

        start = max(page - 1, 0) * size
        columns = (
            list(get_spec(target_names[0]).columns)
            if len(target_names) == 1 and get_spec(target_names[0]) is not None
            else ["业务模块", "单号", "业务名称", "状态", "待处理", "异常"]
        )
        statuses = sorted({
            str(row.get("status") or "")
            for name in target_names
            for row in self.rows(name)
            if base(row) and str(row.get("status") or "")
        })
        return {
            "metric": metric,
            "metric_label": METRIC_LABELS[metric],
            "module": target_names[0] if len(target_names) == 1 else None,
            "cross_module": cross_module,
            "columns": columns,
            "statuses": statuses,
            "facets": self.status_facets(metric, target_names),
            "card_value": matched if status is None else None,
            "status": status,
            "items": items[start:start + size],
            "total": matched,
            "page": page,
            "size": size,
        }

    def module_summary(self, names: list[str]) -> list[dict[str, Any]]:
        """「业务模块」卡片的下钻：列出可见模块及其数字，模块账号只能看到本单位。"""
        overview = self.overview(None)
        by_key = {str(item["key"]): item for item in overview["modules"]}
        return [by_key[name] for name in names if name in by_key]


store = Store()
