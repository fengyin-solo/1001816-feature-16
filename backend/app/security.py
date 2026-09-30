"""值班身份与数据权限。

演示环境没有登录流程，前端通过请求头声明当前值班身份：
- X-Operator-Role: admin（值班管理员，可跨模块下钻）或 module（业务模块账号）
- X-Operator-Module: module 账号所属的业务模块标识

真正接入统一登录后，这里换成从会话/令牌解析即可，路由层不用改。
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header

from app.catalog import get_spec


@dataclass(frozen=True)
class Identity:
    role: str  # admin | module | guest
    module: str | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def can_access(self, module: str) -> bool:
        """值班管理员可看全部模块；业务模块账号只能看本单位经手的模块。"""
        if self.is_admin:
            return True
        return self.role == "module" and self.module == module


def resolve_identity(
    x_operator_role: str | None = Header(default=None),
    x_operator_module: str | None = Header(default=None),
) -> Identity:
    role = (x_operator_role or "").strip().lower()
    module = (x_operator_module or "").strip()
    if role == "admin":
        return Identity(role="admin")
    if role == "module" and get_spec(module) is not None:
        return Identity(role="module", module=module)
    # 未携带或身份不完整时按访客处理：概览可看，下钻与台账一律拦下。
    return Identity(role="guest")
