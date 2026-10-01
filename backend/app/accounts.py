"""账号与权限：值班管理员可跨模块下钻，业务模块账号只能看本单位台账。

账号是演示用的轻量身份：前端切换账号后在请求头 X-Account-Id 带上账号别名，
后端按别名还原身份。没有身份或身份无法识别时拒绝访问；业务模块账号去访问
别的模块时拦下并给出可读原因。真正接入统一登录时，只需要替换 resolve_account。
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, Query

from app.modules import MODULES, get_module

ROLE_ADMIN = "admin"
ROLE_MODULE = "module"

ADMIN_ACCOUNT_ID = "admin"


@dataclass(frozen=True)
class Account:
    id: str
    label: str  # 账号显示名
    role: str
    module_key: str | None = None  # 业务账号对应的唯一模块

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def can_access_module(self, module_key: str) -> bool:
        return self.is_admin or self.module_key == module_key


# 一个值班管理员 + 每个业务模块一个本单位账号
ACCOUNTS: dict[str, Account] = {
    ADMIN_ACCOUNT_ID: Account(ADMIN_ACCOUNT_ID, "值班管理员", ROLE_ADMIN),
    **{
        meta.key: Account(meta.key, f"{meta.name}账号", ROLE_MODULE, meta.key)
        for meta in MODULES
    },
}

# 供前端账号切换下拉使用
ACCOUNT_OPTIONS: tuple[Account, ...] = (ACCOUNTS[ADMIN_ACCOUNT_ID],) + tuple(
    ACCOUNTS[meta.key] for meta in MODULES
)


def resolve_account(x_account_id: str | None) -> Account:
    """从请求头还原当前账号；未登录或账号不存在都明确拦下。"""
    if not x_account_id or not x_account_id.strip():
        raise HTTPException(status_code=401, detail="未登录：请先选择值班账号后再查看业务数据")
    account = ACCOUNTS.get(x_account_id.strip())
    if account is None:
        raise HTTPException(status_code=401, detail="登录已失效：账号无法识别，请重新选择值班账号")
    return account


def require_account(
    x_account_id: str | None = Header(default=None),
    account_id: str | None = Query(default=None, description="导出等无法带请求头的场景用 query 传账号"),
) -> Account:
    """路由依赖：任意已登录账号。优先请求头，其次 query（导出链接 window.open 用）。"""
    return resolve_account(x_account_id or account_id)


def require_admin(
    x_account_id: str | None = Header(default=None),
    account_id: str | None = Query(default=None),
) -> Account:
    """路由依赖：仅值班管理员（跨模块下钻、历史留档）。"""
    account = resolve_account(x_account_id or account_id)
    if not account.is_admin:
        raise HTTPException(
            status_code=403,
            detail="越权访问：只有值班管理员能跨模块查看与操作，业务模块账号仅能查看本单位台账",
        )
    return account


def require_module_account(
    module_key: str,
    x_account_id: str | None = Header(default=None),
    account_id: str | None = Query(default=None),
) -> Account:
    """给业务模块路由做的守卫：先登录，再核对该账号是否属于这个模块。"""
    account = resolve_account(x_account_id or account_id)
    ensure_module_access(account, module_key)
    return account


def ensure_module_access(account: Account, module_key: str) -> None:
    """业务账号访问非本单位模块时拦下并说明原因。"""
    if not account.can_access_module(module_key):
        own_meta = get_module(account.module_key or "")
        own_name = own_meta.name if own_meta else ""
        target_meta = get_module(module_key)
        target_name = target_meta.name if target_meta else module_key
        raise HTTPException(
            status_code=403,
            detail=(
                f"越权访问：{account.label}只能查看本单位台账"
                + (f"（{own_name}）" if own_name else "")
                + f"，无权访问「{target_name}」；跨模块查看仅限值班管理员"
            ),
        )
